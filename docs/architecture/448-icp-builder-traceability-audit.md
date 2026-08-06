# 448 · ICP Builder — screen-by-screen traceability audit

**Lane C · Product Office · 2026-08-05.** **Fourth audit under [D-078](../DECISION_REGISTER.md)**, extended by [D-079](../DECISION_REGISTER.md), [D-080](../DECISION_REGISTER.md) and [D-081](../DECISION_REGISTER.md).

**Screen 9 of 16** — *"Seven criterion groups scored against closed-won outcomes"* ([410](410-approved-ui-specification.md)).
**Named by the product owner as the screen that independently validates People and ICP Matching.** **Measured against `origin/integration` @ `6b7b04e`.**

---

# 0 · Two measurements, and they decide the audit

## ① **Seven criterion groups. Three parseable criteria.**

**`ProductIcp` carries `industries`, `countries`, `employees` — and `notes`, which the code excludes from computation in its own words:**

> *"Anything the criteria above cannot hold — *'only where they already run Salesforce'*. **Read by a human, and by whoever writes the ICP into a prompt later; never parsed.**"*

**So the declaration model expresses three of seven groups.** ✅ **One more is identified** — *Decision makers*, which [417 §1](417-executable-slice-audit.md) enumerates as *"VP Operations or above · exists · identified"* and *"Sustainability owner · exists · named"*, **four criteria, all person-existence.** ⬜ **The remaining three are not extractable from the repository.**

> **This is the first audit where the gap is *countable*, and the count is the finding: 3 of 7 modelled, 1 of 7 identified-and-blocked, 3 of 7 unknown.**

## ② **A customer publishes an ICP and nothing downstream learns.**

**`commercial_profile` declares five things — ICP, committee, competitors, focus, target accounts — and publishes exactly one event: `commercial_profile.target_accounts_changed`.** **`domain/events.py` declares one class.**

> **And the reason is correct rather than negligent**: `TargetAccountsChanged` exists **because `provider_platform` needed a sync trigger.** *"The event is the trigger and the port is the payload."* **An event was created when a consumer appeared** — which is the repository refusing to build speculative events, and it is right.
>
> ⚠️ **A consumer has now appeared.** **[TASK-406](../BACKLOG.md) measures criteria against outcomes, and [TASK-434](../BACKLOG.md)'s predicate is evaluated per account.** **When the ICP changes, every measurement derived from it is stale and nothing says so.**

---

# 1 · The traceability matrix

✅ exists · 🟡 extend · 🟠 conflicts · 🔴 missing · ⬜ not yet extractable

