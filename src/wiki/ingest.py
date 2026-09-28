"""Ingest: turn the original sources into linked wiki notes with the local model.

For every page in the plan the harness (1) gathers the relevant passages from the search index,
(2) asks Gemma to write the note as JSON, (3) validates everything Gemma wrote (citations, figures,
links) and (4) writes the file. The plan decides which notes exist; Gemma only writes their text.
Re-running is safe: a note is regenerated only when its inputs changed, and a note the student has
reviewed or edited is never overwritten unless --force is given (the old version is backed up).
"""

from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

from .citations import unsupported_figures
from .config import Paths
from .errors import WikiError
from .index import build_index
from .llm import LanguageModel
from .plan import Concept, Plan
from .prompts import format_passages, load_instructions, passage_label
from .retrieval import SearchResult, search
from .sources import file_sha256
from .vault import (CATALOG_NAME, INDEX_NAME, STATUS_REVIEWED, KeyPoint, NoteContent, Related, SourceRef,
                    note_path, parse_note, read_pages, render_catalog, render_index, render_note, sanitize_line,
                    text_sha256, dump_frontmatter)

INGEST_INSTRUCTIONS_FILE = "ingest-instructions.md"
NOTE_FORMAT = 3  # bump when the structure of a generated note changes, so untouched drafts are regenerated
TEMPERATURE, MAX_TOKENS, SEED = 0.2, 1200, 7
MAX_POINTS, MAX_RELATED = 6, 4
LINK_CANDIDATES = 6  # at most this many notes are offered to the model as possible links

NOTE_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "key_points": {"type": "array", "items": {
            "type": "object",
            "properties": {"text": {"type": "string"}, "cite": {"type": "array", "items": {"type": "string"}}},
            "required": ["text", "cite"]}},
        "related": {"type": "array", "items": {
            "type": "object",
            "properties": {"title": {"type": "string"}, "reason": {"type": "string"}},
            "required": ["title", "reason"]}},
    },
    "required": ["summary", "key_points", "related"],
}


class NoteError(WikiError):
    """The model's note is unusable (bad JSON, unsupported claims...). The reason is fed back once."""


@dataclass
class PageOutcome:
    title: str
    status: str  # written | up to date | needs attention | failed
    detail: str = ""
    seconds: float = 0.0
    dropped: list[str] = field(default_factory=list)


@dataclass
class IngestReport:
    outcomes: list[PageOutcome]
    seconds: float
    indexed_passages: int
    unplanned_sources: list[str]


# ---------------------------------------------------------------- gathering evidence

def gather_passages(concept: Concept, index_path: Path) -> list[SearchResult]:
    """The passages Gemma will see: best matches, plus at least one from each `also_from` file."""
    chosen = search(index_path, concept.query, concept.limit, concept.sources or None)
    present = {r.chunk.chunk_id for r in chosen}
    for source in concept.also_from:
        if any(r.chunk.source == source for r in chosen):
            continue
        for extra in search(index_path, concept.query, 1, [source]):
            if extra.chunk.chunk_id not in present:
                chosen.append(extra)
                present.add(extra.chunk.chunk_id)
    # Renumber so labels are S1..Sn in the order the model sees them.
    return [SearchResult(rank, r.score, r.chunk) for rank, r in enumerate(chosen, start=1)]


def _ref(result: SearchResult) -> SourceRef:
    chunk = result.chunk
    return SourceRef(chunk.source, chunk.section, chunk.start_line, chunk.end_line, chunk.chunk_id)


def build_messages(instructions: str, concept: Concept, passages: list[SearchResult], other_titles: list[str]) -> list[dict]:
    user = (
        f"Concept: {concept.title}\n\n"
        f"Other notes you may link to (copy titles exactly): {'; '.join(other_titles) or '(none)'}\n\n"
        f"Source passages:\n\n{format_passages(passages)}"
    )
    return [{"role": "system", "content": instructions}, {"role": "user", "content": user}]


