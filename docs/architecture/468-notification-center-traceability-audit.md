# 468 · Notification Center — platform-foundation traceability audit

**Lane C · Product Office · 2026-08-06.** **[D-102](../DECISION_REGISTER.md).** **Platform foundation module 7 of 10.** Follows [467](467-system-states-traceability-audit.md).

> **Chosen second on evidence rather than order** ([Register A-2](../DOMAIN_DISCOVERY_REGISTER.md)): **[R-04](../DOMAIN_DISCOVERY_REGISTER.md) is deferred behind a trigger, and this is the screen that would fire it.**

---

# 0 · What Evidence First found, before anything was proposed

**This module is the most thoroughly pre-decided of the ten, and the audit's value is almost entirely in what it did *not* need to invent.**

| Searched for | Found |
|---|---|
| **A notification architecture** | ✅ **[ADR-0040](adr/0040-notifications.md), and it is substantial** — a bounded context, attention-versus-notification, severity carried and priority not, identity, one row per recipient, two backfill rules, workflow state, provenance, **plus three scenarios run against it that each produced a rule** |
| **The delivery substrate** | ✅ **Built, and verified in [ADR-0402](adr/0402-a-rule-is-data.md)'s own words**: *"a transactional outbox, a relay, dispatch, platform-owned idempotency, dead-lettering and ARQ worker pools. **None of it needs building.**"* |
| **A guard against promising undeliverable capability** | ✅ **`MESSAGE_DELIVERY` is excluded from `LIVE_CAPABILITIES` with its reason in the code**: *"its consumers — Recommendation Engine and Revenue Intelligence Platform — are deferred and unbuilt, so Signora has nothing to deliver"* |
| **The per-person privacy question** | ✅ **[C-302](../LANE_COORDINATION.md), raised 2026-08-02**, with the mechanism already proven: `tenant_scoped_session` sets `app.user_id`, and **`workspace` and `membership` have been user-scoped since migration `0001`** |
| **Whether notifications block Workflow Automation** | ✅ **Already solved.** [ADR-0402](adr/0402-a-rule-is-data.md) §2 makes `workflow` publish an event rather than call a notifier — ***"so Notifications stops being a blocker and becomes a subscriber"*** |
| **A second rule engine** | ⚡ **See §4 — the one genuine reuse question** |

> ## ⛔ **No new foundational capability. R-04 was discovered, is deferred by [D-027](../DECISION_REGISTER.md), and this audit does not re-raise it.**

---

# 1 · ⚡ The ratification blocker is real and its stated form is wrong — and re-measuring found something larger

**[ADR-0040](adr/0040-notifications.md)'s status block:**

> ***"Ratification requires one 🔴 change this ADR cannot make: a fifteenth entry in [04-modules.md](04-modules.md). Draft text is in §10, ready to paste."***

**Measured today rather than taken:**

| | |
|---|---|
| **[04-modules.md](04-modules.md) § Module Reference** | ⚡ **Sixteen entries, not fourteen** |
| **`backend/modules/`** | **Sixteen directories** |
| ⛔ **And they are not the same sixteen** | |

| Direction | Modules | What it means |
|---|---|---|
| ⚠️ **In code, absent from the ratified document** | **`sales_engagement`** *(zero mentions — no heading, no reference entry)* · **`integrations`** *(mentioned three times, **no Module Reference entry**)* | **Two shipped bounded contexts the architecture document does not define** |
| ⚠️ **In the document, absent from code** | **Recommendation Engine** · **Revenue Intelligence Platform** | **Two defined modules that do not exist** — correctly, both are deferred |

> ## **So `04-modules.md` — a ratified `01`–`21` document — disagrees with `backend/modules/` in four places, and Notifications would be the *seventeenth* entry rather than the fifteenth.**

⚡ **This is bigger than Notifications and was found by checking its blocker.** **`CLAUDE.md` §12: *documentation drift is treated as a bug*.** ⛔ **And it is 🔴 — `docs/architecture/01`–`21` is product-owner-plus-ADR**, so this office reports it and does not repair it.

