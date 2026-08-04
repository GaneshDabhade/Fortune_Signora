# 400 — Epic C · People — implementation preparation

> **Prepared by Lane C — Product Office. No code was written and none should be.** This document exists so that the lane which eventually owns Epic C spends its first day building rather than discovering. **Every claim about the repository below was verified against the source on 2026-08-04**, not against a design document.
>
>  ⚠️ **Links to [51-implementation-specifications.md](51-implementation-specifications.md) do not resolve on this branch.** Epic C's specification lives on `lane-b-commercial-profile` and reaches `main` when QE merges it. **The links are correct and are left intact**; they resolve on `integration`. Verified content is quoted inline so this document reads alone until then.
>
> **Nothing here is approved.** Epic C is unapproved scope ([Pack I](../DECISION_PACKS.md)); this is preparation so that the approval decision, when it is taken, is taken with the facts. **The ADR it needs is drafted separately as [ADR-0400](adr/0400-person-as-an-entity.md) and is `Proposed`.**

> ✅ **UNBLOCKED 2026-08-04 — [ADR-0400](adr/0400-person-as-an-entity.md) is RATIFIED.** *"Person becomes a first-class entity within the approved bounded context. Proceed on that assumption for all future preparation."* **❓1 and [C-221](../LANE_COORDINATION.md) are answered by the ruling.** This package stops being preparation-against-a-question and becomes the implementation of a decision that has been taken.


> **Approved UI** — **People Intelligence**. The [Fortune Signora Design Project](410-approved-ui-specification.md) is authoritative for frontend behaviour (2026-08-04). **This package no longer states what the screen looks like; it states what the backend must provide for it.** **The approved screen and this package's blocking question ❓1 are the same question.** The screen is entirely named individuals — roles, stances, an org chart marked confirmed-versus-inferred, a relationship graph, departures. **This package stops being a proposal about whether people are needed; it becomes the implementation of a decision the product has already made, pending [O1](../DECISION_PACKS.md).**


> **Observability, testing, operations and deployment: [405-cross-cutting-concerns.md](405-cross-cutting-concerns.md)** — written once for every prepared package rather than five times. **Epic C's deltas are in its §6 row.** In short: **Redaction must reach personal data before the first `Person` exists** — the pattern is credential-shaped and matches no name, email or phone. **`ForgetPerson` must be observable**, because a silent no-op is worse than no feature.

---

## 0 · Cross-validated 2026-08-04 — ❓1 is answered, and the answer is *no*

> **Lane A claimed Epic C as TASK-201, did exactly what [ADR-0400](adr/0400-person-as-an-entity.md) ❓1 instructed — *"check this before writing any code"* — and stopped.** **No production code was written. That is the preparation working, not failing.**

**The answer: the production provider does not return a person's name.** Verified by Lane A against source — the mapper reads `title`, `type`, `seniority`, `occurred_on`; `RoleChangeValue` has no field to carry a name; the simulator emits exactly those four keys; **the only real data in the repository is two `employee_change` records carrying exactly those four keys**; and no person-name field exists anywhere outside tests.

**This blocks the epic rather than shrinking it**, and the reason is precise: **ADR-0400's aggregate root is an identity whose first component is *"names as claims"*, and there are no name claims to make.** It is the same condition `knowledge_graph` recorded as its reason for excluding people — *no person identifier, so no identity to resolve* — **and this ADR's case was that Epic C supplies it. Nothing does.**

### Three findings from Lane A that change the package, all verified

| | Finding | Effect on this document |
|---|---|---|
| **1** | **The buying score needs no change at all.** `scoring.py` weights by `weight_for(signal.signal_type)` with **no branch per type**, so it would consume a person-subjected signal unmodified | **Removes a phase most planners would have added.** §1's *"→ Score"* row is stronger than stated: not *"already consumes both"* but *"cannot notice the difference"* |
| **2** | **The epic does not split into a blocked half and an executable half.** An interval cannot close without an identity: **pairing an appointment with a departure requires knowing they concern the same person**, and with no identifier, two VPs of Engineering appointed and one departing is unresolvable. **A single-ended interval is exactly today's behaviour** | **Corrects §9.** Phase 2 was listed as depending only on phase 1; **it depends on the name.** The tempting shortcut *"build `Affiliation` without names"* **costs a week to discover it is not there** |
| **3** | **One item remains executable, and it is Lane B's:** a **stable `CommitteeRole` id**, whose own recorded trigger has now fired — useful whichever route wins | §1's second extension trigger is now **actionable independently of the rest of the epic** |

