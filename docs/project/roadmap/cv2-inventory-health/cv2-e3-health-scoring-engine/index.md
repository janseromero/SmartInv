[< CV2 Inventory Health](../index.md)

# CV2.E3 — Health Scoring Engine

**CV:** [CV2 — Inventory Health & Visibility](../index.md)
**Status:** ⚪ Planned
**Depends on:** CV2.E2

---

## What This Is

A deterministic 0–100 health score per item, combining excess, slow-moving, obsolete, stockout risk, and data-quality flags. Deterministic (model-deterministic per [Engineering Principles · T1](../../../../process/engineering-principles.md#t1--three-test-pyramids-not-one)) — same inputs and same scoring version always produce the same score.

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV2.E3.S1 | Define health-score formula and weights (per dimension) | 📥 Backlog |
| CV2.E3.S2 | Implement scoring as a pure Python function with full unit tests | 📥 Backlog |
| CV2.E3.S3 | Nightly recompute via Dramatiq; result persisted on `inventory.items.health_score` | 📥 Backlog |
| CV2.E3.S4 | Score breakdown (per dimension) exposed via API and surfaced in UI | 📥 Backlog |
| CV2.E3.S5 | Score versioned in `ml.model_registry` for reproducibility | 📥 Backlog |
| CV2.E3.S6 | Health donut on the page summarizes the portfolio | 📥 Backlog |

---

## Done Condition

- Every item carries a health_score and a `score_version`.
- A scoring run is reproducible from a fingerprint of inputs + version.
- The portfolio health donut renders Healthy / Excess-slow / Obsolete-risk / DQ-risk percentages.
- Unit tests cover edge cases (zero history, missing fields, retired assets).

---

## Out of Scope

- LLM-driven scoring — explicitly forbidden ([AGENTS.md non-negotiable #3](../../../../AGENTS.md#architectural-non-negotiables)).
- Risk score (operational impact) — **CV4.E1**.
- DQ score — **CV7.E1**.

---

**See also:** [CV2](../index.md) · [CV4.E1](../../cv4-operational-risk/cv4-e1-risk-scoring/index.md) · [CV7.E1](../../cv7-data-quality-trust/cv7-e1-dq-scoring/index.md)
