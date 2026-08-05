# ADR-0400: A person becomes an entity — Epic C's bounded context

## Status

**PRODUCT OWNER APPROVED — 2026-08-04.** ✅ **On `origin/integration` since 2026-08-05, and actionable.** *(This block warned ⚠️ "not yet on `origin/integration` — this file does not exist there" for a day after it did. **A lane obeying that warning would have declined to act on a ruling the repository already carried** — the exact failure the five decision states exist to prevent, in the file that names them. Found by Lane A as [B-205](../../BUGS.md).)* Drafted by Lane C — Product Office. **Person becomes a first-class entity within the approved bounded context, and all future preparation proceeds on that assumption.**

> **It was the only architectural blocker in all 26 approved screens.** Ratification releases Epic C, People Intelligence, half of Global Search, the four *Decision makers* criteria in the ICP Builder, and Account 360's contacts and org-chart sections. **[C-221](../../LANE_COORDINATION.md) is answered by it and needs no separate ruling.**

**Complete: five alternatives assessed, one recommended.** ⚠️ **❓1 is answered — the provider returns no person name** ([C-221](../../LANE_COORDINATION.md)).

> ## ⚠️ Superseded in part, 2026-08-05 — [D-074](../../DECISION_REGISTER.md)
>
> **This block said ratification *"neither approves nor unblocks Epic C"*, and that ❓1 *"blocks the epic"*. Both were true when written and a later product-owner decision changed them.**
>
> **[D-074](../../DECISION_REGISTER.md), ruled 2026-08-05:** *"I approve moving the **People domain** implementation earlier in the roadmap. **I am not approving the full People Intelligence feature set.**"*
>
> **So the approval this ADR declined to give now exists, and it is scoped**: **the domain is approved; the feature set is not.** **[441](../441-people-roadmap.md) separates them into four milestones with four triggers, and ❓1 gates [TASK-429](../../BACKLOG.md) — provider enrichment — rather than the entity**, because an anonymous `Person` with `Affiliation` intervals needs no person name and is derived from data that already flows.
>
> **What still holds unchanged:** *ratifying this ADR is not approving the epic*. **It is [D-074](../../DECISION_REGISTER.md) that approves the domain, not this ratification** — and a row citing this ADR as its authority to build is citing the wrong document. **[TASK-427](../../BACKLOG.md) now cites D-074.**

> **Lane C prepares decisions; the product owner makes them.** This ADR exists so the lane that eventually owns Epic C **inherits a decision rather than re-debating one**. It follows the route [ADR-0035](0035-commercial-profile.md) and [ADR-0038](0038-timeline.md) took: draft first, ratify, then build — **never the other way round.**
>
> **Epic C is unapproved scope** ([Pack I](../../DECISION_PACKS.md)). Ratifying this ADR does not approve the epic; approving the epic does not ratify this ADR. **Both are the product owner's, and they are separate.**

✅ **`../51-implementation-specifications.md` resolves — it reached `integration` and the warning that said otherwise is cleared, 2026-08-05.** *(Second stale-location claim in this status block, same day, same cause: a warning written about a branch state and never revisited once the state changed.)*

**Three questions are deliberately left open and marked ❓.** Each is a product or legal call, not an architectural one.

## Context

**Every persona in the product review asked *"who do I call?"* and nothing answers.** The specification calls C1 an **XL** and *"the only new bounded context Epics A–B do not avoid."*

**The context is genuinely new. The intelligence is not** — and that is the fact this ADR turns on.

Verified against source, 2026-08-04 — the full trace is in [400-epic-c-people.md](../400-epic-c-people.md) §1:

> A provider reports a role change → `ClaimAttribute.ROLE_CHANGE` carries **`RoleChangeValue(title, seniority, direction)`** → `observation_engine` classifies it an **occurrence** → `business_event_engine` emits **`LEADERSHIP_APPOINTED` / `LEADERSHIP_DEPARTED`** → `signal_engine` emits **`new_decision_maker` / `decision_maker_departed`** → the buying score consumes both.
>
> **Six modules, running in production, and not one of them knows a person's name.**

**Two modules excluded people deliberately and wrote down the condition for their arrival.** `knowledge_graph/domain/identity.py:32` — *"Person is deliberately absent: claims carry role changes but no person **identifier**, so there is no identity to resolve."* `commercial_profile/domain/committee.py:116` — a committee role has no stable id because *"nothing cites a role… **Trigger for adding one: the first consumer that needs to cite a particular seat.**"*

**Both conditions are this ADR.** The graph needs a person identifier to exist; the committee needs a consumer that cites a seat. **Epic C supplies each with the other.**

**What the architecture already fixes and this ADR does not reopen:** identity resolution semantics (ADR-0035) · the claim/observation provenance model · the business-event taxonomy · the signal catalog · the timeline projection contract (ADR-0038) · the canonical vocabulary principle (ADR-0034) · workspace tenancy.

## Decision

### The boundary, in one line

> **People knows who somebody is and where they have worked. It never decides what any of that means about a deal.**

**The same discipline `commercial_profile` and `timeline` already hold, from a third direction.** Commercial Profile records and computes nothing; Timeline projects and computes nothing; **People identifies and computes nothing.** Every judgement — is this person important, is this committee covered, does this departure matter — belongs to modules that already make judgements and already have evidence to make them from.

