"""Anomaly review surface (CV2.E5).

Tenant-scoped, role-gated endpoints backing the "Anomalies — last 7 days"
panel: a summary, a filterable list (type / severity / window / status), a
detail with drill-down to the source transaction, and an acknowledge/dismiss
review action.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.audit.service import record_audit_event
from api.auth.dependencies import get_current_user, get_tenant_session, require_role
from api.auth.models import CurrentUser
from api.db.models.inventory import Item, Location, Transaction
from api.db.models.ml import Anomaly

router = APIRouter(tags=["anomalies"], prefix="/anomalies")

READ_ROLES = ("admin", "planner", "manager", "finance")
REVIEW_ROLES = ("admin", "planner")
ReviewDecision = Literal["acknowledge", "dismiss"]


class AnomalyRow(BaseModel):
    id: uuid.UUID
    type: str
    target_type: str
    target_id: uuid.UUID
    source_record_id: str | None = None
    score: float
    severity: str
    status: str
    detected_for: datetime | None = None
    model_version: str
    cause: str | None = None


class TransactionRef(BaseModel):
    source_id: str
    item_number: str | None = None
    description: str | None = None
    location_code: str | None = None
    quantity: float
    unit_cost: float | None = None
    txn_date: datetime | None = None


class AnomalyDetail(AnomalyRow):
    evidence: dict[str, float | str] = {}
    transaction: TransactionRef | None = None


class AnomalyPage(BaseModel):
    anomalies: list[AnomalyRow]
    total: int
    page: int
    page_size: int


class AnomalySummary(BaseModel):
    open: int
    crit: int
    last_7_days: int
    by_type: dict[str, int]


class ReviewRequest(BaseModel):
    decision: ReviewDecision


class ReviewResponse(BaseModel):
    id: uuid.UUID
    status: str


def _row(anomaly: Anomaly) -> AnomalyRow:
    cause = anomaly.evidence.get("cause") if anomaly.evidence else None
    return AnomalyRow(
        id=anomaly.id,
        type=anomaly.type,
        target_type=anomaly.target_type,
        target_id=anomaly.target_id,
        source_record_id=anomaly.source_record_id,
        score=float(anomaly.score),
        severity=anomaly.severity,
        status=anomaly.status,
        detected_for=anomaly.detected_for,
        model_version=anomaly.model_version,
        cause=str(cause) if cause is not None else None,
    )


@router.get("/summary", response_model=AnomalySummary, summary="Anomaly KPIs")
def anomalies_summary(
    _user: Annotated[CurrentUser, Depends(require_role(*READ_ROLES))],
    session: Annotated[Session, Depends(get_tenant_session)],
) -> AnomalySummary:
    cutoff = datetime.now(UTC) - timedelta(days=7)
    open_total = 0
    crit = 0
    last_7 = 0
    by_type: dict[str, int] = {}
    for row in session.scalars(select(Anomaly).where(Anomaly.status == "open")).all():
        open_total += 1
        by_type[row.type] = by_type.get(row.type, 0) + 1
        if row.severity == "crit":
            crit += 1
        if row.detected_for is not None and row.detected_for >= cutoff:
            last_7 += 1
    return AnomalySummary(open=open_total, crit=crit, last_7_days=last_7, by_type=by_type)


@router.get("", response_model=AnomalyPage, summary="List anomalies")
def list_anomalies(
    _user: Annotated[CurrentUser, Depends(require_role(*READ_ROLES))],
    session: Annotated[Session, Depends(get_tenant_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
    type: str | None = None,
    severity: str | None = None,
    anomaly_status: str | None = "open",
    window_days: Annotated[int | None, Query(ge=1)] = None,
) -> AnomalyPage:
    conditions = []
    if type:
        conditions.append(Anomaly.type == type)
    if severity:
        conditions.append(Anomaly.severity == severity)
    if anomaly_status:
        conditions.append(Anomaly.status == anomaly_status)
    if window_days is not None:
        cutoff = datetime.now(UTC) - timedelta(days=window_days)
        conditions.append(Anomaly.detected_for >= cutoff)

    total = session.scalar(select(func.count()).select_from(Anomaly).where(*conditions)) or 0
    rows = session.scalars(
        select(Anomaly)
        .where(*conditions)
        .order_by(
            Anomaly.severity.desc(), Anomaly.detected_for.desc().nullslast(), Anomaly.score.desc()
        )
        .limit(page_size)
        .offset((page - 1) * page_size)
    ).all()
    return AnomalyPage(
        anomalies=[_row(a) for a in rows], total=total, page=page, page_size=page_size
    )


@router.get("/{anomaly_id}", response_model=AnomalyDetail, summary="Anomaly detail + drill-down")
def anomaly_detail(
    anomaly_id: uuid.UUID,
    _user: Annotated[CurrentUser, Depends(require_role(*READ_ROLES))],
    session: Annotated[Session, Depends(get_tenant_session)],
) -> AnomalyDetail:
    anomaly = session.get(Anomaly, anomaly_id)
    if anomaly is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Anomaly not found.")

    txn_ref: TransactionRef | None = None
    if anomaly.target_type == "transaction":
        row = session.execute(
            select(
                Transaction.source_id,
                Item.item_number,
                Item.description,
                Location.location_code,
                Transaction.quantity,
                Transaction.unit_cost,
                Transaction.txn_date,
            )
            .join(Item, Item.id == Transaction.item_id)
            .join(Location, Location.id == Transaction.location_id, isouter=True)
            .where(Transaction.id == anomaly.target_id)
        ).first()
        if row is not None:
            txn_ref = TransactionRef(
                source_id=row.source_id,
                item_number=row.item_number,
                description=row.description,
                location_code=row.location_code,
                quantity=float(row.quantity),
                unit_cost=float(row.unit_cost) if row.unit_cost is not None else None,
                txn_date=row.txn_date,
            )

    base = _row(anomaly)
    return AnomalyDetail(
        **base.model_dump(),
        evidence=dict(anomaly.evidence or {}),
        transaction=txn_ref,
    )


@router.post("/{anomaly_id}/review", response_model=ReviewResponse, summary="Review an anomaly")
def review_anomaly(
    anomaly_id: uuid.UUID,
    body: ReviewRequest,
    _reviewer: Annotated[CurrentUser, Depends(require_role(*REVIEW_ROLES))],
    session: Annotated[Session, Depends(get_tenant_session)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> ReviewResponse:
    anomaly = session.get(Anomaly, anomaly_id)
    if anomaly is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Anomaly not found.")
    anomaly.status = "acknowledged" if body.decision == "acknowledge" else "dismissed"
    anomaly.reviewed_at = datetime.now(UTC)
    record_audit_event(
        session,
        tenant_id=user.tenant_id,
        actor=user.email or user.sub,
        action="anomaly.review",
        resource_type="ml.anomaly",
        resource_id=anomaly.id,
        payload={"decision": body.decision, "status": anomaly.status},
    )
    return ReviewResponse(id=anomaly.id, status=anomaly.status)
