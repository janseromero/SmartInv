[< CV2 Inventory Health](../index.md)

# CV2.E2 — Catalog & Balances Views

**CV:** [CV2 — Inventory Health & Visibility](../index.md)
**Status:** ⚪ Planned
**Depends on:** CV2.E1

---

## What This Is

The first user-visible page in SmartInv: the Inventory Health screen. Items list, filters, KPI cards, item detail drawer — all backed by real data ingested via CV2.E1.

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV2.E2.S1 | `GET /api/inventory/items` with pagination, sort, and filter parameters | 📥 Backlog |
| CV2.E2.S2 | Inventory Health page renders items table from real DB | 📥 Backlog |
| CV2.E2.S3 | Filter bar (Site, Criticality, ABC class, Health) wired to query params | 📥 Backlog |
| CV2.E2.S4 | KPI cards aggregate by site (Excess value, Dead stock, Item master completeness) | 📥 Backlog |
| CV2.E2.S5 | Item detail drawer shows balances by storeroom and recent transactions | 📥 Backlog |
| CV2.E2.S6 | Saved views — planner can save the current filter set | 📥 Backlog |

---

## Done Condition

- Planner can load a real customer's items, filter by site/criticality/health, and drill into a single item.
- All KPI numbers trace back to source records.
- The page passes the performance budget (< 2s TTI on a mid-range laptop).

---

## Out of Scope

- Health scoring computation — **CV2.E3**.
- Recommendations on items — **CV3**.
- Risk lens — **CV4**.

---

**See also:** [CV2](../index.md) · [CV2.E1](../cv2-e1-maximo-connector/index.md) · [CV2.E3](../cv2-e3-health-scoring-engine/index.md)
