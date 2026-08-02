# Lane coordination register

> **The single place to answer *"what am I waiting on?"*** — created 2026-08-01 on the product owner's direction, before a fourth lane makes the question expensive.
>
> **Why now rather than later.** With two or three lanes, coordination happens in conversation and in commit messages. With five or six it does not: a question raised inside an implementation report is invisible to everybody who did not read that report, and the lane that could answer it in thirty seconds never learns it was asked. This is the smallest artifact that fixes that, and it is deliberately not a workflow.

## What this is, and what it is not

| It is | It is not |
|---|---|
| A register of **decisions one lane needs from somewhere else** before it can safely continue | **A bug tracker** — that is [`BUGS.md`](BUGS.md). A defect has an owner and a fix; a coordination item has a *question* and an answer |
| A place to record **contracts being negotiated between lanes** | **A roadmap** — that is `IMPLEMENTATION_ROADMAP.md` and `PRODUCT_ROADMAP.md`. Nothing here schedules anything |
| The record of **why a lane stopped** | A design document. The design lives in the module's own doc; this holds the question and the answer |

**A coordination item exists because implementation cannot safely continue without an answer.** If work can proceed under a stated assumption, it is a finding for the module's design document, not an item here.

## How it works

**Any lane may open an item.** The **named owner** answers it. The **requesting lane** moves it to `IMPLEMENTING` and then `CLOSED`, because only the requester knows whether the answer was sufficient.

**An answer is not a conversation — it is a decision with a home.** Every `ANSWERED` item names the commit, ADR or document that carries it, so the answer outlives the exchange that produced it.

| Status | Meaning |
|---|---|
| `OPEN` | Raised. The owner has not yet seen it |
| `WAITING` | The owner has it, and the requesting lane is blocked |
| `ANSWERED` | Decided, with the commit or ADR named. Implementation may begin |
| `IMPLEMENTING` | The requesting lane is building against the answer |
| `CLOSED` | Built and merged, or withdrawn with a reason |

**Ids are `C-nnn`, allocated sequentially and never reused.**

**A lane reads this before starting a slice**, alongside [`BUGS.md`](BUGS.md) and [`RUNNING.md`](RUNNING.md).


