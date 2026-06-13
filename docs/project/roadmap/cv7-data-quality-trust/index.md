[< Roadmap](../index.md)

# CV7 — Data Quality & Trust

**Status:** ⚪ Planned
**Goal:** SmartInv tells the user — continuously and honestly — *whether the data is good enough to trust the recommendations*. When it isn't, the system surfaces the limit, scopes the cleansing, and quantifies the lift in confidence the cleansing buys.

---

## What This Is

Trust is the moat ([Engineering Principles · P1](../../../process/engineering-principles.md#p1--trust-is-the-moat)). CV7 makes trust *visible* — the screen that proves SmartInv knows its own limits. The promise:

> *"For every item, you see a DQ score. For every recommendation, you see whether its confidence is constrained by data quality. For every DQ issue, you see what fix is available, what effort it costs, and what confidence lift it would buy."*

CV7 is the in-product complement to CV0 (Pilot DQ Assessment). CV0 happens once before pilot; CV7 happens continuously inside the product.

---

## Epics

| Code | Epic | User-visible outcome | Status |
|------|------|----------------------|--------|
| CV7.E1 | DQ Scoring | Deterministic DQ score per item across 10 dimensions (MPN, UoM, description, commodity code, asset link, etc.) | ⚪ Planned |
| CV7.E2 | Issue Backlog UI | Planner / data steward sees DQ donut, KPIs, and the issue backlog with detection method and suggested fix per category | ⚪ Planned |
| CV7.E3 | LLM-Powered Cleansing | Constrained-generation LLM extraction for missing MPNs, UoM normalization, and item description rewriting (high-confidence outputs only) | ⚪ Planned |
| CV7.E4 | DQ → Confidence Linkage | Recommendations carry a DQ warning when the underlying item's DQ < threshold; confidence is explicitly reduced | ⚪ Planned |

---

## Done Condition

CV7 is done when:

- Every item has a DQ score refreshed on a defined cadence.
- The Data Quality page renders the DQ donut, KPIs (items below threshold, lead-time completeness, asset–spare link coverage), and the issue backlog by category.
- A "Start cleansing wave" action triggers a Dramatiq batch that applies LLM extraction at ≥ 0.9 confidence threshold and queues lower-confidence proposals for human review.
- Every recommendation produced by CV3 or CV4 displays a DQ chip when the source data is below the trust threshold.
- The measured impact of DQ on recommendation confidence is reported as a panel on the Data Quality page (the "DQ → confidence" chart).
- An eval suite covers the LLM extraction prompts ([ADR-014](../../decisions.md#adr-014--eval-driven-development-for-ai-features)).

---

## Sequencing

```text
E1 (DQ scoring)
  ├── E2 (issue backlog UI)
  ├── E3 (LLM-powered cleansing)
  └── E4 (DQ → confidence linkage)
```

E1 is the spine. E2, E3, E4 can be worked in parallel once scoring is stable.

---

## Out of Scope

- One-time pre-pilot DQ assessment — **CV0**.
- Multi-tenant DQ benchmarking — Phase 2.
- Source-system master-data write-back of cleansing fixes — out of MVP scope.
- Real-time DQ event triggers — **CV13 (Event Backbone)**.

---

**See also:** [Roadmap](../index.md) · [CV0 Pilot DQ Assessment](../cv0-pilot-dq-assessment/index.md) · [CV2 Inventory Health](../cv2-inventory-health/index.md) · [CV3 Explainable Recommendations](../cv3-explainable-recommendations/index.md) · [Engineering Principles · P1 Trust is the moat](../../../process/engineering-principles.md#p1--trust-is-the-moat)
