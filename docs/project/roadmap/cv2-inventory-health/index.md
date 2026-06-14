[< Roadmap](../index.md)

# CV2 — Inventory Health & Visibility

**Status:** 🟢 In Progress · E1 ingestion (fixtures) + E2 catalog views delivered
**Goal:** A planner sees the items they own, scored for health, traceable to source-system records, with anomalies and duplicates surfaced — for one real customer integrated end-to-end.

---

## What This Is

CV2 is the first MVP killer capability ([AGENTS.md MVP scope](../../../../AGENTS.md#mvp-scope--build-this-defer-that) item 1) and the first time SmartInv produces visible value for a planner. The promise is concrete:

> *"You can see every item in your inventory, scored 0–100 for health, with the badges that matter (excess, slow-moving, obsolete, stockout risk, data quality risk), filterable by site, criticality, ABC class, and supplier — every number traceable to its source-system record."*

The hardest sub-problem is the first source connector. We pick **IBM Maximo** because it's the strongest customer wedge ([ADR-013](../../decisions.md#adr-013--one-source-system-integrated-end-to-end-first)). Other sources (SAP, Oracle) reuse the same pattern in later CVs.

---

## Epics

| Code | Epic | User-visible outcome | Status |
|------|------|----------------------|--------|
| [CV2.E1](cv2-e1-maximo-connector/index.md) | Maximo Source Connector | Source-agnostic ingestion pipeline + messy fixture data + connector status (real Maximo connector pending) | 🟢 In Progress |
| [CV2.E2](cv2-e2-catalog-balances-views/index.md) | Catalog & Balances Views | Inventory Health page: catalog, filters, KPI cards, item drawer (TanStack Query + ui-web) | ✅ Done |
| [CV2.E3](cv2-e3-health-scoring-engine/index.md) | Health Scoring Engine | Deterministic health score per item (0–100) combining excess, slow-moving, obsolete, stockout risk, and DQ flags | ⚪ Planned |
| [CV2.E4](cv2-e4-duplicate-detection/index.md) | Duplicate Detection | Embedding-based item-master deduplication queue with confidence scores | ⚪ Planned |
| [CV2.E5](cv2-e5-anomaly-detection/index.md) | Anomaly Detection | Consumption-spike and price-anomaly surface on a "last 7 days" panel | ⚪ Planned |

---

## Done Condition

CV2 is done when:

- A real Maximo tenant is integrated and items, balances, and transactions are queryable in Postgres.
- A planner can load the Inventory Health page and see ≥ 1,000 real items with health scores, badges, and filters.
- Health score is reproducible: same inputs + same scoring version → same score.
- The duplicate detection queue surfaces probable duplicates with ≥ 0.85 average pair confidence, reviewable by a planner.
- Anomaly detection flags consumption spikes and unit-price jumps within 24 hours of the source event.
- All data flowing through CV2 carries its `tenant_id` and `source_record_id` for traceability.

---

## Sequencing

```text
E1 (Maximo connector)
  └── E2 (catalog & balances UI)
        ├── E3 (health scoring engine)
        ├── E4 (duplicate detection)
        └── E5 (anomaly detection)
```

E1 unblocks everything. E2 makes the data visible. E3, E4, and E5 can be worked in parallel once data is flowing.

---

## Out of Scope

- Optimization (min/max recommendations) — **CV3**.
- Risk-driven views (downtime exposure, critical spare exposure) — **CV4**.
- LLM-powered enrichment (NLP for descriptions, MPN extraction) — **CV7 (Data Quality & Trust)**.
- Additional source connectors (SAP, Oracle, Infor) — Phase 2.
- Real-time event-driven ingestion — **CV13 (Event Backbone)**.

---

**See also:** [Roadmap](../index.md) · [CV1 Foundations](../cv1-foundations/index.md) · [CV3 Explainable Recommendations](../cv3-explainable-recommendations/index.md) · [CV7 Data Quality & Trust](../cv7-data-quality-trust/index.md) · [Decisions](../../decisions.md)
