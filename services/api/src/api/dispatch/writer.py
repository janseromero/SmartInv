"""``SourceWriter`` seam — the single gate that writes to a source system.

The MVP ships an ``EchoSourceWriter`` (deterministic, no external call) because
the real Maximo write client depends on the live ``MaximoConnector`` (CV2.E1.S10,
still backlog). Swapping in ``MaximoSourceWriter`` later changes only the
provider in :mod:`api.infra.providers` — the dispatcher is unaffected (ADR-022
seam pattern; AGENTS non-negotiable #2: writes only through this service).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


class SourceWriteError(RuntimeError):
    """Raised when a source-system write fails (retryable unless noted)."""

    def __init__(self, message: str, *, permanent: bool = False) -> None:
        super().__init__(message)
        self.permanent = permanent


@dataclass(frozen=True)
class WriteReceipt:
    """Proof a source-system write was applied."""

    external_id: str
    detail: str


@runtime_checkable
class SourceWriter(Protocol):
    """Apply an approved change to a source system, idempotently."""

    def write(
        self, *, operation: str, payload: dict[str, Any], idempotency_key: str
    ) -> WriteReceipt:
        """Apply the write and return a receipt, or raise ``SourceWriteError``."""
        ...


class EchoSourceWriter:
    """In-process fake writer: deterministic receipt, no external call.

    The external id is a stable hash of the idempotency key, so replaying the
    same write yields the same receipt — proving idempotency end-to-end without
    a live source system.
    """

    target_system = "echo"

    def write(
        self, *, operation: str, payload: dict[str, Any], idempotency_key: str
    ) -> WriteReceipt:
        digest = hashlib.sha256(idempotency_key.encode()).hexdigest()[:16]
        return WriteReceipt(
            external_id=f"echo-{operation}-{digest}",
            detail="applied by EchoSourceWriter (no live source system in MVP)",
        )
