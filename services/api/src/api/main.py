"""SmartInv API entrypoint.

Exposes a FastAPI application with an initial ``/health`` endpoint and an
OpenAPI schema at ``/openapi.json`` (interactive docs at ``/docs``).
"""

from datetime import UTC, datetime
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field

from api.config import get_settings

settings = get_settings()

app = FastAPI(
    title="SmartInv API",
    description="AI-Powered MRO Inventory Intelligence Platform",
    version=settings.version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


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
