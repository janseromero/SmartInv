"""The source-connector seam (CV2.E1 / ADR-024).

A connector yields batches of already-canonical records per entity. It owns the
mapping from its native format (Maximo OSLC, a fixture generator, …) to our
column names, so the ingestion service stays source-agnostic. The batch +
``since`` shape mirrors real pull semantics (paging, delta syncs) so a real
Maximo client drops in without reshaping the pipeline.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable


class Entity(StrEnum):
    """Entities a connector can supply, in dependency order."""

    LOCATION = "location"
    SUPPLIER = "supplier"
    ITEM = "item"
    ASSET = "asset"
    BALANCE = "balance"
    TRANSACTION = "transaction"


# Ingestion order: referenced entities before the rows that reference them.
ENTITY_ORDER: tuple[Entity, ...] = (
    Entity.LOCATION,
    Entity.SUPPLIER,
    Entity.ITEM,
    Entity.ASSET,
    Entity.BALANCE,
    Entity.TRANSACTION,
)


@dataclass(frozen=True)
class SourceRecord:
    """One source row: a stable source id plus canonical-shaped data.

    ``data`` keys are canonical column names. Foreign references use the source
    id of the referenced entity (e.g. ``item_source_id``), resolved to our UUIDs
    during upsert.
    """

    source_id: str
    data: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class SourceConnector(Protocol):
    """Pulls canonical records from a source system, one entity at a time."""

    source_system: str

    def fetch(
        self, entity: Entity, since: datetime | None = None
    ) -> Iterator[Sequence[SourceRecord]]:
        """Yield batches of records for ``entity`` (optionally changed since ``since``)."""
        ...
