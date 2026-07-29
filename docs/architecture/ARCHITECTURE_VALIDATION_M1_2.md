# Architecture Validation Report — M1.2 Authentication Boundary

> **Milestone:** M1.2 Authentication Boundary
> **Date:** 2026-07-28
> **Scope:** Confirms the M1.2 implementation preserves the ratified architecture
> **Verdict:** ✅ **PASS** — all seven required confirmations hold, evidenced mechanically
> **One defect found and fixed during validation** (Finding 3): the `auth` schema's isolation was defeated by the frontend connecting as the database owner.

> **Note added 2026-07-29.** This is a dated record of what was true at M1.2 and is deliberately **not** rewritten. Where it says a check *runs in CI*, that check now runs locally — CI was disabled project-wide by [ADR-0027](adr/0027-local-first-development.md). Every check named below still exists and still binds; only where it executes has changed.

Every claim below is backed by an automated check that runs mechanically, not by inspection. Where a claim could only be verified by reading code, that is stated explicitly rather than presented as proof.

---

## 1. Module boundaries remain intact ✅

**Confirmed.** All three import-linter contracts pass, and they have been demonstrated to fail on a deliberate violation (M0).

```
modules: Clean Architecture layering                              KEPT
workspace_tenancy: domain has no infrastructure/framework deps    KEPT
signora_platform must not depend on any module                    KEPT
```

M1.2 added no cross-module dependency. The frontend is a separate deployable and cannot import backend modules by construction; the backend gained no import of frontend code.

**Evidence:** `uv run lint-imports` in `.github/workflows/backend.yml`.

---

## 2. Authentication remains frontend-owned ✅

**Confirmed.** Every credential-handling path lives in Next.js:

| Concern | Location | Tier |
|---|---|---|
| Credential storage | Better Auth (`auth` schema) | Frontend |
| OAuth authorization-code exchange | `frontend/app/api/auth/[...all]/route.ts` | Frontend |
| Session lifecycle | `frontend/lib/auth/server.ts` | Frontend |
| Token issuance | `frontend/lib/auth/jwt.ts` | Frontend |
| Token refresh | `frontend/app/api/token/route.ts` | Frontend |

**Mechanical evidence — the Python tier contains none of it:**

- No login, sign-in, OAuth, authorize, or refresh route exists. A repository-wide search over `signora_platform/`, `modules/`, and `apps/` returns no such handler.
- No password storage: no `bcrypt`, `argon2`, `password_hash`, or equivalent appears anywhere in backend production code.
- Password authentication is explicitly disabled in Better Auth (`emailAndPassword.enabled: false`), so credentials are never stored in *either* tier — sign-in is OAuth-only.

**Additional isolation:** migration `0005` grants the `auth` schema to a dedicated `signora_auth` role and **explicitly revokes all access from `signora_app`**. The API tier could not read authentication data even if code attempted to.

Verified against a live database:

```
has_schema_privilege('signora_auth', 'auth', 'CREATE')  →  t
has_schema_privilege('signora_app',  'auth', 'USAGE')   →  f
```

This check was added because the revoke alone did not make the boundary real — see Finding 3.

---

## 3. FastAPI only performs JWT verification ✅

**Confirmed.** The API's entire authentication surface is `signora_platform/auth/`, which contains a verifier and nothing else.

- `JwtVerifier` exposes `verify()` only. It has no `sign()` or `issue()` method — asserted in `test_m1_2_demo_checklist.py::test_item_9`.
- The API is configured with a **public key only**. `check_auth_health` rejects a private key as configuration outright, reporting `unavailable` and refusing readiness.
- The tier is cryptographically incapable of minting a token it would accept.

**Evidence:** `test_item_9_private_key_is_absent_from_backend_configuration` asserts this three ways: health rejects a private key, no production source references private key material, and no signing method exists.

---

## 4. Casbin remains the authorization layer ✅

**Confirmed.** No authorization logic moved into the token or into the frontend.

- Every workspace-scoped route calls `context.authorize(Resource, Action)`, which delegates to Casbin. Three such calls exist in `workspace_tenancy/interface/router.py`, one per protected operation.
- The JWT carries **no permissions, roles, scopes, capabilities, or policy** — asserted in `frontend/tests/unit/jwt-contract.test.ts::carries no permissions or capabilities`.
- Casbin policy evaluation still includes `workspace_id` in the request tuple, so no check is ever global.

**Why this matters:** embedding permissions in the token would fork authorization across two systems and delay every policy change until tokens expire. The test exists specifically to prevent that drift.

---

## 5. No credentials enter the Python tier ✅

**Confirmed**, on four independent counts:

| Check | Result |
|---|---|
| Private signing key in backend production code | None |
| Password hashing or storage in backend | None |
| OAuth client secrets in backend configuration | None — `Settings` has no such field |
| API rejects a private key supplied as `SIGNORA_JWT_PUBLIC_KEY` | Yes, reports `unavailable` |

The backend `Settings` model carries exactly three auth fields: `jwt_public_key`, `jwt_issuer`, `jwt_audience`. There is no field into which a credential could be configured.

---

## 6. JWT contract matches the approved architecture ✅

**Confirmed by cross-tier contract test — the strongest evidence in this report.**

A token minted by the **real** Next.js issuance path (`lib/auth/jwt.ts`) is verified by the **real** Python verifier. Nothing is mocked and neither side's claim set is restated in the test, so drift on either side fails the check.

| Claim | Required | Implemented | Verified |
|---|---|---|---|
| `iss` | ✅ | ✅ | ✅ |
| `aud` | ✅ | ✅ | ✅ |
| `sub` | ✅ | ✅ | ✅ |
| `sid` | ✅ | ✅ | ✅ |
| `email` | ✅ | ✅ | ✅ |
| `email_verified` | ✅ | ✅ | ✅ |
| `active_workspace_id` | optional | ✅ (omitted when null) | ✅ |
| `iat` / `exp` | ✅ | ✅ (900s TTL) | ✅ |
| `jti` | ✅ | ✅ | ✅ |

