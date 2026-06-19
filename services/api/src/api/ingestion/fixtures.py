"""Deliberately-messy synthetic source data (CV2.E1, Option B / ADR-024).

A ``SourceConnector`` that generates Maximo-shaped data with realistic mess —
missing descriptions, duplicate descriptions, null costs, odd UOMs, excess and
stockout balances, obsolete items with no movement, plus seeded anomalies
(recent consumption spikes, unit-price jumps, negative available balances) — so
the catalog, scoring, dedup, and anomaly epics are built and tested against
real-world conditions before the live Maximo connector lands.
"""

from __future__ import annotations

import random
from collections.abc import Iterator, Sequence
from datetime import UTC, datetime, timedelta

from api.ingestion.connector import Entity, SourceRecord

_LOCATIONS = [
    ("LOC-CENTRAL", "Central Storeroom", "storeroom"),
    ("LOC-PLANT-A", "Plant A Storeroom", "storeroom"),
    ("LOC-PLANT-B", "Plant B Storeroom", "storeroom"),
    ("LOC-FIELD", "Field Warehouse", "warehouse"),
]
_UOMS = ["EA", "BOX", "M", "KG", "L", "ea", "pcs"]  # mixed case / inconsistent on purpose
_ITEM_TYPES = ["SPARE", "CONSUMABLE", "TOOL", "LUBRICANT"]
_DESCRIPTIONS = [
    "Ball bearing 6204 2RS",
    "Hydraulic pump seal kit",
    "V-belt A-section",
    "Gasket set cylinder head",
    "Electric motor 5HP 3PH",
    "Pressure gauge 0-10 bar",
    "Solenoid valve 24VDC",
    "O-ring viton 50mm",
    "Grease cartridge EP2",
    "Air filter element",
]


def _batched(records: list[SourceRecord], size: int = 500) -> Iterator[Sequence[SourceRecord]]:
    for start in range(0, len(records), size):
        yield records[start : start + size]


