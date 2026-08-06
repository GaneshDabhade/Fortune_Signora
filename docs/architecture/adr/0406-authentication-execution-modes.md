# ADR-0406: Authentication behaviour is environment-invariant; only infrastructure varies

## Status

<<<<<<< HEAD
✅ **PRODUCT OWNER APPROVED — 2026-08-06, [D-134](../../DECISION_REGISTER.md).** *"The direction is correct, and I agree with the architectural approach. TASK-474 is the correct solution."* **Directed by [D-131](../../DECISION_REGISTER.md), expanded by [D-133](../../DECISION_REGISTER.md), approved with the prohibitions in §2a by [D-134](../../DECISION_REGISTER.md).** Drafted by Lane C.
=======
**PRODUCT OWNER DIRECTED — 2026-08-06, [D-131](../../DECISION_REGISTER.md), expanded by [D-133](../../DECISION_REGISTER.md).** Drafted by Lane C on that instruction. **Awaiting ratification.**
>>>>>>> 2a1bcbb4 (D-133 — the Authentication Operating Model, and the front door has never been walked)

> ⚠️ **The register has no `D-132`.** **Recorded rather than silently renumbered** (§2, *a record of what was true then*): this ADR was expanded by the directive labelled D-133, and the gap is noted so a future reader does not go looking for a decision that was never taken.

---

## The governing principle

> ## **Authentication behaviour must be environment-invariant. Only infrastructure may vary across environments.**

**Every rule below is a consequence of that sentence, and where a future question is not answered here, that sentence answers it.**

⛔ **The test to apply to any proposed authentication change: *would this make the backend believe something different because of where it is running?* If yes, it is refused, however convenient.**

---

## Context

**[C-320](../../LANE_COORDINATION.md), open since 2026-08-03:** *"in every environment this team possesses, including Human Review, a new customer's first hour ends at **check your email**."*

### What is already true, measured rather than named

**Read under [D-130](../../DECISION_REGISTER.md) — the implementations, not their titles:**

| | |
|---|---|
| **`createEmailTransport`** | Writes the **real** Better Auth link, real token, real expiry. ⚡ ***"Nothing here is mocked."*** |
| **`loadAuthConfig`** | **Refuses to start** with a console transport in a deployed environment — *"a password-reset link written to a production log is a credential sitting in a log file"* |
| **`SIGNORA_ENVIRONMENT`** | Names the **deployment**, separately from `NODE_ENV`. **Found by the build failing** |
| **`demo-users.ts`** | **Real accounts, real token, redeemed through `auth.api.verifyEmail`** — *"the route the emailed link resolves"*. Refuses outside a developer's machine |
| **`AuthEmailTransportName`** | A **one-member union** with no branch, deliberately — *"a branch that cannot fail is Decorative Logic"* |

> ## **All three modes already exist. None has a name, nothing reports which is running, and no test has ever walked the front door.**

⛔ **The last clause is the measurement that shaped this ADR: `frontend/tests/e2e/` contains 14 authentication tests and *zero* references to sign-up, verify-email, forgot-password or reset-password.** **Every one of them signs in as an account `demo-users.ts` created.** **C-320's *"the front door is fully implemented and has never been walked"* is true of the test suite as well as of the team.**

---

## Decision

### 1 · One authentication implementation

**Better Auth is the sole Authentication Authority** (`CLAUDE.md` §13), and **there is exactly one implementation of it.**

> **Authorization, session management, JWTs, permissions, workspace membership, email-verification rules and every security decision behave identically in every environment.**

⛔ **Environment selection never changes authentication semantics. Changing an environment must never change what the backend believes to be true.**

⚡ **The Python tier makes this structurally true and must stay that way**: it only *verifies* RS256 ([ADR-0026](0026-jwt-boundary-architecture.md)), holds no signing key, and **has no concept of a mode.** **A backend that cannot observe the mode cannot behave differently because of it** — which is the governing principle enforced by construction rather than by discipline.

### 2 · Modes replace infrastructure, never behaviour

| | **Production** | **Development** | **Demo** |
|---|---|---|---|
| **Email transport** | Real provider | **Local mailbox** (§3) | Not exercised |
| **URLs · callbacks** | Real domains, real DNS | Local | Local |
| **External integrations** | Real | Local or absent | Seeded |
| **Accounts** | Created by customers | Created by the developer, **by the front door** | **Seeded** (§4) |

**And in every mode, without exception:**

> **Better Auth issues the token · Better Auth validates the token · email verification remains required · workspace permissions remain enforced · RBAC remains enforced · session handling is unchanged.**

