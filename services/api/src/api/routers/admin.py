"""Connector governance endpoints (CV2.E1).

Read-only status of source connectors + their recent sync runs, plus a
fixture-sync trigger. No credentials are stored or accepted here — real Maximo
credentials live in the secret manager (ADR-024, Pattern A).
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.anomaly.service import run_anomaly_scan
from api.audit.service import record_audit_event
from api.auth.dependencies import get_current_user, get_tenant_session, require_role
from api.auth.models import CurrentUser
from api.db.models.sources import Connector, SyncRun
from api.dedup.service import run_dedup
from api.forecast.service import run_forecast
from api.ingestion.fixture_sync import run_fixture_sync
from api.optimize.service import run_optimization
from api.risk.service import run_risk_scan
from api.scoring.service import run_scoring

router = APIRouter(prefix="/admin", tags=["admin"])

_RECENT_RUNS = 6


class SyncRunOut(BaseModel):
    object_type: str
    status: str
    records_read: int
    records_upserted: int
    records_failed: int
    finished_at: datetime | None = None


class ConnectorOut(BaseModel):
    id: uuid.UUID
    source_system: str
    name: str
    status: str
    runs: list[SyncRunOut]


@router.get("/connectors", response_model=list[ConnectorOut], summary="List source connectors")
def list_connectors(
    _user: Annotated[CurrentUser, Depends(require_role("admin"))],
    session: Annotated[Session, Depends(get_tenant_session)],
) -> list[ConnectorOut]:
    connectors = session.scalars(select(Connector).order_by(Connector.name)).all()
    result: list[ConnectorOut] = []
    for connector in connectors:
        runs = session.scalars(
            select(SyncRun)
            .where(SyncRun.connector_id == connector.id)
            .order_by(SyncRun.started_at.desc())
            .limit(_RECENT_RUNS)
        ).all()
        result.append(
            ConnectorOut(
                id=connector.id,
                source_system=connector.source_system,
                name=connector.name,
                status=connector.status,
                runs=[
                    SyncRunOut(
                        object_type=run.object_type,
                        status=run.status,
                        records_read=run.records_read,
                        records_upserted=run.records_upserted,
                        records_failed=run.records_failed,
                        finished_at=run.finished_at,
                    )
                    for run in runs
                ],
            )
        )
    return result


@router.post("/connectors/sync", summary="Run the fixture connector sync")
def trigger_fixture_sync(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_tenant_session)],
    _admin: Annotated[CurrentUser, Depends(require_role("admin"))],
) -> dict[str, dict[str, int]]:
    result = run_fixture_sync(session, user.tenant_id)
    _audit_admin_job(session, user, "admin.connectors.sync", result)
    return result


@router.post("/score", summary="Recompute inventory health scores")
def trigger_scoring(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_tenant_session)],
    _admin: Annotated[CurrentUser, Depends(require_role("admin"))],
) -> dict[str, int]:
    result = run_scoring(session, user.tenant_id)
    _audit_admin_job(session, user, "admin.score", result)
    return result


@router.post("/dedup", summary="Recompute duplicate-detection candidates")
def trigger_dedup(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_tenant_session)],
    _admin: Annotated[CurrentUser, Depends(require_role("admin"))],
) -> dict[str, int]:
    result = run_dedup(session, user.tenant_id)
    _audit_admin_job(session, user, "admin.dedup", result)
    return result


@router.post("/anomalies", summary="Recompute anomaly detections")
def trigger_anomaly_scan(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_tenant_session)],
    _admin: Annotated[CurrentUser, Depends(require_role("admin"))],
) -> dict[str, int]:
    result = run_anomaly_scan(session, user.tenant_id)
    _audit_admin_job(session, user, "admin.anomalies", result)
    return result


@router.post("/forecast", summary="Recompute demand forecasts")
def trigger_forecast(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_tenant_session)],
    _admin: Annotated[CurrentUser, Depends(require_role("admin"))],
) -> dict[str, int]:
    result = run_forecast(session, user.tenant_id)
    _audit_admin_job(session, user, "admin.forecast", result)
    return result


@router.post("/optimize", summary="Recompute inventory recommendations")
def trigger_optimization(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_tenant_session)],
    _admin: Annotated[CurrentUser, Depends(require_role("admin"))],
) -> dict[str, int]:
    result = run_optimization(session, user.tenant_id)
    _audit_admin_job(session, user, "admin.optimize", result)
    return result


@router.post("/risk", summary="Recompute operational risk scores")
def trigger_risk_scan(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_tenant_session)],
    _admin: Annotated[CurrentUser, Depends(require_role("admin"))],
) -> dict[str, int]:
    result = run_risk_scan(session, user.tenant_id)
    _audit_admin_job(session, user, "admin.risk", result)
    return result


def _audit_admin_job(
    session: Session, user: CurrentUser, action: str, result: Mapping[str, object]
) -> None:
    record_audit_event(
        session,
        tenant_id=user.tenant_id,
        actor=user.email or user.sub,
        action=action,
        resource_type="admin.job",
        resource_id=action,
        payload={"result": result},
    )
