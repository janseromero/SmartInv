[< CV2 Inventory Health](../index.md)

# CV2.E1 — Maximo Source Connector

**CV:** [CV2 — Inventory Health & Visibility](../index.md)
**Status:** 🟢 In Progress — ingestion pipeline + fixtures delivered; real Maximo connector pending
**Prerequisite for:** CV2.E2, CV2.E3, CV2.E4, CV2.E5

---

## What This Is

The first source-system integration. IBM Maximo is the strongest customer wedge ([ADR-013](../../../decisions.md#adr-013--one-source-system-integrated-end-to-end-first)). This epic builds the connector contract that future sources (SAP, Oracle) will follow.

The connector reads from Maximo via MIF / Object Structures / REST. It writes only via the Workflow & Approval Service ([CV6](../../cv6-workflow-approval/index.md)) — never directly.

**Built data-first with fixtures (Option B, [ADR-024](../../../decisions.md#adr-024--source-ingestion-connector-seam-fixtures-first-secret-manager-credentials)):** the source-agnostic ingestion pipeline (`api/ingestion`) — `SourceConnector` seam, idempotent upserts, per-record failure isolation, `sources.sync_runs` tracking — plus a deliberately-messy `FixtureConnector` ship now, so CV2.E2–E5 build on realistic data immediately. The real `MaximoConnector` implements the same seam next; credentials live in the secret manager (Pattern A), never a DB form.

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV2.E1.S1 | Source-agnostic ingestion: `SourceConnector` seam + idempotent upserts + FK resolution | ✅ Done |
| CV2.E1.S2 | Items upsert into `inventory.items` (idempotent by source ID) | ✅ Done (via fixtures) |
| CV2.E1.S3 | Balances upsert into `inventory.balances` | ✅ Done (via fixtures) |
| CV2.E1.S4 | Transactions upsert into `inventory.transactions` | ✅ Done (via fixtures) |
| CV2.E1.S5 | Assets, locations, suppliers upsert | ✅ Done (via fixtures) |
| CV2.E1.S6 | Work orders / purchase orders upsert | ⏸ Deferred (pipeline supports it; added when CV4/CV9 need them) |
| CV2.E1.S7 | Connector status on the Admin & Governance screen (`GET /admin/connectors`) | ✅ Done |
| CV2.E1.S8 | Scheduled nightly sync via Dramatiq cron | ⏸ Deferred (no worker yet); manual `make sync-fixtures` / `POST /admin/connectors/sync` for now |
| CV2.E1.S9 | Failure isolation: a bad record lands in `sources.error_log`; the rest commit | ✅ Done |
| CV2.E1.S10 | **Real `MaximoConnector`** (REST/MIF client + field mapping) against `maxeamlabs` | 📥 Backlog |

---

## Done Condition

**Delivered now (fixtures path):**
- ✅ Re-running the sync is idempotent (no duplicates, no orphans) — verified by integration test.
- ✅ Connector health and per-entity run counts are queryable (`/admin/connectors`).
- ✅ Source IDs are preserved on every row for traceability.
- ✅ ≥ 1,000 items + balances + transactions are queryable in Postgres (`make sync-fixtures` loads 1,050 items / 3,843 transactions).
- ✅ Failure isolation: a bad record is logged and the rest commit.

**Remaining (closes the epic):**
- ⏳ A **real Maximo tenant** syncs end-to-end through the same pipeline (CV2.E1.S10) — needs authenticated access to `maxeamlabs`.
- ⏳ Scheduled nightly sync (Dramatiq).

---

## Out of Scope

- SAP / Oracle / Infor connectors — Phase 2 (reuse this pattern).
- Streaming / CDC ingestion — **CV13 (Event Backbone)**.
- Source-system write-back — **CV6.E4 (Source-System Write Dispatch)**.

---

**See also:** [CV2](../index.md) · [CV2.E2](../cv2-e2-catalog-balances-views/index.md) · [ADR-013](../../../decisions.md#adr-013--one-source-system-integrated-end-to-end-first)
