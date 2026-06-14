[< CV1 Foundations](../index.md)

# CV1.E6 — Auth & Tenancy

**CV:** [CV1 — Foundations](../index.md)
**Status:** ✅ Done (MVP slice — real IdP deferred)
**Depends on:** CV1.E5

---

## What This Is

JWT carries `tenant_id` and roles. Every API call sets the Postgres `app.current_tenant_id` GUC so RLS works. The chain — `JWT → request context → least-privilege SQLAlchemy session → Postgres GUC → RLS predicate` — is the application-layer half of tenant isolation; the DB layer is its safety net.

**MVP slice (ADR-020, ADR-021):** built the full enforcement loop against a local **HS256 dev token-issuer** behind an OIDC-shaped `verify_token` seam. Real Auth0/Keycloak SSO ([ADR-012](../../../decisions.md#adr-012--auth0-or-keycloak-for-identity-at-mvp)) and full web Auth.js are **deferred** — they swap in by changing only `verify_token` and the login page. The runtime now connects as the least-privilege `smartinv_app` role, so RLS actually filters (the E5 superuser-bypass finding is resolved).

---

## Stories

| Code | Story | Status |
|------|-------|--------|
| CV1.E6.S1 | Token verification behind an OIDC-shaped seam (HS256 dev issuer; real Auth0/Keycloak **deferred**) | ✅ Done (MVP) |
| CV1.E6.S2 | FastAPI dependency that decodes JWT and produces a typed `CurrentUser` | ✅ Done |
| CV1.E6.S3 | Least-privilege session that sets `app.current_tenant_id` before any query | ✅ Done |
| CV1.E6.S4 | RBAC: roles claim parsed from JWT; `require_role` dependency on endpoints | ✅ Done |
| CV1.E6.S5 | `/me` endpoint returning current user + tenant + roles (JIT user provisioning) | ✅ Done |
| CV1.E6.S6 | Web auth: dev sign-in page + token storage + protected routes + logout (full Auth.js **deferred**) | ✅ Done (MVP) |
| CV1.E6.S7 | E2E test asserting cross-tenant data access is impossible | ✅ Done |

---

## Done Condition

- ✅ A signed-in user's queries return only their tenant's data **even though the endpoint never filters by tenant** — RLS + the least-privilege role enforce it (`test_items_are_isolated_per_tenant`).
- ✅ Roles in the JWT gate endpoints; a token without an inventory-read role gets `403`.
- ✅ The cross-tenant E2E test passes against a real Postgres in CI; CI fails if isolation breaks.
- ✅ `services/api` rejects requests without a valid JWT with `401`.

## Deferred to a follow-up (ADR-021)

- Real Auth0/Keycloak OIDC integration (discovery, callback, RS256/JWKS) — swaps into `verify_token` only.
- Full web Auth.js session + TanStack Query data layer.
- RBAC sourced from `core.role_bindings` (currently roles travel in the JWT).

## How to use

```bash
make token TENANT=smartinv-dev ROLES=admin,planner   # mint a dev JWT
# or: POST /auth/dev-login {"tenant_slug": "...", "roles": [...]}
curl -H "Authorization: Bearer <token>" localhost:8000/me
```

---

## Out of Scope

- ABAC / OPA policies — Phase 2 (deferred until role complexity earns it).
- Multi-factor / step-up auth — Future.
- Identity federation between tenants — Future.

---

**See also:** [CV1](../index.md) · [CV1.E5](../cv1-e5-database-foundations/index.md) · [ADR-012](../../../decisions.md#adr-012--auth0-or-keycloak-for-identity-at-mvp) · [Engineering Principles · S5](../../../../process/engineering-principles.md#s5--tenant-isolation-has-two-layers)
