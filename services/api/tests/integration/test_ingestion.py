"""Integration tests for the source-ingestion pipeline (CV2.E1).

Verify idempotent upserts and per-record failure isolation against a real,
tenant-scoped database. Skipped when no database is reachable.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator, Sequence

import psycopg
import pytest
from api.config import get_settings
from api.db.models.inventory import Item
from api.db.models.sources import ErrorLog
from api.db.session import tenant_session
from api.ingestion.connector import Entity, SourceRecord
from api.ingestion.fixture_sync import ensure_fixture_connector
from api.ingestion.fixtures import FixtureConnector
from api.ingestion.service import IngestionService
from sqlalchemy import func, select

ADMIN = get_settings().effective_admin_database_url
SLUG = "e1_ing"


def _reachable() -> bool:
    try:
        with psycopg.connect(ADMIN, connect_timeout=3):
            return True
    except psycopg.OperationalError:
        return False


pytestmark = pytest.mark.skipif(not _reachable(), reason="database not reachable")


@pytest.fixture
def tenant_id() -> Iterator[uuid.UUID]:
    with psycopg.connect(ADMIN) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("DELETE FROM core.tenants WHERE slug = %s", (SLUG,))
            cur.execute(
                "INSERT INTO core.tenants(slug, name, status) "
                "VALUES (%s, 'Ingest', 'active') RETURNING id",
                (SLUG,),
            )
            tid = cur.fetchone()[0]  # type: ignore[index]
    try:
        yield tid
    finally:
        with psycopg.connect(ADMIN) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute("DELETE FROM core.tenants WHERE slug = %s", (SLUG,))


def _item_count(tid: uuid.UUID) -> int:
    with tenant_session(str(tid)) as session:
        return session.scalar(select(func.count()).select_from(Item)) or 0


def _sync(tid: uuid.UUID, connector: object) -> dict[str, dict[str, int]]:
    with tenant_session(str(tid)) as session:
        conn = ensure_fixture_connector(session, tid)
        return IngestionService(session).run(
            connector,  # type: ignore[arg-type]
            tenant_id=tid,
            connector_id=conn.id,
        )


def test_fixture_ingestion_is_idempotent(tenant_id: uuid.UUID) -> None:
    summary = _sync(tenant_id, FixtureConnector(item_count=25, seed=1))
    assert summary["item"]["upserted"] == 25
    assert summary["item"]["failed"] == 0
    assert summary["transaction"]["upserted"] > 0
    first = _item_count(tenant_id)

    _sync(tenant_id, FixtureConnector(item_count=25, seed=1))
    second = _item_count(tenant_id)

    assert first == 25
    assert second == 25  # re-running upserts, never duplicates


class _BadTransactionConnector:
    """Yields one location, one item, and a transaction with a dangling FK."""

    source_system = "fixture"

    def fetch(self, entity: Entity, since: object = None) -> Iterator[Sequence[SourceRecord]]:
        if entity is Entity.LOCATION:
            yield [SourceRecord("L1", {"location_code": "L1"})]
        elif entity is Entity.ITEM:
            yield [SourceRecord("I1", {"item_number": "I1"})]
        elif entity is Entity.TRANSACTION:
            yield [
                SourceRecord(
                    "T1",
                    {
                        "item_source_id": "DOES-NOT-EXIST",
                        "location_source_id": "L1",
                        "type": "issue",
                        "quantity": 1,
                    },
                )
            ]


def test_failure_isolation_logs_and_continues(tenant_id: uuid.UUID) -> None:
    summary = _sync(tenant_id, _BadTransactionConnector())

    assert summary["location"]["upserted"] == 1
    assert summary["item"]["upserted"] == 1
    assert summary["transaction"]["failed"] == 1
    assert summary["transaction"]["upserted"] == 0

    with tenant_session(str(tenant_id)) as session:
        errors = session.scalar(select(func.count()).select_from(ErrorLog)) or 0
    assert errors >= 1
