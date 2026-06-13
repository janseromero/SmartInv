[< CV8 Customer Readiness](../index.md)

# CV8.E1 — Tenant Onboarding Wizard

**CV:** [CV8 — Customer Readiness](../index.md)
**Status:** ⚪ Planned

---

## What This Is

A guided flow that takes an admin from "we have a signed pilot" to "data is flowing and users are inviting each other" in ≤ 1 hour. Covers tenant creation, source connector configuration, user invites with roles, and a "first data flowing" verification step.

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV8.E1.S1 | "Create tenant" step (tenant_id, name, region, defaults) | 📥 Backlog |
| CV8.E1.S2 | Connector setup step (Maximo URL, credentials, scope) | 📥 Backlog |
| CV8.E1.S3 | User invite step (email, role, plant scope) | 📥 Backlog |
| CV8.E1.S4 | "First data flowing" verification (live counters from sync run) | 📥 Backlog |
| CV8.E1.S5 | Onboarding analytics: time-to-first-data, abandonment per step | 📥 Backlog |

---

## Done Condition

- A new tenant can be created and brought to live data in under 1 hour of guided steps.
- Abandonment per step is measured and accessible.

---

## Out of Scope

- Sales-team onboarding tooling — out of product.
- Self-serve trial signup — Future.

---

**See also:** [CV8](../index.md) · [CV2.E1](../../cv2-inventory-health/cv2-e1-maximo-connector/index.md)
