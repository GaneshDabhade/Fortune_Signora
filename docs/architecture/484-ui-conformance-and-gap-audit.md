# 484 · The remaining twenty-five screens, and what stands between here and the product

**Lane C · Product Office · 2026-08-07.** **Product owner's instruction: audit the remaining UI designs and find the gaps to the end goal.**

> ⚡ **[478](478-design-conformance-audit.md) measured one design of twenty-six and said so**: *"the other twenty-five are unaudited, and the finding above should not be assumed to hold for them — it is likely, since no implementation file anywhere references a design document, but likely is not measured."* **This measures them.**

---

# 0 · The two findings, before the evidence

> ## ⛔ **Twenty of twenty-five designs show no evidence of derivation. Fifteen have no route at all.**
>
> ## ⚡ **And the gap is not the backend. Sixteen of nineteen modules are fully built — domain, application and interface — while the surface that would expose them does not exist.**

---

# 1 · Method, and the version of it I threw away

**First attempt: count every capitalised string in a design and search the implementation.** ⛔ **Discarded before reporting.** **It scored `CRM Integrations` at 41% and `Global Search` at 10%, and the difference was mostly how often each design happened to say *Save*, *Cancel* or *Settings*.** ⚠️ **[B-101](../BUGS.md)'s class: a count by proxy rather than by structure.**

✅ **What replaced it.** **A phrase is used only if it appears in *exactly one* of the twenty-six designs** — so `Reset your password` counts and `Save` does not — **and is 12–44 characters, two to seven words.** ⚡ **A distinctive phrase in the code is evidence of derivation; a common one is evidence of English.**

**Searched: every `.tsx` and `.ts` under `frontend/` on `origin/integration`.**

---

# 2 · Per-screen conformance — measured

| Screen | Distinctive phrases | In code | |
|---|---|---|---|
| **Authentication** | 47 | **4** | 🟢 *Create your account*, *Reset your password* |
| **System States** | 34 | **2** | 🟡 *The scoring service did not respond.* |
| **CRM Integrations** · **Design System v2** · **Global Search** · **Help Center** · **Workflow Automation** · **Workspace Setup** | 10–46 | **1 each** | 🟡 one phrase apiece |
| ⛔ **AI Copilot · AI Research · Account 360 · App Shell · Billing · Companies · Design Review · Executive Dashboard · Notification Center · Onboarding · Opportunity Intelligence · Reports · Security Center · Settings · Signal Center · Team Management · User Profile** | 7–40 | **0** | ⛔ **no evidence of derivation** |

> ⛔ **Seventeen screens score zero.** ⚠️ **Including `Account 360` (30 distinctive phrases), `Team Management` (40) and `App Shell` (29) — all three of which *have* a built surface.** ⚡ **So they were built, and not from the design.**

✅ **Authentication moved.** **[478](478-design-conformance-audit.md) found 1 of 11 named elements; this finds 4 distinctive phrases.** **Not conformance — but no longer nothing.**

---

# 3 · ✅ One thing genuinely changed since 478

**[478](478-design-conformance-audit.md): *"`grep` for any reference to the canonical design across `frontend/app` and `frontend/components` returns nothing. No implementation file cites a design document."***

⚡ **Five files now do**, and four are one slice:

| | |
|---|---|
| `components/ui/command-palette.tsx` · `confidence.tsx` · `drawer.tsx` · `error-state.tsx` | **Lane A's [TASK-478](../BACKLOG.md)** — Design System v2 slice 3 |
| `app/globals.css` | 2 references |

> ⚡ **That is the first UI in this repository built *from* the design rather than beside it**, and it is the row this office decomposed out of `TASK-448` four days ago. **The mechanism works; it has run once.**

---

# 4 · The route gap

**Ten designs have a surface. Fifteen do not.**

| ✅ Has a surface | ⛔ No route |
|---|---|
| Authentication *(5 routes)* · Account 360 · Companies · Settings · Team Management · CRM Integrations · Workspace Setup *(partial)* · App Shell *(layout)* · Design System v2 *(`components/ui`)* · System States *(cross-cutting)* | **AI Copilot · AI Research · Billing · Design Review · Executive Dashboard · Global Search · Help Center · Notification Center · Onboarding · Opportunity Intelligence · Reports · Security Center · Signal Center · User Profile · Workflow Automation** |