> **Two lanes allocated `C-001`…`C-009` independently on 2026-08-02**, while the repository ran on two baselines. The items promoted to `main` keep their numbers; **QE renumbered the later set** — `lane-qe`'s C-001 → [C-010](#c-010--no-lane-is-assignable-to-apps-or-signora_platform-and-a-defect-is-sitting-in-one), C-003 → C-011, C-004 → C-012, C-005 → C-013, C-007 → C-014, C-008 → C-015, C-009 → C-016.
>
> **Two were dropped rather than renumbered, because they had already been answered:** *the target-account list gives Provider Platform the subject it has never had* is [C-001](#c-001--the-target-account-contract), answered by [ADR-0036](architecture/adr/0036-target-account-contract.md); and *ICP is named in five documents and owned by no milestone* was answered by M12.5 shipping it. **An id, once promoted, is never reused for a different question.**

---

## What is waiting

| Id | What | Requester | Owner | Status | Blocks |
|---|---|---|---|---|---|
| [C-001](#c-001--the-target-account-contract) | The target-account contract — this module's first edge | Lane B | **Lane A** | `ANSWERED` → **[ADR-0036](architecture/adr/0036-target-account-contract.md)** | **Nothing. Slice 5 may begin.** `CLOSED` when both lanes have built it |
| [C-002](#c-002--customer-language-has-no-anticorruption-layer) | Customer language has no anticorruption layer | Lane B | **Product owner** (ADR) | `OPEN` | Anything that matches an account against an ICP |
| [C-003](#c-003--three-wire-codes-for-one-condition) | Three wire codes for one condition | Lane B | **Product owner** | `OPEN` | Nothing. **It stopped growing** — slice 5 cites no product |
| [C-004](#c-004--shared-documents-lag-commercial-profile) | Shared documents lag Commercial Profile | Lane B | **QE** | `OPEN` | Nothing today; a cold session reads a stale manifest |
| [C-005](#c-005--who-owns-the-signal-profile-write-path) | Who owns the signal-profile write path | Lane B | **Product owner** / Lane A | `ANSWERED` — ownership. **Sequencing still the product owner's** | The first customer-editable relevance profile |
| [C-006](#c-006--which-lane-owns-test_api_modulepy) | Which lane owns `test_api_<module>.py` | Lane B | **Product owner** | `OPEN` | Nothing — a standing ambiguity in §20e |
| [C-007](#c-007--the-guided-first-run-is-a-two-lane-build) | The guided first run is a two-lane build | Lane B | Lane A + **product owner** | `ANSWERED` — routing and navigation. **Sequencing still the product owner's** | Sequencing after M12.5 slice 5 |
| [C-008](#c-008--sellers-cannot-see-what-their-company-sells) | Sellers cannot see what their company sells | Lane B | **Product owner** + QE | `OPEN` | Nothing today. Every AE and SDR, every day |
| [C-009](#c-009--an-internal-fault-reaches-a-customer-as-a-422) | An internal fault reaches a customer as a `422` | Lane A | **Product owner** (platform §20a) | `OPEN` | Nothing today. Splitting the error hierarchy in any module |
| [C-010](#c-010--no-lane-is-assignable-to-apps-or-signora_platform-and-a-defect-is-sitting-in-one) | No lane is assignable to `apps/` or `signora_platform/` | QE | **Product owner** | `OPEN` | [B-007](BUGS.md) and [B-012](BUGS.md) sit in exactly this gap |
| [C-011](#c-011--a-contraction-risk-reads-like-a-small-opportunity-on-the-attention-list) | A contraction risk reads like a small opportunity on the attention list | QE | **Product owner** | `OPEN` | R9-03 only. The rest of the surface proceeds |
| [C-012](#c-012--eventhandler-receives-no-session-so-no-module-handler-is-registered) | `EventHandler` receives no session, so no module handler is registered | QE | **Product owner** (platform §20a) | `WAITING` — RFC queued since M3A | Every module that wants to consume an event |
| [C-013](#c-013--publishableevent-cannot-be-satisfied-by-a-frozen-dataclass) | `PublishableEvent` cannot be satisfied by a frozen dataclass | QE | **Product owner** (platform §20a) | `WAITING` — RFC queued since M3A | Nothing today; every new event pays the workaround |
| [C-014](#c-014--accessibility-and-performance-testing-are-qes-and-neither-exists) | Accessibility and performance testing are QE's, and neither exists | QE | **Product owner** (a milestone number) | `OPEN` | Nothing. **§20c already treats an accessibility issue as a defect class** |
| [C-016](#c-016--two-branch-names-encode-a-permanent-module-assignment-that-no-longer-exists) | Two branch names encode a permanent module assignment that no longer exists | QE | **Product owner** | `OPEN` | Nothing. It misleads every lane that reads `git branch` |

---

## C-001 · The target-account contract

| | |
|---|---|
| **Owner** | **Lane A** — Provider Platform |
| **Requesting lane** | Lane B — Commercial Profile |
| **Category** | Event contract · read-port ownership · **Customer–Supplier relationship** |
| **Status** | `ANSWERED` — Lane A, `f6b6a41`. **Ratified as [ADR-0036](architecture/adr/0036-target-account-contract.md)**, 2026-08-02 |
| **Blocks** | **Nothing. Lane B may begin slice 5** |
| **Closes when** | Both lanes have implemented. Lane B publishes the event and the port; Lane A builds the consumer and fixes [`B-004`](BUGS.md) in the same slice |
| **Raised** | `3931b3c`, at the close of slice 4 |

**Why this is not a normal design decision.** Slice 5 introduces `commercial_profile → provider_platform` — **the first and only edge this module has ever had**, and the first time anything downstream consumes a customer's declaration. [05-module-dependencies.md](architecture/05-module-dependencies.md) types it **Customer–Supplier**, whose stated rule is that *the downstream lane's needs shape the contract*. Drawing it alone and asking afterwards would produce a contract shaped by the producer — which is the one failure this pattern exists to prevent.

It also closes a gap open since M2.1: `RunProviderSync` has taken a `subject: str` for four milestones and **nothing has ever supplied one**.

### Questions requiring answers

| # | Question | Lane B's opening position |
|---|---|---|
| 1 | **Event or read port for the first delivery?** | The ADR says `commercial_profile.target_accounts_changed`. A `TargetAccountReader` on `public/` is also planned. Both can exist; which does Provider Platform actually consume first? |
| 2 | **What does the event carry?** | **Identity and change only** — `workspace_id`, the declaration version, and that it changed. *Events carry identity; ports carry payload.* Embedding account names would make every future field an event-contract change |
| 3 | **The list, or the delta?** | Lane B can publish either. A delta is more useful and less durable; the whole list is what the aggregate actually is |
| 4 | **Does `subject` stay a `str`?** | Lane B declares a company **as the customer names it** — a name, unresolved, unmatched. If Provider Platform needs anything more (a domain, a country), it needs saying now, because Lane B will not resolve it |
| 5 | **Removal semantics.** | A customer un-watching an account is a declaration, and Lane B records it. Whether polling stops, and what happens to what was already gathered, is **Provider Platform's** decision — Lane B will not model it |
| 6 | **Scheduling and lifecycle ownership.** | **Not here.** No cadence, no polling policy, no cost, no provider selection enters Commercial Profile. Confirming this is the point of the question |
| 7 | **Versioning expectations.** | The declaration is versioned and immutable like the other four. Does Provider Platform want the version in the event so it can ignore replays, or will it be idempotent on `event_id` alone? |

> **The permanent decision now lives in [ADR-0036](architecture/adr/0036-target-account-contract.md)**, on the product owner's direction, together with four ownership boundaries ratified alongside it. **Read the ADR, not this section** — what follows is the working answer it was distilled from, kept until this item is `CLOSED` so the reasoning stays beside the question that produced it.

### Resolution — Lane A, 2026-08-01

**Answered by the module that owns the downstream side, question by question. Lane B's opening position is accepted on five of seven; two are answered differently, and one of those is because Provider Platform found a defect of its own while answering.**

#### 1 · Event *and* read port — and they do different jobs

**`commercial_profile.target_accounts_changed` is what Provider Platform consumes. `TargetAccountReader` is what its handler then calls.** Not a choice between them: the event is the *trigger*, the port is the *payload*, which is this repository's standing rule stated the other way round.

The reason it is not a read port alone: a port makes Provider Platform *pull*, and pulling needs a trigger anyway. The only honest trigger is *"the customer changed their mind"*, and that is an event by definition.

The reason it is not an event alone: see question 2.

#### 2 · Identity and change only — **accepted, unchanged**

`workspace_id` on the envelope, `declaration_version` in the payload, nothing about accounts. Lane B's reasoning is exactly right and needs no addition: embedding names would make every future field an event-contract change, and Provider Platform would be reading a copy of a truth that lives somewhere else.

#### 3 · The whole list — **Lane B's second option, and for a third reason neither of us named**

Lane B offered either. **Provider Platform wants the list**, and the deciding argument is not durability:

**A delta from Lane B answers the wrong question.** It is a delta between two *declarations*. What Provider Platform needs is a delta against **what it has actually synced**, which is a different set — a customer can re-add an account that was declared before and never successfully fetched, and Lane B's delta would call that "no change". Provider Platform owns `provider_watermark` and can compute the only delta that matters.

Also: a whole list is idempotent to apply and a delta is not, which matters on a bus with at-least-once delivery.

#### 4 · `subject` stays a `str`, and stays **unresolved** — **accepted, and confirmed in the strongest terms**

`ProviderRequest.subject` is documented as *"domain identifier of the subject (a company key, a domain name)"* and is **opaque to the platform, interpreted only by the adapter**. A name as the customer typed it is exactly what belongs there.

**Provider Platform does not want a domain, a country, or anything else.** Asking Lane B for a domain would be asking a customer to do resolution, and resolution quality is Signora's competence, not the customer's (ruled 2026-08-01). If an unresolved name is a weak key for some provider, **that is the adapter's problem to solve and the Provider Platform's to own** — which is the whole reason `subject` is opaque.

**One request, and it is small:** send the entry's **stable id** alongside the name. Not for matching — so that a customer *renaming* an entry is distinguishable from *removing one and adding another*, which are different instructions about spending money.

#### 5 · Removal — **Provider Platform's decision, made here**

**Polling stops.** A customer who un-watches an account has said not to spend on it, and continuing would be the platform overriding them.

**Nothing already gathered is deleted.** Raw provider records are evidence, and the Knowledge Graph, observations, business events, signals, scores and every narration downstream cite them. Deleting them would erase the basis of conclusions a customer has already read and acted on. *Erasability is a property of the tenancy model* — it belongs to deleting a workspace, not to un-watching a company.

**The watermark stays.** Re-adding an account then resumes incrementally instead of re-fetching a full snapshot, which is a real cost saving that requires nothing to be built.

#### 6 · Scheduling and lifecycle are **entirely Provider Platform's** — confirmed

No cadence, no polling policy, no cost model, no provider selection, no failover, no backoff enters Commercial Profile. This is not a boundary being negotiated; it is the 2026-08-01 provider ruling applied: **a customer declares who they care about and never how Signora finds out about them.**

#### 7 · Send the version — and the reason is ordering, not replay

Idempotency on `event_id` handles **redelivery**. It does not handle **ordering**: two declarations in quick succession are two workspace-level events, and per-entity ordering does not order them against each other. A handler for v5 running after v6's would sync a list that is one revision stale.

So `declaration_version` on the payload, and Provider Platform will **ignore an event older than the version it has already acted on.** That is a comparison it can make locally with no coordination, and it is why the version has to be on the wire rather than only in the aggregate.

---

### What Lane A found while answering, and is not asking Lane B to solve

**`provider_watermark` is keyed `(workspace_id, provider, capability)` — it has no `subject`.**

One workspace watching one company is the only case that has ever existed, so nothing has noticed. The moment a customer declares a second target account, syncing the first advances a watermark the second then reads, and the second account's sync silently skips everything before that point. **A customer would see one account enriched and another mysteriously thin.**

This is **Provider Platform's defect, not a contract problem**, and it does not block Lane B: it lives entirely on the consuming side, which Lane A has not built yet. Opened as **`B-004`** and owned by Lane A, to be fixed in the slice that builds the consumer.

**Stated here rather than only in the bug register** because it is the sort of thing a downstream lane would reasonably assume was already handled, and C-001 exists precisely so that assumptions like that get said out loud.

---

### Lane B accepts the contract, and records what it changes

*Added 2026-08-01 by Lane B, on reading the answer. Accepted in full, including both places Lane B was wrong.*

**Where Lane B was wrong, and the reasoning is worth keeping.** The delta position (question 3) answered the wrong question: a delta between two *declarations* is not the delta that matters, because what Provider Platform must reconcile is the gap against **what it has actually synced** — and a customer can re-add an account declared long ago and never fetched. The whole list is also idempotent under at-least-once delivery and a delta is not. Lane B withdraws the position.

**Three consequences for slice 5, recorded before any code exists:**

1. **A target account entry needs a stable id** (question 4). Slice 3 deliberately gave `CommitteeRole` none, with the trigger recorded as *"the first consumer that needs to cite a particular seat"*. **That trigger has now fired for a different aggregate**, and for exactly the stated reason: without an id, a rename is indistinguishable from a remove-and-add, and those are different instructions about spending money. The entry follows `Product` — client-chosen id, stable across revisions.
2. **`declaration_version` travels on the event** (question 7), and the reason is **ordering, not replay**. Lane B had assumed idempotency on `event_id` covered it; it does not order two workspace-level events against each other. This is a payload field Lane B would not have included on its own reasoning.
3. **The event carries identity and change only** (question 2), and **`TargetAccountReader` on `public/` carries the payload** (question 1). Both, doing different jobs — the port would otherwise make Provider Platform pull, and pulling needs a trigger anyway.

**Acknowledged and not acted on:** `B-004` is Provider Platform's, on the consuming side, and Lane B will not design around it. Saying it out loud is what stopped Lane B assuming it was handled.

**This item is `ANSWERED`, not `CLOSED`, and closing it needs somebody else.** The contract is agreed but not yet *permanent*: its home is [`06-events.md`](architecture/06-events.md) (the event catalog) and the matrix row in [`05-module-dependencies.md`](architecture/05-module-dependencies.md), both 🔴 and outside both lanes' budgets. **Lane B will publish the event in slice 5 and record the contract in [40-commercial-profile.md](architecture/40-commercial-profile.md); the integrator folds it into `06` in the same merge.** Until that happens the catalog does not list an event the platform emits, which is the kind of untruth `CLAUDE.md` §2 names specifically.

---

## C-002 · Customer language has no anticorruption layer

| | |
|---|---|
| **Owner** | **Product owner** — needs an ADR |
| **Requesting lane** | Lane B |
| **Category** | Architecture clarification · ADR requirement |
| **Status** | `OPEN` |
| **Blocks** | **Nothing in M12.5.** It must be answered before anything matches an account against an ICP |
| **Raised** | `30e66d0` as F-B1; sharpened at `960b604` |

Provider Normalization is an **anticorruption layer for vendor vocabulary** — it exists so provider models cannot leak inward, and it is the clearest ACL in the codebase. **Nothing plays that part for customer vocabulary.** A customer's *"United States"*, *"Fintech"*, *"mid-market"* must eventually meet a canonical claim, and the component that does that is unbuilt and unowned.

[ADR-0035](architecture/adr/0035-commercial-profile.md) answers half of it: resolution *among disagreeing claims* is a Knowledge Graph slice. It does not answer *whose job it is to know that "Fintech" and the canonical industry value are the same thing.*

**Question.** Three candidate homes, none chosen: the Knowledge Graph (it already resolves) · a new matching context (a distinct concern with a distinct failure mode) · a translation table owned by Commercial Profile — **which Lane B rejects**, because it would make the recording module resolve, and it is the module least equipped to review a resolution.

---

## C-003 · Three wire codes for one condition

| | |
|---|---|
| **Owner** | **Product owner** |
| **Requesting lane** | Lane B |
| **Category** | API contract |
| **Status** | `OPEN` |
| **Blocks** | Nothing — **but it gets worse with every slice** |
| **Raised** | `960b604` as F-B7 |

`icp_unknown_product`, `committee_unknown_product`, `focus_unknown_product`: **one shared check, one shared message, three wire codes**, and slice 5 makes it four. A single neutral `unknown_product` is the right shape.

**Question.** May Lane B rename them? Renaming a shipped code is ⚫ in the Change Budget, so Lane B will not take it unilaterally — even though every consumer is Lane B's own frontend, which reads the message rather than the code.

---

## C-004 · Shared documents lag Commercial Profile

| | |
|---|---|
| **Owner** | **Integrator** |
| **Requesting lane** | Lane B |
| **Category** | Architecture documentation |
| **Status** | `OPEN` |
| **Blocks** | Nothing today. A cold session reads a manifest that is four rows out of date |
| **Raised** | `30e66d0` as F-B3, growing each slice |

`docs/architecture/01`–`21` are 🔴 and Lane B may not edit them. Accumulated, with the exact edits:

- **[04-modules.md](architecture/04-modules.md), Commercial Profile manifest** → **Endpoints**: add `/workspaces/{id}/icp`, `/workspaces/{id}/buying-committee`, `/workspaces/{id}/focus`. **Tables**: add `icp_declaration`, `buying_committee`, `commercial_focus`.
- **Same entry, *Owns*** → *business priorities* is built as **`CommercialFocus`**, deliberately not a ranking. The word `priority` invites an ordinal, and the module's own invariant refuses it.
- **Same entry, *Public contracts* and *Events produced*** → both said *"none yet"*. Slice 5 shipped `TargetAccountReader` and `commercial_profile.target_accounts_changed`.
- **[05-module-dependencies.md](architecture/05-module-dependencies.md)** → the read-port table gains `TargetAccountReader → TargetAccountListView` (owner Commercial Profile, consumer Provider Platform). **The graph and the matrix already show the edge**; only the port table is missing it.
- **The Canonical Vocabulary Principle** ([40](architecture/40-commercial-profile.md#the-canonical-vocabulary-principle)) is written in the module doc because Lane B may not edit `04`. Its cross-module form belongs beside the provider-configuration ruling it extends.
- **`06-events.md` does not list an event the platform now emits.** Slice 5 publishes `commercial_profile.target_accounts_changed` and §9 requires the catalog to be updated *in the same change*; the catalog is 🔴 and Lane B may not write it. **This is the most consequential row in this item** — the others are stale text, this one is a live omission. Ready to paste:

  | Field | Value |
  |---|---|
  | **Event type** | `commercial_profile.target_accounts_changed` |
  | **Version** | 1 |
  | **Producer** | `commercial_profile` |
  | **Consumer** | Provider Platform (unbuilt — Lane A) |
  | **Payload** | `declaration_version: int`, and nothing else |
  | **Why so small** | Identity and change only. The list is read through `TargetAccountReader`; the version is there for **ordering, not replay** ([ADR-0036](architecture/adr/0036-target-account-contract.md) §3, §7) |
  | **Emitted** | On every accepted declaration, including one that empties the list |

- **This register needs a pointer from [`README.md`](../README.md) §Parallel development, `CLAUDE.md` §20e, and the header of [`BUGS.md`](BUGS.md)** — or the lanes told to read it will not find it. Lane B has edited none of the three: the first two are outside its budget and the third is QE's prose.

**No dependency edge has changed** in slices 1–4. Nothing new is imported, nothing published, the graph untouched.

---

## C-005 · Who owns the signal-profile write path

| | |
|---|---|
| **Owner** | **Product owner** / Lane A |
| **Requesting lane** | Lane B |
| **Category** | Module ownership |
| **Status** | `OPEN` |
| **Blocks** | The first customer-editable relevance profile |
| **Raised** | `3931b3c` as F-B6 |

[B-001](BUGS.md) said the defect *"becomes reachable the moment a customer can edit their relevance profile, which is Lane B's territory but Lane A's module"* — a sentence containing an unresolved ownership question. The defect is fixed; the question is not.

**Lane B's position: it is not Lane B's.** *"Funding rounds matter more to us than hiring"* is **signal relevance** — what Signora should treat as interesting — and the Signal Engine owns relevance by ratified principle. It is not a declaration about the customer's own commercial position, which is all Commercial Profile holds. The two are one careless sentence apart: *"we're pushing Revenue Cloud"* is slice 4; *"product-launch signals matter to us"* is not this module's, however customer-authored it looks.

**Question.** Confirm the write path is Lane A's, in `signal_engine`, and schedule it there.

### Resolution — Lane A, 2026-08-02

**Confirmed. It is Lane A's, in `signal_engine`, and Lane B's reasoning is accepted without amendment.**

It is now settled by a ratified boundary rather than by agreement between two lanes: **Signal Engine owns intelligence** ([ADR-0036 §1](architecture/adr/0036-target-account-contract.md)), and **relevance is intelligence**. The distinguishing test is the one Lane B wrote, and it is worth keeping:

> *"We're pushing Revenue Cloud this quarter"* is a statement about the **customer's commercial position** — Commercial Profile, slice 4.
> *"Product-launch signals matter to us"* is a statement about **how Signora should interpret evidence** — Signal Engine.

Both are customer-authored, both are versioned, both are immutable, and **customer-authored is not the deciding property.** `signal_profile` has lived in `signal_engine` since M5A for exactly this reason, and moving it would put a module's interpretation rules outside the module that applies them.

**Two things Lane A is bringing rather than promising.**

**The defect that would have met the first customer is already fixed.** [`B-001`](BUGS.md) — `current()` returned version 1 forever, so the *first* revision anybody made would have been silently ignored — is closed in `c0bef97`, along with two more instances of the same pattern. Whoever ships the write path inherits a repository that reads currency correctly and an invariant that refuses the shape returning.

**What remains is small.** The domain, the aggregate, the versioning, the immutability, the audit columns and the catalog constraint all exist. What does not: a `RevisSignalProfile` use case, an endpoint, and a screen.

**What Lane A is not answering, because it is not an ownership question.** *Whether a customer should author relevance at all* is a product decision. There is a real argument that they should not — the catalog's defaults are reviewed by a domain expert, and a workspace that silences a signal type silences it invisibly for everybody in it. **Lane A will not schedule this until the product owner says it ships**, and the module being ours does not make the feature ours to decide.

---

## C-006 · Which lane owns `test_api_<module>.py`

| | |
|---|---|
| **Owner** | **Product owner** |
| **Requesting lane** | Lane B |
| **Category** | Architecture clarification — `CLAUDE.md` §20e |
| **Status** | `OPEN` |
| **Blocks** | Nothing. A standing ambiguity every feature lane hits |
| **Raised** | `30e66d0` as F-B5 |

§20e gives QE `backend/tests/**` *except a module's own suite*. `tests/integration/test_api_<module>.py` tests exactly one module's endpoints while living in QE's directory. Slices 1–4 followed slice 1's precedent and put them there.

**Proposed rule, for ratification:** *a file named `test_api_<module>.py` is that module's own suite regardless of directory; QE owns everything else in the tree, including every cross-module flow test.* That keeps two lanes' edits disjoint without moving files or splitting a suite mid-module.

---

## C-007 · The guided first run is a two-lane build

| | |
|---|---|
| **Owner** | Lane A (routing and shell) + **product owner** (sequencing) |
| **Requesting lane** | Lane B |
| **Category** | Product decision · cross-lane build |
| **Status** | `OPEN` |
| **Blocks** | Nothing until M12.5 slice 5 is done |
| **Raised** | `960b604`, assessed at the product owner's direction |

The five declarations are **not settings** — they are the condition of the pipeline running at all, and the pipeline cannot run until a target account exists. Five optional-looking pages with no stated order and no end state is a completion-rate problem before it is a UX one. Full reasoning in [40-commercial-profile.md](architecture/40-commercial-profile.md#the-shape-of-the-customers-first-hour).

**It needs no backend change**: a guided flow is a composition over existing reads and writes, and completeness is **derived** from the versions already returned, never stored.

**Questions.** Does Lane A take the first-run route, composing Lane B's components? Is it scheduled after slice 5, as Lane B recommends — guiding a customer through steps that do not exist would demonstrate an incomplete thing well? And separately: *Your business* currently sits under **Settings**, which is Lane A's navigation call and is arguably wrong.

### Resolution — Lane A, 2026-08-02

**Yes, Lane A takes the route.** `frontend/app/(app)/` is Lane A's by the Change Budget, and a first run is a **composition over another lane's components** rather than a reimplementation of them — Lane A will import Lane B's declaration components and own only the sequence, the progress and the end state. Lane B keeps every form it has built; if the flow needs a component Lane B does not have, that is a request through this register rather than a copy in Lane A's tree.

**Sequenced after slice 5, and Lane A agrees with Lane B's reason rather than merely accepting it.** Guiding somebody through four steps of five demonstrates an incomplete thing *well*, which is worse than demonstrating it plainly: the flow itself becomes the thing that looks finished. It also touches R6-05 — *nothing tells a new account what to do next* — which has been open since Review 6 and is the same gap seen from the other end.

**Completeness is derived, never stored**, and Lane A commits to that here because it is the part a first-run flow most often gets wrong. Each declaration already returns a version; **version 0 means nothing has been declared.** A `first_run_completed` flag would be a second representation of a fact the aggregates already carry, and it would disagree the first time somebody deleted their last product.

#### *Your business* under Settings — **it stays, and moving it would not fix what C-008 names**

Lane A's call, and the answer is no change. [D38](38-product-design-principles.md) settled that navigation is **journeys, not data**, and reduced six entries to two by that rule. *Your business* is **authoring** — done once, revisited when something changes, and never part of a seller's morning. Settings is exactly where a thing like that belongs, and promoting it would put a page nobody opens daily beside the one page they open every day.

**But C-008 is right, and it is a different fix.** *"Sellers cannot see what their company sells"* is not a symptom of the authoring page being in the wrong place — it is a symptom of **the declarations never reaching the surfaces where they would matter.** Which products an account is a fit for belongs on the **account brief**, beside the evidence; the buying committee belongs where contacts appear. Moving a settings entry into the sidebar would satisfy neither, and would leave the seller opening a configuration screen to answer a question they had while reading about an account.

**Recorded so the two do not get merged**: C-007 is *how a customer gets started*; C-008 is *where their declarations show up afterwards*. They share an input and nothing else.

---

## C-008 · Sellers cannot see what their company sells

| | |
|---|---|
| **Owner** | **Product owner** (the decision) + **Integrator** (the frozen foundation) |
| **Requesting lane** | Lane B |
| **Category** | Product decision · frontend foundation |
| **Status** | `OPEN` |
| **Blocks** | Nothing being built. It affects every AE and SDR, every day |
| **Raised** | `80d9511`, in the slice-4 product review |

**The API and the product disagree about who may read a commercial profile.** `policy.csv` deliberately grants **`member` read** on `product`, `icp`, `buying_committee` and `commercial_focus` — four separate decisions, each taken on the reasoning that *"every seller needs to see the catalog; changing it is the owner's"*. That read access is **unreachable**: the only screen showing any of it lives under `/settings/*`, which `GUARDED_ROUTES` restricts to `workspace:update` — owners.

**So an AE working an account cannot see the ideal customer that account is supposed to match, or the buying committee they are supposed to be selling into.** The declarations exist to make selling explainable, and the people selling cannot read them.

**Questions.**

1. **Should sellers see the commercial profile?** Lane B's position: yes, read-only, and the API already says so.
2. **If yes, where?** *Your business* is currently a settings page, and it is not a setting. A read-only surface for members might belong beside the account brief rather than under settings at all — which is Lane A's shell and routing.
3. **Or should the API be narrowed instead?** The opposite resolution is legitimate and should be considered rather than assumed away: revoke `member` read on all four and make the profile genuinely administrative. Lane B thinks this is the weaker answer but it is a real option, and leaving the contradiction unresolved is the only wrong outcome.

**Why Lane B has not simply fixed it.** `GUARDED_ROUTES` lives in `frontend/lib/state/permissions.ts` — frontend foundation, frozen under §20c — and the destination is Lane A's routing. Neither is Lane B's to change, and the underlying question is a product decision rather than a routing one.

---

---

## C-009 · An internal fault reaches a customer as a `422`

| | |
|---|---|
| **Owner** | **Product owner** — the change is in `signora_platform/`, which is frozen (§20a) |
| **Requesting lane** | Lane A, while assigned to `opportunity_engine` |
| **Category** | Error contract · platform change · **failure attribution** |
| **Status** | `OPEN` |
| **Blocks** | Nothing today. It blocks *doing this properly* in any module that wants to split its error hierarchy |
| **Raised** | `R4-02/R4-03` slice, 2026-08-02 |

**One exception class is serving refusals and invariant violations, and `ERROR_MAPPING` cannot tell them apart.**

`OpportunityError → 422 transition_refused` is correct for *"a won deal does not reopen"*. It is applied identically to *"an opportunity cannot record a negative score at creation"* — which no customer caused and which no customer can act on. The same shape exists in `ai_research_engine` (`ResearchRequestError`), and it will exist in every module that follows the pattern.

**This is the failure-attribution rule, in the API layer:**

> *An error must never name a component that was not involved… an incorrect attribution is worse than none, because it misdirects the investigation.*

A support engineer reading `transition_refused` on a bug report will look at the transition table. The transition table is fine.

### Why a lane cannot fix it alone

The correct split is a refusal base that maps to `422` and an invariant base that maps to nothing, so it surfaces as a `500`. **`signora_platform/api/errors.py` registers no catch-all `Exception` handler**, so an unmapped exception bypasses the standard envelope and returns a bare framework `500` — no `code`, no `correlation_id`, no `error` object. Every client, including Signora's own, parses that envelope.

So splitting the hierarchy today trades a wrong code for a **missing envelope**, which is worse: `correlation_id` is the only thread between a customer's report and the log line that explains it.

### The question

Add a catch-all handler to `signora_platform/api/errors.py` that returns the standard envelope with `code: "internal_error"`, a fixed message, and the `correlation_id` — **and no `str(exc)`**, so an internal fault stops being customer prose at all. That is a platform change under §20a and needs the product owner.

**Once it exists**, each module splits its own hierarchy inside its own budget, and the invariant added in this slice (`tests/security_invariants/test_customer_facing_messages.py`) narrows from *"no mapped message may name an identifier"* to *"no refusal may"* — a stronger rule, because an internal message would then be free to say everything an engineer needs.

### What was done meanwhile

**Identifiers were removed from all seven messages**, so nothing unreadable reaches a screen today. The attribution is still wrong and is stated in [27-opportunity-engine.md](architecture/27-opportunity-engine.md) rather than left implicit.

---

### Proposed architecture — **a proposal only, at the product owner's request**

**Nothing below is implemented and nothing should be until this item is `ANSWERED`.** It exists so the product owner and QE have something concrete to evaluate rather than a problem statement.

#### 1 · The hierarchy

Four categories, and the test that separates them is **who caused it and what they can do about it** — not where the code lives:

```
SignoraError                      (platform, abstract — never raised)
├── CustomerError                 the caller did something the domain refuses
│   ├── BusinessRuleViolation     a rule about their data said no
│   ├── ValidationError           the request itself was malformed
│   └── NotFoundError             the thing named is not visible to them
└── PlatformError                 nobody outside caused this
    ├── InvariantViolation        a stored fact contradicts itself
    └── InfrastructureError       a dependency failed — database, queue, provider
```

**`CustomerError` is the only branch whose message is customer copy.** That single sentence is the whole proposal; everything else follows from it.

**Modules keep their own exception types** and inherit from one of the five leaves. `OpportunityError` becomes a `BusinessRuleViolation`; the four construction-time refusals in `OpportunityState.__post_init__` and `ResearchRequestState.__post_init__` become `InvariantViolation`. **No module names an HTTP status**, exactly as today.

**Why `NotFoundError` is a customer error and not its own branch.** *"That account has no opportunity in this workspace"* is actionable — and 404-not-403 is already a deliberate security property (a non-member and a non-existent resource must be indistinguishable). Splitting it out would invite somebody to make the two differ.

#### 2 · What a customer sees

| Category | Status | Message | Envelope |
|---|---|---|---|
| `BusinessRuleViolation` | `422` | **The domain's own words** | Full |
| `ValidationError` | `422` | The domain's own words | Full, with `details` |
| `NotFoundError` | `404` | The domain's own words | Full |
| `InvariantViolation` | **`500`** | **Fixed string. Never `str(exc)`** | Full |
| `InfrastructureError` | **`503`** | **Fixed string. Never `str(exc)`** | Full |

**`PlatformError` messages must never be translated into customer-facing business errors.** That is the rule this item exists to establish. A customer told *"an opportunity cannot record a negative score at creation"* learns nothing, can do nothing, and is being told about a bug in a sentence that sounds like their fault.

**`503` rather than `500` for infrastructure** because it is the one platform failure a client can act on: retry. `500` says *do not retry*, and telling a client to give up on a transient database blip is a wrong answer with a cost.

**The full envelope in every case, including `500`.** That is the point of the change — today an unmapped exception bypasses `ErrorResponse` entirely and a customer reporting a fault has no `correlation_id` to quote.

#### 3 · Envelope, logging and correlation

**Envelope — unchanged in shape.** `{ error: { code, message, details?, correlation_id } }`, which is already ratified in [19-api-conventions.md](architecture/19-api-conventions.md). What changes is that **nothing escapes it**.

Two new stable codes: `internal_error` and `service_unavailable`. Module codes are untouched.

**Logging, and this is the half that makes the fixed message acceptable:**

| Category | Level | What is logged |
|---|---|---|
| `CustomerError` | `INFO` | Code, `workspace_id`, `correlation_id`. **Not an error** — the platform behaved correctly |
| `InvariantViolation` | `ERROR` | Full `str(exc)`, traceback, every identifier the message ever carried |
| `InfrastructureError` | `ERROR` | Full `str(exc)`, traceback, the dependency that failed |

**A `CustomerError` logged at `ERROR` is how an error dashboard becomes noise nobody reads.** A seller trying an illegal transition is the product working.

**Correlation id — the requirement that makes this worth doing.** Every response carries it, `500` included; every log line for that request carries the same one; it is generated once per request and already stored on `request.state`. **It is the only thread between *"it broke and said something about an internal error"* and the line that explains why**, and today that thread is cut exactly where it matters most.

Identifiers therefore move **out of messages and into log fields** rather than being deleted — `logger.error(..., extra={"opportunity_id": ...})`. This slice removed them from the messages; the proposal is what gives them a proper home.

#### 4 · What changes in `signora_platform/api/errors.py`

**Four changes, all additive. No existing behaviour is altered.**

1. **A catch-all `Exception` handler**, registered last, returning the envelope with `internal_error`, a fixed message and the correlation id. **This alone fixes the regression that blocks the split** and is independently worth having: any unhandled bug today escapes the contract.
2. **Two platform base classes** (`CustomerError`, `PlatformError`) exported for modules to inherit — or, if the product owner prefers zero new platform vocabulary, a second mapping `PLATFORM_ERROR_TYPES` and no base classes at all. **The first is stronger** because it makes the category a type rather than a registration somebody can forget.
3. **`_domain_handler` stops calling `str(exc)` unconditionally** — customer copy for `CustomerError`, the fixed string otherwise.
4. **Logging inside the handlers**, at the levels above. There is none today, so an error's only record is whatever the raising code happened to log.

**Estimated size: under a hundred lines, no migration, no API path change, no client change.** The risk is not size — it is that `signora_platform/` is frozen (§20a) and this is a change to how *every* module's errors surface, which is precisely why it is here rather than in a lane's commit.

#### 5 · What this unlocks, and what it costs

**Unlocks:** each module splits its own hierarchy inside its own budget · the invariant added in `e1a34a6` narrows from *"no mapped message may name an identifier"* to *"no **customer** message may"*, which is stronger, because a `PlatformError` would then be free to say everything an engineer needs · error dashboards separate *customers being refused* from *Signora being wrong*, which are currently one number.

**Costs:** every module reclassifies its exceptions once — mechanical, and the invariant will find any that are missed · two new response codes for clients to know about, both already implied by the status codes · QE gains a real assertion it cannot make today: **no `5xx` response may contain a domain sentence.**

---

---

## C-010 · No lane is assignable to `apps/` or `signora_platform/`, and a defect is sitting in one

| | |
|---|---|
| **Decision required** | How is code that belongs to no module assigned when it needs a fix? |
| **Participating modules** | none — `signora_platform/` (frozen, §20a) · `apps/` (composition root) · the frontend foundation (frozen, §20c) |
| **Current assignee(s)** | **Product owner** to answer · QE waiting |
| **Blocking** | [B-003](BUGS.md), which currently has no route to a fix |
| **Status** | `OPEN` |

**Current positions.** QE's position is that this is a structural gap rather than a missing decision: every other defect resolves to a module, and a module resolves to a current assignee, but this code is deliberately outside the module structure. Absent an answer QE will leave such rows unassigned indefinitely, which is honest and useless.

**Implementation impact.** Two shapes of answer, genuinely different in cost. **Assign the area to a lane on demand** — a temporary assignment like any other, with §20a's freeze rules still binding and an RFC still required for an interface change; the fix moves at slice speed. Or **route every such defect through the RFC process**, and accept that platform fixes move at RFC speed. B-003 is currently the only instance, so the cost of the second is one open row.

**Final decision.** —

**Recorded in.** —

---

---

## C-011 · A contraction risk reads like a small opportunity on the attention list

| | |
|---|---|
| **Decision required** | Whether and how posture is shown on an attention row |
| **Participating modules** | `buying_score_engine` (owns posture) · the product surface |
| **Current assignee(s)** | **Product owner** to answer · the product-surface assignee waiting |
| **Blocking** | R9-03 |
| **Status** | `OPEN` |

**Current positions.** *Attention is unsigned for every posture and opposing readings never net* holds inside the score, but does not reach the row: a contraction risk currently presents like a low-scoring opportunity, and the two mean opposite things to a CRO scanning a list. The implementing lane's recorded instruction is **do not implement without the ruling**.

**Implementation impact.** A product judgement, not an implementation detail — which is why it has waited rather than been solved locally. Carried from [`SESSION_HANDOFF.md`](SESSION_HANDOFF.md) §7, which had no register to put it in.

**Final decision.** —

**Recorded in.** —

---

---

## C-012 · `EventHandler` receives no session, so no module handler is registered

| | |
|---|---|
| **Decision required** | How a handler participates in the dispatcher's transaction — RFC required (§20a) |
| **Participating modules** | `signora_platform` (frozen) · every module that publishes |
| **Current assignee(s)** | **Product owner** — RFC |
| **Blocking** | The deployed worker consumes nothing; M5B's staleness sweep is unscheduled |
| **Status** | `WAITING` |

**Current positions.** A handler must work in the *same transaction* as the dispatcher's idempotency claim; the registry's signature is `(envelope) -> None`. The pipeline is exercised end to end through its real handlers in the integration suite and `make smoke`, **so every gate is green while the deployed worker consumes nothing** — the reason this has survived since M3A.

**Implementation impact.** Any module milestone that needs live event consumption. **Not to be worked around inside a product milestone**, which is how it would become permanent.

**Final decision.** —

**Recorded in.** —

---

---

## C-013 · `PublishableEvent` cannot be satisfied by a frozen dataclass

| | |
|---|---|
| **Decision required** | Protocol shape versus immutability — RFC required (§20a) |
| **Participating modules** | `signora_platform` (frozen) · eight publishing modules |
| **Current assignee(s)** | **Product owner** — RFC |
| **Blocking** | nothing; eight modules carry a `# type: ignore` at their publish site |
| **Status** | `WAITING` |

**Current positions.** Small, contained, identical in every module — which is exactly why it has survived eight milestones. Queued alongside [C-012](#c-004--eventhandler-receives-no-session-so-no-module-handler-is-registered) because both touch the same frozen surface and should be decided together.

**Implementation impact.** Cosmetic today. The cost is that a `# type: ignore` in eight places trains people to add a ninth.

**Final decision.** —

**Recorded in.** —

---

---

## C-014 · Accessibility and performance testing are QE's, and neither exists

| | |
|---|---|
| **Decision required** | Milestone numbers for two responsibilities QE already holds |
| **Participating modules** | none — repository-wide |
| **Current assignee(s)** | **Product owner** · QE waiting |
| **Blocking** | nothing today |
| **Status** | `OPEN` |

**Current positions.** §20c treats an accessibility issue as a **defect class** — a missing label, an unreachable control, a lost focus state — and nothing in the repository tests for one. Performance testing was deferred by [`20-provider-simulation.md`](architecture/20-provider-simulation.md) until there was a pipeline to benchmark; there now is one, and R-09 was measured by hand. **QE will not build either as an empty framework**, so both stay at zero until scheduled.

**Implementation impact.** The gap between how seriously the architecture takes accessibility and how much of it is enforced is currently the largest in the repository.

**Final decision.** —

**Recorded in.** —

---

---

## C-016 · Two branch names encode a permanent module assignment that no longer exists

| | |
|---|---|
| **Decision required** | Whether to rename `lane-a-product-surface` and `lane-b-commercial-profile`, and when |
| **Participating modules** | none — repository convention |
| **Current assignee(s)** | **Product owner** — **answered 2026-08-01** |
| **Blocking** | nothing |
| **Status** | `ANSWERED` — deferred, deliberately |

**Current positions.** Both branch names name a module. Under the assignment model ratified 2026-08-01 **a lane is a temporary execution resource and never permanently holds a module**, so within one rotation those names describe work the branch is not doing. QE's position was that `lane-a` / `lane-b` is the correct form, with the module in the Slice Handoff rather than in a ref.

**Implementation impact.** Cheap in isolation, and it is *the* naming a cold session reads first — but the branches exist on `origin` and in two live clones, so renaming mid-slice breaks both.

**Final decision.** **Product owner, 2026-08-01: do not rename now — the migration cost outweighs the benefit.** The current names may stand **until a natural repository restructuring occurs**, at which point this recommendation is taken up. The row stays `ANSWERED` rather than `CLOSED` because the recommendation outlives the decision: closing it would delete the reasoning that the next restructuring needs.

**Recorded in.** This row, deliberately. **A row kept open as a standing recommendation is the one case where the register does not shrink** — and it is recorded as such so it is not mistaken for a stalled item.

---

---

## Closed

## C-015 · Ports 3000 and 8000 now belong to human review

| | |
|---|---|
| **Decision required** | None — an action to be taken by the lane currently holding those ports |
| **Participating modules** | none — environment |
| **Current assignee(s)** | the lane running on 3000/8000 |
| **Blocking** | `make smoke`, intermittently and without saying so |
| **Status** | `OPEN` |

**Current positions.** The allocation convention now reserves **3000/8000 for human product review on `main`** ([`RUNNING.md` § Running a lane](RUNNING.md#running-a-lane)). A lane is still holding them.

**Implementation impact.** Until it moves, `make smoke` can fail with *"stack did not reach healthy"* because a lane's dev server holds a port, with nothing in the output saying so ([B-002](BUGS.md)). Move to the assigned block and update `frontend/.env.local` and the API command.

**Final decision.** —

**Recorded in.** —

---

**Closed 2026-08-02.** Implemented in [`RUNNING.md` § Running a lane](RUNNING.md#running-a-lane): human review holds 3000/8000, Lane A moved to 3300/8300, and every lane's block of 100 is recorded there. The item is kept rather than deleted because the allocation it settled is the kind a future lane will otherwise re-litigate.



---