⚠️ **The ADR is not wrong to name the blocker; it is wrong about the count, and the count was probably right when written on 2026-08-02.** **That is [D-102](../DECISION_REGISTER.md)'s point exactly: a prior conclusion is a measurement with a date on it.**

---

# 2 · ⚡ The approved screen shows four things the ADR's Day One deliberately excludes

**[ADR-0040](adr/0040-notifications.md) § *Day One — the scope, and what it deliberately excludes*:**

| In | ⛔ Out |
|---|---|
| **In-app only** · unread/read · acknowledge/dismiss · event-driven generation · idempotent by identity · workspace- and user-scoped · history · preferences *"only where immediately required"* | **email · SMS · push · Slack · Teams · digests · batching · quiet hours · escalation · reminders · reassignment · role-based routing** |

**[418 §1](418-platform-foundation-assessment.md) records the approved screen as: *"Event × channel matrix · digests · quiet hours · custom rules."***

> ## **Four of the screen's four headline features are on the ADR's exclusion list: the channel matrix, digests, quiet hours, and the rules that drive them.**

⛔ **This is not a contradiction and must not be reported as one.** **[ADR-0040](adr/0040-notifications.md) was written 2026-08-02; the platform-foundation designs arrived 2026-08-04.** **Day One is a *sequencing* decision taken before the design existed — not a denial of it.**

⚠️ **But it is unreconciled, and it is the kind of gap [D-075](../DECISION_REGISTER.md) exists to catch**: *"the approved UI is the authoritative expression of the intended product experience."*

**The question this raises is one and it is the product owner's:**

> **Does *Day One* still mean day one, now that the approved design shows the full surface?** **If yes, the ADR is correct and the screen ships in stages — and the staging should be stated where a lane will read it.** **If no, the ADR's scope section is re-cut before ratification, not after.**

---

# 3 · [C-302](../LANE_COORDINATION.md) — the only architectural question, and it is four days old

> **Whether a tenant-owned table may carry a *second* RLS predicate scoping rows to `app.user_id` within the workspace.**

| | |
|---|---|
| **Why it is genuine** | **Every workspace-owned table so far holds facts about the *organization*. A notification holds a fact about a *person*** — what they were told and whether they read it. **Under a workspace-only policy any member reads any colleague's notifications** |
| ✅ **Why it is cheap** | **The mechanism exists and needs no platform change.** `app.user_id` is already set transaction-locally, and **`workspace` and `membership` have been user-scoped since migration `0001`** — so the predicate is ordinary, not novel |
| 🔴 **Why it is still the product owner's** | **[11-tenancy.md](11-tenancy.md) describes a one-key model and is `01`–`21`.** ⛔ *"A lane invented a second tenancy dimension inside a slice"* is precisely the drift the Change Budget stops |
| **Blocks** | **N-01's migration, and nothing before it** |

⚠️ **It has been `OPEN` since 2026-08-02 and carries no `Status` row** — one of the fourteen [`state-check`](../../infra/state-check.py) now reports. **It is a decision waiting in a document nobody routes.**

---

# 4 · The one reuse question this audit adds

**The screen shows *custom rules*: which events, to whom, on which channel, subject to quiet hours.** **[ADR-0402](adr/0402-a-rule-is-data.md) already ruled what a rule is — *data, evaluated over published events, publishing one event* — for Workflow Automation.**

| | |
|---|---|
| ⚡ **The condition half is the same shape** | *"When an opportunity's stage changes and its value exceeds X"* is one sentence whether it ends in an action or in a notification |
| ⛔ **The consequent half is not** | **A workflow rule decides *whether something should happen*. A notification rule decides *who is told and how*.** **Routing, channel and quiet hours have no analogue in [ADR-0402](adr/0402-a-rule-is-data.md)** |
| ⚠️ **The risk if nobody asks** | **A second condition-tree evaluator, free to disagree with the first** — **the same defect [462 §1](462-observed-attributes-proposal.md) refused for `ClaimSet`, and `commercial_profile/domain/competitors.py` refused in its own code** |