⛔ **`requireEmailVerification` is `true` in all three.** It is what makes the `email_verified` claim mean anything, and a mode that relaxed it would be a mode in which the backend believes something different.

⛔ **`CLAUDE.md` §13 forbids a *"skip auth in development"* flag by name, and this ADR is where somebody would reach for one.** ⚡ **Development Mode is its opposite: it makes the link *reachable*, never *unnecessary*.**

<<<<<<< HEAD
### 2a · Six shortcuts, forbidden by name — [D-134](../../DECISION_REGISTER.md)

> ⚡ **Named individually rather than left to §1's principle, because each is a thing somebody reaches for at a specific moment of frustration, and a general rule loses to a specific temptation.**

| ⛔ **Forbidden** | **The moment it gets proposed** |
|---|---|
| **Automatic email verification** | *"The developer just made this account; obviously it's them."* ⛔ **It deletes the journey being reviewed** |
| **Automatic login after registration** | *"Saves a step."* ⛔ **Production does not do it, so the reviewed flow is not the shipped flow** |
| **Hard-coded verification tokens** | *"A fixed token makes the test deterministic."* ⛔ **Then the test proves a constant, not a flow** |
| **Disabled authorization or permission checks** | *"Seeding is easier without RBAC."* ⛔ **§20e: test data enters the way a customer's data enters** |
| **A mock authentication provider bypassing Better Auth** | *"Just for local."* ⛔ **§13: Better Auth is the *sole* authority. A second authenticator is a second authority** |
| **Any alternative authentication path that would never exist in production** | **The general case, and the one the other five are instances of** |

> ## **Modes may replace infrastructure. They may never replace authentication semantics.**

### 2b · When a journey cannot run locally, the infrastructure is the problem

> ⛔ ***"If you discover a point where the production journey cannot be executed locally without introducing an artificial shortcut, stop and propose architectural alternatives instead of inventing a development-only path."***

**This is an escalation rule with teeth, and it inverts the usual instinct.** ⚡ **The default engineering reflex is to make the blocked thing work; here the blockage is *information*** — it says an infrastructure boundary is in the wrong place, or is missing.

| ✅ **Do** | ⛔ **Do not** |
|---|---|
| **Substitute at an infrastructure boundary** — a transport, a DNS name, a callback URL | **Substitute inside business logic** |
| **Raise it as a coordination item with alternatives, trade-offs and a recommendation** ([§20e](../../../CLAUDE.md), the six fields) | **Invent a development-only path and record it as a limitation** |

> **We always prefer solving the infrastructure problem over weakening the production authentication model.**

=======
>>>>>>> 2a1bcbb4 (D-133 — the Authentication Operating Model, and the front door has never been walked)
### 3 · Development email is a first-class experience, not a `console.log`

> ⚠️ **A console line is a transport, not an experience.** **[D-133](../../DECISION_REGISTER.md) asks for the second, and the difference is what a developer can *do*.**

**A developer must be able to, with no external SMTP provider:**

| | |
|---|---|
| **See every outbound email** | Not only the one just triggered |
| **Inspect the rendered template** | ⚡ **The thing a customer actually receives** — and today nothing renders it at all, so no template has ever been reviewed |
| **Open the verification link** · **the reset link** · **an invitation link** | From the message, as a customer would |
| **Resend** | Without re-running the flow that produced it |
| **Inspect delivery history** | What was sent, to whom, when, and for what purpose |

> ## **It remains a real email pipeline whose final transport is local rather than external.**

⛔ **Not a mock, and the distinction is exact:** **Better Auth still mints the token, still builds the URL, still sets the expiry.** **The only substitution is the last hop.** ⚡ **This is the same shape as [ADR-0028](0028-model-runtime-by-environment.md)'s deterministic provider — *the mock follows the contract; the contract never follows the mock*** — **except that here nothing is even mocked: the pipeline is real and its endpoint is local.**

⚠️ **A stated consequence, because it will be discovered otherwise: delivery history is a record of credentials being issued.** **It is local-only by construction and must never become reachable in a deployed environment** — the same reason `loadAuthConfig` already refuses the console transport there.

### 4 · Demo Mode seeds data and never fakes authentication

> ## **A demo user still logs in through Better Auth.**

**Seeded:** accounts · workspaces · organizations · memberships · AI data.
⛔ **Not seeded, ever:** a session · a token · a verified flag written directly · an authorization decision.

⚡ **`demo-users.ts` already gets this right and is the pattern rather than the exception** — it mints a real token and redeems it through the route the emailed link resolves. **The seeding grows; the discipline does not change.**

⛔ **And §20e still binds: test data enters the way a customer's data enters.** **Seeding is an approved door precisely because it uses the real one.**

