# 438 · Future platform initiatives — reuse audit, gap analysis and decomposition

**Lane C · Product Office · 2026-08-05.** Product Office directive: *"Do not implement anything. Do not assign engineering work. Do not change current priorities."*

**Covers three initiatives** — Data Governance · Internal Administration · Marketplace & Extensibility — **plus the cross-cutting sweep**, and answers the reuse question first because the directive puts it first.

---

# 0 · Four findings, before the decomposition

## ① Three of the largest asks are subscribers to systems that already exist

**Webhooks, connectors and agents are not new platforms.** Each has a foundation shipped and proven:

| Ask | Reuses | Why it is not new |
|---|---|---|
| **Webhooks** | **The outbox → relay → dispatcher chain** | It already provides at-least-once delivery, **an idempotency ledger**, dead-lettering, worker pools and tenant-scoped dispatch. **A webhook is a subscriber with an HTTP sink** — the hard half is built and certified |
| **Connectors** | **`IntegrationSourceAdapter`** | *"Two methods, deliberately… a wider port would need every future source to implement methods most of them do not have, and the usual outcome is adapters raising `NotImplementedError` — which is a contract that lies"* |
| **Agents / MCP** | **The AI Provider Port** | [437](437-ai-platform-future-epic.md) — and agents run into the **statelessness** ruling before they run into a missing framework |

> **Proposing three new platforms here would be the duplicate abstraction the directive forbids**, and the reuse is not superficial: **the outbox's guarantees are exactly a webhook's hard problems.**

## ② The repository is edit-averse, not delete-averse — and I nearly reported the opposite

**Measured across migrations: 32 `FOR SELECT` · 30 `FOR INSERT` · **26 `FOR DELETE`** · 10 `FOR UPDATE`.**

**I expected an append-only repository where the right to be forgotten would collide with immutability.** **It does not.** The discipline is **no `UPDATE`** — *"a revision is a new row naming its parent"*, *"every profile version is immutable, attributed and reproducible"* (AC-47). **Deletion is broadly granted.**

**So erasure is mechanically possible today. What is missing is a strategy**, and the narrower real tension is **audit preservation versus erasure** — not immutability versus erasure.

## ③ There is no delete strategy at all — `deleted_at`, `is_deleted` and soft-delete appear in **zero** files

**The directive asks whether a consistent repository-wide strategy exists. It does not, and nothing has needed one yet.** ⚠️ **This is the single most consequential gap in all three initiatives**, because **the cost of adding one rises with every table** and the repository is at 39 migrations.

## ④ `make dr` is not backup

**`disaster-recovery.sh` restarts each component and asserts nothing is lost.** That is **restart survival**, and it is genuinely proven — 5 stages, every cycle. **It is not a backup policy, a retention schedule, point-in-time recovery, or restore verification.** *(`backup`: 27 docs, 7 code — none of it a backup system.)*

---

# 1 · Reuse audit — the whole directive, measured

**✅ reuse · 🟨 extend · 🔴 genuinely new · ⛔ do not build**

| Capability | Docs | Code | Verdict |
|---|---|---|---|
| **Eventing / job scheduling** | 43 | 9 | ✅ **Outbox, relay, dispatcher, dead-letter, pools.** Certified every cycle |
| **Secrets & credentials** | 37 | **58** | ✅ **Heavily present.** Typed `Settings` per module, §10 |
| **Retention (as a concept)** | 30 | 13 | 🟨 Present in domain records; **no policy engine** |
| **Audit / immutable history** | 10 | 3 | 🟨 **Immutability is the discipline, not a subsystem.** An audit *query* surface is missing |
| **Backup & recovery** | 27 | 7 | 🔴 **`make dr` proves restart survival, not backup** |
| **Connectors** | 5 | 4 | ✅ `IntegrationSourceAdapter` |
| **API keys / auth** | 11 | 4 | ✅ Better Auth is the sole authority (§13) |
| **OpenAPI** | 9 | 2 | 🟨 FastAPI emits it; **no versioning policy** |
| **Notification / email** | 34 | 6 | 🔴 **No transactional email exists** — [TASK-904](../BACKLOG.md) ships invitations as a link *because of this* |
| **Feature flags** | 7 | **1** | 🔴 Genuine gap, **and small** |
| **Soft delete / restore** | **0** | **0** | 🔴 **Finding ③** |
| **Workspace suspend / archive / delete** | 5 | **0** | 🔴 **Lifecycle stops at creation** |
| **GDPR erasure / export / consent** | 3 | 0 | 🔴 Consent has 6 code files; **erasure and export have none** |
| **Rate limiting** | **0** | **0** | 🔴 **Absent, and a GA prerequisite** |
| **Impersonation** | 5 | **0** | 🔴 Security decision before engineering |
| **Maintenance mode / announcements** | 0 | 0 | 🔴 Absent |
| **Tenant admin console** | **0** | **0** | 🔴 **[TASK-425](../BACKLOG.md) already proposed** |
| **Billing administration** | 26 | 4 | 🟨 **[TASK-411/412](../BACKLOG.md) already `SEQUENCED`** |
| **GraphQL** | 2 | 0 | ⛔ **Do not build.** REST ships and nothing needs a second query language |
| **SDKs** | 11 | 6 | ⛔ **Not until a customer integrates.** An SDK with no consumer versions an API nobody calls |
| **Plugin framework** | 3 | **0** | ⛔ **No customer, no extension point.** §20a exists to prevent this |
| **Marketplace** | — | 0 | ⛔ **A marketplace needs supply, demand and a plugin framework.** None exists |
| **Multi-region** | — | 0 | ⛔ Not before a customer with a residency requirement |