> **Finding 2 is worth more than the split would have been.** It is the shortcut every reader reaches for first, and it does not survive contact.

**Where the epic now sits:** **`Waiting on Product Decisions`.** What remains is product direction, an architectural ratification, and **[E1](401-epic-e1-crm-read.md)'s progression** — §7 route B, which is now the only path to a named person. **None of the three is an implementation lane's to supply.**

**And a correction to Lane C's own portfolio reporting:** this package was listed as **READY, 100%**, with its blocking items given as *"ADR-0400 ratification · contact ruling."* **❓1 was documented in the package and omitted from the portfolio row** — a question that could block the epic outright was not carried into the summary a reader allocates from. **The portfolio now carries every blocking question, not only the decisions.**

---

## 1 · The finding that should decide everything else

**Signora already has complete people-shaped intelligence, and there is not one person in it.**

The pipeline runs end to end today. A provider reports that somebody senior joined or left; that becomes a claim, an observation, a business event and a scored signal; a seller sees *"New decision maker"* on an account. **At no point does anything know who the person is.**

| Stage | Module | What exists **today** | Evidence |
|---|---|---|---|
| **Ingest** | `provider_normalization` | `ClaimAttribute.ROLE_CHANGE`, carrying **`RoleChangeValue(title, seniority, direction)`** and `RoleDirection.JOINED / LEFT / PROMOTED` | `domain/vocabulary.py:144` · `mappers/enrichment.py:279–306` |
| **Interpret** | `observation_engine` | `ROLE_CHANGE` classified as **`AttributeKind.OCCURRENCE`** — a thing that happened, not a state that changed | `domain/semantics.py:66,125` |
| **Detect** | `business_event_engine` | **`LEADERSHIP_APPOINTED`** and **`LEADERSHIP_DEPARTED`**, with a seniority filter — *"a manager moving is not leadership news"* | `domain/taxonomy.py:71–72` · `domain/rules/point.py:145–198` |
| **Reason** | `signal_engine` | **`new_decision_maker`** and **`decision_maker_departed`**, both catalogued with hypothesis and rationale | `catalog/signals@1.json` · `domain/catalog.py:57–58` |
| **Score** | `buying_score_engine` | Consumes both | `scoring/scoring_model@1.json` |
| **Declare** | `commercial_profile` | **`BuyingCommittee`** — `ProductCommittee`, `CommitteeRole(title, part)`, `CommitteePart` × 5 | `domain/committee.py` |
| **Surface** | frontend | `components/commercial/committee.tsx`, shipped | CX-05 |

> **Epic C is not *"build people intelligence."* People intelligence is built and scored. Epic C is *"give it a subject."***

**That reframing is worth more than any design below**, because it changes what the epic is: not a new capability, but **an identity to attach to a capability that already runs**. The specification calls C1 an **XL** and *"the only new bounded context Epics A–B do not avoid"*. **The bounded context is genuinely new. The intelligence around it is not.**

### The repository named its own extension trigger, twice

Two modules that deliberately excluded people wrote down the exact condition under which people should arrive. **Both conditions are Epic C.**

> **`knowledge_graph/domain/identity.py:32`** — *"Person is deliberately absent: claims carry role changes but no person **identifier**, so there is no identity to resolve. Adding people now would mean inventing one."*

> **`commercial_profile/domain/committee.py:116`** — a `CommitteeRole` has no stable id, and *"nothing cites a role, and person entities — the first plausible consumer — are deferred platform-wide. **Trigger for adding one: the first consumer that needs to cite a particular seat.**"*

**Read together they are a specification.** The graph is waiting for a person *identifier* to exist; the committee is waiting for a *consumer* that cites a seat. **Epic C supplies both, and each unblocks the other.** A lane inheriting this epic is not designing against silence — it is completing a handoff two modules wrote down in advance.

---

## 2 · Product research — why a customer needs this

### The customer problem, in the customer's words

