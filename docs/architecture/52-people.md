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

⛔ **No reader port, and that is the row's own bound** — *"the types `people` publishes… and nothing that reads them."* **No consumer exists yet**, and a port shaped for an imagined caller is the speculative abstraction §6 forbids. **The first consumer is [TASK-458](../BACKLOG.md)** — `signal_engine`, Lane A's — and the port is designed when there is a caller to design it against.

**What it publishes is a subject, never an identity.** No name, no email, no phone, no provider id — [C-221](../LANE_COORDINATION.md) is the specification, not a limitation. **A test asserts the absence by name**, because *"we did not add one"* is not a property anything can check.

### ⚠️ This contract was `CLAIMED` and empty for a day, and another lane found it

**`people/public/__init__.py` was git's empty blob — `e69de29`, zero bytes — on `integration` and on `main`** while [TASK-457](../BACKLOG.md) read `CLAIMED`. **Lane A found it from the outside** ([C-235](../LANE_COORDINATION.md)) after **TASK-458 had been released against it**.

> **The release check asked *"does the module's `public/` exist and is it reachable?"* and the answer was yes.** ⛔ **The question it needed answered was *"does it export anything?"*** — [B-101](../BUGS.md)'s class, counting by proxy, one register over.

**Two corrections came out of it, and both are code rather than resolve:**

| | |
|---|---|
| **The contract exists** | With a test file of its own. **A contract with no test is how an empty one survives a release check** |
| **`test_boundary.py` now scans `public/` too** | It scanned only `domain/`. **The omission was not deliberate** — when it was written `public/` was empty, so scanning it would have asserted nothing. ⛔ **It is the surface that matters most**: a judgement leaking out of the domain is one module's defect; **a judgement published on the contract is one every consumer inherits.** A second test asserts the scan actually covers something, so it cannot go vacuous again

## ⛔ What this slice deliberately does not do

**Nothing populates these tables.** No event handler, no use case, no endpoint, no screen — and [441 §4](441-people-roadmap.md) says so in its own sequencing: this milestone is *"(none — no screen)"*.

**That is stated rather than dressed up.** Under §2 this is correct work that has not reached a customer, and it is **infrastructure rather than a delivered capability**. Consuming `LEADERSHIP_APPOINTED` / `LEADERSHIP_DEPARTED` into affiliations is **S3**, which also carries the Timeline projection and the committee-seat citation — and S3 has its own dependency: [TASK-901](../BACKLOG.md), because `make runtime-composition` reports 2 of 9 consumers wired and a projection would land dark.

**No events are published.** The ADR names five; none is emitted here, because nothing consumes them and an event catalog entry with no subscriber is the speculative structure §6 refuses.

**No `CommitteeRole` stable id.** It is `commercial_profile`'s, it is small, and its trigger is *"the first consumer that needs to cite a particular seat"* — which is S3, not this.

## How to see it

**You cannot, and that is the honest answer.** There is no screen and no endpoint. What exists is the domain a seller's question will eventually be answered from — *"who has joined and left this account, and when"* — and the tables that will hold it.

**The demonstration belongs to S3**, where an affiliation first appears on a timeline.

## For whoever takes S3

**Read `match_departure` before writing a handler.** The handler's job is to supply the open affiliations and act on the outcome — **including doing nothing on `AMBIGUOUS`**, which is the case a handler is most likely to get wrong by picking one.

**`AMBIGUOUS` carries its candidates deliberately.** A consumer can honestly say *"one of these two left"*; what it must not do is choose. If the product decides it should choose, **that is a product ruling and the rule changes here, in one place.**
