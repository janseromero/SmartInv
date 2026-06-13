[< Roadmap](../index.md)

# CV14 — Advanced ML

**Status:** 🔵 Future
**Goal:** Deepen the SmartInv ML stack — probabilistic deep forecasting where data supports it, graph-based risk via GNN, and bounded reinforcement-learning exploration for policy optimization.

---

## What This Is

CV14 lifts SmartInv from "battle-tested classical ML" to "frontier ML where it earns its cost." It is **explicitly deferred** from the MVP per [AGENTS.md MVP scope](../../../../AGENTS.md#mvp-scope--build-this-defer-that): deep learning, RL, and GNN are on the deferred list. CV3 and CV4 deliver value with gradient boosting and deterministic risk scoring; CV14 expands the depth only where measurable gains exist.

The promise once activated:

> *"For items with enough history, the forecast is probabilistic and outperforms the gradient-boosted baseline on weighted MASE. For asset-rich tenants, risk is reasoned over a graph that captures asset–item–supplier–work-order relationships. For mature policies, reinforcement learning explores improvements under bounded simulation."*

---

## Epics

| Code | Epic | User-visible outcome | Status |
|------|------|----------------------|--------|
| CV14.E1 | Probabilistic Deep Forecasting | Temporal Fusion Transformer / DeepAR / N-BEATS deployed for items where data supports it; A/B against baseline | 🔵 Future |
| CV14.E2 | Risk GNN (Asset Graph) | Graph neural network over the item × asset × supplier × work-order graph; A/B against deterministic risk scoring | 🔵 Future |
| CV14.E3 | Reinforcement Learning Exploration | Bounded RL exploration for inventory policies in simulation; never directly applied to production without human approval | 🔵 Future |

---

## Done Condition

When CV14 activates:

- Each advanced model has a deployment gate: must beat the baseline on a held-out test set with weighted MASE (forecasting) or AUC (risk).
- Models are registered with versioned weights, training data hash, and reproducibility metadata.
- The user always sees which model produced a given prediction, with one-click rollback available.
- No RL policy is auto-applied to live data — exploration runs in simulation and proposals flow through CV6.

---

## Out of Scope

- Foundation-model fine-tuning — Future / Radar.
- Generic generative ML — Future.
- Federated learning across tenants — Future.

---

**See also:** [Roadmap](../index.md) · [CV3 Explainable Recommendations](../cv3-explainable-recommendations/index.md) · [CV4 Operational Risk Intelligence](../cv4-operational-risk/index.md)
