[< CV2 Inventory Health](../index.md)

# CV2.E5 — Anomaly Detection

**CV:** [CV2 — Inventory Health & Visibility](../index.md)
**Status:** ✅ Done (deterministic `anomaly-v1`; Isolation Forest deferred to `anomaly-v2`)
**Depends on:** CV2.E2
**Design:** [ADR-027](../../../decisions.md#adr-027--anomaly-detection-deterministic-robust-z--spc-detectors-versioned-isolation-forest-deferred)

---

## What This Is

Surfaces unusual events the planner should look at: a consumption spike, a unit-price jump, a negative available balance — shown on an "Anomalies — last 7 days" panel with drill-down to the source transaction. Per [ADR-027](../../../decisions.md#adr-027--anomaly-detection-deterministic-robust-z--spc-detectors-versioned-isolation-forest-deferred), the MVP ships **deterministic** detectors (robust z-score / SPC + a reservation-integrity rule, plus a practical-significance floor), not Isolation Forest — reproducible, dependency-free, and sufficient for the Done Condition. An Isolation-Forest / forecast-residual model can slot in later as `anomaly-v2` behind the same registry seam.

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV2.E5.S1 | ~~Isolation Forest~~ → **re-scoped**: per-item robust z-score on issue quantities + practical-significance floor ([ADR-027](../../../decisions.md#adr-027--anomaly-detection-deterministic-robust-z--spc-detectors-versioned-isolation-forest-deferred)) | ✅ Done (re-scoped) |
| CV2.E5.S2 | Robust-z / SPC on the per-item unit-price series (against **fixture-injected** transaction prices; procurement is the real source in CV9) | ✅ Done |
| CV2.E5.S3 | Negative-available-balance / over-reservation rule check | ✅ Done |
| CV2.E5.S4 | "Anomalies — last 7 days" panel on the Inventory Health page | ✅ Done |
| CV2.E5.S5 | Drill-down from an anomaly to the source transaction | ✅ Done |

---

## Done Condition

- ✅ Anomalies are flagged on demand (`make anomalies` / `POST /admin/anomalies`); a **nightly Dramatiq run** — deferred, no worker yet — meets the 24h SLA. The panel filters on `detected_for >= now − 7d`.
- ✅ Each anomaly carries a likely-cause annotation in `evidence.cause` (e.g. "Consumption 12x the item's median usage", "Unit price 4.2x the median").
- ✅ Drill-down resolves to a concrete source transaction (`source_record_id` → transaction detail).
- ✅ Deterministic + versioned: `anomaly-v1` in `ml.model_registry`; every anomaly records `model_version`.

## How to try it

```bash
make migrate && make seed && make sync-fixtures && make anomalies
# Inventory Health page now shows the "Anomalies — last 7 days" panel with
# type filter, severity, likely cause, and drill-down to the source transaction.
```

---

## Out of Scope

- Isolation Forest / forecast-residual model (`anomaly-v2`) — deferred.
- Real price history from procurement — **CV9** (E5 runs on fixture-injected prices).
- Predictive (forecast-based) anomalies — Future.
- Real-time event-driven anomalies — **CV13 (Event Backbone)**.
- LLM-explained anomalies — Future.

---

**See also:** [CV2](../index.md) · [CV9](../../cv9-procurement-supplier/index.md) · [CV13](../../cv13-event-backbone/index.md) · [ADR-027](../../../decisions.md#adr-027--anomaly-detection-deterministic-robust-z--spc-detectors-versioned-isolation-forest-deferred)
