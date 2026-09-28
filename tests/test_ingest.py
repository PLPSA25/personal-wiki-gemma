import json
import re
from pathlib import Path

import pytest

from wiki.chunk import Chunk
from wiki.cli import main
from wiki.config import Paths
from wiki.errors import ModelError, WikiError
from wiki.index import build_index
from wiki.ingest import (NoteError, approve, gather_passages, ingest, link_candidates, parse_reply, validate_note)
from wiki.llm import Reply
from wiki.plan import load_plan
from wiki.prompts import passage_label
from wiki.retrieval import SearchResult
from wiki.sources import file_sha256
from wiki.vault import parse_note

PLAN = """
[[source]]
file = "Economics.md"
description = "Lecture summaries"
origin = "Own words"

[[source]]
file = "Notes.docx"
description = "A Word document"
origin = "My own document"

[[concept]]
title = "Monopoly Pricing"
topic = "Economics"
query = "monopolist marginal revenue"
also_from = ["Notes.docx"]

[[concept]]
title = "Price Takers"
topic = "Economics"
query = "price taker marginal cost"

[[concept]]
title = "Sunk Costs"
topic = "Cases"
query = "sunk costs past spending"
sources = ["Notes.docx"]
"""


class NoteModel:
    """A fake Gemma that writes a plausible JSON note for whatever concept it is asked about."""

    name = "fake:1b"

    def __init__(self, overrides=None, fail_with=None):
        self.calls: list[list[dict]] = []
        self.titles: list[str] = []
        self.overrides = overrides or {}  # title -> list of raw replies to give, in order
        self.fail_with = fail_with

    def identity(self):
        return {"runtime": "fake", "model": "fake:1b", "quantization": "Q0"}

    def chat(self, messages, *, temperature, max_tokens, seed=None, response_format=None):
        if self.fail_with:
            raise self.fail_with
        assert response_format is not None and response_format["type"] == "object"  # structured JSON is requested
        user = messages[-1]["content"] if messages[-1]["role"] == "user" and len(messages) == 2 else messages[1]["content"]
        title = re.search(r"Concept: (.+)", user).group(1)
        self.calls.append(messages)
        self.titles.append(title)
        queued = self.overrides.get(title)
        text = queued.pop(0) if queued else self.default_note(title, user)
        return Reply(text, self.name, 100, 50, 1.5, 0.0)

    @staticmethod
    def default_note(title, user):
        labels = re.findall(r'label="(S\d+)"', user)
        others = [t for t in re.search(r"exactly\): (.*)", user).group(1).split("; ") if t and t != "(none)"]
        return json.dumps({
            "summary": f"{title} is explained in the sources, which describe how it works in practice.",
            "key_points": [
                {"text": f"The sources explain {title} with a worked example.", "cite": [labels[0]]},
                {"text": f"A second fact about {title} appears in the passages.", "cite": [labels[-1]]},
            ],
            "related": [{"title": others[0], "reason": f"{others[0]} is closely connected to {title}."}] if others else [],
        })


@pytest.fixture
def project(tmp_path, make_docx):
    raw = tmp_path / "vault" / "raw"
    raw.mkdir(parents=True)
    (raw / "Economics.md").write_text(
        "## Lecture 5: Monopoly\n\nA monopolist sets marginal revenue equal to marginal cost. "
        "It charges $24 when demand is P = 40 - 2q.\n\n"
        "## Lecture 3: Supply\n\nA price taker produces where price equals marginal cost.\n", encoding="utf-8")
    make_docx([("", "Sunk costs are past spending that cannot change. Marginal decisions ignore them.")],
              name="Notes.docx").rename(raw / "Notes.docx")
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    (prompts / "ingest-instructions.md").write_text("Write a note. Return JSON.", encoding="utf-8")
    (tmp_path / "wiki-plan.toml").write_text(PLAN, encoding="utf-8")
    return Paths(tmp_path)


def run_ingest(paths, model, **kwargs):
    return ingest(load_plan(paths.plan_path), paths, model, progress=lambda line: None, **kwargs)