**The temptation is specific and worth naming**, exactly as `committee.py` named its own: **a person is one plausible field away from becoming an influence model.** `seniority_score`, `is_key_contact`, `priority`, an ordered list read as a ranking — each turns an identity into a scoring input, in the module least equipped to review it. **A structural test refuses the words, as `test_boundary.py` already does for the committee.**

### The model

| | | |
|---|---|---|
| **Aggregate root** | **`Person`** | Identity · names as claims · provider identities · resolution state |
| **Entity** | **`Affiliation`** | person × company × title × **interval**. *This is where the intelligence lives* |
| **Value objects** | `PersonName` · `ProviderPersonIdentity` · `RoleInterval` | |
| **Graph** | **`EntityKind.PERSON`** joins `COMPANY` and `TECHNOLOGY` | The docstring anticipated it |
| **Events** | `person.identified` · `person.affiliation_started` · `person.affiliation_ended` · `person.merged` · `person.forgotten` | Projected by `timeline` |

**`Affiliation` as an entity rather than a field is the load-bearing choice.** *"Priya left Acme"* is not a mutation of Priya — **it is an interval closing.** Storing a current employer as a field would destroy the history the entire product is built on, and would be **the one place in this repository where a state change overwrites its own evidence.**

### What People does not own

**Contact channels** — see ❓2. **Committee seat assignment** — `commercial_profile` owns the declaration; People supplies only the identifier it cites. **Signals, events and scores about a person** — the existing engines, unchanged; a person is a *subject*, never a second pipeline. **Signora's own users** — `workspace_tenancy`, and the separation is load-bearing: **a `Member` is a customer's employee using Signora; a `Person` is somebody at a target account who has never heard of Signora.** Different lawful basis, different lifecycle. **Pinned by a test asserting the two are not joinable.**

## Alternatives considered

| | Option | Why not |
|---|---|---|
| **A** ✅ | **A new `people` module, `EntityKind.PERSON` in the graph** | **Recommended.** Reuses resolution, provenance and ambiguity wholesale; the new context is genuinely new; the boundary is stateable in one sentence |
| **B** | **People inside `knowledge_graph`** | The graph resolves *identity*; affiliation intervals are a different lifecycle with a different erasure story. **It would put personal data in the module every other module reads**, and make `ForgetPerson` a cross-cutting concern instead of a local one |
| **C** | **People inside `commercial_profile`** | That module *records what a customer declares about their own business.* **A person at a target account is neither declared nor theirs**, and `committee.py` argues this against itself already |
| **D** | **A person as a field on the committee role** | **Destroys history** (§Decision), cannot represent a person at two companies, and gives erasure nowhere to happen |
| **E** | **Buy a contact database and expose it** | **A different product.** No provenance, no ambiguity, no differentiation — and the legal exposure of ❓2 without the benefit of ❓2's cheaper route |

## Consequences

**Positive.** Two live, scored signals gain a subject — **the smallest change with the largest visible effect in the epic.** The committee stops being a template. **Epic G2 becomes possible** — its specification already says *"a draft addressed to nobody is not useful."* **Epic D1's champion-departure family becomes attributable.** And the graph's own documented gap closes.

**Negative, and stated plainly.** A new bounded context is 🔴 under §6 and needs this ADR. **Personal data enters the repository for the first time**, which is a standing operational obligation and not a one-off task. **`commercial_profile` must add a stable role id** — small, Lane B's, and it is the trigger that module already wrote down.

**Neutral.** People publishes five events and consumes none it does not already have access to. ⚠️ **`make runtime-composition` reports 2 of 9 consumers wired** ([TASK-901](../../BACKLOG.md)) — **People's timeline projection would land dark unless that is sequenced first.**

## Open questions

> **❓1 · Does the production provider return a person's name?**
>
> **Nothing in this repository can answer it.** `mappers/enrichment.py:279–306` reads `title`, `type` and `seniority`; the simulator (`simulation/generators/enrichment.py:149`) models no name field. **This is a provider-contract question, and it sizes C1.** If the answer is no, Phase 2 of the strategy degrades to *"a VP of Engineering left"* — **today's behaviour** — and ❓2's route B becomes the only path to a named person. **Check this before writing any code.**

> **❓2 · May Signora hold contact channels — email, phone — for people who have not consented?**
>
> **Product and legal, not architectural.** The repository has **no lawful basis declared for personal data**, and `committee.py:38` gives that as one reason people were excluded. **Three routes, assessed in [400-epic-c-people.md](../400-epic-c-people.md) §7. Lane C recommends: no contact channel in Epic C; read contacts from the customer's own CRM when [E1](../51-implementation-specifications.md) lands, under the customer's own basis; never buy contact data without an explicit ruling.** The recommendation is also the cheapest — **it reuses an integration already recommended for approval on its own merits.**

> **❓3 · Does deriving a committee seat from a job title (C3) need [Pack C](../../DECISION_PACKS.md) first?**
>
> *"Which seat does 'Head of Clinical Informatics' fill?"* is **[C-018](../../LANE_COORDINATION.md) with a different noun** — nobody owns the mapping from a customer's words to a canonical value. **Lane C's assessment is that it is the same question and Pack C's ruling should govern both**, but this was not verified in depth. **It affects Phase 4 only; Phases 1–3 are unaffected either way.**

## Compliance

**This ADR is `Proposed`. There is nothing to comply with yet.** On ratification, compliance is: the boundary test refusing scoring fields · the test asserting `Person` and `Member` are not joinable · `ForgetPerson` end to end with aggregate evidence surviving anonymised · **and the regression that matters most — with no name available, behaviour is exactly what it is today.**
