"""Risk-scoring orchestration: gather, score, persist, register (CV4.E1/E2).

Aggregates per-item risk inputs (criticality, balance cover, forecast demand,
CV3 reorder point, lead time, supplier reliability), runs the pure engine,
writes the score + critical-spare flag back onto ``inventory.items``, and
registers ``risk-v1`` in ``ml.model_registry``. On-demand recompute; nightly
schedule deferred (mirrors CV2/CV3).
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from api.db.models.inventory import Balance, Item, Supplier
from api.db.models.ml import ModelRegistry, Prediction, Recommendation
from api.forecast.model import FORECAST_VERSION
from api.risk.engine import score_risk
from api.risk.model import (
    DEFAULT_LEAD_TIME_DAYS,
    LIKELIHOOD_WEIGHTS,
    RISK_VERSION,
    RiskInput,
)

RiskSummary = dict[str, int]

_SINGLE_SOURCE_RELIABILITY = 0.8  # below this, a sole supplier is a real risk


def ensure_risk_version(session: Session) -> None:
    session.execute(
        pg_insert(ModelRegistry)
        .values(
            name="operational_risk",
            version=RISK_VERSION,
            task="risk",
            framework="deterministic",
            params=LIKELIHOOD_WEIGHTS,
            metrics={},
            status="active",
        )
        .on_conflict_do_nothing(index_elements=["name", "version"])
    )


def _demand_rates(session: Session) -> dict[uuid.UUID, float]:
    rows = session.execute(
        select(Prediction.target_id, Prediction.value).where(
            Prediction.model_version == FORECAST_VERSION
        )
    ).all()
    return {r.target_id: float(r.value.get("rate", 0.0)) for r in rows}


def _reorder_points(session: Session) -> dict[uuid.UUID, float]:
    rows = session.execute(
        select(Recommendation.target_id, Recommendation.payload).where(
            Recommendation.type == "reorder_policy"
        )
    ).all()
    points: dict[uuid.UUID, float] = {}
    for r in rows:
        rop = (r.payload or {}).get("reorder_point")
        if rop is not None:
            points[r.target_id] = float(rop)
    return points


def run_risk_scan(session: Session, tenant_id: uuid.UUID) -> RiskSummary:
    ensure_risk_version(session)

    balances = {
        row.item_id: row
        for row in session.execute(
            select(
                Balance.item_id,
                func.sum(Balance.on_hand).label("on_hand"),
                func.sum(Balance.min_level).label("min_level"),
            ).group_by(Balance.item_id)
        ).all()
    }
    demand = _demand_rates(session)
    reorder = _reorder_points(session)
    reliability = {
        row.id: float(row.on_time_rate) if row.on_time_rate is not None else None
        for row in session.execute(select(Supplier.id, Supplier.on_time_rate)).all()
    }

    summary: RiskSummary = {"scored": 0, "critical_spares": 0}
    mappings: list[dict[str, object]] = []

    for item in session.execute(
        select(
            Item.id,
            Item.criticality,
            Item.unit_cost,
            Item.lead_time_days,
            Item.primary_supplier_id,
        )
    ).all():
        bal = balances.get(item.id)
        on_time = reliability.get(item.primary_supplier_id) if item.primary_supplier_id else None
        single_source = on_time is not None and on_time < _SINGLE_SOURCE_RELIABILITY

        result = score_risk(
            RiskInput(
                criticality=item.criticality,
                on_hand=float(bal.on_hand) if bal and bal.on_hand is not None else 0.0,
                demand_rate=demand.get(item.id, 0.0),
                reorder_point=reorder.get(item.id),
                lead_time_days=float(item.lead_time_days or DEFAULT_LEAD_TIME_DAYS),
                on_time_rate=on_time,
                unit_cost=float(item.unit_cost) if item.unit_cost is not None else None,
                single_source=single_source,
            )
        )

        mappings.append(
            {
                "id": item.id,
                "risk_score": result.score,
                "risk_class": str(result.risk_class),
                "risk_version": result.version,
                "risk_breakdown": {
                    **result.breakdown,
                    "likelihood": result.likelihood,
                    "consequence": result.consequence,
                    "downtime_exposure": result.downtime_exposure,
                },
                "is_critical_spare": result.is_critical_spare,
                "critical_reason": result.critical_reason,
            }
        )
        summary["scored"] += 1
        summary[str(result.risk_class)] = summary.get(str(result.risk_class), 0) + 1
        if result.is_critical_spare:
            summary["critical_spares"] += 1

    if mappings:
        session.execute(update(Item), mappings)

    return summary
