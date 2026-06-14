"""``ObjectStore`` contract — blob storage behind a swappable seam.

MVP implementation is S3/SeaweedFS (ADR-017). Cloud stores (AWS S3, R2, GCS)
implement the same protocol without touching domain code.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


class ObjectNotFoundError(KeyError):
    """Raised by :meth:`ObjectStore.get` when a key does not exist."""


@runtime_checkable
class ObjectStore(Protocol):
    """Key/value blob storage."""

    def put(self, key: str, data: bytes, *, content_type: str | None = None) -> None:
        """Store ``data`` under ``key`` (overwrites)."""
        ...

    def get(self, key: str) -> bytes:
        """Return the bytes stored under ``key`` or raise ObjectNotFoundError."""
        ...

    def exists(self, key: str) -> bool:
        """Return whether ``key`` is present."""
        ...

    def url(self, key: str, *, expires_in: int = 3600) -> str:
        """Return a (possibly time-limited) URL for ``key``."""
        ...

    def list(self, prefix: str = "") -> list[str]:
        """Return keys under ``prefix``, sorted."""
        ...

    def delete(self, key: str) -> None:
        """Remove ``key`` if present (no error if absent)."""
        ...
