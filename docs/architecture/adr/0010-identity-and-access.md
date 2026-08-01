# ADR-0010: Identity & Access — Better Auth + Casbin + OAuth (Google, Microsoft)

**Status:** Accepted — amended by [ADR-0026](0026-jwt-boundary-architecture.md)

> **Amendment notice.** This ADR described Better Auth as "framework-native," which holds for the Next.js frontend but not for the FastAPI backend — Better Auth is a TypeScript library with no Python SDK, and this ADR did not specify how the Python tier establishes a principal. That gap blocked the Workspace & Tenancy HTTP layer and was tracked as Risk R-13.
>
> It is resolved by [ADR-0026](0026-jwt-boundary-architecture.md): **Better Auth in Next.js is the sole Authentication Authority and issues short-lived RS256 JWTs; FastAPI only verifies them.** The vendor decision and all reasoning below stand unchanged — only the integration mechanism is now specified.

## Context

Per Principles 14–15, authentication and authorization are bought, not built. Signora needs both, workspace-scoped ([11-tenancy.md](../11-tenancy.md)), and needs to resolve whether Workspace & Tenancy is confirmed as a formal module (it was marked `[INFERRED]` in v1 — see [04-modules.md](../04-modules.md)).

## Decision

**Better Auth** for authentication (credential storage, session issuance, OAuth flows). **Casbin** for authorization (policy evaluation). **Google** and **Microsoft** as OAuth identity providers for sign-in. Workspace & Tenancy is confirmed as a ratified foundational platform module, owning the Workspace aggregate and membership, distinct from both.

## Alternatives Considered — Authentication

| Alternative | Why not chosen |
|---|---|
| **Auth0 / Clerk / WorkOS (bundled AuthN+AuthZ SaaS)** | Mature, enterprise-proven, and would bundle authorization too — but bundling means Signora's workspace-scoped permission model would live inside a vendor's proprietary rules configuration rather than under Signora's own version control, and per-MAU pricing scales unfavorably against a hundreds-of-thousands-of-workspaces target. Better Auth (self-hostable, open-source, framework-native) avoids both costs at the price of being a younger project — accepted as [16-architecture-risks.md](../16-architecture-risks.md) R-11. |
| **Roll our own authentication** | Explicitly rejected by Principle 14 — authentication is a security-critical, solved problem; building it in-house is pure liability with no differentiation. |

## Alternatives Considered — Authorization

| Alternative | Why not chosen |
|---|---|
| **Bundled authorization from an Auth0/Clerk/WorkOS-style vendor** | Rejected for the same reason as above — Signora's permission model (workspace-scoped roles, and likely future resource-level permissions per [17-future-recommendations.md](../17-future-recommendations.md)) is product-specific logic worth owning as policy-as-code, not vendor configuration. |
| **Open Policy Agent (OPA)** | A credible, more general-purpose policy engine, but heavier to operate (a separate policy-evaluation service) for Signora's comparatively contained permission model; Casbin's in-process, library-based model (RBAC/ABAC via policy files) is a better operational fit given the modular monolith's single-deployable design (Principle 1). |
| **Hand-rolled RBAC in application code** | Rejected — reimplements a solved problem (Principle 15's rationale extends here even though authorization-as-a-concept is "built" via Casbin's policy files; the *evaluation engine* itself must not be hand-rolled). |

## Tradeoffs

**We gain:** authorization policy as version-controlled, code-reviewed Casbin policy files under Signora's own control (directly supporting the Casbin policy model maturity roadmap item in [17-future-recommendations.md](../17-future-recommendations.md)); no per-MAU vendor pricing on identity; and two independently swappable, narrowly-scoped vendors instead of one broad, harder-to-partially-replace one.

**We give up:** the turnkey completeness of a bundled Auth0/Clerk/WorkOS-style platform (SSO/SCIM enterprise features ship faster with a bundled incumbent) — accepted because policy ownership was judged more valuable than turnkey speed, and because Better Auth's OAuth support for Google/Microsoft covers the near-term sign-in requirement directly.

## Risks

[16-architecture-risks.md](../16-architecture-risks.md) R-11 (younger-project vendor risk for Better Auth) and the enterprise-SSO/SCIM gap noted above, tracked against enterprise-readiness needs in [17-future-recommendations.md](../17-future-recommendations.md).

## Migration Strategy

Better Auth and Casbin are each accessed through `backend/platform/bought_infra_adapters/`, never called directly from module domain/application code. A migration to a bundled vendor (if enterprise SSO/SCIM demand outpaces Better Auth's roadmap) would replace the authentication adapter without touching Casbin-based authorization policy, or vice versa — the two are independently replaceable by design.

## Consequences

- Every authorization check evaluates a Casbin policy tuple that includes `workspace_id` — never a global permission check ([10-security.md](../10-security.md)).
- Workspace & Tenancy is confirmed as a ratified module in [04-modules.md](../04-modules.md), no longer `[INFERRED]`.
- Sign-in OAuth tokens (Google/Microsoft via Better Auth) are never reused as integration OAuth tokens (Gmail/M365/Google Calendar/Outlook Calendar via the Integration Abstraction Layer, [13-integrations.md](../13-integrations.md)) — these are separate grants with separate scopes and separate storage.
> **Amended 2026-08-01 by [ADR-0033](0033-authentication-methods.md).** Google and Microsoft OAuth are no longer the *only* sign-in methods: email+password is enabled alongside them, on the principle that **the method is configuration and the authenticated identity is invariant**. Nothing else in this ADR changes — Better Auth, Casbin, the two providers and the JWT boundary all stand. The text below is left as written, because it recorded what was true then.

- **Better Auth runs in Next.js only.** The FastAPI tier never stores passwords, never implements an OAuth flow, and never mints tokens — it verifies them. See [ADR-0026](0026-jwt-boundary-architecture.md) and [18-authentication.md](../18-authentication.md).
