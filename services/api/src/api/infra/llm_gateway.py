"""LLMGateway implementation: in-memory echo (MVP).

The real LiteLLM-backed gateway lands in CV5.E1. This deterministic echo
satisfies the contract and lets earlier code be written and tested against the
seam without a model vendor.
"""

from __future__ import annotations

from api.contracts.llm_gateway import LLMMessage, LLMResponse

ECHO_MODEL = "echo-dev"


class EchoLLMGateway:
    """Deterministic gateway that echoes the last user message."""

    def complete(
        self,
        *,
        messages: list[LLMMessage],
        model: str | None = None,
        temperature: float = 0.0,
    ) -> LLMResponse:
        prompt = " ".join(message.content for message in messages)
        last_user = next(
            (m.content for m in reversed(messages) if m.role == "user"),
            "",
        )
        content = f"echo: {last_user}"
        return LLMResponse(
            content=content,
            model=model or ECHO_MODEL,
            prompt_tokens=len(prompt.split()),
            completion_tokens=len(content.split()),
        )
