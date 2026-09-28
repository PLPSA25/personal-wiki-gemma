"""The retrieval tool: find the passages that best match a question. No language model involved.

Ranking is BM25 (the standard keyword-relevance formula): passages containing more of the query's
rarer words rank higher, and a match in the section title counts double.
"""

from __future__ import annotations

import re
import sqlite3
from collections.abc import Collection
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from .chunk import Chunk
from .errors import WikiError

DEFAULT_LIMIT = 5
_SECTION_WEIGHT, _TEXT_WEIGHT = 2.0, 1.0

# Common words carry no meaning for ranking; question words would only add noise.
STOPWORDS = frozenset("""
a an and are as at be but by can could did do does for from had has have how i if in into is it its
me my no not of on or our should so than that the their them then there these they this to us was we
were what when where which who whom whose why will with would you your
""".split())


@dataclass(frozen=True)
class SearchResult:
    rank: int
    score: float  # higher is better
    chunk: Chunk


def build_query(text: str) -> str | None:
    """Turn free text into a safe FTS5 query, or None if it has no meaningful words.

    Only letters and digits survive, and every word is quoted, so nothing the user types can be
    read as FTS5 syntax (operators such as NEAR, OR, *, column filters). Words are OR-ed:
    a passage matching more of them ranks higher.
    """
    words = [w for w in re.findall(r"\w+", text.lower()) if len(w) > 1 and w not in STOPWORDS]
    unique = list(dict.fromkeys(words))
    return " OR ".join(f'"{word}"' for word in unique) if unique else None


def search(index_path: Path, question: str, limit: int = DEFAULT_LIMIT,
           sources: Collection[str] | None = None) -> list[SearchResult]:
    """Return up to `limit` best-matching passages, best first. The index is opened read-only.

    `sources` optionally restricts the search to passages from those files.
    """
    if not index_path.is_file():
        raise WikiError(f"No search index at {index_path}. Build it first with: wiki index")
    query = build_query(question)
    if query is None:
        raise WikiError("Nothing to search for: use at least one meaningful word (not just 'what', 'is', 'the'...).")

    uri = index_path.resolve().as_uri() + "?mode=ro"
    wanted = sorted(sources) if sources else []
    source_filter = f" AND source IN ({', '.join('?' * len(wanted))})" if wanted else ""
    try:
        with closing(sqlite3.connect(uri, uri=True)) as db:
            rows = db.execute(
                f"""SELECT source, idx, section, text, start_line, end_line,
                           -bm25(passages, ?, ?) AS score
                    FROM passages WHERE passages MATCH ?{source_filter}
                    ORDER BY score DESC LIMIT ?""",
                (_SECTION_WEIGHT, _TEXT_WEIGHT, query, *wanted, limit),
            ).fetchall()
    except sqlite3.DatabaseError as error:
        raise WikiError(f"The search index looks damaged ({error}). Rebuild it with: wiki index") from error
    return [
        SearchResult(rank, score, Chunk(source, section, idx, text, start, end))
        for rank, (source, idx, section, text, start, end, score) in enumerate(rows, start=1)
    ]
