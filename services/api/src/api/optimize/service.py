"""Optimization orchestration: gather, optimize, build envelopes, persist (CV3.E2/E3).

Pulls each item's forecast (``ml.predictions``), balance, unit cost, and lead
time, runs the deterministic optimizer, and persists each recommendation as a
full envelope in ``ml.recommendations`` (claim, evidence, confidence,
assumptions, model_version, approval_path). Envelopes are append-only: a
re-run replaces only still-``proposed`` rows, never an accepted/overridden one
(CV3.E3 immutability). On-demand recompute; nightly schedule deferred.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from api.db.models.inventory import Balance, Item
from api.db.models.ml import ModelRegistry, Prediction, Recommendation
from api.forecast.model import FORECAST_VERSION
from api.optimize.engine import optimize_item
from api.optimize.model import (
    DEFAULT_LEAD_TIME_DAYS,
    DEFAULT_SERVICE_LEVEL,
    HOLDING_RATE,
    MONTE_CARLO_SEED,
    OPT_VERSION,
    ORDERING_COST,
    Action,
    OptimizeInput,
)

OptimizeSummary = dict[str, int]

_PARAMS = {
    "holding_rate": HOLDING_RATE,
    "ordering_cost": ORDERING_COST,
    "service_level": DEFAULT_SERVICE_LEVEL,
    "mc_seed": MONTE_CARLO_SEED,
}
# Below this stockout improvement we leave the policy alone (no nagging).
_MIN_ACTION = Action.HOLD


def ensure_opt_version(session: Session) -> uuid.UUID:
    session.execute(
        pg_insert(ModelRegistry)
        .values(
            name="inventory_optimization",
            version=OPT_VERSION,
            task="optimization",
            framework="deterministic",
            params=_PARAMS,
            metrics={},
            status="active",
        )
        .on_conflict_do_nothing(index_elements=["name", "version"])
    )
    model_id = session.scalar(
        select(ModelRegistry.id).where(
            ModelRegistry.name == "inventory_optimization",
            ModelRegistry.version == OPT_VERSION,
        )
    )
    if model_id is None:  # pragma: no cover — insert+select cannot both fail
        raise RuntimeError("optimization model registry entry missing after upsert")
    return model_id


def _forecasts(session: Session) -> dict[uuid.UUID, dict[str, Any]]:
    rows = session.execute(
        select(Prediction.target_id, Prediction.value).where(
            Prediction.model_version == FORECAST_VERSION
        )
    ).all()
    return {row.target_id: row.value for row in rows}


def _balances(session: Session) -> dict[uuid.UUID, tuple[float, float | None, float | None]]:
    rows = session.execute(
        select(
            Balance.item_id,
            func.sum(Balance.on_hand).label("on_hand"),
            func.sum(Balance.min_level).label("min_level"),
            func.sum(Balance.max_level).label("max_level"),
        ).group_by(Balance.item_id)
    ).all()
    return {
        r.item_id: (
            float(r.on_hand or 0),
            float(r.min_level) if r.min_level is not None else None,
            float(r.max_level) if r.max_level is not None else None,
        )
        for r in rows
    }


def run_optimization(session: Session, tenant_id: uuid.UUID) -> OptimizeSummary:
    model_id = ensure_opt_version(session)

    # Append-only: drop only still-proposed reorder policies, then regenerate.
    session.execute(
        delete(Recommendation).where(
            Recommendation.type == "reorder_policy", Recommendation.status == "proposed"
        )
    )

    forecasts = _forecasts(session)
    balances = _balances(session)

    summary: OptimizeSummary = {"recommendations": 0, "actionable": 0}

    for item in session.execute(
        select(Item.id, Item.unit_cost, Item.lead_time_days, Item.item_number)
    ).all():
        fc = forecasts.get(item.id)
        if not fc or float(fc.get("rate", 0)) <= 0:
            continue  # no demand signal — nothing to optimize
        on_hand, current_min, current_max = balances.get(item.id, (0.0, None, None))

        result = optimize_item(
            OptimizeInput(
                demand_rate=float(fc["rate"]),
                demand_cv=float(fc.get("cv", 0.0)),
                unit_cost=float(item.unit_cost) if item.unit_cost is not None else None,
                on_hand=on_hand,
                current_min=current_min,
                current_max=current_max,
                lead_time_days=float(item.lead_time_days or DEFAULT_LEAD_TIME_DAYS),
                demand_events=int(fc.get("diagnostics", {}).get("demand_events", 0)),
            )
        )

        summary["recommendations"] += 1
        action = result.recommended_action
        summary[str(action)] = summary.get(str(action), 0) + 1
        if action is not Action.HOLD:
            summary["actionable"] += 1

        claim = (
            f"Set min/max to {result.min_level}/{result.max_level} "
            f"(reorder at {result.reorder_point}); stockout risk "
            f"{result.stockout_prob:.0%} vs {result.current_stockout_prob:.0%} today."
        )
        session.add(
            Recommendation(
                tenant_id=tenant_id,
                model_id=model_id,
                type="reorder_policy",
                target_type="item",
                target_id=item.id,
                claim=claim,
                payload={
                    "min_level": result.min_level,
                    "max_level": result.max_level,
                    "reorder_point": result.reorder_point,
                    "safety_stock": result.safety_stock,
                    "eoq": result.eoq,
                    "recommended_action": str(action),
                    "current_min": current_min,
                    "current_max": current_max,
                    "on_hand": on_hand,
                    "capital_delta": result.capital_delta,
                },
                confidence=result.confidence,
                evidence={
                    "demand_rate": float(fc["rate"]),
                    "demand_cv": float(fc.get("cv", 0.0)),
                    "forecast_method": fc.get("method"),
                    "lead_time_days": float(item.lead_time_days or DEFAULT_LEAD_TIME_DAYS),
                    "stockout_prob": result.stockout_prob,
                    "current_stockout_prob": result.current_stockout_prob,
                    "pareto": [
                        {
                            "service_level": p.service_level,
                            "capital": p.capital,
                            "stockout_prob": p.stockout_prob,
                        }
                        for p in result.pareto
                    ],
                },
                assumptions={
                    "service_level": DEFAULT_SERVICE_LEVEL,
                    "holding_rate": HOLDING_RATE,
                    "ordering_cost": ORDERING_COST,
                    "mc_seed": MONTE_CARLO_SEED,
                    "forecast_version": FORECAST_VERSION,
                    "optimizer_version": OPT_VERSION,
                },
                model_version=OPT_VERSION,
                approval_path="cv6_workflow",
                status="proposed",
            )
        )

    return summary