> **"Who do I call?"**

Signora can currently tell a seller that an account is worth attention, why it is worth attention, and that its leadership changed. **It cannot tell them who to contact, and it never could.** The seller closes the tab and opens LinkedIn.

**That is the shape of the gap: Signora does the expensive part and stops one step before the cheap part**, and the last step is the one that makes the previous ones actionable.

### Which personas benefit, and how the benefit differs

| Persona | What they get | Why it is different from what they have |
|---|---|---|
| **AE / SDR** | A name against a seat on the committee they already declared, and a reason to call *today* | They already know the archetype — *"we need the RevOps lead"*. **They do not know who currently holds it at this account** |
| **Sales manager** | *"Which of my accounts lost their champion this quarter?"* | The signal exists per-account; **nothing aggregates it across a book**, and nothing survives the person leaving |
| **CRO** | Coverage — *"how many of our target accounts have a named economic buyer?"* | **A measurable gap in pipeline quality** that no current screen can express |
| **RevOps / admin** | Contact data that stays correct because it is observed, not typed once | CRM contact rot is the default state; **an observed identity is the repository's existing answer to exactly this problem** for companies |

### Workflows that become possible, and only then

1. **Signal → person.** *"Decision maker departed"* becomes *"Priya Raman, VP Revenue Operations, left — she was your champion."*
2. **Committee → coverage.** The declared committee stops being a template and becomes a checklist against a real account, with holes visible.
3. **Account → approach.** Epic G's *"draft an approach"* has an addressee. **G2's specification already says it depends on C2** — *"a draft addressed to nobody is not useful."*
4. **Risk → cause.** Epic D1's champion-departure risk family becomes attributable rather than statistical.

### What competitors do, and where Signora differs

**The category solves this with a contact database** — ZoomInfo, Apollo, Cognism, LinkedIn Sales Navigator. Buy a directory, match by company, expose emails and phone numbers. **It is a well-understood product and Signora would be the ninth-best version of it.**

> **Signora's difference is not more contacts. It is that a person here would be an *observed identity with provenance*, exactly like a company.** The repository already resolves a company across disagreeing providers, records who said what and when, refuses to guess when evidence is ambiguous, and shows its working. **No contact database does any of that for people** — they return a row and no account of how they know.

**The differentiated claim, if Epic C is built on the existing model:** *"This person holds this seat, we believe it because these two providers agreed on this date, one of them has since disagreed, and here is the history."* **That is the Knowledge Graph's promise applied to a person, and it is the only version of People worth Signora building.**

**The corollary is a scope discipline:** building a bulk contact directory is the failure mode. **A directory is a different product with different economics, different legal exposure and no relationship to the pipeline this repository already runs.**

---

## 3 · Repository reuse — what must NOT be built

**This section is the most valuable one in the document**, per the standing principle. Everything below **exists, works, and is consumed**. A design that rebuilds any of it has failed the reuse audit ([L-1](../../ENGINEERING_LAWS.md)).

### Do not build — it exists

| ❌ Do not build | ✅ It already exists as | Consequence of ignoring this |
|---|---|---|
| **A "person changed job" detector** | `ClaimAttribute.ROLE_CHANGE` + `RoleChangeValue` | A second ingestion path for the same provider field |
| **A leadership-change event** | `LEADERSHIP_APPOINTED` · `LEADERSHIP_DEPARTED` | A duplicate taxonomy the signal engine cannot read |
| **A "new decision maker" insight** | Two catalogued signals, scored today | **A second scoring input for one fact**, which double-counts |
| **A seniority filter** | `rules/point.py` — *"a manager moving is not leadership news"* | Noise the repository already learned to suppress |
| **Identity resolution for people** | `knowledge_graph` resolution: provider id · exact domain · legal name + country, with `IDENTIFIED / AMBIGUOUS / …` states | **A second resolver with different semantics**, and AC-28 broken |
| **A role vocabulary** | `CommitteePart` × 5 — owned, versioned, deliberately not extensible by providers | A taxonomy nobody agreed and providers would drive |
| **A committee editor** | `committee.tsx`, shipped in CX-05 | A second screen for one declaration |
| **A history/provenance model for an attribute** | Claims + `observation_engine`, thirteen fields since M4 | The exact duplication A5 was built to avoid |
| **A per-entity activity feed** | `timeline` — a projection that owns none of its data | ADR-0038's boundary broken |
| **Workspace membership / roles / invitations** | `workspace_tenancy` — **this is Signora's own users, not the customer's contacts** | **The most dangerous confusion available in this epic.** See §4 |

