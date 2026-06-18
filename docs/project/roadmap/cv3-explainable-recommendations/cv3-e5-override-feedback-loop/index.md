[< CV3 Explainable Recommendations](../index.md)

# CV3.E5 — Override & Feedback Loop

**CV:** [CV3 — Explainable Inventory Recommendations](../index.md)
**Status:** ✅ Done (eval-suite gating deferred)
**Depends on:** CV3.E4
**Design:** [ADR-028](../../../decisions.md#adr-028--explainable-recommendations-deterministic-crostontsb-forecast--closed-form-optimization-versioned-lightgbmpyomo-deferred)

> Overrides are captured in `ml.recommendation_feedback` with a typed reason taxonomy; repeated overrides on the same item axis accumulate into an `ml.regime_signals` record; an acceptance-rate-per-model endpoint feeds the dashboard. Feeding overrides into the eval suite that gates deployments (S5) is deferred until the eval harness exists.

---

## What This Is

The feedback loop that makes SmartInv learn from real planners. Every override is captured with a structured reason, routed to the model-improvement backlog, and surfaced as a regime-change signal when patterns appear. This is the data engine behind continuous quality, *not* an autonomous learning loop.

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV3.E5.S1 | Override modal with structured reason taxonomy (asset retirement, strategy shift, supply change, other) | 📥 Backlog |
| CV3.E5.S2 | Persist overrides linked to the originating envelope and recommendation | 📥 Backlog |
| CV3.E5.S3 | Recurring overrides on the same item × dimension produce a regime-change signal | 📥 Backlog |
| CV3.E5.S4 | Acceptance rate dashboard per model / per agent | 📥 Backlog |
| CV3.E5.S5 | Overrides feed the eval suite that gates future model deployments | 📥 Backlog |

---

## Done Condition

- Every override is captured with a typed reason and an envelope reference.
- Recurring rejections on the same axis trigger a regime-change record.
- The acceptance-rate dashboard is queryable per model version.
- Overrides flow into the model-improvement backlog as structured tickets.

---

## Out of Scope

- Autonomous retraining loops — Future.
- Reinforcement learning from feedback — **CV14.E3**.
- Cross-tenant feedback aggregation — Future (privacy).

---

**See also:** [CV3](../index.md) · [CV3.E4](../cv3-e4-recommendations-ui/index.md) · [Engineering Principles · A8](../../../../process/engineering-principles.md#a8--eval-suites-are-part-of-the-product)
