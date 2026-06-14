"""create least-privilege app role

Creates the ``smartinv_app`` runtime role (NOSUPERUSER, NOBYPASSRLS) the API
connects with so Row-Level Security actually applies (ADR-020). Migrations and
admin keep using the superuser role.

The role is created with a dev password for local/CI convenience. In
production the password is managed out of band (secret manager + ``ALTER ROLE
... PASSWORD``); never rely on this default with real data.

Revision ID: 21516e9bb4a6
Revises: 7a266032b044
Create Date: 2026-06-14 13:20:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "21516e9bb4a6"
down_revision: str | None = "7a266032b044"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP_ROLE = "smartinv_app"
APP_ROLE_DEV_PASSWORD = "smartinv_app"  # noqa: S105 — dev/CI default, see docstring
SCHEMAS = (
    "core",
    "inventory",
    "sources",
    "ml",
    "agent",
    "workflow",
    "audit",
    "rag",
)


def upgrade() -> None:
    op.execute(
        f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '{APP_ROLE}') THEN
                CREATE ROLE {APP_ROLE} LOGIN PASSWORD '{APP_ROLE_DEV_PASSWORD}'
                    NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE;
            END IF;
        END
        $$;
        """
    )
    for schema in SCHEMAS:
        op.execute(f"GRANT USAGE ON SCHEMA {schema} TO {APP_ROLE}")
        op.execute(
            f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA {schema} TO {APP_ROLE}"
        )
        op.execute(f"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA {schema} TO {APP_ROLE}")
        # Future tables/sequences created by the migration role are auto-granted.
        op.execute(
            f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} "
            f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {APP_ROLE}"
        )
        op.execute(
            f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} "
            f"GRANT USAGE, SELECT ON SEQUENCES TO {APP_ROLE}"
        )


def downgrade() -> None:
    for schema in SCHEMAS:
        op.execute(
            f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} "
            f"REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLES FROM {APP_ROLE}"
        )
        op.execute(
            f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} "
            f"REVOKE USAGE, SELECT ON SEQUENCES FROM {APP_ROLE}"
        )
        op.execute(f"REVOKE ALL ON ALL SEQUENCES IN SCHEMA {schema} FROM {APP_ROLE}")
        op.execute(f"REVOKE ALL ON ALL TABLES IN SCHEMA {schema} FROM {APP_ROLE}")
        op.execute(f"REVOKE USAGE ON SCHEMA {schema} FROM {APP_ROLE}")
    op.execute(f"DROP ROLE IF EXISTS {APP_ROLE}")