### Surface rather than build

**The audit's standing finding applies here as strongly as it did to Epic A** — *fifteen modules, eighty-two events and twenty-four endpoints behind five screens.* For Epic C specifically:

- **`decision_maker_departed` already fires and is already scored.** Nothing renders *why* beyond the signal card. **Attaching a name is a render change plus an identifier, not an intelligence project.**
- **The `BuyingCommittee` declaration is already stored, versioned and surfaced.** C2 is *binding*, not authoring.
- **`observation_engine`'s HTTP surface shipped on 2026-08-03** and is generic over attributes. **A person's role history may not need a new endpoint at all** — verify before designing one.

### The one thing that genuinely does not exist

**A person identifier.** That is the whole of C1, and it is why the bounded context is new. **Everything else in Epic C is a binding, a render or a query over things that already exist.**

---

## 4 · Domain research — the bounded context

### What belongs inside People

| | |
|---|---|
| **Identity** | A person as a resolvable entity, with provider identities and a resolution state — **the same shape `EntityKind.COMPANY` already has** |
| **Affiliation** | *This person holds this title at this company, observed from this date to this date.* **A relationship with a lifecycle, not a field on a person** |
| **Naming** | The person's name as the customer's providers report it, with disagreement preserved rather than resolved by overwrite |

### What explicitly does **not** belong inside People

**Stating these prevents the module from becoming what every contact database is.**

| ❌ Not here | Where it belongs | Why |
|---|---|---|
| **Influence, seniority score, priority, "key contact"** | Nowhere yet — it is a judgement about a real deal | **The identical trap `committee.py:14` names**: a declaration is *one plausible field* away from becoming an influence model, in the module least equipped to review it |
| **Contact channels — email, phone, social** | **See §7.** A separate decision with a legal dimension, and **it must not be assumed into C1** | It changes the module's lawful basis, not just its schema |
| **Committee seat assignment** | `commercial_profile` — it owns the declaration | People supplies the identifier; **the seat stays where the seat is** |
| **Signals, events, scores about a person** | The existing engines | They already do this; a person is a *subject*, never a second pipeline |
| **Signora's own users** | `workspace_tenancy` | **Different lawful basis, different lifecycle, different tenancy.** A `Member` is a customer's employee using Signora; a `Person` is somebody at a *target account* who has never heard of Signora. **Merging them is the single worst outcome available in this epic** |

### Aggregates, entities, value objects — the proposal

> **Full reasoning and alternatives are in [ADR-0400](adr/0400-person-as-an-entity.md). Summarised here so this document reads alone.**

| | Proposal | Note |
|---|---|---|
| **Aggregate root** | **`Person`** — identity, names, provider identities, resolution state | Mirrors the company entity deliberately |
| **Entity** | **`Affiliation`** — person × company × title × interval | **Where the intelligence lives.** A departure is an affiliation ending |
| **Value objects** | `PersonName` · `ProviderPersonIdentity` · `RoleInterval` | |
| **Extends** | **`EntityKind.PERSON`** | The graph's docstring anticipates exactly this |
| **Commands** | `ResolvePersonIdentity` · `RecordAffiliation` · `EndAffiliation` · `MergePersons` · `ForgetPerson` | The last two are §11's hard cases |
| **Events** | `person.identified` · `person.affiliation_started` · `person.affiliation_ended` · `person.merged` · `person.forgotten` | **Consumed by `timeline`; must satisfy ADR-0038's projection contract** |
| **Read models** | *People at this account* · *This person's history* · **committee coverage** | The third is the one a manager wants and nothing can currently answer |

> **`Affiliation` as an entity rather than a field is the load-bearing choice.** *"Priya left Acme"* is not a mutation of Priya — it is an interval closing. **Storing a current employer as a field destroys the history the whole product is built on**, and would be the one place in this repository where a state change overwrites its own evidence.

---

