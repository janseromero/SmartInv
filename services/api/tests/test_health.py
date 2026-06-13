"""Tests for the ``/health`` endpoint."""

from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    """The /health endpoint returns 200 with ``status="ok"``."""
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "smartinv-api"
    assert "version" in body
    assert "environment" in body
    assert "timestamp" in body


def test_health_exposes_configured_version(client: TestClient) -> None:
    """The /health endpoint exposes the configured service version."""
    response = client.get("/health")
    assert response.json()["version"] == "0.1.0"


def test_openapi_schema_is_published(client: TestClient) -> None:
    """The OpenAPI schema is available at /openapi.json."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "SmartInv API"
    assert "/health" in schema["paths"]
