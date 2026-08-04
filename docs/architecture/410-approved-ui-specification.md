# 410 — The Approved UI Specification is a product input

> **Recorded 2026-08-04 by Lane C — Product Office**, on the product owner's Product Transition Directive. **This document does not decide anything.** It records what became authoritative, what that changes, and what it does not.

## Status

**The Fortune Signora Design Project is the authoritative specification for frontend behaviour**, with the standing of a ratified ADR or an approved API contract.

| | |
|---|---|
| **Project** | `Signora design system specification` |
| **Identifier** | `1d043179-1ee9-4c9f-b59e-592e04297cad` |
| **Type** | `PROJECT_TYPE_PROJECT` — **not** `PROJECT_TYPE_DESIGN_SYSTEM` |
| **Contents** | 16 screen specifications · 1 design system (v2) · 1 pre-refactor design review |
| **Read** | 2026-08-04, in full, by Lane C |

**It is not analysed, redesigned, critiqued, simplified or improved.** It is read the way a ratified contract is read: to determine what the repository must provide.

## What changed, and what did not

**One thing changed: the source of truth for the frontend.**

Product Office previously prepared backend capability *and* UI assumptions. **The second half is retired.** The frontend no longer drives discovery; the approved design drives backend preparation.

**Nothing else changed.** The Constitution, `CLAUDE.md`, the Engineering Laws, the lane model, the Change Budget, the identifier blocks, the import contracts, the Security Invariants, QE's authority and the Product Office's own responsibilities are all fully in force. **Every governance rule that applied on 2026-08-03 applies on 2026-08-04.**

**In particular, the reuse rules are unchanged and now matter more, not less.** A screen that looks new is not evidence that the capability behind it is new. §3 records what the assessment found: **most of what the approved product needs is built.**

## The inventory

| # | Screen | Reads as |
|---|---|---|
| 1 | **App Shell** | The frame every module mounts inside — 22 numbered specifications |
| 2 | **Design System v2** | Tokens, type scale, radius scale, control heights, 18 canonical components |
| 3 | **Executive Dashboard** | CEO/CRO homepage — forecast, risk, ageing, movements |
| 4 | **Companies** | 8,412 accounts — table, cards, segments, bulk work, import/export |
| 5 | **Account 360** | The flagship record page — 27 sections, each in six states |
| 6 | **People Intelligence** | Buying committee, org chart, relationships, people timeline |
| 7 | **Opportunity Intelligence** | The revenue cockpit — probability, contributions, competitors |
| 8 | **Signal Center** | A triage queue — every signal ends in a decision |
| 9 | **ICP Builder** | Seven criterion groups scored against closed-won outcomes |
| 10 | **Workflow Automation** | Simulated before it runs, approved before it writes |
| 11 | **CRM Integrations** | Connect, map, sync, health, disconnect |
| 12 | **AI Copilot** | 17 surfaces, one contract |
| 13 | **AI Research** | A workspace — answers become documents that keep their sources |
| 14 | **Global Search** | One doorway, two exits, never a second search box |
| 15 | **Reports** | Built once, read three ways |
| 16 | **Settings** | Attributed, reversible, in the audit log |

## What the design project asserts that the repository must honour

**These are not stylistic. Each is a statement about behaviour that the backend either supports or does not.**

**The shell is a contract.** *"A module receives one region and four guarantees… In exchange it may not add chrome, invent a second search, place actions in the top bar, or open its own floating panels."* Global scope — period, region, segment, owner — is applied **before** a module renders, serialises to the URL, and can be saved as a named view.

**There is exactly one global search**, and a natural-language question routes to the assistant rather than returning rows.

**Every AI surface obeys one contract**: it inherits scope, cites what it read, states confidence with its basis, **proposes rather than commits**, and is attributable and reversible. Six verbs and no others — *Explain · Summarize · Predict · Recommend · Generate · Reason*.

**Nothing writes without approval.** Workflow Automation: *"Simulated before it runs, approved before it writes, reversible after it does."* Opportunity Intelligence: *"Nothing sends without your approval. Reversible for 24 hours."* Companies bulk edit: *"reversible for 24 hours as a single named batch."*

**This is the repository's own rule arriving from the design side.** `MACHINE_AUTHORED = frozenset({Stage.TRACKING})` and *"Intelligence suggests. Humans commit."* The approved UI and the ratified architecture agree without having been reconciled, which is the strongest evidence available that neither needs to move.

**Absence is stated, never hidden.** A facet with zero matches stays visible at 45% *"so the absence is information."* A collapsed section still states its worst status. AI Research **refuses** a question it cannot answer and records the refusal. A signal *"without evidence is never raised."*

**This is `live_capabilities` as an interaction principle.** The Connection Center already refuses to advertise what Signora cannot produce; the approved design applies the same discipline to every surface.

## What this document does not do

**It does not create work, assign work, sequence work, or approve any change.** The impact assessment is [411](411-ui-convergence-assessment.md).

**It does not supersede any architecture document.** The design project is authoritative for **frontend behaviour**. It says nothing about module boundaries, the dependency graph, the event catalog, the claim vocabulary or the intelligence pipeline, and it must not be read as if it did. Where a screen implies a backend capability, that capability is still governed by the ordinary rules — and a new bounded context is still 🔴 and still needs an ADR.

**It does not make the design project a design system.** The project is `PROJECT_TYPE_PROJECT`. That type is fixed at creation, so the project cannot be converted; `Design System v2` lives inside it as a screen. **Whether the token layer should live in a real design-system project is a question for whoever owns the frontend refactor, not a Product Office decision.**

## The one thing Lane C flags without deciding

**The design project's own review says the sixteen screens are not yet one product** — *"sixteen dialects of the same language"*, 36 type sizes against a specified 9, 44% of radii off-scale, and *"nobody consumes the App Shell."* It proposes four passes and asks which to run.

**That is a frontend question and it is not Product Office's.** It is recorded here for one reason: **the shell is the substrate every screen assumes**, and §2 of the App Shell specification states that global scope is applied before a module renders. **If the shell is not consumed, no module inherits scope** — and *that* is a backend-visible fact, because it decides whether filter state is a shell concern or sixteen separate module concerns. It appears in [411](411-ui-convergence-assessment.md) §4 as a capability question rather than a styling one.
