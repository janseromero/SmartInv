[< CV4 Operational Risk Intelligence](../index.md)

# CV4.E1 — Risk Scoring (Deterministic)

**CV:** [CV4 — Operational Risk Intelligence](../index.md)
**Status:** ⚪ Planned
**Prerequisite for:** CV4.E2, CV4.E3

---

## What This Is

A deterministic 0–100 risk score per item, combining item criticality, asset criticality, lead-time volatility, consumption probability, supplier reliability, and downtime impact. Reproducible, versioned, explainable. The graph-based variant is deferred to **CV14.E2 (Risk GNN)**.

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV4.E1.S1 | Define risk-score formula and component weights | 📥 Backlog |
| CV4.E1.S2 | Item criticality input from `inventory.items.criticality` (with defaults) | 📥 Backlog |
| CV4.E1.S3 | Asset criticality input via `inventory.assets` relationships | 📥 Backlog |
| CV4.E1.S4 | Lead-time volatility from PO history | 📥 Backlog |
| CV4.E1.S5 | Supplier reliability from delivery / late-PO history | 📥 Backlog |
| CV4.E1.S6 | Risk score persisted on `inventory.items.risk_score` with `risk_score_version` | 📥 Backlog |
| CV4.E1.S7 | Score breakdown per component exposed via API | 📥 Backlog |

---

## Done Condition

- Every item has a risk score with a versioned breakdown.
- The score is reproducible from a fingerprint of inputs + version.
- The score is consumed by the recommendation engine (CV3) for risk-weighting.

---

## Out of Scope

- Graph-based risk (GNN) — **CV14.E2**.
- Real-time risk recompute — **CV13 (Event Backbone)**.
- LLM risk reasoning — **CV11 (Multi-Agent Orchestration)**.

---

**See also:** [CV4](../index.md) · [CV4.E2](../cv4-e2-critical-spare-identification/index.md) · [CV14.E2](../../cv14-advanced-ml/cv14-e2-risk-gnn/index.md)
