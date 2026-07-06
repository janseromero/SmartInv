"""Versioned tool catalog — the boundary between the LLM and SmartInv's data.

The LLM never runs SQL. It may only invoke catalog tools, which are deterministic,
tenant-scoped (RLS), role-scoped, Pydantic-validated, and audited. Each tool
returns a flat set of numeric *facts* plus a source link; those facts are the
only values a composed answer is allowed to state (see :mod:`api.agent.grounding`).

Slice 1 ships two argument-free portfolio tools built directly on the tenant
session. Parameterized tools (item filters, per-plant drill-down) arrive in the
next slice; the ``ToolSpec`` already carries the version/scope/schema surface
they need.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.audit.service import record_audit_event
from api.auth.models import CurrentUser
from api.db.models.inventory import Item

READ_ROLES = ("admin", "planner", "manager", "finance")


class ToolScopeError(Exception):
    """Raised when a caller lacks the role scope a tool requires."""


class ToolOutput(BaseModel):
    """A tool result: numeric facts, human labels, and a source-record link."""

    tool: str
    version: str
    facts: dict[str, float]
    labels: dict[str, str] = {}
    source: str


Executor = Callable[[Session], ToolOutput]


@dataclass(frozen=True)
class ToolSpec:
    """Catalog entry: identity, scope, description, and executor."""

    name: str
    version: str
    description: str
    scope_roles: tuple[str, ...]
    executor: Executor
    input_schema: dict[str, object] = field(default_factory=dict)


# --- executors ---------------------------------------------------------------


def _inventory_summary(session: Session) -> ToolOutput:
    total = session.scalar(select(func.count()).select_from(Item)) or 0
    by_class: dict[str, int] = {
        (row[0] or ""): row[1]
        for row in session.execute(
            select(Item.health_class, func.count()).group_by(Item.health_class)
        ).all()
    }
    return ToolOutput(
        tool="inventory.summary",
        version="v1",
        facts={
            "total_items": float(total),
            "healthy_items": float(by_class.get("healthy", 0)),
            "excess_items": float(by_class.get("excess_slow", 0)),
            "obsolete_risk_items": float(by_class.get("obsolete_risk", 0)),
            "dq_risk_items": float(by_class.get("dq_risk", 0)),
        },
        labels={
            "total_items": "Total items",
            "healthy_items": "Healthy items",
            "excess_items": "Excess / slow-moving items",
            "obsolete_risk_items": "Obsolescence-risk items",
            "dq_risk_items": "Data-quality-risk items",
        },
        source="/health",
    )


def _risk_summary(session: Session) -> ToolOutput:
    critical_spares = (
        session.scalar(
            select(func.count()).select_from(Item).where(Item.is_critical_spare.is_(True))
        )
        or 0
    )
    high_risk = (
        session.scalar(
            select(func.count()).select_from(Item).where(Item.risk_class.in_(("critical", "high")))
        )
        or 0
    )
    downtime = (
        session.scalar(
            select(
                func.coalesce(func.sum(Item.risk_breakdown["downtime_exposure"].as_float()), 0.0)
            )
        )
        or 0.0
    )
    return ToolOutput(
        tool="risk.summary",
        version="v1",
        facts={
            "critical_spares": float(critical_spares),
            "high_risk_items": float(high_risk),
            "total_downtime_exposure": round(float(downtime), 2),
        },
        labels={
            "critical_spares": "Critical spares",
            "high_risk_items": "High/critical-risk items",
            "total_downtime_exposure": "Total downtime exposure ($)",
        },
        source="/risk",
    )


# --- registry ----------------------------------------------------------------

REGISTRY: dict[str, ToolSpec] = {
    "inventory.summary": ToolSpec(
        name="inventory.summary",
        version="v1",
        description=(
            "Portfolio inventory health counts: total items and how many are "
            "healthy, excess/slow-moving, obsolescence-risk, or data-quality-risk."
        ),
        scope_roles=READ_ROLES,
        executor=_inventory_summary,
    ),
    "risk.summary": ToolSpec(
        name="risk.summary",
        version="v1",
        description=(
            "Portfolio operational-risk counts: number of critical spares, "
            "high/critical-risk items, and total downtime exposure in dollars."
        ),
        scope_roles=READ_ROLES,
        executor=_risk_summary,
    ),
}


def list_tools() -> list[ToolSpec]:
    """Return the active tool specs (stable order for prompts and tests)."""
    return [REGISTRY[name] for name in sorted(REGISTRY)]


def run_tool(
    session: Session,
    user: CurrentUser,
    name: str,
    tenant_id: uuid.UUID,
) -> ToolOutput:
    """Scope-check, execute, and audit a single tool call.

    Raises :class:`ToolScopeError` (mapped to 403 by the router) when the caller
    lacks the tool's role scope, and :class:`KeyError` for an unknown tool.
    """
    spec = REGISTRY[name]
    if not user.has_any_role(spec.scope_roles):
        raise ToolScopeError(f"{name} requires one of roles: {', '.join(spec.scope_roles)}")

    output = spec.executor(session)
    record_audit_event(
        session,
        tenant_id=tenant_id,
        actor=user.sub,
        action="agent.tool_invoke",
        resource_type="tool",
        resource_id=f"{spec.name}@{spec.version}",
        payload={"facts": output.facts},
    )
    return output
