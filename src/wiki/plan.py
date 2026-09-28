"""Load and validate the wiki plan (wiki-plan.toml): which pages exist and where their evidence comes from.

Page titles become file names and graph labels, so they are checked strictly here: short, readable,
free of path separators, and unique. Gemma never chooses a title.
"""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

from .errors import WikiError

DEFAULT_PASSAGES = 6
MAX_PASSAGES = 12

# Letters, digits and a few readable symbols; none of the characters Windows forbids in file names.
_TITLE = re.compile(r"[A-Za-z0-9][A-Za-z0-9 ,'&()-]*[A-Za-z0-9)]")
_TOPIC = re.compile(r"[A-Za-z][A-Za-z ]{1,38}[A-Za-z]")


@dataclass(frozen=True)
class SourceInfo:
    file: str
    description: str
    origin: str


@dataclass(frozen=True)
class Concept:
    title: str
    topic: str  # becomes the folder inside vault/wiki
    query: str  # words used to find its passages
    sources: tuple[str, ...] = ()  # if given, passages come only from these files
    also_from: tuple[str, ...] = ()  # files that must contribute at least one passage
    limit: int = DEFAULT_PASSAGES  # passages given to Gemma


@dataclass(frozen=True)
class Plan:
    sources: tuple[SourceInfo, ...]
    concepts: tuple[Concept, ...]

    def titles(self) -> list[str]:
        return [c.title for c in self.concepts]


def load_plan(path: Path) -> Plan:
    """Read wiki-plan.toml. Raises WikiError with a message that names the offending entry."""
    if not path.is_file():
        raise WikiError(f"Wiki plan not found: {path}")
    try:
        raw = path.read_bytes().removeprefix(b"\xef\xbb\xbf")  # Windows editors may add a UTF-8 byte-order mark
        data = tomllib.loads(raw.decode("utf-8"))
    except tomllib.TOMLDecodeError as error:
        raise WikiError(f"The wiki plan {path.name} is not valid TOML: {error}") from error

    sources = tuple(_source(entry) for entry in data.get("source", []))
    known_files = {s.file for s in sources}
    concepts = tuple(_concept(entry, known_files) for entry in data.get("concept", []))
    if not concepts:
        raise WikiError(f"The wiki plan {path.name} lists no [[concept]] pages.")
    _require_unique([s.file for s in sources], "source file")
    _require_unique([c.title.lower() for c in concepts], "page title")
    return Plan(sources, concepts)


def _source(entry: dict) -> SourceInfo:
    try:
        return SourceInfo(str(entry["file"]), str(entry["description"]), str(entry["origin"]))
    except KeyError as error:
        raise WikiError(f"A [[source]] entry in the wiki plan is missing {error}.") from error


def _concept(entry: dict, known_files: set[str]) -> Concept:
    title = str(entry.get("title", "")).strip()
    if not _TITLE.fullmatch(title) or not 2 <= len(title.split()) <= 6 or len(title) > 60:
        raise WikiError(
            f"Invalid page title {title!r}: use 2-6 words made of letters, digits and , ' & ( ) - "
            "(the title becomes the file name)."
        )
    topic = str(entry.get("topic", "")).strip()
    if not _TOPIC.fullmatch(topic):
        raise WikiError(f"Invalid topic {topic!r} for page '{title}': use letters and spaces only (it is a folder name).")
    query = str(entry.get("query", "")).strip()
    if not query:
        raise WikiError(f"Page '{title}' has no query: say which words find its passages.")
    sources = tuple(entry.get("sources", ()))
    also_from = tuple(entry.get("also_from", ()))
    for name in (*sources, *also_from):
        if name not in known_files:
            raise WikiError(f"Page '{title}' refers to '{name}', which is not listed as a [[source]].")
    limit = entry.get("limit", DEFAULT_PASSAGES)
    if not isinstance(limit, int) or not 1 <= limit <= MAX_PASSAGES:
        raise WikiError(f"Page '{title}': limit must be a whole number from 1 to {MAX_PASSAGES}.")
    return Concept(title, topic, query, sources, also_from, limit)


def _require_unique(values: list[str], what: str) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            raise WikiError(f"The wiki plan lists the same {what} twice: {value!r}.")
        seen.add(value)