### 5 · Production Mode is Development Mode with infrastructure replaced

> **No code path changes. Only configuration changes.**

⚡ **This is a *falsifiable* claim, and it is the strongest guarantee in this document**: if a code path exists that runs in one mode and not another, this principle is violated and the check in *Validation* below finds it. ⛔ **A `if (mode === …)` in an authentication path is the defect this ADR exists to prevent.**

**`createEmailTransport` already demonstrates the shape** — it carries no branch, and adding a vendor adds *a member to a union and a case in one factory*, not a fork through the flow.

### 6 · Seventeen customer journeys, each with a stated readiness

**Every authentication journey must execute successfully in all applicable modes.** **The table below is a *measurable gap analysis*, which is one of the three derived artifacts [D-129](../../DECISION_REGISTER.md) permits** — ⛔ **it is not a conformance checklist and adds no specification.**

**Measured 2026-08-06 against `origin/integration`.**

| # | Journey | Surface | Playwright | Needs | Readiness |
|---|---|---|---|---|---|
| 1 | **Registration** | ✅ `(auth)/sign-up` | ⛔ **none** | Dev email | 🟠 **built, never walked** |
| 2 | **Login** | ✅ `(auth)/sign-in` | ✅ **covered** | — | ✅ |
| 3 | **Logout** | ✅ | ✅ **covered** | — | ✅ |
| 4 | **Email verification** | ✅ `(auth)/verify-email` | ⛔ **none** | Dev email | 🔴 **the blocking one** |
| 5 | **Resend verification** | ✅ `verify-email/resend.tsx` | ⛔ **none** | Dev email | 🟠 |
| 6 | **Forgot password** | ✅ `(auth)/forgot-password` | ⛔ **none** | Dev email | 🟠 |
| 7 | **Reset password** | ✅ `(auth)/reset-password` | ⛔ **none** | Dev email | 🟠 |
| 8 | **Workspace creation** | ✅ `POST /workspaces` | ⚠️ **partial** | — | 🟠 ⚠️ **and [TASK-468](../../BACKLOG.md) replaces the surface entirely** |
| 9 | **Workspace invitation** | ✅ `POST …/invitations` | ⛔ **none** | Dev email | 🟠 |
| 10 | **Workspace acceptance** | ✅ `…/invitations/accept` · `(app)/join/[workspaceId]` | ⚠️ **partial** | Dev email | 🟠 |
| 11 | **Team invitation** | ✅ `settings/team/` · resend · revoke | ⛔ **none** | Dev email | 🟠 |
| 12 | **Session expiration** | ✅ Better Auth | ⚠️ **`resilience.spec.ts`** | — | 🟠 **not asserted as a journey** |
| 13 | **Session renewal** | ✅ Better Auth | ⚠️ **partial** | — | 🟠 |
| 14 | **Multi-tab** | ✅ | ⚠️ **`newPage()` used, not asserted for auth** | — | 🟠 |
| 15 | **Unauthorized access** | ✅ `route-guard.tsx` | ✅ **covered** — 6 paths, token endpoint, key leakage | — | ✅ |
| 16 | **Expired links** | ✅ Better Auth token expiry | ⛔ **none** | Dev email | 🟠 |
| 17 | **Invalid links** | ✅ | ⛔ **none** | Dev email | 🟠 |

> ⚡ **Three of seventeen are green, and the pattern is exact: every journey that needs an email is unwalked, and every journey that does not is covered.** ⛔ **Ten of the fourteen gaps close behind one capability — §3.**

<<<<<<< HEAD
#### 6a · The journey is the planning unit, not the screen — [D-134](../../DECISION_REGISTER.md)

> ⚡ **The seventeen above are *steps*. A customer does not experience a step.** **The unit that gets planned, built, reviewed and demonstrated is the composite journey**, and the four below are the first-class ones.

| Composite journey | Steps it composes | Blocked on |
|---|---|---|
| **Register → Verify Email → Login → Workspace Setup → Onboarding** | 1 · 4 · 2 · 8 · — | **§3** · ⚠️ **and Onboarding does not exist** — [TASK-469](../../BACKLOG.md), no route in `frontend/app/` |
| **Forgot Password → Reset Password → Login** | 6 · 7 · 2 | **§3 alone.** ✅ **Every surface exists** — the shortest of the four to green |
| **Invitation → Accept → Join Workspace → Onboarding** | 9 · 10 · 10 · — | **§3** · **Onboarding** |
| **Team Invitation → New Member Activation → First Login** | 11 · 1/4 · 2 | **§3** |

