[< CV8 Customer Readiness](../index.md)

# CV8.E3 — Accessibility Audit

**CV:** [CV8 — Customer Readiness](../index.md)
**Status:** ⚪ Planned

---

## What This Is

A WCAG 2.1 AA audit on the four MVP screens, plus the policies that prevent regressions. Color contrast, keyboard navigation, focus states, screen-reader semantics, and ARIA where needed.

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV8.E3.S1 | Color contrast verification across all tokens | 📥 Backlog |
| CV8.E3.S2 | Keyboard navigation pass on the four MVP screens | 📥 Backlog |
| CV8.E3.S3 | Screen-reader semantics for tables, charts, and evidence strip | 📥 Backlog |
| CV8.E3.S4 | Visible focus ring policy enforced through tokens | 📥 Backlog |
| CV8.E3.S5 | Accessibility CI check (axe-core via Playwright) | 📥 Backlog |
| CV8.E3.S6 | Manual screen-reader run-through documented | 📥 Backlog |

---

## Done Condition

- Automated axe-core scan reports zero blocking findings on the four MVP screens.
- Keyboard-only navigation is sufficient for any critical workflow.
- The accessibility check runs on every PR.

---

## Out of Scope

- WCAG AAA — Future.
- Internationalization beyond English — Future.

---

**See also:** [CV8](../index.md)
