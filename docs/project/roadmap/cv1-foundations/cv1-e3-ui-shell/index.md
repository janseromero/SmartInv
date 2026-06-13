[< CV1 Foundations](../index.md)

# CV1.E3 — UI Shell

**CV:** [CV1 — Foundations](../index.md)
**Status:** ⚪ Planned
**Depends on:** CV1.E2

---

## What This Is

The persistent chrome that every screen lives inside: the sidebar with navigation groups (Overview, Operate, Intelligence, Govern), the topbar with command bar (⌘K), tenant chip, notification dot, and user identity in the sidebar footer. Matches the structure of the high-fidelity UI mock at `docs/smartinv-ui.html`.

This epic does not implement screen content — only the shell and the routing between placeholders.

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV1.E3.S1 | Sidebar component with logo mark, navigation groups, and user footer | 📥 Backlog |
| CV1.E3.S2 | Topbar with command bar (⌘K placeholder), tenant chip, notification dot | 📥 Backlog |
| CV1.E3.S3 | App layout shell (grid: sidebar + topbar + main) with active-screen state | 📥 Backlog |
| CV1.E3.S4 | Route placeholders for the 12 screens from the mock (each: page-head + empty body) | 📥 Backlog |
| CV1.E3.S5 | Active-route highlighting in sidebar | 📥 Backlog |

---

## Done Condition

- Sidebar + topbar render on every page using a single `RootLayout`.
- Navigation between the 12 placeholder screens works via Next.js App Router.
- The shell uses tokens only (no hex).
- The cmd bar and notification dot are visually present but non-functional (real wiring lands in later CVs).
- Keyboard navigation works across sidebar items and the cmd bar shortcut.

---

## Out of Scope

- Real screen content (Inventory Health table, Forecast chart, etc.) — **CV2, CV3, CV4, CV5**.
- Real notification feed — **CV6 (audit-driven)** / **CV13 (event-driven)**.
- Functional cmd bar with semantic search — **CV5 (Governed Conversational Analyst)** prerequisite.

---

**See also:** [CV1](../index.md) · [CV1.E2](../cv1-e2-design-tokens-tailwind/index.md) · [CV1.E8](../cv1-e8-component-contracts-storybook/index.md)
