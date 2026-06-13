"""Shared pytest fixtures for the SmartInv API tests."""

from collections.abc import Iterator

import pytest
from api.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Provide a FastAPI :class:`TestClient` for endpoint tests."""
    with TestClient(app) as test_client:
        yield test_client
