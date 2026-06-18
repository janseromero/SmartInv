"""Unit tests for the deterministic anomaly-detection engine (CV2.E5)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from api.anomaly.engine import (
    detect_consumption_spikes,
    detect_negative_balance,
    detect_price_jumps,
)
from api.anomaly.model import ANOMALY_VERSION, AnomalyType, BalanceState, IssueEvent, Severity

_NOW = datetime(2026, 6, 18, tzinfo=UTC)


def _event(qty: float, cost: float | None = None) -> IssueEvent:
    return IssueEvent(
        txn_id=uuid.uuid4(), source_id="TXN", quantity=qty, unit_cost=cost, txn_date=_NOW
    )


def test_consumption_spike_flagged_above_baseline() -> None:
    events = [_event(q) for q in (10, 11, 9, 10, 12, 9, 11)] + [_event(300)]
    results = detect_consumption_spikes(events)
    assert len(results) == 1
    assert results[0].type is AnomalyType.CONSUMPTION_SPIKE
    assert results[0].severity is Severity.CRIT
    assert results[0].version == ANOMALY_VERSION
    assert "x the item's median" in results[0].evidence["cause"]


def test_no_spike_within_normal_variation() -> None:
    events = [_event(q) for q in (10, 11, 9, 10, 12, 9, 11, 13, 8)]
    assert detect_consumption_spikes(events) == []


def test_tight_series_does_not_flag_small_deviation() -> None:
    # A 1.5x usage is ~statistically extreme on a very tight series, but below
    # the practical-significance floor (3x) — it must not flag.
    events = [_event(q) for q in (10, 10, 10, 10, 10, 10, 15)]
    assert detect_consumption_spikes(events) == []


def test_small_price_wiggle_does_not_flag() -> None:
    # ~7% deviation: statistically extreme on a quiet series, but inside the
    # [0.5x, 2x] practical band — must not flag.
    events = [_event(1, cost=c) for c in (100, 100, 100, 100, 100, 100, 107)]
    assert detect_price_jumps(events) == []


def test_consumption_needs_minimum_history() -> None:
    events = [_event(q) for q in (5, 5, 500)]  # only 3 points
    assert detect_consumption_spikes(events) == []


def test_price_jump_flagged_both_directions() -> None:
    events = [_event(1, cost=c) for c in (100, 102, 98, 101, 99, 100)] + [_event(1, cost=500)]
    results = detect_price_jumps(events)
    assert len(results) == 1
    assert results[0].type is AnomalyType.PRICE_JUMP
    assert "above" in results[0].evidence["cause"]


def test_price_ignores_events_without_cost() -> None:
    events = [_event(1, cost=None) for _ in range(8)]
    assert detect_price_jumps(events) == []


def test_negative_available_balance_is_crit() -> None:
    result = detect_negative_balance(
        BalanceState(balance_id=uuid.uuid4(), on_hand=5, available=-3, reserved=8)
    )
    assert result is not None
    assert result.type is AnomalyType.NEGATIVE_BALANCE
    assert result.severity is Severity.CRIT
    assert result.score == 3.0


def test_over_reservation_without_negative_available_is_warn() -> None:
    result = detect_negative_balance(
        BalanceState(balance_id=uuid.uuid4(), on_hand=5, available=0, reserved=8)
    )
    assert result is not None
    assert result.severity is Severity.WARN


def test_healthy_balance_is_not_flagged() -> None:
    assert (
        detect_negative_balance(
            BalanceState(balance_id=uuid.uuid4(), on_hand=10, available=10, reserved=0)
        )
        is None
    )


def test_detection_is_deterministic() -> None:
    events = [_event(q) for q in (10, 11, 9, 10, 12, 9, 11)] + [_event(300)]
    a = detect_consumption_spikes(events)
    b = detect_consumption_spikes(events)
    assert [r.score for r in a] == [r.score for r in b]
