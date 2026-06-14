"""Capstone integration tests for CV1.E6 (Auth & Tenancy).

Exercises the full chain through real HTTP — JWT -> CurrentUser -> tenant
session GUC -> RLS -> least-privilege role — and asserts that cross-tenant data
access is impossible even though the endpoint never filters by tenant itself.

Skipped when no database is reachable.
"""

from __future__ import annotations

from collections.abc import Iterator

import psycopg
import pytest
from api.auth.tokens import mint_dev_token
from api.config import get_settings
from api.main import app
from fastapi.testclient import TestClient

ADMIN = get_settings().effective_admin_database_url


def _reachable() -> bool:
    try:
        with psycopg.connect(ADMIN, connect_timeout=3):
            return True
    except psycopg.OperationalError:
        return False


pytestmark = pytest.mark.skipif(not _reachable(), reason="database not reachable")


@pytest.fixture
def two_tenants() -> Iterator[tuple[str, str]]:
    """Create two tenants each with one item; yield their ids; clean up after."""
    with psycopg.connect(ADMIN) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO core.tenants(slug, name, status) "
                "VALUES ('e6_a', 'A', 'active'), ('e6_b', 'B', 'active') "
                "RETURNING id"
            )
            # fetch both ids deterministically by slug
            cur.execute("SELECT id FROM core.tenants WHERE slug = 'e6_a'")
            tenant_a = str(cur.fetchone()[0])  # type: ignore[index]
            cur.execute("SELECT id FROM core.tenants WHERE slug = 'e6_b'")
            tenant_b = str(cur.fetchone()[0])  # type: ignore[index]
            for tid, sid in ((tenant_a, "e6-1"), (tenant_b, "e6-2")):
                cur.execute(
                    "INSERT INTO inventory.items"
                    "(tenant_id, source_system, source_id, item_number) "
                    "VALUES (%s, 'maximo', %s, %s)",
                    (tid, sid, f"ITEM-{sid}"),
                )
    try:
        yield tenant_a, tenant_b
    finally:
        with psycopg.connect(ADMIN) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute("DELETE FROM core.tenants WHERE slug IN ('e6_a', 'e6_b')")


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def _token(tenant_id: str, roles: list[str]) -> str:
    return mint_dev_token(sub=f"user|{tenant_id}", tenant_id=tenant_id, roles=roles)


def test_requires_bearer_token(client: TestClient) -> None:
    assert client.get("/inventory/items").status_code == 401


def test_rejects_role_without_permission(client: TestClient, two_tenants: tuple[str, str]) -> None:
    tenant_a, _ = two_tenants
    token = _token(tenant_a, roles=["finance"])  # not an inventory-read role
    resp = client.get("/inventory/items", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_items_are_isolated_per_tenant(client: TestClient, two_tenants: tuple[str, str]) -> None:
    tenant_a, tenant_b = two_tenants

    resp_a = client.get(
        "/inventory/items",
        headers={"Authorization": f"Bearer {_token(tenant_a, ['planner'])}"},
    )
    resp_b = client.get(
        "/inventory/items",
        headers={"Authorization": f"Bearer {_token(tenant_b, ['planner'])}"},
    )
    assert resp_a.status_code == 200
    assert resp_b.status_code == 200

    numbers_a = {i["item_number"] for i in resp_a.json()}
    numbers_b = {i["item_number"] for i in resp_b.json()}

    assert "ITEM-e6-1" in numbers_a
    assert "ITEM-e6-2" not in numbers_a  # tenant A cannot see tenant B's item
    assert "ITEM-e6-2" in numbers_b
    assert "ITEM-e6-1" not in numbers_b


def test_me_reports_authenticated_principal(
    client: TestClient, two_tenants: tuple[str, str]
) -> None:
    tenant_a, _ = two_tenants
    resp = client.get("/me", headers={"Authorization": f"Bearer {_token(tenant_a, ['admin'])}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["tenant_id"] == tenant_a
    assert body["roles"] == ["admin"]
