[< CV0 Pilot DQ Assessment](../index.md)

# CV0.E2 — DQ Assessment Tooling

**CV:** [CV0 — Pilot Data-Quality Assessment](../index.md)
**Status:** ⚪ Planned
**Depends on:** CV0.E1
**Prerequisite for:** CV0.E3

---

## What This Is

The tooling turns the methodology into something the team can run on a customer extract in minutes, not days. CLI for partner-led assessment, notebook for guided exploration, dashboard for executive-grade rollups.

The tooling never modifies customer data — it reads extracts, scores them, and produces structured outputs that feed the report (E3).

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV0.E2.S1 | CLI takes a CSV/Excel/Parquet extract and outputs per-item DQ scores as JSON | 📥 Backlog |
| CV0.E2.S2 | Jupyter notebook walkthrough for partner-led assessment with charts | 📥 Backlog |
| CV0.E2.S3 | Aggregate dashboard generates per-site and per-tenant rollups | 📥 Backlog |
| CV0.E2.S4 | "As-is" vs "after recommended cleansing" comparison view | 📥 Backlog |
| CV0.E2.S5 | Tooling can ingest a Maximo MIF extract and an SAP MM extract without code changes | 📥 Backlog |

---

## Done Condition

- The CLI runs end-to-end on a 100K-item extract in under 10 minutes.
- The notebook is reproducible from a fresh `uv sync`.
- The tooling never writes back to the source; it only reads.
- Two real-shape extracts (Maximo + SAP) have been exercised.

---

## Out of Scope

- Customer-facing report PDF — **CV0.E3**.
- In-product DQ scoring (continuous) — **CV7**.
- Automated cleansing execution — **CV7.E3**.

---

**See also:** [CV0](../index.md) · [CV0.E1](../cv0-e1-dq-assessment-methodology/index.md) · [CV0.E3](../cv0-e3-assessment-report-template/index.md)
