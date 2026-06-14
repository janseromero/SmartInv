"""``WorkflowEngine`` contract — durable workflow execution behind a seam.

Temporal-shaped vocabulary (``start`` / ``signal`` / ``query`` / ``cancel``) so
the MVP Postgres state-machine implementation can later be swapped for Temporal
without touching domain code (ADR-003).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


class WorkflowNotFoundError(KeyError):
    """Raised when a workflow id is unknown."""


@dataclass(frozen=True)
class WorkflowHandle:
    """A snapshot of a workflow's identity and current state."""

    id: uuid.UUID
    workflow_type: str
    state: str


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
    ) -> WorkflowHandle:
        """Create a workflow instance and return its handle."""
        ...

    def signal(
        self,
        workflow_id: uuid.UUID,
        *,
        event: str,
        actor: str | None = None,
        payload: dict[str, Any] | None = None,
        new_state: str | None = None,
    ) -> WorkflowHandle:
        """Record an event, optionally transitioning to ``new_state``."""
        ...

    def query(self, workflow_id: uuid.UUID) -> WorkflowHandle:
        """Return the current handle or raise WorkflowNotFoundError."""
        ...

    def cancel(self, workflow_id: uuid.UUID, *, actor: str | None = None) -> WorkflowHandle:
        """Cancel (reject) the workflow and return its handle."""
        ...
