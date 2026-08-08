# 494 · Authorization architecture — Better Auth roles, Casbin, or something else

**Lane C · Product Office · 2026-08-08.** **[D-175](../DECISION_REGISTER.md), which asks the ten-year question rather than the library question.**

> ⚡ **Sources labelled: 📁 repository evidence · 🌐 external research · 🧠 this office's judgement.**

---

## 0 · The recommendation

> ## ✅ **Casbin only. Adopt Better Auth's *identity* plugins and none of its authorization.**
>
> ## ⛔ **Not hybrid — hybrid is the worst of the three, and §6 asked to be told that plainly.**
>
> ## ⚠️ **And the recommendation is *not* "Casbin is earning its keep today." It is "Casbin is the option that does not have to be replaced when the hard requirements arrive."**

---

## 1 · 📁 What Signora's authorization actually is today

**Read from `model.conf` and `policy.csv` rather than described:**

```
r = sub, dom, obj, act        sub = the workspace ROLE, not the user
p = sub, dom, obj, act        dom = the workspace id
m = r.sub == p.sub && (p.dom == "*" || r.dom == p.dom)
    && r.obj == p.obj && r.act == p.act
```

| | |
|---|---|
| **Policy lines** | **53** |
| **Resource types** | **4** — `workspace` `member` `opportunity` `account` |
| ⛔ **Role hierarchy (`g`)** | **Not configured** |
| ⛔ **ABAC, `keyMatch`, custom matchers** | **None — the matcher is four equalities** |
| ⛔ **Per-workspace policy** | **Every line uses `dom = "*"`** |

> ## ⚡ **So Signora is using perhaps five percent of Casbin. What is deployed is a role→(resource-type, action) matrix with a domain column that is always a wildcard — a CSV lookup, not a policy engine.**

⚠️ **And the model file says why the subject is a *role* rather than a user, which matters later:** *"membership lives in PostgreSQL under Row-Level Security and is verified per request, so mirroring it into Casbin's grouping policy would duplicate the source of truth and let the two drift."* ✅ **That decision is correct and it is the reason `g` is absent.**

---

## 2 · 🌐 What Better Auth's organization plugin actually is

| | |
|---|---|
| **Model** | **RBAC — resource-action pairs, `organization:delete`, `member:create`** |
| **Roles** | **owner · admin · member, plus custom roles via `createAccessControl()`** |
| **Custom roles** | **Static in code, *or* dynamic in an `organizationRole` table when `dynamicAccessControl` is enabled** |
| ⛔ **Scope** | 🌐 ***"Permissions apply to the entire organization, not individual resources or accounts."*** |
| ⛔ **Hierarchy / inheritance** | 🌐 ***"No stated permission inheritance or hierarchical role structures. Permissions are flat mappings."*** |
| ⛔ **Teams** | 🌐 ***"Teams cannot override organization-level permissions."*** |

> ## ⚡ **Both are flat role→(resource-type, action) matrices today. Swapping one for the other is lateral — it buys nothing and costs a migration.**

---

## 3 · 🧠 The question that actually decides it

**[D-175](../DECISION_REGISTER.md) §1 lists twenty-three future capabilities. Sorted by *what they demand of an authorization model*, they collapse to four demands:**

| Demand | Example from the list | 📁 Today | Casbin | Better Auth org |
|---|---|---|---|---|
| ⚡ **A non-human principal** | **AI agents · AI tools · API keys · service accounts · marketplace extensions · public APIs** | ⛔ **Does not exist** | ⚠️ **`sub` is a string — an agent is a subject like any other** | ⛔ **Subjects are organization *members*. An API key is not a member** |
| ⚡ **Object-level permission** | **Resource-level · object ownership · *"this specific account"*** | ⛔ **Does not exist** | ✅ **`keyMatch`, a resource-id in `obj`, or an ABAC matcher — a `model.conf` edit** | ⛔ 🌐 **Structurally organization-scoped, by its own documentation** |
| ⚡ **Context-aware / temporary** | **ABAC · temporary permissions · context-aware · approval workflows** | ⛔ **Does not exist** | ✅ **Matchers read request attributes; this is Casbin's design centre** | ⛔ **Flat mappings** |
| **Hierarchy** | **Organizations → workspaces → teams → departments · inheritance · templates** | ⛔ **Flat** | ✅ **`g` and `g2` grouping policies** | ⛔ 🌐 ***"No stated permission inheritance"*** |

> ## ⛔ **Better Auth's organization plugin cannot express three of the four, and its documentation says so rather than this office inferring it.** ✅ **Casbin expresses all four through `model.conf`, with no library change and no migration.**

### ⚠️ And the finding that reframes the whole comparison

📁 **`AuthenticatedPrincipal` carries `user_id`, `session_id`, `email`, `email_verified`, `active_workspace_id`, `token_id`.** ⛔ **Every field is human. `grep` for `service_account`, `api_key`, `ServiceAccount` or `agent_id` outside tests returns nothing.**

> ## ⚡ **The binding constraint on Signora's next decade is not the policy engine. It is that Signora has no model of a non-human caller — and neither option supplies one.**
>
> ## ⛔ **Choosing an engine on "which does roles better" optimises the wrong variable. Both do roles. Neither does principals.**

---

## 4 · 🔴 Why hybrid is the worst option — §6 answered directly

**Hybrid means Better Auth's organization roles for identity-adjacent permissions and Casbin for domain permissions.**

