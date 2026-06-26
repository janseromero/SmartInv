"""cv6 configurable approval path

Revision ID: d1c2f3a4b5c6
Revises: a7a6b9eaa367
Create Date: 2026-06-26 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d1c2f3a4b5c6"
down_revision: str | None = "a7a6b9eaa367"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_DEFAULT_PATH = """'[{
  "state": "planner_review",
  "reviewer_type": "role",
  "reviewer": "planner"
}]'::jsonb"""


def upgrade() -> None:
    op.add_column(
        "approvals",
        sa.Column("current_step_index", sa.Integer(), nullable=False, server_default=sa.text("-1")),
        schema="workflow",
    )
    op.add_column(
        "approvals",
        sa.Column("current_reviewer_type", sa.String(length=16), nullable=True),
        schema="workflow",
    )
    op.add_column(
        "approvals",
        sa.Column("current_reviewer", sa.String(length=128), nullable=True),
        schema="workflow",
    )
    op.add_column(
        "approvals",
        sa.Column(
            "approval_path",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text(_DEFAULT_PATH),
        ),
        schema="workflow",
    )
    op.add_column(
        "approval_events",
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        schema="workflow",
    )
    op.add_column(
        "approval_events",
        sa.Column("from_state", sa.String(length=32), nullable=True),
        schema="workflow",
    )
    op.add_column(
        "approval_events",
        sa.Column("to_state", sa.String(length=32), nullable=True),
        schema="workflow",
    )
    op.create_unique_constraint(
        "uq_approval_events_idempotency",
        "approval_events",
        ["tenant_id", "approval_id", "idempotency_key"],
        schema="workflow",
    )
    op.alter_column("approvals", "current_step_index", server_default=None, schema="workflow")
    op.alter_column("approvals", "approval_path", server_default=None, schema="workflow")


def downgrade() -> None:
    op.drop_constraint(
        "uq_approval_events_idempotency", "approval_events", schema="workflow", type_="unique"
    )
    op.drop_column("approval_events", "to_state", schema="workflow")
    op.drop_column("approval_events", "from_state", schema="workflow")
    op.drop_column("approval_events", "idempotency_key", schema="workflow")
    op.drop_column("approvals", "approval_path", schema="workflow")
    op.drop_column("approvals", "current_reviewer", schema="workflow")
    op.drop_column("approvals", "current_reviewer_type", schema="workflow")
    op.drop_column("approvals", "current_step_index", schema="workflow")
