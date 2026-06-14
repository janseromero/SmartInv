"""``SearchIndex`` contract — text search behind a swappable seam.

MVP ships an in-memory implementation only; the real ``pg_trgm``-backed
PostgresSearchIndex lands in CV2 with the first item-search consumer. The
protocol is defined now so search-using code depends on the seam, not on
Postgres vs OpenSearch vs a vector store.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class SearchHit:
    """A single search result."""

    id: str
    score: float
    payload: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class SearchIndex(Protocol):
    """Indexing and querying of text documents."""

    def index(self, *, doc_id: str, text: str, payload: dict[str, Any] | None = None) -> None:
        """Add or replace a document in the index."""
        ...

    def search(self, query: str, *, limit: int = 10) -> list[SearchHit]:
        """Return up to ``limit`` hits ranked by descending score."""
        ...

    def delete(self, doc_id: str) -> None:
        """Remove a document (no error if absent)."""
        ...
