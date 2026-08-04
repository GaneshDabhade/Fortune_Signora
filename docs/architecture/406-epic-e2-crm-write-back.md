# 406 — Epic E2 · CRM write-back — implementation preparation

> **Prepared by Lane C — Product Office. No code was written and none should be.** **Every claim verified against source on 2026-08-04.**
>
> **Observability, testing, operations and deployment: [405-cross-cutting-concerns.md](405-cross-cutting-concerns.md).** E2's deltas are in §9 below — they are E1's plus one, and the one is **write auditing**.
>
> ⚠️ **Links to [51-implementation-specifications.md](51-implementation-specifications.md) do not resolve on this branch.** Everything relied on is quoted inline.

> **Approved UI** — **CRM Integrations**. The [Fortune Signora Design Project](410-approved-ui-specification.md) is authoritative for frontend behaviour (2026-08-04). **This package no longer states what the screen looks like; it states what the backend must provide for it.** *"Signora writes to 3 fields in total across 8,412 accounts. Everything else is read-only by design."* **The approved screen bounds write-back more tightly than this package assumed.**


---

## 1 · Executive summary

**E2 writes into a customer's system of record, and that makes it categorically different from every other epic prepared so far.** Everything else in this repository reads the world, derives from it, and shows the result. **E2 changes something a customer's business runs on.**

**The repository already has a ratified principle that decides most of E2**, and it was written for a different module two months before E2 was considered:

> **`opportunity_engine/public/__init__.py`, ratified 2026-07-29:**
> ***"Intelligence suggests. Humans commit."*** *A buying score may **create** an opportunity. **Only a human may progress one beyond the machine-authored boundary.** Commercial intelligence informs workflow; it never owns it.*

**And it is enforced, not aspirational:** `MACHINE_AUTHORED: Final = frozenset({Stage.TRACKING})` — **exactly one stage may exist without a human actor**, and `Opportunity` raises if `actor_id is None` for any other (`domain/opportunity.py:82,205`).

> **The whole of E2's risk, in one sentence: a write-back is a commitment, and a machine-authored commitment in a customer's CRM is the principle above being broken in somebody else's database.**

---

## 2 · Customer problem, value, personas

**A seller's CRM is their system of record, and Signora is currently a second window they must reconcile by hand.** They read an insight in Signora, then retype it into Salesforce so their manager's pipeline review sees it. **The retyping is where the value leaks** — it is skipped under time pressure, and what is skipped is invisible.

| Persona | Value | Why it needs *write*, not read |
|---|---|---|
| **AE / SDR** | Opportunities they progressed in Signora appear in the CRM without retyping | Read-only leaves two systems disagreeing about the same deal |
| **Sales manager** | Pipeline reviews run on the CRM and see Signora's contribution | **A manager will not adopt a second window**; the CRM is where the meeting happens |
| **RevOps** | Attribution — *which pipeline did Signora actually create?* | **The commercial question behind renewal**, and unanswerable without a write |
| **CRO** | — | **No direct value.** Stated because a package that finds value for every persona has stopped looking |

---

## 3 · Repository validation — what exists

| | Exists today | Evidence |
|---|---|---|
| **Connection · grant · secrets** | `ConnectedAccount` · `IntegrationGrant` · encrypted `integration_secret` | [401](401-epic-e1-crm-read.md) §1 |
| **`ExecutionContext`** | Carries **`scopes`** — *"what the customer permitted, so a missing scope is a readable refusal"* | `integrations/application/resolve.py:48` |
| **The commit boundary** | **`MACHINE_AUTHORED`**, enforced by construction | `opportunity_engine/domain/opportunity.py:82` |
| **A workflow module** | `opportunity_engine` — *"records human commitment, which nothing reproduces"* | `public/__init__.py` |
| **Human actor identity** | `actor_id` required on every non-machine stage | `domain/events.py:71` |
| **Sync machinery** | `run_sync` · `pacing` · watermarks · three sync events | `provider_platform/` |
| **The firmographic reader** | `HubSpotCompanyMapper` — **inbound**, landed by Lane B | [401](401-epic-e1-crm-read.md) §0 |

