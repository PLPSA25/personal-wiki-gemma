"""Split a source's text into short passages that keep their source name, section and line range.

Why: Gemma reads a limited amount of text at once, and short passages let us find and cite exactly
the relevant part of a source. Passages follow the document's own structure (headings, then
paragraphs) and are never longer than `max_chars`, except when a single word is longer.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

DEFAULT_MAX_CHARS = 1200

_HEADING = re.compile(r"^(#{1,3})\s+(.+?)\s*$")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


@dataclass(frozen=True)
class Chunk:
    """One passage of a source. Lines refer to the text returned by extract.read_source."""

    source: str  # file name inside vault/raw, e.g. "Economics Lectures.md"
    section: str  # nearest heading above the passage, e.g. "Lecture 5: Introduction to Monopoly"
    index: int  # 1-based position within the source
    text: str
    start_line: int
    end_line: int

    @property
    def chunk_id(self) -> str:
        return f"{self.source}#{self.index}"

    @property
    def label(self) -> str:
        """Human-readable location used in citations."""
        return f"{self.source} > {self.section}"


@dataclass(frozen=True)
class _Paragraph:
    section: str
    text: str
    start_line: int
    end_line: int


def chunk_text(source: str, text: str, max_chars: int = DEFAULT_MAX_CHARS) -> list[Chunk]:
    """Split `text` (from the file named `source`) into passages of at most `max_chars` characters."""
    if max_chars < 100:
        raise ValueError("max_chars must be at least 100")
    default_section = source.rsplit(".", 1)[0]
    chunks: list[Chunk] = []
    pending: list[_Paragraph] = []

    def flush() -> None:
        if pending:
            joined = "\n\n".join(p.text for p in pending)
            chunks.append(Chunk(source, pending[0].section, len(chunks) + 1, joined,
                                pending[0].start_line, pending[-1].end_line))
            pending.clear()

    for paragraph in _paragraphs(text, default_section):
        for piece in _fit(paragraph, max_chars):
            same_section = pending and pending[0].section == piece.section
            size = sum(len(p.text) + 2 for p in pending) + len(piece.text)
            if pending and (not same_section or size > max_chars):
                flush()
            pending.append(piece)
    flush()
    return chunks


def _paragraphs(text: str, default_section: str):
    """Yield paragraphs (blocks separated by blank lines) tagged with their nearest heading."""
    section = default_section
    lines: list[str] = []
    start = 0

    def close(end_line: int):
        block = "\n".join(lines).strip()
        lines.clear()
        return _Paragraph(section, block, start, end_line) if block else None

    for number, line in enumerate(text.splitlines(), start=1):
        heading = _HEADING.match(line)
        if heading or not line.strip():
            done = close(number - 1)
            if done:
                yield done
            if heading:
                section = heading.group(2)
        else:
            if not lines:
                start = number
            lines.append(line.rstrip())
    done = close(len(text.splitlines()))
    if done:
        yield done


def _fit(paragraph: _Paragraph, max_chars: int) -> list[_Paragraph]:
    """Return the paragraph itself, or sentence-based pieces if it is longer than max_chars."""
    if len(paragraph.text) <= max_chars:
        return [paragraph]
    pieces, current = [], ""
    for sentence in _SENTENCE_END.split(paragraph.text):
        for part in _hard_split(sentence, max_chars):
            if current and len(current) + 1 + len(part) > max_chars:
                pieces.append(current)
                current = part
            else:
                current = f"{current} {part}".strip()
    if current:
        pieces.append(current)
    return [_Paragraph(paragraph.section, piece, paragraph.start_line, paragraph.end_line) for piece in pieces]


def _hard_split(sentence: str, max_chars: int) -> list[str]:
    """Split an over-long sentence on spaces (last resort; keeps every word)."""
    if len(sentence) <= max_chars:
        return [sentence]
    parts, current = [], ""
    for word in sentence.split(" "):
        if current and len(current) + 1 + len(word) > max_chars:
            parts.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    if current:
        parts.append(current)
    return parts