---

# 2 · Shared foundations — built once, reused everywhere

**The directive asks for these explicitly, and they are the most valuable output of this document.** **Five capabilities carry all three initiatives**, and getting them wrong once is expensive three times.

| # | Foundation | Carries | Status |
|---|---|---|---|
| **S1** | **A deletion and retention strategy** | GDPR erasure · workspace deletion · retention · legal hold · tenant cleanup | 🔴 **Nothing.** **Build first or build three times** |
| **S2** | **Workspace lifecycle states** | Suspension · archival · restoration · billing dunning · support actions | 🔴 `workspace_tenancy` has creation and membership; **no state machine** |
| **S3** | **An audit query surface** | Compliance reporting · support lookup · security evidence · GDPR proof | 🟨 **The data exists and is immutable; nothing reads it as a history** |
| **S4** | **Outbound delivery** | Webhooks · notifications · email · announcements | 🟨 **The outbox is the delivery half. The sink half is missing** |
| **S5** | **An internal operator identity** | Every internal surface, impersonation, support audit | 🔴 **Better Auth authenticates customers. Nobody has modelled a Signora employee** |

> **S1 and S5 are the ones that cause rework if deferred.** **S1 because every new table makes it more expensive**, and **S5 because an internal console built on customer identity is a tenancy violation that is very hard to unpick later.**

---

# 3 · Initiative 1 · Data Governance

**Assessment only. No rows proposed** — see §7.

**What exists:** immutability as a discipline · forced RLS on every tenant table · `DELETE` policies on 26 tables · restart-survival DR · consent in 6 files.

**What is missing:** S1 (strategy) · S2 (lifecycle) · S3 (audit surface) · backup policy · erasure · export.

## The decision this initiative actually contains

> **What survives an erasure?** **Immutability says a record of what was true then must not be rewritten. Erasure says a person's data must go.** **Both are correct and they meet in the same row.**
>
> **Recommended shape, for when this is scheduled:** **erase the person and keep the event.** A `signal` that says *a named person changed role* becomes a signal that says *a role changed* — **the business fact survives, the identity does not.** **That is only cheap if it is designed before the data exists**, which is finding ③ restated.

⚠️ **And it interacts with [C-221](../LANE_COORDINATION.md), ruled today:** *"do not expand the architecture around people until we have a reliable provider capability."* **No person's name enters the platform today** — **so the erasure surface is currently near-zero, and this is the cheapest moment in Signora's life to design it.**

---

# 4 · Initiative 2 · Internal Administration

## ⚠️ The name — I am challenging *Signora Studio*

**"Studio" is the name you will want for the customer-facing builder**, and Initiative 3 is what tells me so: it proposes a marketplace for **templates, prompts, workflows, reports and dashboards.** **Those are precisely what a customer-facing "Studio" builds** — the word means *a place where a user creates things* in every SaaS product that uses it.

> **Spending it on a console customers never see means renaming one of the two later**, and the one that gets renamed is always the one with users.

**Recommendation: name the internal surface for what it is** — **Signora Operations**, or **Ops Console**. **Unglamorous on purpose:** an internal tool that sounds like a product invites customer-facing scope, which is the mixing this directive is trying to prevent.

> **If you want one word: "Signora Control".** **Reserve "Studio" for the customer builder.**

## The separation — and the mechanism already exists

**The directive asks for strict separation of customer-facing, internal and platform capabilities.** **Do not introduce a new concept for it.** [`modules.toml`](../coordination/modules.toml) already carries `context` and ownership per module; **the separation is one field.**