class FixtureConnector:
    """Generates a stable, messy inventory dataset for one source system."""

    source_system = "fixture"

    def __init__(self, *, item_count: int = 1050, seed: int = 42) -> None:
        self._rng = random.Random(seed)  # noqa: S311 — synthetic fixtures, not crypto
        self._item_count = item_count
        self._locations = self._build_locations()
        self._suppliers = self._build_suppliers()
        self._items = self._build_items()
        self._assets = self._build_assets()
        self._balances = self._build_balances()
        self._transactions = self._build_transactions()

    # --- generation ------------------------------------------------------

    def _build_locations(self) -> list[SourceRecord]:
        return [
            SourceRecord(code, {"location_code": code, "name": name, "type": kind})
            for code, name, kind in _LOCATIONS
        ]

    def _build_suppliers(self) -> list[SourceRecord]:
        return [
            SourceRecord(
                f"SUP-{i:03d}",
                {
                    "supplier_code": f"SUP-{i:03d}",
                    "name": f"Supplier {i}",
                    "status": "active",
                    # Delivery reliability — a few unreliable suppliers seed
                    # single-source risk (CV4.E1).
                    "on_time_rate": round(self._rng.uniform(0.6, 0.99), 4),
                },
            )
            for i in range(1, 11)
        ]

    def _build_items(self) -> list[SourceRecord]:
        items: list[SourceRecord] = []
        for i in range(self._item_count):
            roll = self._rng.random()
            description: str | None = self._rng.choice(_DESCRIPTIONS)
            if roll < 0.06:
                description = None  # missing description
            elif roll < 0.09:
                description = _DESCRIPTIONS[0]  # duplicate description (dedup fodder)
            unit_cost: float | None = round(self._rng.uniform(2, 1800), 2)
            if self._rng.random() < 0.05:
                unit_cost = None  # missing cost
            source_id = f"ITEM-{1000 + i}"
            items.append(
                SourceRecord(
                    source_id,
                    {
                        "item_number": source_id,
                        "description": description,
                        "uom": self._rng.choice(_UOMS),
                        "item_type": self._rng.choice(_ITEM_TYPES),
                        "status": "ACTIVE",
                        "unit_cost": unit_cost,
                        "lead_time_days": self._rng.choice([7, 14, 21, 30, 45, 60, 90]),
                        # Criticality skews low; a minority are high-impact spares (CV4).
                        "criticality": self._rng.choices(
                            [1, 2, 3, 4, 5], weights=[15, 30, 30, 18, 7]
                        )[0],
                        "primary_supplier_source_id": f"SUP-{self._rng.randint(1, 10):03d}",
                    },
                )
            )
        return items

    def _build_assets(self) -> list[SourceRecord]:
        return [
            SourceRecord(
                f"AST-{i:03d}",
                {
                    "asset_number": f"AST-{i:03d}",
                    "description": f"Asset {i}",
                    "criticality": self._rng.randint(1, 5),
                    "status": "OPERATING",
                    "location_source_id": self._rng.choice(self._locations).source_id,
                },
            )
            for i in range(1, 51)
        ]

    def _build_balances(self) -> list[SourceRecord]:
        now = datetime.now(UTC)
        balances: list[SourceRecord] = []
        for index, item in enumerate(self._items):
            location = self._rng.choice(self._locations)
            min_level = self._rng.choice([0, 2, 5, 10])
            max_level = min_level + self._rng.choice([10, 25, 50, 100])
            roll = self._rng.random()
            if roll < 0.1:
                on_hand = 0.0  # stockout
            elif roll < 0.25:
                on_hand = float(max_level * self._rng.randint(3, 8))  # excess
            else:
                on_hand = float(self._rng.randint(min_level, max_level))
            # ~3% reservation-integrity breaks: reserved exceeds on-hand, so
            # available goes negative (CV2.E5.S3 anomaly fodder).
            reserved = 0.0
            available = on_hand
            if index % 31 == 3:
                reserved = on_hand + float(self._rng.randint(5, 50))
                available = on_hand - reserved
            balances.append(
                SourceRecord(
                    f"{item.source_id}@{location.source_id}",
                    {
                        "item_source_id": item.source_id,
                        "location_source_id": location.source_id,
                        "on_hand": on_hand,
                        "available": available,
                        "reserved": reserved,
                        "min_level": float(min_level),
                        "max_level": float(max_level),
                        "as_of": now,
                    },
                )
            )
        return balances

    def _build_transactions(self) -> list[SourceRecord]:
        now = datetime.now(UTC)
        txns: list[SourceRecord] = []
        seq = 0
        for index, item in enumerate(self._items):
            base_cost = item.data.get("unit_cost")
            # Each item has a characteristic usage rate so normal variation is
            # tight and a genuine spike stands out (robust-z stays clean).
            base_qty = self._rng.randint(2, 50)
            is_spike = index % 19 == 5  # ~5% consumption-spike items
            is_price = index % 19 == 11 and base_cost is not None  # ~5% price-jump items
            forced = is_spike or is_price
            # ~20% of items have no movement (obsolete) — anomaly items always move.
            if not forced and self._rng.random() < 0.2:
                continue
            location_id = self._balance_location(item.source_id)
            count = self._rng.randint(1, 8)
            if forced:
                count = max(count, 6)  # guarantee a baseline (MIN_HISTORY = 5)
            for _ in range(count):
                seq += 1
                days_ago = self._rng.randint(0, 720)
                quantity = max(1.0, round(base_qty * self._rng.uniform(0.6, 1.4)))
                txns.append(
                    SourceRecord(
                        f"TXN-{seq}",
                        {
                            "item_source_id": item.source_id,
                            "location_source_id": location_id,
                            "type": "issue",
                            "quantity": float(quantity),
                            "unit_cost": self._priced(base_cost),
                            "txn_date": now - timedelta(days=days_ago),
                        },
                    )
                )
            # Inject a recent (last 7 days) anomalous issue for the cohort items.
            if is_spike:
                seq += 1
                txns.append(
                    self._issue(
                        seq,
                        item.source_id,
                        location_id,
                        quantity=float(base_qty * self._rng.randint(8, 15)),
                        unit_cost=self._priced(base_cost),
                        when=now - timedelta(days=self._rng.randint(0, 6)),
                    )
                )
            if is_price and base_cost is not None:
                seq += 1
                txns.append(
                    self._issue(
                        seq,
                        item.source_id,
                        location_id,
                        quantity=float(max(1, round(base_qty * self._rng.uniform(0.6, 1.4)))),
                        unit_cost=round(base_cost * self._rng.uniform(3.0, 6.0), 2),
                        when=now - timedelta(days=self._rng.randint(0, 6)),
                    )
                )
        return txns

    def _priced(self, base_cost: float | None) -> float | None:
        """A unit price near the item's baseline (±5%) — the normal price series."""
        if base_cost is None:
            return None
        return round(base_cost * self._rng.uniform(0.95, 1.05), 2)

    def _issue(
        self,
        seq: int,
        item_source_id: str,
        location_id: str,
        *,
        quantity: float,
        unit_cost: float | None,
        when: datetime,
    ) -> SourceRecord:
        return SourceRecord(
            f"TXN-{seq}",
            {
                "item_source_id": item_source_id,
                "location_source_id": location_id,
                "type": "issue",
                "quantity": quantity,
                "unit_cost": unit_cost,
                "txn_date": when,
            },
        )

    def _balance_location(self, item_source_id: str) -> str:
        for balance in self._balances:
            if balance.data["item_source_id"] == item_source_id:
                location: str = balance.data["location_source_id"]
                return location
        return self._locations[0].source_id

    # --- connector interface --------------------------------------------

    def fetch(
        self, entity: Entity, since: datetime | None = None
    ) -> Iterator[Sequence[SourceRecord]]:
        records = {
            Entity.LOCATION: self._locations,
            Entity.SUPPLIER: self._suppliers,
            Entity.ITEM: self._items,
            Entity.ASSET: self._assets,
            Entity.BALANCE: self._balances,
            Entity.TRANSACTION: self._transactions,
        }[entity]
        yield from _batched(records)
