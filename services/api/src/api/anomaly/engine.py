"""The pure anomaly-detection functions (CV2.E5.S1/S2/S3).

Deterministic: no I/O, no randomness, no clock. Robust z-scores use the median
and the (scaled) median absolute deviation, which resist the very outliers we
are trying to find. Fully unit-tested; this is the model-deterministic core.
"""

from __future__ import annotations

from collections.abc import Sequence

from api.anomaly.model import (
    CRIT_Z,
    MAD_SCALE,
    MIN_HISTORY,
    MIN_SPIKE_RATIO,
    PRICE_RATIO_HI,
    PRICE_RATIO_LO,
    Z_THRESHOLD,
    AnomalyResult,
    AnomalyType,
    BalanceState,
    IssueEvent,
    Severity,
)


def _median(values: Sequence[float]) -> float:
    ordered = sorted(values)
    n = len(ordered)
    mid = n // 2
    if n % 2 == 1:
        return float(ordered[mid])
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def _std(values: Sequence[float], mean: float) -> float:
    if len(values) < 2:
        return 0.0
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return float(variance**0.5)


def _dispersion(values: Sequence[float], median: float) -> float:
    """Scaled MAD, falling back to std dev when the MAD collapses to zero."""
    mad = _median([abs(v - median) for v in values])
    scaled = MAD_SCALE * mad
    if scaled > 0:
        return scaled
    return _std(values, sum(values) / len(values))


def _severity(z: float) -> Severity:
    return Severity.CRIT if abs(z) >= CRIT_Z else Severity.WARN


def detect_consumption_spikes(events: Sequence[IssueEvent]) -> list[AnomalyResult]:
    """Flag issue quantities far above the item's robust baseline (S1)."""
    if len(events) < MIN_HISTORY:
        return []
    quantities = [e.quantity for e in events]
    median = _median(quantities)
    dispersion = _dispersion(quantities, median)
    if dispersion <= 0:
        return []

    results: list[AnomalyResult] = []
    for event in events:
        z = (event.quantity - median) / dispersion
        ratio = event.quantity / median if median > 0 else event.quantity
        # Statistically unusual AND materially large (practical-significance floor).
        if z < Z_THRESHOLD or ratio < MIN_SPIKE_RATIO:  # only upward spikes
            continue
        results.append(
            AnomalyResult(
                type=AnomalyType.CONSUMPTION_SPIKE,
                target_type="transaction",
                target_id=event.txn_id,
                source_record_id=event.source_id,
                score=round(z, 4),
                severity=_severity(z),
                detected_for=event.txn_date,
                evidence={
                    "observed": event.quantity,
                    "baseline_median": median,
                    "z": round(z, 4),
                    "cause": f"Consumption {ratio:.1f}x the item's median usage.",
                },
            )
        )
    return results


def detect_price_jumps(events: Sequence[IssueEvent]) -> list[AnomalyResult]:
    """Flag unit prices that deviate sharply from the item's price history (S2)."""
    priced = [e for e in events if e.unit_cost is not None]
    if len(priced) < MIN_HISTORY:
        return []
    prices = [e.unit_cost for e in priced if e.unit_cost is not None]
    median = _median(prices)
    dispersion = _dispersion(prices, median)
    if dispersion <= 0:
        return []

    results: list[AnomalyResult] = []
    for event in priced:
        price = event.unit_cost
        if price is None:
            continue
        z = (price - median) / dispersion
        ratio = price / median if median > 0 else price
        material = ratio >= PRICE_RATIO_HI or ratio <= PRICE_RATIO_LO
        if abs(z) < Z_THRESHOLD or not material:  # unusual AND materially large
            continue
        direction = "above" if z > 0 else "below"
        results.append(
            AnomalyResult(
                type=AnomalyType.PRICE_JUMP,
                target_type="transaction",
                target_id=event.txn_id,
                source_record_id=event.source_id,
                score=round(z, 4),
                severity=_severity(z),
                detected_for=event.txn_date,
                evidence={
                    "observed": price,
                    "baseline_median": median,
                    "z": round(z, 4),
                    "cause": f"Unit price {ratio:.1f}x the median ({direction} contract baseline).",
                },
            )
        )
    return results


def detect_negative_balance(balance: BalanceState) -> AnomalyResult | None:
    """Flag reservation-integrity breaks: negative available or over-reservation (S3)."""
    over_reserved = balance.reserved - balance.on_hand
    if balance.available >= 0 and over_reserved <= 0:
        return None

    magnitude = max(-balance.available, over_reserved, 0.0)
    return AnomalyResult(
        type=AnomalyType.NEGATIVE_BALANCE,
        target_type="balance",
        target_id=balance.balance_id,
        source_record_id=None,
        score=round(magnitude, 4),
        severity=Severity.CRIT if balance.available < 0 else Severity.WARN,
        detected_for=None,
        evidence={
            "on_hand": balance.on_hand,
            "reserved": balance.reserved,
            "available": balance.available,
            "cause": "Available balance is negative."
            if balance.available < 0
            else "Reserved quantity exceeds on-hand.",
        },
    )
