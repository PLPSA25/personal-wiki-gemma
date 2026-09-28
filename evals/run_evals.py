"""Run the four ask-mode tests and save an evidence card for each.

Usage (from the project folder, with Ollama running):
    python evals/run_evals.py --label run-1-initial
    python evals/run_evals.py --label run-2-after-fix --only test-4

Each run writes evidence/ask-tests/<label>/test-N.md (one card per question), summary.md and results.json.
The answer key (evals/questions.toml) stays outside the vault; the harness never reads it.
Automated checks are only a first pass: the "Assessment" section of every card is for a human who has
opened the cited sources.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path

from wiki.ask import (MAX_ANSWER_TOKENS, SEED, TEMPERATURE, AskResult, answer_question)
from wiki.config import Paths, default_root
from wiki.errors import WikiError
from wiki.llm import DEFAULT_MODEL, DEFAULT_NUM_CTX, DEFAULT_OLLAMA_URL, OllamaClient
from wiki.prompts import passage_label
from wiki.retrieval import DEFAULT_LIMIT


def load_questions(path: Path) -> list[dict]:
    with path.open("rb") as handle:
        return tomllib.load(handle)["question"]


def check_result(question: dict, result: AskResult) -> dict:
    """Automated first-pass verdicts for one test."""
    expected_sources = set(question["expected_sources"])
    expected_section = question.get("expected_section", "")
    retrieved_sources = {r.chunk.source for r in result.retrieved}
    section_rank = next(
        (r.rank for r in result.retrieved if r.chunk.section == expected_section and r.chunk.source in expected_sources),
        None,
    )
    actual_behavior = "insufficient_evidence" if result.insufficient else "answer"
    answer = result.answer.lower()
    checks = {
        "expected_sources_retrieved": expected_sources <= retrieved_sources if expected_sources else None,
        "expected_section_rank": section_rank,
        "behavior_matches": actual_behavior == question["expected_behavior"],
        "actual_behavior": actual_behavior,
        "answer_contains_ok": all(t.lower() in answer for t in question.get("answer_must_contain", [])),
        "answer_avoids_ok": not any(t.lower() in answer for t in question.get("answer_must_not_contain", [])),
        "format_clean": not re.match(r"\s*\d+\.\s", result.answer),  # a numbered list means reasoning leaked
        "citation_status": result.report.status if result.report else "n/a (insufficient evidence)",
    }
    checks["passed"] = bool(
        checks["behavior_matches"] and checks["answer_contains_ok"] and checks["answer_avoids_ok"] and checks["format_clean"]
        and (checks["expected_sources_retrieved"] in (True, None))
        and (result.insufficient or result.report.status != "failed")
    )
    return checks


def render_card(question: dict, result: AskResult, checks: dict, label: str, when: str, top_k: int) -> str:
    ident = result.identity
    lines = [
        f"# Ask test: {question['id']} ({question['kind']})",
        "",
        f"**Question:** {question['question']}",
        "",
        f"- Interaction mode: **ask** (standalone, no chat history, no persona) | Execution: **local** (Ollama on 127.0.0.1, no internet needed)",
        f"- Run: `{label}` at {when}",
        f"- Model: `{ident.get('model')}` | quantization {ident.get('quantization')} | {ident.get('parameter_size')} parameters"
        f" | digest `{str(ident.get('digest'))[:16]}` | Ollama {ident.get('ollama_version')}",
        f"- Settings: temperature {TEMPERATURE}, seed {SEED}, max answer tokens {MAX_ANSWER_TOKENS}, context window {DEFAULT_NUM_CTX},"
        f" top-k {top_k}, thinking off",
        "",
        "## Expected (answer key, kept outside the vault)",
        f"- Behaviour: `{question['expected_behavior']}`",
        f"- Expected sources: {', '.join(question['expected_sources']) or 'none'}",
        f"- Expected section: {question.get('expected_section') or 'none'}",
        f"- Expected passage/content: {question['expected_passage']}",
        "",
        f"## Retrieved passages (top {top_k}, before the model saw anything)",
    ]
    for r in result.retrieved:
        chunk = r.chunk
        lines += ["", f"### [{passage_label(r.rank)}] {chunk.label} (lines {chunk.start_line}-{chunk.end_line}, score {r.score:.2f})",
                  *("> " + line for line in chunk.text.splitlines())]
    lines += ["", "## Answer (as displayed to the user)", "", *("> " + line for line in result.answer.splitlines()), ""]
    if result.report:
        lines.append(f"- Citation check of the draft: {result.report.describe()}")
    if result.answerable:
        lines.append(f"- Answerability check (draft-free, fact-seeking questions only): replied {result.answerable.raw!r} -> "
                     f"{'passed' if result.answerable.supported else 'NOT passed'} ({result.answerable.reply.seconds:.1f} s)")
    if result.verdict:
        lines.append(f"- Verification (second model call, yes/no): replied {result.verdict.raw!r} -> "
                     f"{'supported' if result.verdict.supported else 'NOT supported'} ({result.verdict.reply.seconds:.1f} s)")
    if result.withheld_draft:
        lines += [f"- **Draft answer withheld** because {result.withheld_reason}.",
                  "  Withheld draft (never shown to the user as an answer):",
                  *("  > " + line for line in result.withheld_draft.splitlines())]
    lines += [
        f"- Retrieval: expected section first found at rank {checks['expected_section_rank']}; "
        f"all expected sources in top {top_k}: {checks['expected_sources_retrieved']}",
        f"- Behaviour: expected `{question['expected_behavior']}`, got `{checks['actual_behavior']}` -> "
        f"{'match' if checks['behavior_matches'] else 'MISMATCH'}",
        f"- Required content present: {checks['answer_contains_ok']} | forbidden content absent: {checks['answer_avoids_ok']}"
        f" | clean format (no leaked reasoning): {checks['format_clean']}",
    ]
    if result.reply:
        lines.append(f"- Timing: model {result.reply.seconds:.1f} s (load {result.reply.load_seconds:.1f} s), "
                     f"{result.reply.prompt_tokens} prompt tokens, {result.reply.output_tokens} answer tokens, "
                     f"{result.prompt_chars} characters sent to the model")
    lines += ["", f"**Automated verdict: {'PASS' if checks['passed'] else 'FAIL'}**", "",
              "## Assessment (human, after opening the cited sources)", "", "_Pending._", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--label", required=True, help="name of this run, e.g. run-1-initial")
    parser.add_argument("--only", help="run a single test id, e.g. test-4")
    parser.add_argument("--top-k", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL)
    args = parser.parse_args()

    paths = Paths(default_root())
    questions = [q for q in load_questions(paths.root / "evals" / "questions.toml") if args.only in (None, q["id"])]
    if not questions:
        print(f"No test named {args.only!r}", file=sys.stderr)
        return 1
    out_dir = paths.root / "evidence" / "ask-tests" / args.label
    out_dir.mkdir(parents=True, exist_ok=True)
    model = OllamaClient(args.ollama_url, args.model)
    # Keep the exact instructions this run used, so a later prompt change never rewrites the history.
    (out_dir / "instructions-used.md").write_text(
        (paths.prompts_dir / "wiki-instructions.md").read_text(encoding="utf-8"), encoding="utf-8")
    for name in ("verify-instructions.md", "answerable-instructions.md"):
        source = paths.prompts_dir / name
        if source.is_file():  # earlier runs predate these files
            (out_dir / name.replace(".md", "-used.md")).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    when = datetime.now(timezone.utc).isoformat(timespec="seconds")

    summary, records = [], []
    try:
        for question in questions:
            print(f"Running {question['id']}: {question['question']}", flush=True)
            result = answer_question(question["question"], paths.index_path, model, paths.prompts_dir, args.top_k)
            checks = check_result(question, result)
            (out_dir / f"{question['id']}.md").write_text(
                render_card(question, result, checks, args.label, when, args.top_k), encoding="utf-8")
            summary.append(f"| {question['id']} | {question['kind']} | {checks['actual_behavior']} | "
                           f"{checks['citation_status']} | {checks['expected_section_rank']} | "
                           f"{'PASS' if checks['passed'] else 'FAIL'} |")
            records.append({"id": question["id"], "answer": result.answer, "checks": checks,
                            "model": result.identity, "seconds": None if not result.reply else round(result.reply.seconds, 1)})
            print(f"  -> {'PASS' if checks['passed'] else 'FAIL'}: {result.answer[:110]}", flush=True)
    except WikiError as error:
        print(f"wiki: {error}", file=sys.stderr)
        return 1

    header = ["| test | kind | behaviour | citation check | expected section rank | automated verdict |",
              "|---|---|---|---|---|---|"]
    (out_dir / "summary.md").write_text(
        f"# Ask tests, run `{args.label}` ({when})\n\nMode: ask, local. Cards: one file per test in this folder.\n\n"
        + "\n".join(header + summary) + "\n", encoding="utf-8")
    (out_dir / "results.json").write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved evidence cards to {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
