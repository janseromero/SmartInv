"""Duplicate-detection review queue (CV2.E4).

Tenant-scoped, role-gated endpoints backing the duplicate queue: a list of
candidate pairs sorted by confidence, a side-by-side pair detail, and a review
action (merge / not-duplicate / hold). "Merge" never mutates source rows — it
stages a ``ml.recommendations`` envelope routed through CV6 approval.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session, aliased

from api.audit.service import record_audit_event
from api.auth.dependencies import get_current_user, get_tenant_session, require_role
from api.auth.models import CurrentUser
from api.db.models.inventory import Item
from api.db.models.ml import DuplicateCandidate
from api.dedup.service import propose_merge

router = APIRouter(tags=["duplicates"], prefix="/duplicates")

READ_ROLES = ("admin", "planner", "manager", "finance")
REVIEW_ROLES = ("admin", "planner")
ReviewDecision = Literal["merge", "not_duplicate", "hold"]


class ItemSide(BaseModel):
    id: uuid.UUID
    item_number: str
    description: str | None = None
    uom: str | None = None
    item_type: str | None = None
    status: str | None = None
    unit_cost: float | None = None
    health_score: int | None = None


class CandidateRow(BaseModel):
    id: uuid.UUID
    confidence: float
    band: str
    status: str
    model_version: str
    item_a: ItemSide
    item_b: ItemSide


class CandidateDetail(CandidateRow):
    features: dict[str, float] = {}


class CandidatePage(BaseModel):
    candidates: list[CandidateRow]
    total: int
    page: int
    page_size: int


class CandidateSummary(BaseModel):
    open: int
    probable: int
    possible: int
    resolved: int


class ReviewRequest(BaseModel):
    decision: ReviewDecision
    keep_item_id: uuid.UUID | None = None


class ReviewResponse(BaseModel):
    id: uuid.UUID
    status: str
    recommendation_id: uuid.UUID | None = None


def _side(item: Item) -> ItemSide:
    return ItemSide(
        id=item.id,
        item_number=item.item_number,
        description=item.description,
        uom=item.uom,
        item_type=item.item_type,
        status=item.status,
        unit_cost=float(item.unit_cost) if item.unit_cost is not None else None,
        health_score=item.health_score,
    )


@router.get("/summary", response_model=CandidateSummary, summary="Duplicate queue KPIs")
def duplicates_summary(
    _user: Annotated[CurrentUser, Depends(require_role(*READ_ROLES))],
    session: Annotated[Session, Depends(get_tenant_session)],
) -> CandidateSummary:
    counts = {"open": 0, "probable": 0, "possible": 0, "resolved": 0}
    for cand in session.scalars(select(DuplicateCandidate)).all():
        if cand.status == "open":
            counts["open"] += 1
            counts[cand.band] = counts.get(cand.band, 0) + 1
        else:
            counts["resolved"] += 1
    return CandidateSummary(**counts)


@router.get("", response_model=CandidatePage, summary="List duplicate candidates")
def list_candidates(
    _user: Annotated[CurrentUser, Depends(require_role(*READ_ROLES))],
    session: Annotated[Session, Depends(get_tenant_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
    band: str | None = None,
    candidate_status: str | None = "open",
) -> CandidatePage:
    item_a = aliased(Item)
    item_b = aliased(Item)

    conditions = []
    if band:
        conditions.append(DuplicateCandidate.band == band)
    if candidate_status:
        conditions.append(DuplicateCandidate.status == candidate_status)

    total = (
        session.scalar(select(func.count()).select_from(DuplicateCandidate).where(*conditions)) or 0
    )

    rows = session.execute(
        select(DuplicateCandidate, item_a, item_b)
        .join(item_a, item_a.id == DuplicateCandidate.item_a_id)
        .join(item_b, item_b.id == DuplicateCandidate.item_b_id)
        .where(*conditions)
        .order_by(DuplicateCandidate.confidence.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    ).all()

    candidates = [
        CandidateRow(
            id=cand.id,
            confidence=float(cand.confidence),
            band=cand.band,
            status=cand.status,
            model_version=cand.model_version,
            item_a=_side(a),
            item_b=_side(b),
        )
        for cand, a, b in rows
    ]
    return CandidatePage(candidates=candidates, total=total, page=page, page_size=page_size)


@router.get("/{candidate_id}", response_model=CandidateDetail, summary="Candidate pair detail")
def candidate_detail(
    candidate_id: uuid.UUID,
    _user: Annotated[CurrentUser, Depends(require_role(*READ_ROLES))],
    session: Annotated[Session, Depends(get_tenant_session)],
) -> CandidateDetail:
    cand = session.get(DuplicateCandidate, candidate_id)
    if cand is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found.")
    a = session.get(Item, cand.item_a_id)
    b = session.get(Item, cand.item_b_id)
    if a is None or b is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paired item missing.")
    return CandidateDetail(
        id=cand.id,
        confidence=float(cand.confidence),
        band=cand.band,
        status=cand.status,
        model_version=cand.model_version,
        item_a=_side(a),
        item_b=_side(b),
        features={k: float(v) for k, v in (cand.features or {}).items()},
    )


@router.post("/{candidate_id}/review", response_model=ReviewResponse, summary="Review a candidate")
def review_candidate(
    candidate_id: uuid.UUID,
    body: ReviewRequest,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_tenant_session)],
    _reviewer: Annotated[CurrentUser, Depends(require_role(*REVIEW_ROLES))],
) -> ReviewResponse:
    cand = session.get(DuplicateCandidate, candidate_id)
    if cand is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found.")
    if cand.status != "open":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Candidate already reviewed."
        )

    recommendation_id: uuid.UUID | None = None
    if body.decision == "merge":
        keep = body.keep_item_id
        if keep not in (cand.item_a_id, cand.item_b_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="keep_item_id must be one of the paired items.",
            )
        recommendation = propose_merge(session, user.tenant_id, cand, keep, None)
        session.flush()
        recommendation_id = recommendation.id
    elif body.decision == "not_duplicate":
        cand.status = "not_duplicate"
        cand.reviewed_at = datetime.now(UTC)
    else:  # hold
        cand.status = "hold"
        cand.reviewed_at = datetime.now(UTC)

    record_audit_event(
        session,
        tenant_id=user.tenant_id,
        actor=user.email or user.sub,
        action="duplicate.review",
        resource_type="ml.duplicate_candidate",
        resource_id=cand.id,
        payload={
            "decision": body.decision,
            "recommendation_id": str(recommendation_id) if recommendation_id else None,
        },
    )
    return ReviewResponse(id=cand.id, status=cand.status, recommendation_id=recommendation_id)
