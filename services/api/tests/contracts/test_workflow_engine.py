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
from api.contracts.workflow_engine import (
    ApprovalStep,
    InvalidApprovalPathError,
    InvalidWorkflowTransitionError,
    WorkflowEngine,
    WorkflowNotFoundError,
)
from api.db.session import tenant_session
from api.infra.workflow_engine import (
    APPROVED_STATE,
    CANCELLED_STATE,
    DEFAULT_APPROVAL_PATH,
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


def test_start_creates_workflow_in_initial_state_with_default_path(
    engine_and_tenant: tuple[WorkflowEngine, uuid.UUID],
) -> None:
    engine, tenant_id = engine_and_tenant
    handle = engine.start(
        workflow_type="min_max_change", payload={"item": "X"}, tenant_id=tenant_id
    )
    assert handle.state == INITIAL_STATE
    assert handle.workflow_type == "min_max_change"
    assert handle.approval_path == DEFAULT_APPROVAL_PATH
    assert handle.current_step_index == -1
    assert engine.query(handle.id).state == INITIAL_STATE


def test_submit_moves_to_first_configured_reviewer(
    engine_and_tenant: tuple[WorkflowEngine, uuid.UUID],
) -> None:
    engine, tenant_id = engine_and_tenant
    path = [ApprovalStep(state="planner_review", reviewer_type="user", reviewer="u-123")]
    handle = engine.start(
        workflow_type="transfer", payload={}, tenant_id=tenant_id, approval_path=path
    )

    submitted = engine.signal(handle.id, event="submit", actor="agent", idempotency_key="submit-1")

    assert submitted.state == "planner_review"
    assert submitted.current_step_index == 0
    assert submitted.current_reviewer_type == "user"
    assert submitted.current_reviewer == "u-123"


def test_approve_walks_configured_role_and_user_path_to_approved(
    engine_and_tenant: tuple[WorkflowEngine, uuid.UUID],
) -> None:
    engine, tenant_id = engine_and_tenant
    path = [
        ApprovalStep(state="planner_review", reviewer_type="role", reviewer="planner"),
        ApprovalStep(state="manager_review", reviewer_type="user", reviewer="manager@example.com"),
        ApprovalStep(state="finance_review", reviewer_type="role", reviewer="finance"),
    ]
    handle = engine.start(
        workflow_type="risk_mitigation", payload={}, tenant_id=tenant_id, approval_path=path
    )

    first = engine.signal(handle.id, event="submit", actor="agent", idempotency_key="submit")
    second = engine.signal(first.id, event="approve", actor="planner", idempotency_key="planner")
    third = engine.signal(second.id, event="approve", actor="manager", idempotency_key="manager")
    final = engine.signal(third.id, event="approve", actor="finance", idempotency_key="finance")

    assert first.state == "planner_review"
    assert second.state == "manager_review"
    assert second.current_reviewer_type == "user"
    assert second.current_reviewer == "manager@example.com"
    assert third.state == "finance_review"
    assert final.state == APPROVED_STATE
    assert final.current_reviewer_type is None
    assert final.current_reviewer is None


def test_reject_sets_cancelled_state(
    engine_and_tenant: tuple[WorkflowEngine, uuid.UUID],
) -> None:
    engine, tenant_id = engine_and_tenant
    handle = engine.start(workflow_type="transfer", payload={}, tenant_id=tenant_id)
    engine.signal(handle.id, event="submit", actor="agent", idempotency_key="submit")
    rejected = engine.signal(handle.id, event="reject", actor="manager", idempotency_key="reject")
    assert rejected.state == CANCELLED_STATE


def test_cancel_sets_cancelled_state(
    engine_and_tenant: tuple[WorkflowEngine, uuid.UUID],
) -> None:
    engine, tenant_id = engine_and_tenant
    handle = engine.start(workflow_type="transfer", payload={}, tenant_id=tenant_id)
    engine.cancel(handle.id, actor="manager")
    assert engine.query(handle.id).state == CANCELLED_STATE


def test_idempotency_key_replays_without_applying_second_event(
    engine_and_tenant: tuple[WorkflowEngine, uuid.UUID],
) -> None:
    engine, tenant_id = engine_and_tenant
    handle = engine.start(workflow_type="transfer", payload={}, tenant_id=tenant_id)

    first = engine.signal(handle.id, event="submit", actor="agent", idempotency_key="same-key")
    replay = engine.signal(handle.id, event="approve", actor="planner", idempotency_key="same-key")

    assert first.state == "planner_review"
    assert replay.state == "planner_review"


def test_invalid_transition_raises(
    engine_and_tenant: tuple[WorkflowEngine, uuid.UUID],
) -> None:
    engine, tenant_id = engine_and_tenant
    handle = engine.start(workflow_type="transfer", payload={}, tenant_id=tenant_id)

    with pytest.raises(InvalidWorkflowTransitionError):
        engine.signal(handle.id, event="approve", actor="planner", idempotency_key="bad")


def test_terminal_workflow_rejects_new_events(
    engine_and_tenant: tuple[WorkflowEngine, uuid.UUID],
) -> None:
    engine, tenant_id = engine_and_tenant
    handle = engine.start(workflow_type="transfer", payload={}, tenant_id=tenant_id)
    engine.signal(handle.id, event="submit", actor="agent", idempotency_key="submit")
    engine.signal(handle.id, event="approve", actor="planner", idempotency_key="approve")

    with pytest.raises(InvalidWorkflowTransitionError):
        engine.signal(handle.id, event="reject", actor="planner", idempotency_key="too-late")


def test_invalid_path_raises(engine_and_tenant: tuple[WorkflowEngine, uuid.UUID]) -> None:
    engine, tenant_id = engine_and_tenant
    with pytest.raises(InvalidApprovalPathError):
        engine.start(
            workflow_type="transfer",
            payload={},
            tenant_id=tenant_id,
            approval_path=[
                ApprovalStep(state="approved", reviewer_type="role", reviewer="planner"),
            ],
        )


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
