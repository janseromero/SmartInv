[< CV4 Operational Risk Intelligence](../index.md)

# CV4.E3 — Risk Dashboard UI

**CV:** [CV4 — Operational Risk Intelligence](../index.md)
**Status:** ✅ Done (LLM risk narrative deferred to CV5/CV10)
**Depends on:** CV4.E1, CV4.E2
**Design:** [ADR-029](../../../decisions.md#adr-029--operational-risk-deterministic-likelihoodxconsequence-score--rule-based-critical-spare-versioned-gnngbm-deferred)

> The `/risk` screen: KPI cards (downtime exposure, critical-spare coverage, single-source items, obsolescence candidates), a plant×risk-class heatmap shaded by exposure, the top critical-spare exposures table, and a drill-down with the breakdown + a **grounded, templated** narrative (no LLM). The "Summarize risk story" LLM version (S5) lands with CV5/CV10.

---

## What This Is

The Risk & Criticality screen from the mock. KPI cards (Downtime exposure, Critical spare coverage, Single-source items, Obsolescence candidates), Plant × Risk dimension heatmap, Top critical-spare exposures table.

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV4.E3.S1 | KPI cards aggregating risk metrics across the portfolio | 📥 Backlog |
| CV4.E3.S2 | Plant × Risk-dimension heatmap component | 📥 Backlog |
| CV4.E3.S3 | Top critical-spare exposures table with downtime $ and supplier risk badges | 📥 Backlog |
| CV4.E3.S4 | Drill-down from heatmap cell to filtered item list | 📥 Backlog |
| CV4.E3.S5 | "Summarize risk story" button (uses grounded narrative pattern) | 📥 Backlog |

---

## Done Condition

- The Risk & Criticality page renders fully on real data.
- The heatmap is interactive and scoped per plant + dimension.
- Every dollar figure traces back to source.

---

## Out of Scope

- LLM-generated risk narratives — touched here as a stub; deepens in **CV10**.
- Live risk recompute on events — **CV13**.

---

**See also:** [CV4](../index.md) · [CV4.E4](../cv4-e4-mitigation-workflows/index.md)
