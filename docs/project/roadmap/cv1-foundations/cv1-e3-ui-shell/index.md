[< CV1 Foundations](../index.md)

# CV1.E3 — UI Shell

**CV:** [CV1 — Foundations](../index.md)
**Status:** ✅ Done
**Depends on:** CV1.E2

---

## What This Is

The persistent chrome that every screen lives inside: the sidebar with navigation groups (Overview, Operate, Intelligence, Govern), the topbar with command bar (⌘K), tenant chip, notification dot, and user identity in the sidebar footer. Matches the structure of the high-fidelity UI mock at `docs/smartinv-ui.html`.

This epic does not implement screen content — only the shell and the routing between placeholders.

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV1.E3.S1 | Sidebar component with logo mark, navigation groups, and user footer | ✅ Done |
| CV1.E3.S2 | Topbar with command bar (⌘K placeholder), tenant chip, notification dot | ✅ Done |
| CV1.E3.S3 | App layout shell (flex: sidebar + topbar + main) with active-screen state | ✅ Done |
| CV1.E3.S4 | Route placeholders for the 12 screens from the mock (each: page-head + empty body) | ✅ Done |
| CV1.E3.S5 | Active-route highlighting in sidebar via `usePathname()` + `aria-current="page"` | ✅ Done |

---

## Done Condition

All criteria met:

- ✅ Sidebar + topbar render on every page using `apps/web/app/(app)/layout.tsx`.
- ✅ 12 placeholder screens render via Next.js App Router; build emits all as static.
- ✅ Shell uses tokens only — `pnpm lint:hex` clean across `apps/web` and `packages/ui-web`.
- ✅ Cmd bar and notification dot present but non-functional (wiring lands in CV5/CV6/CV13).
- ✅ Keyboard navigation works (Next.js `<Link>` is anchor-based; `aria-current="page"` set on active route).

---

## Delivered in

- `d08fad7` feat(tokens): extend chrome and teal families for on-dark text shades
- `b48934b` feat(web): scaffold UI shell with sidebar, topbar, and 12 routes

---

## Out of Scope

- Real screen content (Inventory Health table, Forecast chart, etc.) — **CV2, CV3, CV4, CV5**.
- Real notification feed — **CV6 (audit-driven)** / **CV13 (event-driven)**.
- Functional cmd bar with semantic search — **CV5 (Governed Conversational Analyst)** prerequisite.

---

**See also:** [CV1](../index.md) · [CV1.E2](../cv1-e2-design-tokens-tailwind/index.md) · [CV1.E8](../cv1-e8-component-contracts-storybook/index.md)
