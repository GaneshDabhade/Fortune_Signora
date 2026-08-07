# 52 — People (module design)

> Status: **As built — TASK-427, stages S1 and S2. Lane B, 2026-08-06.**
> Ratified by [ADR-0400](adr/0400-person-as-an-entity.md), which remains this context's architectural decision record. Approved at this scope by [D-074](../DECISION_REGISTER.md); assigned to Lane B by [D-103](../DECISION_REGISTER.md). Roadmap: [441](441-people-roadmap.md).
>
> ⚠️ **Document number allocated from the highest free number, because architecture document numbers have no allocation block** — [B-126](../BUGS.md), which is open and Lane C's. **Checked against every branch before use**: `52` was free on `integration`, `lane-a`, `lane-c-sync` and `lane-qe`. **If it collides anyway, that is the defect B-126 describes and not a second instance of it.**

## The boundary, stated first

> **People knows who somebody is and where they have worked. It never decides what any of that means about a deal.**

The same discipline `commercial_profile` and `timeline` already hold, from a third direction. **Commercial Profile records and computes nothing; Timeline projects and computes nothing; People identifies and computes nothing.**

**The temptation is specific and the ADR names it**: *a person is one plausible field away from becoming an influence model.* `seniority_score`, `is_key_contact`, `priority`, an ordered list read as a ranking — each turns an identity into a scoring input, **in the module least equipped to review it.** `tests/people/test_boundary.py` reads the domain package as a syntax tree and refuses those words, exactly as the committee's does.

An import contract holds the other half: `people` may not import `signal_engine`, `buying_score_engine`, `opportunity_engine`, the AI modules, `commercial_profile` — **or `workspace_tenancy`**, which is the load-bearing one.

## A `Person` is not a `Member`

**A `Member` is a customer's employee using Signora. A `Person` is somebody at a target account who has never heard of Signora.** Different lawful basis, different lifecycle, different erasure story. **The contract makes them structurally unjoinable** rather than leaving it to review.

## Anonymous, and that is the specification rather than a limitation

**No name. No email. No phone. No provider identifier.** [C-221](../LANE_COORDINATION.md) — *"do not expand the architecture around people; focus on role-based and organization-level intelligence"* — **is not a constraint on this module. It is what the module is.**

**Six modules already run role changes through production and not one knows a name.** A provider reports `ROLE_CHANGE` carrying `RoleChangeValue(title, seniority, direction)`; `observation_engine` classifies it; `business_event_engine` emits leadership appointed and departed; `signal_engine` emits `new_decision_maker`. **What was missing was never a name — it was a subject those events could point at.**

Whether a provider *could* supply a name is ❓1 of the ADR and gates [TASK-429](../BACKLOG.md). **Nothing here changes if the answer is no.**

## The model

| | | |
|---|---|---|
| **`Person`** | An identity and its tenant. **Nothing else** | `domain/person.py` |
| **`Affiliation`** | person × company × title × interval. **Where the intelligence lives** | `domain/affiliation.py` |
| **`RoleInterval`** | `started_on`, and `ended_on` which is usually absent | `domain/affiliation.py` |
| **`EntityKind.PERSON`** | The graph names the kind | `knowledge_graph/domain/identity.py` |

**`Affiliation` is an entity rather than a field, and that is the load-bearing choice**: *"Priya left Acme" is not a mutation of Priya — it is an interval closing.* A `current_employer` field would be **the one place in this repository where a state change overwrites its own evidence**, and there is no such column anywhere in migration 0040.

### `EntityKind.PERSON` is named and never bound

The graph's docstring said Person was absent because *"claims carry role changes but no person identifier, so there is no identity to resolve."* **That is still true.** What changed is that a person no longer needs resolving to be useful — so `PERSON` is a kind the graph **names and does not bind**. No `identity_binding` row will carry it until a provider supplies an identifier, which is TASK-429. **Recorded in the enum's own docstring**, because a member resolution never produces looks like a bug to whoever finds it next.

### Open-ended is a state, not a missing value

An affiliation with no `ended_on` means **no departure has been observed** — which is *not* the same claim as *"they still work there"*, and this module can only ever make the first. A screen will want the second sentence; the honest one is the first.

## The rule that decides which affiliation a departure closes

**The one genuinely hard question in an anonymous People domain**, written down as a rule rather than buried in whichever use case needed it first — the discipline `select_name` set.

> **A departure closes the single open affiliation at that company with that title. If there is more than one, it closes none and says so.**

`match_departure` returns `MATCHED`, `NONE_OPEN` or `AMBIGUOUS`, with the candidates travelling on every outcome.