## 5 · Data model — lifecycle and derived state

**Derive before storing** *(standing principle)*. Applied here:

| Fact | **Derived** or **stored** | Why |
|---|---|---|
| Person exists, with an identity | **Stored** | It is the thing that does not exist today |
| Person's name | **Stored as claims**, resolved on read | **Providers disagree about names constantly.** Storing one resolved name repeats the mistake M12.1.5 fixed for companies |
| Current employer | **Derived** — the affiliation with no end | Never a field |
| *"Left the company"* | **Derived** — an affiliation interval that closed | The existing `RoleDirection.LEFT` already says it |
| *"Is a decision maker"* | **Derived** — title matched against the declared committee | A stored flag would be a judgement, and stale within a quarter |
| **Committee coverage** | **Derived** — declared seats × affiliations at that account | **The new read model, and it stores nothing** |

**State transitions** — an affiliation is `OBSERVED → CURRENT → ENDED`, and may go `→ DISPUTED` when providers disagree. **`DISPUTED` must be a visible state and not a silent pick**, because that is what `IdentityState.AMBIGUOUS` already does for companies and the reason a seller trusts the account brief.

---

## 6 · Product workflows

### Seller — the happy path

```
account brief ─▶ "Decision maker departed" ─▶ WHO ─▶ Priya Raman, VP RevOps, left ~14 Jun
                                                │
                        committee coverage ◀────┴───▶ her seat is now unfilled
                                │
                     "Economic buyer: unknown" ─▶ the gap is the next action
```

**The workflow ends at a gap, not at a contact.** That is deliberate and it is the honest version of the product until §7 is decided.

### Manager

*"Which accounts lost a committee member this quarter?"* — a query across affiliations that ended, joined to declared committees. **No new intelligence; a read model over two things that exist.**

### Administrator

**Erasure and correction.** A person who is not a customer and never consented must be removable on request. **This is a first-class workflow, not an edge case** — see §10 and §11.

### Failure and recovery paths

| Path | Behaviour |
|---|---|
| **Provider gives a title but no name** | **The current state of the world.** The affiliation is recorded against an *unnamed seat*; the signal still fires; the screen says *"a VP of Engineering left"* — **exactly what it says today.** Epic C must degrade to today's behaviour, never below it |
| **Two providers disagree on who holds a title** | `DISPUTED`, both shown with provenance. **Never a silent winner** |
| **A person appears at two companies at once** | **Legitimate** — advisors, board seats. Two open affiliations, not a conflict |
| **Enrichment fails entirely** | Committee coverage reports *unknown*, which is honest and already the status quo |

---

## 7 · The contact-channel decision — **the one the product owner must take**

> **"Who do I call?" has two halves, and only one of them is an engineering problem.**

**Half one — *who*.** A name against a seat. **Buildable inside the repository's existing model, with the existing providers, at the existing lawful basis** (business role information about a person's professional capacity). This is C1 + C2, and it is what everything above prepares.

**Half two — *call*.** An email address or a phone number. **This is a different question and it should not be assumed into the epic.**

| Route | What it means | Assessment |
|---|---|---|
| **A** — buy contact data from an enrichment provider | Emails and phones for people who have not consented, held by Signora | **Highest legal exposure**, and the repository has **no lawful basis declared for personal data** — `committee.py:38` says so explicitly. **It also makes Signora a contact database**, which §2 argues is the wrong product |
| **B** ✅ — **read contacts from the customer's own CRM** | The customer already holds these contacts under **their** lawful basis, and already has a relationship with these people | **Recommended.** It reuses **Epic E1** entirely, adds no new provider, and the data is better — a customer's own CRM knows who actually replied |
| **C** — no contact channel at all | Signora names the seat and the person; the seller reaches them however they already do | **The correct v1**, and it is what §6's workflow describes |

> **Recommendation: C for Epic C, B when [E1](51-implementation-specifications.md) lands. Never A without an explicit ruling.**
>
> **This is not caution for its own sake — it is a dependency finding.** Routing contact through E1 means **Epic C's most legally exposed half costs nothing to build**, because E1 is already the highest-leverage item in the roadmap and is being recommended for approval on its own merits. **Two epics, one integration.**

---

## 8 · Integration analysis

