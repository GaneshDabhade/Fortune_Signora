# 51 · Sales Workspace — discovery

> **Assigned 2026-08-03 by the product owner, to Lane A, immediately after SE-09d was handed to QE.** *"When a salesperson logs into Signora every morning, they should land here. The question it answers is simple: what should I do today?"*
>
> **No code was written before this document**, on the discipline that produced nine Lead Lifecycle slices without changing a domain once, and a Sales Engagement milestone whose central noun turned out not to exist.
>
> **The product owner asked to be challenged rather than implemented.** §4 is that challenge, and it disagrees with parts of the brief.

---

## 1 · The finding that decides the milestone

**The Sales Workspace already exists, it is already the homepage, and it was already designed from first principles against the same brief.**

`frontend/app/(app)/page.tsx` is `/`. Its own docstring, written at M12.3:

> *"The morning workspace — **which accounts should I work on today?** … **Not a dashboard.** There is no chart, no KPI tile, no summary of totals. A dashboard reports on a period; this answers a question a person is about to act on."*

**It replaced an Overview page** — three permanently-empty counters and a promise of an integration a milestone away — which was *"reviewed from first principles and retired at M12.3 (**D38**)"*.

> **The assignment's central instruction — *think bigger than a dashboard, most CRMs already have dashboards, people rarely live inside dashboards* — is a decision this repository already made, acted on, and shipped.** Independently reaching it twice is a strong signal it is right. It is also the reason this milestone must not begin by building one.

**So the milestone is not *"build a homepage."*** It is:

> **The homepage answers one question well. It has to become a place a seller can stay.**

Today `/` answers *which accounts deserve attention*, ordered, with evidence. It does not answer *what changed*, *what is getting worse*, *what should I prepare for*, or *what did I say I would do*. **And there is nowhere to go afterwards** — see §3.

---

## 2 · Repository reuse audit

| Requested capability | Exists? | Verdict |
|---|---|---|
| **Accounts Heating Up** | ✅ **This is `/` today** — attention ranking, score movement, the reason, evidence state, contested marks | **Already built. Do not rebuild** |
| **Pipeline Movement** | ✅ `Stage`, `MACHINE_AUTHORED`, `OPEN_STAGES`, the transition table, held-since, ownership — Lead Lifecycle, nine slices | **Compose.** Nothing aggregates it across a seller's accounts |
| **What changed** | ✅ Timeline, **and it is one of only two modules wired into the deployed worker** | **Compose — and see §3, it is per-account only** |
| **Deals At Risk** | ✅ `evidence_state`, cooling, staleness, `Risk` kinds, contested identity | **Compose.** Every input exists; nothing asks the question |
| **AI Summary** | ✅ **SE-09c/09d built exactly this machinery** — reasoning graph → closed context → pass → fence | **Reuse the architecture, not a second one.** See §5 |
| **Suggested Next Actions** | ✅ `NextAction` — approach · verify · **wait** — per account, with reasons | **Compose.** It is per-account; a day is a set of them |
| **Meetings Today** | ❌ | **Blocked** — §3 |
| **Emails** | ❌ | **Blocked** — §3 |
| **Calls** | ❌ | **Blocked**, and further than emails — §3 |
| **Tasks** | ❌ **No backend anywhere in the repository** | **Blocked** — §3 |
| **Recommended Outreach** | ⛔ | **Refused by Signora's own first principle** — §4 |

> **Six of eleven are composition over capabilities that already exist and are read by nothing.** That is the seventh time this pattern has appeared in three milestones: *built, correct, and unreachable.*

---

## 3 · Missing capability audit — and the honest size of it

### Every integration is `connectable=False`. There is no acquisition path.

```python
CATALOG: Final[dict[str, CatalogEntry]] = {
    "salesforce":       CatalogEntry(..., connectable=False),
    "hubspot":          CatalogEntry(..., connectable=False),
    "google_calendar":  CatalogEntry(..., connectable=False),
    "google_workspace": CatalogEntry(..., connectable=False),
    ...
}
```

The module's own words: *"no acquisition path exists yet, because the OAuth flow belongs at the frontend edge and has not been built. The catalog says what the product understands; it does not pretend the button works."*

**And nothing anywhere imports `integrations.public`.** The connection register has no consumer. So a connected calendar would still reach no screen.

