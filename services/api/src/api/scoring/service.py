"""Scoring orchestration: gather facts, score, persist, register (CV2.E3).

Aggregates per-item facts across sites, runs the pure engine, writes the score
back onto ``inventory.items``, and registers the score version in
``ml.model_registry`` for reproducibility. Recompute is on-demand (CLI / admin
endpoint); a nightly Dramatiq schedule is deferred.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from api.db.models.inventory import Balance, Item, Transaction
from api.db.models.ml import ModelRegistry
from api.scoring.engine import score_item
from api.scoring.model import SCORE_VERSION, WEIGHTS, ScoreInput

ScoringSummary = dict[str, int]


def ensure_score_version(session: Session) -> None:
    """Register the active score version in the model registry (idempotent)."""
    stmt = (
        pg_insert(ModelRegistry)
        .values(
            name="health_score",
            version=SCORE_VERSION,
            task="scoring",
            framework="deterministic",
            params=WEIGHTS,
            metrics={},
            status="active",
        )
        .on_conflict_do_nothing(index_elements=["name", "version"])
    )
    session.execute(stmt)


def run_scoring(session: Session, tenant_id: uuid.UUID) -> ScoringSummary:
    ensure_score_version(session)
    now = datetime.now(UTC)

    balances = {
        row.item_id: row
        for row in session.execute(
            select(
                Balance.item_id,
                func.sum(Balance.on_hand).label("on_hand"),
                func.sum(Balance.min_level).label("min_level"),
                func.sum(Balance.max_level).label("max_level"),
            ).group_by(Balance.item_id)
        ).all()
    }
    last_movement = {
        row.item_id: row.last
        for row in session.execute(
            select(Transaction.item_id, func.max(Transaction.txn_date).label("last")).group_by(
                Transaction.item_id
            )
        ).all()
    }

    summary: ScoringSummary = {"scored": 0, "disposal_candidates": 0}
    mappings: list[dict[str, object]] = []

    for item in session.execute(
        select(Item.id, Item.unit_cost, Item.description, Item.status)
    ).all():
        bal = balances.get(item.id)
        last = last_movement.get(item.id)
        days = (now - last).days if last is not None else None

        result = score_item(
            ScoreInput(
                on_hand=float(bal.on_hand) if bal and bal.on_hand is not None else 0.0,
                min_level=float(bal.min_level) if bal and bal.min_level is not None else None,
                max_level=float(bal.max_level) if bal and bal.max_level is not None else None,
                unit_cost=float(item.unit_cost) if item.unit_cost is not None else None,
                has_description=item.description is not None,
                days_since_movement=days,
                status=item.status,
            )
        )

        mappings.append(
            {
                "id": item.id,
                "health_score": result.score,
                "health_class": str(result.classification),
                "score_version": result.version,
                "score_dimensions": result.dimensions,
                "scored_at": now,
            }
        )
        summary["scored"] += 1
        summary[str(result.classification)] = summary.get(str(result.classification), 0) + 1
        if result.is_disposal_candidate:
            summary["disposal_candidates"] += 1

    if mappings:
        session.execute(update(Item), mappings)

    return summary
