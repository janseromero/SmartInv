"""``LLMGateway`` contract — the single entry point to language models.

MVP ships an in-memory echo implementation only; the real LiteLLM-backed
implementation lands in CV5.E1 (the gateway's first real consumer). Defined now
so any earlier code depends on the seam, not on a vendor.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class LLMMessage:
    """A single chat message."""

    role: str  # 'system' | 'user' | 'assistant'
    content: str


@dataclass(frozen=True)
class LLMResponse:
    """A model completion with usage accounting (A7 — cost is a property)."""

    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int


@runtime_checkable
class LLMGateway(Protocol):
    """Vendor-agnostic LLM completion."""

    def complete(
        self,
        *,
        messages: list[LLMMessage],
        model: str | None = None,
        temperature: float = 0.0,
    ) -> LLMResponse:
        """Return a completion for ``messages``."""
        ...
