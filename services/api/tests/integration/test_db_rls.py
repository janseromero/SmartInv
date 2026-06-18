"""Integration tests for the database foundations (CV1.E5).

Run against a real Postgres (D4). They verify that:

1. ``alembic upgrade head`` produced all eight schemas and their tables.
2. Row-Level Security enforces tenant isolation and default-deny for a
   least-privilege (non-superuser) role.

Skipped automatically when no database is reachable, so the unit suite still
runs on a laptop without the stack up.
"""

from __future__ import annotations

import psycopg
import pytest
from api.config import get_settings

SCHEMAS = ("core", "inventory", "sources", "ml", "agent", "workflow", "audit", "rag")
EXPECTED_TABLE_COUNT = 29  # +1 for ml.duplicate_candidates (CV2.E4)
ROLE = "rls_test_role"


@pytest.fixture(scope="module")
def db_url() -> str:
    # Uses the admin (superuser) URL: this test creates roles and SET ROLEs.
    url = get_settings().effective_admin_database_url
    try:
        with psycopg.connect(url, connect_timeout=3):
            pass
    except psycopg.OperationalError:
        pytest.skip("database not reachable")
    return url


def _drop_test_role(cur: psycopg.Cursor) -> None:
    cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (ROLE,))
    if cur.fetchone():
        for schema in ("core", "inventory"):
            cur.execute(f"REVOKE ALL ON ALL TABLES IN SCHEMA {schema} FROM {ROLE}")  # noqa: S608
            cur.execute(f"REVOKE ALL ON SCHEMA {schema} FROM {ROLE}")  # noqa: S608
        cur.execute(f"DROP ROLE {ROLE}")  # noqa: S608


def test_all_schemas_and_tables_present(db_url: str) -> None:
    with psycopg.connect(db_url) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT count(*) FROM information_schema.tables WHERE table_schema = ANY(%s)",
            (list(SCHEMAS),),
        )
        row = cur.fetchone()
        assert row is not None
        assert row[0] == EXPECTED_TABLE_COUNT


def test_rls_enforces_isolation_and_default_deny(db_url: str) -> None:
    # --- setup as admin (superuser bypasses RLS, so seeding is unaffected) ---
    with psycopg.connect(db_url) as admin:
        admin.autocommit = True
        with admin.cursor() as cur:
            _drop_test_role(cur)
            cur.execute(f"CREATE ROLE {ROLE} NOSUPERUSER NOBYPASSRLS")  # noqa: S608
            for schema in ("core", "inventory"):
                cur.execute(f"GRANT USAGE ON SCHEMA {schema} TO {ROLE}")  # noqa: S608
                cur.execute(  # noqa: S608
                    f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES "
                    f"IN SCHEMA {schema} TO {ROLE}"
                )
            cur.execute(
                "INSERT INTO core.tenants(slug, name, status) "
                "VALUES ('rls_a', 'A', 'active') RETURNING id"
            )
            tenant_a = cur.fetchone()[0]  # type: ignore[index]
            cur.execute(
                "INSERT INTO core.tenants(slug, name, status) "
                "VALUES ('rls_b', 'B', 'active') RETURNING id"
            )
            tenant_b = cur.fetchone()[0]  # type: ignore[index]
            for tenant_id, source_id in ((tenant_a, "1"), (tenant_b, "2")):
                cur.execute(
                    "INSERT INTO inventory.items"
                    "(tenant_id, source_system, source_id, item_number) "
                    "VALUES (%s, 'maximo', %s, 'I')",
                    (tenant_id, source_id),
                )

    try:
        # --- isolation: as least-privilege role, tenant A sees only its row ---
        with psycopg.connect(db_url) as conn, conn.cursor() as cur:
            cur.execute(f"SET ROLE {ROLE}")  # noqa: S608
            cur.execute("SELECT set_config('app.current_tenant_id', %s, true)", (str(tenant_a),))
            cur.execute("SELECT count(*) FROM inventory.items WHERE source_id IN ('1', '2')")
            assert cur.fetchone()[0] == 1  # type: ignore[index]
            conn.rollback()

        # --- default-deny: no tenant set -> zero rows visible ---
        with psycopg.connect(db_url) as conn, conn.cursor() as cur:
            cur.execute(f"SET ROLE {ROLE}")  # noqa: S608
            cur.execute("SELECT count(*) FROM inventory.items WHERE source_id IN ('1', '2')")
            assert cur.fetchone()[0] == 0  # type: ignore[index]
            conn.rollback()

        # --- WITH CHECK: cannot write a row for a different tenant ---
        with psycopg.connect(db_url) as conn, conn.cursor() as cur:
            cur.execute(f"SET ROLE {ROLE}")  # noqa: S608
            cur.execute("SELECT set_config('app.current_tenant_id', %s, true)", (str(tenant_a),))
            with pytest.raises(psycopg.errors.Error):
                cur.execute(
                    "INSERT INTO inventory.items"
                    "(tenant_id, source_system, source_id, item_number) "
                    "VALUES (%s, 'maximo', '9', 'X')",
                    (tenant_b,),
                )
            conn.rollback()
    finally:
        with psycopg.connect(db_url) as admin:
            admin.autocommit = True
            with admin.cursor() as cur:
                cur.execute("DELETE FROM core.tenants WHERE slug IN ('rls_a', 'rls_b')")
                _drop_test_role(cur)