| UI element | Business meaning | Source of truth | Audit | Owner | Consumers | Priority |
|---|---|---|---|---|---|---|
| **The declaration surface** | Who buys each product, in the customer's words | **Aggregate** — `IcpDeclaration` · `ProductIcp` | ✅ **Built.** `GET`/`PUT /icp`, immutable, versioned, `supersedes`, no `UPDATE` grant | `commercial_profile` | ICP Builder · Companies · Account 360 | — |
| **Industry · country · size criteria** | Three of the seven groups | **Value objects** — `industries` · `countries` · `EmployeeRange` | ✅ **Exists.** **`EmployeeRange` is a count, not a band** — *"providers report employee counts as numbers… so a range of integers needs no shared vocabulary and cannot drift from one"* | `commercial_profile` | ICP Builder | — |
| **The *Decision makers* group** | Four person-existence criteria | **Entity** — `Person` | 🔴 **[R-01](../DOMAIN_DISCOVERY_REGISTER.md).** *"VP Operations or above · **exists · identified**"* — ⚠️ **and *identified* is the named half, which [441](441-people-roadmap.md) puts at [TASK-429](../BACKLOG.md), not [TASK-427](../BACKLOG.md)** | `people` *(new)* | ICP Builder · Copilot · Account 360 · Exec Dashboard | **§3** |
| **The other three groups** | ⬜ Unknown | ⬜ | ⬜ **Not extractable.** 410 says *seven*; the repository evidences four | ⬜ | ICP Builder | **Extraction** |
| **Free-text notes** | *"Only where they already run Salesforce"* | **Value object** — `notes` | 🟠 **Exists and is deliberately inert** — *"never parsed."* ⚠️ **A criterion a customer typed and nothing scores is a criterion the backtest silently omits** | `commercial_profile` | ICP Builder | **§4** |
| **Criterion-level lift vs closed-won** | Does this criterion predict anything? | **Computed view** | 🔨 **[TASK-406](../BACKLOG.md) — `IN PROGRESS`** | `opportunity_engine` measures ([C-328](../LANE_COORDINATION.md)) | ICP Builder · Exec Dashboard | — |
| **In-ICP vs outside cohorts** | The backtest's two halves | **Domain service** — the criterion predicate | ✅ ⚡ **[TASK-434](../BACKLOG.md) `PROMOTED`.** **The screen that most needed it got it first** | `commercial_profile` | **16 consumers** | — |
| **Validation warnings** | *"This describes everybody"* | **Domain rule** — `describes_nobody_in_particular` | ✅ **Already exists**, and correctly framed: *"**A question, not a refusal**… refusing a broad segment would be this module judging the customer's business"* | `commercial_profile` | ICP Builder | — |
| **Fitted weights and drift** | A model that learns the ICP | **AI capability** | 🔴 **Missing, and [TASK-406](../BACKLOG.md) non-goals it explicitly** — *"they are a model, not a measurement, and are a later slice"* | ⚠️ Undecided | ICP Builder | **Deferred by the row itself** |
| **TAM funnel** | How big the addressable market is | **External provider** | 🔴 **Missing. Needs a market database that does not exist** — [TASK-406](../BACKLOG.md) says so | ⛔ **External** | ICP Builder | **Evidence-gated** |
| **Publishing an ICP** | A commercial decision, dated and attributed | **Business event** — `icp.declared` | 🔴 **Missing — and a consumer has now appeared.** §0② | `commercial_profile` | **[TASK-406](../BACKLOG.md) · [TASK-434](../BACKLOG.md)'s consumers** | **§5** |
| **Segments** | ⬜ | ⬜ | ⬜ **Unchanged from [446 §0](446-companies-traceability-audit.md)** | ⬜ | ICP Builder · Companies · Global Search | **[TASK-433](../BACKLOG.md)** |

**Twelve elements: 4 ✅ · 1 🔨 · 1 🟠 · 3 🔴 · 3 ⬜.**

---

# 2 · Workflow — *a customer declares who buys their product*

| | | |
|---|---|---|
| **Inputs** | Criteria, per product | 🟠 **Three of seven groups expressible** |
| **Outputs** | An immutable, versioned `IcpDeclaration` | ✅ |
| **Business events** | ⛔ **None.** §0② | 🔴 |
| **State transitions** | `SegmentState` with `_ALLOWED` and `next_state` | ✅ **One of the repository's three state machines** |
| **Domain rules** | *A description with no criteria describes every company* | ✅ **`describes_nobody_in_particular`** |
| **Validation** | `MAX_CRITERIA`, `MAX_CRITERION`, `MAX_NOTES`, case-folded duplicates | ✅ |
| **Permissions** | `Resource.ICP`, and `update` is **owner-only** while `read` is both | ✅ **Correct — *"who a product is for" is an administrative act*** |
| **Side effects** | ⛔ **None today** — and §0② is exactly this row | 🔴 |
| **Notifications** | *"your ICP changed; 400 accounts left the cohort"* | ⏸ [ADR-0040](adr/0040-notifications.md) |
| **AI interactions** | The ICP is written into a prompt — *`notes` is read "by whoever writes the ICP into a prompt later"* | 🟡 **A stated consumer with no port** |
| **Background jobs** | **Re-evaluating 8,412 accounts when the ICP changes** | 🔴 **The event's real consequence** — §5 |
| **Audit** | *Who declared this, when, superseding what* | ✅ **`created_by`, `version`, `supersedes`, and no `UPDATE` grant** |

