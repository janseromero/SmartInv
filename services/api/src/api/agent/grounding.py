"""Grounding validator — the trust contract enforced in code, not the prompt.

Every numeric claim in a composed answer must trace back to a value that a tool
actually returned. This module extracts numbers from free text (handling
currency, percent, thousands separators, and compact K/M/B suffixes), then
checks each against the set of tool-output values within a small relative
tolerance. Ungrounded numbers are reported; the orchestrator fails closed on
them ([ADR-014](../../../docs/project/decisions.md), Engineering Principles A4).

Pure and deterministic: no I/O, no model calls — fully unit-testable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# A number optionally prefixed by $ and suffixed by % or a K/M/B multiplier.
# Examples matched: 1,234  ·  $1.2M  ·  45%  ·  0.86  ·  3
_NUMBER_RE = re.compile(
    r"\$?\s*(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s*(%|[KkMmBb])?\b",
)

_MULTIPLIER = {"k": 1_000.0, "m": 1_000_000.0, "b": 1_000_000_000.0}

# Small integers are ordinary prose ("the 3 plants", "top 5") and would make the
# validator hypersensitive, so they are not treated as grounded claims.
_TRIVIAL_MAX = 12.0
# Relative tolerance absorbs rounding/formatting ($1.2M vs 1,200,000).
_REL_TOLERANCE = 0.01


@dataclass(frozen=True)
class GroundingResult:
    """Outcome of grounding an answer against tool-output values."""

    grounded: bool
    claims: list[float]
    ungrounded: list[float]


def extract_numbers(text: str) -> list[float]:
    """Return every numeric value mentioned in ``text`` (normalized to float)."""
    values: list[float] = []
    for raw, suffix in _NUMBER_RE.findall(text):
        value = float(raw.replace(",", ""))
        if suffix == "%":
            # A percentage is grounded against either its 0..100 or 0..1 form;
            # keep the face value — callers pass both forms in allowed values.
            pass
        elif suffix:
            value *= _MULTIPLIER[suffix.lower()]
        values.append(value)
    return values


def _matches(claim: float, allowed: list[float]) -> bool:
    for value in allowed:
        scale = max(abs(claim), abs(value), 1.0)
        if abs(claim - value) <= _REL_TOLERANCE * scale:
            return True
    return False


def check_grounded(answer: str, allowed_values: list[float]) -> GroundingResult:
    """Verify every non-trivial number in ``answer`` matches a tool output.

    ``allowed_values`` should include each tool value in the forms the model
    might restate it (e.g. a ratio 0.9 and its percentage 90).
    """
    claims = extract_numbers(answer)
    ungrounded = [
        claim
        for claim in claims
        if abs(claim) > _TRIVIAL_MAX and not _matches(claim, allowed_values)
    ]
    return GroundingResult(grounded=not ungrounded, claims=claims, ungrounded=ungrounded)


def expand_allowed(values: list[float]) -> list[float]:
    """Expand tool values with the alternate forms a model may restate.

    A ratio (0.9) may be restated as a percentage (90) and vice-versa, so both
    forms are accepted to avoid false ungrounded flags on percentages.
    """
    expanded = list(values)
    for value in values:
        if 0.0 < abs(value) <= 1.0:
            expanded.append(value * 100.0)
        if abs(value) > 1.0:
            expanded.append(value / 100.0)
    return expanded