**Recommended:** add `audience = "customer" | "internal" | "platform"` to the registry **when the first internal module exists**, not before. **Every module today is `customer` or `platform`, so the field would have one value — the decorative class §2 forbids.**

## What internal administration actually needs first

**Not a console. `S5` — an operator identity.** **Everything in the directive's list assumes somebody is logged in who is not a customer**, and that person does not exist in the model. **[TASK-425](../BACKLOG.md) is already proposed and is the right first slice**: read-only workspace state for support.

---

# 5 · Initiative 3 · Marketplace & Extensibility

**Sequenced by dependency, and most of it is far away.**

| | Reuse | Verdict |
|---|---|---|
| **Webhooks** | **The outbox chain** | **The nearest real capability.** A `webhook_endpoint` per workspace, a subscriber, and delivery attempts recorded as history. **⚠️ Needs S1** — a customer deleting an endpoint expects the deliveries to go |
| **Public API versioning** | FastAPI's OpenAPI | 🟨 **A policy, not a platform.** One ADR |
| **Rate limiting** | — | 🔴 **Absent and a GA prerequisite** — see §6 |
| **Connectors** | `IntegrationSourceAdapter` | ✅ **Already the architecture.** A connector is an adapter |
| **Agent framework** | The AI Provider Port | ⛔ **Blocked on [437](437-ai-platform-future-epic.md)'s state question.** Agents are stateful by nature |
| **SDK · GraphQL · Plugins · Marketplace** | — | ⛔ **No customer.** Each is a large surface whose first version is always wrong without one |

---

# 6 · Cross-cutting — only the genuine gaps

**Evaluated as instructed; most are already satisfied.**

| Gap | Why it is real |
|---|---|
| 🔴 **Rate limiting** | **0 docs, 0 code.** **A public API without it is not GA-ready**, and it is small |
| 🔴 **Transactional notification** | **Already shaping the product** — TASK-904 ships a link instead of an email |
| 🔴 **Feature flags** | **Small, and 1 code file.** ⚠️ **Propose only when a slice needs one** |
| 🔴 **Operational runbooks** | **`RUNNING.md` covers development, not production incidents** |
| ✅ **Job scheduling · config · secrets · search · workflow** | **Satisfied.** Do not propose |
| ⛔ **Reporting · export/import · license management · multi-region · BCP** | **No demand signal.** Each fails the *no-speculative-ports* rule |

---

# 7 · My second challenge — the volume

**The directive names roughly forty capabilities across three initiatives. I have decomposed almost none of them into tasks, deliberately, and this is where I ask you to disagree if you want more.**

> **A speculative backlog decays, and this repository has measured the cost.** **In two days: [C-008](../LANE_COORDINATION.md) was ruled and still read `OPEN`; [C-412](../LANE_COORDINATION.md) named the wrong lane on both pairs; [414](414-wave-1-account-360.md) counted a section that had no route.** **Every one of those mis-sequenced a lane**, and each was written when it was true.

**Rows written against triggers eighteen months out will be wrong in exactly that way, and nobody will be checking them.** **The assessment above does not decay** — it is a measurement with dates and a method, and it can be re-run.

**So I propose rows only where the trigger is near and the design is stable:**

| | |
|---|---|
| ✅ **Proposed now** | **S1 — the deletion and retention strategy.** Its cost rises with every migration, and **the erasure surface is near-zero today because no person's name is in the platform.** *(This is [TASK-426](../BACKLOG.md).)* |
| ✅ **Already proposed** | [TASK-425](../BACKLOG.md) internal admin · [TASK-411/412](../BACKLOG.md) billing · [TASK-420–424](../BACKLOG.md) Epic H |
| **Assessment only** | Everything else. **This document is the record; a row can be cut from it in minutes when a trigger fires** |

**If you would rather have the full decomposition now, say so and I will write it** — **but I would be manufacturing the staleness I have spent two days correcting**, and I would rather say that first.

---

# 8 · What this document did not do

| | |
|---|---|
| **No queue changed** | Nothing in `docs/coordination/queues/` |
| **No task assigned** | One new row, `SEQUENCED` with a trigger |
| **No priority moved** | Lane A on **TASK-417**; Lane B on **TASK-406** |
| **No new module, context or service** | **Not one** — every proposal above extends something that exists, or is refused |
| **No ADR written** | Two are *candidates*: **the erasure/audit boundary**, and **API versioning policy** |
| **No regression** | **Nothing executable changed** |
