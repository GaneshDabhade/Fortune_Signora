# 497 · Commodity versus differentiation — the doctrine exists, and it is half-adopted

**Lane C · Product Office · 2026-08-08.** **[D-178](../DECISION_REGISTER.md), which asks for a build-versus-reuse philosophy for the whole product.**

> ## ⚡ **The philosophy already exists, ratified, with the exact test [D-178](../DECISION_REGISTER.md) §1 proposes.**
>
> 📁 **`09-build-vs-buy.md`, *Living document — Architectural Constitution — RATIFIED*:** ***"Build it only if it is Signora's competitive advantage. Buy it if a mature vendor already solves it well."***

⛔ **So this document does not propose a philosophy. It grades the one that exists against six months of implementation, and reports what that measurement found.**

---

## 0 · The three findings

> ## 🔴 **① Eight of twelve ratified *buy* decisions have not been adopted — and where one is unadopted, the workflow that needs it is blocked or building around it.**
>
> ## ⚡ **② The doctrine's rows are *products*, not *capabilities* — which is exactly the granularity [D-178](../DECISION_REGISTER.md) §4 asks to fix, and it is why *"Authorization → Casbin"* hid a capability with no vendor at all.**
>
> ## ✅ **③ Every *build* decision has aged well. Not one of the thirteen has been regretted. The doctrine's failure mode is under-buying, not over-building.**

---

## 1 · 📁 Adoption, measured against the ratified table

| Ratified | Vendor | Adopted? |
|---|---|---|
| **Authentication** | **Better Auth** | ✅ |
| **Authorization** | **Casbin** | ✅ |
| **Monitoring** | **OpenTelemetry · Sentry** | ✅ |
| **Background queue** | **Redis · ARQ** | ✅ |
| **Object storage** | **MinIO** | ⚠️ **In the dev compose file; not in either manifest** |
| **Billing** | **Stripe** | ⛔ |
| **Notifications** | **Novu** | ⛔ |
| **Email** | **Resend** | ⛔ |
| **Search** | **Meilisearch** | ⛔ |
| **Analytics** | **PostHog** | ⛔ |
| **Feature flags** | **Flagsmith** | ⛔ |
| **Workflow orchestration** | **Temporal** | ⛔ |

⚠️ **Unadopted is not wrong — most are simply not needed yet, and [§6](../../CLAUDE.md) forbids adding a dependency before the requirement exists.** ⛔ **What is wrong is when a workflow is *blocked* while the vendor that would unblock it sits ratified and unbought.**

### 🔴 Three cases where that is happening now

| | |
|---|---|
| **Notifications** | 📁 **Workflow 17 was blocked until yesterday on *"ADR-0040 unratified"*.** ⚡ **Novu was ratified as the notification vendor in `09`.** ⛔ **The blocked question was about *delivery infrastructure* — the outbox, relay, dispatch, idempotency, dead-lettering — which is the part `09` already says not to build** |
| **Email** | 📁 **`lib/auth/email.ts` is a port with one implementation, and its own comment says *"what arrives later is a vendor."*** ⚡ **Resend is ratified.** ⛔ **[TASK-474](../BACKLOG.md) — the developer mailbox — exists because no vendor is wired, and it currently gates Workflows 3, 4 and 5** |
| **Search** | 📁 **Workflow 16 is Global Search.** ⚡ **Meilisearch is ratified, unadopted, and the workflow is undecomposed** |

> ## ⚡ **The pattern: a *"buy"* decision that is ratified but unbought behaves exactly like an *unmade* decision — a lane reaches the capability and builds around it, because nothing in the queue says a vendor is already chosen.**

⛔ **This is the same class as [TASK-490](../BACKLOG.md): the answer existed, in a document, and no row carried it.**

---

## 2 · ⚡ The doctrine's real gap — granularity

**`09` has one row per *product*. [D-178](../DECISION_REGISTER.md) §4 asks for one row per *capability*, and the difference is not cosmetic.**

📁 **`09` says *Authorization → Casbin*.** ⛔ **[496](496-security-architecture-blueprint.md) established that authorization is three questions:**

| | Doctrine says | Reality |
|---|---|---|
| **Capability authorization** | **Buy — Casbin** | ✅ **Correct** |
| **Relationship authorization** | *(not a row)* | ⚡ **Bought without noticing — it is PostgreSQL RLS** |
| **Quota authorization** | *(not a row)* | 🔴 **No vendor exists. It is a *build* the doctrine never classified** |

> ## ⛔ **A product-level row can hide a capability with no vendor. That is how *"we buy authorization"* coexisted with an unclassified build.**

✅ **The correction is [D-178](../DECISION_REGISTER.md) §8's three-way classification, and it should replace `09`'s two columns rather than sit beside them.**

---

## 3 · The classification applied

**Commodity · Platform · Domain, for the capabilities [D-178](../DECISION_REGISTER.md) §4 lists.**

### ⛔ Commodity — reuse, and the burden of proof is on building

**Authentication · sessions · OAuth · OIDC · SAML · SSO · SCIM · directory sync · MFA · passkeys · password policy · credential lifecycle · provisioning · impersonation · email delivery · notification delivery · search infrastructure · object storage · job queues · feature flags · analytics · billing.**

⚡ **Every one is a solved, security-critical or reputation-critical problem where years of hardening are the product.** 🌐 **The passkey case is the clearest: building WebAuthn is building cryptography.**

