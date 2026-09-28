import pytest

from wiki.errors import SourceError, WikiError
from wiki.index import build_index
from wiki.retrieval import build_query, search
from wiki.sources import file_sha256


@pytest.fixture
def library(tmp_path):
    """A tiny vault/raw with two Markdown sources, already indexed. Returns (raw_dir, index_path)."""
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "Statistics.md").write_text(
        "# Statistics\n\n"
        "## Lecture 5: Polling\n\nA plus or minus 3 percentage point poll needs 1,112 people.\n\n"
        "## Lecture 6: Experiments\n\nRandomized experiments reveal causal effects.\n"
    )
    (raw / "Economics.md").write_text(
        "# Economics\n\n"
        "## Lecture 5: Monopoly\n\nA monopolist sets marginal revenue equal to marginal cost.\n\n"
        "## Lecture 3: Supply\n\nA price taker produces where price equals marginal cost.\n"
    )
    index_path = tmp_path / "data" / "index.db"
    build_index(raw, index_path)
    return raw, index_path


def test_most_relevant_passage_ranks_first(library):
    _, index_path = library
    results = search(index_path, "poll margin percentage points")
    assert results[0].rank == 1
    assert results[0].chunk.source == "Statistics.md"
    assert "1,112" in results[0].chunk.text


def test_stemming_matches_word_variants(library):
    _, index_path = library
    assert search(index_path, "monopolists")[0].chunk.section == "Lecture 5: Monopoly"


def test_section_title_matches_count(library):
    _, index_path = library
    assert search(index_path, "experiments")[0].chunk.section == "Lecture 6: Experiments"


def test_results_carry_location_and_are_limited(library):
    _, index_path = library
    results = search(index_path, "marginal cost", limit=1)
    assert len(results) == 1
    chunk = results[0].chunk
    assert (chunk.source, chunk.start_line) == ("Economics.md", 5)
    assert chunk.label == "Economics.md > Lecture 5: Monopoly"


def test_unrelated_words_give_no_results(library):
    _, index_path = library
    assert search(index_path, "penguin volcano") == []


@pytest.mark.parametrize("hostile", [
    '"; DROP TABLE passages; --',
    "poll NEAR(experiments) OR *",
    'section:monopoly AND "unbalanced',
    "poll) OR (",
    "-poll ^experiments",
    "☃ \u0000 poll",
])
def test_special_characters_cannot_break_or_inject_into_the_query(library, hostile):
    _, index_path = library
    before = file_sha256(index_path)
    search(index_path, hostile)  # must not raise
    assert file_sha256(index_path) == before  # opened read-only: the index is untouched


def test_query_with_only_stopwords_is_rejected_with_a_helpful_message(library):
    _, index_path = library
    with pytest.raises(WikiError, match="meaningful word"):
        search(index_path, "what is the")


def test_missing_index_says_how_to_build_it(tmp_path):
    with pytest.raises(WikiError, match="wiki index"):
        search(tmp_path / "nope.db", "poll")


def test_corrupt_index_says_how_to_rebuild_it(tmp_path):
    broken = tmp_path / "index.db"
    broken.write_bytes(b"this is not a sqlite database" * 100)
    with pytest.raises(WikiError, match="damaged"):
        search(broken, "poll")


def test_build_query_drops_stopwords_and_quotes_every_word():
    assert build_query("What is the margin of error?") == '"margin" OR "error"'
    assert build_query("poll poll Poll") == '"poll"'
    assert build_query("the of a") is None


def test_rebuilding_replaces_the_index_and_records_source_hashes(library):
    raw, index_path = library
    (raw / "Statistics.md").write_text("## New\n\nCompletely different words: giraffe.\n")
    indexed = build_index(raw, index_path)
    assert {s.name for s in indexed} == {"Economics.md", "Statistics.md"}
    assert search(index_path, "giraffe")[0].chunk.source == "Statistics.md"
    assert search(index_path, "poll") == []  # old text is gone
    assert {s.name: s.sha256 for s in indexed}["Statistics.md"] == file_sha256(raw / "Statistics.md")


def test_failed_rebuild_keeps_the_previous_index_and_leaves_no_temp_file(library):
    raw, index_path = library
    (raw / "broken.docx").write_text("not a zip")
    with pytest.raises(SourceError):
        build_index(raw, index_path)
    assert search(index_path, "monopolist")  # old index still works
    assert not list(index_path.parent.glob("*.building"))