def fingerprint(concept: Concept, passages: list[SearchResult], instructions: str, model_name: str,
                other_titles: list[str]) -> str:
    """Changes whenever anything that shapes the note changes: passages, plan entry, instructions, model, link targets."""
    payload = {
        "concept": [concept.title, concept.topic, concept.query, concept.sources, concept.also_from, concept.limit],
        "passages": [[r.chunk.chunk_id, text_sha256(r.chunk.text)] for r in passages],
        "instructions": text_sha256(instructions), "model": model_name, "links": other_titles, "format": NOTE_FORMAT,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------- validating the model's note

def parse_reply(text: str) -> dict:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        raise NoteError(f"the reply was not valid JSON ({error.msg})") from error
    if not isinstance(data, dict) or not isinstance(data.get("summary"), str):
        raise NoteError("the JSON has no text 'summary'")
    if not isinstance(data.get("key_points"), list) or not isinstance(data.get("related", []), list):
        raise NoteError("'key_points' and 'related' must be lists")
    return data


def validate_note(data: dict, passages: list[SearchResult], other_titles: list[str],
                  required_sources: tuple[str, ...] = ()) -> tuple[NoteContent, list[str]]:
    """Check every claim against the passages. Returns the usable note and what was dropped and why.

    `required_sources` are files whose passages the note must actually use (at least one key point cites them).
    """
    by_label = {passage_label(r.rank): r for r in passages}
    all_text = " ".join(r.chunk.text for r in passages)
    dropped: list[str] = []

    summary = sanitize_line(data["summary"], 700)
    if len(summary) < 40:
        raise NoteError("the summary is missing or too short")
    if bad := unsupported_figures(summary, all_text):
        raise NoteError(f"the summary contains figures that are not in the passages: {', '.join(bad)}")

    points: list[KeyPoint] = []
    for item in data["key_points"]:
        if not isinstance(item, dict):
            continue
        text = sanitize_line(item.get("text", ""), 400)
        labels = [label for label in item.get("cite", []) if isinstance(label, str) and label in by_label]
        if len(text) < 15 or not labels:
            dropped.append(f"key point without a valid citation: {text[:60]!r}")
            continue
        evidence = " ".join(by_label[label].chunk.text for label in labels)
        if bad := unsupported_figures(text, evidence):
            dropped.append(f"key point with figures not in its cited passage ({', '.join(bad)}): {text[:60]!r}")
            continue
        points.append(KeyPoint(text, tuple(_ref(by_label[label]) for label in dict.fromkeys(labels))))
        if len(points) == MAX_POINTS:
            break
    if len(points) < 2:
        raise NoteError(f"fewer than 2 key points survived validation ({'; '.join(dropped) or 'none were usable'})")
    used = {ref.source for point in points for ref in point.refs}
    if unused := [name for name in required_sources if name not in used]:
        raise NoteError(f"no key point uses the passage from {', '.join(unused)}; add a key point that "
                        "describes what that document says, citing its passage")

    allowed = {title.lower(): title for title in other_titles}
    related: list[Related] = []
    for item in data.get("related", []):
        if not isinstance(item, dict):
            continue
        title = allowed.get(sanitize_line(item.get("title", ""), 80).lower())
        reason = sanitize_line(item.get("reason", ""), 220)
        if title is None or len(reason) < 10:
            dropped.append(f"related link not in the plan: {str(item.get('title'))[:40]!r}")
        elif all(r.title != title for r in related) and len(related) < MAX_RELATED:
            related.append(Related(title, reason))
    used = {ref.chunk_id: ref for point in points for ref in point.refs}  # only passages a key point actually cites
    return NoteContent(summary, tuple(points), tuple(related), tuple(used.values())), dropped


def write_note(model: LanguageModel, messages: list[dict], passages: list[SearchResult],
               other_titles: list[str], required_sources: tuple[str, ...] = ()) -> tuple[NoteContent, list[str], float]:
    """Ask the model for a note; if it is unusable, tell it why and ask once more."""
    total, prompt, last_error = 0.0, messages, "unknown problem"
    for _attempt in range(2):
        reply = model.chat(prompt, temperature=TEMPERATURE, max_tokens=MAX_TOKENS, seed=SEED, response_format=NOTE_SCHEMA)
        total += reply.seconds
        try:
            content, dropped = validate_note(parse_reply(reply.text), passages, other_titles, required_sources)
            return content, dropped, total
        except NoteError as error:
            last_error = str(error)
            prompt = messages + [
                {"role": "assistant", "content": reply.text},
                {"role": "user", "content": f"That JSON was rejected because {last_error}. "
                                            "Write the note again, fixing exactly that, using only the passages."},
            ]
    raise NoteError(last_error)


def link_candidates(title: str, evidence: dict[str, set[str]], limit: int = LINK_CANDIDATES) -> list[str]:
    """Notes that share evidence with `title`: the only pages the model may link to.

    `evidence` maps every page title to the ids of the passages gathered for it. Two notes that are built
    from the same passages are about connected ideas; a link chosen this way rests on shared sources, not on
    how plausible a title sounds. Pages with no overlap are simply not offered.
    """
    mine = evidence[title]
    shared = [(len(mine & ids), other) for other, ids in evidence.items() if other != title and mine & ids]
    return [other for _count, other in sorted(shared, key=lambda item: (-item[0], item[1]))[:limit]]


# ---------------------------------------------------------------- the orchestration

def existing_state(path: Path, new_fingerprint: str) -> str:
    """absent | up to date | stale (safe to regenerate) | protected (reviewed or edited) | unmanaged (not ours)."""
    if not path.is_file():
        return "absent"
    parsed = parse_note(path.read_text(encoding="utf-8"))
    if parsed is None or "fingerprint" not in parsed[0]:
        return "unmanaged"
    meta, body = parsed
    if meta["fingerprint"] == new_fingerprint:
        return "up to date"
    edited = text_sha256(body) != meta.get("body_sha256")
    return "protected" if meta.get("status") == STATUS_REVIEWED or edited else "stale"


def ingest(plan: Plan, paths: Paths, model: LanguageModel, only: list[str] | None = None, force: bool = False,
           progress: Callable[[str], None] = print) -> IngestReport:
    started = time.perf_counter()
    missing = [s.file for s in plan.sources if not (paths.raw_dir / s.file).is_file()]
    if missing:
        raise WikiError(f"The plan lists sources that are not in {paths.raw_dir}: {', '.join(missing)}")
    instructions = load_instructions(paths.prompts_dir, INGEST_INSTRUCTIONS_FILE)
    indexed = build_index(paths.raw_dir, paths.index_path)  # keeps `wiki search` and `wiki ask` in step with raw/
    planned_files = {s.file for s in plan.sources}
    unplanned = sorted({s.name for s in indexed} - planned_files)

    wanted = {t.lower() for t in only} if only else None
    if wanted and (unknown := wanted - {t.lower() for t in plan.titles()}):
        raise WikiError(f"Not in the plan: {', '.join(sorted(unknown))}")
    concepts = [c for c in plan.concepts if wanted is None or c.title.lower() in wanted]
    identity = model.identity()
    model_label = f"{identity.get('model', model.name)} ({identity.get('quantization', 'unknown quantization')})"

    evidence = {c.title: {r.chunk.chunk_id for r in gather_passages(c, paths.index_path)} for c in plan.concepts}
    outcomes = []
    for number, concept in enumerate(concepts, start=1):
        candidates = link_candidates(concept.title, evidence)
        outcome = _ingest_one(concept, candidates, paths, model, instructions, model_label, force)
        outcomes.append(outcome)
        progress(f"[{number}/{len(concepts)}] {concept.title}: {outcome.status}"
                 f"{' - ' + outcome.detail if outcome.detail else ''} ({outcome.seconds:.0f} s)")

    _write_landing_pages(plan, paths)
    return IngestReport(outcomes, time.perf_counter() - started, sum(s.passages for s in indexed), unplanned)


def _ingest_one(concept: Concept, other_titles: list[str], paths: Paths, model: LanguageModel, instructions: str,
                model_label: str, force: bool) -> PageOutcome:
    """`other_titles` are the link candidates for this note (see link_candidates)."""
    started = time.perf_counter()
    try:
        passages = gather_passages(concept, paths.index_path)
        if not passages:
            return PageOutcome(concept.title, "failed", "no passage matched the plan's query", time.perf_counter() - started)
        path = note_path(paths.wiki_dir, concept.topic, concept.title)
        new_fingerprint = fingerprint(concept, passages, instructions, model_label, other_titles)
        state = existing_state(path, new_fingerprint)
        if state == "up to date":
            return PageOutcome(concept.title, "up to date", "", time.perf_counter() - started)
        if state == "unmanaged" or (state == "protected" and not force):
            reason = ("a file with this name exists that this program did not write" if state == "unmanaged" else
                      "inputs changed but the note was reviewed or edited; run with --force to regenerate (old version is backed up)")
            return PageOutcome(concept.title, "needs attention", reason, time.perf_counter() - started)

        messages = build_messages(instructions, concept, passages, other_titles)
        present = {r.chunk.source for r in passages}
        required = tuple(name for name in concept.also_from if name in present)  # only if a passage was found
        content, dropped, _ = write_note(model, messages, passages, other_titles, required)
        meta = {"generated_by": model_label, "generated_at": date.today().isoformat(), "fingerprint": new_fingerprint}
        text, _body = render_note(concept.title, concept.topic, content, meta)
        if path.is_file():
            _back_up(path, paths)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return PageOutcome(concept.title, "written", f"{len(passages)} passages, {len(content.key_points)} key points, "
                           f"{len(content.related)} links", time.perf_counter() - started, dropped)
    except NoteError as error:  # a ModelError (server down) is not caught: it stops the whole run at once
        return PageOutcome(concept.title, "failed", str(error), time.perf_counter() - started)


def _back_up(path: Path, paths: Paths) -> None:
    target = paths.backup_dir / path.parent.name / f"{path.stem} {datetime.now():%Y%m%d-%H%M%S}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")


