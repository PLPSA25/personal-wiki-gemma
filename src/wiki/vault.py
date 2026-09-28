"""The Obsidian vault: note files, links, index.md and the source catalog.

All bookkeeping is done by code, never by the model: file names come from the plan, links are only made
to notes that exist, and every piece of model-written text is sanitised before it reaches a file.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from .errors import WikiError
from .plan import Plan, SourceInfo

INDEX_NAME = "index.md"
CATALOG_NAME = "Source Catalog.md"
STATUS_DRAFT, STATUS_REVIEWED = "draft", "reviewed"

_TAG = re.compile(r"<[A-Za-z/!][^>]*>")
_LECTURE = re.compile(r"(Lecture \d+)")
_FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n?(.*)\Z", re.DOTALL)


@dataclass(frozen=True)
class SourceRef:
    """One passage a note used: where it came from."""

    source: str
    section: str
    start_line: int
    end_line: int
    chunk_id: str


@dataclass(frozen=True)
class KeyPoint:
    text: str
    refs: tuple[SourceRef, ...]


@dataclass(frozen=True)
class Related:
    title: str
    reason: str


@dataclass(frozen=True)
class NoteContent:
    """A validated note, ready to be written."""

    summary: str
    key_points: tuple[KeyPoint, ...]
    related: tuple[Related, ...]
    passages: tuple[SourceRef, ...]  # every passage the model was given


@dataclass(frozen=True)
class PageInfo:
    """What the index and catalog need to know about a note that is already on disk."""

    title: str
    topic: str
    description: str
    status: str
    source_files: tuple[str, ...]


def sanitize_line(text: str, limit: int) -> str:
    """One safe line of plain text from model output: no HTML, no wiki-link syntax, no control characters."""
    text = _TAG.sub("", str(text))
    text = text.replace("[[", "[").replace("]]", "]")
    text = "".join(ch if ch.isprintable() else " " for ch in text)
    text = re.sub(r"\s+", " ", text).strip().lstrip("#>*-+ ")
    return text[:limit].rstrip()


def note_path(wiki_dir: Path, topic: str, title: str) -> Path:
    """Where a note lives. The result is guaranteed to be inside `wiki_dir`."""
    path = (wiki_dir / topic / f"{title}.md").resolve()
    if wiki_dir.resolve() not in path.parents:
        raise WikiError(f"Refusing to write outside the wiki folder: {topic}/{title}")
    return path


def _short_section(section: str) -> str:
    match = _LECTURE.match(section)
    return match.group(1) if match else section


def source_link(source: str, section: str | None = None) -> str:
    """Obsidian link to an original in raw/. Markdown files link by name, other files keep their extension."""
    stem = source[:-3] if source.lower().endswith(".md") else source
    label = stem.removesuffix(".docx")
    if section and _short_section(section) != label:  # a document without headings has no separate section name
        label = f"{label}, {_short_section(section)}"
    label = re.sub(r"[|\[\]]", " ", label)
    return f"[[raw/{stem}|{label}]]"


def _citation(refs: tuple[SourceRef, ...]) -> str:
    seen, links = set(), []
    for ref in refs:
        key = (ref.source, _short_section(ref.section))
        if key not in seen:
            seen.add(key)
            links.append(source_link(ref.source, ref.section))
    return " (" + "; ".join(links) + ")" if links else ""


def render_note(title: str, topic: str, content: NoteContent, meta: dict) -> tuple[str, str]:
    """Return (full file text, body text). `meta` is extra frontmatter (fingerprint, model, date...)."""
    lines = [f"# {title}", "", content.summary, "", "## Key points", ""]
    lines += [f"- {point.text}{_citation(point.refs)}" for point in content.key_points]
    lines += ["", "## Related notes", ""]
    lines += [f"- [[{item.title}]] - {item.reason}" for item in content.related] or ["- (none identified)"]
    lines += ["", "## Sources", ""]
    ordered = sorted(content.passages, key=lambda ref: (ref.source.lower(), ref.start_line))
    lines += [f"- {source_link(ref.source)} - {ref.section} (lines {ref.start_line}-{ref.end_line})" for ref in ordered]
    body = "\n".join(lines) + "\n"

    front = {
        "title": title,
        "topic": topic,
        "status": STATUS_DRAFT,
        "description": first_sentence(content.summary),
        "source_files": sorted({ref.source for ref in content.passages}),
        "source_passages": [ref.chunk_id for ref in content.passages],
        **meta,
        "body_sha256": text_sha256(body),
    }
    return dump_frontmatter(front) + "\n" + body, body


def dump_frontmatter(data: dict) -> str:
    return "---\n" + yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=1000) + "---\n"


def parse_note(text: str) -> tuple[dict, str] | None:
    """Split a note into (frontmatter dict, body). None if it has no readable frontmatter (not one of ours)."""
    match = _FRONTMATTER.match(text.replace("\r\n", "\n"))
    if not match:
        return None
    try:
        meta = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None
    return (meta, match.group(2).lstrip("\n")) if isinstance(meta, dict) else None


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def first_sentence(text: str, limit: int = 180) -> str:
    sentence = re.split(r"(?<=[.!?])\s", text.strip(), maxsplit=1)[0]
    if len(sentence) <= limit:
        return sentence
    cut = sentence[: limit - 3]
    if " " in cut:  # end on a whole word, never in the middle of one
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip(" ,;:") + "..."


def read_pages(wiki_dir: Path) -> list[PageInfo]:
    """All notes in the wiki that carry our frontmatter."""
    pages = []
    for path in sorted(wiki_dir.rglob("*.md")):
        parsed = parse_note(path.read_text(encoding="utf-8"))
        if parsed is None or "title" not in parsed[0]:
            continue
        meta = parsed[0]
        pages.append(PageInfo(str(meta["title"]), str(meta.get("topic", "")), str(meta.get("description", "")),
                              str(meta.get("status", STATUS_DRAFT)), tuple(meta.get("source_files", ()))))
    return pages


def render_index(pages: list[PageInfo], topic_order: list[str]) -> str:
    lines = [
        "# Study Wiki", "",
        "Notes on my MBA Fall A courses: microeconomics (MBA 201A) and Data & Decisions (MBA 200S). "
        "Pick a topic below. Every note ends with the original sources it was written from; "
        f"[[{CATALOG_NAME[:-3]}]] lists all originals.", "",
    ]
    topics = [t for t in topic_order if any(p.topic == t for p in pages)]
    topics += sorted({p.topic for p in pages} - set(topics))
    for topic in topics:
        lines += [f"## {topic}", ""]
        lines += [f"- [[{p.title}]] - {p.description}" for p in sorted(pages, key=lambda p: p.title) if p.topic == topic]
        lines.append("")
    return "\n".join(lines)


def render_catalog(sources: tuple[SourceInfo, ...], hashes: dict[str, str], pages: list[PageInfo]) -> str:
    lines = [
        "# Source Catalog", "",
        "The originals in `raw/` are never changed. Each row shows what an original is, where it came from, its "
        "SHA-256 fingerprint (proof it is unchanged) and the notes that cite it.", "",
        "| Original | What it is | Origin | SHA-256 | Cited by |", "|---|---|---|---|---|",
    ]
    for source in sources:
        stem = source.file[:-3] if source.file.lower().endswith(".md") else source.file
        citing = ", ".join(f"[[{p.title}]]" for p in sorted(pages, key=lambda p: p.title) if source.file in p.source_files)
        lines.append(f"| [[raw/{stem}]] | {_cell(source.description)} | {_cell(source.origin)} | "
                     f"`{hashes.get(source.file, 'missing')[:16]}` | {citing or '-'} |")
    return "\n".join(lines) + "\n"


def _cell(text: str) -> str:
    return text.replace("|", "/").replace("\n", " ")
