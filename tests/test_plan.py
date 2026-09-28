from pathlib import Path

import pytest

from wiki.errors import WikiError
from wiki.plan import load_plan

REPO = Path(__file__).resolve().parents[1]

HEADER = '[[source]]\nfile = "A.md"\ndescription = "d"\norigin = "o"\n\n'


def plan_file(tmp_path, body, header=HEADER):
    path = tmp_path / "wiki-plan.toml"
    path.write_text(header + body, encoding="utf-8")
    return path


def concept(title="Price Theory", topic="Economics", query="price", extra=""):
    return f'[[concept]]\ntitle = "{title}"\ntopic = "{topic}"\nquery = "{query}"\n{extra}\n'


def test_a_valid_plan_loads(tmp_path):
    plan = load_plan(plan_file(tmp_path, concept() + concept("Cost Curves", extra='also_from = ["A.md"]\nlimit = 4')))
    assert plan.titles() == ["Price Theory", "Cost Curves"]
    assert plan.concepts[1].also_from == ("A.md",) and plan.concepts[1].limit == 4
    assert plan.concepts[0].limit == 6  # default


@pytest.mark.parametrize("title", [
    "A/B Testing", "../Evil Page", "Bad:Title Here", "Star * Title", "Quote \" Title", "Pipe | Title",
    "Backslash \\ Title", "OneWord", "One Two Three Four Five Six Seven", " ", "Ends With Dash-", "-Starts Dash",
    "Line\nbreak Title", "Title.md Extra", "x" * 70 + " y",
])
def test_unsafe_or_unreadable_titles_are_rejected(tmp_path, title):
    with pytest.raises(WikiError, match="Invalid page title"):
        load_plan(plan_file(tmp_path, concept(title.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n"))))


@pytest.mark.parametrize("title", ["Long-Run Competition", "Type I and Type II Errors", "Two-Part Tariffs", "Rock & Roll"])
def test_readable_titles_with_common_punctuation_are_allowed(tmp_path, title):
    assert load_plan(plan_file(tmp_path, concept(title))).titles() == [title]


@pytest.mark.parametrize("topic", ["../x", "Eco/nomics", "E", "Topic1", ""])
def test_topics_must_be_plain_folder_names(tmp_path, topic):
    with pytest.raises(WikiError, match="Invalid topic"):
        load_plan(plan_file(tmp_path, concept(topic=topic)))


def test_duplicate_titles_are_rejected_ignoring_case(tmp_path):
    with pytest.raises(WikiError, match="same page title twice"):
        load_plan(plan_file(tmp_path, concept("Price Theory") + concept("price theory")))


def test_duplicate_sources_are_rejected(tmp_path):
    with pytest.raises(WikiError, match="same source file twice"):
        load_plan(plan_file(tmp_path, concept(), header=HEADER + HEADER))


def test_concepts_may_only_use_listed_sources(tmp_path):
    with pytest.raises(WikiError, match="not listed as a"):
        load_plan(plan_file(tmp_path, concept(extra='sources = ["Other.md"]')))


@pytest.mark.parametrize("extra", ["limit = 0", "limit = 99", 'limit = "many"'])
def test_limit_must_be_a_sensible_whole_number(tmp_path, extra):
    with pytest.raises(WikiError, match="limit"):
        load_plan(plan_file(tmp_path, concept(extra=extra)))


def test_a_concept_needs_a_query(tmp_path):
    with pytest.raises(WikiError, match="no query"):
        load_plan(plan_file(tmp_path, concept(query="  ")))


def test_a_plan_saved_with_a_windows_byte_order_mark_still_loads(tmp_path):
    """PowerShell's Set-Content -Encoding utf8 and old Notepad versions add a BOM; the demo script hit exactly this."""
    path = plan_file(tmp_path, concept())
    path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes())
    assert load_plan(path).titles() == ["Price Theory"]


def test_a_plan_without_concepts_and_broken_files_are_clear_errors(tmp_path):
    with pytest.raises(WikiError, match="no \\[\\[concept\\]\\]"):
        load_plan(plan_file(tmp_path, ""))
    bad = tmp_path / "bad.toml"
    bad.write_text("this is = = not toml")
    with pytest.raises(WikiError, match="not valid TOML"):
        load_plan(bad)
    with pytest.raises(WikiError, match="not found"):
        load_plan(tmp_path / "missing.toml")


def test_a_source_entry_must_be_complete(tmp_path):
    with pytest.raises(WikiError, match="missing"):
        load_plan(plan_file(tmp_path, concept(), header='[[source]]\nfile = "A.md"\n\n'))


def test_the_real_plan_is_valid_and_matches_the_sources_on_disk():
    plan = load_plan(REPO / "wiki-plan.toml")
    assert len(plan.concepts) >= 10 and len(plan.sources) >= 3
    raw = REPO / "vault" / "raw"
    if raw.is_dir():
        for source in plan.sources:
            assert (raw / source.file).is_file(), f"plan lists {source.file} but it is not in vault/raw"
        on_disk = {p.name for p in raw.iterdir() if p.is_file()}
        assert on_disk == {s.file for s in plan.sources}, "vault/raw and the plan's source list must match"