| Requested | What it actually needs | Owner |
|---|---|---|
| **Meetings Today** | An OAuth acquisition flow · a calendar sync · a meeting↔account resolver · storage · a projection | Integrations + a new consumer |
| **Emails** | The same, plus email↔account attribution, plus a lawful-basis position on message content | Integrations + **[C-210](../LANE_COORDINATION.md)** territory |
| **Calls** | All of the above **and a call-recording integration nothing in the catalog lists**. Lead Lifecycle already recorded the constraint in LO-06: *Signora cannot see a call* | Not in the catalog |
| **Tasks** | **A bounded context that does not exist.** No table, no module, no event, no vocabulary | 🔴 New context |

> **Four of the eleven initial capabilities are a different milestone wearing this one's name**, and one of them (Tasks) is a new bounded context. **This is the same shape as *"Signora has no people"*** — the honest answer is not to build a thinner version, it is to say which four and why.

### `/settings/connections` is a closed loop with no door

Recorded in [43-customer-experience.md](43-customer-experience.md): the Connection Center is *"linked from nowhere in the product"* — the only links to it are inside its own OAuth redirect helpers. **A customer can reach it only by already being in it.**

### A `member` can reach two screens

| | |
|---|---|
| Backend HTTP endpoints | **31**, across 11 modules |
| Navigable application screens | **5** |
| **Screens a `member` can reach** | **2** — the attention list and an account brief |

> **A workspace a seller "spends the whole day in" cannot be built on a product with two member-reachable screens.** That is not a criticism of the work — it is the measured cost of nine pipeline stages ahead of any surface, which `31-m10-design-review-evidence.md` predicted before it was felt. **It is also the single biggest constraint on this milestone**, and it is largely Lane A's own Product Surface assignment.

### Timeline is per-account, and the workspace needs it per-seller

`GET /accounts/{id}/timeline` is the only timeline endpoint. **There is no workspace-scoped "what changed across everything I hold, since I last looked."**

> **This is the highest-value unblocked gap in the entire assignment.** *"Three Target Accounts became significantly more active overnight"* — the product owner's own example of what AI should feel like — is a **workspace-scoped timeline query**, and the module that owns it is wired, live, and already writing the data.

---

## 4 · Challenging the brief, as asked

### ⛔ Recommended Outreach is refused, and not by me

The product owner's rule, adopted verbatim as Sales Engagement's design constraint and ratified in [50-sales-engagement.md](50-sales-engagement.md) §3:

> **Outreach tools optimise volume. Signora optimises relevance.**

That section rules out message generation, sequences, send, and open-tracking **by design, not for now**. The Approach Brief's own refusal list reads: *no message · no send · no cadence · no contact table.*

**"Recommended Outreach" on the workspace would reintroduce all four through a different door.** What the product *can* honestly offer is what Sales Engagement already produces: **which account, which role, why now, what to ask, and what not to claim** — and the seller writes the message in the tool that has their signature and their deliverability.

> **Recommended: rename the capability to *Recommended Attention*, or drop it.** If outreach is genuinely wanted, that reverses a ratified first principle and belongs in an ADR rather than in a workspace slice.

### ⚠️ "Emails, Calls, Meetings, Tasks" is a CRM inbox, and it is the thing the brief says not to build

The assignment says *"do not build another dashboard full of cards"* and *"most CRMs already have dashboards."* **A panel of Meetings / Emails / Calls / Tasks is the other half of a CRM home screen** — and it is the half a seller already has open in Gmail, Outlook and their calendar, rendered better, with working reply buttons.

**The question worth asking is not *"can we show today's meetings?"*** — it is:

> **"What does Signora know about the companies in today's meetings that the seller does not?"**

That is not a calendar panel. It is *"you have two meetings today; here is what changed inside those companies since yesterday"* — which is the product owner's own best example, and **it is Signora-shaped rather than CRM-shaped.** It still needs a calendar, but it changes what to build when the calendar arrives: **an intelligence overlay, not an agenda.**

### ⚠️ "Continuously" is a claim the pipeline cannot currently make

*"Three Target Accounts became significantly more active overnight"* presumes something ran overnight. **Seven of nine pipeline modules are in-process rather than worker-wired**, deliberately, pending [C-012](../LANE_COORDINATION.md) — so the pipeline advances when something pushes it, not on a schedule.

**A workspace that says *overnight* must either be true or not say it.** Timeline and AI Research are wired; the scoring pipeline is not.

### ✅ Where I think the brief is exactly right

**Progressive disclosure and glanceability**, which the attention list already practises: *"the order of information on a row is deliberate — what, why, how much it moved, how far it can be trusted. A seller decides from the first two."*

**One continuous session rather than widgets.** This is the strongest instruction in the assignment, and §5 is built around it.

