"""Integration tests for the duplicate-detection queue endpoints (CV2.E4)."""

from __future__ import annotations

import uuid
from collections.abc import Iterator

import psycopg
import pytest
from api.auth.tokens import mint_dev_token
from api.config import get_settings
from api.db.models.inventory import Item
from api.db.models.ml import Recommendation
from api.db.session import tenant_session
from api.dedup.service import run_dedup
from api.main import app
from fastapi.testclient import TestClient
from sqlalchemy import select

ADMIN = get_settings().effective_admin_database_url
SLUG = "e4_views"


def _reachable() -> bool:
    try:
        with psycopg.connect(ADMIN, connect_timeout=3):
            return True
    except psycopg.OperationalError:
        return False


pytestmark = pytest.mark.skipif(not _reachable(), reason="database not reachable")


def _item(session: object, tid: uuid.UUID, number: str, desc: str) -> None:
    session.add(  # type: ignore[attr-defined]
        Item(
            tenant_id=tid,
            source_system="FIXTURE",
            source_id=number,
            item_number=number,
            description=desc,
            uom="EA",
            item_type="SPARE",
            unit_cost=100.0,
        )
    )


@pytest.fixture
def seeded_tenant() -> Iterator[uuid.UUID]:
    with psycopg.connect(ADMIN) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("DELETE FROM core.tenants WHERE slug = %s", (SLUG,))
            cur.execute(
                "INSERT INTO core.tenants(slug, name, status) "
                "VALUES (%s, 'DupViews', 'active') RETURNING id",
                (SLUG,),
            )
            tid = cur.fetchone()[0]  # type: ignore[index]
    with tenant_session(str(tid)) as session:
        _item(session, tid, "B-001", "Ball bearing 6204 2RS sealed")
        _item(session, tid, "B-002", "Bearing ball 6204 2RS sealed")
        _item(session, tid, "G-001", "Safety gloves nitrile large")
    with tenant_session(str(tid)) as session:
        run_dedup(session, tid)
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


def test_summary_and_list(seeded_tenant: uuid.UUID) -> None:
    client = _client(seeded_tenant, ["planner"])

    summary = client.get("/duplicates/summary").json()
    assert summary["open"] >= 1
    assert summary["probable"] >= 1

    page = client.get("/duplicates").json()
    assert page["total"] >= 1
    pair = page["candidates"][0]
    assert pair["confidence"] >= 0.85
    assert pair["item_a"]["item_number"]
    assert pair["item_b"]["item_number"]


def test_detail_exposes_feature_breakdown(seeded_tenant: uuid.UUID) -> None:
    client = _client(seeded_tenant, ["planner"])
    candidate_id = client.get("/duplicates").json()["candidates"][0]["id"]
    detail = client.get(f"/duplicates/{candidate_id}").json()
    assert "description" in detail["features"]
    assert detail["model_version"]


def test_merge_proposes_recommendation_not_mutation(seeded_tenant: uuid.UUID) -> None:
    client = _client(seeded_tenant, ["planner"])
    pair = client.get("/duplicates").json()["candidates"][0]
    keep_id = pair["item_a"]["id"]

    result = client.post(
        f"/duplicates/{pair['id']}/review",
        json={"decision": "merge", "keep_item_id": keep_id},
    ).json()
    assert result["status"] == "merged"
    assert result["recommendation_id"] is not None

    with tenant_session(str(seeded_tenant)) as session:
        rec = session.scalar(select(Recommendation).where(Recommendation.type == "item_merge"))
        assert rec is not None
        assert rec.status == "proposed"
        assert rec.approval_path == "cv6_workflow"

    # A second review on the resolved pair is rejected.
    conflict = client.post(f"/duplicates/{pair['id']}/review", json={"decision": "hold"})
    assert conflict.status_code == 409


def test_review_requires_review_role(seeded_tenant: uuid.UUID) -> None:
    client = _client(seeded_tenant, ["finance"])  # read-only role
    pair = client.get("/duplicates").json()["candidates"][0]
    resp = client.post(
        f"/duplicates/{pair['id']}/review",
        json={"decision": "not_duplicate"},
    )
    assert resp.status_code == 403


def test_list_requires_auth() -> None:
    assert TestClient(app).get("/duplicates").status_code == 401
