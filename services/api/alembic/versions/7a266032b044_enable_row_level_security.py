"""enable row level security

Enables Row-Level Security on every tenant-scoped table with a **default-deny**
policy: when the ``app.current_tenant_id`` GUC is not set, ``current_setting``
returns NULL, the predicate evaluates to NULL, and no rows are visible. The
application sets the GUC per request in CV1.E6.

FORCE ROW LEVEL SECURITY is applied so the table owner (the application role)
is also subject to the policy — RLS is the safety net, not bypassable by the
owning role.

Platform-level tables (``core.tenants``, ``core.roles``, ``ml.model_registry``,
``agent.tool_catalog``) are intentionally excluded — they carry no tenant_id.

Revision ID: 7a266032b044
Revises: 636dd6342d66
Create Date: 2026-06-14 12:55:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "7a266032b044"
down_revision: str | None = "636dd6342d66"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

POLICY_NAME = "tenant_isolation"

# (schema, table) for every tenant-scoped table. Keep this list explicit — it
# is a security boundary and is reviewed by a human (AGENTS.md slow lane).
TENANT_SCOPED_TABLES: tuple[tuple[str, str], ...] = (
    ("core", "users"),
    ("core", "role_bindings"),
    ("inventory", "items"),
    ("inventory", "balances"),
    ("inventory", "transactions"),
    ("inventory", "assets"),
    ("inventory", "locations"),
    ("inventory", "work_orders"),
    ("inventory", "purchase_orders"),
    ("inventory", "suppliers"),
    ("sources", "connectors"),
    ("sources", "sync_runs"),
    ("sources", "error_log"),
    ("ml", "predictions"),
    ("ml", "recommendations"),
    ("ml", "feature_snapshots"),
    ("agent", "conversations"),
    ("agent", "runs"),
    ("agent", "events"),
    ("workflow", "approvals"),
    ("workflow", "approval_events"),
    ("audit", "events"),
    ("rag", "documents"),
    ("rag", "chunks"),
)

_PREDICATE = "tenant_id = current_setting('app.current_tenant_id', true)::uuid"


def upgrade() -> None:
    for schema, table in TENANT_SCOPED_TABLES:
        fq = f"{schema}.{table}"
        op.execute(f"ALTER TABLE {fq} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {fq} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY {POLICY_NAME} ON {fq} USING ({_PREDICATE}) WITH CHECK ({_PREDICATE})"
        )


def downgrade() -> None:
    for schema, table in TENANT_SCOPED_TABLES:
        fq = f"{schema}.{table}"
        op.execute(f"DROP POLICY IF EXISTS {POLICY_NAME} ON {fq}")
        op.execute(f"ALTER TABLE {fq} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {fq} DISABLE ROW LEVEL SECURITY")
