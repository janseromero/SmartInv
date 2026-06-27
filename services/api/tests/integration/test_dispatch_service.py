"""Integration tests for source-system write dispatch (CV6.E4)."""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from typing import Any

import psycopg
import pytest
from api.config import get_settings
from api.db.models.ml import Recommendation
from api.db.models.workflow import SourceWrite
from api.db.session import tenant_session
from api.dispatch.service import enqueue_source_write, process_pending
from api.dispatch.writer import EchoSourceWriter, SourceWriteError, WriteReceipt
from sqlalchemy import select

ADMIN = get_settings().effective_admin_database_url
SLUG = "cv6_dispatch"


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
                "VALUES (%s, 'CV6Dispatch', 'active') RETURNING id",
                (SLUG,),
            )
            tid = cur.fetchone()[0]  # type: ignore[index]
    try:
        yield tid
    finally:
        with psycopg.connect(ADMIN) as admin:
            admin.autocommit = True
            with admin.cursor() as cur:
                cur.execute("DELETE FROM core.tenants WHERE slug = %s", (SLUG,))


def _recommendation(session: Any, tid: uuid.UUID) -> Recommendation:
    rec = Recommendation(
        tenant_id=tid,
        type="reorder_policy",
        target_type="item",
        target_id=uuid.uuid4(),
        claim="Raise min to 5",
        payload={"min_level": 5, "max_level": 12},
        status="proposed",
    )
    session.add(rec)
    session.flush()
    return rec


class _FailingWriter:
    def write(
        self, *, operation: str, payload: dict[str, Any], idempotency_key: str
    ) -> WriteReceipt:
        raise SourceWriteError("source unavailable")


def test_enqueue_is_idempotent(tenant_id: uuid.UUID) -> None:
    with tenant_session(str(tenant_id)) as session:
        rec = _recommendation(session, tenant_id)
        first = enqueue_source_write(
            session, tenant_id=tenant_id, recommendation=rec, approval_id=None
        )
        second = enqueue_source_write(
            session, tenant_id=tenant_id, recommendation=rec, approval_id=None
        )
        assert first.id == second.id
        assert first.operation == "min_max_change"


def test_process_delivers_and_writes_receipt(tenant_id: uuid.UUID) -> None:
    with tenant_session(str(tenant_id)) as session:
        rec = _recommendation(session, tenant_id)
        enqueue_source_write(session, tenant_id=tenant_id, recommendation=rec, approval_id=None)
        tally = process_pending(session, tenant_id=tenant_id, writer=EchoSourceWriter())
        assert tally["delivered"] == 1
        write = session.scalar(
            select(SourceWrite).where(SourceWrite.tenant_id == tenant_id).limit(1)
        )
        assert write is not None
        assert write.status == "delivered"
        assert write.receipt["external_id"].startswith("echo-")
        refreshed = session.get(Recommendation, rec.id)
        assert refreshed is not None
        assert refreshed.status == "delivered"


def test_failure_retries_then_dead_letters(tenant_id: uuid.UUID) -> None:
    with tenant_session(str(tenant_id)) as session:
        rec = _recommendation(session, tenant_id)
        write = enqueue_source_write(
            session, tenant_id=tenant_id, recommendation=rec, approval_id=None
        )
        write.max_attempts = 2
        session.flush()
        writer = _FailingWriter()

        first = process_pending(session, tenant_id=tenant_id, writer=writer)
        assert first["pending"] == 1
        second = process_pending(session, tenant_id=tenant_id, writer=writer)
        assert second["dead_letter"] == 1

        dead = session.get(SourceWrite, write.id)
        assert dead is not None
        assert dead.status == "dead_letter"
        assert dead.attempts == 2
        assert dead.last_error is not None
