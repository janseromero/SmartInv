"""``WorkflowEngine`` contract — durable workflow execution behind a seam.

Temporal-shaped vocabulary (``start`` / ``signal`` / ``query`` / ``cancel``) so
the MVP Postgres state-machine implementation can later be swapped for Temporal
without touching domain code (ADR-003).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Literal, Protocol, runtime_checkable


class WorkflowNotFoundError(KeyError):
    """Raised when a workflow id is unknown."""


class InvalidWorkflowTransitionError(ValueError):
    """Raised when a workflow event is not legal from the current state."""


class InvalidApprovalPathError(ValueError):
    """Raised when an approval path is empty or malformed."""


ReviewerType = Literal["role", "user"]
WorkflowState = Literal[
    "agent_proposed",
    "planner_review",
    "manager_review",
    "finance_review",
    "approved",
    "rejected",
]


@dataclass(frozen=True)
class ApprovalStep:
    """One configured reviewer step in an approval path.

    ``reviewer_type`` supports Option B for CV6: the assignee can be a role
    (``planner``, ``manager``, ``finance``) or a specific user identifier.
    The chosen path is persisted on the workflow so future policy edits do not
    rewrite in-flight approvals.
    """

    state: WorkflowState
    reviewer_type: ReviewerType
    reviewer: str


@dataclass(frozen=True)
class WorkflowHandle:
    """A snapshot of a workflow's identity, current state, and assignee."""

    id: uuid.UUID
    workflow_type: str
    state: str
    approval_path: tuple[ApprovalStep, ...] = ()
    current_step_index: int = -1
    current_reviewer_type: ReviewerType | None = None
    current_reviewer: str | None = None


@runtime_checkable
class WorkflowEngine(Protocol):
    """Durable workflow lifecycle over a tenant-scoped backend."""

    def start(
        self,
        *,
        workflow_type: str,
        payload: dict[str, Any],
        tenant_id: uuid.UUID,
        recommendation_id: uuid.UUID | None = None,
        approval_path: tuple[ApprovalStep, ...] | list[ApprovalStep] | None = None,
    ) -> WorkflowHandle:
        """Create a workflow instance with a persisted approval path."""
        ...

    def signal(
        self,
        workflow_id: uuid.UUID,
        *,
        event: str,
        idempotency_key: str,
        actor: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> WorkflowHandle:
        """Record an idempotent event and apply the state transition it implies."""
        ...

    def query(self, workflow_id: uuid.UUID) -> WorkflowHandle:
        """Return the current handle or raise WorkflowNotFoundError."""
        ...

    def cancel(self, workflow_id: uuid.UUID, *, actor: str | None = None) -> WorkflowHandle:
        """Cancel (reject) the workflow and return its handle."""
        ...
