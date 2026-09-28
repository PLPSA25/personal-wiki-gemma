"""Build the local keyword index (SQLite FTS5) over the passages of every source.

The index is a machine-generated file kept outside the vault. It is rebuilt from vault/raw in
well under a second, into a temporary file that replaces the old index only when complete, so a
failure half-way (for example a corrupt source) never leaves a broken or half-empty index.
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from .chunk import DEFAULT_MAX_CHARS, chunk_text
from .extract import read_source
from .sources import file_sha256, list_sources

# 'porter unicode61' lowercases and stems words, so "monopolists" also matches "monopolist".
_SCHEMA = """
CREATE VIRTUAL TABLE passages USING fts5(
    section, text,
    source UNINDEXED, idx UNINDEXED, start_line UNINDEXED, end_line UNINDEXED,
    tokenize = 'porter unicode61'
);
CREATE TABLE sources (name TEXT PRIMARY KEY, sha256 TEXT NOT NULL, passages INTEGER NOT NULL);
"""


@dataclass(frozen=True)
class IndexedSource:
    name: str
    sha256: str
    passages: int


def build_index(raw_dir: Path, index_path: Path, max_chars: int = DEFAULT_MAX_CHARS) -> list[IndexedSource]:
    """Index every source in `raw_dir` into `index_path`, replacing any previous index."""
    index_path.parent.mkdir(parents=True, exist_ok=True)
    building = index_path.with_name(index_path.name + ".building")
    building.unlink(missing_ok=True)
    try:
        indexed = _write_index(raw_dir, building, max_chars)
        os.replace(building, index_path)  # atomic: readers see the old index or the new one
    finally:
        building.unlink(missing_ok=True)
    return indexed


def _write_index(raw_dir: Path, target: Path, max_chars: int) -> list[IndexedSource]:
    indexed = []
    with closing(sqlite3.connect(target)) as db:
        db.executescript(_SCHEMA)
        for path in list_sources(raw_dir):
            chunks = chunk_text(path.name, read_source(path), max_chars)
            db.executemany(
                "INSERT INTO passages (section, text, source, idx, start_line, end_line) VALUES (?, ?, ?, ?, ?, ?)",
                [(c.section, c.text, c.source, c.index, c.start_line, c.end_line) for c in chunks],
            )
            source = IndexedSource(path.name, file_sha256(path), len(chunks))
            db.execute("INSERT INTO sources VALUES (?, ?, ?)", (source.name, source.sha256, source.passages))
            indexed.append(source)
        db.commit()
    return indexed
