"""Ask mode: a standalone, neutral, evidence-only answer with checked citations.

Flow: question -> retrieve passages -> build prompt (instructions + labelled passages) -> local model
-> draft answer -> checks (citations, then a yes/no verification of the cited passages) -> result.
A draft that fails a check is withheld and shown as "insufficient evidence". Nothing from any chat
history and no assistant personality is ever added here.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .citations import CitationReport, check_answer
from .llm import LanguageModel, Reply
from .prompts import ASK_INSTRUCTIONS_FILE, build_ask_messages, load_instructions, passage_label
from .retrieval import DEFAULT_LIMIT, SearchResult, search
from .verify import Verdict, check_answerable, seeks_specific_fact, verify_answer

INSUFFICIENT_TOKEN = "INSUFFICIENT_EVIDENCE"
INSUFFICIENT_MESSAGE = "Insufficient evidence: the wiki does not contain the information needed to answer this question."
TEMPERATURE = 0.1  # low: we want the same, evidence-bound answer each time
MAX_ANSWER_TOKENS = 400
SEED = 7  # fixed so reruns are comparable


@dataclass(frozen=True)
class AskResult:
    question: str
    answer: str  # text shown to the user
    insufficient: bool
    retrieved: tuple[SearchResult, ...]
    report: CitationReport | None  # citation check of the draft; None if the model itself refused
    reply: Reply | None  # the model's answer call; None when no model call was needed
    identity: dict
    retrieval_seconds: float
    prompt_chars: int
    mode: str = "local"
    withheld_draft: str | None = None  # a draft answer that failed a check (kept for the log, never shown as an answer)
    withheld_reason: str | None = None
    verdict: Verdict | None = None  # the draft-aware verification, when it ran
    answerable: Verdict | None = None  # the draft-free answerability check (fact-seeking questions only)


def answer_question(question: str, index_path: Path, model: LanguageModel, prompts_dir: Path,
                    top_k: int = DEFAULT_LIMIT) -> AskResult:
    instructions = load_instructions(prompts_dir, ASK_INSTRUCTIONS_FILE)
    started = time.perf_counter()
    results = tuple(search(index_path, question, top_k))
    retrieval_seconds = time.perf_counter() - started

    if not results:  # nothing matched at all: no reason to call the model
        return AskResult(question, INSUFFICIENT_MESSAGE, True, results, None, None, {}, retrieval_seconds, 0)

    messages = build_ask_messages(instructions, question, list(results))
    reply = model.chat(messages, temperature=TEMPERATURE, max_tokens=MAX_ANSWER_TOKENS, seed=SEED)
    prompt_chars = sum(len(m["content"]) for m in messages)
    common = dict(question=question, retrieved=results, reply=reply, identity=model.identity(),
                  retrieval_seconds=retrieval_seconds, prompt_chars=prompt_chars)

    refused, draft = interpret_reply(reply.text)
    if refused:
        return AskResult(answer=INSUFFICIENT_MESSAGE, insufficient=True, report=None, **common)

    passages = {passage_label(r.rank): r.chunk.text for r in results}
    report = check_answer(draft, passages, question)
    if report.status == "failed":
        return _withheld(common, report, None, None, draft, f"its citations did not check out ({report.describe()})")

    cited = [r for r in results if passage_label(r.rank) in report.cited]
    answerable = None
    if seeks_specific_fact(question):  # draft-free check first: it cannot be anchored by the draft's wording
        answerable = check_answerable(model, prompts_dir, question, cited)
        if not answerable.supported:
            reason = ("the answerability check found no cited passage that states the specific fact requested "
                      f"(it replied {answerable.raw!r})")
            return _withheld(common, report, None, answerable, draft, reason)
    verdict = verify_answer(model, prompts_dir, question, draft, cited)
    if not verdict.supported:
        reason = f"the verification step did not confirm that the cited passages state the answer (it replied {verdict.raw!r})"
        return _withheld(common, report, verdict, answerable, draft, reason)
    return AskResult(answer=draft, insufficient=False, report=report, verdict=verdict, answerable=answerable, **common)


def _withheld(common: dict, report: CitationReport, verdict: Verdict | None, answerable: Verdict | None,
              draft: str, reason: str) -> AskResult:
    return AskResult(answer=INSUFFICIENT_MESSAGE, insufficient=True, report=report, verdict=verdict,
                     answerable=answerable, withheld_draft=draft, withheld_reason=reason, **common)


def interpret_reply(text: str) -> tuple[bool, str]:
    """Return (refused, draft answer).

    A refusal is displayed by the harness in its own fixed words. Anything else the model wrote next
    to INSUFFICIENT_EVIDENCE is dropped: a refusal must never carry claims of its own.
    """
    stripped = text.strip()
    if INSUFFICIENT_TOKEN in stripped.upper():
        return True, ""
    return False, stripped


def format_result(result: AskResult, model_name: str) -> str:
    lines = [
        f"Ask (mode: {result.mode} | model: {model_name} | standalone: no chat history, no persona)",
        f"Question: {result.question}",
        "",
        "Answer:",
        *("  " + line for line in result.answer.splitlines()),
        "",
    ]
    if not result.insufficient and result.report:
        cited = [r for r in result.retrieved if passage_label(r.rank) in result.report.cited]
        lines.append("Cited passages:")
        lines += [f"  [{passage_label(r.rank)}] {r.chunk.label} (lines {r.chunk.start_line}-{r.chunk.end_line})"
                  for r in cited] or ["  (none)"]
        lines.append(f"Citation check: {result.report.describe()}")
        if result.answerable:
            lines.append(f"Answerability check: {result.answerable.raw} (the cited passages contain the requested fact)")
        if result.verdict:
            lines.append("Verification: the cited passages state what the question asks for (YES)")
        others = [passage_label(r.rank) for r in result.retrieved if passage_label(r.rank) not in result.report.cited]
        if others:
            lines.append(f"Retrieved but not cited: {', '.join(others)}")
    elif result.retrieved:
        if result.withheld_reason:
            lines.append(f"A draft answer was withheld because {result.withheld_reason}. It is kept in the log, not shown.")
        lines.append("Closest passages found (none of them gives the requested information):")
        lines += [f"  [{passage_label(r.rank)}] {r.chunk.label} (lines {r.chunk.start_line}-{r.chunk.end_line})"
                  for r in result.retrieved]
    else:
        lines.append("No passage in the wiki contains any of the question's words.")
    if result.reply:
        verify_s = sum(v.reply.seconds for v in (result.answerable, result.verdict) if v)
        lines.append(
            f"Time: retrieval {result.retrieval_seconds:.2f} s, answer {result.reply.seconds:.1f} s "
            f"(load {result.reply.load_seconds:.1f} s), verification {verify_s:.1f} s | "
            f"{result.reply.prompt_tokens} prompt tokens, {result.reply.output_tokens} answer tokens | "
            f"{result.prompt_chars} characters sent"
        )
    return "\n".join(lines)


def save_run(log_path: Path, result: AskResult) -> None:
    """Append one JSON line per question so every answer can be inspected later (outside the vault)."""
    record = {
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mode": result.mode,
        "question": result.question,
        "answer": result.answer,
        "insufficient": result.insufficient,
        "withheld_draft": result.withheld_draft,
        "withheld_reason": result.withheld_reason,
        "answerability": None if result.answerable is None else {
            "supported": result.answerable.supported, "reply": result.answerable.raw,
            "seconds": round(result.answerable.reply.seconds, 2)},
        "verification": None if result.verdict is None else {
            "supported": result.verdict.supported, "reply": result.verdict.raw,
            "seconds": round(result.verdict.reply.seconds, 2)},
        "model": result.identity,
        "retrieved": [
            {"label": passage_label(r.rank), "source": r.chunk.source, "section": r.chunk.section,
             "lines": [r.chunk.start_line, r.chunk.end_line], "score": round(r.score, 3), "text": r.chunk.text}
            for r in result.retrieved
        ],
        "citation_check": None if result.report is None else {
            "status": result.report.status, "cited": list(result.report.cited),
            "unknown": list(result.report.unknown), "unsupported_figures": list(result.report.unsupported_figures),
            "uncited_sentences": list(result.report.uncited_sentences),
        },
        "timing": None if result.reply is None else {
            "retrieval_s": round(result.retrieval_seconds, 3), "model_s": round(result.reply.seconds, 2),
            "load_s": round(result.reply.load_seconds, 2), "prompt_tokens": result.reply.prompt_tokens,
            "output_tokens": result.reply.output_tokens, "prompt_chars": result.prompt_chars,
        },
    }
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