---

# 3 · ⚡ Independent validation of People — and it moves a boundary

**The product owner named this audit as the one that validates [R-01](../DOMAIN_DISCOVERY_REGISTER.md) independently. It does, and it sharpens it.**

| | |
|---|---|
| ✅ **Confirms the domain** | *"VP Operations or above · **exists**"* is **role-level and anonymous** — buildable from `Affiliation` intervals with no person name. **[TASK-427](../BACKLOG.md) serves it** |
| ⚠️ **And splits the group** | *"Sustainability owner · exists · **named**"* and *"· **identified**"* are **not** role-level. **They need [TASK-429](../BACKLOG.md) — provider enrichment** |

> **So [440](440-people-roadmap-integration.md) and [441](441-people-roadmap.md) were right that ICP Builder depends on People, and imprecise about *which* People.** **The group splits across the M-D / M-E boundary that [D-074](../DECISION_REGISTER.md) drew** — **two of the four criteria are buildable at wave 1.5 and two wait on a provider contract.**
>
> ✅ **This is the four-milestone separation earning itself on a screen it was not designed for.** **A screen-level audit found the seam a roadmap-level one had blurred.**

---

# 4 · ⚖️ Challenging the implementation — the inert criterion

**`notes` is *"never parsed"*, and that is a correct decision about a free-text field.** **The implementation risk is what happens next.**

> **A customer types *"only where they already run Salesforce"* into the ICP. The backtest reports lift for industry, country and size — and silently omits the criterion the customer cares most about.** **The number is right and the impression is wrong.**

**The obvious implementation is to parse the note. That would be a second, unreviewed criterion vocabulary** — and `TECHNOLOGY_DETECTED` already exists as a canonical claim, so *"they run Salesforce"* is **an eighth criterion group the pipeline could evaluate today**, not a parsing problem.

> **Challenge, as a recommendation:** **the backtest must state which criteria it scored and which it could not**, on the same discipline [TASK-406](../BACKLOG.md) already carries — *"a criterion no outcome data supports says so rather than reporting `1.0×`"*. ⚠️ **And `unmeasured` is already in [TASK-434](../BACKLOG.md)'s type.** **The mechanism exists; this row is the reminder to use it here.**

---

# 5 · Event discovery ([D-081](../DECISION_REGISTER.md) §4) — the second eventless human decision

**The four questions, on this screen's completion point:**

| | |
|---|---|
| **Should publishing an ICP emit an event?** | ✅ **Yes — now.** A consumer exists: every measurement derived from an ICP is stale the moment it changes |
| **Which consumers need it?** | **[TASK-406](../BACKLOG.md)'s lift · the backtest's cohorts · any cached evaluation of [TASK-434](../BACKLOG.md)'s predicate · re-scoring 8,412 accounts** |
| **Does an equivalent exist?** | **No — and one sibling does.** `commercial_profile.target_accounts_changed` is the exact shape, created when *its* consumer appeared |
| **Can existing infrastructure be reused?** | ✅ **Entirely.** Outbox, relay, dispatch, idempotency and ARQ are built, and **registering an event type is *"a use of the platform, not a change to it"*** (§20a) |

> ## The pattern across two screens
>
> **Signal Center: a human resolves a signal → no event.** **ICP Builder: a human publishes an ICP → no event.**
>
> **Not a systemic failure** — `opportunity.stage_changed` and `commercial_profile.target_accounts_changed` both exist, **because a consumer appeared.** **The pattern is narrower and more useful than *"human decisions are eventless"*: this repository creates an event when something needs one, and two consumers have now appeared without their events being noticed.**
>
> **Recorded as [R-14](../DOMAIN_DISCOVERY_REGISTER.md), and it is a *checkable* rule rather than a complaint**: when a screen's completion point is a human decision, ask who downstream is now waiting.