**Refusing is the point.** Every alternative is a judgement this module has no standing to make — *close the oldest* assumes tenure predicts departure, *close the newest* assumes the opposite, *close them all* invents a mass exit from one event. **An unmatched departure is recoverable; a wrongly closed interval is not**, because nothing downstream can tell it from a real one.

**`NONE_OPEN` is not an error.** Signora never saw the arrival — the person was in post before it started watching. The fact still happened.

**Title comparison folds case and space and nothing else.** *"VP of Engineering"* and *"VP, Engineering"* are one job to a human and two strings here. **Same limitation as `commercial_profile.evaluation`, same reason**: deciding two different words mean one thing is a reviewed catalog, not code.

## Persistence — migration 0040

Two tables, both workspace-owned, both with forced RLS and policies covering `SELECT`/`INSERT`/`DELETE`, both registered in `tenancy_policy.py` in the same change that created them.

**`affiliation` carries an `UPDATE` grant and `person` does not**, which is the one place this module departs from its neighbours and is argued in the migration rather than assumed. Closing an interval is not an edit of a fact: `ended_on` moves exactly once, from `NULL` to a date, nothing else in the row is ever touched, a check constraint makes the harmful direction impossible, and the repository's `ended_on IS NULL` predicate makes a second close a no-op where two processes cannot see each other. **The append-only alternative was rejected as premature** — nothing yet reads an affiliation's *history of revisions*, and a superseding chain nobody queries is structure without a consumer.

**No foreign key to `entity`.** The company id is carried and joined at read time, the way every module cites an entity; a constraint across a boundary neither context owns would make one module's migration depend on another's table shape.

## What `people` publishes — TASK-457

**Two value types and no reader**: `PersonView` *(an id and a workspace, and there will never be a third field that identifies anybody)* and `AffiliationView` *(person, company, title, seniority, and the interval)*.

### ⚡ The reader, added when the caller became real — C-237

**TASK-457 published no reader**, on the stated ground that *"a port shaped for an imagined caller is the speculative abstraction §6 forbids"*, and named the trigger that would end it: **the first consumer.** **[TASK-458](../BACKLOG.md) is that consumer**, and Lane A raised [C-237](../LANE_COORDINATION.md) rather than adding the port to a module that is not theirs.

> **`AffiliationReader` — `at_company` and `for_person`, both read-only.**

**It is specified by its caller rather than guessed at**, which is the whole reason the delay was worth it. C-237 stated the requirement in Lane A's own words — *"what a signal cannot say today is **which seat**"* — so:

| | |
|---|---|
| **`at_company` returns open *and* closed intervals** | *"Who left, and when"* is what `decision_maker_departed` exists to answer, and a read returning only current holders could not answer it at all |
| **The answer carries the interval, never a current employer** | C-237 names the reason exactly: `ended_on = None` means **no departure has been observed**, not *"they still work there"* — **the distinction a signal would otherwise flatten** |
| **Scoped to one company** | The same title is held at every company in a workspace. A workspace-wide read would invite matching on title alone, which is the mistake `match_departure` refuses one layer down |
| ⛔ **No write, at any point** | Affiliations are opened and closed by this module's own use case. **A judging module must never be able to author the history it reads** |

⚠️ **`for_person` returns one affiliation in almost every case today**, and that is a property of the platform rather than of the port — see the minting note below. **Documented on the method** so a consumer does not read a single-element result as a data gap.

**What it publishes is a subject, never an identity.** No name, no email, no phone, no provider id — [C-221](../LANE_COORDINATION.md) is the specification, not a limitation. **A test asserts the absence by name**, because *"we did not add one"* is not a property anything can check.

### ⚠️ This contract was `CLAIMED` and empty for a day, and another lane found it

**`people/public/__init__.py` was git's empty blob — `e69de29`, zero bytes — on `integration` and on `main`** while [TASK-457](../BACKLOG.md) read `CLAIMED`. **Lane A found it from the outside** ([C-235](../LANE_COORDINATION.md)) after **TASK-458 had been released against it**.

> **The release check asked *"does the module's `public/` exist and is it reachable?"* and the answer was yes.** ⛔ **The question it needed answered was *"does it export anything?"*** — [B-101](../BUGS.md)'s class, counting by proxy, one register over.

**Two corrections came out of it, and both are code rather than resolve:**

| | |
|---|---|
| **The contract exists** | With a test file of its own. **A contract with no test is how an empty one survives a release check** |
| **`test_boundary.py` now scans `public/` too** | It scanned only `domain/`. **The omission was not deliberate** — when it was written `public/` was empty, so scanning it would have asserted nothing. ⛔ **It is the surface that matters most**: a judgement leaking out of the domain is one module's defect; **a judgement published on the contract is one every consumer inherits.** A second test asserts the scan actually covers something, so it cannot go vacuous again