def _write_landing_pages(plan: Plan, paths: Paths) -> None:
    """index.md and the source catalog are built by code from the notes that exist on disk."""
    pages = read_pages(paths.wiki_dir)
    topic_order = list(dict.fromkeys(c.topic for c in plan.concepts))
    (paths.vault_dir / INDEX_NAME).write_text(render_index(pages, topic_order), encoding="utf-8")
    hashes = {s.file: file_sha256(paths.raw_dir / s.file) for s in plan.sources}
    (paths.vault_dir / CATALOG_NAME).write_text(render_catalog(plan.sources, hashes, pages), encoding="utf-8")


def approve(paths: Paths, titles: list[str] | None) -> list[str]:
    """Mark notes as reviewed (all of them if `titles` is None). Returns the titles that changed."""
    wanted = {t.lower() for t in titles} if titles is not None else None
    found: set[str] = set()
    changed: list[str] = []
    for path in sorted(paths.wiki_dir.rglob("*.md")):
        parsed = parse_note(path.read_text(encoding="utf-8"))
        if parsed is None or "fingerprint" not in parsed[0]:
            continue  # not one of our notes
        meta, body = parsed
        title = str(meta["title"])
        if wanted is not None and title.lower() not in wanted:
            continue
        found.add(title.lower())
        if meta.get("status") == STATUS_REVIEWED and meta.get("body_sha256") == text_sha256(body):
            continue  # already approved and untouched since
        meta["status"] = STATUS_REVIEWED
        meta["body_sha256"] = text_sha256(body)  # what was reviewed is exactly what is on disk now
        path.write_text(dump_frontmatter(meta) + "\n" + body, encoding="utf-8")
        changed.append(title)
    if wanted is not None and (missing := wanted - found):
        raise WikiError(f"No such note: {', '.join(sorted(missing))}")
    return changed
