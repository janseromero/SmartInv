"""Forecasting orchestration: bucket demand, forecast, persist, register (CV3.E1).

Buckets each item's issue history into fixed periods, runs the pure Croston/TSB
engine, and persists quantile forecasts into ``ml.predictions`` with a pinned
``model_version`` and an input fingerprint (reproducibility, D2). On-demand
recompute (CLI / admin); nightly schedule deferred (mirrors CV2).
"""

from __future__ import annotations

import hashlib
import json
import uuid
from collections import defaultdict
from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from api.db.models.inventory import Item, Transaction
from api.db.models.ml import ModelRegistry, Prediction
from api.forecast.engine import forecast_demand
from api.forecast.model import (
    ALPHA,
    BETA,
    FORECAST_VERSION,
    PERIOD_DAYS,
    ForecastInput,
    ForecastResult,
)

ForecastSummary = dict[str, int]

HISTORY_PERIODS = 18  # ~18 months of monthly buckets
DEFAULT_HORIZON = 12

_PARAMS = {"alpha": ALPHA, "beta": BETA, "period_days": PERIOD_DAYS, "history": HISTORY_PERIODS}


def ensure_forecast_version(session: Session) -> uuid.UUID:
    """Register the active forecast version; return its model-registry id."""
    session.execute(
        pg_insert(ModelRegistry)
        .values(
            name="demand_forecast",
            version=FORECAST_VERSION,
            task="forecast",
            framework="deterministic",
            params=_PARAMS,
            metrics={},
            status="active",
        )
        .on_conflict_do_nothing(index_elements=["name", "version"])
    )
    model_id = session.scalar(
        select(ModelRegistry.id).where(
            ModelRegistry.name == "demand_forecast",
            ModelRegistry.version == FORECAST_VERSION,
        )
    )
    if model_id is None:  # pragma: no cover — insert+select cannot both fail
        raise RuntimeError("forecast model registry entry missing after upsert")
    return model_id


def _buckets(session: Session, now: datetime) -> dict[uuid.UUID, list[float]]:
    """Per item, demand quantity per period (oldest -> newest), zero-filled."""
    series: dict[uuid.UUID, list[float]] = defaultdict(lambda: [0.0] * HISTORY_PERIODS)
    rows = session.execute(
        select(Transaction.item_id, Transaction.quantity, Transaction.txn_date).where(
            Transaction.type == "issue", Transaction.txn_date.isnot(None)
        )
    ).all()
    for row in rows:
        age_days = (now - row.txn_date).days
        period_back = age_days // PERIOD_DAYS  # 0 = current period
        if 0 <= period_back < HISTORY_PERIODS:
            series[row.item_id][HISTORY_PERIODS - 1 - period_back] += float(row.quantity)
    return series


def _fingerprint(series: list[float]) -> str:
    payload = json.dumps(series, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()[:32]


def forecast_for(series: list[float], horizon: int = DEFAULT_HORIZON) -> ForecastResult:
    return forecast_demand(ForecastInput(periods=series, horizon=horizon))


def run_forecast(session: Session, tenant_id: uuid.UUID) -> ForecastSummary:
    model_id = ensure_forecast_version(session)
    now = datetime.now(UTC)

    # Idempotent: clear this model's prior forecasts, then re-insert.
    session.execute(delete(Prediction).where(Prediction.model_id == model_id))

    series_by_item = _buckets(session, now)
    summary: ForecastSummary = {"forecasted": 0}

    all_items = session.scalars(select(Item.id)).all()
    for item_id in all_items:
        series = series_by_item.get(item_id, [0.0] * HISTORY_PERIODS)
        result = forecast_for(series)
        session.execute(
            pg_insert(Prediction).values(
                tenant_id=tenant_id,
                model_id=model_id,
                target_type="item",
                target_id=item_id,
                horizon=f"{result.horizon}p",
                value={
                    "rate": result.rate,
                    "p50": result.p50,
                    "p80": result.p80,
                    "p95": result.p95,
                    "cv": result.cv,
                    "method": str(result.method),
                    "diagnostics": result.diagnostics,
                },
                input_fingerprint=_fingerprint(series),
                model_version=result.version,
                predicted_at=now,
            )
        )
        summary["forecasted"] += 1
        summary[str(result.method)] = summary.get(str(result.method), 0) + 1

    return summary
