"""Tests for CV6 approval-policy resolution."""

from __future__ import annotations

from decimal import Decimal

from api.contracts.workflow_engine import ApprovalStep
from api.workflow.policies import (
    ApprovalPolicyCandidate,
    PolicyInputs,
    choose_approval_path,
    extract_policy_inputs,
)

PLANNER = (ApprovalStep(state="planner_review", reviewer_type="role", reviewer="planner"),)
PLANNER_MANAGER = (
    ApprovalStep(state="planner_review", reviewer_type="role", reviewer="planner"),
    ApprovalStep(state="manager_review", reviewer_type="role", reviewer="manager"),
)
PLANNER_FINANCE = (
    ApprovalStep(state="planner_review", reviewer_type="role", reviewer="planner"),
    ApprovalStep(state="finance_review", reviewer_type="user", reviewer="cfo@example.com"),
)
PLANNER_MANAGER_FINANCE = (
    ApprovalStep(state="planner_review", reviewer_type="role", reviewer="planner"),
    ApprovalStep(state="manager_review", reviewer_type="role", reviewer="manager"),
    ApprovalStep(state="finance_review", reviewer_type="user", reviewer="cfo@example.com"),
)


def _policies() -> list[ApprovalPolicyCandidate]:
    return [
        ApprovalPolicyCandidate(workflow_type="risk_mitigation", required_path=PLANNER, priority=0),
        ApprovalPolicyCandidate(
            workflow_type="risk_mitigation",
            required_path=PLANNER_MANAGER,
            min_criticality=4,
            priority=10,
        ),
        ApprovalPolicyCandidate(
            workflow_type="risk_mitigation",
            required_path=PLANNER_FINANCE,
            min_value=Decimal("25000"),
            priority=20,
        ),
        ApprovalPolicyCandidate(
            workflow_type="risk_mitigation",
            required_path=PLANNER_MANAGER_FINANCE,
            min_value=Decimal("25000"),
            min_criticality=4,
            priority=30,
        ),
    ]


def test_low_value_low_criticality_uses_planner_path() -> None:
    path = choose_approval_path(
        _policies(), "risk_mitigation", PolicyInputs(value=Decimal("1000"), criticality=2)
    )
    assert path == PLANNER


def test_critical_item_adds_manager_review() -> None:
    path = choose_approval_path(
        _policies(), "risk_mitigation", PolicyInputs(value=Decimal("1000"), criticality=4)
    )
    assert path == PLANNER_MANAGER


def test_high_value_adds_finance_review_with_specific_user() -> None:
    path = choose_approval_path(
        _policies(), "risk_mitigation", PolicyInputs(value=Decimal("25000"), criticality=2)
    )
    assert path == PLANNER_FINANCE
    assert path[-1].reviewer_type == "user"
    assert path[-1].reviewer == "cfo@example.com"


def test_high_value_critical_item_uses_most_specific_path() -> None:
    path = choose_approval_path(
        _policies(), "risk_mitigation", PolicyInputs(value=Decimal("90000"), criticality=5)
    )
    assert path == PLANNER_MANAGER_FINANCE


def test_non_matching_workflow_type_returns_none() -> None:
    path = choose_approval_path(
        _policies(), "item_merge", PolicyInputs(value=Decimal("90000"), criticality=5)
    )
    assert path is None


def test_extract_policy_inputs_accepts_envelope_aliases() -> None:
    inputs = extract_policy_inputs({"capital_impact": "12345.67", "item_criticality": "4"})
    assert inputs.value == Decimal("12345.67")
    assert inputs.criticality == 4
