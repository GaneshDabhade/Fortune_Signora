# 447 · Signal Center — screen-by-screen traceability audit

**Lane C · Product Office · 2026-08-05.** **Third audit under [D-078](../DECISION_REGISTER.md)**, extended by [D-079](../DECISION_REGISTER.md) and [D-080](../DECISION_REGISTER.md).

**Screen 8 of 16** — *"A triage queue — every signal ends in a decision"* ([410](410-approved-ui-specification.md)). **[417 §2b](417-executable-slice-audit.md) calls its triage state *absent, required, unblocked*.**
**Measured against `origin/integration` @ `6b7b04e`. Nothing implemented, no lane named.**

---

# 0 · The headline corrects a finding I published an hour ago

> ## **[446](446-companies-traceability-audit.md) said a deadline-driven lifecycle *"is a genuinely new shape"* for this repository. It is not. `signal_engine` solved it, and its answer is to refuse to model it as a state change at all.**

**`Snoozed.until: datetime` exists today, and its docstring is the whole architecture:**

> *"**The evidence is intact because nothing about the signal is touched.** **Returning is a read that stops filtering this resolution out, not a regeneration**, so the account a customer sees in a fortnight is the one they postponed rather than a fresh reading that happens to resemble it."*

| | |
|---|---|
| **What 446 assumed** | *"Reversible for 24 hours"* needs a transition that fires when time passes — **an actor-less state change with no event to carry it** |
| **What the repository already does** | **A deadline is a *read-time predicate*, never a transition.** A snoozed signal returns because `now() >= until` **stops excluding it**, and nothing runs |
| **What that means for [R-03](../DOMAIN_DISCOVERY_REGISTER.md)** | **A batch is withdrawable while `now() < applied_at + window`.** ✅ **No scheduler. No timer. No expiry job.** **One predicate, and the same one twice** |

**And the measurement supports it repository-wide: `cron`, `scheduled_for`, `wake_at` and `due_at` return *zero* across `modules/`, `signora_platform/` and `apps/`.** **There is no scheduled execution anywhere, and nothing has needed one** — which is not an accident but the same discipline that keeps `evidence_state` computed rather than stored.

> **Two audits, and the second corrected the first.** **That is [D-079 §8](../DECISION_REGISTER.md)'s cross-screen validation doing exactly what it is for**, and it saved [R-03](../DOMAIN_DISCOVERY_REGISTER.md) from acquiring a scheduler it does not need.

---

# 1 · The traceability matrix

✅ exists · 🟡 extend · 🟠 conflicts · 🔴 missing · ⬜ not yet extractable

