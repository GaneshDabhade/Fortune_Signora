# 47 — Opportunities & Signals: a deferred implementation package

> **A record, not an instruction.** Written 2026-08-03 by Lane B, which was assigned the capability, ran the reuse audit, and found the capability already built and half of it owned by another lane ([C-306](../LANE_COORDINATION.md)).
>
> **Its purpose is that nobody repeats this analysis.** Whoever resumes should begin from *"here is everything that already exists"* rather than *"let's build Opportunities"* — which is the distinction the product owner named when asking for it.

---

## 1 · The finding that changes the brief

**The Opportunities & Signals experience is already built, and every part of it is reachable.**

That was not the expectation. The three assignments before this one each found a capability that existed and could not be opened — Timeline had no mount point, the Connection Center had no route, Timeline's projection had no subscription. **This one has no such gap**, and the check was explicit rather than assumed: every backend endpoint in the three engines has a frontend caller, and every hook is consumed by a rendered screen.

| Customer question | Answered today by |
|---|---|
| *"What should I work on?"* | **`/`** — `AttentionScore`, `ScoreMovement`, `Hypothesis`, `ContestedMark`, `EvidenceHealth`, `Ownership`, `DecidedAccounts` |
| *"Why this account?"* | **`/accounts/{id}`** — `WorkflowStage`, `OpportunityMomentum`, `ContributionList` |
| *"Prove it."* | `EvidenceDrawer`, opened from a citation |
| *"What did we observe?"* | `ValidationBlock` — signals as the evidence layer beneath a score |
| *"What happened?"* | `AccountHistory` — the timeline, mounted by Lane A in `CX-03` |
| *"Go find out more."* | `ResearchPanel` |
| *"I'm working this."* | `WorkflowActions`, `DecisionHistory`, `AccountSequence` |

> **Rebuilding this would discard fourteen findings from real product review and replace a reviewed surface with an unreviewed one.** The reuse policy in its strongest form: **the experience evolves; the findings are the backlog.**

**Closed as a direct result:** [C-024](../LANE_COORDINATION.md), which the register still described as *"the highest-value item on this page — no customer can open it."* It was reachable.

---

## 2 · What exists, and must not be rebuilt

**The reusable inventory, so a future slice starts from it.**

| Layer | Asset |
|---|---|
| **Endpoints** | `GET /accounts` · `/accounts/decided` · `/accounts/{id}/opportunity` · `/accounts/{id}/score` · `/accounts/{id}/validation` · `/accounts/{id}/timeline` · `/signal-catalog` · `POST /opportunities/{id}/states` |
| **Read models** | `OpportunityQueries` (six-deep composition) · `BuyingScoreQueries` · `SignalQueries` · `TimelineQueries` |
| **Domain** | `Opportunity` + `opportunity_state` (append-only) · `BuyingScore` + **Contribution Ledger** · `Signal`, `SignalCatalog`, `SignalProfile` |
| **Components** | `attention.tsx` · `opportunity.tsx` · `contributions.tsx` · `evidence.tsx` · `validation.tsx` · `narration.tsx` · `research.tsx` · `workflow.tsx` · `decided.tsx` · `decision-history.tsx` · `sequence.tsx` · `entity-name.tsx` · `dates.ts` · `timeline/feed.tsx` |
| **Hooks** | `useAccounts` · `useAccountIdentities` · `useDecidedAccounts` · `useAccountScore` · `useAccountValidation` · `useAccountNarration` · `useAccountResearch` · `useAccountTimeline` · `useSignalCatalog` |
| **Patterns worth copying** | Two-request name resolution that never blocks triage · per-section failure reporting (B-006) · the evidence drawer as a transition · `limit + 1` `has_more` |

---

## 3 · The findings, classified — because not every one needs implementation

**Thirty-four open findings were re-read and asked the product owner's question: *is this actually a backend problem?*** Several are not what their title suggests.

### Not implementation at all — six

| | Finding | What it actually is |
|---|---|---|
| **R4-05** | Every account offers the same three moves | **Already recorded as correct.** Kept so it is not "fixed" |
| **R8-05** | Two roles, reviewers asked for five | **A product decision**, not a defect. Roles are Casbin's and adding three is a permissions model |
| **R8-06** · **R6-06** | Verification link in the terminal · no way in without a signing key | **Local-environment affordances**, not product defects. They disappear in a deployed environment (M14.5) and would be *wrong* to fix locally |
| **R11-02** · **R12-06** | Six capabilities entered through a Demo Scenario | **A roadmap-hygiene finding.** The fix is a scope entry, and the roadmap is the product owner's |

### Solved by another finding — four

**Fixing these individually would be work that disappears.**

| | Dissolves when |
|---|---|
| **R1-02** — trigger and evidence state contradict | **R1-01 lands.** A signal title and an evidence state do not appear to contradict; a *recomputation trigger* and an evidence state do. Recorded in R1-02's own text |
| **R5-03** · **R1-05** — rows tie, and two are visibly identical | **R1-01 lands.** The ties are visible *because* the discriminating column says the same thing on eleven rows |
| **R9-02** — the score is on the row twice | **R9-04 lands** — the row becoming one line of a story removes the duplicate rather than deleting it |

### Genuinely backend — seven, and Lane B holds the modules

