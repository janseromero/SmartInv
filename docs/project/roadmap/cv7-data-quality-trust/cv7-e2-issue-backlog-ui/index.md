[< CV7 Data Quality & Trust](../index.md)

# CV7.E2 — Issue Backlog UI

**CV:** [CV7 — Data Quality & Trust](../index.md)
**Status:** ⚪ Planned
**Depends on:** CV7.E1

---

## What This Is

The Data Quality screen from the mock. DQ donut, KPI cards, the issue backlog table by category with detection method and suggested fix, and the "Start cleansing wave" action that triggers CV7.E3.

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV7.E2.S1 | Data Quality page with DQ donut and KPI cards | 📥 Backlog |
| CV7.E2.S2 | Issue backlog table grouped by category | 📥 Backlog |
| CV7.E2.S3 | "Run fix" action per category triggers a Dramatiq batch | 📥 Backlog |
| CV7.E2.S4 | DQ → confidence chart on the page proving the linkage | 📥 Backlog |
| CV7.E2.S5 | Drill-down from category to affected item list | 📥 Backlog |

---

## Done Condition

- Data Quality page renders with real per-tenant aggregates.
- Each backlog category shows count, impact, detection method, and a fix action.
- The DQ → confidence chart updates when cleansing waves complete.

---

## Out of Scope

- Data steward workflows (assignment, due dates) — Future.
- Cross-tenant DQ benchmarks — Future.

---

**See also:** [CV7](../index.md) · [CV7.E3](../cv7-e3-llm-powered-cleansing/index.md)
