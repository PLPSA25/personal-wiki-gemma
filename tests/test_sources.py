import hashlib
from pathlib import Path

import pytest

from wiki.chunk import DEFAULT_MAX_CHARS
from wiki.errors import SourceError
from wiki.sources import file_sha256, list_sources, load_chunks

REAL_RAW = Path(__file__).resolve().parents[1] / "vault" / "raw"


def test_list_sources_is_sorted_and_skips_unsupported_files(tmp_path):
    for name in ("b.md", "A.txt", "c.png", "notes.docx"):
        (tmp_path / name).write_bytes(b"x")
    (tmp_path / "folder").mkdir()
    assert [p.name for p in list_sources(tmp_path)] == ["A.txt", "b.md", "notes.docx"]


def test_missing_folder_has_a_clear_message(tmp_path):
    with pytest.raises(SourceError, match="not found"):
        list_sources(tmp_path / "nope")


def test_sha256_matches_hashlib(tmp_path):
    path = tmp_path / "a.md"
    path.write_bytes(b"hello")
    assert file_sha256(path) == hashlib.sha256(b"hello").hexdigest()


def test_load_chunks_reads_markdown_and_docx(tmp_path, make_docx):
    (tmp_path / "one.md").write_text("## Topic\n\nMarkdown text.")
    make_docx([("", "Word text.")], name="two.docx")  # the fixture writes into the same tmp_path
    chunks = load_chunks(tmp_path)
    assert [(c.source, c.text) for c in chunks] == [("one.md", "Markdown text."), ("two.docx", "Word text.")]


def test_load_chunks_does_not_modify_sources(tmp_path):
    path = tmp_path / "one.md"
    path.write_text("## Topic\n\nText.")
    before = file_sha256(path)
    load_chunks(tmp_path)
    assert file_sha256(path) == before


@pytest.mark.skipif(not REAL_RAW.is_dir(), reason="vault/raw not present")
def test_real_sources_are_all_readable_and_chunked_within_the_limit():
    chunks = load_chunks(REAL_RAW)
    sources = {c.source for c in chunks}
    assert len(sources) >= 3
    assert all(0 < len(c.text) <= DEFAULT_MAX_CHARS for c in chunks)
    assert all(c.section for c in chunks)
