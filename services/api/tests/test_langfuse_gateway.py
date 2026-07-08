"""Unit tests for Langfuse wiring in the LLM gateway (CV5.E1.S7).

Observability only: these assert the LiteLLM Langfuse callbacks are registered
when keys are present and left untouched otherwise. No model call is made.
"""

from __future__ import annotations

import os

import pytest
from api.config import Settings
from api.infra import llm_gateway


@pytest.fixture(autouse=True)
def _reset_flag() -> None:
    # The configured flag is process-global; reset so tests are order-independent.
    llm_gateway._langfuse_configured = False


def test_not_configured_when_keys_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "")
    assert llm_gateway.configure_langfuse(Settings()) is False


def test_registers_callbacks_when_keys_present(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf-test")
    monkeypatch.setenv("LANGFUSE_BASE_URL", "https://us.cloud.langfuse.com")

    assert llm_gateway.configure_langfuse(Settings()) is True

    import litellm

    assert "langfuse" in litellm.success_callback
    assert "langfuse" in litellm.failure_callback
    assert os.environ["LANGFUSE_PUBLIC_KEY"] == "pk-lf-test"
    assert os.environ["LANGFUSE_HOST"] == "https://us.cloud.langfuse.com"

    # Idempotent: a second call is a no-op that still reports configured.
    assert llm_gateway.configure_langfuse(Settings()) is True
