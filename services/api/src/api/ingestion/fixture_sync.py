"""Convenience wiring to run the fixture connector for a tenant (CV2.E1)."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.db.models.sources import Connector
from api.ingestion.fixtures import FixtureConnector
from api.ingestion.service import IngestionService, IngestionSummary

FIXTURE_SOURCE = "fixture"


def ensure_fixture_connector(session: Session, tenant_id: uuid.UUID) -> Connector:
    """Return the tenant's fixture connector, creating it on first use."""
    connector = session.scalar(
        select(Connector).where(
            Connector.tenant_id == tenant_id,
            Connector.source_system == FIXTURE_SOURCE,
        )
    )
    if connector is None:
        connector = Connector(
            tenant_id=tenant_id,
            source_system=FIXTURE_SOURCE,
            name="Fixture Maximo",
            config={"note": "synthetic data; replaced by the real Maximo connector"},
            status="active",
        )
        session.add(connector)
        session.flush()
    return connector


def run_fixture_sync(session: Session, tenant_id: uuid.UUID) -> IngestionSummary:
    """Ingest the fixture dataset into the tenant's inventory tables."""
    connector = ensure_fixture_connector(session, tenant_id)
    return IngestionService(session).run(
        FixtureConnector(), tenant_id=tenant_id, connector_id=connector.id
    )