| UI element | Business meaning | Source of truth | Audit | Owner | Consumers | Priority |
|---|---|---|---|---|---|---|
| **The queue** | Hypotheses awaiting a human decision | **Aggregate** — `Signal` + the catalog | ✅ **Built and scored** | `signal_engine` | Signal Center · Account 360 | — |
| **Actioned · Assigned · Snoozed · Dismissed** | The four ways a signal ends | **Value objects** — `Actioned` · `Assigned` · `Snoozed` · `Dismissed` · `Resolution` | ✅ **All four exist.** ⚠️ **[417](417-executable-slice-audit.md) said *"none of it exists"* — that is stale; the domain was built since** | `signal_engine` | Signal Center | — |
| **"Snoozed signals return at the stated time"** | Postponement without loss of evidence | **Value object** — `Snoozed.until` + a **read-time predicate** | ✅ **Solved, and it is the pattern [R-03](../DOMAIN_DISCOVERY_REGISTER.md) should copy** — §0 | `signal_engine` | Signal Center · **[R-03](../DOMAIN_DISCOVERY_REGISTER.md)'s 6 screens** | — |
| **A dismissal reason** | Feedback about *Signora's* judgement, not a sales outcome | **Value object** — `DismissalReason` | ✅ **Exists.** ⛔ **And must never become a second vocabulary** — `opportunity_engine` owns `DISMISSED`, *"deliberately distinct from `CLOSED_LOST`"*, and §4 forbids a second definition | `signal_engine` | Signal Center | — |
| **"Every resolution is auditable · nothing is deleted"** | The decision record outlives the decision | **Projection** — an audit surface | 🟡 **Immutability ✅ — no `UPDATE` grant, supersession is the pattern. A readable audit 🔴** | ⚠️ Undecided | Signal Center · Settings · Copilot | **[R-07](../DOMAIN_DISCOVERY_REGISTER.md)** |
| **A triaged signal, downstream** | The pipeline learns a human decided | **Business event** — `signal.resolved` | 🔴 **Missing.** `signal_engine` publishes `signal.generated` and `signal.superseded` and **nothing for the decision** | `signal_engine` | **timeline · [TASK-406](../BACKLOG.md) ICP measurement · reports · `opportunity_engine`** | ⚡ **[TASK-432](../BACKLOG.md)** |
| **"Dismissal reasons feed rule precision"** | The catalog learns which rules misfire | **Projection** — precision per signal type | 🔴 **Missing, and it is downstream of the event above.** Without `signal.resolved` **there is nothing to aggregate** | `signal_engine` | Signal Center · ICP Builder | **After [TASK-432](../BACKLOG.md)** |
| **Assigning a signal to somebody** | A colleague owns this decision | **Value object** — `Assigned` | 🟡 **The value object exists; the *target* is a `Member`.** ⚠️ **Not a `Person`** — a colleague, not somebody at a target account. **[441](441-people-roadmap.md)'s boundary holds and is worth stating** | `signal_engine` · `workspace_tenancy` | Signal Center | — |
| **Resolving a signal** | A write on a signal | **Authorization** — `Resource.SIGNAL` | 🔴 **Missing.** [C-224](../LANE_COORDINATION.md) is `RULED` and the member **is not yet added** — the enum still holds thirteen | `signora_platform` | **Every future write surface** | **[TASK-405](../BACKLOG.md)** |
| **Triage counts and grouping** | *How many, of what kind, awaiting me* | **Computed view** | ✅ **Already exists frontend-side and correctly**: `lib/state/triage.ts` — *"every question below is a **filter over a fact the server already computed**… **this partitions; it never re-ranks**"* | Product Surface | Signal Center | — |

**Ten elements: 6 ✅ · 2 🟡 · 2 🔴.** **Both 🔴 are already carried by rows that exist.**

---

# 2 · Workflow — *a human decides about a signal*

| | | |
|---|---|---|
| **Inputs** | A signal, an outcome, a reason, sometimes an assignee or a time | ✅ |
| **Outputs** | An immutable `Resolution` | ✅ |
| **Business events** | ⛔ **`signal.resolved` does not exist** | 🔴 **[TASK-432](../BACKLOG.md)** |
| **State transitions** | ⛔ **None, and that is the design.** A resolution is recorded, never mutated | ✅ |
| **Scheduled transitions** | ⛔ **None, deliberately.** **A snooze is a read-time predicate** — §0 | ✅ **The finding of this audit** |
| **Domain rules** | *Nothing is deleted*; a dismissal is feedback about Signora, not about a deal | ✅ |
| **Validation** | A dismissal requires a reason | ✅ |
| **Permissions** | 🔴 **No `Resource.SIGNAL`.** **Triage is a *write* on a page every member reads** | 🔴 **[R-13](../DOMAIN_DISCOVERY_REGISTER.md)** |
| **Side effects** | The signal stops appearing; the score is untouched | ✅ **Correct — resolution is not re-scoring** |
| **Notifications** | *"three signals need you"* | ⏸ [ADR-0040](adr/0040-notifications.md) deferred |
| **AI interactions** | ⛔ None | ✅ |
| **Background jobs** | ⛔ **None needed** — §0 | ✅ |
| **Audit** | *"every resolution is auditable"* | 🟡 **[R-07](../DOMAIN_DISCOVERY_REGISTER.md)** |

> ## The workflow finding: this screen closes the only open loop in the pipeline
>
> **Nine stages record what a provider said. This screen is the one place a *human* answers back, and the answer goes nowhere.**
>
> **`signal.resolved` is not a feature of Signal Center. It is the return path of the whole intelligence pipeline** — **and three consumers are already waiting for it**: [TASK-406](../BACKLOG.md) measures ICP criteria against outcomes and *dismissed with a reason* **is** an outcome; `timeline` projects nine kinds of event and none of them is a decision; and *"dismissal reasons feed rule precision"* is a projection with no input.
>
> **Every day it does not exist, evidence is produced and discarded.**

