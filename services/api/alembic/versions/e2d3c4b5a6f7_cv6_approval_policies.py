"""cv6 approval policies

Revision ID: e2d3c4b5a6f7
Revises: d1c2f3a4b5c6
Create Date: 2026-06-26 00:00:00.000001
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "e2d3c4b5a6f7"
down_revision: str | None = "d1c2f3a4b5c6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_POLICY = "tenant_isolation"
_PREDICATE = "tenant_id = current_setting('app.current_tenant_id', true)::uuid"


def upgrade() -> None:
    op.create_table(
        "approval_policies",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("workflow_type", sa.String(length=32), nullable=False),
        sa.Column("min_value", sa.Numeric(14, 2), nullable=True),
        sa.Column("max_value", sa.Numeric(14, 2), nullable=True),
        sa.Column("min_criticality", sa.SmallInteger(), nullable=True),
        sa.Column("required_path", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
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
            ["tenant_id"],
            ["core.tenants.id"],
            name=op.f("fk_approval_policies_tenant_id_tenants"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_approval_policies")),
        schema="workflow",
    )
    op.create_index(
        op.f("ix_workflow_approval_policies_tenant_id"),
        "approval_policies",
        ["tenant_id"],
        unique=False,
        schema="workflow",
    )
    op.create_index(
        "ix_workflow_approval_policies_lookup",
        "approval_policies",
        ["tenant_id", "workflow_type", "status", "priority"],
        unique=False,
        schema="workflow",
    )
    op.execute("ALTER TABLE workflow.approval_policies ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE workflow.approval_policies FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY "
        f"{_POLICY} ON workflow.approval_policies USING ({_PREDICATE}) WITH CHECK ({_PREDICATE})"
    )


def downgrade() -> None:
    op.execute(f"DROP POLICY IF EXISTS {_POLICY} ON workflow.approval_policies")
    op.drop_index(
        "ix_workflow_approval_policies_lookup", table_name="approval_policies", schema="workflow"
    )
    op.drop_index(
        op.f("ix_workflow_approval_policies_tenant_id"),
        table_name="approval_policies",
        schema="workflow",
    )
    op.drop_table("approval_policies", schema="workflow")
