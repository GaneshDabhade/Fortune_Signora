# 410 — The Approved UI Specification is a product input

> **Recorded 2026-08-04 by Lane C — Product Office**, on the product owner's Product Transition Directive. **This document does not decide anything.** It records what became authoritative, what that changes, and what it does not.

## Status

**The Fortune Signora Design Project is the authoritative specification for frontend behaviour**, with the standing of a ratified ADR or an approved API contract.

| | |
|---|---|
| **Project** | `Signora design system specification` |
| **Identifier** | `1d043179-1ee9-4c9f-b59e-592e04297cad` |
| **Type** | `PROJECT_TYPE_PROJECT` — **not** `PROJECT_TYPE_DESIGN_SYSTEM` |
| ⚡ **Location** | **https://claude.ai/design/p/1d043179-1ee9-4c9f-b59e-592e04297cad** — **registered [D-128](../DECISION_REGISTER.md), 2026-08-06.** **One canonical location, many consumers — exactly how an ADR is registered.** ⛔ **The design is never duplicated into Product Office documentation** |

> ✅ **How a lane opens it, recorded 2026-08-06 ([D-137](../DECISION_REGISTER.md) §2, [C-421](../LANE_COORDINATION.md)).** **`DesignSync` · `projectId` `1d043179-1ee9-4c9f-b59e-592e04297cad` · `get_file` with the screen's document path** — e.g. `Fortune Signora Authentication.dc.html`. **`list_files` returns all twenty-six.** ⚠️ **`list_projects` does *not* show it**: that method returns design-*system* projects and this is typed `PROJECT`. ⛔ **An absence in that listing is not an absence of access, and reading it as one cost [TASK-467](../BACKLOG.md), [TASK-468](../BACKLOG.md) and [TASK-471](../BACKLOG.md) two days.**
| **Contents** | ⚠️ **26 screen specifications** · 1 design system (v2) · 1 pre-refactor design review |
| **Read** | 2026-08-04, in full, by Lane C |

> ⚠️ **The `Contents` row read *16 screen specifications* until 2026-08-06 and the set is twenty-six** — **sixteen business screens plus the ten platform-foundation modules [418 §1](418-platform-foundation-assessment.md) inventories.** **The ten arrived on the same day and were recorded in a different document, so the canonical register described part of the canonical set.** **Corrected here, because a register that undercounts its own contents is how *"that screen has no design"* becomes true by omission.**

---

## ⚖️ The authority rule — [D-128](../DECISION_REGISTER.md), 2026-08-06

> ## **The finalized design documents are the authority. Existing code is not.**

**Not historical UI. Not intermediate mockups. Not an implementation that happens to run.** **The design set at the location above is the source of truth for:** **page layout · visual hierarchy · interaction model · navigation · information architecture · spacing · typography · component usage · responsive behaviour · loading, empty and error states · customer journeys · accessibility expectations · workflow sequencing.**

### ⚡ Why this needed writing down, and it is measured rather than argued

**On 2026-08-06 this office reported six authentication screens as *shipped* and reasoned from their existence.** **Dating them against this document settled it:**

| Screen | First committed | |
|---|---|---|
| **Login** | **2026-07-28** | 🔴 **seven days before the design existed** |
| **Workspace Creation** | **2026-07-28** | 🔴 **before** |
| **Registration · Verification · Forgot · Reset** | **2026-08-01** | 🔴 **before** — built to [ADR-0033](adr/0033-authentication-methods.md), not to this |
| **Team Management** | **2026-08-04** | 🟠 **the same day — concurrent, not derived** |
| **Workspace Invitation** | **2026-08-05** | ✅ **after** |

> **Six of eight predate the specification they are now measured against.** ⛔ **Their existence establishes nothing about their correctness**, and reporting them as complete treated historical UI and approved UI as equivalent.

### The lifecycle every UI implementation is classified against

| | |
|---|---|
| **Legacy implementation** | **Built before the finalized design, or unverified against it.** ⛔ **The default for anything predating 2026-08-04** |
| **Design-compliant implementation** | **Verified against the approved design** |
| **Functionally complete** | Compliant, and the journey completes |
| **Production ready** | Complete, and its states, accessibility and error paths hold |
| **Enterprise ready** | Production ready, plus the enterprise surface the design specifies |

⛔ **A screen that predates the design must never be reported as production-ready merely because code exists.**

### The sequence every UI audit and decomposition follows

**① Approved design** *(canonical)* → **② current repository implementation** → **③ gap analysis** → **④ refinement or replacement work** → **⑤ executable slices.**

⚡ **④ preserves what the design does not govern**: **backend, Better Auth integration and published APIs are reused, never rebuilt.** **Only the UI and interaction model are replaced.**

⚠️ **And ① is a real precondition, not a formality.** **On 2026-08-06 this office was asked to audit conformance across fifteen dimensions and could not**: **the design set is not in the repository, and no `.dc.html` or export exists here.** **Stating that beat inventing an assessment** — **and it is why the location above is now registered rather than assumed.**

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
| 2 | **Design System v2** | ⛔ **This cell read *"18 canonical components"* until 2026-08-06 and the number was this office's, not the design's.** **The design does not contain the word *eighteen*.** ⚡ **It enumerates itself** — nineteen sections, each carrying a `data-screen-label`: **01 Critique of v1 · 02 Quiet Premium · 03 Color · 04 Typography · 05 Space and radius · 06 Elevation · 07 Navigation · 08 Headers · 09 Cards · 10 Controls · 11 Tables · 12 Overlays · 13 States · 14 AI system · 15 Agent workflows · 16 Motion · 17 Accessibility · 18 Tokens · 19 Migration.** ⛔ **Most are foundations, not components, so the old cell was wrong on kind as well as count.** **Read [`design-snapshot/screens/Fortune Signora Design System v2.dc.html`](../design-snapshot/screens/) — the section list above is *not* a specification to work from, it is a pointer to where the specification is** ([D-137](../DECISION_REGISTER.md)) |
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
