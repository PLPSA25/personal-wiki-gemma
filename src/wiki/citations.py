"""Check an answer against the passages it was given.

What this proves: every cited label refers to a passage that was really retrieved, and every number
or month in the answer appears in the cited passages (or in the question).
What it cannot prove: that a cited passage truly supports the claim. Only reading the source does.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_CITATION_GROUP = re.compile(r"\[([^\]]*)\]")
_LABEL = re.compile(r"S\d+")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?%?")
_MONTH = re.compile(
    r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\b", re.I
)
_MIN_WORDS_FOR_CLAIM = 4


@dataclass(frozen=True)
class CitationReport:
    cited: tuple[str, ...]  # labels cited in the answer, in order of first appearance
    unknown: tuple[str, ...]  # cited labels that were not among the retrieved passages
    uncited_sentences: tuple[str, ...]  # claim-like sentences with no citation (a warning)
    unsupported_figures: tuple[str, ...]  # numbers/months not found in the cited passages or the question

    @property
    def status(self) -> str:
        if not self.cited or self.unknown or self.unsupported_figures:
            return "failed"
        return "warning" if self.uncited_sentences else "ok"

    def describe(self) -> str:
        if not self.cited:
            return "FAILED: the answer cites no passage"
        parts = []
        if self.unknown:
            parts.append(f"cites labels that were never retrieved: {', '.join(self.unknown)}")
        if self.unsupported_figures:
            parts.append(f"figures not found in the cited passages: {', '.join(self.unsupported_figures)}")
        if self.uncited_sentences:
            parts.append(f"{len(self.uncited_sentences)} sentence(s) without a citation")
        if not parts:
            return f"OK: {len(self.cited)} passage(s) cited, all retrieved; every figure appears in them"
        return f"{self.status.upper()}: " + "; ".join(parts)


def extract_labels(answer: str) -> tuple[str, ...]:
    """Labels like S1, S2 cited in square brackets, e.g. '[S1]', '[S1][S3]' or '[S1, S3]'."""
    labels = [label for group in _CITATION_GROUP.findall(answer) for label in _LABEL.findall(group)]
    return tuple(dict.fromkeys(labels))


def strip_citations(answer: str) -> str:
    return re.sub(r"\s*\[(?:\s*S\d+\s*,?)+\]", "", answer)


def check_answer(answer: str, passages: dict[str, str], question: str = "") -> CitationReport:
    """Compare `answer` with `passages` (label -> passage text)."""
    cited = extract_labels(answer)
    unknown = tuple(label for label in cited if label not in passages)
    known = [label for label in cited if label in passages]
    evidence = " ".join(passages[label] for label in known) if known else " ".join(passages.values())

    unsupported = unsupported_figures(strip_citations(answer), evidence + " " + question)
    return CitationReport(cited, unknown, _uncited_sentences(answer), unsupported)


def _uncited_sentences(answer: str) -> tuple[str, ...]:
    """Claim-like sentences that no citation covers. A citation covers the earlier sentences of its paragraph."""
    uncited: list[str] = []
    for paragraph in answer.split("\n"):
        pending: list[str] = []
        for sentence in _SENTENCE_END.split(paragraph.strip()):
            if extract_labels(sentence):
                pending.clear()
            elif len(sentence.split()) >= _MIN_WORDS_FOR_CLAIM:
                pending.append(sentence)
        uncited.extend(pending)
    return tuple(uncited)


def _normalize_number(token: str) -> str:
    return token.replace(",", "").rstrip("%")


def unsupported_figures(answer: str, evidence: str) -> tuple[str, ...]:
    """Numbers and month names in the answer that do not occur in the evidence text.

    Single-digit whole numbers are ignored (they are usually counts like 'three' or list markers).
    """
    known_numbers = {_normalize_number(n) for n in _NUMBER.findall(evidence)}
    known_months = {m.lower() for m in _MONTH.findall(evidence)}
    missing = []
    for token in _NUMBER.findall(answer):
        value = _normalize_number(token)
        if len(value) == 1 and "%" not in token:
            continue
        if value not in known_numbers:
            missing.append(token.rstrip(".,"))
    for month in _MONTH.findall(answer):
        if month.lower() not in known_months:
            missing.append(month)
    return tuple(dict.fromkeys(missing))
