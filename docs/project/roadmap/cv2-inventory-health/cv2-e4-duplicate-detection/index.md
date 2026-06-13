[< CV2 Inventory Health](../index.md)

# CV2.E4 — Duplicate Detection

**CV:** [CV2 — Inventory Health & Visibility](../index.md)
**Status:** ⚪ Planned
**Depends on:** CV2.E2

---

## What This Is

Embedding-based detection of probable item-master duplicates. Sentence-transformer embeddings + blocking + a calibrated pair classifier produce candidate pairs with confidence scores. A planner reviews the queue and decides Merge / Not a duplicate / Hold.

The model is registered in `ml.model_registry` so we can roll back if quality regresses ([Engineering Principles · A1](../../../../process/engineering-principles.md#a1--one-tool-per-capability-versioned)).

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV2.E4.S1 | Sentence-transformer embeddings for item descriptions stored in `rag.chunks` | 📥 Backlog |
| CV2.E4.S2 | Blocking strategy (commodity + UoM + manufacturer prefix) to cap pair candidates | 📥 Backlog |
| CV2.E4.S3 | Pair classifier (gradient boosting) with calibrated probabilities | 📥 Backlog |
| CV2.E4.S4 | Batch detection runs nightly on incremental item updates | 📥 Backlog |
| CV2.E4.S5 | Review queue UI with side-by-side comparison and merge/not-duplicate/hold | 📥 Backlog |
| CV2.E4.S6 | "Merge" action goes through CV6 approval (never a direct DB merge) | 📥 Backlog |

---

## Done Condition

- The duplicate queue surfaces ≥ 0.85 average confidence for "probable" pairs.
- Merges route through approval; planners can audit the trail.
- The model is versioned and the queue records which model produced each pair.

---

## Out of Scope

- Cross-tenant duplicate detection — Future (privacy implications).
- Auto-merge — explicitly forbidden at MVP.

---

**See also:** [CV2](../index.md) · [CV6](../../cv6-workflow-approval/index.md)
