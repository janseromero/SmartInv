"""Operational-risk surface (CV4.E3/E4).

The Risk & Criticality dashboard: portfolio KPIs, a plant x risk-class heatmap,
the top critical-spare exposures table, item drill-down with a grounded
(templated, no-LLM) narrative, and a "Mitigate" action that stages a
risk-mitigation envelope routed to the approval queue (CV6) via CV3's policy.
"""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.auth.dependencies import get_current_user, get_tenant_session, require_role
from api.auth.models import CurrentUser
from api.db.models.inventory import Balance, Item, Location, Supplier
from api.db.models.ml import Recommendation
from api.risk.model import RISK_VERSION

router = APIRouter(tags=["risk"], prefix="/risk")

READ_ROLES = ("admin", "planner", "manager", "finance")
ACT_ROLES = ("admin", "planner", "manager")
RISK_CLASSES = ("critical", "high", "moderate", "low")


class RiskItemRow(BaseModel):
    id: uuid.UUID
    item_number: str
    description: str | None = None
    criticality: int | None = None
    risk_score: int | None = None
    risk_class: str | None = None
    downtime_exposure: float = 0.0
    is_critical_spare: bool = False
    single_source: bool = False
    supplier_on_time_rate: float | None = None


class RiskItemsPage(BaseModel):
    items: list[RiskItemRow]
    total: int
    page: int
    page_size: int


class RiskSummary(BaseModel):
    downtime_exposure: float
    critical_spares: int
    critical_spare_coverage: float
    single_source_items: int
    obsolescence_candidates: int
    risk_distribution: dict[str, int]


class HeatmapRow(BaseModel):
    location_code: str
    scores: dict[str, int]  # risk dimension -> 0..100


class ExposureCell(BaseModel):
    location_code: str
    risk_class: str
    count: int
    exposure: float


# Risk dimensions surfaced in the Plant x dimension heatmap (CV4.E3.S2).
HEATMAP_DIMENSIONS = ("stockout", "lead_time", "supplier", "criticality")


class RiskItemDetail(RiskItemRow):
    breakdown: dict[str, float] = {}
    narrative: str
    has_mitigation_policy: bool


class MitigateResponse(BaseModel):
    recommendation_id: uuid.UUID
    status: str


def _exposure(item: Item) -> float:
    return float((item.risk_breakdown or {}).get("downtime_exposure", 0.0))


def _single_source(on_time_rate: float | None) -> bool:
    return on_time_rate is not None and float(on_time_rate) < 0.8


@router.get("/summary", response_model=RiskSummary, summary="Risk KPIs")
def risk_summary(
    _user: Annotated[CurrentUser, Depends(require_role(*READ_ROLES))],
    session: Annotated[Session, Depends(get_tenant_session)],
) -> RiskSummary:
    distribution = dict.fromkeys(RISK_CLASSES, 0)
    exposure = 0.0
    critical = 0
    covered = 0
    obsolescence = 0

    reliability = {
        r.id: r.on_time_rate
        for r in session.execute(select(Supplier.id, Supplier.on_time_rate)).all()
    }
    single_source = 0

    for item in session.scalars(select(Item)).all():
        if item.risk_class in distribution:
            distribution[item.risk_class] = distribution[item.risk_class] + 1
        breakdown = item.risk_breakdown or {}
        exposure += float(breakdown.get("downtime_exposure", 0.0))
        if item.is_critical_spare:
            critical += 1
            if float(breakdown.get("stockout", 0.0)) < 0.5:
                covered += 1
        if item.primary_supplier_id and _single_source(reliability.get(item.primary_supplier_id)):
            single_source += 1
        if float((item.score_dimensions or {}).get("obsolete", 0.0)) > 0:
            obsolescence += 1

    coverage = round(covered / critical * 100, 1) if critical else 100.0
    return RiskSummary(
        downtime_exposure=round(exposure, 2),
        critical_spares=critical,
        critical_spare_coverage=coverage,
        single_source_items=single_source,
        obsolescence_candidates=obsolescence,
        risk_distribution=distribution,
    )


