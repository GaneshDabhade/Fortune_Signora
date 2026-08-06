# ADR-0406: Authentication has three execution modes, and the running one is always visible

## Status

**PRODUCT OWNER DIRECTED — 2026-08-06, [D-131](../../DECISION_REGISTER.md).** Drafted by Lane C on that instruction. **Awaiting ratification.**

> **The directive, verbatim:** *"During development, do not allow missing infrastructure to unnecessarily block UI implementation. However, do not introduce shortcuts that misrepresent production behavior."*

---

## Context

**[C-320](../../LANE_COORDINATION.md) has been open since 2026-08-03 and states the problem exactly:**

> *"Sign-up requires email verification… The link goes to a terminal. **So in every environment this team possesses, including Human Review, a new customer's first hour ends at *"check your email"*.***"

⚡ **And the consequence it drew is the one that matters:** *"every account that has ever existed in Signora was created by `demo-users.ts`… **The front door is fully implemented and has never been walked.**"*

### What is already true, and none of it is a defect

**Measured 2026-08-06 under [D-130](../../DECISION_REGISTER.md) — by reading the implementations, not their names:**

| | |
|---|---|
| **`createEmailTransport`** | Returns a console transport that writes the **real Better Auth link**, with its real token and real expiry, framed so it cannot be missed in a dev server's output. ⚡ ***"Nothing here is mocked."*** |
| **`loadAuthConfig`** | **Refuses to start** when the console transport is selected in a deployed environment — *"a password-reset link written to a production log is a credential sitting in a log file"* |
| **`SIGNORA_ENVIRONMENT`** | Already names the **deployment**, separately from `NODE_ENV`. **Found by the build failing**: `NODE_ENV=production` means *an optimised build*, not *deployed* |
| **`demo-users.ts`** | Creates **real accounts**, mints a **real token**, and redeems it through **`auth.api.verifyEmail`** — *"the route the emailed link resolves"*. **Refuses outside a developer's machine** |
| **`AuthEmailTransportName`** | A union with **one member**, and `createEmailTransport` deliberately carries **no branch** — *"a branch that cannot fail is Decorative Logic, giving the impression of a choice the build cannot make"* |

> ## **All three of the product owner's modes already exist. None of them has a name, and nothing tells you which one is running.**

**That is the whole finding.** The engineering is correct and was correct before this ADR; **what is missing is that the modes are implicit**, and [D-131](../../DECISION_REGISTER.md) requires the opposite: *"A user or developer should always know which mode is active."*

---

## Decision

> ## **Authentication has exactly three execution modes. Each is named, each is explicit, and the active one is observable without reading configuration.**

| Mode | What it is | Transport | Accounts |
|---|---|---|---|
| **Production** | **The complete Better Auth flow against real infrastructure** | ⛔ **A real vendor transport. Does not exist yet** — the one genuine gap | Real, by the front door |
| **Development** | **The flow a developer walks locally.** ✅ **This is today's console transport, named** | Console — **the real link, to stdout** | Real, by the front door |
| **Demo** | **Seeded accounts for demonstration** | Not used — no link is sent | ✅ **`demo-users.ts`, named** |

### 1 · One flow, three configurations — never three implementations

⛔ **This ADR does not add an authentication path.** **Better Auth remains the sole Authentication Authority** (`CLAUDE.md` §13), the Python tier still only verifies RS256, and **every mode walks the same Better Auth flow.** **What varies is where the link goes and whether accounts were seeded — nothing else.**

> ⚡ **The distinction that keeps this safe: a *mode* selects a transport and a seeding policy. A mode never selects an authentication rule.** **`requireEmailVerification` is `true` in all three**, because it is what makes the `email_verified` claim mean anything.

⛔ **And the rule `CLAUDE.md` §13 already states by name stands unchanged: *never add a "skip auth in development" flag*.** **Development Mode is not that flag.** **It delivers the link somewhere a developer can reach; it does not stop requiring the link to be used.**

### 2 · A mode never silently imitates production

**Two obligations, and they point in opposite directions:**

