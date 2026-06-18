"""Integration tests for the recommendation envelope endpoints (CV3.E3/E4/E5)."""

from __future__ import annotations

import uuid
from collections.abc import Iterator

import psycopg
import pytest
from api.auth.tokens import mint_dev_token
from api.config import get_settings
from api.db.session import tenant_session
from api.forecast.service import run_forecast
from api.ingestion.fixture_sync import ensure_fixture_connector
from api.ingestion.fixtures import FixtureConnector
from api.ingestion.service import IngestionService
from api.main import app
from api.optimize.service import run_optimization
from fastapi.testclient import TestClient

ADMIN = get_settings().effective_admin_database_url
SLUG = "cv3_views"
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
                "VALUES (%s, 'CV3Views', 'active') RETURNING id",
                (SLUG,),
            )
            tid = cur.fetchone()[0]  # type: ignore[index]
    with tenant_session(str(tid)) as session:
        connector = ensure_fixture_connector(session, tid)
        IngestionService(session).run(
            FixtureConnector(item_count=ITEMS, seed=11), tenant_id=tid, connector_id=connector.id
        )
    with tenant_session(str(tid)) as session:
        run_forecast(session, tid)
        run_optimization(session, tid)
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


def test_summary_and_list_with_envelope(seeded_tenant: uuid.UUID) -> None:
    client = _client(seeded_tenant, ["planner"])

    summary = client.get("/recommendations/summary").json()
    assert summary["proposed"] >= 1
    assert "by_action" in summary

    page = client.get("/recommendations").json()
    assert page["total"] >= 1
    row = page["recommendations"][0]
    assert row["claim"]
    assert row["confidence"] is not None
    assert row["model_version"]


def test_detail_exposes_full_envelope(seeded_tenant: uuid.UUID) -> None:
    client = _client(seeded_tenant, ["planner"])
    rec_id = client.get("/recommendations").json()["recommendations"][0]["id"]
    detail = client.get(f"/recommendations/{rec_id}").json()
    assert {"min_level", "max_level", "reorder_point"} <= set(detail["payload"])
    assert "pareto" in detail["evidence"]
    assert detail["assumptions"]["optimizer_version"]
    assert detail["approval_path"] == "cv6_workflow"


def test_accept_routes_and_records_feedback(seeded_tenant: uuid.UUID) -> None:
    client = _client(seeded_tenant, ["planner"])
    rec_id = client.get("/recommendations").json()["recommendations"][0]["id"]
    result = client.post(f"/recommendations/{rec_id}/accept").json()
    assert result["status"] == "accepted"

    # A second action on an actioned recommendation is rejected.
    conflict = client.post(f"/recommendations/{rec_id}/accept")
    assert conflict.status_code == 409

    rates = client.get("/recommendations/acceptance-rate").json()
    assert any(r["accepted"] >= 1 for r in rates)


def test_override_requires_valid_reason_and_creates_signal(seeded_tenant: uuid.UUID) -> None:
    client = _client(seeded_tenant, ["planner"])
    rec_id = client.get("/recommendations").json()["recommendations"][1]["id"]

    bad = client.post(f"/recommendations/{rec_id}/override", json={"reason_code": "nonsense"})
    assert bad.status_code == 400

    ok = client.post(
        f"/recommendations/{rec_id}/override",
        json={"reason_code": "supply_change", "reason_note": "vendor lead time doubled"},
    ).json()
    assert ok["status"] == "overridden"

    signals = client.get("/recommendations/regime-signals").json()
    assert any(s["dimension"] == "supply_change" for s in signals)


def test_override_requires_act_role(seeded_tenant: uuid.UUID) -> None:
    client = _client(seeded_tenant, ["finance"])  # read-only
    rec_id = client.get("/recommendations").json()["recommendations"][0]["id"]
    resp = client.post(f"/recommendations/{rec_id}/override", json={"reason_code": "other"})
    assert resp.status_code == 403


def test_list_requires_auth() -> None:
    assert TestClient(app).get("/recommendations").status_code == 401
