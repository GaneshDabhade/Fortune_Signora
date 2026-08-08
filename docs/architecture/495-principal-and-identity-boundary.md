# 495 · The principal model, the identity boundary, and an attempt to disprove Casbin

**Lane C · Product Office · 2026-08-08.** **[D-176](../DECISION_REGISTER.md) — the final due diligence before authorization is ratified.**

> ⚡ **Sources labelled: 📁 repository evidence · 🌐 external research · 🧠 judgement.**

---

## 0 · The answer to §6 first, because it is the one that decides ratification

**Three attempts to disprove *"Casbin only"*. Two failed. One partially succeeded and the recommendation is amended rather than defended.**

| | Attack | Outcome |
|---|---|---|
| **①** | ***"Authorization must also happen in the Next.js tier, so there are already two evaluators."*** | ⛔ **Fails.** 📁 **`frontend/lib/auth/jwt.ts:85`: *"Deliberately carries no permission or capability claims. Casbin is the single source of authorization truth (ADR-0010)."*** **And [§20c](../../CLAUDE.md) makes client checks presentational.** ⚡ **The architecture closed this before it was attacked** |
| **②** | ***"Casbin cannot do object-level permission at scale, so it will be replaced anyway."*** | ⛔ **Fails as an argument against Casbin.** ⚡ **`policy.csv` per object would explode — but 📁 Signora answers *"which rows may this caller see?"* with Row-Level Security, not with the policy engine.** **Object-level *filtering* is PostgreSQL's; object-level *sharing* is the day OpenFGA is considered** |
| **③** | ⚡ ***"Custom roles need a database adapter, so 'no migration' is false."*** | ✅ **PARTIALLY SUCCEEDS, and the recommendation is amended** |

### ⚠️ Attack ③, conceded

**[D-175](../DECISION_REGISTER.md) claimed Casbin-only costs no migration. That is true of the *engine* and false of the *storage*.**

📁 **`policy.csv` is a file in the repository. Customer-defined roles — §1's *"Custom Roles"*, *"Permission Templates"*, *"Customer-specific Security Policies"* — cannot live in a file, because a customer cannot commit to this repository.**

> ## ⛔ **So one migration is certain under every option: `policy.csv` → a Casbin database adapter.** ✅ **It is a *storage* change rather than an architecture change, the adapter is first-party, and the model file is untouched — but it is not free and [D-175](../DECISION_REGISTER.md) implied it was.**

⚡ **The recommendation survives, because the same requirement under Better Auth is `dynamicAccessControl` plus its `organizationRole` table — the same migration, into a model that then cannot express the other three demands.** ⛔ **The claim that changes is "no migration", not "Casbin".**

---

## 1 · 🧠 The principal model — the actual deliverable

**📁 Today: `AuthenticatedPrincipal` has `user_id`, `session_id`, `email`, `email_verified`, `active_workspace_id`, `token_id`. Every field is human, and every non-human caller in [D-176](../DECISION_REGISTER.md) §1 is unrepresentable.**

### The shape

> ## **One principal type. A `kind`. A `subject_id`. A workspace. And — the field that does the real work — `acting_for`.**

| Field | Why |
|---|---|
| **`kind`** | **`HUMAN` · `SERVICE_ACCOUNT` · `AGENT` · `API_KEY` · `PAT` · `OAUTH_CLIENT` · `EXTENSION` · `AUTOMATION` · `JOB`** |
| **`subject_id`** | **The stable identity. For a human, Better Auth's `sub`. For everything else, a Signora-issued id** |
| **`workspace_id`** | ⛔ **Non-nullable for every non-human kind.** ⚡ **A machine identity that is not workspace-scoped is a cross-tenant credential, and [§11](../../CLAUDE.md) has no category for one** |
| **`owner_user_id`** | **Every machine principal is *owned* by a human.** ⚡ **This is what makes revocation on offboarding tractable and audit attributable** |
| ⚡ **`acting_for`** | **The human on whose behalf a machine is acting, when there is one.** ⛔ **The field the whole model exists for** |

### ⚡ The rule that makes agents safe, and it is one line

> ## **A principal's effective permission is the *intersection* of its own grant and the grant of the principal it acts for.**

📁 **`Resource.RESEARCH` exists because *"reading an account is free and asking for research spends a model call, and one resource could not express both."*** ✅ **Intersection is what expresses *"the agent may read but not spend"* without a second policy language: the agent's grant omits `RESEARCH`, the human's includes it, and the intersection decides.**

⛔ **Union would be a privilege-escalation primitive.** ⚠️ **And Better Auth's organization plugin already reaches for the weaker version of this rule — 🌐 *"cannot add permissions exceeding caller's own permission set"* — which is intersection at *grant* time rather than at *evaluation* time.** ⚡ **Evaluation-time is the correct one: a human's permissions can be reduced after an agent is created.**

### Lifecycle, per kind

| | Human | Machine kinds |
|---|---|---|
| **Authentication** | 🌐 **Better Auth** — password, OAuth, passkey, MFA, SSO | 🧠 **Signora-issued credential, verified by the same RS256 boundary** ([ADR-0026](adr/0026-jwt-boundary-architecture.md)) |
| **Authorization** | **Casbin, `sub` = role** | ⚡ **Casbin, `sub` = the principal's own role — *no new mechanism*** |
| **Audit identity** | `user_id` | ⛔ **`subject_id` *and* `acting_for` — both, always.** **An action taken by an agent for a person must name both or the audit is a lie** |
| **Revocation** | **Session revocation** | **Credential revocation, ⚡ *plus* cascade when `owner_user_id` leaves the workspace** |
| **Rotation** | **Password / passkey** | **Credential rotation with an overlap window** |
| **Impersonation** | ⛔ **Better Auth's admin plugin can impersonate.** ⚠️ **If adopted, an impersonated session must set `acting_for` and be marked in the audit — an unmarked impersonation is indistinguishable from the person acting** |