| | |
|---|---|
| ⛔ **A non-production mode must be impossible to mistake for production** | The console transport already refuses to load in a deployed environment, and `demo-users.ts` already refuses outside a developer's machine. **Both guards are kept and neither is weakened** |
| ⛔ **Production must be impossible to run in a non-production configuration** | **The startup refusal is the mechanism**, and it stays a startup failure rather than a runtime one — *"the failure mode of getting this wrong is silent: every flow appears to work and nobody receives anything"* |

⚡ **This is [ADR-0028](0028-model-runtime-by-environment.md)'s guarantee applied to authentication**, and the sentence transfers exactly: *"a production service answering from a deterministic stub is indistinguishable from one that is working — which is strictly worse than the outage it would be hiding."*

### 3 · The active mode is observable, and that is the new requirement

> **The running mode is surfaced to whoever is using the process — not buried in an environment variable somebody has to know to read.**

**Because the failure this prevents is specific: a reviewer walking the first hour cannot currently tell whether they signed in as a seeded demo account or created one.** ⚠️ **Those are different products to review**, and a review of the wrong one is worse than no review, because it is reported as a review.

⛔ **Not decided here: how it is surfaced.** **A banner, a badge, a startup line, a health field — that is a design question and [410](../410-approved-ui-specification.md) is the authority.** **This ADR requires that it is surfaced and refuses to invent the treatment**, which is [D-129](../../DECISION_REGISTER.md)'s rule.

### 4 · Production Mode's transport stays a vendor decision

⛔ **This ADR does not choose an email vendor.** **That is a dependency decision, it is 🔴, and [ADR-0033](0033-authentication-methods.md) already names it as outstanding.**

✅ **What this ADR does settle is that the absence no longer blocks anything but production itself.** **[C-320](../../LANE_COORDINATION.md) asked *"where, and when, does Signora get an email transport — and until then, how does anybody experience a customer's first hour?"*** **The second half is answered: Development Mode, by the front door, with the real link.** **The first half stays with deployment.**

---

## Alternatives

| | | |
|---|---|---|
| **(a)** | **A development-only bypass of verification** | ⛔ **Refused, and it is forbidden by name.** `CLAUDE.md` §13: *never add a "skip auth in development" flag*. ⚡ **It also destroys the thing being reviewed** — the first hour *is* the verification step |
| **(b)** | ✅ **Three named modes over one flow** | **Directed.** **Each mode changes delivery and seeding; none changes an authentication rule** |
| **(c)** | **Wait for a production transport** | ⛔ **This is the status quo, and it has held the review of the product's first hour since 2026-08-03.** **D-131: *do not allow missing infrastructure to unnecessarily block UI implementation*** |
| **(d)** | **A mock Better Auth in development** | ⛔ **Refused.** **A mocked authority is not the authority**, and §13 makes Better Auth the sole one. ⚡ **[ADR-0028](0028-model-runtime-by-environment.md)'s mock exists because a *model* is non-deterministic; an auth flow is not, so the reason does not transfer** |

---

## Consequences

✅ **The front door becomes walkable**, and [TASK-455](../../BACKLOG.md) is the slice that walks it.
✅ **[D-113](../../DECISION_REGISTER.md)'s authentication Playwright journey becomes writable** — a scenario that signs up needs an environment where signing up completes.
⚠️ **Three modes is three things to keep honest**, and the guards are what keep them honest. ⛔ **Weakening either refusal is how this decision turns into the bypass it refused.**
⛔ **Nothing in `backend/` changes.** **The Python tier verifies RS256 and knows nothing about modes** — §13, and it stays that way.

---

## Validation

**Each is checkable rather than asserted:**

**①** `requireEmailVerification` is `true` in every mode — **grep, not review** · **②** no code path issues a session without a Better Auth flow having produced it · **③** `loadAuthConfig` still fails at startup for a console transport in a deployed environment · **④** `demo-users.ts` still refuses outside a developer's machine · **⑤** ⚡ **the running mode is reported by the process, and a test asserts the reported value changes with the configuration** — **the one new guarantee, and the only one that would survive somebody deleting this document.**
