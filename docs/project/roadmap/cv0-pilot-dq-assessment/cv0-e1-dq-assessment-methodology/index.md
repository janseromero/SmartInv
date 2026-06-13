[< CV0 Pilot DQ Assessment](../index.md)

# CV0.E1 — DQ Assessment Methodology

**CV:** [CV0 — Pilot Data-Quality Assessment](../index.md)
**Status:** ⚪ Planned
**Prerequisite for:** CV0.E2, CV0.E3

---

## What This Is

The methodology is the contract. Before we automate scoring (E2) or productize a report (E3), we need a clear definition of *what we measure*, *how we score it*, and *what the score implies for SmartInv's ability to deliver value on this customer's data*.

The output is a written framework that any team member can apply to a customer extract and produce a defensible assessment.

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV0.E1.S1 | Define the 10 DQ dimensions and their measurement criteria (MPN, UoM, description, commodity, asset link, lead time, supplier, criticality, classification, duplicates) | 📥 Backlog |
| CV0.E1.S2 | Define the per-item, per-site, and per-tenant DQ score aggregation formula | 📥 Backlog |
| CV0.E1.S3 | Define the cleansing investment framework (per-dimension effort × confidence lift) | 📥 Backlog |
| CV0.E1.S4 | Pilot the methodology on a synthetic dataset and validate scores against known issues | 📥 Backlog |
| CV0.E1.S5 | Document the methodology as a reusable framework (`docs/process/dq-assessment.md`) | 📥 Backlog |

---

## Done Condition

- The 10 dimensions are named, defined, and measurable from a typical Maximo / SAP / Oracle extract.
- The scoring formula is reproducible: same inputs → same score.
- The cleansing investment framework distinguishes *safe* cleansing (auto-applied) from *human-review* cleansing.
- A synthetic dataset proves the methodology surfaces seeded issues at the expected scores.
- The written framework can be applied by anyone on the team — no tacit knowledge required.

---

## Out of Scope

- Tooling automation — **CV0.E2**.
- Customer-facing report — **CV0.E3**.
- In-product DQ scoring — **CV7 (Data Quality & Trust)**.

---

**See also:** [CV0](../index.md) · [CV0.E2](../cv0-e2-dq-assessment-tooling/index.md) · [CV7](../../cv7-data-quality-trust/index.md)
