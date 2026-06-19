[< Roadmap](../index.md)

# CV4 — Operational Risk Intelligence

**Status:** 🟢 In Progress · E1–E4 delivered deterministically (`risk-v1`); GNN/GBM deferred per [ADR-029](../decisions.md#adr-029--operational-risk-deterministic-likelihoodxconsequence-score--rule-based-critical-spare-versioned-gnngbm-deferred)
**Goal:** A maintenance manager sees, in dollar terms, where missing parts hurt — by plant, by asset, by supplier — and triggers mitigations that preserve uptime without compromising the capital story.

---

## What This Is

CV4 is the third MVP killer capability ([AGENTS.md MVP scope](../../../../AGENTS.md#mvp-scope--build-this-defer-that) item 3). Where CV3 optimizes for cost, CV4 optimizes for **operational risk** — the lens that makes industrial customers different from retail. The promise:

> *"You can see, in one screen, which of your critical spares are at risk of stockout, how much downtime exposure that represents in dollars, where supplier concentration creates single-source risk, and which mitigations preserve uptime cheapest."*

Risk is computed deterministically at MVP (item criticality × asset criticality × lead-time volatility × consumption probability × supplier reliability × financial impact). The graph-based GNN variant is **deferred to CV14**.

---

## Epics

| Code | Epic | User-visible outcome | Status |
|------|------|----------------------|--------|
| [CV4.E1](cv4-e1-risk-scoring/index.md) | Risk Scoring (Deterministic) | 0–100 likelihood×consequence risk score per item (criticality, stockout cover, lead time, supplier reliability) + $ downtime exposure, versioned | ✅ Done |
| [CV4.E2](cv4-e2-critical-spare-identification/index.md) | Critical Spare Identification | Rule-based `is_critical_spare` flag with reason + coverage ratio (GBM classifier deferred) | ✅ Done |
| [CV4.E3](cv4-e3-risk-dashboard-ui/index.md) | Risk Dashboard UI | `/risk` screen: KPI cards, plant×risk heatmap, top critical-spare exposures table, drill-down | ✅ Done |
| [CV4.E4](cv4-e4-mitigation-workflows/index.md) | Mitigation Workflows | "Mitigate" stages a `risk_mitigation` envelope (via CV3 policy) to the approval seam; grounded narrative | ✅ Done |

---

## Done Condition

CV4 is done when:

- A risk score is computed for every item in the active tenant and refreshed on a defined cadence.
- The Risk & Criticality page renders all KPIs, the plant × dimension heatmap, and the top critical-spare exposures table.
- Each item row shows downtime exposure in dollars and a single-source flag where applicable.
- Clicking "Mitigate" on a high-risk item produces a candidate mitigation envelope (via CV3) that is routed to approval (via CV6).
- The risk-narrative card on the dashboard is grounded in governed metrics (per CV5's grounding pattern).

---

## Sequencing

```text
E1 (risk scoring)
  └── E2 (critical spare identification)
        └── E3 (risk dashboard UI)
              └── E4 (mitigation workflows)
```

Linear chain. Risk score is the prerequisite for everything else.

---

## Out of Scope

- Graph-based risk (asset graph + GNN) — **CV14 (Advanced ML)**.
- Multi-agent risk reasoning — **CV11 (Multi-Agent Orchestration)**.
- Obsolescence catalog management — adjacent, surfaced as a KPI only at MVP.
- Insurance / safety stock for regulatory compliance — out of MVP scope.

---

**See also:** [Roadmap](../index.md) · [CV2 Inventory Health](../cv2-inventory-health/index.md) · [CV3 Explainable Recommendations](../cv3-explainable-recommendations/index.md) · [CV6 Workflow & Approval](../cv6-workflow-approval/index.md) · [CV14 Advanced ML](../cv14-advanced-ml/index.md)
