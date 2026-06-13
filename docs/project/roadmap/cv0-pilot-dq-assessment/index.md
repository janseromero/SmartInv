[< Roadmap](../index.md)

# CV0 — Pilot Data-Quality Assessment

**Status:** ⚪ Planned
**Goal:** Decide in days — not weeks — whether a customer's MRO data is good enough for SmartInv to deliver measurable value, before any feature work for that customer begins.

---

## What This Is

Per [AGENTS.md MVP scope](../../../../AGENTS.md#mvp-scope--build-this-defer-that), Phase 0 happens *first* for every pilot. Industrial customers carry decades of inventory baggage: weak descriptions, missing manufacturer part numbers, inconsistent units of measure, broken asset-to-spare relationships, and incomplete lead times. SmartInv recommendations are only as trustworthy as the data feeding them.

CV0 builds the methodology, tooling, and reporting that let us answer one question with confidence:

> *"If we deploy SmartInv on this customer's data today, what is the realistic confidence band of our recommendations, and what is the cleansing investment required to lift it?"*

CV0 is **not a product feature** — its outputs are reports and conversations with prospects, not screens inside SmartInv. It is the gate that prevents us from over-promising.

---

## Epics

| Code | Epic | User-visible outcome | Status |
|------|------|----------------------|--------|
| CV0.E1 | DQ Assessment Methodology | A repeatable framework that scores a customer's MRO data across 10 dimensions | ⚪ Planned |
| CV0.E2 | DQ Assessment Tooling | A CLI / notebook that runs the methodology against a customer's data extract | ⚪ Planned |
| CV0.E3 | Assessment Report Template | A polished, executive-grade report customers can act on | ⚪ Planned |

---

## Done Condition

CV0 is done when:

- A new customer prospect can have their MRO data assessed in **≤ 5 business days** from the moment they share an extract.
- The assessment produces a DQ score per item, per dimension, and per site, plus a recommended cleansing investment with effort and confidence estimates.
- The assessment report explicitly distinguishes **what SmartInv can deliver today** from **what requires DQ work first**.
- The methodology and tooling are reusable by anyone on the team — not tied to a single person's knowledge.
- The assessment outputs feed naturally into CV7 (Data Quality & Trust) once the customer becomes a pilot.

---

## Sequencing

```text
E1 (methodology)
  └── E2 (tooling)
        └── E3 (report template)
```

The methodology comes first — we should not implement scoring against an unclear contract. Tooling automates the methodology. The report packages it for non-engineers.

---

## Out of Scope

- In-product DQ surfaces — those belong to **CV7 (Data Quality & Trust)**.
- Customer-specific cleansing execution — that's pilot delivery, not assessment.
- Hosted self-service DQ scoring — premature; assessment is partner-led at MVP.

---

**See also:** [CV7 Data Quality & Trust](../cv7-data-quality-trust/index.md) · [CV8 Customer Readiness](../cv8-customer-readiness/index.md) · [Roadmap](../index.md)
