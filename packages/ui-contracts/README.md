# @smartinv/ui-contracts

TypeScript **interfaces only** for SmartInv's shared UI primitives. No rendering,
no React — just the prop shapes that screens depend on.

## Why this exists (the contracts pattern)

Screens import **contracts**, not concrete components:

```
apps/web  →  @smartinv/ui-contracts (prop shapes)
                     ▲
                     │ implements
          @smartinv/ui-web (React, token-styled)
```

Because consumers depend on the contract — never on the implementation — we can:

- **Re-skin** the web components without touching any screen.
- **Port to native** later: a `@smartinv/ui-web-native` package implements the
  same contracts; screens are unchanged ([ADR-002](../../docs/project/decisions.md#adr-002--web-only-mvp-but-shared-system-ready-option-b)).
- **Review components in isolation** (Ladle) against the contract.

## Primitives

| Contract | Purpose |
|---|---|
| `KpiCardProps` | A KPI tile (label, value, delta, trend, status). |
| `EvidenceStripProps` | Evidence chips + confidence + model version — the recommendation envelope UI. |
| `BadgeProps` | Status / AI / neutral chip. `ai` is violet, reserved for AI content. |
| `ApprovalStepProps` | A single step in an approval workflow. |
| `ConfidenceMeterProps` | A 0..1 confidence bar with optional bands. |

## Rules

- Contracts are **pure types** — adding rendering logic here is a mistake.
- Implementations live in [`@smartinv/ui-web`](../ui-web) and use **tokens only**
  (no raw hex — enforced by `pnpm lint:hex`).
- Interactive, accessibility-critical widgets adopt Radix **inside `ui-web`** when
  needed; presentational primitives stay plain ([ADR-023](../../docs/project/decisions.md#adr-023--component-primitives-plain-token-styled-react-no-radix-until-needed)).

## Usage

```tsx
import type { KpiCardProps } from '@smartinv/ui-contracts';
import { KpiCard } from '@smartinv/ui-web';

const props: KpiCardProps = { label: 'Inventory Value', value: '$4.2M', status: 'ok' };
<KpiCard {...props} />;
```
