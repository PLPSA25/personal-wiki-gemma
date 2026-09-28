"""Chat routing: does this message need a look at the notes, or is it conversation?

The rules run in this order and the first match wins. A message about the assistant itself, a greeting,
a follow-up on the previous reply ("make that shorter") or a drafting/brainstorming task never triggers
a search. An explicit mention of the notes always does. A question about course content searches, but only
if the best match is at least a weak match, so off-topic questions do not fetch noise.

Why rules and not a score threshold alone: a drafting task such as "plan my study week for data and
decisions" matches the notes strongly (score 8.5) yet needs no lookup, while "explain marginal revenue"
matches less (5.5) and needs one. Intent, not similarity, decides.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .errors import WikiError
from .retrieval import SearchResult, search

CHAT_PASSAGES = 4
MIN_MATCH_SCORE = 4.0  # below this a question is treated as general conversation

_SOCIAL = re.compile(r"^\s*(hi|hello|hey|thanks|thank you|thx|ok|okay|cool|great|nice|bye|goodbye|good (morning|evening|afternoon))\b")
_META = re.compile(
    r"\bwhat (can|could|do) (you|we|i)\b|\bwhat do you do\b|\bwho are you\b|\bwhat are you\b|\bhow (do|does) (you|this) work\b"
    r"|\b(your|the) (name|purpose|commands|capabilities|features)\b|^\s*help\s*[!?.]*\s*$|\bwhat can i (ask|do|use)\b",
    re.IGNORECASE,
)
_FOLLOW_UP = re.compile(
    r"\b(shorter|longer|shorten|lengthen|rewrite|rephrase|reword|simplif\w+|expand|elaborate|translate|continue|again|redo"
    r"|more (formal|casual|concise|detail)|less formal|tl;?dr)\b|\bmake (it|that|this|them)\b|\bturn (it|that|this) into\b",
    re.IGNORECASE,
)
_NOTE_REFERENCE = re.compile(
    r"\b(my|the|these|those) (notes?|wiki|lectures?|slides?|documents?|docs?|summar(y|ies)|cases?|sources?)\b"
    r"|\baccording to\b|\bwhat did (i|the (lecture|professor|notes))\b|\blecture \d+\b|\bfrom (the|my) (notes|lectures?)\b",
    re.IGNORECASE,
)
_CREATIVE = re.compile(
    r"^\s*(please )?((can|could|would) you )?(help me )?(draft|write|compose|brainstorm|plan|schedule|outline|suggest|create"
    r"|generate|prepare|come up with|give me (some )?(ideas|tips|advice))\b"
    r"|\bhelp me (plan|write|draft|prepare|decide|choose|organi[sz]e|study|revise)\b|\bany (advice|tips|ideas)\b"
    r"|\bi (feel|am|'m) (stressed|worried|anxious|nervous|overwhelmed)\b",
    re.IGNORECASE,
)
_QUESTION = re.compile(
    r"^\s*(what|why|how|when|where|which|who|explain|define|describe|compare|summari[sz]e|tell me about|is|are|does|do|did|can)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Route:
    retrieve: bool
    reason: str  # shown to the user: the harness explains what it decided
    results: tuple[SearchResult, ...] = ()
    about_assistant: bool = False  # the message asks what the assistant can do: attach the real capability list


def decide_route(message: str, index_path: Path, *, has_history: bool = False, force_notes: bool = False,
                 limit: int = CHAT_PASSAGES) -> Route:
    """Decide whether to search the notes for `message`, and do the search if so."""
    text = message.strip()
    if force_notes:
        return _search(text, index_path, limit, "you asked for the notes (/notes)", must_match=False)
    if len(text.split()) <= 8 and "?" not in text and _SOCIAL.match(text):
        return Route(False, "conversation: greeting or thanks")
    if _META.search(text):
        return Route(False, "conversation: a question about the assistant itself", about_assistant=True)
    if has_history and _FOLLOW_UP.search(text) and not _NOTE_REFERENCE.search(text):
        return Route(False, "conversation: a follow-up on the previous reply")
    if _NOTE_REFERENCE.search(text):
        return _search(text, index_path, limit, "you referred to your notes", must_match=False)
    if _CREATIVE.search(text):
        return Route(False, "conversation: a drafting, planning or brainstorming request")
    if _QUESTION.match(text) or text.endswith("?"):
        return _search(text, index_path, limit, "a question about course content", must_match=True)
    return Route(False, "conversation: no notes needed")


def _search(text: str, index_path: Path, limit: int, why: str, must_match: bool) -> Route:
    try:
        results = tuple(search(index_path, text, limit))
    except WikiError as error:
        if "meaningful word" in str(error):  # only stopwords: nothing to look up
            return Route(False, "conversation: nothing specific to look up")
        raise
    if not results:
        return Route(False, f"searched ({why}) but nothing matched")
    if must_match and results[0].score < MIN_MATCH_SCORE:
        return Route(False, f"searched ({why}) but the best match was too weak (score {results[0].score:.1f})")
    return Route(True, f"notes searched: {why}; best match score {results[0].score:.1f}", results)
