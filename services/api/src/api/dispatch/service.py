"""Dispatch service: enqueue and deliver approved source-system writes (CV6.E4).

The dispatcher is synchronous and idempotent so it runs identically from an
admin endpoint today and from a Dramatiq worker later (the worker simply calls
``process_pending``). Retries are bounded; a permanently failed write lands in
``dead_letter`` and emits a structured incident audit event — never silently
swallowed (Done Condition).
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.audit.service import record_audit_event
from api.db.models.ml import Recommendation
from api.db.models.workflow import SourceWrite
from api.dispatch.writer import SourceWriteError, SourceWriter

# Recommendation type -> source-system operation. Unknown types pass through.
OPERATION_BY_TYPE = {
    "reorder_policy": "min_max_change",
    "risk_mitigation": "min_max_change",
    "item_merge": "item_merge",
}


def enqueue_source_write(
    session: Session,
    *,
    tenant_id: uuid.UUID,
    recommendation: Recommendation,
    approval_id: uuid.UUID | None,
    target_system: str = "maximo",
    max_attempts: int = 3,
) -> SourceWrite:
    """Queue a source-system write for an approved recommendation (idempotent).

    Re-enqueuing the same recommendation returns the existing row, so a repeated
    approval can never create a duplicate write.
    """

    idempotency_key = f"recwrite:{recommendation.id}"
    existing = session.scalar(
        select(SourceWrite).where(
            SourceWrite.tenant_id == tenant_id,
            SourceWrite.idempotency_key == idempotency_key,
        )
    )
    if existing is not None:
        return existing

    operation = OPERATION_BY_TYPE.get(recommendation.type, recommendation.type)
    write = SourceWrite(
        tenant_id=tenant_id,
        recommendation_id=recommendation.id,
        approval_id=approval_id,
        target_system=target_system,
        operation=operation,
        payload=dict(recommendation.payload or {}),
        idempotency_key=idempotency_key,
        status="pending",
        max_attempts=max_attempts,
    )
    session.add(write)
    session.flush()
    return write


def _deliver_one(session: Session, write: SourceWrite, writer: SourceWriter, *, actor: str) -> None:
    write.attempts += 1
    try:
        receipt = writer.write(
            operation=write.operation,
            payload=write.payload,
            idempotency_key=write.idempotency_key,
        )
    except SourceWriteError as exc:
        write.last_error = str(exc)
        permanent = exc.permanent or write.attempts >= write.max_attempts
        write.status = "dead_letter" if permanent else "pending"
        if permanent:
            record_audit_event(
                session,
                tenant_id=write.tenant_id,
                actor=actor,
                action="dispatch.incident",
                resource_type="workflow.source_write",
                resource_id=write.id,
                payload={
                    "operation": write.operation,
                    "attempts": write.attempts,
                    "error": str(exc),
                },
            )
        return

    write.status = "delivered"
    write.last_error = None
    write.receipt = {"external_id": receipt.external_id, "detail": receipt.detail}

    if write.recommendation_id is not None:
        rec = session.get(Recommendation, write.recommendation_id)
        if rec is not None:
            rec.status = "delivered"
            rec.payload = {**(rec.payload or {}), "_delivery_external_id": receipt.external_id}

    record_audit_event(
        session,
        tenant_id=write.tenant_id,
        actor=actor,
        action="dispatch.delivered",
        resource_type="workflow.source_write",
        resource_id=write.id,
        payload={"operation": write.operation, "external_id": receipt.external_id},
    )


def process_pending(
    session: Session,
    *,
    tenant_id: uuid.UUID,
    writer: SourceWriter,
    actor: str = "dispatcher",
    limit: int = 100,
) -> dict[str, int]:
    """Deliver pending writes for a tenant; return a status tally."""

    pending = list(
        session.scalars(
            select(SourceWrite)
            .where(SourceWrite.tenant_id == tenant_id, SourceWrite.status == "pending")
            .order_by(SourceWrite.created_at.asc())
            .limit(limit)
        ).all()
    )
    for write in pending:
        _deliver_one(session, write, writer, actor=actor)
    session.flush()

    tally = {"processed": len(pending), "delivered": 0, "pending": 0, "dead_letter": 0}
    for write in pending:
        tally[write.status] = tally.get(write.status, 0) + 1
    return tally
