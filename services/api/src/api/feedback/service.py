"""Override capture, regime-change detection, acceptance rate (CV3.E5).

Records a planner's verdict on a recommendation envelope, transitions the
envelope status, and \u2014 for repeated overrides on the same item axis \u2014 raises a
regime-change signal (the world may have shifted; the model is a refresh
candidate). This is the data engine behind continuous quality, not an
autonomous learning loop.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from api.db.models.ml import Recommendation, RecommendationFeedback, RegimeSignal

# Repeated overrides at/above this count on one axis = a regime-change signal.
REGIME_THRESHOLD = 2

REASON_CODES = frozenset(
    {"asset_retirement", "strategy_shift", "supply_change", "demand_change", "other"}
)
_STATUS_BY_DECISION = {"accept": "accepted", "adjust": "adjusted", "override": "overridden"}


def record_feedback(
    session: Session,
    tenant_id: uuid.UUID,
    recommendation: Recommendation,
    *,
    decision: str,
    reason_code: str | None = None,
    reason_note: str | None = None,
    adjusted_payload: dict[str, Any] | None = None,
) -> RecommendationFeedback:
    """Persist the verdict, transition the envelope, and update regime signals."""
    feedback = RecommendationFeedback(
        tenant_id=tenant_id,
        recommendation_id=recommendation.id,
        decision=decision,
        reason_code=reason_code,
        reason_note=reason_note,
        adjusted_payload=adjusted_payload,
        model_version=recommendation.model_version,
    )
    session.add(feedback)
    recommendation.status = _STATUS_BY_DECISION.get(decision, recommendation.status)

    # Overrides/adjusts on the same (item, reason) axis accumulate into a signal.
    if decision in ("override", "adjust") and reason_code:
        _bump_regime_signal(session, tenant_id, recommendation.target_id, reason_code, reason_note)

    return feedback


def _bump_regime_signal(
    session: Session,
    tenant_id: uuid.UUID,
    item_id: uuid.UUID,
    dimension: str,
    note: str | None,
) -> None:
    stmt = (
        pg_insert(RegimeSignal)
        .values(
            tenant_id=tenant_id,
            item_id=item_id,
            dimension=dimension,
            override_count=1,
            last_reason_note=note,
            status="open",
        )
        .on_conflict_do_update(
            constraint="uq_regime_signals_axis",
            set_={
                "override_count": RegimeSignal.override_count + 1,
                "last_reason_note": note,
                "updated_at": func.now(),
            },
        )
    )
    session.execute(stmt)


def acceptance_rate(session: Session) -> list[dict[str, Any]]:
    """Accept / adjust / override breakdown per model version."""
    rows = session.execute(
        select(
            RecommendationFeedback.model_version,
            RecommendationFeedback.decision,
            func.count().label("n"),
        ).group_by(RecommendationFeedback.model_version, RecommendationFeedback.decision)
    ).all()

    by_model: dict[str, dict[str, int]] = {}
    for row in rows:
        version = row.model_version or "unknown"
        by_model.setdefault(version, {"accept": 0, "adjust": 0, "override": 0})
        by_model[version][row.decision] = row.n

    result: list[dict[str, Any]] = []
    for version, counts in sorted(by_model.items()):
        total = sum(counts.values())
        result.append(
            {
                "model_version": version,
                "total": total,
                "accepted": counts["accept"],
                "adjusted": counts["adjust"],
                "overridden": counts["override"],
                "acceptance_rate": round(counts["accept"] / total, 4) if total else 0.0,
            }
        )
    return result
