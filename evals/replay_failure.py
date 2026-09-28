"""Replay a recorded bad draft answer through the real checks.

Some failures depend on what the model happens to write (run 3 of test 4 cited a passage that really
contains "40%", so the figure check could not catch it). To prove a later fix works on that exact
failure, this script hands the recorded draft to the harness as the model's first reply and lets the
real local model run every later step (answerability check, verification).

Usage: python evals/replay_failure.py --from-run run-3-instructions-v3 --test test-4 --label replay-run3-draft
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from run_evals import check_result, load_questions, render_card  # noqa: E402

from wiki.ask import answer_question  # noqa: E402
from wiki.config import Paths, default_root  # noqa: E402
from wiki.llm import OllamaClient, Reply  # noqa: E402


class ScriptedFirstReply:
    """Returns `draft` for the first call (the answer) and forwards every later call to the real model."""

    def __init__(self, real: OllamaClient, draft: str):
        self.real, self.draft, self.used = real, draft, False
        self.name = real.name

    def chat(self, messages, *, temperature, max_tokens, seed=None):
        if not self.used:
            self.used = True
            return Reply(self.draft, self.name, 0, 0, 0.0, 0.0)
        return self.real.chat(messages, temperature=temperature, max_tokens=max_tokens, seed=seed)

    def identity(self):
        return self.real.identity()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--from-run", required=True, help="evidence/ask-tests/<run> holding the recorded draft")
    parser.add_argument("--test", required=True, help="test id, e.g. test-4")
    parser.add_argument("--label", required=True)
    args = parser.parse_args()

    paths = Paths(default_root())
    question = next(q for q in load_questions(paths.root / "evals" / "questions.toml") if q["id"] == args.test)
    recorded = json.loads((paths.root / "evidence" / "ask-tests" / args.from_run / "results.json").read_text(encoding="utf-8"))
    draft = next(r["answer"] for r in recorded if r["id"] == args.test)

    model = ScriptedFirstReply(OllamaClient(), draft)
    result = answer_question(question["question"], paths.index_path, model, paths.prompts_dir)
    checks = check_result(question, result)
    out_dir = paths.root / "evidence" / "ask-tests" / args.label
    out_dir.mkdir(parents=True, exist_ok=True)
    when = datetime.now(timezone.utc).isoformat(timespec="seconds")
    card = render_card(question, result, checks, args.label, when, 5)
    note = (f"\n> **Replay:** the first model reply was NOT generated in this run. It is the recorded draft from "
            f"`{args.from_run}`: `{draft}`. Only the checks after it ran for real.\n")
    (out_dir / f"{args.test}.md").write_text(card.replace("\n## Expected", note + "\n## Expected", 1), encoding="utf-8")
    print(f"recorded draft : {draft}")
    print(f"citation check : {result.report.describe() if result.report else 'n/a'}")
    print(f"answerability  : {result.answerable.raw if result.answerable else 'not run'}")
    print(f"verification   : {result.verdict.raw if result.verdict else 'not run'}")
    print(f"outcome        : {'withheld -> ' if result.withheld_draft else ''}{result.answer}")
    print(f"automated verdict: {'PASS' if checks['passed'] else 'FAIL'}; card: {out_dir / (args.test + '.md')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
