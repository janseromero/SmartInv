"""Integration tests for the risk dashboard + mitigation endpoints (CV4.E3/E4)."""

from __future__ import annotations

import uuid
from collections.abc import Iterator

import psycopg
import pytest
from api.auth.tokens import mint_dev_token
from api.config import get_settings
from api.db.models.ml import Recommendation
from api.db.session import tenant_session
from api.forecast.service import run_forecast
from api.ingestion.fixture_sync import ensure_fixture_connector
from api.ingestion.fixtures import FixtureConnector
from api.ingestion.service import IngestionService
from api.main import app
from api.optimize.service import run_optimization
from api.risk.service import run_risk_scan
from fastapi.testclient import TestClient
from sqlalchemy import select

ADMIN = get_settings().effective_admin_database_url
SLUG = "cv4_views"
ITEMS = 150


def _reachable() -> bool:
    try:
        with psycopg.connect(ADMIN, connect_timeout=3):
            return True
    except psycopg.OperationalError:
        return False


pytestmark = pytest.mark.skipif(not _reachable(), reason="database not reachable")


@pytest.fixture
def seeded_tenant() -> Iterator[uuid.UUID]:
    with psycopg.connect(ADMIN) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("DELETE FROM core.tenants WHERE slug = %s", (SLUG,))
            cur.execute(
                "INSERT INTO core.tenants(slug, name, status) "
                "VALUES (%s, 'CV4Views', 'active') RETURNING id",
                (SLUG,),
            )
            tid = cur.fetchone()[0]  # type: ignore[index]
    with tenant_session(str(tid)) as session:
        connector = ensure_fixture_connector(session, tid)
        IngestionService(session).run(
            FixtureConnector(item_count=ITEMS, seed=17), tenant_id=tid, connector_id=connector.id
        )
    with tenant_session(str(tid)) as session:
        run_forecast(session, tid)
        run_optimization(session, tid)
        run_risk_scan(session, tid)
    try:
        yield tid
    finally:
        with psycopg.connect(ADMIN) as admin:
            admin.autocommit = True
            with admin.cursor() as cur:
                cur.execute("DELETE FROM core.tenants WHERE slug = %s", (SLUG,))


def _client(tid: uuid.UUID, roles: list[str]) -> TestClient:
    token = mint_dev_token(sub="dev", tenant_id=tid, roles=roles)
    client = TestClient(app)
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


def test_summary_and_heatmap(seeded_tenant: uuid.UUID) -> None:
    client = _client(seeded_tenant, ["manager"])

    summary = client.get("/risk/summary").json()
    assert summary["critical_spares"] >= 1
    assert 0 <= summary["critical_spare_coverage"] <= 100
    assert sum(summary["risk_distribution"].values()) >= 1

    heatmap = client.get("/risk/heatmap").json()
    assert len(heatmap) >= 1
    assert {"location_code", "scores"} <= set(heatmap[0])
    # Plant x risk-dimension scores, each 0..100.
    assert {"stockout", "lead_time", "supplier", "criticality"} <= set(heatmap[0]["scores"])
    assert all(0 <= v <= 100 for v in heatmap[0]["scores"].values())

    exposure = client.get("/risk/exposure").json()
    assert len(exposure) >= 1
    assert {"location_code", "risk_class", "count", "exposure"} <= set(exposure[0])


def test_items_ranked_by_risk(seeded_tenant: uuid.UUID) -> None:
    client = _client(seeded_tenant, ["planner"])
    page = client.get("/risk/items").json()
    assert page["total"] >= 1
    scores = [r["risk_score"] for r in page["items"]]
    assert scores == sorted(scores, reverse=True)  # ranked, highest risk first


def test_detail_has_grounded_narrative(seeded_tenant: uuid.UUID) -> None:
    client = _client(seeded_tenant, ["planner"])
    item_id = client.get("/risk/items?critical_only=true").json()["items"][0]["id"]
    detail = client.get(f"/risk/items/{item_id}").json()
    assert detail["narrative"]
    assert "risk" in detail["narrative"].lower()
    assert "breakdown" in detail


def test_mitigate_stages_envelope_to_approval(seeded_tenant: uuid.UUID) -> None:
    client = _client(seeded_tenant, ["manager"])
    item_id = client.get("/risk/items").json()["items"][0]["id"]
    result = client.post(f"/risk/items/{item_id}/mitigate").json()
    assert result["status"] == "proposed"

    with tenant_session(str(seeded_tenant)) as session:
        rec = session.scalar(select(Recommendation).where(Recommendation.type == "risk_mitigation"))
        assert rec is not None
        assert rec.approval_path == "cv6_workflow"
        assert rec.evidence["risk_score"] is not None


def test_mitigate_requires_act_role(seeded_tenant: uuid.UUID) -> None:
    client = _client(seeded_tenant, ["finance"])  # read-only
    item_id = client.get("/risk/items").json()["items"][0]["id"]
    resp = client.post(f"/risk/items/{item_id}/mitigate")
    assert resp.status_code == 403


def test_summary_requires_auth() -> None:
    assert TestClient(app).get("/risk/summary").status_code == 401
