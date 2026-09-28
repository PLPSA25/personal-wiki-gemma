"""Find the original sources in vault/raw and turn them into passages. Sources are only ever read."""

from __future__ import annotations

import hashlib
from pathlib import Path

from .chunk import Chunk, DEFAULT_MAX_CHARS, chunk_text
from .errors import SourceError
from .extract import SUPPORTED_SUFFIXES, read_source


def list_sources(raw_dir: Path) -> list[Path]:
    """Supported files directly inside `raw_dir`, sorted by name."""
    if not raw_dir.is_dir():
        raise SourceError(f"Source folder not found: {raw_dir}")
    files = [p for p in raw_dir.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES]
    return sorted(files, key=lambda p: p.name.lower())


def file_sha256(path: Path) -> str:
    """Fingerprint used to notice whether a source changed since the last ingest."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 16), b""):
            digest.update(block)
    return digest.hexdigest()


def load_chunks(raw_dir: Path, max_chars: int = DEFAULT_MAX_CHARS) -> list[Chunk]:
    """Read every source in `raw_dir` and return all of their passages."""
    chunks: list[Chunk] = []
    for path in list_sources(raw_dir):
        chunks.extend(chunk_text(path.name, read_source(path), max_chars))
    return chunks