def wiki_tree(paths):
    return {str(p.relative_to(paths.vault_dir)): p.read_bytes() for p in paths.vault_dir.rglob("*") if p.is_file()
            and "raw" not in p.relative_to(paths.vault_dir).parts}


def assert_all_links_resolve(paths):
    """Every [[link]] in the vault points at an existing note or original."""
    notes = {p.stem for p in paths.wiki_dir.rglob("*.md")}
    for page in [*paths.wiki_dir.rglob("*.md"), *paths.vault_dir.glob("*.md")]:
        for target in re.findall(r"\[\[([^\]|#]+)", page.read_text(encoding="utf-8")):
            if target.startswith("raw/"):
                name = target[4:]
                assert (paths.raw_dir / name).is_file() or (paths.raw_dir / f"{name}.md").is_file(), f"{page.name} -> {target}"
            else:
                assert target in notes or target == "Source Catalog", f"{page.name} links to missing note {target}"


# ---------------------------------------------------------------- gathering evidence

def test_also_from_guarantees_a_passage_from_that_source_and_labels_are_renumbered(project):
    build_index(project.raw_dir, project.index_path)
    concept = load_plan(project.plan_path).concepts[0]
    passages = gather_passages(concept, project.index_path)
    assert {r.chunk.source for r in passages} >= {"Economics.md", "Notes.docx"}
    assert [r.rank for r in passages] == list(range(1, len(passages) + 1))


def test_sources_restriction_limits_the_passages(project):
    build_index(project.raw_dir, project.index_path)
    concept = load_plan(project.plan_path).concepts[2]
    assert {r.chunk.source for r in gather_passages(concept, project.index_path)} == {"Notes.docx"}


# ---------------------------------------------------------------- validating what the model wrote

def passages_for_validation():
    texts = ["A monopolist sets marginal revenue equal to marginal cost and charges $24.",
             "A price taker produces where price equals marginal cost."]
    return [SearchResult(i, 1.0, Chunk("E.md", f"Lecture {i}", i, t, 1, 2)) for i, t in enumerate(texts, start=1)]


def note(**changes):
    data = {"summary": "Monopoly pricing sets marginal revenue equal to marginal cost, charging $24 here.",
            "key_points": [{"text": "A monopolist sets marginal revenue equal to cost.", "cite": ["S1"]},
                           {"text": "A price taker produces where price equals cost.", "cite": ["S2"]}],
            "related": [{"title": "price takers", "reason": "It is the competitive counterpart."}]}
    data.update(changes)
    return data


def test_a_good_note_is_accepted_and_related_titles_are_normalised():
    content, dropped = validate_note(note(), passages_for_validation(), ["Price Takers", "Sunk Costs"])
    assert len(content.key_points) == 2 and dropped == []
    assert [(r.title) for r in content.related] == ["Price Takers"]  # canonical spelling from the plan
    assert content.key_points[0].refs[0].chunk_id == "E.md#1"


def test_invented_links_and_duplicates_are_dropped_and_reported():
    related = [{"title": "Nonexistent Page", "reason": "Made up by the model."},
               {"title": "Price Takers", "reason": "The competitive counterpart."},
               {"title": "Price Takers", "reason": "The same page listed twice."},
               {"title": "Sunk Costs", "reason": "short"}]
    content, dropped = validate_note(note(related=related), passages_for_validation(), ["Price Takers", "Sunk Costs"])
    assert [r.title for r in content.related] == ["Price Takers"]
    assert any("Nonexistent Page" in d for d in dropped)


def test_at_most_four_related_links_are_kept():
    titles = [f"Concept Number {n}" for n in range(8)]
    related = [{"title": t, "reason": f"{t} is relevant because of the passages."} for t in titles]
    content, _ = validate_note(note(related=related), passages_for_validation(), titles)
    assert len(content.related) == 4


