[< CV1 Foundations](../index.md)

# CV1.E8 — Component Contracts & Web Implementations

**CV:** [CV1 — Foundations](../index.md)
**Status:** ✅ Done
**Depends on:** CV1.E2

---

## What This Is

Populates `@smartinv/ui-contracts` with TypeScript interfaces for every shared UI primitive (`KpiCard`, `EvidenceStrip`, `Badge`, `ApprovalStep`, `ConfidenceMeter`) and `@smartinv/ui-web` with the React implementations that consume tokens from `@smartinv/tokens`. **Ladle** makes the components visible, testable, and design-reviewable in isolation.

The contracts pattern ([ADR-002](../../../decisions.md#adr-002--web-only-mvp-but-shared-system-ready-option-b)) is what makes the future cross-platform port a re-skin, not a rewrite. Components are **plain token-styled React — no Radix/shadcn** until an interactive widget needs it ([ADR-023](../../../decisions.md#adr-023--component-primitives-plain-token-styled-react-no-radix-until-needed)).

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV1.E8.S1 | `KpiCard`, `EvidenceStrip`, `Badge`, `ApprovalStep`, `ConfidenceMeter` interfaces in `@smartinv/ui-contracts` | ✅ Done |
| CV1.E8.S2 | Each component implemented in `@smartinv/ui-web` as plain token-styled React (no Radix) | ✅ Done |
| CV1.E8.S3 | **Ladle** explorer with stories per component (variants: default/with-data/states/loading/dense) | ✅ Done |
| CV1.E8.S4 | Biome rule blocking `@radix-ui/*` outside `ui-web` | ⏸ Deferred until Radix is introduced ([ADR-023](../../../decisions.md#adr-023--component-primitives-plain-token-styled-react-no-radix-until-needed)) |
| CV1.E8.S5 | Vitest + @testing-library/react snapshots per component | ✅ Done |
| CV1.E8.S6 | Contracts pattern documented in `packages/ui-contracts/README.md` | ✅ Done |

---

## Done Condition

- ✅ All five primitive contracts are implemented and consumed by the Ladle explorer.
- ✅ No file imports from `@radix-ui/*` (Radix is not used yet; the guardrail rule is deferred with it).
- ✅ Ladle builds and is deployable as a static site (`pnpm --filter @smartinv/ui-web ladle:build`).
- ✅ Vitest snapshot suite passes (`pnpm test`); every component has stories covering its meaningful prop variations.

## Usage

```bash
pnpm --filter=@smartinv/ui-web ladle        # explorer at http://localhost:61000
pnpm --filter=@smartinv/ui-web ladle:build  # static site -> packages/ui-web/build
pnpm --filter=@smartinv/ui-web test         # snapshot tests
```

---

## Out of Scope

- React Native implementations — **CV12.E1 (Cross-Platform Design System)**.
- Theme switching at runtime — Future.
- Visual regression testing (Chromatic / Percy) — Future.

---

**See also:** [CV1](../index.md) · [CV1.E2](../cv1-e2-design-tokens-tailwind/index.md) · [ADR-002](../../../decisions.md#adr-002--web-only-mvp-but-shared-system-ready-option-b)