@router.get("/heatmap", response_model=list[HeatmapRow], summary="Plant x risk-dimension heatmap")
def risk_heatmap(
    _user: Annotated[CurrentUser, Depends(require_role(*READ_ROLES))],
    session: Annotated[Session, Depends(get_tenant_session)],
) -> list[HeatmapRow]:
    """Average 0–100 risk-dimension score per plant (Plant × risk dimension)."""
    rows = session.execute(
        select(
            Location.location_code,
            func.avg(Item.risk_breakdown["stockout"].as_float()).label("stockout"),
            func.avg(Item.risk_breakdown["lead_time"].as_float()).label("lead_time"),
            func.avg(Item.risk_breakdown["supplier"].as_float()).label("supplier"),
            func.avg(Item.risk_breakdown["criticality"].as_float()).label("criticality"),
        )
        .select_from(Item)
        .join(Balance, Balance.item_id == Item.id)
        .join(Location, Location.id == Balance.location_id)
        .where(Item.risk_score.isnot(None))
        .group_by(Location.location_code)
        .order_by(Location.location_code)
    ).all()

    result: list[HeatmapRow] = []
    for r in rows:
        result.append(
            HeatmapRow(
                location_code=r.location_code,
                scores={
                    "stockout": round(float(r.stockout or 0) * 100),
                    "lead_time": round(float(r.lead_time or 0) * 100),
                    "supplier": round(float(r.supplier or 0) * 100),
                    # criticality is stored raw (1..5); normalise to 0..100.
                    "criticality": round((float(r.criticality or 1) - 1) / 4 * 100),
                },
            )
        )
    return result


@router.get("/exposure", response_model=list[ExposureCell], summary="Plant x risk-class exposure")
def risk_exposure(
    _user: Annotated[CurrentUser, Depends(require_role(*READ_ROLES))],
    session: Annotated[Session, Depends(get_tenant_session)],
) -> list[ExposureCell]:
    """Item count + downtime exposure per plant x risk class (Plant × risk class)."""
    rows = session.execute(
        select(
            Location.location_code,
            Item.risk_class,
            func.count(func.distinct(Item.id)).label("item_count"),
            func.coalesce(func.sum(Item.risk_breakdown["downtime_exposure"].as_float()), 0).label(
                "exposure"
            ),
        )
        .select_from(Item)
        .join(Balance, Balance.item_id == Item.id)
        .join(Location, Location.id == Balance.location_id)
        .where(Item.risk_class.isnot(None))
        .group_by(Location.location_code, Item.risk_class)
    ).all()
    return [
        ExposureCell(
            location_code=r.location_code,
            risk_class=r.risk_class,
            count=r.item_count,
            exposure=round(float(r.exposure or 0), 2),
        )
        for r in rows
    ]


