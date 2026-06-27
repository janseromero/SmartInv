"""cv6 source writes

Revision ID: a1b2c3d4e5f6
Revises: f3a4b5c6d7e8
Create Date: 2026-06-27 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "f3a4b5c6d7e8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_POLICY = "tenant_isolation"
_PREDICATE = "tenant_id = current_setting('app.current_tenant_id', true)::uuid"


def upgrade() -> None:
    op.create_table(
        "source_writes",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("recommendation_id", sa.UUID(), nullable=True),
        sa.Column("approval_id", sa.UUID(), nullable=True),
        sa.Column("target_system", sa.String(length=32), nullable=False),
        sa.Column("operation", sa.String(length=32), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.String(length=512), nullable=True),
        sa.Column("receipt", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["recommendation_id"],
            ["ml.recommendations.id"],
            name=op.f("fk_source_writes_recommendation_id_recommendations"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["approval_id"],
            ["workflow.approvals.id"],
            name=op.f("fk_source_writes_approval_id_approvals"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["core.tenants.id"],
            name=op.f("fk_source_writes_tenant_id_tenants"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_source_writes")),
        sa.UniqueConstraint("tenant_id", "idempotency_key", name="uq_source_writes_idempotency"),
        schema="workflow",
    )
    op.create_index(
        op.f("ix_workflow_source_writes_tenant_id"),
        "source_writes",
        ["tenant_id"],
        unique=False,
        schema="workflow",
    )
    op.create_index(
        "ix_workflow_source_writes_status",
        "source_writes",
        ["tenant_id", "status"],
        unique=False,
        schema="workflow",
    )
    op.execute("ALTER TABLE workflow.source_writes ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE workflow.source_writes FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY "
        f"{_POLICY} ON workflow.source_writes USING ({_PREDICATE}) WITH CHECK ({_PREDICATE})"
    )


def downgrade() -> None:
    op.execute(f"DROP POLICY IF EXISTS {_POLICY} ON workflow.source_writes")
    op.drop_index("ix_workflow_source_writes_status", table_name="source_writes", schema="workflow")
    op.drop_index(
        op.f("ix_workflow_source_writes_tenant_id"),
        table_name="source_writes",
        schema="workflow",
    )
    op.drop_table("source_writes", schema="workflow")
