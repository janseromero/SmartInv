"""Forecasting value objects, constants, and quantile config (CV3.E1).

Deterministic Croston / TSB baseline (``forecast-croston-v1``). Same inputs +
same version always produce the same forecast. Design in [ADR-028].
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

FORECAST_VERSION = "forecast-croston-v1"

# Demand is bucketed into fixed periods (≈ monthly) before forecasting.
PERIOD_DAYS = 30
# Minimum non-zero demand events before a model is trustworthy.
MIN_DEMAND_EVENTS = 3
# Smoothing constants for Croston / TSB.
ALPHA = 0.1  # demand-size / level smoothing
BETA = 0.1  # demand-probability smoothing (TSB)

# Standard-normal quantile multipliers for the P80 / P95 bands.
Z80 = 0.8416
Z95 = 1.6449
# Coefficient-of-variation clamp so a tiny sample can't explode the bands.
MAX_CV = 1.5


class Method(StrEnum):
    CROSTON = "croston"
    TSB = "tsb"
    NAIVE = "naive"  # not enough signal — fall back to the mean
    EMPTY = "empty"  # no demand history at all


@dataclass(frozen=True)
class ForecastInput:
    """Per-item demand history: one bucket per period, chronological."""

    periods: list[float]  # demand quantity per period (zeros included)
    horizon: int = 12  # number of future periods the caller asks about


@dataclass(frozen=True)
class ForecastResult:
    """A per-period demand forecast with probabilistic bands."""

    rate: float  # P50 demand per period (the point forecast)
    p50: float
    p80: float
    p95: float
    cv: float  # coefficient of variation used for the bands
    method: Method
    horizon: int
    version: str = FORECAST_VERSION
    diagnostics: dict[str, float] = field(default_factory=dict)
