import pytest

from wiki.errors import WikiError
from wiki.plan import SourceInfo
from wiki.vault import (NoteContent, PageInfo, KeyPoint, Related, SourceRef, first_sentence, note_path, parse_note,
                        render_catalog, render_index, render_note, sanitize_line, source_link, text_sha256)

REF_MD = SourceRef("Economics Lectures.md", "Lecture 5: Introduction to Monopoly", 190, 205, "Economics Lectures.md#20")
REF_DOC = SourceRef("Group Pricing.docx", "Group Pricing", 1, 9, "Group Pricing.docx#1")


def content():
    return NoteContent(
        summary="Group pricing charges different groups different prices. It needs identifiable groups.",
        key_points=(KeyPoint("Three conditions must hold.", (REF_MD, REF_DOC)),
                    KeyPoint("Netflix offers returning subscribers a discount.", (REF_DOC,))),
        related=(Related("Menu Pricing", "It is the other form of price discrimination."),),
        passages=(REF_MD, REF_DOC),
    )


def test_sanitize_removes_html_wikilinks_control_characters_and_markdown_prefixes():
    dirty = "## <script>alert(1)</script>Steal [[Secret Page]]\x00 now\n\n   > quoted"
    clean = sanitize_line(dirty, 200)
    assert "<script>" not in clean and "[[" not in clean and "\x00" not in clean and "\n" not in clean
    assert clean.startswith("alert(1)Steal [Secret Page]") and clean.endswith("now > quoted")  # a mid-line ">" is harmless


def test_sanitize_keeps_math_and_limits_length():
    assert sanitize_line("MR < P and 2 > 1", 100) == "MR < P and 2 > 1"
    assert len(sanitize_line("word " * 100, 50)) <= 50


def test_note_paths_stay_inside_the_wiki_folder(tmp_path):
    assert note_path(tmp_path, "Economics", "Group Pricing") == (tmp_path / "Economics" / "Group Pricing.md").resolve()
    for topic, title in (("..", "Evil"), ("../..", "Evil"), ("Economics", "../../Evil")):
        with pytest.raises(WikiError, match="outside the wiki"):
            note_path(tmp_path, topic, title)


def test_source_links_use_names_obsidian_can_resolve():
    assert source_link("Economics Lectures.md", "Lecture 5: Introduction to Monopoly") == \
        "[[raw/Economics Lectures|Economics Lectures, Lecture 5]]"
    assert source_link("Group Pricing.docx") == "[[raw/Group Pricing.docx|Group Pricing]]"
    label = source_link("Odd [name] | file.md").rsplit("|", 1)[1].removesuffix("]]")
    assert "[" not in label and "]" not in label and "|" not in label  # the display label cannot break the link


def test_rendered_note_has_matching_heading_links_sources_and_frontmatter():
    text, body = render_note("Group Pricing", "Economics", content(), {"fingerprint": "abc", "generated_by": "gemma"})
    meta, parsed_body = parse_note(text)
    assert parsed_body == body and body.startswith("# Group Pricing\n")
    assert meta["title"] == "Group Pricing" and meta["topic"] == "Economics" and meta["status"] == "draft"
    assert meta["source_files"] == ["Economics Lectures.md", "Group Pricing.docx"]
    assert meta["source_passages"] == ["Economics Lectures.md#20", "Group Pricing.docx#1"]
    assert meta["body_sha256"] == text_sha256(body) and meta["fingerprint"] == "abc"
    assert "[[raw/Economics Lectures|Economics Lectures, Lecture 5]]" in body
    assert "- [[Menu Pricing]] - It is the other form of price discrimination." in body
    assert "## Sources" in body and "(lines 190-205)" in body
    assert meta["description"] == "Group pricing charges different groups different prices."


def test_a_note_without_related_links_says_so_instead_of_inventing_any():
    solo = NoteContent(content().summary, content().key_points, (), content().passages)
    assert "(none identified)" in render_note("Group Pricing", "Economics", solo, {})[1]


def test_yaml_special_characters_in_titles_survive_a_round_trip():
    text, _ = render_note("Rock & Roll: Part 2", "Economics", content(), {})
    assert parse_note(text)[0]["title"] == "Rock & Roll: Part 2"


@pytest.mark.parametrize("text", ["# Just a note\n", "---\n: bad: yaml: [\n---\nbody", "---\n- a list\n---\nbody", ""])
def test_files_without_our_frontmatter_are_not_parsed(text):
    assert parse_note(text) is None


def test_index_groups_by_topic_in_plan_order_and_links_the_catalog():
    pages = [PageInfo("Beta Note", "Data Analysis", "About beta.", "draft", ()),
             PageInfo("Alpha Note", "Economics", "About alpha.", "draft", ()),
             PageInfo("Aardvark Note", "Economics", "About aardvark.", "draft", ())]
    index = render_index(pages, ["Economics", "Data Analysis"])
    assert index.index("## Economics") < index.index("## Data Analysis")
    assert index.index("[[Aardvark Note]]") < index.index("[[Alpha Note]]")  # alphabetical within a topic
    assert "- [[Beta Note]] - About beta." in index and "[[Source Catalog]]" in index


def test_catalog_lists_hashes_and_which_notes_cite_each_source():
    sources = (SourceInfo("Economics Lectures.md", "Lecture summaries", "Written from slides"),
               SourceInfo("Group Pricing.docx", "An example", "My own document"))
    pages = [PageInfo("Group Pricing", "Economics", "d", "draft", ("Economics Lectures.md", "Group Pricing.docx")),
             PageInfo("Menu Pricing", "Economics", "d", "draft", ("Economics Lectures.md",))]
    catalog = render_catalog(sources, {"Economics Lectures.md": "ab" * 32, "Group Pricing.docx": "cd" * 32}, pages)
    assert "| [[raw/Economics Lectures]] | Lecture summaries | Written from slides | `abababababababab` |" in catalog
    assert "[[Group Pricing]], [[Menu Pricing]]" in catalog and "| [[raw/Group Pricing.docx]] |" in catalog


def test_first_sentence():
    assert first_sentence("One. Two.") == "One."
    assert first_sentence("word " * 100).endswith("...") and len(first_sentence("word " * 100)) <= 180


def test_a_long_first_sentence_is_shortened_at_a_word_boundary_never_mid_word():
    text = "Two-part tariffs involve setting both a per-unit price and a fee, where the optimal strategy is to set the price equal to marginal cost and capture the remaining surplus as the fee."
    short = first_sentence(text, limit=120)
    assert short.endswith("...") and len(short) <= 120
    assert text.startswith(short[:-3])  # a true prefix of the sentence
    assert text[len(short) - 3] == " "  # the cut fell on a space, so no word is broken
