[< Roadmap](../index.md)

# CV8 — Customer Readiness

**Status:** ⚪ Planned
**Goal:** Close the gap between "the four MVP capabilities work end-to-end on a dev laptop" and "a paying pilot customer can be onboarded, supported, and renewed."

---

## What This Is

CV8 is the discipline of going from *demo-able code* to *customer pays*. It is the CV that small teams skip and pay for later. The promise:

> *"A new tenant can be onboarded, their data ingested, their users invited, the four MVP capabilities used productively, and the team can support them in production without heroics."*

CV8 does not invent new features. It hardens, polishes, and packages what CV1–CV7 produced.

---

## Epics

| Code | Epic | User-visible outcome | Status |
|------|------|----------------------|--------|
| CV8.E1 | Tenant Onboarding Wizard | Authorized admin can create a tenant, connect a Maximo source, invite users with roles, and see "first data flowing" within a single guided flow | ⚪ Planned |
| CV8.E2 | UX Polish | Every page has empty states, loading skeletons, error states, and keyboard-navigable affordances | ⚪ Planned |
| CV8.E3 | Accessibility Audit | The four MVP screens pass a WCAG 2.1 AA audit on color contrast, keyboard nav, focus rings, screen-reader semantics | ⚪ Planned |
| CV8.E4 | Performance Budget | Dashboard pages load in < 2s TTI on a mid-range laptop; long jobs surface progress, never freeze the UI | ⚪ Planned |
| CV8.E5 | Deployment & Support Runbook | A reproducible pilot deployment runbook (Fly / Hetzner / small K8s) and a one-page-per-question support handover | ⚪ Planned |

---

## Done Condition

CV8 is done when:

- An onboarding wizard takes a new tenant from creation to first data in ≤ 1 hour of guided steps.
- Every page in the four MVP screens has empty / loading / error states and passes a keyboard-only navigation check.
- A WCAG 2.1 AA audit on the four MVP screens reports no blocking findings.
- The performance budget is met on a mid-range laptop and recorded as part of CI.
- A pilot deployment can be executed by anyone on the team using the runbook.
- A one-page support guide exists per common operational question.

---

## Sequencing

```text
E1 (tenant onboarding wizard)
  └── E2 (UX polish)
        └── E3 (accessibility audit)
              └── E4 (performance budget)
                    └── E5 (deployment & support runbook)
```

Order matters: onboarding informs UX polish; UX polish reveals accessibility issues; accessibility informs performance work; everything informs the runbook.

---

## Out of Scope

- Pilot data-quality assessment for new prospects — **CV0**.
- SOC 2 / ISO 27001 certification — **CV15 (Compliance & Multi-Tenant Operations)**.
- Marketing site, pricing page, sales collateral — out of product scope.
- Localization (es-MX, pt-BR) — Future / Radar.

---

**See also:** [Roadmap](../index.md) · [CV0 Pilot DQ Assessment](../cv0-pilot-dq-assessment/index.md) · [CV1 Foundations](../cv1-foundations/index.md) · [CV15 Compliance & Multi-Tenant Operations](../cv15-compliance-operations/index.md)
