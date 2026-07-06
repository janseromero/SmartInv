"""Demand-forecasting read surface (CV3.E1).

Exposes the persisted Croston/TSB forecasts (``ml.predictions``) for the Demand
Forecasting screen: portfolio KPIs, a paginated per-item table, and an item
drill-down that pairs the probabilistic bands with the item's bucketed demand
history so the UI can plot history + a flat projection with a confidence band.

Read-only: forecasting produces no state changes, so there is no act-role and no
approval path here. Every figure is pinned to the active ``forecast-croston-v1``
model version (reproducibility, D2).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.auth.dependencies import get_tenant_session, require_role
from api.auth.models import CurrentUser
from api.db.models.inventory import Item
from api.db.models.ml import Prediction
from api.forecast.model import FORECAST_VERSION, PERIOD_DAYS
from api.forecast.service import DEFAULT_HORIZON, HISTORY_PERIODS, item_demand_history

router = APIRouter(tags=["forecast"], prefix="/forecast")

READ_ROLES = ("admin", "planner", "manager", "finance")
METHODS = ("croston", "tsb", "naive", "empty")


class ForecastItemRow(BaseModel):
    id: uuid.UUID
    item_number: str
    description: str | None = None
    method: str
    rate: float  # P50 demand per period (the point forecast)
    p50: float
    p80: float
    p95: float
    cv: float
    demand_events: int
    model_version: str


class ForecastItemsPage(BaseModel):
    items: list[ForecastItemRow]
    total: int
    page: int
    page_size: int


class ForecastSummary(BaseModel):
    forecasted: int
    total_items: int
    coverage_pct: float
    obsolescence_trending: int  # TSB with decaying demand
    avg_cv: float
    by_method: dict[str, int]
    model_version: str


class ForecastItemDetail(ForecastItemRow):
    horizon: int  # number of future periods projected
    period_days: int
    history: list[float]  # bucketed issue demand, oldest -> newest
    diagnostics: dict[str, float] = {}
    predicted_at: str | None = None
    input_fingerprint: str | None = None


def _value(prediction: Prediction) -> dict[str, Any]:
    return prediction.value or {}


def _demand_events(value: dict[str, Any]) -> int:
    return int((value.get("diagnostics") or {}).get("demand_events", 0))


def _row(item: Item, prediction: Prediction) -> ForecastItemRow:
    value = _value(prediction)
    return ForecastItemRow(
        id=item.id,
        item_number=item.item_number,
        description=item.description,
        method=str(value.get("method", "empty")),
        rate=float(value.get("rate", 0.0)),
        p50=float(value.get("p50", 0.0)),
        p80=float(value.get("p80", 0.0)),
        p95=float(value.get("p95", 0.0)),
        cv=float(value.get("cv", 0.0)),
        demand_events=_demand_events(value),
        model_version=prediction.model_version,
    )


@router.get("/summary", response_model=ForecastSummary, summary="Forecast KPIs")
def forecast_summary(
    _user: Annotated[CurrentUser, Depends(require_role(*READ_ROLES))],
    session: Annotated[Session, Depends(get_tenant_session)],
) -> ForecastSummary:
    by_method = dict.fromkeys(METHODS, 0)
    cv_sum = 0.0
    cv_count = 0
    obsolescence = 0
    forecasted = 0

    predictions = session.scalars(
        select(Prediction).where(Prediction.model_version == FORECAST_VERSION)
    ).all()
    for prediction in predictions:
        value = _value(prediction)
        method = str(value.get("method", "empty"))
        by_method[method] = by_method.get(method, 0) + 1
        forecasted += 1
        if method != "empty":
            cv_sum += float(value.get("cv", 0.0))
            cv_count += 1
        if method == "tsb":
            obsolescence += 1

    total_items = session.scalar(select(func.count()).select_from(Item)) or 0
    coverage = round(forecasted / total_items * 100, 1) if total_items else 0.0
    avg_cv = round(cv_sum / cv_count, 4) if cv_count else 0.0

    return ForecastSummary(
        forecasted=forecasted,
        total_items=total_items,
        coverage_pct=coverage,
        obsolescence_trending=obsolescence,
        avg_cv=avg_cv,
        by_method=by_method,
        model_version=FORECAST_VERSION,
    )


@router.get("/items", response_model=ForecastItemsPage, summary="Per-item forecasts")
def list_forecast_items(
    _user: Annotated[CurrentUser, Depends(require_role(*READ_ROLES))],
    session: Annotated[Session, Depends(get_tenant_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
    method: str | None = None,
) -> ForecastItemsPage:
    conditions: list[Any] = [Prediction.model_version == FORECAST_VERSION]
    if method:
        conditions.append(Prediction.value["method"].astext == method)

    stmt = (
        select(Item, Prediction)
        .join(Prediction, Prediction.target_id == Item.id)
        .where(*conditions)
    )
    total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = session.execute(
        stmt.order_by(Prediction.value["rate"].as_float().desc(), Item.item_number)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return ForecastItemsPage(
        items=[_row(item, prediction) for item, prediction in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/items/{item_id}", response_model=ForecastItemDetail, summary="Forecast detail")
def forecast_item_detail(
    item_id: uuid.UUID,
    _user: Annotated[CurrentUser, Depends(require_role(*READ_ROLES))],
    session: Annotated[Session, Depends(get_tenant_session)],
) -> ForecastItemDetail:
    result = session.execute(
        select(Item, Prediction)
        .join(Prediction, Prediction.target_id == Item.id)
        .where(Item.id == item_id, Prediction.model_version == FORECAST_VERSION)
    ).first()
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No forecast for this item — run `make forecast`.",
        )

    item, prediction = result
    value = _value(prediction)
    row = _row(item, prediction)
    history = item_demand_history(session, item.id, datetime.now(UTC))

    return ForecastItemDetail(
        **row.model_dump(),
        horizon=DEFAULT_HORIZON,
        period_days=PERIOD_DAYS,
        history=history,
        diagnostics={k: float(v) for k, v in (value.get("diagnostics") or {}).items()},
        predicted_at=prediction.predicted_at.isoformat() if prediction.predicted_at else None,
        input_fingerprint=prediction.input_fingerprint,
    )


# Re-exported for tests / callers that assert the history length.
__all__ = ["router", "HISTORY_PERIODS"]
