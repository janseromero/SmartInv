[< CV2 Inventory Health](../index.md)

# CV2.E1 — Maximo Source Connector

**CV:** [CV2 — Inventory Health & Visibility](../index.md)
**Status:** ⚪ Planned
**Prerequisite for:** CV2.E2, CV2.E3, CV2.E4, CV2.E5

---

## What This Is

The first source-system integration. IBM Maximo is the strongest customer wedge ([ADR-013](../../../decisions.md#adr-013--one-source-system-integrated-end-to-end-first)). This epic builds the connector contract that future sources (SAP, Oracle) will follow.

The connector reads from Maximo via MIF / Object Structures / REST. It writes only via the Workflow & Approval Service ([CV6](../../cv6-workflow-approval/index.md)) — never directly.

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV2.E1.S1 | Maximo REST/MIF client with auth, paging, retries, and structured logging | 📥 Backlog |
| CV2.E1.S2 | Pull `MXITEM` master into `inventory.items` (idempotent by source ID) | 📥 Backlog |
| CV2.E1.S3 | Pull inventory balances into `inventory.balances` | 📥 Backlog |
| CV2.E1.S4 | Pull inventory transactions (24 months) into `inventory.transactions` | 📥 Backlog |
| CV2.E1.S5 | Pull assets and locations into `inventory.assets` and `inventory.locations` | 📥 Backlog |
| CV2.E1.S6 | Pull work orders into `inventory.work_orders` | 📥 Backlog |
| CV2.E1.S7 | Connector status surfaced on `/admin/connectors` page | 📥 Backlog |
| CV2.E1.S8 | Scheduled nightly sync via Dramatiq cron task | 📥 Backlog |
| CV2.E1.S9 | Failure isolation: a failing entity does not block others; errors land in `sources.error_log` | 📥 Backlog |

---

## Done Condition

- A real Maximo tenant syncs end-to-end into the eight target tables.
- Re-running the sync is idempotent (no duplicates, no orphans).
- Connector health and last-sync timestamps are queryable.
- Source IDs are preserved on every row for traceability back to Maximo.

---

## Out of Scope

- SAP / Oracle / Infor connectors — Phase 2 (reuse this pattern).
- Streaming / CDC ingestion — **CV13 (Event Backbone)**.
- Source-system write-back — **CV6.E4 (Source-System Write Dispatch)**.

---

**See also:** [CV2](../index.md) · [CV2.E2](../cv2-e2-catalog-balances-views/index.md) · [ADR-013](../../../decisions.md#adr-013--one-source-system-integrated-end-to-end-first)
