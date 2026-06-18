"""Recommendation envelope surface (CV3.E3/E4/E5).

Read the explainable recommendation envelopes, act on them (accept / adjust /
override), and inspect the feedback loop (acceptance rate, regime signals).
Accepting routes to the approval workflow (CV6) — never a direct source write.
"""

from __future__ import annotations

import uuid
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.auth.dependencies import get_current_user, get_tenant_session, require_role
from api.auth.models import CurrentUser
from api.db.models.inventory import Item
from api.db.models.ml import Recommendation, RegimeSignal
from api.feedback.service import REASON_CODES, acceptance_rate, record_feedback

router = APIRouter(tags=["recommendations"], prefix="/recommendations")

READ_ROLES = ("admin", "planner", "manager", "finance")
ACT_ROLES = ("admin", "planner")
Decision = Literal["override", "adjust"]


class RecommendationRow(BaseModel):
    id: uuid.UUID
    type: str
    target_id: uuid.UUID
    item_number: str | None = None
    description: str | None = None
    claim: str
    confidence: float | None = None
    recommended_action: str | None = None
    capital_delta: float | None = None
    status: str
    model_version: str | None = None


class EnvelopeDetail(RecommendationRow):
    payload: dict[str, Any] = {}
    evidence: dict[str, Any] = {}
    assumptions: dict[str, Any] = {}
    approval_path: str | None = None


class RecommendationPage(BaseModel):
    recommendations: list[RecommendationRow]
    total: int
    page: int
    page_size: int


class RecommendationSummary(BaseModel):
    proposed: int
    actionable: int
    capital_delta: float
    avg_confidence: float
    by_action: dict[str, int]


class OverrideRequest(BaseModel):
    decision: Decision = "override"
    reason_code: str
    reason_note: str | None = None
    adjusted_payload: dict[str, Any] | None = None


class ActionResponse(BaseModel):
    id: uuid.UUID
    status: str


class AcceptanceRateRow(BaseModel):
    model_version: str
    total: int
    accepted: int
    adjusted: int
    overridden: int
    acceptance_rate: float


class RegimeSignalRow(BaseModel):
    id: uuid.UUID
    item_id: uuid.UUID
    item_number: str | None = None
    dimension: str
    override_count: int
    last_reason_note: str | None = None
    status: str
    is_regime_change: bool


def _row(rec: Recommendation, item: Item | None) -> RecommendationRow:
    payload = rec.payload or {}
    return RecommendationRow(
        id=rec.id,
        type=rec.type,
        target_id=rec.target_id,
        item_number=item.item_number if item else None,
        description=item.description if item else None,
        claim=rec.claim,
        confidence=float(rec.confidence) if rec.confidence is not None else None,
        recommended_action=payload.get("recommended_action"),
        capital_delta=payload.get("capital_delta"),
        status=rec.status,
        model_version=rec.model_version,
    )


@router.get("/summary", response_model=RecommendationSummary, summary="Recommendation KPIs")
def recommendations_summary(
    _user: Annotated[CurrentUser, Depends(require_role(*READ_ROLES))],
    session: Annotated[Session, Depends(get_tenant_session)],
) -> RecommendationSummary:
    proposed = 0
    actionable = 0
    capital = 0.0
    confidences: list[float] = []
    by_action: dict[str, int] = {}
    for rec in session.scalars(
        select(Recommendation).where(
            Recommendation.type == "reorder_policy", Recommendation.status == "proposed"
        )
    ).all():
        proposed += 1
        payload = rec.payload or {}
        action = payload.get("recommended_action", "hold")
        by_action[action] = by_action.get(action, 0) + 1
        if action != "hold":
            actionable += 1
        capital += float(payload.get("capital_delta") or 0.0)
        if rec.confidence is not None:
            confidences.append(float(rec.confidence))
    avg_conf = round(sum(confidences) / len(confidences), 4) if confidences else 0.0
    return RecommendationSummary(
        proposed=proposed,
        actionable=actionable,
        capital_delta=round(capital, 2),
        avg_confidence=avg_conf,
        by_action=by_action,
    )