| Participant | Provides | Status |
|---|---|---|
| **CoreSignal / Apollo** | `employee_changes[]` — `type`, `title`, `seniority`, `occurred_on` | **Live.** ⚠️ **No name field is mapped, and none is present in the simulator** (`simulation/generators/enrichment.py:149`). **Whether the real provider returns a name is the first thing the owning lane must verify** — it is a contract question, not a design question, and it sizes C1 |
| **Customer CRM** | Contacts, with the customer's own basis | **Unbuilt — Epic E1** |
| **`knowledge_graph`** | Resolution, `EntityKind`, ambiguity states | **Live.** Extended, not replaced |
| **`commercial_profile`** | The declared committee | **Live.** Needs a **stable role id** — the trigger it already documented |
| **`timeline`** | Projection of person events | **Live**, but ⚠️ `make runtime-composition` reports **2 of 9 consumers wired** ([TASK-901](../BACKLOG.md)). **Epic C's events would be the tenth declared and the third wired** unless TASK-901 lands first |
| **`observation_engine`** | Attribute history with provenance | **Live**, generic. **Check before building a person-history endpoint** |

**Contracts needed:** `knowledge_graph` publishes person identity · `commercial_profile` exposes a citable role id · People publishes five events · a **read model contract** for committee coverage. **Contracts that already exist:** claim ingestion, observation query, business-event and signal consumption, timeline projection.

---

## 9 · Implementation strategy — phases, and the critical path

**Five phases. Each ends at something a customer can see** — the repository's standing test.

| # | Phase | Delivers | Effort | Depends on |
|---|---|---|---|---|
| **1** | **Person identity** | `EntityKind.PERSON`, resolution, provider identities | **L** | **ADR-0400 ratified** · provider name contract verified |
| **2** | **Affiliation from role changes** | Existing `ROLE_CHANGE` claims gain a subject. **`decision_maker_departed` names a person** | **M** | Phase 1 |
| **3** | **Committee binding** *(C2)* | A declared seat cites a person. **Committee coverage** | **M** | Phase 2 · **a stable `CommitteeRole` id** |
| **4** | **Derived committee roles** *(C3)* | Inferring the seat a title fills | **L** | Phase 3 · [C-018](../LANE_COORDINATION.md) / [Pack C](../DECISION_PACKS.md) — **the same vocabulary problem** |
| **5** | **Contact channel** | *"Call"* as well as *"who"* | **M** | **[E1](51-implementation-specifications.md)**, and §7 |

> **The critical path is short and it is not code.** **ADR-0400 → the provider name contract → Phase 1.** Everything else follows and much of it parallelises.

