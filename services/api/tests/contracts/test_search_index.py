"""Contract tests for SearchIndex (in-memory impl)."""

from __future__ import annotations

from api.contracts.search_index import SearchIndex
from api.infra.search_index import InMemorySearchIndex


def _index() -> SearchIndex:
    return InMemorySearchIndex()


def test_index_and_search_ranks_relevant_first() -> None:
    index = _index()
    index.index(doc_id="1", text="hydraulic pump seal kit", payload={"sku": "A1"})
    index.index(doc_id="2", text="electric motor bearing", payload={"sku": "B2"})

    hits = index.search("hydraulic pump")
    assert hits
    assert hits[0].id == "1"
    assert hits[0].payload["sku"] == "A1"
    assert hits == sorted(hits, key=lambda h: h.score, reverse=True)


def test_search_respects_limit() -> None:
    index = _index()
    for i in range(5):
        index.index(doc_id=str(i), text=f"valve type {i}")
    assert len(index.search("valve", limit=2)) <= 2


def test_delete_removes_document() -> None:
    index = _index()
    index.index(doc_id="1", text="gasket set")
    index.delete("1")
    assert index.search("gasket") == []
    index.delete("1")  # idempotent


def test_implements_protocol() -> None:
    assert isinstance(_index(), SearchIndex)
