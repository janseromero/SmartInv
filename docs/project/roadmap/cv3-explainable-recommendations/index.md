[< Roadmap](../index.md)

# CV3 — Explainable Inventory Recommendations

**Status:** 🟢 In Progress · E1–E5 delivered deterministically (`forecast-croston-v1` + `optimize-eoq-v1`); LightGBM/Pyomo deferred per [ADR-028](../decisions.md#adr-028--explainable-recommendations-deterministic-crostontsb-forecast--closed-form-optimization-versioned-lightgbmpyomo-deferred)
**Goal:** A planner accepts AI-generated min/max and reorder recommendations *and trusts them*, because every recommendation arrives with its envelope: claim, evidence, confidence, assumptions, model version, and the approval path.

---

## What This Is

CV3 is the second MVP killer capability ([AGENTS.md MVP scope](../../../../AGENTS.md#mvp-scope--build-this-defer-that) item 2) and the deepest single capability in the MVP. It combines four disciplines under one promise:

> *"For every recommendation SmartInv proposes, you can see exactly why, how confident the system is, what assumptions it made, which model version produced it, and what approval is required before it is acted on."*

The architectural rule that protects this promise is non-negotiable ([AGENTS.md](../../../../AGENTS.md#architectural-non-negotiables) #1): **agents propose, deterministic code disposes.** Recommendations originate from explainable optimization, not from an LLM.

---

## Epics

| Code | Epic | User-visible outcome | Status |
|------|------|----------------------|--------|
| [CV3.E1](cv3-e1-forecasting-baseline/index.md) | Demand Forecasting Baseline | Croston/TSB intermittent-demand forecast with P50/P80/P95 bands in `ml.predictions`, pinned `model_version` (LightGBM deferred) | ✅ Done |
| [CV3.E2](cv3-e2-optimization-engine/index.md) | Inventory Optimization Engine | Closed-form min/max + safety stock + reorder point, seeded Monte-Carlo stockout, analytical Pareto frontier (Pyomo deferred) | ✅ Done |
| [CV3.E3](cv3-e3-recommendation-envelope/index.md) | Recommendation Envelope | Every recommendation persisted in `ml.recommendations` as a complete, append-only envelope | ✅ Done |
| [CV3.E4](cv3-e4-recommendations-ui/index.md) | Recommendations UI | Optimization Recommendations screen: cards + EvidenceStrip + accept/override + Pareto + capital impact | ✅ Done |
| [CV3.E5](cv3-e5-override-feedback-loop/index.md) | Override & Feedback Loop | Typed override taxonomy, regime-change signals, acceptance-rate-per-model dashboard | ✅ Done |

---

## Done Condition

CV3 is done when:

- The forecast engine produces probabilistic forecasts for every item in the active tenant, with MASE and bias tracked per item class.
- The optimization engine produces min/max + reorder recommendations whose Monte Carlo stockout-probability claim is reproducible.
- Every recommendation is persisted with a complete envelope and a pointer to the originating model versions.
- The Recommendations UI shows the evidence strip on every card; no recommendation card lacks confidence or model version.
- Accepting a recommendation triggers the approval workflow ([CV6 Workflow & Approval](../cv6-workflow-approval/index.md)) — never a direct source-system write.
- Planner overrides are captured with structured reasons and queryable downstream.

---

## Sequencing

```text
E1 (forecasting baseline)
  └── E2 (optimization engine)
        └── E3 (recommendation envelope)
              └── E4 (recommendations UI)
                    └── E5 (override & feedback loop)
```

Linear dependency chain — the envelope cannot exist before optimization, and the UI cannot render without the envelope.

---

## Out of Scope

- LLM-driven recommendations or LLM-edited numbers — explicitly forbidden ([AGENTS.md](../../../../AGENTS.md#architectural-non-negotiables) #3).
- Deep probabilistic forecasting (TFT, DeepAR) — **CV14 (Advanced ML)**.
- Reinforcement learning policy optimization — **CV14**.
- Approval workflow execution — **CV6**.
- Risk-weighted recommendation re-ranking — **CV4 (Operational Risk Intelligence)**.

---

**See also:** [Roadmap](../index.md) · [CV1 Foundations](../cv1-foundations/index.md) · [CV2 Inventory Health](../cv2-inventory-health/index.md) · [CV4 Operational Risk Intelligence](../cv4-operational-risk/index.md) · [CV6 Workflow & Approval](../cv6-workflow-approval/index.md)
