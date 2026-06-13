[< CV1 Foundations](../index.md)

# CV1.E2 — Design Tokens & Tailwind Wiring

**CV:** [CV1 — Foundations](../index.md)
**Status:** ✅ Done
**Depends on:** CV1.E1
**Prerequisite for:** CV1.E3, CV1.E8

---

## What This Is

Populates `@smartinv/tokens` with the source-of-truth values from the high-fidelity UI mock (colors, spacing, typography, radii, shadows). Wires Tailwind to consume the tokens. Bans raw hex codes in components — enforced in CI ([AGENTS.md non-negotiable #7](../../../../AGENTS.md#architectural-non-negotiables)).

This is the contract that makes the future migration to a shared design system (Tamagui / mobile) a re-skin rather than a rewrite ([ADR-002](../../../decisions.md#adr-002--web-only-mvp-but-shared-system-ready-option-b)).

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV1.E2.S1 | Define design tokens in `@smartinv/tokens` from the HTML mock (colors, spacing, typography, radii, shadows) | ✅ Done |
| CV1.E2.S2 | Wire `apps/web/tailwind.config.ts` to read from `@smartinv/tokens` | ✅ Done |
| CV1.E2.S3 | Add no-raw-hex scanner banning `#hex` literals in `apps/web` and `packages/ui-web` (custom Node script, CI-wired) | ✅ Done |
| CV1.E2.S4 | Add token export for "violet = AI" semantic ([AGENTS.md non-negotiable #8](../../../../AGENTS.md#architectural-non-negotiables)) | ✅ Done |
| CV1.E2.S5 | Document token usage in `packages/tokens/README.md` | ✅ Done |

---

## Done Condition

All criteria met:

- ✅ Every color, spacing, radius, and font family used by the web app comes from `@smartinv/tokens`.
- ✅ No file in `apps/web/` or `packages/ui-web/` contains a raw hex code; CI fails on regression (verified by planting and removing a violation).
- ✅ The violet AI-content semantic is encoded as a named token (`semantic.aiContent` + Tailwind `bg-ai`, `text-ai`, `bg-ai-soft`).
- ✅ The token package builds, type-checks strictly, and is consumed by the web app.

Storybook consumption lands in CV1.E8 (component contracts), where the
tokens earn their place in primitives like `KpiCard`, `EvidenceStrip`,
and `Badge`.

---

## Delivered in

- `9d1bcea` feat(tokens,web): populate @smartinv/tokens and wire Tailwind
- `b2dfd69` ci(lint): add no-raw-hex scanner banning hex codes in components

---

## Out of Scope

- Native (React Native) implementations of the same tokens — **CV12 (Mobile & Field)**.
- Dark mode — Future.
- Theme switching at runtime — Future.

---

**See also:** [CV1](../index.md) · [CV1.E3](../cv1-e3-ui-shell/index.md) · [CV1.E8](../cv1-e8-component-contracts-storybook/index.md) · [ADR-015](../../../decisions.md#adr-015--tokens-only-styling-no-hex-codes-in-components)
