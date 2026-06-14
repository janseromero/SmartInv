[< CV2 Inventory Health](../index.md)

# CV2.E2 — Catalog & Balances Views

**CV:** [CV2 — Inventory Health & Visibility](../index.md)
**Status:** ✅ Done (Health/ABC filters land with CV2.E3; saved views deferred)
**Depends on:** CV2.E1

---

## What This Is

The first user-visible data page in SmartInv: the Inventory Health screen. Items list, filters, KPI cards, item detail drawer — all backed by the data ingested via CV2.E1. This epic also brings in the **web data layer** deferred from CV1.E6: TanStack Query + a typed API client, and wires the CV1.E8 components (`KpiCard`, `Badge`) into a real screen.

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV2.E2.S1 | `GET /inventory/items` with pagination, sort, search, type, site filters (+ `/summary`, `/locations`, `/items/{id}`) | ✅ Done |
| CV2.E2.S2 | Inventory Health page renders the items table from the real DB (TanStack Query) | ✅ Done |
| CV2.E2.S3 | Filter bar wired to query params: Site, Type, search, Missing-data (**Health/ABC filters → CV2.E3**) | ✅ Done (partial: Health/ABC need scoring) |
| CV2.E2.S4 | KPI cards: Items, Inventory value, Excess value, Item-master completeness | ✅ Done |
| CV2.E2.S5 | Item detail drawer: balances by site + recent transactions | ✅ Done |
| CV2.E2.S6 | Saved views (persist filter sets) | ⏸ Deferred (low value pre-pilot; revisit) |

---

## Done Condition

- ✅ Planner can load the items catalog, filter by site/type/search/missing-data, sort, paginate, and drill into a single item (balances + recent transactions). Criticality/Health/ABC filters arrive with CV2.E3 scoring.
- ✅ All KPI numbers aggregate from source-traceable rows (`source_system`+`source_id`).
- ✅ Endpoints are tenant-scoped (RLS), role-gated, and covered by integration tests; the page is lightweight (server-rendered shell + cached queries).

## How to try it

```bash
make migrate && make seed && make sync-fixtures && make api
# pnpm --filter=@smartinv/web dev -> http://localhost:3000 -> sign in (planner) -> Inventory Health
```

---

## Out of Scope

- Health scoring computation — **CV2.E3**.
- Recommendations on items — **CV3**.
- Risk lens — **CV4**.

---

**See also:** [CV2](../index.md) · [CV2.E1](../cv2-e1-maximo-connector/index.md) · [CV2.E3](../cv2-e3-health-scoring-engine/index.md)