def test_key_points_with_invented_figures_or_bad_citations_are_dropped():
    points = [{"text": "A monopolist sets marginal revenue equal to cost.", "cite": ["S1"]},
              {"text": "A monopolist earns $99 of profit at the optimum.", "cite": ["S1"]},  # 99 is invented
              {"text": "A price taker produces where price equals cost.", "cite": ["S9"]},  # unknown label
              {"text": "A price taker produces where price equals cost.", "cite": []},  # no citation
              {"text": "A price taker produces where price equals cost.", "cite": ["S2"]}]
    content, dropped = validate_note(note(key_points=points), passages_for_validation(), ["Price Takers"])
    assert [p.text for p in content.key_points] == ["A monopolist sets marginal revenue equal to cost.",
                                                    "A price taker produces where price equals cost."]
    assert len(dropped) == 3 and any("99" in d for d in dropped)


def test_a_figure_is_checked_against_the_passage_it_cites_not_just_any_passage():
    points = [{"text": "A price taker produces where price equals cost, at $24.", "cite": ["S2"]},  # $24 is in S1 only
              {"text": "A monopolist sets marginal revenue equal to cost.", "cite": ["S1"]},
              {"text": "A monopolist charges $24 in the example.", "cite": ["S1"]}]
    content, dropped = validate_note(note(key_points=points), passages_for_validation(), ["Price Takers"])
    assert len(content.key_points) == 2 and len(dropped) == 1


@pytest.mark.parametrize("bad", [
    note(summary="Too short."),
    note(summary="This summary claims the answer is $12,345 which appears nowhere in the sources at all."),
    note(key_points=[{"text": "Only one usable point here.", "cite": ["S1"]}]),
    note(key_points=[]),
])
def test_unusable_notes_are_rejected_with_a_reason(bad):
    with pytest.raises(NoteError):
        validate_note(bad, passages_for_validation(), [])


@pytest.mark.parametrize("raw", ["not json at all", "[1, 2]", '{"summary": 5}', '{"summary": "x", "key_points": "no"}'])
def test_malformed_model_json_is_rejected(raw):
    with pytest.raises(NoteError):
        parse_reply(raw)


def test_injected_markup_in_model_text_is_neutralised():
    hostile = note(summary="Monopoly pricing is <img src=x onerror=alert(1)> set by [[Evil Page]] and marginal revenue equals cost.",
                   key_points=[{"text": "[[Evil]] A monopolist sets marginal revenue equal to cost. <b>bold</b>", "cite": ["S1"]},
                               {"text": "# A price taker produces where price equals cost.", "cite": ["S2"]}])
    content, _ = validate_note(hostile, passages_for_validation(), [])
    joined = content.summary + " ".join(p.text for p in content.key_points)
    assert "<" not in joined and "[[" not in joined and not content.key_points[1].text.startswith("#")


def test_a_note_must_use_the_passages_of_sources_the_plan_requires():
    with pytest.raises(NoteError, match="no key point uses the passage from Other.docx"):
        validate_note(note(), passages_for_validation(), [], required_sources=("Other.docx",))
    content, _ = validate_note(note(), passages_for_validation(), [], required_sources=("E.md",))
    assert len(content.key_points) == 2


def test_a_note_that_ignores_a_required_document_is_retried_with_the_reason(project):
    ignoring = json.dumps({
        "summary": "Monopoly pricing sets marginal revenue equal to marginal cost in the lecture.",
        "key_points": [{"text": "A monopolist sets marginal revenue equal to marginal cost.", "cite": ["S1"]},
                       {"text": "A price taker produces where price equals marginal cost.", "cite": ["S1"]}],
        "related": []})
    model = NoteModel({"Monopoly Pricing": [ignoring]})  # then the default note, which also cites the last passage
    report = run_ingest(project, model, only=["Monopoly Pricing"])
    assert report.outcomes[0].status == "written" and len(model.calls) == 2
    assert "no key point uses the passage from Notes.docx" in model.calls[1][-1]["content"]
    meta, body = parse_note((project.wiki_dir / "Economics" / "Monopoly Pricing.md").read_text(encoding="utf-8"))
    assert "[[raw/Notes.docx|Notes]]" in body.split("## Key points")[1].split("## Related")[0]