@router.get("", response_model=RecommendationPage, summary="List recommendations")
def list_recommendations(
    _user: Annotated[CurrentUser, Depends(require_role(*READ_ROLES))],
    session: Annotated[Session, Depends(get_tenant_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
    rec_status: str | None = "proposed",
    action: str | None = None,
) -> RecommendationPage:
    conditions = [Recommendation.type == "reorder_policy"]
    if rec_status:
        conditions.append(Recommendation.status == rec_status)

    rows = session.execute(
        select(Recommendation, Item)
        .join(Item, Item.id == Recommendation.target_id, isouter=True)
        .where(*conditions)
        .order_by(Recommendation.confidence.desc().nullslast())
    ).all()

    # Action filter is on a JSONB payload field — filter in Python for clarity.
    filtered = [
        (rec, item)
        for rec, item in rows
        if action is None or (rec.payload or {}).get("recommended_action") == action
    ]
    total = len(filtered)
    start = (page - 1) * page_size
    page_rows = filtered[start : start + page_size]
    return RecommendationPage(
        recommendations=[_row(rec, item) for rec, item in page_rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/acceptance-rate", response_model=list[AcceptanceRateRow], summary="Acceptance rate")
def get_acceptance_rate(
    _user: Annotated[CurrentUser, Depends(require_role(*READ_ROLES))],
    session: Annotated[Session, Depends(get_tenant_session)],
) -> list[AcceptanceRateRow]:
    return [AcceptanceRateRow(**row) for row in acceptance_rate(session)]


@router.get(
    "/regime-signals", response_model=list[RegimeSignalRow], summary="Regime-change signals"
)
def get_regime_signals(
    _user: Annotated[CurrentUser, Depends(require_role(*READ_ROLES))],
    session: Annotated[Session, Depends(get_tenant_session)],
) -> list[RegimeSignalRow]:
    from api.feedback.service import REGIME_THRESHOLD

    rows = session.execute(
        select(RegimeSignal, Item.item_number)
        .join(Item, Item.id == RegimeSignal.item_id, isouter=True)
        .order_by(RegimeSignal.override_count.desc())
    ).all()
    return [
        RegimeSignalRow(
            id=sig.id,
            item_id=sig.item_id,
            item_number=item_number,
            dimension=sig.dimension,
            override_count=sig.override_count,
            last_reason_note=sig.last_reason_note,
            status=sig.status,
            is_regime_change=sig.override_count >= REGIME_THRESHOLD,
        )
        for sig, item_number in rows
    ]


@router.get(
    "/{recommendation_id}", response_model=EnvelopeDetail, summary="Recommendation envelope"
)
def recommendation_detail(
    recommendation_id: uuid.UUID,
    _user: Annotated[CurrentUser, Depends(require_role(*READ_ROLES))],
    session: Annotated[Session, Depends(get_tenant_session)],
) -> EnvelopeDetail:
    rec = session.get(Recommendation, recommendation_id)
    if rec is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found."
        )
    item = session.get(Item, rec.target_id)
    base = _row(rec, item)
    return EnvelopeDetail(
        **base.model_dump(),
        payload=dict(rec.payload or {}),
        evidence=dict(rec.evidence or {}),
        assumptions=dict(rec.assumptions or {}),
        approval_path=rec.approval_path,
    )


@router.post(
    "/{recommendation_id}/accept", response_model=ActionResponse, summary="Accept (-> approval)"
)
def accept_recommendation(
    recommendation_id: uuid.UUID,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_tenant_session)],
    _actor: Annotated[CurrentUser, Depends(require_role(*ACT_ROLES))],
) -> ActionResponse:
    rec = _open_recommendation(session, recommendation_id)
    record_feedback(session, user.tenant_id, rec, decision="accept")
    # Accept routes to the CV6 approval queue; never a direct source write.
    return ActionResponse(id=rec.id, status=rec.status)


@router.post(
    "/{recommendation_id}/override", response_model=ActionResponse, summary="Override / adjust"
)
def override_recommendation(
    recommendation_id: uuid.UUID,
    body: OverrideRequest,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_tenant_session)],
    _actor: Annotated[CurrentUser, Depends(require_role(*ACT_ROLES))],
) -> ActionResponse:
    if body.reason_code not in REASON_CODES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"reason_code must be one of {sorted(REASON_CODES)}.",
        )
    rec = _open_recommendation(session, recommendation_id)
    record_feedback(
        session,
        user.tenant_id,
        rec,
        decision=body.decision,
        reason_code=body.reason_code,
        reason_note=body.reason_note,
        adjusted_payload=body.adjusted_payload,
    )
    return ActionResponse(id=rec.id, status=rec.status)


def _open_recommendation(session: Session, recommendation_id: uuid.UUID) -> Recommendation:
    rec = session.get(Recommendation, recommendation_id)
    if rec is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found."
        )
    if rec.status != "proposed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Recommendation already actioned."
        )
    return rec
