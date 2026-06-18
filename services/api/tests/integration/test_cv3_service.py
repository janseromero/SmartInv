"""Integration tests for the CV3 forecast/optimize/feedback services."""

from __future__ import annotations

import uuid
from collections.abc import Iterator

import psycopg
import pytest
from api.config import get_settings
from api.db.models.inventory import Item
from api.db.models.ml import ModelRegistry, Prediction, Recommendation, RegimeSignal
from api.db.session import tenant_session
from api.feedback.service import record_feedback
from api.forecast.model import FORECAST_VERSION
from api.forecast.service import run_forecast
from api.ingestion.fixture_sync import ensure_fixture_connector
from api.ingestion.fixtures import FixtureConnector
from api.ingestion.service import IngestionService
from api.optimize.model import OPT_VERSION
from api.optimize.service import run_optimization
from sqlalchemy import func, select

ADMIN = get_settings().effective_admin_database_url
SLUG = "cv3_service"
ITEMS = 150


def _reachable() -> bool:
    try:
        with psycopg.connect(ADMIN, connect_timeout=3):
            return True
    except psycopg.OperationalError:
        return False


pytestmark = pytest.mark.skipif(not _reachable(), reason="database not reachable")


@pytest.fixture
def tenant_id() -> Iterator[uuid.UUID]:
    with psycopg.connect(ADMIN) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("DELETE FROM core.tenants WHERE slug = %s", (SLUG,))
            cur.execute(
                "INSERT INTO core.tenants(slug, name, status) "
                "VALUES (%s, 'CV3', 'active') RETURNING id",
                (SLUG,),
            )
            tid = cur.fetchone()[0]  # type: ignore[index]
    with tenant_session(str(tid)) as session:
        connector = ensure_fixture_connector(session, tid)
        IngestionService(session).run(
            FixtureConnector(item_count=ITEMS, seed=11), tenant_id=tid, connector_id=connector.id
        )
    try:
        yield tid
    finally:
        with psycopg.connect(ADMIN) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute("DELETE FROM core.tenants WHERE slug = %s", (SLUG,))


def test_forecast_persists_predictions_and_registers(tenant_id: uuid.UUID) -> None:
    with tenant_session(str(tenant_id)) as session:
        summary = run_forecast(session, tenant_id)

    assert summary["forecasted"] == ITEMS
    with tenant_session(str(tenant_id)) as session:
        predictions = session.scalar(
            select(func.count())
            .select_from(Prediction)
            .where(Prediction.model_version == FORECAST_VERSION)
        )
        assert predictions == ITEMS
        sample = session.scalars(select(Prediction)).first()
        assert sample is not None
        assert {"rate", "p50", "p80", "p95", "method"} <= set(sample.value)
        assert sample.input_fingerprint
        registered = session.scalar(
            select(func.count())
            .select_from(ModelRegistry)
            .where(ModelRegistry.name == "demand_forecast")
        )
        assert registered == 1


def test_optimization_builds_full_envelopes(tenant_id: uuid.UUID) -> None:
    with tenant_session(str(tenant_id)) as session:
        run_forecast(session, tenant_id)
        summary = run_optimization(session, tenant_id)

    assert summary["recommendations"] >= 1
    with tenant_session(str(tenant_id)) as session:
        rec = session.scalars(
            select(Recommendation).where(Recommendation.type == "reorder_policy")
        ).first()
        assert rec is not None
        # The envelope is complete (non-negotiable #4).
        assert rec.claim
        assert rec.confidence is not None
        assert {"min_level", "max_level", "reorder_point"} <= set(rec.payload)
        assert "pareto" in rec.evidence
        assert rec.assumptions["optimizer_version"] == OPT_VERSION
        assert rec.approval_path == "cv6_workflow"
        assert rec.status == "proposed"


def test_optimization_is_append_only_for_actioned(tenant_id: uuid.UUID) -> None:
    with tenant_session(str(tenant_id)) as session:
        run_forecast(session, tenant_id)
        run_optimization(session, tenant_id)
        rec = session.scalars(
            select(Recommendation).where(Recommendation.type == "reorder_policy")
        ).first()
        assert rec is not None
        rec.status = "accepted"  # human decision

    with tenant_session(str(tenant_id)) as session:
        run_optimization(session, tenant_id)  # re-run
        # The accepted envelope survives; only proposed ones are regenerated.
        accepted = session.scalar(
            select(func.count())
            .select_from(Recommendation)
            .where(Recommendation.status == "accepted")
        )
        assert accepted == 1


def test_repeated_overrides_raise_a_regime_signal(tenant_id: uuid.UUID) -> None:
    with tenant_session(str(tenant_id)) as session:
        item_id = session.scalar(select(Item.id))
        assert item_id is not None
        # Two recommendations for the same item, both overridden on one axis.
        for _ in range(2):
            rec = Recommendation(
                tenant_id=tenant_id,
                type="reorder_policy",
                target_type="item",
                target_id=item_id,
                claim="test",
                payload={},
                model_version=OPT_VERSION,
                status="proposed",
            )
            session.add(rec)
            session.flush()
            record_feedback(
                session,
                tenant_id,
                rec,
                decision="override",
                reason_code="demand_change",
                reason_note="seasonal turnaround",
            )

    with tenant_session(str(tenant_id)) as session:
        signal = session.scalars(select(RegimeSignal)).first()
        assert signal is not None
        assert signal.override_count == 2
        assert signal.dimension == "demand_change"
