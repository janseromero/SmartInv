"""WorkflowEngine implementations: Postgres state machine (MVP) and in-memory.

The Postgres engine maps the Temporal-shaped vocabulary onto the
``workflow.approvals`` + ``workflow.approval_events`` tables (ADR-003). It runs
inside a tenant-scoped session, so RLS isolates every operation.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.contracts.workflow_engine import (
    ApprovalStep,
    InvalidApprovalPathError,
    InvalidWorkflowTransitionError,
    WorkflowHandle,
    WorkflowNotFoundError,
    WorkflowState,
)
from api.db.models.workflow import Approval, ApprovalEvent
from api.workflow.policies import resolve_approval_path

INITIAL_STATE: WorkflowState = "agent_proposed"
APPROVED_STATE: WorkflowState = "approved"
CANCELLED_STATE: WorkflowState = "rejected"
DEFAULT_APPROVAL_PATH = (
    ApprovalStep(state="planner_review", reviewer_type="role", reviewer="planner"),
)
REVIEW_STATES = {"planner_review", "manager_review", "finance_review"}
TERMINAL_STATES = {APPROVED_STATE, CANCELLED_STATE}
ALLOWED_REVIEWER_TYPES = {"role", "user"}


def _step_to_json(step: ApprovalStep) -> dict[str, str]:
    return {"state": step.state, "reviewer_type": step.reviewer_type, "reviewer": step.reviewer}


def _step_from_json(raw: dict[str, Any]) -> ApprovalStep:
    return ApprovalStep(
        state=raw["state"], reviewer_type=raw["reviewer_type"], reviewer=raw["reviewer"]
    )


def _normalize_path(
    approval_path: tuple[ApprovalStep, ...] | list[ApprovalStep] | None,
) -> tuple[ApprovalStep, ...]:
    path = tuple(approval_path or DEFAULT_APPROVAL_PATH)
    if not path:
        raise InvalidApprovalPathError("approval path must contain at least one reviewer step")

    for index, step in enumerate(path):
        if step.state not in REVIEW_STATES:
            raise InvalidApprovalPathError(f"step {index} has invalid review state: {step.state}")
        if step.reviewer_type not in ALLOWED_REVIEWER_TYPES:
            raise InvalidApprovalPathError(
                f"step {index} has invalid reviewer_type: {step.reviewer_type}"
            )
        if not step.reviewer.strip():
            raise InvalidApprovalPathError(f"step {index} must name a reviewer")
    return path


def _require_idempotency_key(idempotency_key: str) -> None:
    if not idempotency_key.strip():
        raise ValueError("idempotency_key is required for workflow transitions")


class PostgresWorkflowEngine:
    """Durable workflow backed by the Postgres approval state machine."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def _handle(self, approval: Approval) -> WorkflowHandle:
        path = tuple(_step_from_json(step) for step in approval.approval_path)
        return WorkflowHandle(
            id=approval.id,
            workflow_type=approval.type,
            state=approval.state,
            approval_path=path,
            current_step_index=approval.current_step_index,
            current_reviewer_type=approval.current_reviewer_type,  # type: ignore[arg-type]
            current_reviewer=approval.current_reviewer,
        )

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
        approval_path: tuple[ApprovalStep, ...] | list[ApprovalStep] | None = None,
    ) -> WorkflowHandle:
        resolved_path = approval_path
        if resolved_path is None:
            resolved_path = resolve_approval_path(
                self._session, workflow_type=workflow_type, payload=payload
            )
        path = _normalize_path(resolved_path)
        approval = Approval(
            tenant_id=tenant_id,
            type=workflow_type,
            payload=payload,
            state=INITIAL_STATE,
            current_step_index=-1,
            approval_path=[_step_to_json(step) for step in path],
            recommendation_id=recommendation_id,
        )
        self._session.add(approval)
        self._session.flush()
        self._session.add(
            ApprovalEvent(
                tenant_id=tenant_id,
                approval_id=approval.id,
                event="started",
                from_state=None,
                to_state=INITIAL_STATE,
                payload={"workflow_payload": payload, "approval_path": approval.approval_path},
            )
        )
        self._session.flush()
        return self._handle(approval)

    def _idempotent_handle(self, approval: Approval, idempotency_key: str) -> WorkflowHandle | None:
        existing = self._session.scalar(
            select(ApprovalEvent).where(
                ApprovalEvent.tenant_id == approval.tenant_id,
                ApprovalEvent.approval_id == approval.id,
                ApprovalEvent.idempotency_key == idempotency_key,
            )
        )
        if existing is None:
            return None
        return self._handle(approval)

    def _apply_transition(self, approval: Approval, event: str) -> WorkflowState:
        path = tuple(_step_from_json(step) for step in approval.approval_path)
        current_state = approval.state

        if current_state in TERMINAL_STATES:
            raise InvalidWorkflowTransitionError(
                f"workflow {approval.id} is terminal ({current_state}); no events accepted"
            )

        if event == "submit":
            if current_state != INITIAL_STATE:
                raise InvalidWorkflowTransitionError(
                    f"submit is only valid from {INITIAL_STATE}, not {current_state}"
                )
            next_index = 0
            next_step = path[next_index]
            approval.current_step_index = next_index
            approval.current_reviewer_type = next_step.reviewer_type
            approval.current_reviewer = next_step.reviewer
            return next_step.state

        if event == "approve":
            if current_state not in REVIEW_STATES:
                raise InvalidWorkflowTransitionError(
                    f"approve is only valid from review states, not {current_state}"
                )
            next_index = approval.current_step_index + 1
            if next_index >= len(path):
                approval.current_reviewer_type = None
                approval.current_reviewer = None
                return APPROVED_STATE
            next_step = path[next_index]
            approval.current_step_index = next_index
            approval.current_reviewer_type = next_step.reviewer_type
            approval.current_reviewer = next_step.reviewer
            return next_step.state

        if event in {"reject", "cancelled"}:
            approval.current_reviewer_type = None
            approval.current_reviewer = None
            return CANCELLED_STATE

        raise InvalidWorkflowTransitionError(f"unsupported workflow event: {event}")

    def signal(
        self,
        workflow_id: uuid.UUID,
        *,
        event: str,
        idempotency_key: str,
        actor: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> WorkflowHandle:
        _require_idempotency_key(idempotency_key)
        approval = self._load(workflow_id)
        idempotent = self._idempotent_handle(approval, idempotency_key)
        if idempotent is not None:
            return idempotent

        from_state = approval.state
        to_state = self._apply_transition(approval, event)
        approval.state = to_state
        approval.current_actor = actor
        self._session.add(
            ApprovalEvent(
                tenant_id=approval.tenant_id,
                approval_id=approval.id,
                actor=actor,
                event=event,
                idempotency_key=idempotency_key,
                from_state=from_state,
                to_state=to_state,
                payload=payload or {},
            )
        )
        self._session.flush()
        return self._handle(approval)

    def query(self, workflow_id: uuid.UUID) -> WorkflowHandle:
        return self._handle(self._load(workflow_id))

    def cancel(self, workflow_id: uuid.UUID, *, actor: str | None = None) -> WorkflowHandle:
        return self.signal(
            workflow_id,
            event="cancelled",
            actor=actor,
            idempotency_key=f"cancel:{workflow_id}:{actor or 'system'}",
        )


@dataclass
class _Record:
    handle: WorkflowHandle
    events: list[dict[str, Any]] = field(default_factory=list)
    idempotency_keys: set[str] = field(default_factory=set)


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
        approval_path: tuple[ApprovalStep, ...] | list[ApprovalStep] | None = None,
    ) -> WorkflowHandle:
        path = _normalize_path(approval_path)
        workflow_id = uuid.uuid4()
        handle = WorkflowHandle(
            id=workflow_id,
            workflow_type=workflow_type,
            state=INITIAL_STATE,
            approval_path=path,
            current_step_index=-1,
        )
        self._records[workflow_id] = _Record(handle=handle, events=[{"event": "started"}])
        return handle

    def _require(self, workflow_id: uuid.UUID) -> _Record:
        record = self._records.get(workflow_id)
        if record is None:
            raise WorkflowNotFoundError(str(workflow_id))
        return record

    def _transition(self, handle: WorkflowHandle, event: str) -> WorkflowHandle:
        if handle.state in TERMINAL_STATES:
            raise InvalidWorkflowTransitionError(
                f"workflow {handle.id} is terminal ({handle.state}); no events accepted"
            )
        if event == "submit":
            if handle.state != INITIAL_STATE:
                raise InvalidWorkflowTransitionError(
                    f"submit is only valid from {INITIAL_STATE}, not {handle.state}"
                )
            step = handle.approval_path[0]
            return WorkflowHandle(
                id=handle.id,
                workflow_type=handle.workflow_type,
                state=step.state,
                approval_path=handle.approval_path,
                current_step_index=0,
                current_reviewer_type=step.reviewer_type,
                current_reviewer=step.reviewer,
            )
        if event == "approve":
            if handle.state not in REVIEW_STATES:
                raise InvalidWorkflowTransitionError(
                    f"approve is only valid from review states, not {handle.state}"
                )
            next_index = handle.current_step_index + 1
            if next_index >= len(handle.approval_path):
                return WorkflowHandle(
                    id=handle.id,
                    workflow_type=handle.workflow_type,
                    state=APPROVED_STATE,
                    approval_path=handle.approval_path,
                    current_step_index=handle.current_step_index,
                )
            step = handle.approval_path[next_index]
            return WorkflowHandle(
                id=handle.id,
                workflow_type=handle.workflow_type,
                state=step.state,
                approval_path=handle.approval_path,
                current_step_index=next_index,
                current_reviewer_type=step.reviewer_type,
                current_reviewer=step.reviewer,
            )
        if event in {"reject", "cancelled"}:
            return WorkflowHandle(
                id=handle.id,
                workflow_type=handle.workflow_type,
                state=CANCELLED_STATE,
                approval_path=handle.approval_path,
                current_step_index=handle.current_step_index,
            )
        raise InvalidWorkflowTransitionError(f"unsupported workflow event: {event}")

    def signal(
        self,
        workflow_id: uuid.UUID,
        *,
        event: str,
        idempotency_key: str,
        actor: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> WorkflowHandle:
        _require_idempotency_key(idempotency_key)
        record = self._require(workflow_id)
        if idempotency_key in record.idempotency_keys:
            return record.handle
        record.idempotency_keys.add(idempotency_key)
        record.handle = self._transition(record.handle, event)
        record.events.append({"event": event, "actor": actor, "idempotency_key": idempotency_key})
        return record.handle

    def query(self, workflow_id: uuid.UUID) -> WorkflowHandle:
        return self._require(workflow_id).handle

    def cancel(self, workflow_id: uuid.UUID, *, actor: str | None = None) -> WorkflowHandle:
        return self.signal(
            workflow_id,
            event="cancelled",
            actor=actor,
            idempotency_key=f"cancel:{workflow_id}:{actor or 'system'}",
        )
