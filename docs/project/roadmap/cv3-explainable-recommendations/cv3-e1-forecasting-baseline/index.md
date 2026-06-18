[< CV3 Explainable Recommendations](../index.md)

# CV3.E1 — Demand Forecasting Baseline

**CV:** [CV3 — Explainable Inventory Recommendations](../index.md)
**Status:** ✅ Done (deterministic `forecast-croston-v1`; LightGBM deferred to `forecast-v2`)
**Prerequisite for:** CV3.E2
**Design:** [ADR-028](../../../decisions.md#adr-028--explainable-recommendations-deterministic-crostontsb-forecast--closed-form-optimization-versioned-lightgbmpyomo-deferred)

> **Re-scoped (ADR-028):** ships Croston/TSB + CV-based P50/P80/P95 quantiles in `ml.predictions`, versioned, with `make forecast` / `POST /admin/forecast` and a reproducibility fingerprint. LightGBM feature-engineering (S2) and regime-change refresh (S5, now part of CV3.E5) are deferred. On-demand recompute; nightly schedule deferred.

---

## What This Is

Probabilistic demand forecasting tuned for intermittent MRO patterns. Two-tier approach: Croston / TSB as the explainable baseline, gradient boosting (LightGBM) for items with enough signal. Every prediction carries `model_version`, P50/P80/P95 quantiles, and a reproducibility fingerprint ([Engineering Principles · D2](../../../../process/engineering-principles.md#d2--versioned-model-outputs)).

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV3.E1.S1 | Implement Croston / TSB baseline per item × site | 📥 Backlog |
| CV3.E1.S2 | LightGBM forecaster with feature engineering (seasonality, PM plans, asset state) | 📥 Backlog |
| CV3.E1.S3 | Quantile forecasts (P50/P80/P95) persisted in `ml.predictions` | 📥 Backlog |
| CV3.E1.S4 | Model registry entry per model version with held-out MASE | 📥 Backlog |
| CV3.E1.S5 | Regime-change detection (asset retirement, strategy shift) signals model refresh | 📥 Backlog |
| CV3.E1.S6 | `GET /api/forecast/{item_id}?horizon=12` endpoint | 📥 Backlog |

---

## Done Condition

- Forecasts exist for every item in the active tenant.
- Each prediction record includes `model_version`, quantiles, and input fingerprint.
- Forecast accuracy (weighted MASE, bias, P80 coverage) is tracked per model version.
- The forecast API is consumable by the optimization engine (CV3.E2).

---

## Out of Scope

- Deep probabilistic forecasting (TFT, DeepAR, N-BEATS) — **CV14.E1**.
- Reinforcement learning policy optimization — **CV14.E3**.
- Conversational forecast queries — **CV5**.

---

**See also:** [CV3](../index.md) · [CV3.E2](../cv3-e2-optimization-engine/index.md) · [CV14.E1](../../cv14-advanced-ml/cv14-e1-probabilistic-deep-forecasting/index.md)
