"""Second looks at a draft answer, as narrow yes/no questions to the model.

Open-ended instructions ("refuse if the passages do not answer") are unreliable for a small model, which
tends to answer with the closest related fact. Two narrow checks work better, and each fixes a different
weakness (see evidence/ask-tests for the experiments):

* verify_answer:   sees the draft and the passages it cites. Good at "does the text back this answer?",
                   but it can be anchored by the draft (a matching number makes it say YES).
* check_answerable: does NOT see the draft. Asks only "do the passages contain the kind of fact the question
                   requests?" Good at refusing "when is X?" when only a related weight is present, but it
                   wrongly refuses open-ended "why / what conditions" questions, so it is used only for
                   fact-seeking questions.

The harness fails closed: anything other than a clear YES means the draft is withheld.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .llm import LanguageModel, Reply
from .prompts import format_passages, load_instructions
from .retrieval import SearchResult

VERIFY_INSTRUCTIONS_FILE = "verify-instructions.md"
ANSWERABLE_INSTRUCTIONS_FILE = "answerable-instructions.md"

_YES = re.compile(r"\s*\**yes\b", re.IGNORECASE)
_VERDICT = re.compile(r"VERDICT:\s*\**(YES|NO)\b", re.IGNORECASE)

# Questions that ask for one specific fact: when / where / who / which, how many / much / long, and
# "what [is/are] [the] [one word] <date|time|size|weight...>", e.g. "What sample size ..." or "What is the
# weight of ...". Ambiguous nouns such as cost or value are left out on purpose: "What is opportunity cost?"
# asks for a definition, which the draft-free check would wrongly refuse.
_FACT_SEEKING = re.compile(
    r"^\s*(?:when|where|who|whom|whose|which|how\s+(?:many|much|long|often|old|far|big|large)"
    r"|what\s+(?:(?:is|are|was|were)\s+)?(?:the\s+)?(?:\w+\s+){0,2}?"
    r"(?:date|time|year|day|month|number|percent|percentage|amount|size|price|weight|score))\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Verdict:
    supported: bool
    raw: str  # what the model actually replied, kept for the evidence cards
    reply: Reply


def seeks_specific_fact(question: str) -> bool:
    """True for questions such as 'When is...?', 'How many...?', 'What sample size...?'."""
    return bool(_FACT_SEEKING.match(question))


def verify_answer(model: LanguageModel, prompts_dir: Path, question: str, answer: str,
                  cited: list[SearchResult]) -> Verdict:
    """Do the cited passages state what the question asks for and back this draft answer?"""
    instructions = load_instructions(prompts_dir, VERIFY_INSTRUCTIONS_FILE)
    user = (
        f"Question: {question}\n\nProposed answer: {answer}\n\nCited passages:\n\n{format_passages(cited)}\n\n"
        "Do the cited passages state what the question asks for? Reply YES or NO."
    )
    reply = _ask(model, instructions, user, max_tokens=8)
    return Verdict(bool(_YES.match(reply.text)), reply.text, reply)


def check_answerable(model: LanguageModel, prompts_dir: Path, question: str, cited: list[SearchResult]) -> Verdict:
    """Without seeing any draft: do the passages contain the kind of fact the question requests?"""
    instructions = load_instructions(prompts_dir, ANSWERABLE_INSTRUCTIONS_FILE)
    user = (
        f"Question: {question}\n\nPassages:\n\n{format_passages(cited)}\n\n"
        "Do the passages state what the question asks for?"
    )
    reply = _ask(model, instructions, user, max_tokens=40)
    match = _VERDICT.search(reply.text)
    return Verdict(bool(match and match.group(1).upper() == "YES"), reply.text, reply)


def _ask(model: LanguageModel, instructions: str, user: str, max_tokens: int) -> Reply:
    messages = [{"role": "system", "content": instructions}, {"role": "user", "content": user}]
    return model.chat(messages, temperature=0.0, max_tokens=max_tokens, seed=0)
