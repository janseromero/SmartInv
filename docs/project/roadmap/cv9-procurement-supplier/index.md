[< Roadmap](../index.md)

# CV9 — Procurement & Supplier Intelligence

**Status:** 🔵 Future
**Goal:** Procurement teams act earlier on supplier risk, negotiate with price and lead-time evidence, and convert insight into governed requisitions.

---

## What This Is

CV9 widens the SmartInv user base from Inventory Planning into Procurement. It is **explicitly deferred** from the MVP per [AGENTS.md MVP scope](../../../../AGENTS.md#mvp-scope--build-this-defer-that) — *RFQ generation* and *price forecasting* are listed as deferred capabilities.

The promise once activated:

> *"Late-PO risk is predicted before it surfaces. Suppliers carry a scorecard you can trust. A draft RFQ comes with price history, supplier shortlist, and substitution candidates. Approved purchases dispatch through the same governance layer as inventory changes."*

---

## Epics

| Code | Epic | User-visible outcome | Status |
|------|------|----------------------|--------|
| [CV9.E1](cv9-e1-late-po-risk/index.md) | Late-PO Risk Prediction | Calibrated probability per open PO with reason codes | 🔵 Future |
| [CV9.E2](cv9-e2-supplier-scorecards/index.md) | Supplier Scorecards | Rolling 12-month scorecards with lead-time adherence, price trend, late deliveries, emergency buys | 🔵 Future |
| [CV9.E3](cv9-e3-procurement-ui/index.md) | Procurement UI | KPI cards, open-POs table with late-risk meters, supplier scorecards table | 🔵 Future |
| [CV9.E4](cv9-e4-rfq-drafting/index.md) | Constrained RFQ Drafting (LLM) | LLM drafts RFQs from governed price history and supplier registry, never inventing values | 🔵 Future |
| [CV9.E5](cv9-e5-requisition-workflow/index.md) | Requisition Workflow | "Create requisition" routed through Workflow & Approval ([CV6](../cv6-workflow-approval/index.md)) | 🔵 Future |

---

## Done Condition

When CV9 activates:

- Procurement-role users have a dedicated landing page rendering CV9.E3.
- Late-PO predictions are scored and ranked; "Expedite" routes to a procurement workflow.
- RFQ drafts are grounded in governed price history; no invented numbers, no invented suppliers ([ADR-014](../../decisions.md#adr-014--eval-driven-development-for-ai-features)).
- A new requisition enters the same approval queue used by inventory recommendations.

---

## Out of Scope

- Spot-price negotiation chatbots — Future.
- Auction / RFx platforms — Future.
- Supply-chain disruption forecasting (geopolitical, weather) — Future.

---

**See also:** [Roadmap](../index.md) · [CV6 Workflow & Approval](../cv6-workflow-approval/index.md) · [CV10 Executive Narratives](../cv10-executive-narratives/index.md)
