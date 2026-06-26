"""Approval-policy resolution for CV6 workflow paths.

Policies are tenant-scoped rules that convert workflow facts (type, value, and
criticality) into the concrete ordered reviewer path persisted on an approval.
The engine executes the path; this module chooses it.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, cast

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.contracts.workflow_engine import (
    ApprovalStep,
    InvalidApprovalPathError,
    ReviewerType,
    WorkflowState,
)
from api.db.models.workflow import ApprovalPolicy

VALUE_KEYS = ("value", "estimated_value", "capital_impact", "exposure_value", "amount")
CRITICALITY_KEYS = ("criticality", "item_criticality", "risk_criticality")


@dataclass(frozen=True)
class PolicyInputs:
    """Facts used to resolve a workflow policy."""

    value: Decimal | None
    criticality: int | None


@dataclass(frozen=True)
class ApprovalPolicyCandidate:
    """In-memory projection of a policy row for deterministic selection tests."""

    workflow_type: str
    required_path: tuple[ApprovalStep, ...]
    min_value: Decimal | None = None
    max_value: Decimal | None = None
    min_criticality: int | None = None
    priority: int = 0
    status: str = "active"


def _decimal_or_none(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _int_or_none(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def extract_policy_inputs(payload: dict[str, Any]) -> PolicyInputs:
    """Extract policy facts from a recommendation/workflow payload.

    CV3/CV4 envelopes use slightly different names for money and criticality.
    The policy resolver accepts the common aliases and treats missing values as
    unknown rather than inventing defaults.
    """

    value = next((_decimal_or_none(payload.get(key)) for key in VALUE_KEYS if key in payload), None)
    criticality = next(
        (_int_or_none(payload.get(key)) for key in CRITICALITY_KEYS if key in payload), None
    )
    return PolicyInputs(value=value, criticality=criticality)


def path_from_json(raw_path: list[dict[str, Any]]) -> tuple[ApprovalStep, ...]:
    """Parse a JSON policy path into typed steps."""

    path = tuple(
        ApprovalStep(
            state=cast(WorkflowState, step.get("state")),
            reviewer_type=cast(ReviewerType, step.get("reviewer_type")),
            reviewer=step.get("reviewer", ""),
        )
        for step in raw_path
    )
    if not path:
        raise InvalidApprovalPathError("policy required_path must contain at least one step")
    return path


def _matches(candidate: ApprovalPolicyCandidate, workflow_type: str, inputs: PolicyInputs) -> bool:
    if candidate.status != "active" or candidate.workflow_type != workflow_type:
        return False
    if candidate.min_value is not None and (
        inputs.value is None or inputs.value < candidate.min_value
    ):
        return False
    if candidate.max_value is not None and (
        inputs.value is None or inputs.value > candidate.max_value
    ):
        return False
    if candidate.min_criticality is not None and (
        inputs.criticality is None or inputs.criticality < candidate.min_criticality
    ):
        return False
    return True


def choose_approval_path(
    candidates: Iterable[ApprovalPolicyCandidate], workflow_type: str, inputs: PolicyInputs
) -> tuple[ApprovalStep, ...] | None:
    """Return the highest-priority matching policy path, if any."""

    matches = [candidate for candidate in candidates if _matches(candidate, workflow_type, inputs)]
    if not matches:
        return None
    matches.sort(
        key=lambda candidate: (
            candidate.priority,
            candidate.min_criticality or -1,
            candidate.min_value or Decimal("-1"),
        ),
        reverse=True,
    )
    return matches[0].required_path


def resolve_approval_path(
    session: Session,
    *,
    workflow_type: str,
    payload: dict[str, Any],
) -> tuple[ApprovalStep, ...] | None:
    """Resolve a configured approval path from tenant-scoped Postgres policies."""

    rows = session.scalars(
        select(ApprovalPolicy).where(
            ApprovalPolicy.workflow_type == workflow_type,
            ApprovalPolicy.status == "active",
        )
    ).all()
    candidates = (
        ApprovalPolicyCandidate(
            workflow_type=row.workflow_type,
            required_path=path_from_json(row.required_path),
            min_value=row.min_value,
            max_value=row.max_value,
            min_criticality=row.min_criticality,
            priority=row.priority,
            status=row.status,
        )
        for row in rows
    )
    return choose_approval_path(candidates, workflow_type, extract_policy_inputs(payload))
