[< CV2 Inventory Health](../index.md)

# CV2.E3 — Health Scoring Engine

**CV:** [CV2 — Inventory Health & Visibility](../index.md)
**Status:** ✅ Done (nightly Dramatiq schedule deferred)
**Depends on:** CV2.E2

---

## What This Is

A deterministic 0–100 health score per item, combining excess, slow-moving, obsolete, stockout risk, and data-quality flags. Deterministic (model-deterministic per [Engineering Principles · T1](../../../../process/engineering-principles.md#t1--three-test-pyramids-not-one)) — same inputs and same scoring version always produce the same score. Design + weights in [ADR-025](../../../decisions.md#adr-025--health-scoring-deterministic-weighted-penalty-engine-versioned).

**Obsolete = dead stock = disposal candidate** (`on_hand > 0`, no usage in 24 months) is defined here and drives the Dead-stock KPI (value + disposal-candidate count) the UI shows.

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV2.E3.S1 | Health-score formula + per-dimension weights (ADR-025) | ✅ Done |
| CV2.E3.S2 | Pure Python scoring function with full unit tests (10) | ✅ Done |
| CV2.E3.S3 | Recompute persisted on `inventory.items` (`make score` / `POST /admin/score`; **nightly Dramatiq deferred**) | ✅ Done (on-demand) |
| CV2.E3.S4 | Score + badges + per-dimension breakdown via API; Health filter, badges, drawer breakdown in UI | ✅ Done |
| CV2.E3.S5 | Score versioned in `ml.model_registry` for reproducibility | ✅ Done |
| CV2.E3.S6 | Portfolio health distribution bar + Dead-stock KPI on the page | ✅ Done |

---

## Done Condition

- ✅ Every scored item carries `health_score`, `health_class`, `score_version`, and a `score_dimensions` breakdown.
- ✅ The engine is pure + deterministic — same inputs + version reproduce the score; the version is registered in `ml.model_registry`.
- ✅ The portfolio bar renders Healthy / Excess-slow / Obsolete-risk / DQ-risk percentages; the Dead-stock KPI shows value + disposal-candidate count.
- ✅ Unit tests cover edge cases (zero history, never-moved stock, missing fields, retired status, clamping).

## How to try it

```bash
make migrate && make seed && make sync-fixtures && make score
# Inventory Health page now shows scores, badges, the health bar, Dead-stock KPI, and a Health filter.
```

---

## Out of Scope

- LLM-driven scoring — explicitly forbidden ([AGENTS.md non-negotiable #3](../../../../AGENTS.md#architectural-non-negotiables)).
- Risk score (operational impact) — **CV4.E1**.
- DQ score — **CV7.E1**.

---

**See also:** [CV2](../index.md) · [CV4.E1](../../cv4-operational-risk/cv4-e1-risk-scoring/index.md) · [CV7.E1](../../cv7-data-quality-trust/cv7-e1-dq-scoring/index.md)