**13 `page.tsx` routes against 25 designs.**

---

# 5 · ⚡ The gap is not the backend, and this is the number that matters

| | |
|---|---|
| **Modules fully built** *(domain + application + interface)* | ⚡ **16 of 19** |
| **Partial** | **`action_batch`** *(domain only — [TASK-463](../BACKLOG.md) is `READY`)* · **`people`** *(no interface — [TASK-428](../BACKLOG.md) is `IN VALIDATION`)* |
| **Designs with no route** | ⛔ **15 of 25** |

> ## **The intelligence pipeline is built. The product that shows it is not.**

⚠️ **[§2](../../CLAUDE.md) predicted this in `31-m10-design-review-evidence.md` and the rule that followed it:** *"the pipeline ran nine stages ahead of any user-visible surface and that was a real cost."* ⛔ **The cost is now measurable: sixteen working modules, and a customer can reach four of them.**

---

# 6 · ⛔ Four screens have no backlog row at all

**Every unrouted design was checked against `BACKLOG.md`.**

| Screen | Coverage |
|---|---|
| **Reports** | 10 rows · **Global Search** 4 · **AI Copilot** 3 |
| **Billing · Onboarding · Opportunity Intelligence · Signal Center** | 2 rows each |
| **AI Research · Executive Dashboard · User Profile · Workflow Automation** | 1 row each |
| ⛔ **Design Review** · ⛔ **Help Center** · ⛔ **Notification Center** · ⛔ **Security Center** | **NO ROW** |

> ⛔ **Four finalized designs are in nobody's plan.** ⚡ **[D-135](../DECISION_REGISTER.md): *every task carries an owner even when it cannot yet have an executor* — and these are not tasks at all.** ⚠️ **This office owns backlog completeness, and it did not notice.**

**Two are plausibly deliberate — `Design Review` may be an internal tool, and `Security Center` may be Enterprise-Ready scope.** ⛔ **`Help Center` and `Notification Center` are customer-facing and neither has a reason recorded.** ⚡ **A decision not to build is a decision; an absence is not.**

---

# 7 · The gaps to the end goal, ranked by what each costs

**Against [D-137 §7](../DECISION_REGISTER.md)'s five milestones. ⛔ Reporting one number for five questions is how this stayed invisible.**

| # | Gap | Size | Whose |
|---|---|---|---|
| **1** | ⛔ **Fifteen designs with no route, against sixteen built modules** | **The dominant gap** | **Lanes A and B, sequenced by the product owner** |
| **2** | ⛔ **Twenty of twenty-five screens show no derivation from the design** — every one is *Implemented* at best and none is *Design Compliant* | **Repository-wide** | **Refinement rows exist for some; most have none** |
| **3** | ⛔ **Four designs in no plan** | **4 rows** | ⚡ **Product owner — build or record why not** |
| **4** | ⚠️ **No screen has been measured against *Functionally Complete*** — loading · empty · error · permissions | **Unmeasured** | **Per-slice, [D-129](../DECISION_REGISTER.md)** |
| **5** | ⚠️ **`Production Ready` and `Enterprise Ready` are unmeasured entirely** | **Unmeasured** | **Not yet due** |

---

# 8 · What this audit did not do

⛔ **It did not open a screen.** **Presence of a phrase is not a rendered surface**, and [§2](../../CLAUDE.md) is explicit that *no frontend screen is complete until a human has reviewed it*. ⚡ **[TASK-455](../BACKLOG.md) makes that reviewable environment reachable; nobody has yet walked it.**

⛔ **It did not check the four *Functionally Complete* states** for any screen. **That belongs in each refinement slice's own gap analysis** ([D-129](../DECISION_REGISTER.md)).

⛔ **It created no rows.** **Naming four uncovered screens is a finding; deciding whether they are built is the product owner's.**

⚠️ **A zero here means *no distinctive phrase reached the code*. It does not prove a screen was never looked at** — a developer can read a design and write different words. ⚡ **But twenty screens at zero, and the only non-zero derivation being the one slice that cites its design in a comment, is a pattern rather than a coincidence.**
