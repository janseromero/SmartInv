"""The pure demand-forecasting functions (CV3.E1.S1/S3).

Deterministic: no I/O, no randomness, no clock. Croston's method and TSB are
the classic explainable intermittent-demand baselines; quantile bands come from
the historical coefficient of variation. Fully unit-tested.
"""

from __future__ import annotations

from collections.abc import Sequence

from api.forecast.model import (
    ALPHA,
    BETA,
    FORECAST_VERSION,
    MAX_CV,
    MIN_DEMAND_EVENTS,
    Z80,
    Z95,
    ForecastInput,
    ForecastResult,
    Method,
)


def _mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _std(xs: Sequence[float], mean: float) -> float:
    if len(xs) < 2:
        return 0.0
    return float((sum((x - mean) ** 2 for x in xs) / len(xs)) ** 0.5)


def croston(series: Sequence[float], alpha: float = ALPHA) -> float:
    """Croston's method: smooth demand size and inter-arrival interval."""
    sizes = [x for x in series if x > 0]
    if not sizes:
        return 0.0
    # Inter-arrival intervals between non-zero demands.
    intervals: list[float] = []
    gap = 1
    seen = False
    for x in series:
        if x > 0:
            if seen:
                intervals.append(gap)
            seen = True
            gap = 1
        else:
            gap += 1
    z = sizes[0]  # smoothed demand size
    p = intervals[0] if intervals else 1.0  # smoothed interval
    for size in sizes[1:]:
        z = z + alpha * (size - z)
    for interval in intervals[1:]:
        p = p + alpha * (interval - p)
    return z / p if p > 0 else z


def tsb(series: Sequence[float], alpha: float = ALPHA, beta: float = BETA) -> float:
    """Teunter-Syntetos-Babai: smooth demand size and demand *probability*.

    Better than Croston for items going obsolete — trailing zeros decay the
    forecast toward zero instead of holding it flat.
    """
    sizes = [x for x in series if x > 0]
    if not sizes:
        return 0.0
    prob = 1.0 if series[0] > 0 else 0.0
    level = sizes[0]
    for x in series:
        if x > 0:
            level = level + alpha * (x - level)
            prob = prob + beta * (1.0 - prob)
        else:
            prob = prob + beta * (0.0 - prob)
    return level * prob


def _coefficient_of_variation(series: Sequence[float]) -> float:
    sizes = [x for x in series if x > 0]
    mean = _mean(sizes)
    if mean <= 0:
        return 0.0
    return min(MAX_CV, _std(sizes, mean) / mean)


def _is_intermittent(series: Sequence[float]) -> bool:
    nonzero = sum(1 for x in series if x > 0)
    return 0 < nonzero < len(series)


def forecast_demand(inp: ForecastInput) -> ForecastResult:
    """Return a per-period demand forecast with P50/P80/P95 bands."""
    series = inp.periods
    nonzero = [x for x in series if x > 0]

    if not nonzero:
        return ForecastResult(
            rate=0.0, p50=0.0, p80=0.0, p95=0.0, cv=0.0, method=Method.EMPTY, horizon=inp.horizon
        )

    # TSB when the series has gaps (intermittent / obsolescence-prone);
    # Croston when it is intermittent but dense; naive mean otherwise.
    if len(nonzero) < MIN_DEMAND_EVENTS:
        rate = _mean(series)
        method = Method.NAIVE
    elif _is_intermittent(series):
        # Trailing zeros => obsolescence risk => prefer TSB.
        trailing_zeros = 0
        for x in reversed(series):
            if x > 0:
                break
            trailing_zeros += 1
        if trailing_zeros >= 2:
            rate = tsb(series)
            method = Method.TSB
        else:
            rate = croston(series)
            method = Method.CROSTON
    else:
        rate = _mean(series)
        method = Method.NAIVE

    cv = _coefficient_of_variation(series)
    p80 = rate * (1.0 + Z80 * cv)
    p95 = rate * (1.0 + Z95 * cv)
    return ForecastResult(
        rate=round(rate, 4),
        p50=round(rate, 4),
        p80=round(p80, 4),
        p95=round(p95, 4),
        cv=round(cv, 4),
        method=method,
        horizon=inp.horizon,
        version=FORECAST_VERSION,
        diagnostics={
            "periods": float(len(series)),
            "demand_events": float(len(nonzero)),
            "mean_size": round(_mean(nonzero), 4),
        },
    )