def test_a_note_lists_only_the_passages_its_key_points_actually_cite(project):
    run_ingest(project, NoteModel(), only=["Monopoly Pricing"])
    text = (project.wiki_dir / "Economics" / "Monopoly Pricing.md").read_text(encoding="utf-8")
    meta, body = parse_note(text)
    assert len(meta["source_passages"]) == 2  # three passages were shown to the model; the default note cites S1 and S3
    assert body.split("## Sources")[1].count("(lines ") == 2
    assert meta["source_files"] == ["Economics.md", "Notes.docx"]


def test_sources_section_is_in_a_readable_order(project):
    run_ingest(project, NoteModel())
    body = parse_note((project.wiki_dir / "Economics" / "Monopoly Pricing.md").read_text(encoding="utf-8"))[1]
    listed = re.findall(r"\(lines (\d+)-", body.split("## Sources")[1])
    economics = [int(n) for n in listed[:-1]]  # the docx passage sorts after Economics.md
    assert economics == sorted(economics)


def test_link_candidates_are_the_notes_that_share_evidence_strongest_first():
    evidence = {"A Note": {"p1", "p2", "p3"}, "B Note": {"p1", "p2"}, "C Note": {"p3", "p9"}, "D Note": {"p7"}}
    assert link_candidates("A Note", evidence) == ["B Note", "C Note"]  # D shares nothing, so it is never offered
    assert link_candidates("D Note", evidence) == []
    assert link_candidates("A Note", evidence, limit=1) == ["B Note"]


def test_ties_are_broken_alphabetically_so_runs_are_reproducible():
    evidence = {"Main Note": {"x"}, "Zed Note": {"x"}, "Alpha Note": {"x"}}
    assert link_candidates("Main Note", evidence) == ["Alpha Note", "Zed Note"]


def test_the_model_is_only_offered_evidence_linked_candidates(project):
    model = NoteModel()
    run_ingest(project, model, only=["Sunk Costs"])
    offered = re.search(r"exactly\): (.*)", model.calls[0][1]["content"]).group(1)
    # Sunk Costs is built only from the Notes.docx passage; the two Economics notes also gather it, so both overlap.
    assert set(offered.split("; ")) == {"Monopoly Pricing", "Price Takers"} and "Sunk Costs" not in offered


# ---------------------------------------------------------------- the whole run

def test_ingest_writes_readable_linked_notes_landing_pages_and_never_touches_the_originals(project):
    before = {p.name: file_sha256(p) for p in project.raw_dir.iterdir()}
    model = NoteModel()
    report = run_ingest(project, model)

    assert [o.status for o in report.outcomes] == ["written"] * 3
    files = sorted(p.relative_to(project.wiki_dir).as_posix() for p in project.wiki_dir.rglob("*.md"))
    assert files == ["Cases/Sunk Costs.md", "Economics/Monopoly Pricing.md", "Economics/Price Takers.md"]
    for path in project.wiki_dir.rglob("*.md"):
        meta, body = parse_note(path.read_text(encoding="utf-8"))
        assert body.startswith(f"# {path.stem}\n") and meta["title"] == path.stem  # heading == file name == title
        assert meta["status"] == "draft" and meta["source_files"] and "## Sources" in body
    assert_all_links_resolve(project)
    index = (project.vault_dir / "index.md").read_text(encoding="utf-8")
    assert "## Economics" in index and "[[Monopoly Pricing]]" in index and "## Cases" in index
    catalog = (project.vault_dir / "Source Catalog.md").read_text(encoding="utf-8")
    assert "[[raw/Economics]]" in catalog and "[[raw/Notes.docx]]" in catalog and "[[Monopoly Pricing]]" in catalog
    assert {p.name: file_sha256(p) for p in project.raw_dir.iterdir()} == before  # originals unchanged
    assert report.indexed_passages >= 3 and project.index_path.is_file()  # ingest also refreshed the search index


