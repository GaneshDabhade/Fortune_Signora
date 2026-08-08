# 496 · The Signora security architecture — a ten-year blueprint

**Lane C, as Chief Architect · 2026-08-08.** **[D-177](../DECISION_REGISTER.md), which asks for a blueprint rather than a library comparison.**

> ⚡ **Sources: 📁 repository · 🌐 research · 🧠 judgement.**

---

## 0 · The one idea this blueprint turns on

**Every previous package asked *"which authorization engine?"* — including mine. That question has no good answer because it presumes one engine.**

> ## ⚡ **Authorization is not one question. It is three, and they have different shapes, different data, different latency and different owners.**

| | The question | Shape | Answered by |
|---|---|---|---|
| **① Capability** | ***"May this kind of principal do this kind of thing?"*** | **A small static matrix. Microseconds. In-process** | ✅ **Casbin today. Cedar if it is ever re-let** |
| **② Relationship** | ***"May this principal touch this specific object?"*** | **A graph of millions of edges. A store** | ✅ **Row-Level Security today. OpenFGA or SpiceDB when sharing arrives** |
| **③ ⚡ Quota** | ***"May this principal spend this?"*** | **A counter with a limit and a window** | 🔴 **Nothing. It does not exist in any engine on the list** |

⛔ **RBAC, ABAC and ReBAC all answer boolean questions. *"May the agent call the model"* and *"may the agent call the model five hundred more times this month"* are different questions, and every authorization product named in [D-177](../DECISION_REGISTER.md) answers only the first.**

📁 **Signora already knows this and has not named it.** **`Resource.RESEARCH` exists because *"reading an account is free and asking for research spends a model call, and one resource could not express both."*** **`TASK-424` is *"a workspace has an AI budget."*** ⚡ **Two artifacts circling a third authorization primitive nobody has written down.**

> ## 🔴 **The most important architectural finding in this package: an AI-native platform needs a *quantitative* authorization dimension, and it is the one thing no vendor supplies. It is therefore, by definition, Signora's.**

---

## 1 · 🌐 What the industry actually did, and why

| | | Why it matters here |
|---|---|---|
| **OpenFGA** | **CNCF, Zanzibar ReBAC, DSL, `check`/`list-objects`/`expand`** | ⚡ **`list-objects` is the capability RLS cannot give: *"which accounts may this seller see?"* answered by the store** |
| **SpiceDB** | **gRPC, strong consistency via ZedTokens.** 🌐 ***OpenAI uses SpiceDB for ChatGPT Enterprise connectors, tens of billions of permissions*** | 🔴 **The closest analogue to Signora that exists: an AI-native enterprise product, per-object permissions over connected customer data** |
| **Cedar** | **Declarative, *formally verified*, 28–35× faster than OpenFGA and 42–80× faster than Rego** | ⚡ **Formal verification is a real property for a security foundation, and nothing else on the list has it** |
| **Cerbos · OPA** | **Policy-as-code, ABAC** | **Externalised policy; another service** |
| **Oso · Casbin** | **Embedded libraries** | 📁 **What Signora runs** |
| **Keycloak · Permit.io · Auth0 FGA** | **Hosted platforms** | ⛔ **Each imports a tenancy model, which is the thing [D-175](494-authorization-architecture.md) established Signora must not do** |

> ## 🧠 **The pattern behind every one of these choices: the large platforms did not pick an engine — they *split the layers*, and put a Zanzibar store under the object question while keeping something small and fast for the capability question.** ⚡ **That is not a compromise; it is the shape of the problem.**

---

## 2 · The blueprint

### 2.1 · One seam, and it already exists

📁 **`signora_platform/authorization/enforcer.py` is a single port. `Resource` and the action vocabulary are Signora's, not Casbin's. `jwt.ts:85` refuses to put permissions in the token.**

> ## ✅ **Three decisions already made correctly, and together they are the whole extensibility story. Everything below plugs into that seam.**

### 2.2 · The layers, and their permanent owners

| Layer | Owner | Now | At maturity |
|---|---|---|---|
| **Identity · authentication · sessions · MFA · passkeys · SSO · SCIM · credential lifecycle** | 🌐 **Better Auth** | **Plugins unadopted** | **Adopted. ⛔ Never its authorization** |
| **① Capability authorization** | 📁 **Signora, via Casbin behind the port** | **53 lines** | ⚡ **Same shape. Cedar is the successor *if* formal verification ever becomes a buying requirement** |
| **② Relationship authorization** | 📁 **PostgreSQL RLS** | **Sufficient** | ⚡ **OpenFGA behind the same port, *only* when per-object sharing arrives** |
| **③ 🔴 Quota authorization** | 🔴 **Signora. Nobody else has it** | **Does not exist** | ⚡ **A first-class primitive beside capability** |
| **Tenancy** | 📁 **Signora — the workspace, under RLS** | ✅ **Correct** | **Unchanged. ⛔ The one thing never delegated** |
| **Principal model** | 🔴 **Signora** | ⛔ **Human-only** | ✅ **§3 below** |
| **Audit · security events · risk** | 🔴 **Signora** | **`membership_role_change` alone** | **[TASK-492](../BACKLOG.md)** |

---

## 3 · 🔴 AI-first authorization — the part that is genuinely different

**Traditional SaaS authorizes a human who is present. Signora authorizes an agent that acts while nobody is watching. Three properties follow, and none is in an off-the-shelf model.**

### ① Attenuation — authority may only narrow along a chain

> ## **A principal's effective permission is the *intersection* of its own grant and every principal it acts for, transitively.**

⛔ **Agent-to-agent must never *widen*.** ⚡ **This is capability-security thinking — macaroons, not roles — and it is one clause in a matcher: `r.sub ⊆ r.acting_for`.** ⛔ **In a role model it is unrepresentable, because roles compose by union.**