**What does not exist:** **any write path to any external system.** `Capability` has `MESSAGE_DELIVERY` and it is **excluded from `LIVE_CAPABILITIES`** because its consumers are unbuilt. **Every catalog entry is `connectable=False`.** The `integrations` module has three endpoints — list, list, disconnect — **and no write.**

> **E2 is the repository's first outbound write of any kind.** That is worth stating plainly: there is no prior art here to reuse, and no existing mistake to learn from.

---

## 4 · The decision E2 turns on — what may be written, and by whom

**Four candidates, and they are not equally safe.**

| | Candidate | Assessment |
|---|---|---|
| **A** ✅ | **An opportunity a human progressed in Signora** | **Recommended for v1.** A person already committed, with an `actor_id` recorded. **The write carries a human's decision into the system that decision belongs in** — and the principle is satisfied because the commitment happened before the write, not because of it |
| **B** | **A note or activity summarising Signora's findings** | **Defensible second.** Additive, reversible, and a note is understood by every CRM as commentary rather than state. **But it is machine-authored content in a customer's record**, so it must be **attributed to Signora and never to a person** |
| **C** | **A field update from a derived value** — buying score onto the account | ⚠️ **Rejected for v1.** The score is *"a snapshot with a stated validity period"* and decays; **writing it into a CRM field creates a stale copy the customer cannot tell is stale.** `CLAUDE.md` §2 — truth has one authoritative representation |
| **D** | **Creating or progressing a CRM opportunity from a machine conclusion** | 🔴 **Rejected outright.** This is the principle broken in somebody else's database. **A machine would be committing on a human's behalf, in the record their compensation is calculated from** |

> **Recommendation: A for v1, B behind an explicit customer opt-in, C only if a customer asks and with a decay story, D never.**

**And a guardrail worth putting in the type rather than the review:** **a write must carry the `actor_id` of the human whose commitment it represents.** A write path with no actor is option D wearing option A's clothes — **and `opportunity_engine` already refuses exactly this shape**, so the pattern is a copy rather than an invention.

---

## 5 · Architecture, ownership and contracts

**No new bounded context.** E2 extends the same two modules E1 does.

| Concern | Owner | Change |
|---|---|---|
| **The permission to write** | `integrations` | **A write capability row** + **scopes** — `ExecutionContext.scopes` already exists so *"a missing scope is a readable refusal"* rather than a 403 from a vendor |
| **Performing the write** | `provider_platform` | An **outbound adapter** behind the existing port. **The same consumption edge E1 builds** ([401](401-epic-e1-crm-read.md) §1) — E2 is its second caller, not a new one |
| **What is worth writing** | `opportunity_engine` | **Publishes already.** `opportunity.stage_changed` carries the actor. **E2 subscribes; it does not reach into the module** |
| **The record of what was written** | **New — a small write log** | §9. **Not optional**: an unlogged write into a customer's system of record is unauditable by construction |

> **E2 is event-driven and should stay that way.** `opportunity.stage_changed` fires today. **A subscriber that writes back is loosely coupled, replayable, and uses the outbox, idempotency and dead-lettering that already exist** — the same argument [Epic F](402-epic-f-workflow.md) makes, and the same reuse.

**Idempotency is not optional here and is already provided.** `event_bus/idempotency.py` is platform-owned. **A redelivered event that writes twice creates two CRM records**, and the customer sees the duplicate before anyone sees the log.

---

## 6 · Workflows

**Happy path:** a person progresses an opportunity in Signora → `opportunity.stage_changed` with `actor_id` → the subscriber checks the connection is usable and the scope is granted → writes → **records the write with the actor, the target and the response.**

**Failure paths, and each has a required behaviour rather than a suggested one:**

| | Behaviour |
|---|---|
| **Scope not granted** | **Refuse before calling the vendor.** `ExecutionContext.scopes` exists so this is a readable refusal |
| **Connection revoked** | The write fails; **`ConnectionState` already models this** and the customer must see it ([405](405-cross-cutting-concerns.md) §6) |
| **Vendor rejects — validation, permissions, required field** | **Dead-letter and surface.** Never retry into a duplicate |
| **Vendor accepts, response lost** | **The hard one.** Idempotency key on the write, or a read-back before retry. **Decide explicitly; a naive retry duplicates a customer's opportunity** |
| **The customer edits it afterwards** | **Signora does not overwrite.** A customer's edit to their own record wins, permanently. **Last-writer-wins here means Signora silently reverting a person's correction** |
| **The opportunity is reverted in Signora** | **Do not delete in the CRM.** Write a correction or nothing — **deleting from a system of record is not Signora's to do** |

