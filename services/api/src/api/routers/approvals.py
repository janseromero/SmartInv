"""Approval queue API (CV6.E2).

Read and transition Postgres-backed approval workflows. The workflow engine owns
state transitions; this router shapes them for the approval queue UI.
"""

from __future__ import annotations

import uuid
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.auth.dependencies import get_current_user, get_tenant_session, require_role
from api.auth.models import CurrentUser
from api.contracts.workflow_engine import InvalidWorkflowTransitionError
from api.db.models.ml import Recommendation
from api.db.models.workflow import Approval, ApprovalPolicy
from api.infra.providers import get_workflow_engine

router = APIRouter(prefix="/approvals", tags=["approvals"])

READ_ROLES = ("admin", "planner", "manager", "finance")
ACT_ROLES = READ_ROLES
TERMINAL_STATES = {"approved", "rejected"}


class ApprovalStepResponse(BaseModel):
    state: str
    reviewer_type: Literal["role", "user"]
    reviewer: str
    ui_state: Literal["pending", "active", "approved", "rejected"]


class ApprovalRowResponse(BaseModel):
    id: uuid.UUID
    workflow_type: str
    state: str
    current_reviewer_type: str | None
    current_reviewer: str | None
    current_actor: str | None
    created_at: str
    updated_at: str
    recommendation_id: uuid.UUID | None
    claim: str
    target_label: str
    confidence: float | None
    model_version: str | None
    evidence: list[dict[str, str]]
    impact: dict[str, str]
    steps: list[ApprovalStepResponse]


class ApprovalPageResponse(BaseModel):
    approvals: list[ApprovalRowResponse]
    total: int


class ApprovalActionRequest(BaseModel):
    action: Literal["approve", "request_changes", "reject"]
    reason_code: str | None = None
    reason_note: str | None = None
    idempotency_key: str = Field(..., min_length=1)


class ApprovalActionResponse(BaseModel):
    id: uuid.UUID
    state: str
    current_reviewer_type: str | None
    current_reviewer: str | None


class ApprovalPolicyResponse(BaseModel):
    id: uuid.UUID
    workflow_type: str
    min_value: float | None
    max_value: float | None
    min_criticality: int | None
    required_path: list[dict[str, Any]]
    priority: int
    status: str


def _is_assigned_to_user(approval: Approval, user: CurrentUser) -> bool:
    if approval.current_reviewer_type == "role":
        return approval.current_reviewer in user.roles
    if approval.current_reviewer_type == "user":
        return approval.current_reviewer in {user.sub, user.email}
    return False


def _ui_state(approval: Approval, step_index: int, step: dict[str, Any]) -> str:
    if approval.state == "rejected":
        return "rejected" if step_index == approval.current_step_index else "pending"
    if approval.state == "approved":
        return "approved"
    if step_index < approval.current_step_index:
        return "approved"
    if step_index == approval.current_step_index and approval.state == step.get("state"):
        return "active"
    return "pending"


def _format_money(value: Any) -> str | None:
    if value is None:
        return None
    try:
        return f"${float(value):,.0f}"
    except (TypeError, ValueError):
        return str(value)


def _approval_to_response(
    approval: Approval, recommendation: Recommendation | None
) -> ApprovalRowResponse:
    payload = approval.payload or {}
    claim = recommendation.claim if recommendation else str(payload.get("claim") or approval.type)
    confidence = (
        float(recommendation.confidence) if recommendation and recommendation.confidence else None
    )
    model_version = recommendation.model_version if recommendation else payload.get("model_version")
    target_label = str(
        payload.get("item_number")
        or payload.get("target_label")
        or (recommendation.target_type if recommendation else approval.type)
    )

    evidence: list[dict[str, str]] = []
    rec_evidence = recommendation.evidence if recommendation else payload.get("evidence", {})
    if isinstance(rec_evidence, dict):
        for key, value in rec_evidence.items():
            if isinstance(value, (str, int, float)):
                evidence.append({"metric": key, "value": str(value)})
    for key in ("value", "capital_impact", "estimated_value", "criticality"):
        if key in payload:
            value = (
                _format_money(payload[key])
                if "value" in key or "impact" in key
                else str(payload[key])
            )
            evidence.append({"metric": key.replace("_", " "), "value": value or "—"})
    evidence = evidence[:5]

    impact: dict[str, str] = {}
    for key in ("before", "after", "capital_impact", "stockout_delta", "risk_delta"):
        if key in payload:
            raw = payload[key]
            impact[key] = (_format_money(raw) or "—") if "capital" in key else str(raw)

    steps = [
        ApprovalStepResponse(
            state=str(step["state"]),
            reviewer_type=step["reviewer_type"],
            reviewer=str(step["reviewer"]),
            ui_state=_ui_state(approval, index, step),  # type: ignore[arg-type]
        )
        for index, step in enumerate(approval.approval_path)
    ]

    return ApprovalRowResponse(
        id=approval.id,
        workflow_type=approval.type,
        state=approval.state,
        current_reviewer_type=approval.current_reviewer_type,
        current_reviewer=approval.current_reviewer,
        current_actor=approval.current_actor,
        created_at=approval.created_at.isoformat(),
        updated_at=approval.updated_at.isoformat(),
        recommendation_id=approval.recommendation_id,
        claim=claim,
        target_label=target_label,
        confidence=confidence,
        model_version=model_version,
        evidence=evidence,
        impact=impact,
        steps=steps,
    )


