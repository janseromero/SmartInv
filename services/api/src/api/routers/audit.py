"""Audit trail query API (CV6.E3)."""

from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.auth.dependencies import get_tenant_session, require_role
from api.auth.models import CurrentUser
from api.db.models.audit import Event

router = APIRouter(prefix="/audit", tags=["audit"])

READ_ROLES = ("admin", "finance")


class AuditEventResponse(BaseModel):
    id: int
    actor: str | None
    action: str
    resource_type: str | None
    resource_id: str | None
    payload: dict[str, object]
    occurred_at: str


class AuditPageResponse(BaseModel):
    events: list[AuditEventResponse]
    total: int


def _query_events(
    session: Session,
    *,
    actor: str | None,
    action: str | None,
    resource_type: str | None,
    since: datetime | None,
    until: datetime | None,
    limit: int,
) -> list[Event]:
    stmt = select(Event).order_by(Event.occurred_at.desc(), Event.id.desc()).limit(limit)
    if actor:
        stmt = stmt.where(Event.actor == actor)
    if action:
        stmt = stmt.where(Event.action == action)
    if resource_type:
        stmt = stmt.where(Event.resource_type == resource_type)
    if since:
        stmt = stmt.where(Event.occurred_at >= since)
    if until:
        stmt = stmt.where(Event.occurred_at <= until)
    return list(session.scalars(stmt).all())


def _row(event: Event) -> AuditEventResponse:
    return AuditEventResponse(
        id=event.id,
        actor=event.actor,
        action=event.action,
        resource_type=event.resource_type,
        resource_id=event.resource_id,
        payload=event.payload,
        occurred_at=event.occurred_at.isoformat(),
    )


@router.get("/events", response_model=AuditPageResponse)
def list_audit_events(
    _reader: Annotated[CurrentUser, Depends(require_role(*READ_ROLES))],
    session: Annotated[Session, Depends(get_tenant_session)],
    actor: str | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> AuditPageResponse:
    events = _query_events(
        session,
        actor=actor,
        action=action,
        resource_type=resource_type,
        since=since,
        until=until,
        limit=limit,
    )
    return AuditPageResponse(events=[_row(event) for event in events], total=len(events))


@router.get("/events.csv", response_class=Response)
def export_audit_events_csv(
    _reader: Annotated[CurrentUser, Depends(require_role(*READ_ROLES))],
    session: Annotated[Session, Depends(get_tenant_session)],
    actor: str | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    limit: Annotated[int, Query(ge=1, le=5000)] = 1000,
) -> Response:
    events = _query_events(
        session,
        actor=actor,
        action=action,
        resource_type=resource_type,
        since=since,
        until=until,
        limit=limit,
    )
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["id", "occurred_at", "actor", "action", "resource_type", "resource_id"])
    for event in events:
        writer.writerow(
            [
                event.id,
                event.occurred_at.isoformat(),
                event.actor or "",
                event.action,
                event.resource_type or "",
                event.resource_id or "",
            ]
        )
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="audit-events.csv"'},
    )