| | |
|---|---|
| ⛔ **Two role stores** | **`organizationRole` in Better Auth's schema *and* `membership.role` in PostgreSQL under RLS.** ⚡ **[§2](../../CLAUDE.md): *truth has exactly one authoritative representation* — and this is the defect *inside the security layer*, where drift is a vulnerability rather than an inconvenience** |
| ⛔ **Two tenancy units** | 📁 **Signora's domain unit is the *workspace*; Better Auth's is the *organization*.** ⚠️ **[D-175](../DECISION_REGISTER.md) §1's own vision has organizations *containing* workspaces — so mapping one onto the other is not a shim, it is a false statement about the domain** |
| ⛔ **Two answers to one question** | **A reviewer asking *"may this person do this?"* must know which engine owns that resource.** 🧠 **That is a permanent tax on every future authorization change** |
| ⛔ **Synchronisation** | **Every role change writes twice, and the failure mode is a permission that exists in one store** |

> ## ✅ **Hybrid is not recommended, and the reason is not complexity — it is that it creates a second source of truth for authorization, which is the one place this repository can least afford one.**

---

## 5 · 🌐 The third architecture, named honestly — Zanzibar / OpenFGA

**[D-175](../DECISION_REGISTER.md) §9 asks for a third option if one serves better. There is one, and it is the industry answer to exactly the requirement Casbin serves least well.**

| | |
|---|---|
| **What it is** | **Relationship-based access control — Google's Zanzibar model, open-sourced as OpenFGA and SpiceDB.** **Permissions are edges: *"user X is an editor of account Y"*** |
| ✅ **What it does better than either option** | ⚡ **Object-level permission at scale, with `list-objects` — *"which accounts may this seller see?"* — answered by the store rather than by filtering in the application** |
| ⛔ **Why it is not the recommendation today** | 📁 **[§3](../../CLAUDE.md) Principle 6: *one PostgreSQL database*, and a second datastore requires an explicit approved exception.** **OpenFGA is a service.** ⚠️ **And Signora already answers *"which rows may this caller see?"* with Row-Level Security — which is a relationship model, in the database, already enforced** |
| ⚡ **When it becomes right** | 🧠 **If per-object sharing arrives — *"share this opportunity with one person outside the team"* — RLS and a role matrix both stop being enough on the same day.** ✅ **Recorded so it is a considered option then, not a discovery** |

---

## 6 · Repository impact

| Option | Migration | Risk |
|---|---|---|
| ✅ **Casbin only** | ⛔ **None. It is the status quo** | **None** |
| **Better Auth only** | **53 policy lines · the `Resource` enum · every `enforce` call site · and a *tenancy* mapping that does not exist** | 🔴 **High — and it trades a model that can grow for one whose limits are documented** |
| **Hybrid** | **Partial migration plus permanent synchronisation** | 🔴 **Highest — two sources of truth in the security layer** |

---

## 7 · 🧠 §11 — what I would do as Chief Architect for the decade

> ## **I would keep Casbin, adopt none of Better Auth's authorization, and spend the effort saved on the two things that actually block the ten-year vision: a principal model that admits non-humans, and object-level permission.**

**Because:**

⚡ **① The decision that is hard to reverse is the *tenancy* one, not the engine one.** **Adopting Better Auth's organization model imports its unit of tenancy into every authorization check.** ⛔ **Signora's unit is the workspace, enforced by RLS in PostgreSQL, and that is the one architectural commitment in this repository I would least want to relitigate.**

⚡ **② Casbin's value here is optionality, not features.** 📁 **It is doing almost nothing today — 53 flat lines.** **But every one of the four future demands is a `model.conf` change, and `model.conf` is a text file.** 🧠 **Paying nothing now for the ability to express ABAC later is the cheapest option on this page.**

⚠️ **③ What I would avoid even though it looks simpler today: the organization plugin.** **It would delete 53 lines of CSV and feel like a simplification.** ⛔ **It would also fix the permission model at *flat, organization-scoped, no inheritance* — and three of the twenty-three capabilities [D-175](../DECISION_REGISTER.md) §1 names would then need a second engine anyway.** ⚡ **That is how a repository arrives at hybrid by accident rather than by choice.**

### The risks I see in my own recommendation

| | |
|---|---|
| ⚠️ **Casbin becomes decorative** | 📁 **A 53-line flat matrix could be a Python dict, and a dependency that earns nothing is a maintenance cost.** ✅ **The mitigation is a date, not a hope: if object-level or ABAC has not arrived by the time the twelfth resource type does, revisit whether the dependency is justified** |
| ⚠️ **Two permission *vocabularies* still appear** | **Better Auth's plugins define their own permissions for their own routes — `organization:delete` lives in Better Auth whether Signora uses it or not** | 
| ⚠️ **`policy.csv` in a repository does not scale to customer-defined roles** | 🧠 **Custom roles per workspace need a database adapter, which Casbin has.** ⛔ **That is a real migration and it is not free — but it is a *storage* change, not an architecture change** |

---

## 8 · The opportunity this unlocks

⚡ **Keeping the engine and fixing the principal is the ordering that makes the AI platform's authorization tractable.** 📁 **`Resource.RESEARCH` already exists because *"reading an account is free and asking for research spends a model call."*** 🧠 **An AI agent acting on a customer's behalf is a subject with a *narrower* permission set than the human who invoked it — and expressing "the agent may read but not spend" is one policy line in a model that admits non-human subjects, and impossible in one that only admits members.**

> ## ✅ **That is the strongest argument on this page: Signora's differentiator is agents acting inside a customer's data, and the authorization model must admit an actor that is not a person. Casbin does. Better Auth's organization plugin does not.**
