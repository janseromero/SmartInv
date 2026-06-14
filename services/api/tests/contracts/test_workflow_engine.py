"""Contract tests for WorkflowEngine — in-memory and Postgres implementations.

The Postgres case runs against a real, tenant-scoped session (RLS active) and is
skipped when no database is reachable.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator

import psycopg
import pytest
from api.config import get_settings
from api.contracts.workflow_engine import WorkflowEngine, WorkflowNotFoundError
from api.db.session import tenant_session
from api.infra.workflow_engine import (
    CANCELLED_STATE,
    INITIAL_STATE,
    InMemoryWorkflowEngine,
    PostgresWorkflowEngine,
)

ADMIN = get_settings().effective_admin_database_url
SLUG = "e7_wf"


def _db_reachable() -> bool:
    try:
        with psycopg.connect(ADMIN, connect_timeout=3):
            return True
    except psycopg.OperationalError:
        return False


@pytest.fixture(params=["memory", "postgres"])
def engine_and_tenant(
    request: pytest.FixtureRequest,
) -> Iterator[tuple[WorkflowEngine, uuid.UUID]]:
    if request.param == "memory":
        yield InMemoryWorkflowEngine(), uuid.uuid4()
        return

    if not _db_reachable():
        pytest.skip("database not reachable")

    with psycopg.connect(ADMIN) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("DELETE FROM core.tenants WHERE slug = %s", (SLUG,))
            cur.execute(
                "INSERT INTO core.tenants(slug, name, status) "
                "VALUES (%s, 'WF', 'active') RETURNING id",
                (SLUG,),
            )
            tenant_id = cur.fetchone()[0]  # type: ignore[index]
    try:
        with tenant_session(str(tenant_id)) as session:
            yield PostgresWorkflowEngine(session), tenant_id
    finally:
        with psycopg.connect(ADMIN) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute("DELETE FROM core.tenants WHERE slug = %s", (SLUG,))


def test_start_creates_workflow_in_initial_state(
    engine_and_tenant: tuple[WorkflowEngine, uuid.UUID],
) -> None:
    engine, tenant_id = engine_and_tenant
    handle = engine.start(
        workflow_type="min_max_change", payload={"item": "X"}, tenant_id=tenant_id
    )
    assert handle.state == INITIAL_STATE
    assert handle.workflow_type == "min_max_change"
    assert engine.query(handle.id).state == INITIAL_STATE


def test_signal_transitions_state(
    engine_and_tenant: tuple[WorkflowEngine, uuid.UUID],
) -> None:
    engine, tenant_id = engine_and_tenant
    handle = engine.start(workflow_type="transfer", payload={}, tenant_id=tenant_id)
    engine.signal(handle.id, event="approved", actor="planner", new_state="planner_review")
    assert engine.query(handle.id).state == "planner_review"


def test_cancel_sets_cancelled_state(
    engine_and_tenant: tuple[WorkflowEngine, uuid.UUID],
) -> None:
    engine, tenant_id = engine_and_tenant
    handle = engine.start(workflow_type="transfer", payload={}, tenant_id=tenant_id)
    engine.cancel(handle.id, actor="manager")
    assert engine.query(handle.id).state == CANCELLED_STATE


def test_query_unknown_raises(
    engine_and_tenant: tuple[WorkflowEngine, uuid.UUID],
) -> None:
    engine, _ = engine_and_tenant
    with pytest.raises(WorkflowNotFoundError):
        engine.query(uuid.uuid4())


def test_implements_protocol(
    engine_and_tenant: tuple[WorkflowEngine, uuid.UUID],
) -> None:
    engine, _ = engine_and_tenant
    assert isinstance(engine, WorkflowEngine)