| | Finding | The actual change |
|---|---|---|
| **R1-01** 🔴 | *"Why now"* says the same thing eleven times | The read model carries `ScoreTrigger` — *why the score was recomputed*, a pipeline event. It should carry **the strongest contributing signal**, which the Contribution Ledger already holds |
| **R1-04** 🟠 | The brief never says an account is cooling | `ScoreTrend` exists and the brief does not surface it. **A read-model field, then a render** |
| **R5-02** · **R9-03** 🟠 | A contraction risk reads like a small opportunity | **Signal *direction* is in the domain and absent from the read model.** Not a ranking change — a missing field |
| **R2-01** 🟠 | Two accounts get identical guidance | Guidance is derived from signal type alone. Making it discriminate needs the ledger's specifics |
| **R3-01** 🟠 | Corroboration is rare and most valuable | **Corroboration count is computable from the ledger** and is not exposed |
| **R10-04** 🟠 | The narration says *"3 facts"* and cannot show them | The narration's evidence refs exist; the read model drops them |
| **R11-06** 🟡 | Attributes are engineering's words | `knowledge_graph` — **already [TASK-003](../BACKLOG.md), and not this capability's** |

### Genuinely frontend — Lane A's, and blocked for Lane B

**R1-06 · R1-07 · R2-02 · R2-03 · R3-02 · R4-02 · R4-03 · R4-04 · R5-04 · R9-04 · R10-01 🔴 · R10-02 · R10-03 · R11-01 🔴** — navigation, hierarchy, copy, reachability. **All in Product Surface.**

### Neither, and the largest of them all

**R12-04** 🔴 — *"Organization" appears nowhere in the repository* — is the root cause of a vocabulary class, spans every lane, and is [ADR-0034](adr/0034-ubiquitous-language.md)'s territory rather than this capability's.

---

## 4 · The implementation package

**Ordered by what unblocks the most. Each entry is what a resuming lane needs and nothing it can derive.**

### P1 — `signal_engine` · `buying_score_engine` · **the row's most valuable line**

| | |
|---|---|
| **Customer problem** | *"Every row says the same thing, so I stopped reading that column by the fourth row."* (AE) |
| **Evidence** | R1-01, R1-02, R1-05, R5-03 — four findings, one cause |
| **Current implementation** | `AccountAttention.trigger` carries `ScoreTrigger`, an enum of pipeline events with two live values across twelve accounts |
| **Missing capability** | The **strongest contributing signal's title** on the attention row |
| **Reusable foundation** | **The Contribution Ledger already holds it** — one entry per contributing business event, ordered. Nothing new is computed; a field is exposed |
| **Backend work** | Extend the accounts read model with the top contribution's signal type and direction. **No migration** |
| **Frontend work** | Replace the trigger column. **Lane A** |
| **Dependencies** | [C-306](../LANE_COORDINATION.md) for the frontend half only |
| **Migration · QE · risk** | None · one changed response shape, one visual regression · **low — additive field, existing data** |
| **Effort · value** | Small backend, small frontend · **the highest on the page: it is the line a seller reads first** |

### P2 — `buying_score_engine` · **direction, so a contraction stops reading like an opportunity**

Evidence R5-02, R9-03. **Direction exists in the domain** (`observation.direction`, carried into business events) and is dropped by the read model. Backend: expose it. Frontend: Lane A. **No migration.** *Value: the most dangerous misread on the daily surface — a risk that looks like an opportunity.*

### P3 — `buying_score_engine` · **trend and corroboration on the brief**

Evidence R1-04, R3-01. Both derivable from the ledger, neither exposed. **No migration.**

### P4 — `ai_platform` boundary · **the narration's evidence refs**

Evidence R10-04. The narration claims *"3 facts"*; the refs exist on the artifact and the read model drops them. **Check first whether R11-04's citation rule already forbids what this asks for.**

### P5 — **Product Surface** · everything in §3's frontend list

**Blocked on ownership, not on design.** R10-01 (🔴, one exit and it is backwards) and R11-01 (🔴, five stages built and unreachable) are the two worth doing first.

---

## 5 · Future pressure

| | |
|---|---|
| **AI** | Every P-item exposes a *deterministic* field. The daily surface's explicit rule is that no model wrote anything on it; AI belongs on the brief beside its citations. **The pressure is the first request to put a generated sentence on a row** |
| **Sales workflow** | Five unreachable lifecycle stages (R11-01) are a workflow gap, not a UI one. **Reaching them may need stages the domain does not have** |
| **Enterprise** | Roles: two, and reviewers asked for five (R8-05). A permissions model, and Casbin's |
| **Analytics** | *"Which segment produced the best opportunities?"* needs opportunities to cite an ICP. **They do not** — and ICP-01's identity/version split is what will let them |
| **Performance** | The brief composes six read models deep. **Fine per account; the first list that composes them per row is the trigger** |
| **Data volume** | The attention list is unpaginated. A workspace watching thousands of accounts pages, and the platform cursor is datetime-keyed |
| **Observability** | Every P-item changes a response shape. **Nothing measures whether a seller reads the new column**, which is what would prove R1-01 fixed rather than changed |

---

## 6 · Resume conditions

**This package is complete and needs no rediscovery.** To resume:

1. **Answer [C-306](../LANE_COORDINATION.md)** — who owns Product Surface for this work. **P1–P4 need no answer; they are backend-only in modules Lane B has claimed.**
2. **Start at P1.** It resolves four findings, needs no migration, and changes the line a seller reads first.
3. **Do not rebuild.** §2 is the inventory; §1 is why.
4. **Re-verify before reporting.** [C-024](../LANE_COORDINATION.md) sat `OPEN` for a day after Lane A closed it by implementation, and the register was still calling it the highest-value item on the page. **Check the code, not the register.**