### ✅ Platform — Signora owns because the architecture depends on it

**Tenancy · the principal model · workspace membership · policy evaluation *interface* · the security event stream · the enforcer port · the module boundary · the provider port · the AI provider port.**

⚡ **The test that separates these from commodity is not difficulty — it is *coupling*.** ⛔ **Each is consumed by every module, so a vendor here imports a vendor's model of the product into every module.** 📁 **That is why [D-175](494-authorization-architecture.md) refused Better Auth's organization roles: not because they are bad, but because adopting them imports its tenancy unit everywhere.**

### 🔴 Domain — Signora's IP, never delegated

**Knowledge graph · provider normalization · observation engine · business events · signal engine · buying score · opportunity engine · AI research · AI reasoning · revenue intelligence — and, newly classified: AI authorization · AI budgets and quota · agent delegation · risk signals · workspace security analytics.**

> ## ⚡ **The five new ones share a property: they are *authorization about AI*, and no vendor sells them because no vendor has the domain.** ⛔ **Quota is the sharpest — every product in [D-178](../DECISION_REGISTER.md) §3 answers boolean questions, and *"may spend up to here"* is not boolean.**

---

## 4 · §6 — justifying every *build*

| Build | Mature alternative? | Why insufficient | Cost accepted |
|---|---|---|---|
| **Quota / AI budget** | ⛔ **None.** **Rate limiters are per-endpoint and stateless** | **Must be workspace-scoped, billing-period-windowed, delegable to an agent, and denied in the same shape as a permission** | **A counter store and an enforcer clause. ⚡ Small** |
| **Agent delegation / attenuation** | **Macaroons · biscuits** | ⚡ **Genuinely close, and worth revisiting.** ⛔ **Both are token formats; Signora's authority lives server-side in Casbin, and adopting a token format would put permissions in tokens — which `jwt.ts:85` refuses on purpose** | **One matcher clause** |
| **Security event stream** | **Novu · Sentry · SIEM products** | ⛔ **Those *transport* events. The stream is a workspace-tenanted immutable record with two-identity attribution — a domain artifact** | **One append-only table** |
| **Risk signals** | **Auth0 Detection · Keycloak** | ⛔ **They score *authentication* risk. Signora's differentiator is scoring risk *over a customer's revenue data*, which no vendor can see** | **A signal catalogue, reusing the existing pipeline** |
| **Tenancy / principal model** | **Keycloak realms · Better Auth organizations** | ⛔ **Both import a tenancy unit; Signora's is the workspace, enforced by RLS** | **Already built** |

---

## 5 · §7 — challenging the *reuse* assumption honestly

| Reuse | What we lose | When to replace |
|---|---|---|
| **Better Auth** | ⚠️ **Its schema, its migration cadence, and its idea of an *organization*.** 📁 **Mitigated: `authSchema` isolates it and the Python tier only verifies RS256** | ⛔ **If it ever requires its organization model to use its identity plugins** |
| **Casbin** | **Little — 53 lines behind a port** | **[496](496-security-architecture-blueprint.md)'s watched triggers** |
| **Novu · Resend · Meilisearch** | ⚠️ **Deliverability, ranking and delivery semantics become someone else's roadmap** | ⛔ **Only if the *ranking* becomes domain IP — plausible for search over a customer's own accounts, and worth watching** |
| **Stripe** | **Pricing-model flexibility bounded by its primitives** | ⚡ **Usage-based AI billing is where this binds first; [TASK-411](../BACKLOG.md)/[412](../BACKLOG.md) already own the *metering*, which is the right split** |

---

## 6 · ⚠️ Attempting to invalidate this

| | Attack | Response |
|---|---|---|
| **①** | ***"You are grading a doctrine instead of writing one. D-178 asked for an architecture."*** | ⛔ **Fails.** ⚡ **Writing a second philosophy while a ratified one exists would create the two-authorities defect this office has reported four times this week.** ✅ **The deliverable is the amendment: product rows become capability rows, and two categories become three** |
| **②** | ***"Eight unadopted vendors is prudence, not a defect — you said yourself not to add dependencies early."*** | ⚠️ **Lands for five of the eight.** ⛔ **Fails for the three where a workflow is blocked or a lane built a workaround: email, notifications, search.** ✅ **The distinction is whether a *requirement has arrived*, and for those three it has** |
| **③** | ***"Quota is not authorization. You are inflating a counter into an architectural primitive to justify building something."*** | ⚡ **The strongest attack, and it was made against [496](496-security-architecture-blueprint.md) too.** ⛔ **It fails on *delegation*: a rate limit cannot be split between a human and the agent acting for them, and that split is the whole AI-budget requirement.** ⚠️ **Conceded again: the *storage* is a counter and should reuse one** |

---

## 7 · The recommendation

> ## ✅ **Amend `09-build-vs-buy.md` rather than replace it: one row per *capability*, three categories instead of two, and a column recording whether the decision is *adopted* — because a ratified-but-unbought decision behaves exactly like an unmade one.**
>
> ## 🔴 **And treat the three blocked cases as rows, not as findings: email, notifications and search each have a ratified vendor and a workflow waiting.**
>
> ## ⚡ **The philosophy needs no change. Its granularity and its follow-through do.**

⛔ **The doctrine's failure mode is not over-building — thirteen build decisions, none regretted.** ⚡ **It is under-buying: deciding to buy, recording it, and then meeting the capability again in a workflow that has no idea the decision was already made.**
