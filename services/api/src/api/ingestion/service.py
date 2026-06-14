"""Ingestion orchestration with per-record failure isolation (CV2.E1).

Runs a connector entity-by-entity in dependency order. Each record upserts
inside a SAVEPOINT, so one bad row is logged to ``sources.error_log`` and the
rest of the batch still commits (failure isolation — E1.S9). Every entity gets
a ``sources.sync_runs`` row with read/upserted/failed counts.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from api.db.models.sources import ErrorLog, SyncRun
from api.ingestion.connector import ENTITY_ORDER, SourceConnector
from api.ingestion.upserts import HANDLERS, IngestContext

IngestionSummary = dict[str, dict[str, int]]


@dataclass
class _Counts:
    read: int = 0
    upserted: int = 0
    failed: int = 0


class IngestionService:
    """Pulls from a connector and upserts into the canonical tables."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def run(
        self,
        connector: SourceConnector,
        *,
        tenant_id: uuid.UUID,
        connector_id: uuid.UUID,
    ) -> IngestionSummary:
        ctx = IngestContext(tenant_id=tenant_id, source_system=connector.source_system)
        summary: IngestionSummary = {}

        for entity in ENTITY_ORDER:
            run = SyncRun(
                tenant_id=tenant_id,
                connector_id=connector_id,
                object_type=str(entity),
                status="running",
            )
            self._session.add(run)
            self._session.flush()

            counts = _Counts()
            handler = HANDLERS[entity]
            for batch in connector.fetch(entity):
                for record in batch:
                    counts.read += 1
                    try:
                        with self._session.begin_nested():
                            handler(self._session, ctx, record)
                        counts.upserted += 1
                    except Exception as exc:  # noqa: BLE001 — isolate, log, continue
                        counts.failed += 1
                        with self._session.begin_nested():
                            self._session.add(
                                ErrorLog(
                                    tenant_id=tenant_id,
                                    sync_run_id=run.id,
                                    object_type=str(entity),
                                    source_id=record.source_id,
                                    error_code=type(exc).__name__,
                                    message=str(exc)[:500],
                                )
                            )

            run.status = "success" if counts.failed == 0 else "partial"
            run.records_read = counts.read
            run.records_upserted = counts.upserted
            run.records_failed = counts.failed
            run.finished_at = datetime.now(UTC)
            self._session.flush()
            summary[str(entity)] = {
                "read": counts.read,
                "upserted": counts.upserted,
                "failed": counts.failed,
            }

        return summary
