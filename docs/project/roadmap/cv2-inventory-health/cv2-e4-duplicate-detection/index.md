[< CV2 Inventory Health](../index.md)

# CV2.E4 — Duplicate Detection

**CV:** [CV2 — Inventory Health & Visibility](../index.md)
**Status:** ✅ Done (deterministic `dedup-v1`; embeddings/classifier deferred to `dedup-v2` post-CV5)
**Depends on:** CV2.E2
**Design:** [ADR-026](../../../decisions.md#adr-026--duplicate-detection-deterministic-blocked-similarity-engine-versioned-embeddingsclassifier-deferred)

---

## What This Is

Detection of probable item-master duplicates surfaced as a review queue. A deterministic blocked-similarity engine produces confidence-scored candidate pairs; a planner reviews each pair side-by-side and decides Merge / Not a duplicate / Hold. A "merge" never edits source rows — it stages an `ml.recommendations` envelope routed through CV6 approval.

The model is registered in `ml.model_registry` so we can reproduce or roll back ([Engineering Principles · A1](../../../../process/engineering-principles.md#a1--one-tool-per-capability-versioned)). Per [ADR-026](../../../decisions.md#adr-026--duplicate-detection-deterministic-blocked-similarity-engine-versioned-embeddingsclassifier-deferred), the MVP ships a **deterministic** engine (no embeddings, no classifier, no new ML dependency); the sentence-transformer + gradient-boosting variant becomes a drop-in `dedup-v2` once CV5 fixes the embedding model.

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV2.E4.S1 | ~~Sentence-transformer embeddings in `rag.chunks`~~ → **re-scoped**: deterministic description normalization (token-set). Embeddings deferred to `dedup-v2` post-CV5 ([ADR-026](../../../decisions.md#adr-026--duplicate-detection-deterministic-blocked-similarity-engine-versioned-embeddingsclassifier-deferred)). | ✅ Done (re-scoped) |
| CV2.E4.S2 | Blocking strategy `(item_type, uom, block-prefix)` to cap pair candidates | ✅ Done |
| CV2.E4.S3 | ~~Gradient-boosting classifier~~ → **re-scoped**: deterministic weighted-feature scorer with banded confidence (`probable`/`possible`) | ✅ Done (re-scoped) |
| CV2.E4.S4 | On-demand detection (`make dedup` / `POST /admin/dedup`); re-runs preserve reviewed pairs. **Nightly Dramatiq deferred** (no worker yet, mirrors E3) | ✅ Done (on-demand) |
| CV2.E4.S5 | Review queue UI: confidence-sorted list, side-by-side compare, feature breakdown, merge/not-duplicate/hold | ✅ Done |
| CV2.E4.S6 | "Merge" emits an `ml.recommendations` envelope (`status='proposed'`, `approval_path='cv6_workflow'`) — never a direct DB merge. Actual merge wires in when CV6 lands | ✅ Done (seam) |

---

## Done Condition

- ✅ The duplicate queue surfaces ≥ 0.85 average confidence for "probable" pairs (blocking forces equal type+UoM, so a perfect description match reaches exactly 0.85).
- ✅ Merges route through approval (a `proposed` recommendation envelope); the candidate records `reviewed_*` for the audit trail.
- ✅ The model is versioned (`dedup-v1` in `ml.model_registry`) and every candidate records `model_version`.

## How to try it

```bash
make migrate && make seed && make sync-fixtures && make dedup
# Duplicate Detection page (/duplicates) shows the queue, KPIs, side-by-side
# compare with feature breakdown, and merge/not-duplicate/hold actions.
```

---

## Out of Scope

- Embedding/classifier model (`dedup-v2`) — deferred until CV5 fixes the embedding model.
- MPN extraction from descriptions — **CV7** (the `manufacturer` feature is wired but 0 until then).
- Cross-tenant duplicate detection — Future (privacy implications).
- Auto-merge — explicitly forbidden at MVP.
- Executing the merge — **CV6** performs the approved merge; E4 only proposes it.

---

**See also:** [CV2](../index.md) · [CV6](../../cv6-workflow-approval/index.md) · [ADR-026](../../../decisions.md#adr-026--duplicate-detection-deterministic-blocked-similarity-engine-versioned-embeddingsclassifier-deferred)
