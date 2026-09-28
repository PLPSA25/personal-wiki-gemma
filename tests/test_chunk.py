import pytest

from wiki.chunk import chunk_text

DOC = "# Title\n\n## Alpha\n\nfirst para\n\n## Beta\n\nsecond para"


def test_each_heading_starts_its_own_chunk_with_that_section():
    chunks = chunk_text("Doc.md", DOC)
    assert [(c.section, c.text) for c in chunks] == [("Alpha", "first para"), ("Beta", "second para")]


def test_chunks_are_numbered_and_carry_source_and_lines():
    first, second = chunk_text("Doc.md", DOC)
    assert (first.index, first.chunk_id, first.start_line, first.end_line) == (1, "Doc.md#1", 5, 5)
    assert (second.index, second.start_line, second.end_line) == (2, 9, 9)
    assert second.label == "Doc.md > Beta"


def test_small_paragraphs_in_one_section_are_packed_together():
    text = "## S\n\none\n\ntwo\n\nthree"
    (chunk,) = chunk_text("D.md", text)
    assert chunk.text == "one\n\ntwo\n\nthree"
    assert (chunk.start_line, chunk.end_line) == (3, 7)


def test_chunks_never_mix_sections():
    text = "## A\n\nshort\n\n## B\n\nshort too"
    assert len(chunk_text("D.md", text)) == 2


def test_wrapped_lines_of_one_paragraph_stay_together():
    (chunk,) = chunk_text("D.md", "## S\n\nline one\nline two")
    assert chunk.text == "line one\nline two"


def test_long_paragraph_is_split_at_sentences_within_the_limit():
    sentences = [f"This is sentence number {i} of a long paragraph." for i in range(40)]
    chunks = chunk_text("D.md", "## S\n\n" + " ".join(sentences), max_chars=300)
    assert len(chunks) > 3
    assert all(len(c.text) <= 300 for c in chunks)
    assert all(c.text.endswith(".") for c in chunks)  # cut at sentence ends, not mid-sentence


def test_no_words_are_lost_when_splitting():
    words = [f"w{i}" for i in range(500)]
    chunks = chunk_text("D.md", "## S\n\n" + " ".join(words), max_chars=200)  # no punctuation at all
    assert all(len(c.text) <= 200 for c in chunks)
    assert " ".join(c.text for c in chunks).split() == words


def test_text_without_headings_uses_the_file_name_as_section():
    (chunk,) = chunk_text("Group Pricing.docx", "Just a paragraph.")
    assert chunk.section == "Group Pricing"


def test_empty_text_gives_no_chunks():
    assert chunk_text("D.md", "") == []
    assert chunk_text("D.md", "\n\n   \n") == []


def test_same_input_gives_same_chunks():
    assert chunk_text("D.md", DOC) == chunk_text("D.md", DOC)


def test_tiny_max_chars_is_rejected():
    with pytest.raises(ValueError):
        chunk_text("D.md", DOC, max_chars=10)