def test_re_ingest_changes_nothing_and_does_not_call_the_model(project):
    model = NoteModel()
    run_ingest(project, model)
    snapshot, calls = wiki_tree(project), len(model.calls)
    report = run_ingest(project, model)
    assert [o.status for o in report.outcomes] == ["up to date"] * 3
    assert len(model.calls) == calls and wiki_tree(project) == snapshot  # no duplicates, no rewrites, same bytes
    assert not list(project.wiki_dir.rglob("* (1).md"))


def test_a_changed_source_regenerates_only_the_notes_that_use_it_and_backs_up_the_old_version(project):
    model = NoteModel()
    run_ingest(project, model)
    (project.raw_dir / "Economics.md").write_text(
        "## Lecture 5: Monopoly\n\nA monopolist sets marginal revenue equal to marginal cost. Updated text.\n"
        "## Lecture 3: Supply\n\nA price taker produces where price equals marginal cost.\n", encoding="utf-8")
    model.titles.clear()
    report = run_ingest(project, model)
    statuses = {o.title: o.status for o in report.outcomes}
    assert statuses["Monopoly Pricing"] == "written" and statuses["Sunk Costs"] == "up to date"
    assert "Sunk Costs" not in model.titles
    assert len(list((project.backup_dir).rglob("Monopoly Pricing *.md"))) == 1
    assert len(list(project.wiki_dir.rglob("Monopoly Pricing*.md"))) == 1  # updated in place, no second file


def test_reviewed_and_edited_notes_are_protected_until_forced(project):
    model = NoteModel()
    run_ingest(project, model)
    reviewed = project.wiki_dir / "Economics" / "Monopoly Pricing.md"
    edited = project.wiki_dir / "Economics" / "Price Takers.md"
    edited.write_text(edited.read_text(encoding="utf-8") + "\nMy own correction.\n", encoding="utf-8")
    assert approve(project, ["Monopoly Pricing"]) == ["Monopoly Pricing"]
    protected_text = reviewed.read_text(encoding="utf-8")

    (project.prompts_dir / "ingest-instructions.md").write_text("Write a better note. Return JSON.", encoding="utf-8")
    report = run_ingest(project, model)
    statuses = {o.title: o.status for o in report.outcomes}
    assert statuses["Monopoly Pricing"] == "needs attention" and statuses["Price Takers"] == "needs attention"
    assert statuses["Sunk Costs"] == "written"  # an untouched draft is regenerated
    assert reviewed.read_text(encoding="utf-8") == protected_text and "My own correction." in edited.read_text(encoding="utf-8")

    forced = run_ingest(project, model, force=True, only=["Price Takers"])
    assert forced.outcomes[0].status == "written" and "My own correction." not in edited.read_text(encoding="utf-8")
    assert list(project.backup_dir.rglob("Price Takers *.md"))  # the edited version was kept


def test_a_file_that_this_program_did_not_write_is_never_overwritten(project):
    target = project.wiki_dir / "Economics" / "Price Takers.md"
    target.parent.mkdir(parents=True)
    target.write_text("# Price Takers\n\nMy handwritten note.\n", encoding="utf-8")
    report = run_ingest(project, NoteModel())
    assert {o.title: o.status for o in report.outcomes}["Price Takers"] == "needs attention"
    assert target.read_text(encoding="utf-8") == "# Price Takers\n\nMy handwritten note.\n"


def test_an_unusable_reply_is_retried_once_with_the_reason(project):
    good = NoteModel.default_note("Sunk Costs", 'label="S1" exactly): Price Takers')
    model = NoteModel({"Sunk Costs": ["this is not json", good]})
    report = run_ingest(project, model, only=["Sunk Costs"])
    assert report.outcomes[0].status == "written"
    retry_messages = model.calls[1]
    assert retry_messages[-2] == {"role": "assistant", "content": "this is not json"}
    assert "rejected because the reply was not valid JSON" in retry_messages[-1]["content"]


