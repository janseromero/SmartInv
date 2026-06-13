[< CV1 Foundations](../index.md)

# CV1.E8 — Component Contracts & Web Implementations

**CV:** [CV1 — Foundations](../index.md)
**Status:** ⚪ Planned
**Depends on:** CV1.E2

---

## What This Is

Populates `@smartinv/ui-contracts` with TypeScript interfaces for every shared UI primitive (`KpiCard`, `EvidenceStrip`, `Badge`, `ApprovalStep`, `ConfidenceMeter`) and `@smartinv/ui-web` with the React implementations that consume tokens from `@smartinv/tokens`. Storybook (or Ladle) makes the components visible, testable, and design-reviewable in isolation.

The contracts pattern ([ADR-002](../../../decisions.md#adr-002--web-only-mvp-but-shared-system-ready-option-b)) is what makes the future cross-platform port a re-skin, not a rewrite.

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV1.E8.S1 | Define `KpiCard`, `EvidenceStrip`, `Badge`, `ApprovalStep`, `ConfidenceMeter` interfaces in `@smartinv/ui-contracts` | 📥 Backlog |
| CV1.E8.S2 | Implement each component in `@smartinv/ui-web` using shadcn/ui primitives + tokens | 📥 Backlog |
| CV1.E8.S3 | Add Storybook with `default`, `with-data`, `loading`, `error`, and `dense` stories per component | 📥 Backlog |
| CV1.E8.S4 | Biome rule blocking direct `@radix-ui/*` imports outside `@smartinv/ui-web` | 📥 Backlog |
| CV1.E8.S5 | Vitest snapshots for each Storybook story | 📥 Backlog |
| CV1.E8.S6 | Document the contracts pattern in `packages/ui-contracts/README.md` | 📥 Backlog |

---

## Done Condition

- All five primitive contracts are implemented and consumed by Storybook.
- No file outside `@smartinv/ui-web` imports from `@radix-ui/*`.
- Storybook builds and is deployable as a static site for design review.
- Vitest snapshot suite passes; every prop variation has a story.

---

## Out of Scope

- React Native implementations — **CV12.E1 (Cross-Platform Design System)**.
- Theme switching at runtime — Future.
- Visual regression testing (Chromatic / Percy) — Future.

---

**See also:** [CV1](../index.md) · [CV1.E2](../cv1-e2-design-tokens-tailwind/index.md) · [ADR-002](../../../decisions.md#adr-002--web-only-mvp-but-shared-system-ready-option-b)
