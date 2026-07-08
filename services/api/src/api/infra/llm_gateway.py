"""``LLMGateway`` implementations.

:class:`EchoLLMGateway` is a deterministic test double (no vendor). The
:class:`LiteLLMGateway` is the real CV5.E1 gateway: the LiteLLM Python SDK
in-process (ADR-032), vendor-agnostic via ``settings.llm_model``. ``litellm`` is
imported lazily so tests and non-LLM code paths never load it.
"""

from __future__ import annotations

import os

from api.config import Settings, get_settings
from api.contracts.llm_gateway import LLMMessage, LLMResponse

ECHO_MODEL = "echo-dev"

# Registered once per process; LiteLLM callbacks are global.
_langfuse_configured = False


class LLMNotConfiguredError(RuntimeError):
    """Raised when the real LLM gateway is used without an API key."""


def configure_langfuse(settings: Settings) -> bool:
    """Register LiteLLM's Langfuse callbacks once, when keys are present (S7).

    Observability only: enabling this never changes answers or the fail-closed
    grounding guarantee (that lives in code, not Langfuse). Returns whether
    tracing is active. No-op (and returns False) when keys are unset, so CI and
    local runs without keys behave exactly as before.
    """
    global _langfuse_configured
    if _langfuse_configured:
        return True
    if not (settings.langfuse_public_key and settings.langfuse_secret_key):
        return False

    import litellm

    # The Langfuse SDK reads these from the environment; mirror the settings.
    os.environ["LANGFUSE_PUBLIC_KEY"] = settings.langfuse_public_key
    os.environ["LANGFUSE_SECRET_KEY"] = settings.langfuse_secret_key
    os.environ["LANGFUSE_HOST"] = settings.langfuse_base_url
    if "langfuse" not in litellm.success_callback:
        litellm.success_callback = [*litellm.success_callback, "langfuse"]
    if "langfuse" not in litellm.failure_callback:
        litellm.failure_callback = [*litellm.failure_callback, "langfuse"]
    _langfuse_configured = True
    return True


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

        # Trace to Langfuse when configured (S7); harmless no-op otherwise.
        traced = configure_langfuse(self._settings)
        metadata = {"trace_name": "ask-smartinv", "tags": ["ask-smartinv"]} if traced else {}

        response = litellm.completion(
            model=model or self._settings.llm_model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
            api_key=self._settings.openai_api_key,
            metadata=metadata,
        )
        choice = response.choices[0].message.content or ""
        usage = getattr(response, "usage", None)
        return LLMResponse(
            content=choice,
            model=getattr(response, "model", model or self._settings.llm_model),
            prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
            completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
        )