@router.get("", response_model=ApprovalPageResponse)
def list_approvals(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_tenant_session)],
    _reader: Annotated[CurrentUser, Depends(require_role(*READ_ROLES))],
    bucket: Annotated[
        Literal["my_queue", "semi", "completed", "overrides", "all"], Query()
    ] = "my_queue",
) -> ApprovalPageResponse:
    approvals = list(session.scalars(select(Approval).order_by(Approval.updated_at.desc())).all())
    if bucket == "my_queue":
        approvals = [
            a for a in approvals if a.state not in TERMINAL_STATES and _is_assigned_to_user(a, user)
        ]
    elif bucket == "semi":
        approvals = [a for a in approvals if a.state not in TERMINAL_STATES]
    elif bucket == "completed":
        approvals = [a for a in approvals if a.state in TERMINAL_STATES]
    elif bucket == "overrides":
        approvals = [a for a in approvals if (a.payload or {}).get("decision") == "override"]

    rec_ids: list[uuid.UUID] = [a.recommendation_id for a in approvals if a.recommendation_id]
    recommendations = (
        {
            r.id: r
            for r in session.scalars(
                select(Recommendation).where(Recommendation.id.in_(rec_ids))
            ).all()
        }
        if rec_ids
        else {}
    )
    rows = [
        _approval_to_response(
            a, recommendations.get(a.recommendation_id) if a.recommendation_id else None
        )
        for a in approvals
    ]
    return ApprovalPageResponse(approvals=rows, total=len(rows))


@router.post("/{approval_id}/actions", response_model=ApprovalActionResponse)
def transition_approval(
    approval_id: uuid.UUID,
    body: ApprovalActionRequest,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_tenant_session)],
    _actor: Annotated[CurrentUser, Depends(require_role(*ACT_ROLES))],
) -> ApprovalActionResponse:
    approval = session.get(Approval, approval_id)
    if approval is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval not found")
    if "admin" not in user.roles and not _is_assigned_to_user(approval, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Approval not assigned to user"
        )

    event = "approve" if body.action == "approve" else "reject"
    payload = {
        "action": body.action,
        "reason_code": body.reason_code,
        "reason_note": body.reason_note,
    }
    try:
        handle = get_workflow_engine(session).signal(
            approval_id,
            event=event,
            actor=user.email or user.sub,
            payload=payload,
            idempotency_key=body.idempotency_key,
        )
    except InvalidWorkflowTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return ApprovalActionResponse(
        id=handle.id,
        state=handle.state,
        current_reviewer_type=handle.current_reviewer_type,
        current_reviewer=handle.current_reviewer,
    )


@router.get("/policies", response_model=list[ApprovalPolicyResponse])
def list_approval_policies(
    _reader: Annotated[CurrentUser, Depends(require_role(*READ_ROLES))],
    session: Annotated[Session, Depends(get_tenant_session)],
) -> list[ApprovalPolicyResponse]:
    policies = session.scalars(
        select(ApprovalPolicy).order_by(
            ApprovalPolicy.workflow_type.asc(), ApprovalPolicy.priority.desc()
        )
    ).all()
    return [
        ApprovalPolicyResponse(
            id=policy.id,
            workflow_type=policy.workflow_type,
            min_value=float(policy.min_value) if policy.min_value is not None else None,
            max_value=float(policy.max_value) if policy.max_value is not None else None,
            min_criticality=policy.min_criticality,
            required_path=policy.required_path,
            priority=policy.priority,
            status=policy.status,
        )
        for policy in policies
    ]
