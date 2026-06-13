[< CV2 Inventory Health](../index.md)

# CV2.E5 — Anomaly Detection

**CV:** [CV2 — Inventory Health & Visibility](../index.md)
**Status:** ⚪ Planned
**Depends on:** CV2.E2

---

## What This Is

Surfaces unusual events the planner should look at: a consumption spike, a unit-price jump, a negative available balance. Isolation Forest for volume anomalies, statistical SPC for price anomalies — both deterministic and reproducible.

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV2.E5.S1 | Isolation Forest on rolling consumption per item; flag z-score > threshold | 📥 Backlog |
| CV2.E5.S2 | Statistical anomaly detection on unit prices vs contracted price history | 📥 Backlog |
| CV2.E5.S3 | Negative-available-balance rule check (reservation integrity) | 📥 Backlog |
| CV2.E5.S4 | "Anomalies — last 7 days" panel on the Inventory Health page | 📥 Backlog |
| CV2.E5.S5 | Drill-down from anomaly row to the source transaction | 📥 Backlog |

---

## Done Condition

- Anomalies are flagged within 24 hours of the source event.
- Each anomaly carries a "likely cause" annotation (work order link, off-contract supplier, etc.).
- Drill-down resolves to a concrete source-system record.

---

## Out of Scope

- Predictive anomaly detection (forecast-based) — Future.
- Real-time event-driven anomalies — **CV13 (Event Backbone)**.
- LLM-explained anomalies — Future.

---

**See also:** [CV2](../index.md) · [CV13](../../cv13-event-backbone/index.md)