⚡ **Reading the table as a plan rather than a record: journey 2 is buildable the moment §3 lands, and the other three additionally wait on Onboarding**, which is [TASK-469](../../BACKLOG.md) and behind [C-421](../../LANE_COORDINATION.md).

> ⛔ **Each journey executes through the real backend and the real Better Auth implementation.** **Local simulation occurs only at infrastructure boundaries — the email transport — and never inside business logic** (§2a, §2b).

=======
>>>>>>> 2a1bcbb4 (D-133 — the Authentication Operating Model, and the front door has never been walked)
### 7 · Playwright runs the same tests in every mode

> **The only thing that changes between Development and Production is environment configuration. The tests are identical.**

⛔ **A test that branches on the mode is validating an environment rather than a customer** — and it would silently stop testing production the day the branch was wrong.

⚡ **The suite is already built this way and this ADR must not break it**: `auth-journey.spec.ts`'s *"offers a provider button when one is configured, and nothing when not"* reads configuration to decide **what the customer should see**, never **which assertions to run.**

### 8 · Future enterprise capabilities extend this model

**MFA · passkeys · SAML SSO · OIDC · Google · Microsoft · Okta · Azure AD · SCIM · domain-based IdP routing · conditional access · organization policies.**

> **Each extends the authentication model. None replaces it, and none is designed here** (§2, *do not add abstraction for hypothetical futures*).

**What this ADR guarantees for all of them, and it is the only thing it needs to guarantee:**

| | |
|---|---|
| **They arrive inside Better Auth** | It stays the sole authority — §13. ⛔ **A second authenticator is what this forbids, whatever it authenticates with** |
| **The Python tier still only verifies** | **A new factor or a new IdP changes who gets a token, never who validates one.** ⚡ **[ADR-0026](0026-jwt-boundary-architecture.md) needs no amendment for any item on that list**, which is the evidence the boundary was drawn correctly |
| **They are infrastructure, not behaviour** | **An IdP is a provider.** ⚡ **The existing provider button — *"one when configured, and nothing when not"* — is already this pattern at n=1** |
| **A mode never grants an exemption** | ⛔ **No *"MFA off in development"*.** **It is §13's forbidden flag wearing a newer coat**, and the governing principle refuses it without further argument |

---

## Alternatives

| | | |
|---|---|---|
| **(a)** | **A development-only verification bypass** | ⛔ **Forbidden by name** (§13). ⚡ **And it destroys the subject** — the first hour *is* the verification step |
| **(b)** | ✅ **One implementation, three infrastructure configurations** | **Directed** |
| **(c)** | **Wait for a production transport** | ⛔ **The status quo, and it has blocked review since 2026-08-03** and left ten journeys untested |
| **(d)** | **A mocked Better Auth in development** | ⛔ **A mocked authority is not the authority.** ⚡ **[ADR-0028](0028-model-runtime-by-environment.md)'s mock exists because a *model* is non-deterministic; an auth flow is not, so the reason does not transfer** |
| **(e)** | **A hosted dev SMTP sandbox** | ⛔ **An external operational dependency for local development**, which [D-133](../../DECISION_REGISTER.md) explicitly excludes — *"without requiring an external SMTP provider"* |

---

## Consequences

✅ **Ten of fourteen journey gaps close behind one capability**, and it is buildable locally.
✅ **[D-113](../../DECISION_REGISTER.md)'s authentication journeys become writable** — a scenario that registers needs an environment where registering completes.
✅ **The email templates get reviewed for the first time.** ⚠️ **Nothing renders them today**, so no human has seen what a customer receives.
⚠️ **Three modes is three things to keep honest, and the two existing refusals are what keep them honest.** ⛔ **Weakening either is how this becomes the bypass it refused.**
⛔ **`backend/` changes in no way.** **The Python tier verifies RS256 and has no concept of a mode** — and that is a guarantee, not an omission.

---

## Validation

**Run before the first slice; each is checkable rather than asserted:**

**①** `requireEmailVerification` is `true` on every path — **grep, not review** · **②** ⚡ **no authentication code path branches on the mode or on `SIGNORA_ENVIRONMENT`** — **§5 stated as a check, and the strongest one here** · **③** no code path issues a session that a Better Auth flow did not produce · **④** `loadAuthConfig` still fails at **startup** for a console transport in a deployed environment · **⑤** `demo-users.ts` still refuses outside a developer's machine · **⑥** **the running mode is reported, and a test asserts the reported value *changes with the configuration*** — ⛔ **never that it equals today's value** ([B-130](../../BUGS.md)) · **⑦** **no Playwright spec branches on the mode** · **⑧** **the delivery-history surface is unreachable in a deployed environment**, by the same startup refusal as ④.