@router.get("/items", response_model=RiskItemsPage, summary="Top risk exposures")
def list_risk_items(
    _user: Annotated[CurrentUser, Depends(require_role(*READ_ROLES))],
    session: Annotated[Session, Depends(get_tenant_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
    risk_class: str | None = None,
    critical_only: bool = False,
) -> RiskItemsPage:
    conditions: list[Any] = [Item.risk_score.isnot(None)]
    if risk_class:
        conditions.append(Item.risk_class == risk_class)
    if critical_only:
        conditions.append(Item.is_critical_spare.is_(True))

    total = session.scalar(select(func.count()).select_from(Item).where(*conditions)) or 0
    rows = session.execute(
        select(Item, Supplier.on_time_rate)
        .join(Supplier, Supplier.id == Item.primary_supplier_id, isouter=True)
        .where(*conditions)
        .order_by(Item.risk_score.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    ).all()
    return RiskItemsPage(
        items=[_row(item, on_time) for item, on_time in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/items/{item_id}", response_model=RiskItemDetail, summary="Risk item detail")
def risk_item_detail(
    item_id: uuid.UUID,
    _user: Annotated[CurrentUser, Depends(require_role(*READ_ROLES))],
    session: Annotated[Session, Depends(get_tenant_session)],
) -> RiskItemDetail:
    item = session.get(Item, item_id)
    if item is None or item.risk_score is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Risk item not found.")
    on_time = None
    if item.primary_supplier_id:
        supplier = session.get(Supplier, item.primary_supplier_id)
        on_time = supplier.on_time_rate if supplier else None
    base = _row(item, on_time)
    has_policy = (
        session.scalar(
            select(func.count())
            .select_from(Recommendation)
            .where(
                Recommendation.type == "reorder_policy",
                Recommendation.target_id == item.id,
            )
        )
        or 0
    ) > 0
    return RiskItemDetail(
        **base.model_dump(),
        breakdown={k: float(v) for k, v in (item.risk_breakdown or {}).items()},
        narrative=_narrative(item, base),
        has_mitigation_policy=has_policy,
    )


@router.post("/items/{item_id}/mitigate", response_model=MitigateResponse, summary="Mitigate risk")
def mitigate(
    item_id: uuid.UUID,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_tenant_session)],
    _actor: Annotated[CurrentUser, Depends(require_role(*ACT_ROLES))],
) -> MitigateResponse:
    item = session.get(Item, item_id)
    if item is None or item.risk_score is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Risk item not found.")

    # Reuse the CV3 reorder policy as the mitigation basis (CV4.E4.S2).
    policy = session.scalars(
        select(Recommendation)
        .where(
            Recommendation.type == "reorder_policy",
            Recommendation.target_id == item.id,
        )
        .order_by(Recommendation.created_at.desc())
    ).first()
    if policy is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No optimization policy for this item — run the optimizer first.",
        )

    exposure = _exposure(item)
    mitigation = Recommendation(
        tenant_id=user.tenant_id,
        model_id=policy.model_id,
        type="risk_mitigation",
        target_type="item",
        target_id=item.id,
        claim=(
            f"Raise stock to the recommended policy to mitigate "
            f"${exposure:,.0f} downtime exposure (risk {item.risk_score})."
        ),
        payload={
            "min_level": (policy.payload or {}).get("min_level"),
            "max_level": (policy.payload or {}).get("max_level"),
            "reorder_point": (policy.payload or {}).get("reorder_point"),
            "source_policy_id": str(policy.id),
            "downtime_exposure": exposure,
        },
        confidence=policy.confidence,
        evidence={
            "risk_score": item.risk_score,
            "risk_class": item.risk_class,
            "downtime_exposure": exposure,
            "breakdown": item.risk_breakdown or {},
        },
        assumptions={"risk_version": RISK_VERSION},
        model_version=RISK_VERSION,
        approval_path="cv6_workflow",
        status="proposed",
    )
    session.add(mitigation)
    session.flush()
    return MitigateResponse(recommendation_id=mitigation.id, status=mitigation.status)


def _row(item: Item, on_time_rate: float | None) -> RiskItemRow:
    return RiskItemRow(
        id=item.id,
        item_number=item.item_number,
        description=item.description,
        criticality=item.criticality,
        risk_score=item.risk_score,
        risk_class=item.risk_class,
        downtime_exposure=_exposure(item),
        is_critical_spare=item.is_critical_spare,
        single_source=_single_source(on_time_rate),
        supplier_on_time_rate=float(on_time_rate) if on_time_rate is not None else None,
    )


def _narrative(item: Item, row: RiskItemRow) -> str:
    """Grounded, templated risk narrative — no LLM, no invented numbers (CV4.E4.S5)."""
    parts = [
        f"{row.description or item.item_number} carries a {item.risk_class} operational risk "
        f"(score {item.risk_score})."
    ]
    if item.is_critical_spare and item.critical_reason:
        parts.append(item.critical_reason)
    if row.downtime_exposure > 0:
        parts.append(f"Estimated downtime exposure is ${row.downtime_exposure:,.0f}.")
    if row.single_source:
        rate = row.supplier_on_time_rate or 0.0
        parts.append(f"It is single-sourced from a supplier delivering on time only {rate:.0%}.")
    return " ".join(parts)
