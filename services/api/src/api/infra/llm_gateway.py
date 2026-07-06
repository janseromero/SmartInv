"""``LLMGateway`` implementations.

:class:`EchoLLMGateway` is a deterministic test double (no vendor). The
:class:`LiteLLMGateway` is the real CV5.E1 gateway: the LiteLLM Python SDK
in-process (ADR-032), vendor-agnostic via ``settings.llm_model``. ``litellm`` is
imported lazily so tests and non-LLM code paths never load it.
"""

from __future__ import annotations

from api.config import Settings, get_settings
from api.contracts.llm_gateway import LLMMessage, LLMResponse

ECHO_MODEL = "echo-dev"


class LLMNotConfiguredError(RuntimeError):
    """Raised when the real LLM gateway is used without an API key."""


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


class LiteLLMGateway:
    """Vendor-agnostic gateway backed by the LiteLLM Python SDK (ADR-032).

    Model choice is config (``llm_model``); switching vendor (e.g. to
    ``claude-3-5-haiku``) is a settings change, not a code change.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    @property
    def configured(self) -> bool:
        return bool(self._settings.openai_api_key)

    def complete(
        self,
        *,
        messages: list[LLMMessage],
        model: str | None = None,
        temperature: float = 0.0,
    ) -> LLMResponse:
        if not self.configured:
            raise LLMNotConfiguredError(
                "OPENAI_API_KEY is not set — the conversational analyst is unconfigured."
            )
        import litellm  # lazy: keeps the heavy dep off non-LLM code paths

        response = litellm.completion(
            model=model or self._settings.llm_model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
            api_key=self._settings.openai_api_key,
        )
        choice = response.choices[0].message.content or ""
        usage = getattr(response, "usage", None)
        return LLMResponse(
            content=choice,
            model=getattr(response, "model", model or self._settings.llm_model),
            prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
            completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
        )
