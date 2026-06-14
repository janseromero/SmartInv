"""WorkflowEngine implementations: Postgres state machine (MVP) and in-memory.

The Postgres engine maps the Temporal-shaped vocabulary onto the
``workflow.approvals`` + ``workflow.approval_events`` tables (ADR-003). It runs
inside a tenant-scoped session, so RLS isolates every operation.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from api.contracts.workflow_engine import WorkflowHandle, WorkflowNotFoundError
from api.db.models.workflow import Approval, ApprovalEvent

INITIAL_STATE = "agent_proposed"
CANCELLED_STATE = "rejected"


class PostgresWorkflowEngine:
    """Durable workflow backed by the Postgres approval state machine."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def _handle(self, approval: Approval) -> WorkflowHandle:
        return WorkflowHandle(id=approval.id, workflow_type=approval.type, state=approval.state)

    def _load(self, workflow_id: uuid.UUID) -> Approval:
        approval = self._session.get(Approval, workflow_id)
        if approval is None:
            raise WorkflowNotFoundError(str(workflow_id))
        return approval

    def start(
        self,
        *,
        workflow_type: str,
        payload: dict[str, Any],
        tenant_id: uuid.UUID,
        recommendation_id: uuid.UUID | None = None,
    ) -> WorkflowHandle:
        approval = Approval(
            tenant_id=tenant_id,
            type=workflow_type,
            payload=payload,
            state=INITIAL_STATE,
            recommendation_id=recommendation_id,
        )
        self._session.add(approval)
        self._session.flush()
        self._session.add(
            ApprovalEvent(
                tenant_id=tenant_id, approval_id=approval.id, event="started", payload=payload
            )
        )
        self._session.flush()
        return self._handle(approval)

    def signal(
        self,
        workflow_id: uuid.UUID,
        *,
        event: str,
        actor: str | None = None,
        payload: dict[str, Any] | None = None,
        new_state: str | None = None,
    ) -> WorkflowHandle:
        approval = self._load(workflow_id)
        if new_state is not None:
            approval.state = new_state
            approval.current_actor = actor
        self._session.add(
            ApprovalEvent(
                tenant_id=approval.tenant_id,
                approval_id=approval.id,
                actor=actor,
                event=event,
                payload=payload or {},
            )
        )
        self._session.flush()
        return self._handle(approval)

    def query(self, workflow_id: uuid.UUID) -> WorkflowHandle:
        return self._handle(self._load(workflow_id))

    def cancel(self, workflow_id: uuid.UUID, *, actor: str | None = None) -> WorkflowHandle:
        return self.signal(workflow_id, event="cancelled", actor=actor, new_state=CANCELLED_STATE)


@dataclass
class _Record:
    handle: WorkflowHandle
    events: list[dict[str, Any]] = field(default_factory=list)


class InMemoryWorkflowEngine:
    """In-memory workflow engine for tests and contract-compliance checks."""

    def __init__(self) -> None:
        self._records: dict[uuid.UUID, _Record] = {}

    def start(
        self,
        *,
        workflow_type: str,
        payload: dict[str, Any],
        tenant_id: uuid.UUID,
        recommendation_id: uuid.UUID | None = None,
    ) -> WorkflowHandle:
        workflow_id = uuid.uuid4()
        handle = WorkflowHandle(id=workflow_id, workflow_type=workflow_type, state=INITIAL_STATE)
        self._records[workflow_id] = _Record(handle=handle, events=[{"event": "started"}])
        return handle

    def _require(self, workflow_id: uuid.UUID) -> _Record:
        record = self._records.get(workflow_id)
        if record is None:
            raise WorkflowNotFoundError(str(workflow_id))
        return record

    def signal(
        self,
        workflow_id: uuid.UUID,
        *,
        event: str,
        actor: str | None = None,
        payload: dict[str, Any] | None = None,
        new_state: str | None = None,
    ) -> WorkflowHandle:
        record = self._require(workflow_id)
        record.events.append({"event": event, "actor": actor})
        if new_state is not None:
            record.handle = WorkflowHandle(
                id=record.handle.id, workflow_type=record.handle.workflow_type, state=new_state
            )
        return record.handle

    def query(self, workflow_id: uuid.UUID) -> WorkflowHandle:
        return self._require(workflow_id).handle

    def cancel(self, workflow_id: uuid.UUID, *, actor: str | None = None) -> WorkflowHandle:
        return self.signal(workflow_id, event="cancelled", actor=actor, new_state=CANCELLED_STATE)
