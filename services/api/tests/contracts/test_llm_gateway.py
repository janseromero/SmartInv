"""Contract tests for LLMGateway (in-memory echo impl)."""

from __future__ import annotations

from api.contracts.llm_gateway import LLMGateway, LLMMessage
from api.infra.llm_gateway import EchoLLMGateway


def _gateway() -> LLMGateway:
    return EchoLLMGateway()


def test_complete_returns_response_with_usage() -> None:
    gateway = _gateway()
    response = gateway.complete(
        messages=[LLMMessage(role="user", content="hello there")],
    )
    assert "hello there" in response.content
    assert response.model
    assert response.prompt_tokens > 0
    assert response.completion_tokens > 0


def test_complete_honours_requested_model() -> None:
    gateway = _gateway()
    response = gateway.complete(
        messages=[LLMMessage(role="user", content="ping")],
        model="custom-model",
    )
    assert response.model == "custom-model"


def test_implements_protocol() -> None:
    assert isinstance(_gateway(), LLMGateway)
