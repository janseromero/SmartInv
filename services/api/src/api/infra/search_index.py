"""SearchIndex implementation: in-memory (MVP).

The real ``pg_trgm``-backed PostgresSearchIndex lands in CV2 with its first
consumer. This in-memory index uses difflib similarity so the contract and any
search-using code can be exercised today.
"""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any

from api.contracts.search_index import SearchHit


@dataclass
class _Doc:
    text: str
    payload: dict[str, Any]


class InMemorySearchIndex:
    """Similarity-ranked in-memory text index."""

    def __init__(self) -> None:
        self._docs: dict[str, _Doc] = {}

    def index(self, *, doc_id: str, text: str, payload: dict[str, Any] | None = None) -> None:
        self._docs[doc_id] = _Doc(text=text, payload=payload or {})

    def search(self, query: str, *, limit: int = 10) -> list[SearchHit]:
        normalized = query.lower().strip()
        hits: list[SearchHit] = []
        for doc_id, doc in self._docs.items():
            text = doc.text.lower()
            score = SequenceMatcher(None, normalized, text).ratio()
            if normalized and normalized in text:
                score = max(score, 0.9)
            if score > 0.0:
                hits.append(SearchHit(id=doc_id, score=score, payload=doc.payload))
        hits.sort(key=lambda hit: hit.score, reverse=True)
        return hits[:limit]

    def delete(self, doc_id: str) -> None:
        self._docs.pop(doc_id, None)
