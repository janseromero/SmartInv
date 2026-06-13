[< CV7 Data Quality & Trust](../index.md)

# CV7.E4 — DQ → Confidence Linkage

**CV:** [CV7 — Data Quality & Trust](../index.md)
**Status:** ⚪ Planned
**Depends on:** CV7.E1, CV3.E3

---

## What This Is

Connects DQ score directly to the recommendation envelope. Items with DQ below threshold produce recommendations carrying a "DQ warning" chip and a reduced confidence value. The system always tells the truth about its own confidence boundary.

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV7.E4.S1 | DQ-threshold check inside the recommendation pipeline | 📥 Backlog |
| CV7.E4.S2 | Confidence adjustment formula (penalty proportional to DQ gap) | 📥 Backlog |
| CV7.E4.S3 | DQ warning chip rendered on the EvidenceStrip | 📥 Backlog |
| CV7.E4.S4 | "DQ → confidence" chart on the Data Quality page | 📥 Backlog |
| CV7.E4.S5 | Test asserting low-DQ items never produce high-confidence recommendations | 📥 Backlog |

---

## Done Condition

- A low-DQ item produces a recommendation with both reduced confidence and a visible DQ warning.
- The DQ → confidence relationship is queryable and visualized.
- The regression test guards the linkage.

---

## Out of Scope

- Real-time confidence recalibration on event — **CV13**.
- Customer-tunable confidence thresholds — Future.

---

**See also:** [CV7](../index.md) · [CV3.E3](../../cv3-explainable-recommendations/cv3-e3-recommendation-envelope/index.md)