### ② Quota — the third question

**An agent's dangerous permissions are *spending* permissions: model calls, research, external connectors, writes to a customer's CRM.** ⛔ **A boolean cannot express *"may spend, up to here, in this window."***

| | |
|---|---|
| **The primitive** | **`(principal, resource, limit, window, consumed)`** — **workspace-tenanted, person-attributable** |
| ⚡ **Why it is authorization and not metering** | **It must be checked *before* the act, deny in the same shape as a permission denial, and appear in the same audit line.** ⛔ **Metering that reports after the fact is billing, not authorization** |
| 📁 **What already exists** | **`Resource.RESEARCH` · `TASK-424` · `TASK-411`/`412` usage accounting.** ⚡ **Three artifacts, one missing primitive** |

### ③ Attribution — every act names two identities

⛔ **An action taken by an agent for a person must record *both*, always.** ⚡ **An audit line naming only the agent cannot answer *"who authorised this?"*; one naming only the human is a lie.** ✅ **`subject_id` + `acting_for` in every security event — which is why [TASK-492](../BACKLOG.md) precedes the agent work rather than following it.**

---

## 4 · Why each second-best was rejected

| Decision | Second-best | Why rejected |
|---|---|---|
| **Capability: Casbin** | **Cedar** | ⚡ **Genuinely better — formally verified, far faster.** ⛔ **Rejected on *timing*: it is a migration for no capability Signora needs today, and the port makes it cheap later.** ✅ **The trigger is explicit: adopt Cedar if formal verification becomes a buying requirement or the matrix passes ~500 rules** |
| **Relationship: RLS now** | **OpenFGA now** | ⛔ **Rejected on [§3](../../CLAUDE.md) Principle 6 — one PostgreSQL database — and because no product requirement needs `list-objects` yet.** ⚠️ **Accepting the risk that RLS and a policy matrix both become insufficient on the same day** |
| **Relationship at maturity: OpenFGA** | **SpiceDB** | ⚡ **SpiceDB is the stronger engine and has the closest precedent — OpenAI's connectors.** ✅ **OpenFGA is recommended on CNCF governance and the gentler operational profile; ⚠️ if strong consistency across regions becomes a requirement, SpiceDB wins and the port makes that swap the same cost** |
| **Identity: Better Auth** | **Keycloak** | ⛔ **Rejected because it imports an organization/realm tenancy model, and Signora's unit is the workspace** |
| **Quota: build** | **Reuse** | ⛔ **Nothing to reuse. Every product on the list answers boolean questions** |

---

## 5 · ⚠️ Attempting to invalidate this blueprint

**Assume an experienced architect disagrees. The three strongest attacks:**

| | Attack | Response |
|---|---|---|
| **①** | ***"You are inventing a third authorization primitive. Quota is rate limiting, and rate limiting is infrastructure."*** | ⚡ **The strongest attack.** ⛔ **It fails on *attribution and scope*: a rate limit is per-caller-per-endpoint and stateless; an AI budget is per-workspace-per-resource-per-billing-period and must survive restarts, appear in audit, and be *delegable* — an agent inherits a slice of its owner's budget.** ⚠️ **Conceded: the *enforcement* mechanism may well be an existing counter store. The *model* is not infrastructure's** |
| **②** | ***"Three layers is three things to reason about. One engine — OpenFGA — does capability and relationship, and you have chosen complexity."*** | ⚠️ **Partially lands.** ✅ **OpenFGA can express role checks.** ⛔ **But it is a network hop for a question answered today in microseconds in-process, and it does not answer quota either — so it removes one layer of three and adds a service.** 🧠 **Revisit if the capability matrix ever needs relationship data to evaluate** |
| **③** | ***"Deferring OpenFGA is the same mistake as deferring the design tokens: identified, published, never scheduled — and then a lane pays for it."*** | 🔴 **This lands hardest because it is this office's own recent failure.** ✅ **The mitigation is that the trigger is *a product requirement*, not a date: the first design that shows one person sharing one record with another.** ⛔ **No such screen exists in the twenty-six** |

> ## ✅ **The blueprint survives, and attack ③ improves it: the OpenFGA trigger is written into [`workflows.toml`](../coordination/workflows.toml) as a watched condition rather than left in a document.**

---

## 6 · Migration and evolution strategy

| | |
|---|---|
| ✅ **Already done** | **One enforcer port · Signora-owned `Resource` vocabulary · no permissions in the JWT · RLS as the row filter** |
| **Next** | **The principal model ([495](495-principal-and-identity-boundary.md)) · the security event stream ([TASK-492](../BACKLOG.md)) · Better Auth plugins ([TASK-493](../BACKLOG.md))** |
| **Then** | **Quota as a first-class primitive · `policy.csv` → database adapter, when a customer defines a role** |
| **On trigger** | **OpenFGA behind the port, when per-object sharing appears in a design** |
| ⛔ **Never** | **Better Auth's organization roles · permissions in tokens · a second tenancy unit · authorization outside the port** |

---

## 7 · 🧠 The recommendation, in one paragraph

> ## **Better Auth owns identity and never authorization. Signora owns tenancy, the principal model, audit and risk — permanently. Authorization is three questions behind one port: capability, answered by Casbin today and Cedar if verification is ever bought; relationship, answered by Row-Level Security today and OpenFGA when a design first shows one person sharing one record; and quota, which no vendor supplies and which an AI-native platform cannot do without.**
>
> ## ⚡ **The decision that matters is not which engine. It is the port, the workspace as the tenancy unit, and a principal model where authority only ever narrows. Those three make every later engine choice reversible — which is the only honest way to make a ten-year decision.**
