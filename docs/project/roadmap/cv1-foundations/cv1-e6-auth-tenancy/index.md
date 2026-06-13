[< CV1 Foundations](../index.md)

# CV1.E6 — Auth & Tenancy

**CV:** [CV1 — Foundations](../index.md)
**Status:** ⚪ Planned
**Depends on:** CV1.E5

---

## What This Is

SSO sign-in via Auth0 or Keycloak ([ADR-012](../../../decisions.md#adr-012--auth0-or-keycloak-for-identity-at-mvp)). JWT carries `tenant_id` and roles. Every API call sets the Postgres `app.current_tenant_id` GUC so RLS works. The chain — `JWT → request context → SQLAlchemy session → Postgres GUC → RLS predicate` — is the application-layer half of tenant isolation; the DB layer is its safety net, not its primary defense.

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV1.E6.S1 | Integrate Auth0 (or Keycloak) — OIDC discovery, callback, token verification | 📥 Backlog |
| CV1.E6.S2 | FastAPI dependency that decodes JWT and produces a typed `CurrentUser` | 📥 Backlog |
| CV1.E6.S3 | SQLAlchemy session middleware that sets `app.current_tenant_id` before any query | 📥 Backlog |
| CV1.E6.S4 | RBAC: roles claim parsed from JWT; `require_role` decorator on endpoints | 📥 Backlog |
| CV1.E6.S5 | `/me` endpoint returning current user + tenant + roles | 📥 Backlog |
| CV1.E6.S6 | Web auth: Next.js `auth.js` integration, protected routes, logout | 📥 Backlog |
| CV1.E6.S7 | E2E test asserting cross-tenant data access is impossible | 📥 Backlog |

---

## Done Condition

- A signed-in user lands on a tenant-scoped page; queries return only their tenant's data even when the application code "forgets" to filter.
- Roles in the JWT gate access to admin / planner / manager / finance routes.
- The cross-tenant access E2E test passes; CI fails if isolation is broken.
- `services/api` rejects requests without a valid JWT with `401`.

---

## Out of Scope

- ABAC / OPA policies — Phase 2 (deferred until role complexity earns it).
- Multi-factor / step-up auth — Future.
- Identity federation between tenants — Future.

---

**See also:** [CV1](../index.md) · [CV1.E5](../cv1-e5-database-foundations/index.md) · [ADR-012](../../../decisions.md#adr-012--auth0-or-keycloak-for-identity-at-mvp) · [Engineering Principles · S5](../../../../process/engineering-principles.md#s5--tenant-isolation-has-two-layers)
