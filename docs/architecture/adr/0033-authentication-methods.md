# ADR-0033: Authentication Methods Are Configuration — Email + Password Alongside OAuth

## Status

**Accepted** — 2026-08-01. Amends [ADR-0010](0010-identity-and-access.md), which stated Google and Microsoft OAuth as the sign-in requirement and recorded email+password as deliberately excluded. ADR-0010 is **not superseded**: Better Auth, Casbin, the two OAuth providers, and the boundary in [ADR-0026](0026-jwt-boundary-architecture.md) all stand unchanged. What changes is that OAuth is no longer the *only* method.

## Context

The product owner asked whether Signora's authentication architecture supports multiple first-class sign-in methods, in the way ChatGPT, Notion, Linear, Stripe, GitHub and Vercel all do — email+password, Google, Microsoft, magic link, enterprise SSO, passkeys — where **the method changes and the authenticated session does not.**

The immediate trigger was product feedback rather than architecture: `/sign-in` offers only Google and Microsoft, neither is configured locally, and the product owner therefore **cannot review the product they are directing.** Every review in [39-product-review-findings.md](../39-product-review-findings.md) carries the same limitation — *"I could not open the browser UI"* — and the standing rule that no screen is complete until a human has reviewed it in the demo environment has been unsatisfiable for five reviews running.

### The architecture was reviewed before anything was proposed. It already supports this.

**The JWT contract names no authentication method, and never did.** [18-authentication.md](../18-authentication.md) fixes the claim set at `sub`, `sid`, `email`, `email_verified`, `jti`, `exp`, `iat`, `iss`, `aud`, plus the optional `active_workspace_id`. There is no `provider`, no `amr`, no `method`. A password sign-in therefore produces a **byte-identical claim set** to a Google sign-in, and the Python tier cannot distinguish them because there is nothing in the token to distinguish.

That is the property this ADR is really about, and it was achieved by *omission* — which is the strongest form. Everything downstream is untouched: verification, membership re-verification, RLS context, Casbin, audit logging, the Security Invariants.

**`email_verified` is already a first-class claim** and is already validated as a boolean by the verifier — and has never meant anything, because an OAuth identity provider always asserts it. Under email+password it becomes a real state with a real flow behind it.

**Method availability is already driven by configuration.** `socialProviders` is populated only from credentials that are actually present, and the sign-in page renders only what is configured. The pattern this ADR needs already exists; it is keyed to the wrong noun.

**The one thing standing in the way is a single config flag** — `emailAndPassword.enabled: false` — carrying a comment that cites ADR-0010. Reversing a ratified decision requires an ADR, which is why this document exists rather than a one-line commit.

### What the review found that does need changing

1. **`configuredProviders()` returns social providers and is used to answer *"can anyone sign in?"***. The health check reports `degraded — no OAuth provider is configured; sign-in is unavailable`. The moment password sign-in works, that report is **false about a healthy install**, which is the class of defect the repository-tells-the-truth principle names.
2. **Verification and password reset both have to deliver a link**, and nothing in the repository can send email. Without a delivery path both flows are dead ends.
3. **The auth pages are the one part of the frontend not built from the design system.** `app/(auth)/sign-in` uses `border-slate-200`, `bg-white`, `text-slate-500` — raw palette utilities forbidden everywhere else. `design-tokens.test.tsx` scans `components/` only, so the **first screen every customer sees** escaped the rule the whole product follows.

## Decision

**Authentication methods are configuration. The authenticated identity is invariant.**

1. **Email + password is enabled in Better Auth**, with `requireEmailVerification: true` and a stated minimum password length. Better Auth owns credential storage, hashing, verification tokens and reset tokens exactly as it owns OAuth — **no authentication logic is written by Signora, and none is duplicated.**

2. **The unit of configuration becomes a *sign-in method*, not an OAuth provider.** `signInMethods()` reports what a human can actually use — `password`, `google`, `microsoft` — and drives both the sign-in page and the health check. This is the only new concept, and it is required by (1) rather than anticipated for (5).

3. **Email delivery is a port with one implementation.** `AuthEmailTransport` is a function type; the shipped transport writes the link to stdout as a structured line. **The flow is real** — real token, real expiry, real Better Auth route; only the transport differs, in the same way a test mints a real token rather than skipping verification.

4. **The console transport refuses to run outside development.** `loadAuthConfig()` throws at startup when `NODE_ENV=production` and no real transport is configured, because a password-reset link printed to a production log is a credential in a log file. This follows the file's existing stance that *authentication config that is wrong is not something to discover in production traffic.*

5. **The token contract is unchanged, and a test now says so.** Nothing is added to the claim set. A frontend contract test asserts the claims a password sign-in mints are exactly the claims an OAuth sign-in mints — so a future author who adds a `provider` claim "for analytics" breaks a test that explains why.

