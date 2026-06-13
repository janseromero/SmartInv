[< CV7 Data Quality & Trust](../index.md)

# CV7.E1 — DQ Scoring

**CV:** [CV7 — Data Quality & Trust](../index.md)
**Status:** ⚪ Planned
**Prerequisite for:** CV7.E2, CV7.E4

---

## What This Is

The in-product complement to CV0.E1's pilot methodology. Continuous, deterministic DQ scoring per item across 10 dimensions. Persisted on `inventory.items.dq_score` and refreshed on every source-side update.

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV7.E1.S1 | Reuse the 10-dimension DQ definitions from CV0.E1 inside `services/api` | 📥 Backlog |
| CV7.E1.S2 | Per-item DQ score computation with deterministic formula | 📥 Backlog |
| CV7.E1.S3 | Score persisted on `inventory.items` with `dq_score_version` | 📥 Backlog |
| CV7.E1.S4 | Recompute job triggered on item updates (via Dramatiq) | 📥 Backlog |
| CV7.E1.S5 | DQ score breakdown (per dimension) exposed via API | 📥 Backlog |
| CV7.E1.S6 | Aggregate KPIs: tenant-wide DQ, items below threshold, lead-time completeness | 📥 Backlog |

---

## Done Condition

- Every item carries a DQ score, version, and per-dimension breakdown.
- Recompute is incremental — only changed items rescored.
- KPIs match the methodology defined in CV0.E1.

---

## Out of Scope

- LLM-driven cleansing — **CV7.E3**.
- DQ → confidence linkage — **CV7.E4**.
- Pilot-time assessment tooling — **CV0.E2**.

---

**See also:** [CV7](../index.md) · [CV0.E1](../../cv0-pilot-dq-assessment/cv0-e1-dq-assessment-methodology/index.md) · [CV7.E4](../cv7-e4-dq-confidence-linkage/index.md)