> **Raised as a question, not a proposal.** ⛔ **Neither module is built, and designing the shared half before either exists is the speculative abstraction §6 forbids.** ✅ **What is cheap and worth doing is recording the trigger**: **whichever of `workflow` and `notifications` is built second must state whether it reuses the first's condition model or explain why not.**

---

# 5 · The twelve dimensions

| | |
|---|---|
| **Foundational entities** | ⛔ **None new.** `Notification` · recipient · severity · read state — **all defined in [ADR-0040](adr/0040-notifications.md)** |
| **Aggregates** | ✅ **One row per recipient** — [ADR-0040](adr/0040-notifications.md) §5, decided |
| **Value objects** | ✅ **Severity, carried and not ranked** — §3 |
| **Workflows** | ✅ **Unread → read → acknowledged/dismissed** — §7, with the `UPDATE` grant it needs named |
| **Business events** | 🟡 **Notifications *consumes*; [ADR-0402](adr/0402-a-rule-is-data.md) made it a subscriber.** ⚠️ **The trigger vocabulary is 23, not 34 and not 82** — a builder offering the catalogued set advertises triggers that never fire |
| ⚡ **Permissions** | 🔴 **[C-302](../LANE_COORDINATION.md) — the audit's only open architectural question** |
| **Lifecycle models** | ✅ **Decided**, including two rules that stop a backfill paging everyone |
| **AI capabilities** | ✅ **Provenance recorded and AI-authored content marked** — §8 |
| **Platform capabilities** | ✅ **Outbox · relay · dispatch · idempotency · dead-lettering · ARQ — all built** |
| **Operational requirements** | ⚠️ **`MESSAGE_DELIVERY` stays out of `LIVE_CAPABILITIES` until a delivered channel ships** — and the code already says so |
| **Reusable abstractions** | ⚡ **§4** |
| ⚠️ **Ownership** | **A new bounded context with no `modules.toml` row** — **[TASK-427](../BACKLOG.md)'s shape exactly.** **Recorded once here rather than treated as a new finding** |

---

# 6 · Recommendation

| | | |
|---|---|---|
| **1** | 🔴 **Reconcile [04-modules.md](04-modules.md) with `backend/modules/`** | **Four discrepancies, and Notifications is a fifth waiting.** ⚡ **Worth more than this audit's subject** — every future module reference is measured against that document |
| **2** | 🔴 **Rule on [C-302](../LANE_COORDINATION.md)** | **Four days old, cheap, and it blocks N-01's migration** |
| **3** | 🔴 **Confirm or re-cut [ADR-0040](adr/0040-notifications.md)'s *Day One*** | **§2 — the design arrived after the scope was set** |
| **4** | ✅ **Record §4's trigger** | 🟢 **One sentence in the Register.** No design work |
| ⛔ | **Do not re-raise [R-04](../DOMAIN_DISCOVERY_REGISTER.md)** | **[D-027](../DECISION_REGISTER.md) deferred it and nothing here disturbs that** |

**⛔ No backlog row · no ADR drafted · no lane named · nothing implemented.**

---

# 7 · What this audit did not do

**It did not re-derive [ADR-0040](adr/0040-notifications.md)** — which is thorough, and re-deriving it would be the review-that-rewrites §6a forbids · **did not reopen [D-027](../DECISION_REGISTER.md)** · **did not propose a rule model** · **did not invent a UI element.**

⚡ **And its most useful finding is not about notifications.** **Checking one ADR's stated blocker — *"a fifteenth entry"* — found a ratified architecture document four modules out of step with the code it describes** ([B-401](../BUGS.md)).

**The blocker is real. Its arithmetic was correct on 2026-08-02 and is not correct now** — which is the whole of [D-102](../DECISION_REGISTER.md)'s second principle, met on the first audit that looked for it: **a prior conclusion is a measurement with a date on it, and this one was four days old.**
