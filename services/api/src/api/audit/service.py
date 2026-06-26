"""Append-only audit event helpers (CV6.E3)."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from api.db.models.audit import Event


def record_audit_event(
    session: Session,
    *,
    tenant_id: uuid.UUID,
    actor: str | None,
    action: str,
    resource_type: str | None = None,
    resource_id: str | uuid.UUID | None = None,
    payload: dict[str, Any] | None = None,
) -> Event:
    """Persist one audit event without mutating any existing audit row."""

    event = Event(
        tenant_id=tenant_id,
        actor=actor,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        payload=payload or {},
    )
    session.add(event)
    session.flush()
    return event
