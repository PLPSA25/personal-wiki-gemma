"""Prompt assembly: instruction files + labelled passages + the question, as chat messages.

Instructions live in prompts/*.md (not in the code) so they can be read, changed and versioned on
their own. Ask mode loads ONLY wiki-instructions.md: no persona, no conversation history.
"""

from __future__ import annotations

from pathlib import Path

from .errors import WikiError
from .retrieval import SearchResult

ASK_INSTRUCTIONS_FILE = "wiki-instructions.md"


def load_instructions(prompts_dir: Path, filename: str) -> str:
    path = prompts_dir / filename
    try:
        text = path.read_text(encoding="utf-8-sig").strip()
    except OSError as error:
        raise WikiError(f"Cannot read the instruction file {path}: {error.strerror or error}") from error
    if not text:
        raise WikiError(f"The instruction file {path} is empty.")
    return text


def passage_label(position: int) -> str:
    """S1, S2, ... : the short label the model must cite."""
    return f"S{position}"


def format_passages(results: list[SearchResult]) -> str:
    """Render passages as clearly delimited data blocks the model is told to cite by label."""
    blocks = []
    for result in results:
        chunk = result.chunk
        # A passage must not be able to close its own block and pose as instructions.
        safe_text = chunk.text.replace("</passage", "< /passage")
        blocks.append(
            f'<passage label="{passage_label(result.rank)}" source="{chunk.source}" section="{chunk.section}">\n'
            f"{safe_text}\n</passage>"
        )
    return "\n\n".join(blocks)


def build_ask_messages(instructions: str, question: str, results: list[SearchResult]) -> list[dict]:
    user = f"Source passages:\n\n{format_passages(results)}\n\nQuestion: {question}"
    return [{"role": "system", "content": instructions}, {"role": "user", "content": user}]