---

## 2 · The identity boundary — explicit, as §2 asks

| 🌐 **Better Auth owns, permanently** | 📁 **Signora owns, permanently** |
|---|---|
| **Authentication · sessions · human identities · OAuth and social providers · MFA · passkeys · SSO and SAML · credential lifecycle · email verification · password reset and policy enforcement · session revocation *mechanism*** | **Authorization · tenancy · the principal model · workspace membership · permission definition · policy evaluation · audit · security intelligence · risk signals · machine credentials · the *meaning* of a trusted device** |

> ## ⚡ **The seam, in one sentence: Better Auth answers *"who is this?"* and Signora answers *"what may they do here?"*** ⛔ **Every capability that needs the word *here* — a workspace — is Signora's, because Better Auth's unit is the organization and Signora's is the workspace.**

---

## 3 · 🧠 Can Casbin reach maturity? — §3, honestly

| Requirement | Verdict |
|---|---|
| **ABAC · contextual · temporary** | ✅ **A matcher edit. `model.conf` reads request attributes; `r.time < p.expires` is one clause** |
| **Object-level** | ⚠️ **Yes via `keyMatch` or an id in `obj` — ⛔ but *policy-per-object does not scale*.** ✅ **Signora does not need it to: RLS filters rows** |
| **Delegated · AI agent** | ✅ **Falls out of the principal model, not the engine — intersection is evaluated in the enforcer, once** |
| **Policy inheritance** | ✅ **`g` and `g2` grouping policies. Not configured today and not needed today** |
| **Dynamic · customer-defined** | ⚠️ **Needs the database adapter — attack ③** |

> ## ⛔ **The one material limit: per-object policy rows at scale.** ⚡ **It becomes material the day a customer shares a single opportunity with one person outside the team — and on that day RLS stops being sufficient too, so the two limits arrive together and are answered together.**

---

## 4 · Migration risk, and what to do today

| | |
|---|---|
| **If we stay on Casbin** | ⛔ **Nothing becomes difficult.** ⚠️ **One migration is certain: `policy.csv` → adapter** |
| **If we later leave Casbin** | ⚡ **Cheap, *if* the enforcer stays a port.** 📁 **It already is — `signora_platform/authorization/enforcer.py` is the single call site** |
| ✅ **If we later adopt OpenFGA** | **Two things done today make it a swap rather than a rewrite: ① every authorization decision goes through the one enforcer port; ② `Resource` and the action vocabulary stay Signora's, not Casbin's** |

> ## ⚡ **Both are already true. The preparation §4 asks for is *already in the repository* — which is the strongest evidence that the boundary is drawn in the right place.**

---

## 5 · 🌐 §5 — the roadmap question

**Better Auth 1.5 is current. Its trajectory is visibly *identity* — SSO moved to its own package and gained SAML 2.0; passkey moved to its own package; the organization plugin gained dynamic roles.**

🧠 **The honest reading: it is growing *toward* richer organization roles, not toward domain authorization.** ⛔ **Overlap with Casbin is therefore expected at the *role* layer and not at the policy layer** — **and the role layer is exactly the part [D-175](../DECISION_REGISTER.md) recommends not adopting.** ⚠️ **If Better Auth ever ships workspace-scoped ABAC with non-human subjects, that is the evidence that reopens this — and it is a specific, checkable trigger rather than a vague *"revisit later."***

---

## 6 · 🧠 §7 — my own recommendations, beyond the questions

| | |
|---|---|
| 🔴 **The real extensibility constraint is `Resource`, not Casbin** | 📁 **15 members, in `signora_platform` — 🔴 frozen — with a ruling ([C-224](../LANE_COORDINATION.md)) that adding one is a *declarative registration*.** ⚡ **Every new capability needs an enum member and a policy line, in two files, in a frozen package.** ✅ **Recommend: `Resource` moves to a registry the way `policy.csv` is — the ruling already treats it as one** |
| ⚡ **Make the intersection rule a Security Invariant before the first agent exists** | 📁 **[§11](../../CLAUDE.md): the suite states architectural guarantees rather than feature behaviour.** ⛔ **A test asserting *an agent can never exceed the human it acts for* is cheap now and unwritable after the first agent ships** |
| ⚠️ **`membership_role_change` should become the audit stream's first producer, not its own table** | 📁 **It already records every role transition and nothing reads it.** ⚡ **[TASK-492](../BACKLOG.md) should consume it rather than duplicate it** |
| ⛔ **Do not put permissions in the JWT — and keep the comment that says why** | 📁 **`jwt.ts:85` already refuses.** ⚡ **The moment a permission is in a token, revocation is bounded by token lifetime and the *"single source of authorization truth"* claim becomes false** |

---

## 7 · The recommendation, after the attempt to falsify it

> ## ✅ **Casbin only, unchanged — and now with one correction: a storage migration to a database adapter is certain, and was previously implied to be avoidable.**
>
> ## ✅ **Ratify the principal model above, the boundary in §2, and the intersection rule.**
>
> ## ⚡ **The recommendation survived the strongest attack this office could construct — that there are already two evaluators — because the repository had closed it before it was attacked. That is a better reason to ratify than the original argument.**
