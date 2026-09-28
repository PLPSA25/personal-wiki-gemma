"""Review helper: find key points whose source link points at the wrong lecture section, and repair them.

For every key point of every note, the words of the point are compared with the passages its link points to. If the point is
poorly covered there but well covered (>= 0.9) by another passage of the same source, the link is re-pointed to that passage and the
note's Sources list and properties are rebuilt from what the key points really cite. Notes are only reported unless --apply is given.
The note's status stays `draft` and its body hash is left unchanged, so it still counts as edited by hand.

Usage: python evals/fix_misattributed_links.py [--apply]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from wiki.config import Paths, default_root
from wiki.chunk import Chunk, chunk_text
from wiki.extract import read_source
from wiki.retrieval import STOPWORDS
from wiki.sources import list_sources
from wiki.vault import dump_frontmatter, parse_note, source_link

LOW, HIGH = 0.75, 0.9
_LINK = re.compile(r"\[\[raw/([^|\]]+)\|([^\]]+)\]\]")


def words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]{4,}", text.lower()) if w not in STOPWORDS}


def coverage(point: str, chunk_texts: list[str]) -> float:
    w = words(point)
    return len(w & words(" ".join(chunk_texts))) / max(1, len(w))


def short(section: str) -> str:
    match = re.match(r"(Lecture \d+)", section)
    return match.group(1) if match else section


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    paths = Paths(default_root())
    chunks: dict[str, Chunk] = {}
    for source in list_sources(paths.raw_dir):
        for chunk in chunk_text(source.name, read_source(source)):
            chunks[chunk.chunk_id] = chunk

    changed_notes = 0
    for path in sorted(paths.wiki_dir.rglob("*.md")):
        meta, body = parse_note(path.read_text(encoding="utf-8"))
        cited = list(meta["source_passages"])
        lines = body.split("\n")
        start = lines.index("## Key points") + 1
        end = lines.index("## Related notes")
        fixed, keep_ids = False, set()
        for i in range(start, end):
            line = lines[i]
            if not line.startswith("- "):
                continue
            point = _LINK.sub("", line[2:]).strip(" ()")
            links = _LINK.findall(line)
            if not links:
                continue
            target, label = links[0]
            source = target if target.endswith(".docx") else target + ".md"
            section = label.split(", ")[1] if ", " in label else None
            pool = [chunks[c] for c in cited if chunks[c].source == source and (section is None or short(chunks[c].section) == section)]
            if coverage(point, [c.text for c in pool]) < LOW:
                best = max((c for c in chunks.values() if c.source == source), key=lambda c: coverage(point, [c.text]))
                if coverage(point, [best.text]) >= HIGH:
                    new_label = label.split(", ")[0] + (f", {short(best.section)}" if section is not None else "")
                    print(f"[{meta['title']}] {point[:70]!r}\n    link {label!r} -> {new_label!r} (passage {best.chunk_id}, lines {best.start_line}-{best.end_line})")
                    lines[i] = line.replace(f"|{label}]]", f"|{new_label}]]")
                    if best.chunk_id not in cited:
                        cited.append(best.chunk_id)
                    pool, fixed = [best], True
            for c in pool:
                if coverage(point, [c.text]) >= LOW:
                    keep_ids.add(c.chunk_id)
        if fixed and args.apply:
            ordered = sorted(keep_ids, key=lambda cid: (chunks[cid].source.lower(), chunks[cid].start_line))
            src_lines = [f"- {source_link(chunks[cid].source)} - {chunks[cid].section} (lines {chunks[cid].start_line}-{chunks[cid].end_line})" for cid in ordered]
            new_body = "\n".join(lines[: lines.index("## Sources") + 2] + src_lines) + "\n"
            meta["source_passages"] = ordered
            meta["source_files"] = sorted({chunks[cid].source for cid in ordered})
            path.write_text(dump_frontmatter(meta) + "\n" + new_body, encoding="utf-8")
            changed_notes += 1
    print(f"{'repaired' if args.apply else 'would repair'} {changed_notes if args.apply else 'the notes above'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