---

## 7 · Phases

| # | Phase | Delivers | Effort | Depends on |
|---|---|---|---|---|
| **1** | **Write scope and capability** | The customer grants write; a missing scope refuses readably | **S** | **[E1](401-epic-e1-crm-read.md) acquisition** |
| **2** | **The write log** | Every attempted write recorded with actor, target, outcome | **S** | Phase 1 |
| **3** | **Opportunity write-back (option A)** | A human's commitment reaches the CRM | **M** | Phase 2 · **E1's consumption edge** |
| **4** | **Notes / activity (option B)** | Signora's findings as attributed commentary | **M** | Phase 3 · **opt-in** |
| — | ~~Field updates · machine-authored opportunities~~ | **Not in E2** — §4 | — | — |

> **Phase 2 before phase 3, and not the other way round.** A write log built after the first write exists is a log with a gap in it, **and the gap is the period nobody was watching.**

**Every phase is Lane B's** — `integrations`, `provider_platform` and `opportunity_engine`'s events are all its own. **Zero cross-lane crossings**, which is unusual and worth preserving.

---

## 8 · Risks

| Class | Risk | Mitigation |
|---|---|---|
| **Product** 🔴 | **A machine commits in the customer's system of record** | §4 option D refused; **`actor_id` required on the write path, in the type** |
| **Data** 🔴 | **A duplicate opportunity from a redelivered event** | Platform idempotency **plus** a vendor-side idempotency key. **Both** |
| **Data** 🔴 | **Signora overwrites a customer's own edit** | §6 — the customer's edit wins, permanently |
| **Compliance** 🟠 | **An unauditable write** | Phase 2 first. **Non-negotiable** |
| **Architectural** 🟠 | A stale derived value written into a CRM field | §4 option C — **decay makes it a lie over time** |
| **Security** 🟠 | Write scope granted where read was intended | **Separate scopes, separate consent.** `scopes` already models it |
| **Operational** 🟡 | Vendor rate limits on writes | `pacing` exists; **writes are lower-volume than reads** |
| **Product** 🟡 | The customer cannot tell what Signora wrote | The write log should be **visible to the customer**, not only to support |

---

## 9 · Cross-cutting deltas ([405](405-cross-cutting-concerns.md))

| Concern | Delta | Decision it serves |
|---|---|---|
| **Audit** 🔴 | **A write log is a feature, not a metric.** Actor, target record, payload identity, vendor response | *What did Signora change in my CRM?* — **unanswerable otherwise, and a customer will ask** |
| **Metric** | Writes attempted / succeeded / refused-on-scope / dead-lettered | *Is write-back working, or quietly failing?* |
| **Testing** 🔴 | **Structural: no write path without an `actor_id`** | §4's guardrail, held by the type rather than review |
| **Testing** | Idempotency exercised — **redeliver and assert one record** | The duplicate is customer-visible before it is log-visible |
| **Redaction** | Inherits E1's — **verify `Credential.__repr__` survives the write path too** | A write path logs request bodies more often than a read path |

---

## 10 · Definition of done, and open questions

**Done when a commitment a person made in Signora appears in their CRM, attributed to them, exactly once, with a record the customer can read — and when Signora writes nothing a person did not decide.**

**Gates:** no write without an `actor_id` · idempotency proven by redelivery · **the customer's own edit is never overwritten** · a missing scope refuses before the vendor is called · **the write log precedes the first write** · no derived value written to a CRM field.

### Open questions

> **🟡 Upcoming — is option B (notes/activity) in scope, and is it opt-in?** Lane C recommends **yes, and yes.** It is the highest-value half for a manager and the half most likely to annoy a RevOps lead who did not ask for it. **Needed before phase 4, not before phase 1.**

> **🟢 Background — should the write log be customer-visible?** Lane C recommends yes. *"What did Signora change?"* is a question a customer is entitled to answer without contacting support.

> **Not escalated — engineering answers these:** the vendor idempotency mechanism per CRM · whether the subscriber is its own worker pool · the write log's retention.
