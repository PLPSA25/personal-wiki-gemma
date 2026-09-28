"""Run the chat / search / ask boundary checks and save a transcript as evidence.

Usage (from the project folder, with Ollama running):
    python evals/run_mode_checks.py --label mode-checks-1

Checks (from the assignment):
  A. Chat: "what can you help me with?" and "what can we do?" explain real capabilities, without a notes
     search, citations or an "insufficient evidence" answer.
  B. Chat follow-up: a short draft, then "make that shorter" uses the conversation.
  C. Chat with notes: a question that refers to the notes searches them and cites passages.
  D. Search: original passages and source locations, no generated answer, no model call.
  E. Boundary: a claim made only in chat is not evidence in ask mode.
The automated checks are a first pass; read the transcript to judge the quality of the replies.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone

from wiki.ask import answer_question, format_result
from wiki.chat import ChatSession
from wiki.config import Paths, default_root
from wiki.llm import OllamaClient
from wiki.retrieval import search


class SpyModel:
    """Wraps the real model and counts calls, so a check can prove that a mode did (or did not) use it."""

    def __init__(self, real):
        self.real, self.name, self.calls = real, real.name, 0

    def chat(self, *args, **kwargs):
        self.calls += 1
        return self.real.chat(*args, **kwargs)

    def identity(self):
        return self.real.identity()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--label", required=True)
    args = parser.parse_args()

    paths = Paths(default_root())
    out_dir = paths.root / "evidence" / "mode-checks" / args.label
    out_dir.mkdir(parents=True, exist_ok=True)
    real = OllamaClient()
    identity = real.identity()
    when = datetime.now(timezone.utc).isoformat(timespec="seconds")
    lines = [f"# Mode checks, run `{args.label}` ({when})", "",
             f"Execution: local (Ollama on 127.0.0.1) | model `{identity.get('model')}` {identity.get('quantization')} | "
             f"Ollama {identity.get('ollama_version')}", ""]
    results: list[dict] = []

    def record(name: str, checks: dict[str, bool]) -> None:
        verdict = "PASS" if all(checks.values()) else "FAIL"
        lines.append(f"**Automated verdict for {name}: {verdict}** " + ", ".join(f"{k}={v}" for k, v in checks.items()))
        lines.append("")
        results.append({"check": name, "verdict": verdict, "checks": checks})
        print(f"{name}: {verdict}", flush=True)
        # save after every check, so an interruption (crash, power loss) keeps everything finished so far
        (out_dir / "transcript.md").write_text("\n".join(lines) + "\n\n_(run in progress or interrupted)_\n", encoding="utf-8")
        (out_dir / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    def show_turn(message: str, turn) -> None:
        lines.extend([f"> **You:** {message}", "", f"> **Scout:** {turn.reply}", "",
                      f"- route: {turn.route.reason}",
                      f"- notes attached: {len(turn.route.results)}; citation check: "
                      f"{turn.report.describe() if turn.report else 'not applicable (no notes attached)'}",
                      f"- time: {turn.seconds:.1f} s", ""])

    # ---- A: capabilities ---------------------------------------------------------------------------
    lines += ["## A. Chat: what can you help me with? / what can we do?", ""]
    session = ChatSession(SpyModel(real), paths)
    for message in ("what can you help me with?", "what can we do?"):
        turn = session.say(message)
        show_turn(message, turn)
        text = turn.reply.lower()
        record(f"A ({message})", {
            "no notes search": not turn.route.retrieve,
            "no citations": "[s" not in text,
            "no insufficient-evidence refusal": "insufficient" not in text,
            "mentions the real commands (ask and search)": "wiki ask" in text and "wiki search" in text,
            "does not claim it can run commands": not re.search(r"i (can|could|will)( also)? (run|execute|type)", text),
            "suggests a starting point": any(w in text for w in ("start", "try", "for example", "suggestion", "begin")),
            "non-empty": len(text) > 40,
        })

    # ---- B: follow-up ---------------------------------------------------------------------------------
    lines += ["## B. Chat follow-up: draft, then 'make that shorter'", ""]
    session = ChatSession(SpyModel(real), paths)
    first = session.say("Draft a short three-step plan to revise for the Data & Decisions final.")
    show_turn("Draft a short three-step plan to revise for the Data & Decisions final.", first)
    second = session.say("make that shorter")
    show_turn("make that shorter", second)
    record("B (follow-up)", {
        "draft without notes search": not first.route.retrieve,
        "first reply is an actual draft (a list)": bool(re.search(r"^\s*(1[.)]|[-*])\s", first.reply, re.M)),
        "follow-up without notes search": not second.route.retrieve,
        "follow-up is shorter": 0 < len(second.reply) < len(first.reply),
        "follow-up keeps the topic of the draft": any(w in second.reply.lower() for w in ("data", "decision", "final", "revise", "review", "practice", "step")),
    })

    # ---- C: chat with notes ---------------------------------------------------------------------------
    lines += ["## C. Chat about the notes", ""]
    session = ChatSession(SpyModel(real), paths)
    message = "According to my notes, what is the golden rule for a price-taking firm?"
    turn = session.say(message)
    show_turn(message, turn)
    record("C (notes turn)", {
        "notes searched": turn.route.retrieve,
        "reply cites a passage": bool(turn.report and turn.report.cited),
        "no unknown citations": bool(turn.report and not turn.report.unknown),
    })

    # ---- D: search ---------------------------------------------------------------------------------------
    lines += ["## D. Search: original passages, no generated answer, no model call", ""]
    spy = SpyModel(real)
    found = search(paths.index_path, "price discrimination group pricing", 3)
    for result in found:
        chunk = result.chunk
        lines += [f"**[{result.rank}] {chunk.label}** (`{chunk.chunk_id}`, lines {chunk.start_line}-{chunk.end_line}, score {result.score:.2f})",
                  "", *("> " + line for line in chunk.text.splitlines()), ""]
    record("D (search)", {"returned passages": len(found) > 0, "model calls": spy.calls == 0,
                          "passages are original text": all(r.chunk.text for r in found)})

    # ---- E: chat claims are not evidence for ask ---------------------------------------------------------
    lines += ["## E. A claim made only in chat is not evidence in ask", ""]
    chat_spy = SpyModel(real)
    session = ChatSession(chat_spy, paths)
    claim = "My MBA 201A final exam is on December 5th."
    turn = session.say(claim)
    show_turn(claim, turn)
    ask_spy = SpyModel(real)
    asked = answer_question("When is the MBA 201A final exam?", paths.index_path, ask_spy, paths.prompts_dir)
    lines += ["Then, in a separate ask-mode call:", "", "```", format_result(asked, real.name), "```", ""]
    record("E (boundary)", {
        "ask says insufficient evidence": asked.insufficient,
        "answer does not contain the chat claim": "december" not in asked.answer.lower(),
    })

    passed = sum(r["verdict"] == "PASS" for r in results)
    lines += ["## Summary", "", "| check | automated verdict |", "|---|---|", *[f"| {r['check']} | {r['verdict']} |" for r in results],
              "", f"{passed} of {len(results)} automated checks passed. Read the replies above to judge their quality.", ""]
    (out_dir / "transcript.md").write_text("\n".join(lines), encoding="utf-8")
    (out_dir / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Saved {out_dir / 'transcript.md'} ({passed}/{len(results)} passed)")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