def test_two_bad_replies_fail_that_note_but_the_run_continues(project):
    model = NoteModel({"Price Takers": ["bad", "still bad"]})
    report = run_ingest(project, model)
    statuses = {o.title: o.status for o in report.outcomes}
    assert statuses == {"Monopoly Pricing": "written", "Price Takers": "failed", "Sunk Costs": "written"}
    assert not (project.wiki_dir / "Economics" / "Price Takers.md").exists()
    assert "Price Takers" not in (project.vault_dir / "index.md").read_text(encoding="utf-8").split("## Cases")[0].split("[[Monopoly")[0]


def test_a_model_server_that_is_down_stops_the_whole_run_at_once(project):
    with pytest.raises(ModelError, match="Cannot reach"):
        run_ingest(project, NoteModel(fail_with=ModelError("Cannot reach the local model server")))
    assert not list(project.wiki_dir.rglob("*.md"))


def test_only_selects_notes_and_unknown_titles_are_refused(project):
    model = NoteModel()
    report = run_ingest(project, model, only=["sunk costs"])
    assert [o.title for o in report.outcomes] == ["Sunk Costs"] and model.titles == ["Sunk Costs"]
    with pytest.raises(WikiError, match="Not in the plan: nothing here"):
        run_ingest(project, model, only=["Nothing Here"])


def test_missing_sources_are_reported_before_any_model_call(project):
    (project.raw_dir / "Notes.docx").unlink()
    model = NoteModel()
    with pytest.raises(WikiError, match="Notes.docx"):
        run_ingest(project, model)
    assert model.calls == []


def test_sources_not_in_the_plan_are_reported_not_silently_ignored(project):
    (project.raw_dir / "Extra.md").write_text("## X\n\nsomething", encoding="utf-8")
    assert run_ingest(project, NoteModel()).unplanned_sources == ["Extra.md"]


def test_a_note_never_gets_a_link_to_itself(project):
    run_ingest(project, NoteModel())
    for path in project.wiki_dir.rglob("*.md"):
        assert f"[[{path.stem}]]" not in path.read_text(encoding="utf-8")


# ---------------------------------------------------------------- approve and the CLI

def test_approve_marks_notes_reviewed_is_idempotent_and_rejects_unknown_titles(project):
    run_ingest(project, NoteModel())
    assert sorted(approve(project, None)) == ["Monopoly Pricing", "Price Takers", "Sunk Costs"]
    assert approve(project, None) == []  # nothing left to change
    meta, _ = parse_note((project.wiki_dir / "Cases" / "Sunk Costs.md").read_text(encoding="utf-8"))
    assert meta["status"] == "reviewed"
    with pytest.raises(WikiError, match="No such note: nothing"):
        approve(project, ["Nothing"])


def test_cli_ingest_then_re_ingest_then_approve(project, monkeypatch, capsys):
    monkeypatch.setattr("wiki.cli._make_model", lambda args: NoteModel())
    assert main(["--root", str(project.root), "ingest"]) == 0
    assert "3 written" in capsys.readouterr().out
    assert main(["--root", str(project.root), "ingest"]) == 0
    assert "3 up to date" in capsys.readouterr().out
    assert main(["--root", str(project.root), "approve", "--all"]) == 0
    assert "Marked 3 note(s)" in capsys.readouterr().out
    assert main(["--root", str(project.root), "approve"]) == 1
    assert "Say which notes" in capsys.readouterr().err


def test_cli_ingest_with_the_server_down_is_a_friendly_error(project, capsys):
    code = main(["--root", str(project.root), "ingest", "--ollama-url", "http://127.0.0.1:1"])
    err = capsys.readouterr().err
    assert code == 1 and "ollama serve" in err and "Traceback" not in err


def test_cli_ingest_refuses_a_different_source_folder(project, tmp_path, capsys):
    other = tmp_path / "elsewhere"
    other.mkdir()
    assert main(["--root", str(project.root), "ingest", str(other)]) == 1
    assert "Sources are read from" in capsys.readouterr().err
