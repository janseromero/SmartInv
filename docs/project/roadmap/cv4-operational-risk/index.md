[< Roadmap](../index.md)

# CV4 — Operational Risk Intelligence

**Status:** ⚪ Planned
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
| CV4.E1 | Risk Scoring (Deterministic) | Every item gets a 0–100 risk score combining criticality, lead-time, supplier reliability, and consumption probability | ⚪ Planned |
| CV4.E2 | Critical Spare Identification | Items whose absence causes major downtime/safety impact are surfaced and flagged | ⚪ Planned |
| CV4.E3 | Risk Dashboard UI | KPI cards, plant × risk dimension heatmap, top critical-spare exposures table | ⚪ Planned |
| CV4.E4 | Mitigation Workflows | "Mitigate" action on any high-risk item routes to optimization or procurement workflows | ⚪ Planned |

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
