"""cv6 audit event indexes

Revision ID: f3a4b5c6d7e8
Revises: e2d3c4b5a6f7
Create Date: 2026-06-26 00:00:00.000002
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "f3a4b5c6d7e8"
down_revision: str | None = "e2d3c4b5a6f7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_audit_events_tenant_actor_action_time",
        "events",
        ["tenant_id", "actor", "action", "occurred_at"],
        unique=False,
        schema="audit",
    )


def downgrade() -> None:
    op.drop_index("ix_audit_events_tenant_actor_action_time", table_name="events", schema="audit")
