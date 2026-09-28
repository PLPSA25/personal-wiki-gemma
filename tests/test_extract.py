import zipfile

import pytest

from wiki import extract
from wiki.errors import SourceError
from wiki.extract import read_source


def test_docx_paragraphs_are_separated_by_blank_lines(make_docx):
    path = make_docx([("", "First paragraph."), ("", "Second paragraph.")])
    assert read_source(path) == "First paragraph.\n\nSecond paragraph."


def test_docx_headings_become_markdown_headings(make_docx):
    path = make_docx([("Title", "My Note"), ("Heading2", "Details"), ("", "Body text.")])
    assert read_source(path) == "# My Note\n\n## Details\n\nBody text."


def test_docx_skips_empty_paragraphs(make_docx):
    path = make_docx([("", "One"), ("", "   "), ("", "Two")])
    assert read_source(path) == "One\n\nTwo"


def test_docx_special_characters_survive(make_docx):
    path = make_docx([("", "Price < $5 & “quoted”")])
    assert read_source(path) == "Price < $5 & “quoted”"


def test_docx_tabs_and_line_breaks(tmp_path):
    xml = (
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'
        "<w:p><w:r><w:t>a</w:t><w:tab/><w:t>b</w:t><w:br/><w:t>c</w:t></w:r></w:p></w:body></w:document>"
    )
    path = tmp_path / "t.docx"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", xml)
    assert read_source(path) == "a\tb\nc"


def test_docx_with_dtd_is_refused(make_docx):
    path = make_docx([("", "hello")], extra_xml='<!DOCTYPE d [<!ENTITY x "boom">]>')
    with pytest.raises(SourceError, match="DTD"):
        read_source(path)


def test_docx_that_expands_too_much_is_refused(make_docx, monkeypatch):
    path = make_docx([("", "hello")])
    monkeypatch.setattr(extract, "MAX_XML_BYTES", 10)
    with pytest.raises(SourceError, match="too much text"):
        read_source(path)


def test_oversized_docx_file_is_refused(make_docx, monkeypatch):
    path = make_docx([("", "hello")])
    monkeypatch.setattr(extract, "MAX_DOCX_BYTES", 10)
    with pytest.raises(SourceError, match="larger than"):
        read_source(path)


def test_not_a_zip_is_refused(tmp_path):
    path = tmp_path / "fake.docx"
    path.write_text("this is not a zip file")
    with pytest.raises(SourceError, match="not a valid .docx"):
        read_source(path)


def test_zip_without_document_xml_is_refused(tmp_path):
    path = tmp_path / "empty.docx"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("other.txt", "x")
    with pytest.raises(SourceError, match="no word/document.xml"):
        read_source(path)


def test_malformed_xml_is_refused(tmp_path):
    path = tmp_path / "bad.docx"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", "<w:document><unclosed>")
    with pytest.raises(SourceError, match="malformed XML"):
        read_source(path)


def test_markdown_is_read_as_is_and_bom_is_dropped(tmp_path):
    path = tmp_path / "note.md"
    path.write_bytes(b"\xef\xbb\xbf# Title\n\nText")
    assert read_source(path) == "# Title\n\nText"


def test_invalid_utf8_text_is_refused(tmp_path):
    path = tmp_path / "bad.txt"
    path.write_bytes(b"\xff\xfe\x00broken")
    with pytest.raises(SourceError, match="UTF-8"):
        read_source(path)


def test_oversized_text_file_is_refused(tmp_path, monkeypatch):
    path = tmp_path / "big.md"
    path.write_text("x" * 100)
    monkeypatch.setattr(extract, "MAX_TEXT_BYTES", 10)
    with pytest.raises(SourceError, match="larger than"):
        read_source(path)


def test_missing_file_has_a_clear_message(tmp_path):
    with pytest.raises(SourceError, match="not found"):
        read_source(tmp_path / "nope.md")


def test_unsupported_type_lists_supported_ones(tmp_path):
    path = tmp_path / "picture.png"
    path.write_bytes(b"png")
    with pytest.raises(SourceError, match=r"supported: \.docx, \.md, \.txt"):
        read_source(path)
