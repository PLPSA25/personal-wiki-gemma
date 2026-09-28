"""Turn a source file (Markdown, plain text or Word) into plain text, offline and safely.

A .docx file is a zip archive; the text lives in word/document.xml. We read it with the
standard library only, and refuse anything that looks like a zip bomb or an XML entity attack.
"""

from __future__ import annotations

import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from .errors import SourceError

SUPPORTED_SUFFIXES = frozenset({".md", ".txt", ".docx"})

MAX_TEXT_BYTES = 2_000_000  # .md / .txt file size
MAX_DOCX_BYTES = 5_000_000  # the .docx file itself
MAX_XML_BYTES = 20_000_000  # document.xml after decompression (zip-bomb guard)

_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_HEADING_STYLE = re.compile(r"Heading([1-6])")


def read_source(path: Path) -> str:
    """Return the plain text of a source file. Raises SourceError with a readable message."""
    if not path.is_file():
        raise SourceError(f"Source file not found: {path}")
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        supported = ", ".join(sorted(SUPPORTED_SUFFIXES))
        raise SourceError(f"Unsupported file type '{path.suffix}' for {path.name} (supported: {supported})")
    if suffix == ".docx":
        return _read_docx(path)
    return _read_text(path)


def _read_text(path: Path) -> str:
    if path.stat().st_size > MAX_TEXT_BYTES:
        raise SourceError(f"{path.name} is larger than {MAX_TEXT_BYTES // 1_000_000} MB; refusing to read it")
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as error:
        raise SourceError(f"{path.name} is not valid UTF-8 text") from error


def _read_docx(path: Path) -> str:
    if path.stat().st_size > MAX_DOCX_BYTES:
        raise SourceError(f"{path.name} is larger than {MAX_DOCX_BYTES // 1_000_000} MB; refusing to read it")
    try:
        with zipfile.ZipFile(path) as archive:
            info = archive.getinfo("word/document.xml")
            if info.file_size > MAX_XML_BYTES:
                raise SourceError(f"{path.name} expands to too much text; refusing to read it")
            xml = archive.read(info)
    except KeyError as error:
        raise SourceError(f"{path.name} has no word/document.xml; is it really a Word file?") from error
    except zipfile.BadZipFile as error:
        raise SourceError(f"{path.name} is not a valid .docx (zip) file") from error

    # Word files never need a DTD; entity definitions are how "billion laughs" attacks work.
    if b"<!DOCTYPE" in xml or b"<!ENTITY" in xml:
        raise SourceError(f"{path.name} contains an XML DTD/entity declaration; refusing to parse it")
    try:
        root = ElementTree.fromstring(xml)
    except ElementTree.ParseError as error:
        raise SourceError(f"{path.name} contains malformed XML: {error}") from error
    return _paragraphs_to_markdown(root)


def _paragraphs_to_markdown(root: ElementTree.Element) -> str:
    """Join the paragraphs of a Word document; Word headings become Markdown headings."""
    blocks = []
    for paragraph in root.iter(f"{_W}p"):
        text = _paragraph_text(paragraph)
        if not text:
            continue
        level = _heading_level(paragraph)
        blocks.append(f"{'#' * level} {text}" if level else text)
    return "\n\n".join(blocks)


def _paragraph_text(paragraph: ElementTree.Element) -> str:
    parts = []
    for node in paragraph.iter():
        if node.tag == f"{_W}t" and node.text:
            parts.append(node.text)
        elif node.tag == f"{_W}tab":
            parts.append("\t")
        elif node.tag in (f"{_W}br", f"{_W}cr"):
            parts.append("\n")
    return "".join(parts).strip()


def _heading_level(paragraph: ElementTree.Element) -> int:
    """0 for a normal paragraph, 1-6 for Word's Title/Heading styles."""
    style = paragraph.find(f"{_W}pPr/{_W}pStyle")
    name = style.get(f"{_W}val", "") if style is not None else ""
    if name == "Title":
        return 1
    match = _HEADING_STYLE.fullmatch(name)
    return int(match.group(1)) if match else 0
