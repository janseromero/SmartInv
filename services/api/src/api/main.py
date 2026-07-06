"""SmartInv API entrypoint.

Exposes a FastAPI application with an initial ``/health`` endpoint and an
OpenAPI schema at ``/openapi.json`` (interactive docs at ``/docs``).
"""

from datetime import UTC, datetime
from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from api.config import get_settings
from api.routers import (
    admin,
    agents,
    anomalies,
    approvals,
    audit,
    dev_auth,
    duplicates,
    forecast,
    identity,
    inventory,
    recommendations,
    risk,
)

settings = get_settings()

app = FastAPI(
    title="SmartInv API",
    description="AI-Powered MRO Inventory Intelligence Platform",
    version=settings.version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dev_auth.router)
app.include_router(identity.router)
app.include_router(inventory.router)
app.include_router(duplicates.router)
app.include_router(anomalies.router)
app.include_router(recommendations.router)
app.include_router(forecast.router)
app.include_router(agents.router)
app.include_router(approvals.router)
app.include_router(audit.router)
app.include_router(risk.router)
app.include_router(admin.router)


class HealthResponse(BaseModel):
    """Payload returned by the ``/health`` endpoint."""

    status: Literal["ok"] = Field(..., description="Service health flag.")
    service: str = Field(..., description="Service identifier.")
    version: str = Field(..., description="Deployed service version.")
    environment: str = Field(..., description="Runtime environment.")
    timestamp: str = Field(..., description="UTC timestamp at response time.")


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["system"],
    summary="Service health check",
)
async def health() -> HealthResponse:
    """Return service health information.

    Used by load balancers, CI smoke tests, and uptime checks.
    """
    return HealthResponse(
        status="ok",
        service=settings.service_name,
        version=settings.version,
        environment=settings.environment,
        timestamp=datetime.now(UTC).isoformat(),
    )