## A role change becomes an affiliation — TASK-428, S3

**`RecordRoleChange` is the use case half of *"nothing populates these tables"*.** An arrival opens an interval; a departure closes **the one the rule can identify, and no other**.

| | |
|---|---|
| **`arrived`** | Mints a `Person` and opens an `Affiliation` at that company, dated by **when it happened in the customer's business** — never by when Signora concluded it, which would put an arrival after the departure that followed it |
| **`departed`** | Reads the open affiliations at that company, asks `match_departure`, and acts on the outcome |

### ⛔ It obeys `match_departure` rather than restating it

**This document told whoever arrived here what to do, before the handler existed** — *"the handler's job is to supply the open affiliations and act on the outcome, including doing nothing on `AMBIGUOUS`, which is the case a handler is most likely to get wrong by picking one."* **The handler does exactly that and inspects `candidates` for nothing but a count.**

**Both refusals are reported, never swallowed:**

| Outcome | What happened | What is written |
|---|---|---|
| `MATCHED` | One open holder of that title | **The interval closes** |
| `NONE_OPEN` | Nobody was recorded in the role | **Nothing.** Signora never saw the arrival — the person was in post before it started watching. **Not an error** |
| `AMBIGUOUS` | Two or more hold the title | **Nothing**, and `candidate_count` travels with it so a consumer can say *"one of these two left"* rather than nothing at all |

⚠️ **`Departure` carries the outcome rather than a bare success flag**, which is [P-A](../DOMAIN_DISCOVERY_REGISTER.md) one module over: **a departure that closed nothing must never be indistinguishable from one that was never reported.**

### ⚠️ Every arrival mints a new `Person`, and it will sometimes be the same human twice

**Stated here rather than left to be found as a duplicate-person bug.** Signora holds no name, no email and no provider identifier ([C-221](../LANE_COORDINATION.md)), so **there is nothing to match an arrival against** — a heuristic on title alone would merge two strangers who share a job title.

**Joining a person across companies needs a provider identifier**, which is ❓1 of [ADR-0400](adr/0400-person-as-an-entity.md) and gates [TASK-429](../BACKLOG.md). ⛔ **Not a defect in this use case; a capability the module deliberately does not have yet.**

## ⛔ What this slice deliberately does not do

**No event handler and no subscription yet** — so nothing *calls* `RecordRoleChange` in production, and the tables stay empty until the wiring slice. **The use case is complete and unwired**, which is stated rather than dressed up: it is the same shape as the contract-first slices before it, and [441 §4](441-people-roadmap.md)'s sequencing still reads *"(none — no screen)"*.

⚠️ **And the wiring is not a small remainder.** `business_event.detected` carries `entity_id`, `type_key` and timings — **it does not carry the title or the seniority**, so a handler cannot build a `RoleChange` from the event alone. The role detail lives in `RoleChangeValue`, reachable through `provider_normalization/public`'s `ClaimReader` via the business event's evidence. **Both edges are permitted** — `people`'s import contract forbids the judging modules and neither `business_event_engine` nor `provider_normalization` is among them — **but the read path is a slice of its own, and it is the next one.**

**That is stated rather than dressed up.** Under §2 this is correct work that has not reached a customer, and it is **infrastructure rather than a delivered capability**. Consuming `LEADERSHIP_APPOINTED` / `LEADERSHIP_DEPARTED` into affiliations is **S3**, which also carries the Timeline projection and the committee-seat citation — and S3 has its own dependency: [TASK-901](../BACKLOG.md), because `make runtime-composition` reports 2 of 9 consumers wired and a projection would land dark.

**No events are published.** The ADR names five; none is emitted here, because nothing consumes them and an event catalog entry with no subscriber is the speculative structure §6 refuses.

**No `CommitteeRole` stable id.** It is `commercial_profile`'s, it is small, and its trigger is *"the first consumer that needs to cite a particular seat"* — which is S3, not this.

## How to see it

**You cannot, and that is the honest answer.** There is no screen and no endpoint. What exists is the domain a seller's question will eventually be answered from — *"who has joined and left this account, and when"* — and the tables that will hold it.

**The demonstration belongs to S3**, where an affiliation first appears on a timeline.

## For whoever takes S3

**Read `match_departure` before writing a handler.** The handler's job is to supply the open affiliations and act on the outcome — **including doing nothing on `AMBIGUOUS`**, which is the case a handler is most likely to get wrong by picking one.

**`AMBIGUOUS` carries its candidates deliberately.** A consumer can honestly say *"one of these two left"*; what it must not do is choose. If the product decides it should choose, **that is a product ruling and the rule changes here, in one place.**
