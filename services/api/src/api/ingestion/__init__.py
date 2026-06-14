"""Source ingestion (CV2.E1).

A source-agnostic pipeline that pulls canonical records from a ``SourceConnector``
and upserts them idempotently into ``inventory.*``, tracking each run in
``sources.sync_runs`` with per-record failure isolation.

The MVP ships a ``FixtureConnector`` (deliberately messy synthetic data). The
real ``MaximoConnector`` implements the same seam later (ADR-024).
"""

from api.ingestion.connector import ENTITY_ORDER, Entity, SourceConnector, SourceRecord
from api.ingestion.service import IngestionService, IngestionSummary

__all__ = [
    "ENTITY_ORDER",
    "Entity",
    "IngestionService",
    "IngestionSummary",
    "SourceConnector",
    "SourceRecord",
]