**Also confirmed:**
- Algorithm is `RS256`; the verifier's allowed list is pinned to exactly `["RS256"]`.
- The `alg:none` and algorithm-confusion attacks are re-verified as rejected after M1.2's changes to the auth path (`test_algorithm_confusion_is_still_rejected_after_m1_2_changes`).
- A token from a foreign key, or for a different audience, is rejected.
- `active_workspace_id` remains a **hint**: membership is re-verified server-side on every request, evidenced by `test_item_5` (a non-member receives 404, and their workspace list is empty).

**Evidence:** `backend/tests/integration/test_jwt_cross_tier_contract.py`, run as a dedicated CI job.

---

## 7. Documentation remains synchronized ✅

**Confirmed.**

| Document | Status |
|---|---|
| `18-authentication.md` | Updated with issuer-side configuration as built |
| `ADR-0026` | Unchanged — implementation matches the ratified decision |
| `11-tenancy.md` | Updated — per-tier database roles (Finding 3) |
| `10-security.md` | Unchanged — no security posture change |
| `PROJECT_STATUS.md` | Updated to v5 |
| `IMPLEMENTATION_ROADMAP.md` | Unchanged — M1.2 delivered as scoped |

All internal documentation links resolve. No architectural change was made, so no new ADR is required.

---

## Additional requirements delivered

Beyond the seven confirmations, M1.2 carried three added requirements:

**Authentication observability.** Structured `AUTH_*` events on both tiers, sharing one vocabulary so the two log streams are queryable as one. Frontend emits `LOGIN_SUCCESS`, `LOGIN_FAILURE`, `TOKEN_ISSUED`, `TOKEN_REFRESH`, `TOKEN_REJECTED`, `LOGOUT`, `OAUTH_CALLBACK`, `WORKSPACE_SWITCH`. API emits `TOKEN_ACCEPTED`, `TOKEN_REJECTED`, `WORKSPACE_SWITCH`, `WORKSPACE_ACCESS_DENIED` — only the states it can actually observe.

Two design choices worth recording:
- **`outcome` is derived from the event name, never passed in**, so a failure cannot be recorded as a success by a mistaken argument. An audit trail that can lie is worse than none.
- **PII and tokens are excluded structurally, not by convention.** The frontend event context is a closed type that drops email and token-shaped keys at emit time; `jti` is explicitly permitted because it is an opaque identifier, not a credential.

**Authentication health.** Readiness now covers the auth subsystem on both tiers: Better Auth database connectivity and schema presence, signing-key availability *and pair-match*, JWT configuration, and OAuth provider configuration.

The pair-match check is the one worth highlighting: both keys can load cleanly, every token mints successfully, and every request 401s with no obvious cause. Sign-then-verify at startup turns that baffling outage into a clear configuration error.

**Status semantics** are deliberate: no OAuth provider configured reports `degraded`, not `unavailable` — the process is healthy and restarting it would not help, but an operator needs to know.

---

## Findings

**No architectural violations.** Two implementation-quality notes and one defect:

1. **ESLint's `eslint-config-next` flat-config bridge fails to load** in this setup. Replaced with a direct `typescript-eslint` configuration. Next.js-specific linting still runs during `next build`. No architectural impact; recorded so the choice is not mistaken for an oversight.

2. **`@vitejs/plugin-react` was dropped** from devDependencies — its Vite version conflicts with `better-auth`'s optional Svelte peer dependencies. Not needed: M1.2's tests target JWT and key-management logic, which is plain TypeScript. React component testing will need it back when M1.3 adds component tests.

**One defect found and fixed during validation:**

3. **`signora_auth` was created but never connected as.** Migration `0005` creates the role and revokes `signora_app` from the `auth` schema — but the role was `NOLOGIN`, nothing issued it a credential, and the frontend's default connection string was the **database owner**. The owner reads every application table and is not subject to Row-Level Security, so the schema isolation the migration exists to create was defeated at the point of connection.

   The revoke was doing real work; it was simply pointed at the wrong tier. The API tier was correctly locked out while the frontend held a credential strictly stronger than the one being denied.

   Fixed by `infra/postgres-init/02-auth-role.sql` (local credential, mirroring the existing `signora_app` pattern), a matching CI step, and changing the frontend's default to `signora_auth`. Confirmed against a live database as shown in §2.

   **Why it survived every prior check:** the two tiers' permissions were each verified in isolation, and both were individually correct. Nothing asserted the relationship *between* them. This is the same class of gap the cross-tier contract test exists to close for JWT claims.

   **Regression guard:** `test_tenant_isolation.py::TestTierRoleSeparation` now asserts the relationship in both directions — `signora_app` has no `USAGE` on `auth`, `signora_auth` can `SELECT` no table in `public`, and neither role is superuser or holds `BYPASSRLS`. Confirmed to bite: granting the two privileges back fails two of the three tests.

---

## Verification Summary

| Gate | Result |
|---|---|
| Backend tests | **242 passing** |
| Frontend tests | **29 passing** |
| Cross-tier contract | **3 passing** |
| M1.2 Demo Checklist | **10 / 10** |
| Backend coverage | **95.84%** (gate 95%) |
| mypy strict | Clean, 102 files |
| ruff | Clean |
| ESLint / Prettier / tsc | Clean |
| import-linter | 3 contracts kept |
| Migrations | Reversible across 6 revisions |

**Verdict: the M1.2 implementation preserves the approved architecture in full.**
