"""Anomaly-detection orchestration: gather, detect, persist, register (CV2.E5).

Loads issue transactions (grouped per item) and stock balances, runs the pure
detectors, upserts results into ``ml.anomalies``, and registers the model
version in ``ml.model_registry`` for reproducibility. Recompute is on-demand
(CLI / admin endpoint); a nightly Dramatiq schedule \u2014 which would satisfy the
"within 24 hours" SLA \u2014 is deferred (mirrors CV2.E3/E4). Re-runs preserve a
planner's decision (only still-``open`` anomalies are refreshed).
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from api.anomaly.engine import (
    detect_consumption_spikes,
    detect_negative_balance,
    detect_price_jumps,
)
from api.anomaly.model import (
    ANOMALY_VERSION,
    AnomalyResult,
    BalanceState,
    IssueEvent,
)
from api.db.models.inventory import Balance, Transaction
from api.db.models.ml import Anomaly, ModelRegistry

AnomalySummary = dict[str, int]

_PARAMS = {
    "z_threshold": 3.5,
    "min_history": 5,
    "detectors": ["consumption_spike", "price_jump", "negative_balance"],
}


def ensure_anomaly_version(session: Session) -> None:
    """Register the active anomaly version in the model registry (idempotent)."""
    stmt = (
        pg_insert(ModelRegistry)
        .values(
            name="anomaly_detection",
            version=ANOMALY_VERSION,
            task="anomaly",
            framework="deterministic",
            params=_PARAMS,
            metrics={},
            status="active",
        )
        .on_conflict_do_nothing(index_elements=["name", "version"])
    )
    session.execute(stmt)


def _issue_events(session: Session) -> dict[uuid.UUID, list[IssueEvent]]:
    events: dict[uuid.UUID, list[IssueEvent]] = defaultdict(list)
    for row in session.execute(
        select(
            Transaction.id,
            Transaction.item_id,
            Transaction.source_id,
            Transaction.quantity,
            Transaction.unit_cost,
            Transaction.txn_date,
        ).where(Transaction.type == "issue")
    ).all():
        events[row.item_id].append(
            IssueEvent(
                txn_id=row.id,
                source_id=row.source_id,
                quantity=float(row.quantity),
                unit_cost=float(row.unit_cost) if row.unit_cost is not None else None,
                txn_date=row.txn_date,
            )
        )
    return events


def _balances(session: Session) -> list[BalanceState]:
    return [
        BalanceState(
            balance_id=row.id,
            on_hand=float(row.on_hand),
            available=float(row.available),
            reserved=float(row.reserved),
        )
        for row in session.execute(
            select(Balance.id, Balance.on_hand, Balance.available, Balance.reserved)
        ).all()
    ]


def detect_all(session: Session) -> list[AnomalyResult]:
    """Pure-ish: gather facts, run every detector, return the flagged anomalies."""
    results: list[AnomalyResult] = []
    for events in _issue_events(session).values():
        results.extend(detect_consumption_spikes(events))
        results.extend(detect_price_jumps(events))
    for balance in _balances(session):
        flagged = detect_negative_balance(balance)
        if flagged is not None:
            results.append(flagged)
    return results


def run_anomaly_scan(session: Session, tenant_id: uuid.UUID) -> AnomalySummary:
    ensure_anomaly_version(session)
    now = datetime.now(UTC)

    results = detect_all(session)

    summary: AnomalySummary = {"anomalies": len(results)}
    for result in results:
        summary[str(result.type)] = summary.get(str(result.type), 0) + 1
        stmt = (
            pg_insert(Anomaly)
            .values(
                tenant_id=tenant_id,
                type=str(result.type),
                target_type=result.target_type,
                target_id=result.target_id,
                source_record_id=result.source_record_id,
                score=result.score,
                severity=str(result.severity),
                detected_for=result.detected_for,
                evidence=result.evidence,
                model_version=result.version,
                status="open",
                updated_at=now,
            )
            .on_conflict_do_update(
                constraint="uq_anomalies_target",
                set_={
                    "score": result.score,
                    "severity": str(result.severity),
                    "detected_for": result.detected_for,
                    "evidence": result.evidence,
                    "model_version": result.version,
                    "updated_at": now,
                },
                where=Anomaly.status == "open",
            )
        )
        session.execute(stmt)

    return summary