**Role variants later, not now.** Correct — and cheap to preserve, because every section is a *view over a query*, not a stored layout.

---

## 5 · The architectural insight this milestone should be built on

**The Approach Brief is a reasoning graph about one Target Account. The Morning Brief is the same architecture, scoped to a seller's portfolio.**

```
  SE-09c/d, per account          this milestone, per seller
  ─────────────────────          ──────────────────────────
  evidence, committee, fits      every account I hold
        ↓                              ↓
  reasoning graph                portfolio reasoning graph
        ↓                              ↓
  CommercialContext (v2)         the same protocol, wider scope
        ↓                              ↓
  Pass → model → fence           Pass → model → fence
        ↓                              ↓
  ApproachBrief                  the workspace's narrated sections
```

**Everything below `Pass` is already built, tested and measured**: the closed-set contract, the context protocol, the draft parser, the fence, the registry, the release derivation, the harness, the golden-set discipline. **A workspace narration is a seventh `Pass` and a wider graph — not a second AI system.**

> **The rule that must survive this milestone:** the deterministic layer decides what changed and what matters; the model only explains it. A workspace that let a model choose the day's priorities would put ranking behind a prompt — the exact mistake [ADR-0200](adr/0200-sales-engagement.md) refused for role ranking.

**And the fence gets more valuable, not less, at portfolio scope.** A summary that invents a company name is worse when it is the first thing a seller reads every morning.

---

## 6 · What is buildable now, in the order value arrives

| | Slice | Depends on |
|---|---|---|
| **SW-01** | **This document**, and an ADR if §7 D-2 says the workspace is its own bounded context | Product owner |
| **SW-02** | **Workspace-scoped *what changed since you last looked*** — Timeline across held accounts. **The highest-value unblocked capability in the assignment** | Timeline is wired and live |
| **SW-03** | **Deals at risk** — cooling, stale evidence, contested identity, held-a-long-time. Every input exists; nothing asks | SW-02 |
| **SW-04** | **Pipeline movement** — stage transitions across the seller's accounts, from Lead Lifecycle's own history | SW-02 |
| **SW-05** | **The day as one session** — the attention list, what changed, what is at risk and what to do next, on one screen with progressive disclosure | SW-02…04 |
| **SW-06** | **Morning narration** — a workspace `Pass` over the portfolio graph, refused when unsupported | SE-09c fence · SW-05 |
| **SW-07+** | **Meetings · Emails · Calls · Tasks** | ⛔ §3 — integrations, and Tasks is a new context |

**Every slice SW-02…06 is composition over modules that are built, wired and read by nothing.** None needs another lane. **None needs a new bounded context.**

---

## 7 · Product owner decisions required

| | Decision | Why it matters | Recommendation |
|---|---|---|---|
| **D-1** | **Is *Recommended Outreach* in or out?** | It reverses a ratified first principle (§4). Everything else in the brief is compatible with it | **Out.** Rename to *Recommended Attention*. If it is genuinely wanted, it needs an ADR, not a slice |
| **D-2** | **Does the workspace get its own bounded context, or is it a composition in the Product Surface?** | It reads Opportunity, Timeline, Buying Score and Sales Engagement — four modules. Sales Engagement's answer to the identical question was *a new module, with an ADR first* | **A read-model in the Product Surface, not a new module.** Unlike Sales Engagement it draws **no commercial conclusion of its own** — it arranges conclusions other modules already reached. A bounded context with no judgement is a folder |
| **D-3** | **Does *overnight* have to be true?** | §4. A workspace claiming continuous monitoring on a pipeline that advances only when pushed would be the repository asserting something untrue about itself | **Say *since you last looked*, which is true today**, and revisit when C-012 is answered |
| **D-4** | **Which four capabilities are deferred, and is that acceptable?** | Meetings · Emails · Calls · Tasks are 4 of the 11 named, and Tasks is a new bounded context | **Defer all four, explicitly.** They are an integrations milestone, not this one |

---

## 8 · The honest summary

**The Sales Workspace exists, and it is one question deep.** It answers *which accounts deserve attention* better than a dashboard would, and it was designed against the same brief this assignment restates — which is a reason to extend it rather than to start again.

**Four of the eleven requested capabilities are a different milestone**, gated on an OAuth flow nobody has built, a connection register nothing consumes, and one bounded context that does not exist.

**Six of the other seven are composition over capabilities that are already built and read by nothing** — and the seventh reverses a ratified principle.

> **The workspace does not need new intelligence. It needs the intelligence that already exists to reach a seller in one place, in the order they work.**
