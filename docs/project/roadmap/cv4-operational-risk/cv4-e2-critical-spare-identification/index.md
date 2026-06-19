[< CV4 Operational Risk Intelligence](../index.md)

# CV4.E2 — Critical Spare Identification

**CV:** [CV4 — Operational Risk Intelligence](../index.md)
**Status:** ✅ Done (rule-based; GBM classifier deferred to `critical-v2`)
**Depends on:** CV4.E1
**Design:** [ADR-029](../../../decisions.md#adr-029--operational-risk-deterministic-likelihoodxconsequence-score--rule-based-critical-spare-versioned-gnngbm-deferred)

> Rule-based `is_critical_spare` flag with a human-readable reason (criticality ≥ 4, or single-source mid-criticality at stockout risk) + a coverage-ratio metric. **The gradient-boosted classifier (S2) is deferred** and explicitly gated on a *labeled pilot dataset* — a model against synthetic data would be theatre.

---

## What This Is

A classifier flags items whose absence causes major downtime, safety, or compliance impact — even when the customer's master data doesn't explicitly mark them critical. Combines source-system criticality flags, asset relationships, failure-mode history, and consumption patterns.

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV4.E2.S1 | Rule-based classifier consuming asset criticality, item flags, and failure history | 📥 Backlog |
| CV4.E2.S2 | Gradient-boosted classifier for items without explicit criticality flags | 📥 Backlog |
| CV4.E2.S3 | Critical spare KPI surfaced on the Executive Overview | 📥 Backlog |
| CV4.E2.S4 | Critical-spare-coverage ratio metric (percentage of critical spares with safe stock) | 📥 Backlog |
| CV4.E2.S5 | Critical-spare list view with filters and explanations | 📥 Backlog |

---

## Done Condition

- Every item carries a `is_critical_spare` flag with the reason (rule fired or model probability).
- The coverage ratio is computed nightly and trended.
- Planners can audit *why* an item was flagged critical.

---

## Out of Scope

- Asset-graph reasoning — **CV14.E2**.
- Multi-agent critical-spare review — **CV11**.

---

**See also:** [CV4](../index.md) · [CV4.E1](../cv4-e1-risk-scoring/index.md)
