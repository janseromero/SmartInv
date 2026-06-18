"""Unit tests for the deterministic demand-forecasting engine (CV3.E1)."""

from __future__ import annotations

from collections.abc import Sequence

from api.forecast.engine import croston, forecast_demand, tsb
from api.forecast.model import FORECAST_VERSION, ForecastInput, ForecastResult, Method


def _fc(periods: Sequence[float], horizon: int = 12) -> ForecastResult:
    return forecast_demand(ForecastInput(periods=list(periods), horizon=horizon))


def test_empty_history_yields_empty_method() -> None:
    result = _fc([0.0] * 12)
    assert result.method is Method.EMPTY
    assert result.rate == 0.0
    assert result.p95 == 0.0


def test_croston_on_intermittent_dense_series() -> None:
    # Demand every other period — intermittent, no long trailing gap.
    result = _fc([10, 0, 12, 0, 11, 0, 9, 0, 10, 0, 13, 0])
    assert result.method is Method.CROSTON
    assert result.rate > 0
    assert result.version == FORECAST_VERSION


def test_tsb_when_trailing_zeros_signal_obsolescence() -> None:
    result = _fc([8, 0, 9, 7, 10, 0, 8, 0, 0, 0, 0, 0])
    assert result.method is Method.TSB
    # TSB decays toward zero with the long zero tail.
    assert result.rate < 8


def test_naive_when_too_few_events() -> None:
    result = _fc([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 7])
    assert result.method is Method.NAIVE


def test_quantile_bands_are_ordered() -> None:
    result = _fc([10, 2, 14, 3, 11, 1, 9, 4, 10, 2, 13, 5])
    assert result.p50 <= result.p80 <= result.p95


def test_forecast_is_deterministic() -> None:
    series = [10, 0, 12, 0, 11, 0, 9, 0, 10, 0, 13, 0]
    assert _fc(series) == _fc(series)


def test_croston_rate_is_size_over_interval() -> None:
    # Constant size 10, interval 2 -> rate ~ 5 per period.
    rate = croston([10, 0, 10, 0, 10, 0, 10, 0])
    assert 4.0 < rate < 6.0


def test_tsb_higher_probability_raises_rate() -> None:
    dense = tsb([10, 10, 10, 10, 10, 10])
    sparse = tsb([10, 0, 0, 0, 10, 0])
    assert dense > sparse
