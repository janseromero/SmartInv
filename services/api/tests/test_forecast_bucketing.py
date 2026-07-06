"""Unit tests for the pure demand-bucketing helper (CV3.E1)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from api.forecast.model import PERIOD_DAYS
from api.forecast.service import bucket_series

NOW = datetime(2026, 6, 1, tzinfo=UTC)


def _days_ago(days: int) -> datetime:
    return NOW - timedelta(days=days)


def test_empty_events_zero_filled_series() -> None:
    series = bucket_series([], NOW, periods=6)
    assert series == [0.0] * 6


def test_current_period_lands_in_last_bucket() -> None:
    series = bucket_series([(4.0, _days_ago(1))], NOW, periods=6)
    assert series[-1] == 4.0
    assert sum(series[:-1]) == 0.0


def test_older_demand_lands_further_left() -> None:
    # ~3 periods back (oldest -> newest ordering).
    series = bucket_series([(7.0, _days_ago(PERIOD_DAYS * 3 + 2))], NOW, periods=6)
    assert series[6 - 1 - 3] == 7.0


def test_events_in_same_bucket_accumulate() -> None:
    series = bucket_series([(2.0, _days_ago(2)), (3.0, _days_ago(3))], NOW, periods=6)
    assert series[-1] == 5.0


def test_events_beyond_window_are_dropped() -> None:
    series = bucket_series([(9.0, _days_ago(PERIOD_DAYS * 50))], NOW, periods=6)
    assert series == [0.0] * 6