---

# 3 · ⚖️ Challenging the implementation, not the screen ([D-080](../DECISION_REGISTER.md) §3)

**The approved screen says *"snoozed signals return at the stated time."*** **Read as a specification, that is a scheduler: something wakes at `until` and puts the signal back.**

> **The screen expresses the experience correctly and prescribes nothing.** **The correct implementation is the one `signal_engine` already wrote down** — *"returning is a read that stops filtering this resolution out"* — **and it needs no scheduler, no timer, no job and no new infrastructure.**

**This is the same shape as [446 §3](446-companies-traceability-audit.md)'s import finding, and stating it the right way round matters**: **the UI describes intent; the obvious implementation would have been a scheduler, and the repository already has a better answer.**

---

# 4 · Findings, in the ten categories

| | |
|---|---|
| **Existing and correctly modelled** | `Signal` and the catalog · all four resolution outcomes · **`Snoozed.until` as a read-time predicate** · `DismissalReason` · immutability with no `UPDATE` grant · `triage.ts` as a partition that never re-ranks |
| **Extension candidates** | **An audit surface** ([R-07](../DOMAIN_DISCOVERY_REGISTER.md)) · **`Resource.SIGNAL`**, ruled and unbuilt |
| **Architectural evolution** | ⛔ **None. This screen needs no boundary to move** |
| **Missing foundational capabilities** | ⛔ **None new** — and that is a result. **[R-03](../DOMAIN_DISCOVERY_REGISTER.md)'s deadline problem is *solved here*** |
| **Missing workflows** | ⛔ **None.** The triage workflow is complete except its event |
| **Missing entities** | ⛔ **None** |
| **Missing business events** | ⚡ **`signal.resolved` — the return path of the pipeline, with three consumers waiting** |
| **Missing permissions** | **`Resource.SIGNAL`** — ruled at [C-224](../LANE_COORDINATION.md), still thirteen members in the enum |
| **Missing projections** | **Rule precision from dismissal reasons** — downstream of the event |
| **Missing platform capabilities** | ⛔ **None.** ✅ **And one was *avoided*: no scheduler** |

---

# 5 · Cross-screen validation ([D-080](../DECISION_REGISTER.md) §2)

| Capability | Screens | Status |
|---|---|---|
| **[R-03](../DOMAIN_DISCOVERY_REGISTER.md) reversible action** | Copilot · Companies · **Signal Center supplies the *mechanism*** | ⚡ **Elevated: the deadline half is answered.** [TASK-431](../BACKLOG.md) needs no scheduler |
| **[R-07](../DOMAIN_DISCOVERY_REGISTER.md) audit surface** | Settings · Signal Center · Copilot | **3 screens — promoted from an Epic I capability to a product requirement** |
| **[R-13](../DOMAIN_DISCOVERY_REGISTER.md) authorization dimensions** | Copilot *(spend)* · Companies *(field, quantity)* · **Signal Center — a plain missing `Resource`** | 🟡 **Refined: three screens need *new dimensions*, one needs the existing model applied.** **Not every authorization gap is architectural, and saying so keeps R-13 honest** |

---

# 6 · What this produces

**No new backlog row, and no new register entry.** **Three audits, three screens, zero rows** — every gap was already carried by [TASK-432](../BACKLOG.md), [TASK-405](../BACKLOG.md) or an existing R-number.

**What it adds:** ⚡ **[R-03](../DOMAIN_DISCOVERY_REGISTER.md) loses its scheduler** · **[R-07](../DOMAIN_DISCOVERY_REGISTER.md) is at three screens** · **[R-13](../DOMAIN_DISCOVERY_REGISTER.md) is narrowed to the three dimensions that are genuinely new** · **[446](446-companies-traceability-audit.md)'s "genuinely new shape" is corrected** · **[417 §2b](417-executable-slice-audit.md)'s *"none of it exists"* is dated — the triage domain was built since.**

---

# 7 · What this document did not do

**Nothing implemented · no lane named · no wave reordered · no module created · no ADR drafted · no queue file touched · no backlog row added.**

**And it invented no UI element.** **The one thing it changed was a conclusion this office had published**, on evidence that was in the repository the whole time.