**Parallelisable:** the committee role id (a `commercial_profile` change, **Lane B's**, and independently useful) · the coverage read model's UX · Phase 4's vocabulary work, which is Pack C's question in a new costume.

**Phases 1–3 are one lane's work end to end** and touch `knowledge_graph`, a new module, and `commercial_profile` — **all Lane B's today.** Recommending Epic C to Lane B keeps it 🟢; splitting it across lanes creates the ownership crossing this epic otherwise entirely avoids.

**Stop-after-any-phase test:** each phase leaves the product strictly better and nothing half-built. **Phase 2 alone would justify the epic** — it turns two live, scored signals from *"someone senior left"* into *"this person left."*

---

## 10 · Risks

| Class | Risk | Mitigation |
|---|---|---|
| **Product** 🔴 | **Signora becomes a contact database** and competes where it has no advantage | §2's differentiation, §4's exclusions, and **§7 route C** |
| **Legal** 🔴 | **Personal data with no declared lawful basis.** The repository has none today, and `committee.py:38` avoided people partly for this reason | **§7 route B/C.** A ruling before Phase 5, **not during it** |
| **Architectural** 🟠 | A person becomes a scoring input inside People | The `committee.py` invariant pattern — **a structural test that refuses the fields**, written in Phase 1 |
| **Architectural** 🟠 | `Person` and `workspace_tenancy.Member` converge | **Name the separation in the ADR and pin it with a test.** They are different lawful bases |
| **Data** 🟠 | Duplicate people across providers | Reuse `IdentityState.AMBIGUOUS` — **do not invent a second ambiguity model** |
| **Data** 🟠 | **Storing a current employer as a field**, destroying history | §5 — affiliation intervals, never a field |
| **Integration** 🟠 | **The provider may not return names at all** | **Verify first.** If not, Epic C's value halves and §7 route B becomes the *only* route |
| **Operational** 🟡 | Erasure requests | §11 — designed in, not retrofitted |
| **Repository** 🟡 | Timeline consumers unwired ([TASK-901](../BACKLOG.md)) | Sequence after it, or accept the projection lands dark |
| **Performance** 🟡 | Coverage joins committees × affiliations per account | Derived read model; measure before optimising |

---

## 11 · Edge cases

**Significant effort here, as directed. Each is a decision the implementing lane would otherwise have to invent.**

| Case | Recommended behaviour |
|---|---|
| **No name from the provider** | **Record the affiliation unnamed.** Degrade to today's behaviour, never below it |
| **Two people, one name** *(John Smith × 2)* | `AMBIGUOUS`. **Never merge on name** — the graph already refuses this for companies |
| **One person, two records** | `MergePersons`, **provenance preserved**, reversible. The merge is an event |
| **Conflicting titles from two providers** | `DISPUTED`, both shown. **No silent winner** |
| **Stale affiliation** — nobody reports a departure | **Confidence decays with age; the affiliation does not silently end.** *"Last observed 14 months ago"* is honest; inventing a departure is not |
| **Company merges or is acquired** | Affiliations follow the **company entity's** resolution. `ACQUISITION` already exists as a claim attribute |
| **Person returns to a former employer** | **Two affiliations, both real.** Never reopen a closed interval |
| **Person at two companies simultaneously** | Legitimate. Two open affiliations |
| **Erasure request** | **`ForgetPerson`** — identity and names removed; **the aggregate role-change evidence survives anonymised**, because *"a VP of Engineering left"* is a fact about a company. **Design this in Phase 1** |
| **Deleted CRM contact** | The CRM is authoritative for **its** contact. Signora's observed affiliation is separate and survives — **and the difference must be visible on screen** |
| **Unknown company** | An affiliation to an unresolved entity is **still recorded**; it resolves later. The graph already models this |
| **Permissions** | Person data is **workspace-scoped like everything else.** The tenancy invariant applies unchanged — **verify it, do not re-implement it** |
| **Provider disagrees with the CRM** | **Show both.** The CRM is the customer's truth; the observation is the world's. **Reconciling them silently would be the worst possible behaviour** |

---

## 12 · Definition of done

**Epic C is complete when a seller can answer *"who do I call?"* on a real account without leaving Signora — and when Signora says *"I don't know"* rather than guessing.**

| Gate | Measurable |
|---|---|
| **Capability** | `decision_maker_departed` names a person and the seat they held |
| **Capability** | Committee coverage renders per account, with gaps explicit |
| **Provenance** | Every person fact cites its provider and observation time — the same standard the company brief meets |
| **Honesty** | `AMBIGUOUS` and `DISPUTED` reach the screen and are not resolved silently |
| **Boundary** | A structural test refuses influence-scoring fields in People, as `commercial_profile` does |
| **Boundary** | A test asserts `Person` and `Member` are not joinable |
| **Privacy** | `ForgetPerson` works end to end, aggregate evidence survives anonymised |
| **Regression** | **Behaviour with no name available is exactly today's behaviour** |
| **Reuse** | **No new resolver, no new event taxonomy, no second scoring input.** Verifiable by diff |

---

## 13 · What this preparation could not settle

**Stated rather than hidden, because a package that pretends to certainty it does not have is worse than one that does not.**

1. **Does the production provider return a person's name?** The simulator does not model one and the mapper does not read one. **This is a contract question, it sizes C1, and it is the first thing to check.**
2. **The contact-channel ruling (§7).** Product owner's, with a legal dimension.
3. **Does Phase 4 need Pack C first?** *Which seat does "Head of Clinical Informatics" fill?* is [C-018](../LANE_COORDINATION.md) with a different noun. **Probably the same answer; not verified.**
4. **Effort.** Phases are **L/M/M/L/M** as estimates. **The specification's XL for C1 is not contradicted here** — it is *narrowed*, and it will only be confirmed once question 1 is answered.