6. **The auth pages are rebuilt from `components/ui` and design tokens**, and `design-tokens.test.tsx` is extended to cover `app/(auth)`. This is a defect fix under [CLAUDE.md §20c](../../../CLAUDE.md), not a foundation change: the rule already applied and the enforcement did not reach.

### What is deliberately *not* decided here

**Magic link, enterprise SSO, SCIM and passkeys are not built.** They are named because the shape above must not obstruct them, and it does not: each is a Better Auth capability that adds a method and touches nothing downstream. **Naming a future is not the same as building for it** — no abstraction here exists for a method that does not ship today.

**No production email provider is chosen.** That needs a vendor decision and a new dependency, which is its own ADR. The port is what lets that arrive without touching a flow.

## Alternatives Considered

| | Alternative | Verdict |
|---|---|---|
| **A** | Enable `emailAndPassword` and change nothing else | **Rejected.** It works, and it leaves the health check lying about a healthy install and both email flows as dead ends. The flag is the small part |
| **B** | A development-only sign-in bypass | **Rejected, and explicitly ruled out by the product owner.** [18-authentication.md](../18-authentication.md) already names *"a skip auth in development flag"* as an anti-pattern: it diverges the test path from production and inevitably reaches production. It would also fail to give what was asked for — the point is to **exercise the customer's journey**, and a bypass exercises nothing |
| **C** | A seeded test user created by a script | **Rejected.** It gives a session without a sign-up, so registration, verification and reset stay unexercised and unreviewed — the flows most likely to be wrong. It also puts a credential in the repository |
| **D** | An identity abstraction layer over Better Auth | **Rejected.** Better Auth *is* the abstraction; wrapping it would duplicate authentication logic, which ADR-0010 bought a vendor specifically to avoid. The provider/AI/integration abstraction layers exist because those markets have many interchangeable vendors — the Authentication Authority is deliberately singular |
| **E** | Add a `provider` or `amr` claim so the backend knows how someone signed in | **Rejected, and this is the load-bearing rejection.** Business behaviour must not depend on how a user authenticated. A claim the backend can read is a claim the backend can branch on, and the first branch would be a security decision keyed to a method rather than to a policy. The same reasoning as vendor neutrality in the AI Platform: **identity is recorded as provenance, never consulted for a decision** — and here it is not even recorded |
| **F** | Email+password in development, OAuth-only in production | **Rejected.** Two authentication architectures, one of them unreviewed. Multiple methods are what the real product should offer; making it a dev-only affordance would be a bypass with better manners |

## Tradeoffs

| Choice | We gain | We give up |
|---|---|---|
| Email+password as a first-class method | The product owner can review the product · the customer journey is exercised end to end · the ICP is no longer assumed to have a Google or Microsoft account | Credential storage and breach exposure, which ADR-0010 accepted a narrower surface to avoid. Better Auth carries it; Signora does not implement it |
| `requireEmailVerification: true` | `email_verified` becomes a fact rather than an OAuth assertion nobody checked | An extra step in the local review loop — the link is in the dev server output |
| An email port with a console transport | Both flows are real today, with no new dependency and no vendor decision taken under time pressure | Nothing can email a real customer until a provider is chosen |
| Method-agnostic token | Every future method is free downstream — no migration, no claim change, no backend release | The backend genuinely cannot tell a password user from an SSO user. **This is the feature** |

## Risks

- **A password reset link reaching a production log.** Mitigated by a startup failure rather than a runtime check: the console transport cannot be selected in production, and a misconfiguration stops the process rather than quietly emailing nobody.
- **Weak passwords.** Mitigated by a stated minimum length enforced by Better Auth. Signora writes no hashing, no comparison and no timing-sensitive code — that surface belongs to the vendor, which is why the vendor was bought.
- **Enumeration through the reset flow.** Better Auth's `forgetPassword` responds identically whether or not the address exists; the UI must not add a message that distinguishes them. Asserted by a test.
- **The dev transport becoming the production plan by inertia.** Mitigated by (4) and by this ADR naming the provider decision as outstanding.

## Migration Strategy

Reversing this is one flag and one config value: `emailAndPassword.enabled: false` removes the method, and `signInMethods()` stops reporting it — the sign-in page and health check follow automatically, because both read the same function. Existing password users would lose their sign-in method and would need to link an OAuth identity, which is the only irreversible part and the reason the decision is recorded rather than assumed.

Nothing downstream would change, because nothing downstream knows.

## Consequences

- [18-authentication.md](../18-authentication.md) gains a section stating that the method is not in the token, and that this is the property that makes every future method free.
- [ADR-0010](0010-identity-and-access.md) gains a pointer here. Its own text is **not edited** — it recorded what was true then.
- The health check's `oauth_providers` becomes `sign_in_methods`. The e2e journey asserts the new name.
- `design-tokens.test.tsx` covers `app/(auth)`, closing a gap that predates it.
- **A production email provider is now an outstanding decision with a stated trigger:** the first environment that is not a developer's machine.
