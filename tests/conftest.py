"""Shared test helpers."""

import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

import pytest

_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def build_docx(path: Path, paragraphs: list[tuple[str, str]], extra_xml: str = "") -> Path:
    """Write a minimal .docx. `paragraphs` is a list of (style, text); style '' means a normal paragraph."""
    body = ""
    for style, text in paragraphs:
        props = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
        body += f"<w:p>{props}<w:r><w:t>{escape(text)}</w:t></w:r></w:p>"
    xml = f'{extra_xml}<w:document xmlns:w="{_NS}"><w:body>{body}</w:body></w:document>'
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", xml)
    return path


@pytest.fixture
def make_docx(tmp_path):
    def factory(paragraphs, name="note.docx", extra_xml=""):
        return build_docx(tmp_path / name, paragraphs, extra_xml)

    return factory


class FakeModel:
    """Stands in for Gemma in unit tests: returns scripted replies and records the prompts it received."""

    name = "fake:1b"

    def __init__(self, *replies: str):
        self.replies = list(replies)
        self.calls: list[list[dict]] = []
        self.settings: list[dict] = []

    def chat(self, messages, *, temperature, max_tokens, seed=None, response_format=None, on_token=None):
        from wiki.llm import Reply

        self.calls.append(messages)
        self.settings.append({"temperature": temperature, "max_tokens": max_tokens, "seed": seed})
        if response_format is not None:
            self.settings[-1]["response_format"] = response_format
        text = self.replies.pop(0)
        if on_token is not None:
            on_token(text)
        return Reply(text, self.name, prompt_tokens=100, output_tokens=20, seconds=0.5, load_seconds=0.0)

    def identity(self):
        return {"runtime": "fake", "model": self.name}


@pytest.fixture
def fake_model():
    return FakeModel
