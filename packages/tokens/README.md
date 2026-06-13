# @smartinv/tokens

> Single source of truth for SmartInv design tokens: colors, spacing,
> typography, radii, shadows, and semantic aliases.

This package is **how SmartInv stays portable across surfaces**. Web today,
mobile later, internal admin tools whenever needed — every renderer reads
from these tokens. Components never carry raw hex codes.

## What's exported

```ts
import {
  // Raw color palettes (per family)
  chrome, surface, ink, teal, ai, ok, warn, crit,
  color,         // aggregate, used by Tailwind
  // Other primitives
  space, radius, fontFamily, fontSize, shadow,
  // Named aliases for product meaning
  semantic,
} from '@smartinv/tokens';
```

### Semantic naming

Always prefer **semantic tokens** over raw colors when the token has product
meaning:

| Semantic | Raw equivalent | When to use |
|---|---|---|
| `semantic.aiContent` | `ai.DEFAULT` | Any AI-produced content (per [AGENTS.md non-negotiable #8](../../AGENTS.md#architectural-non-negotiables)) |
| `semantic.aiContentSoft` | `ai.soft` | AI-content backgrounds |
| `semantic.statusOk` | `ok.DEFAULT` | Healthy / approved / on-track |
| `semantic.statusWarn` | `warn.DEFAULT` | Watch / yellow / attention |
| `semantic.statusCrit` | `crit.DEFAULT` | Critical / failed / blocking |

Using `semantic.aiContent` instead of `ai.DEFAULT` makes the intent explicit
in the code: it tells the next reader "this is AI-produced" and protects the
violet=AI invariant.

## Where these values come from

The values are sourced from the high-fidelity UI mock at
`docs/smartinv-ui.html`. Changing a token here changes the look of every
surface that consumes it.

## How Tailwind reads these

`apps/web/tailwind.config.ts` imports the `color`, `space`, `radius`,
`fontFamily`, and `shadow` exports and maps them into the Tailwind theme.
Components then use familiar Tailwind utilities (`bg-teal`, `text-ink-2`,
`bg-ai-soft`, `rounded-md`, `shadow-card`) without ever touching a hex value.

## How to add a new token

1. Define it in the appropriate file (`colors.ts`, `spacing.ts`, ...).
2. Re-export it from `src/index.ts`.
3. If it has product meaning, alias it in `semantic.ts`.
4. Map it into Tailwind theme in `apps/web/tailwind.config.ts`.
5. Add an entry to this README.
6. Use it.

## How to make sure no hex creeps in

```bash
pnpm lint:hex
```

This scans `apps/web/**/*.{ts,tsx,css}` and `packages/ui-web/**/*.{ts,tsx,css}`
for raw `#RRGGBB` literals and fails on any hit. CI runs the same check.

The only legitimate hex literals live in:
- This package (`packages/tokens/`)
- `apps/web/tailwind.config.ts` (consumes tokens, may inline default Tailwind palette)
- Generated files (`.next`, `dist`, `node_modules`)

## Related

- [ADR-002 — Web-only MVP, but shared-system-ready (Option B)](../../docs/project/decisions.md#adr-002--web-only-mvp-but-shared-system-ready-option-b)
- [ADR-015 — Tokens-only styling](../../docs/project/decisions.md#adr-015--tokens-only-styling-no-hex-codes-in-components)
- [AGENTS.md non-negotiables](../../AGENTS.md#architectural-non-negotiables)
