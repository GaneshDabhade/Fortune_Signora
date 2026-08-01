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

---

## What is waiting

| Id | What | Requester | Owner | Status | Blocks |
|---|---|---|---|---|---|
| [C-001](#c-001--the-target-account-contract) | The target-account contract — this module's first edge | Lane B | **Lane A** | `WAITING` | **M12.5 slice 5 — implementation is paused** |
| [C-002](#c-002--customer-language-has-no-anticorruption-layer) | Customer language has no anticorruption layer | Lane B | **Product owner** (ADR) | `OPEN` | Anything that matches an account against an ICP |
| [C-003](#c-003--three-wire-codes-for-one-condition) | Three wire codes for one condition | Lane B | **Product owner** | `OPEN` | Nothing — but it grows every slice |
| [C-004](#c-004--shared-documents-lag-commercial-profile) | Shared documents lag Commercial Profile | Lane B | **Integrator** | `OPEN` | Nothing today; a cold session reads a stale manifest |
| [C-005](#c-005--who-owns-the-signal-profile-write-path) | Who owns the signal-profile write path | Lane B | **Product owner** / Lane A | `OPEN` | The first customer-editable relevance profile |
| [C-006](#c-006--which-lane-owns-test_api_modulepy) | Which lane owns `test_api_<module>.py` | Lane B | **Product owner** | `OPEN` | Nothing — a standing ambiguity in §20e |
| [C-007](#c-007--the-guided-first-run-is-a-two-lane-build) | The guided first run is a two-lane build | Lane B | Lane A + **product owner** | `OPEN` | Sequencing after M12.5 slice 5 |

---

## C-001 · The target-account contract

| | |
|---|---|
| **Owner** | **Lane A** — Provider Platform |
| **Requesting lane** | Lane B — Commercial Profile |
| **Category** | Event contract · read-port ownership · **Customer–Supplier relationship** |
| **Status** | `WAITING` |
| **Blocks** | **M12.5 slice 5. Lane B has paused implementation and will not start until this is `ANSWERED`** |
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

### Resolution

*Not yet answered. Record the commit or ADR here, set `ANSWERED`, and Lane B will begin.*

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
- **The Canonical Vocabulary Principle** ([40](architecture/40-commercial-profile.md#the-canonical-vocabulary-principle)) is written in the module doc because Lane B may not edit `04`. Its cross-module form belongs beside the provider-configuration ruling it extends.
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

---

## Closed

*None yet.*
