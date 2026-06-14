"""Contract tests for ObjectStore — run against both implementations.

The same suite asserts protocol compliance for the in-memory fake and the real
S3/SeaweedFS store, proving they are swap-compliant (CV1.E7 Done Condition).
The S3 case is skipped when the object store is unreachable.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator

import pytest
from api.contracts.object_store import ObjectNotFoundError, ObjectStore
from api.infra.object_store import InMemoryObjectStore, S3ObjectStore


def _s3_store() -> S3ObjectStore | None:
    try:
        store = S3ObjectStore.from_settings()
        store.list()  # forces a connection
    except Exception:  # noqa: BLE001 — any connectivity failure -> skip
        return None
    return store


@pytest.fixture(params=["memory", "s3"])
def store(request: pytest.FixtureRequest) -> Iterator[ObjectStore]:
    if request.param == "memory":
        yield InMemoryObjectStore()
        return
    s3 = _s3_store()
    if s3 is None:
        pytest.skip("object store not reachable")
    try:
        yield s3
    finally:
        for key in s3.list("contract-test/"):
            s3.delete(key)


def test_put_get_roundtrip(store: ObjectStore) -> None:
    key = f"contract-test/{uuid.uuid4()}.txt"
    store.put(key, b"hello world", content_type="text/plain")
    assert store.get(key) == b"hello world"


def test_exists(store: ObjectStore) -> None:
    key = f"contract-test/{uuid.uuid4()}.txt"
    assert store.exists(key) is False
    store.put(key, b"x")
    assert store.exists(key) is True


def test_get_missing_raises(store: ObjectStore) -> None:
    with pytest.raises(ObjectNotFoundError):
        store.get(f"contract-test/missing-{uuid.uuid4()}")


def test_list_with_prefix(store: ObjectStore) -> None:
    prefix = f"contract-test/list-{uuid.uuid4()}/"
    store.put(f"{prefix}a", b"1")
    store.put(f"{prefix}b", b"2")
    listed = store.list(prefix)
    assert listed == sorted(listed)
    assert {f"{prefix}a", f"{prefix}b"} <= set(listed)


def test_delete(store: ObjectStore) -> None:
    key = f"contract-test/{uuid.uuid4()}.txt"
    store.put(key, b"x")
    store.delete(key)
    assert store.exists(key) is False
    store.delete(key)  # idempotent


def test_url_references_key(store: ObjectStore) -> None:
    key = f"contract-test/{uuid.uuid4()}.txt"
    store.put(key, b"x")
    assert key.split("/")[-1] in store.url(key)