---

# 6 · Findings, in the ten categories

| | |
|---|---|
| **Existing and correctly modelled** | `IcpDeclaration` and its versioning · `EmployeeRange` as a count not a band · `describes_nobody_in_particular` as a question not a refusal · `SegmentState`'s state machine · owner-only `icp:update` · **[TASK-434](../BACKLOG.md)'s predicate, promoted** |
| **Extension candidates** | **An `icp.declared` event** · **`TECHNOLOGY_DETECTED` as a real criterion group** rather than a note |
| **Architectural evolution** | 🟠 **`notes` is inert and the backtest does not say so** — §4 |
| **Missing foundational capabilities** | ⚠️ **CORRECTED 2026-08-06 · [B-327](../BUGS.md).** ~~None new. R-00 shipped~~ → **one, and this audit missed it**: **[R-00](../DOMAIN_DISCOVERY_REGISTER.md)'s predicate shipped and no module can construct its input** — [C-332](../LANE_COORDINATION.md). [R-01](../DOMAIN_DISCOVERY_REGISTER.md) is sequenced and unaffected |
| **Missing workflows** | **Re-evaluation when an ICP changes** — background, and it needs the event first |
| **Missing entities** | ⬜ **Three unidentified criterion groups** |
| **Missing business events** | **`icp.declared`** — [R-14](../DOMAIN_DISCOVERY_REGISTER.md) |
| **Missing permissions** | ⛔ **None.** `Resource.ICP` already separates read from update, correctly |
| **Missing projections** | **Criterion lift** — [TASK-406](../BACKLOG.md), in progress |
| **Missing platform capabilities** | ⛔ **None.** ✅ **And none avoided this time — the infrastructure the event needs is all built** |

---

# 7 · Cross-screen validation ([D-081](../DECISION_REGISTER.md) §5)

| Capability | Screens converging | Confidence |
|---|---|---|
| **[R-00](../DOMAIN_DISCOVERY_REGISTER.md) matching** | Companies · Copilot · **ICP Builder** · Exec Dashboard · Workflow · E1 · Search · Research | ⚠️ **CORRECTED 2026-08-06 · [B-327](../BUGS.md).** ~~Shipped. Validated by the screen that needed it most~~ → **Implemented, not usable** — [C-332](../LANE_COORDINATION.md). ⚡ **The convergence count of 8 is unchanged and is the reason this matters**: eight screens read this row to decide whether they are blocked |
| **[R-01](../DOMAIN_DISCOVERY_REGISTER.md) People** | Account 360 · Copilot · **ICP Builder** · Exec Dashboard · Global Search | ⚡ **Strengthened *and split* — §3.** Two criteria at M-D, two at M-E |
| **[R-14](../DOMAIN_DISCOVERY_REGISTER.md) events at human completion points** | Signal Center · **ICP Builder** | **New, at two screens** |
| **[R-02](../DOMAIN_DISCOVERY_REGISTER.md) · [R-13](../DOMAIN_DISCOVERY_REGISTER.md)** | Segments ⬜ unchanged · authorization already correct here | **Neither strengthened, and that is information too** |

---

# 8 · What this produces

**No new backlog row.** **`icp.declared` joins [TASK-432](../BACKLOG.md)'s shape and is recorded as [R-14](../DOMAIN_DISCOVERY_REGISTER.md); everything else is carried.**

**What it changes:** ⚡ **[TASK-427](../BACKLOG.md)'s scope is sharpened — two of ICP Builder's four *Decision makers* criteria are M-E, not M-D** · **[TASK-406](../BACKLOG.md) gains a stated obligation to report which criteria it could not score** · **three criterion groups are recorded ⬜ rather than guessed.**

---

# 9 · What this document did not do

**Nothing implemented · no lane named · no wave reordered · no module created · no ADR drafted · no queue file touched · no backlog row added.** **And it invented no criterion group** — 410 says seven, the repository evidences four, **and the other three are recorded as unknown.**
