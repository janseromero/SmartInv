[< Roadmap](../index.md)

# CV15 — Compliance & Multi-Tenant Operations

**Status:** 🔵 Future
**Goal:** Lift SmartInv from pilot-grade to enterprise-grade — formal SOC 2 readiness, multi-tenant operations (onboarding flows, cross-tenant admin, isolation test suites), and the certifications customers need to commit budget.

---

## What This Is

CV15 is the discipline that turns SmartInv from "we can run pilots" into "we can sign annual enterprise contracts." It is **explicitly deferred** from the MVP per [AGENTS.md MVP scope](../../../../AGENTS.md#mvp-scope--build-this-defer-that): "SOC 2 certification (target readiness, not the audit)" and "Multi-tenant operations & hardening" are on the deferred list.

Important caveat (also from AGENTS.md): tenant-aware *foundations* are NOT deferred — see [non-negotiable #5](../../../../AGENTS.md#architectural-non-negotiables). CV15 builds on the foundations that CV1 already shipped; it doesn't bolt them on later.

The promise once activated:

> *"SOC 2 Type II + ISO 27001 readiness. Tenant onboarding is a documented operations procedure, not a developer ticket. Cross-tenant admin tooling exists and is audited. Isolation is verified by a continuously running test suite."*

---

## Epics

| Code | Epic | User-visible outcome | Status |
|------|------|----------------------|--------|
| [CV15.E1](cv15-e1-soc2-readiness/index.md) | SOC 2 Readiness | Controls catalog mapped to SmartInv; readiness audit scoped; evidence collection automated | 🔵 Future |
| [CV15.E2](cv15-e2-tenant-operations/index.md) | Tenant Operations | Tenant onboarding, suspension, deletion, and data export as documented operations procedures with audit | 🔵 Future |
| [CV15.E3](cv15-e3-cross-tenant-admin-console/index.md) | Cross-Tenant Admin Console | Internal-only admin surface to inspect tenants, audit access, and support customers with full audit trail | 🔵 Future |
| [CV15.E4](cv15-e4-isolation-test-suites/index.md) | Isolation Test Suites | Continuously running tests that assert no cross-tenant data leakage at the API, DB, queue, and storage layers | 🔵 Future |

---

## Done Condition

When CV15 activates:

- A SOC 2 Type II audit is scoped and ready to begin within 30 days of the activation decision.
- Tenant operations procedures are runnable by anyone on the operations rota.
- The admin console is rate-limited, audited per session, and never exposes raw tenant data to anyone without explicit elevation.
- Isolation tests run on every push and on a daily schedule; failures page the on-call.

---

## Out of Scope

- White-label SaaS multi-tenancy (brand theming, billing primitives) — Radar.
- On-prem / air-gapped deployment — Radar.
- ISO 27017 / 27018 cloud-specific extensions — Future.

---

**See also:** [Roadmap](../index.md) · [CV1 Foundations](../cv1-foundations/index.md) · [CV6 Workflow & Approval](../cv6-workflow-approval/index.md) · [CV8 Customer Readiness](../cv8-customer-readiness/index.md) · [AGENTS.md non-negotiables](../../../../AGENTS.md#architectural-non-negotiables)
