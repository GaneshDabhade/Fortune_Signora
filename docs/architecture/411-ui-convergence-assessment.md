# 411 — Repository impact assessment against the approved UI

> **Lane C — Product Office, 2026-08-04.** Measured against `origin/integration`, not against this branch and not against the roadmap. Companion to [410](410-approved-ui-specification.md), which records what became authoritative.
>
> **This assessment identifies backend capability. It does not redesign a screen, sequence a lane, or assign anybody.**

## 1 · The headline, stated before the detail

**The approved product is far closer to the repository than a sixteen-screen design project suggests, and the gap is concentrated in four places rather than spread across sixteen.**

| Measured on `origin/integration` | |
|---|---|
| Backend modules | **16** |
| HTTP endpoints across 12 module routers | **46** |
| Frontend routes | **11**, of which 5 are authentication |
| Frontend test files | **87** — zero Storybook, zero Cypress, zero pixel snapshots |

**Eleven of the sixteen screens are mostly a read surface over intelligence that already exists.** Account 360 alone reuses eight existing endpoints. **The four real gaps are People, Reports, Global Search and the Shell's own services** — and only the first of them is architecturally blocked.

## 2 · Screen → module → capability

**Reuse column is the governing one.** 🟩 existing capability, read differently · 🟠 existing module, new capability · 🔴 nothing to reuse.

| Screen | Reuses | Missing backend capability | |
|---|---|---|---|
| **Account 360** | `buying_score_engine` · `observation_engine` · `timeline` · `opportunity_engine` · `ai_research_engine` · `ai_platform` · `signal_engine` · `business_event_engine` — **8 endpoints, 8 modules** | Notes with mentions · contacts · product-usage and intent panels | 🟩 |
| **AI Research** | `ai_research_engine` POST+GET `/research` — **built, with an interface layer** | Document sections · preserved edits through regeneration · recorded refusals | 🟩 |
| **Companies** | `opportunity_engine` `GET /accounts` · `knowledge_graph` `account-identities`, `account-search` | Saved views and segments · bulk actions with 24h reversal · import · export with field-level permissions | 🟠 |
| **Signal Center** | `signal_engine` `signal-catalog`, `validation` | **Triage state** — assign, snooze, dismiss-with-reason, and the audit of each · rule precision and retune proposals | 🟠 |
| **ICP Builder** | `commercial_profile` `GET/PUT /icp`, `GET /icp-segments` — **the declaration surface is built** | Criterion-level lift against closed-won · fitted weights and drift · backtest · TAM funnel · validation warnings | 🟠 |
| **Opportunity Intelligence** | `opportunity_engine` · `buying_score_engine` contributions · `signal_engine` validation | Probability model distinct from the rep's stage · competitor mentions · conversation intelligence (talk ratio, commitments) | 🟠 |
| **Executive Dashboard** | `opportunity_engine` `/accounts`, `/accounts/decided` · `buying_score_engine` `/score` | Quarter aggregates · commit / best-case / projection against a plan · stage conversion and ageing · movement since a date | 🟠 |
| **CRM Integrations** | `integrations` — connections, catalog, connect, disconnect · `ResolveExecutionContext` **built and unwired** | The inbound read path — **[409](409-inbound-source-port-contract.md) defines it** · field mapping · sync health · write-back (E2) | 🟠 |
| **AI Copilot** | `ai_platform` narration · `ai_reasoning_engine` · **`sales_engagement`** | **Interface layers.** `ai_reasoning_engine` and `sales_engagement` both have **no `interface/` directory** | 🟠 |
| **Settings** | `workspace_tenancy` — members, roles, invitations, ownership, history — **13 endpoints, the largest router in the repository** | SSO/SCIM · API keys and webhooks · audit-log export · seats and billing | 🟠 |
| **App Shell** | `workspace_tenancy` workspaces and membership | **Global scope service** · saved views · **notifications** · system status · impersonation · sandbox environment · trial and seat state | 🟠 |
| **Global Search** | `knowledge_graph` `account-search` — **1 of 4 object types** | People, calls and deals as searchable types · typed grouping and ranking · saved and monitored searches | 🟠 |
| **Workflow Automation** | Outbox, relay, dispatch, idempotency, dead-lettering, ARQ pools — **all built** | The `workflow` bounded context. **[ADR-0402](adr/0402-a-rule-is-data.md) specifies it and is READY FOR RATIFICATION** | 🟠 |
| **Reports** | — | Report definitions · blocks · queries · narrative regeneration · three renderings · permission-respecting shares | 🔴 |
| **People Intelligence** | — | **Person as an entity. Everything else on the screen depends on it** | 🔴 |
| **Design System v2** | — | **None. This screen requires no backend at all** | — |

## 3 · The four real gaps

### 3a · People — the only architecturally blocked screen

**`EntityKind` has two members, `COMPANY` and `TECHNOLOGY`, and the docstring says the absence is deliberate:** *"Person is deliberately absent… there is no identity to resolve. Adding people now would mean inventing one."* `50-sales-engagement.md`, written by Lane A on 2026-08-03, restates it: *"A committee is a **template of roles**, never a list of people."*

**The approved People Intelligence screen is entirely about named individuals** — Sørensen, Bruun, Hald — with roles, stances, evidence, engagement history, an org chart marked confirmed-versus-inferred, a relationship graph, and a timeline of departures and role changes.

**These cannot both stand.** The approved product requires the entity the architecture deliberately declined to create.

> **[ADR-0400 — Person as an entity](adr/0400-person-as-an-entity.md) has been READY FOR RATIFICATION since before this directive. It is now a precondition of the approved product rather than a proposal about it.** Its assumptions were re-verified against `origin/integration` on 2026-08-04 and still hold.

**Nothing else on that screen is blocked by anything else.** Engagement, timeline and inference-marking all have working analogues in `observation_engine` and `timeline`. **The entity is the whole blocker.**

### 3b · The Shell's own services — the widest gap, and it is not one screen's

**The App Shell specification is 22 numbered sections, and it states that global scope is applied before a module renders.** *"Global scope survives navigation, serialises to the URL, and can be saved as a named view."*

**Nothing in the repository provides this.** It is not an Account 360 feature or a Companies feature; it is a service every screen consumes, and building it inside any one module is how it becomes sixteen copies. **This is the aggregate test applied to the frontend**, and it is the reason the design review's *"nobody consumes the App Shell"* is recorded in [410](410-approved-ui-specification.md) as a capability question.

**Notifications is the second shell service, and it is the older problem.** The shell specifies a three-tab popover with unread state, per-item actors, and AI-marked items. **[ADR-0040](adr/0040-notifications.md) is `Proposed` and there is no module.** `MESSAGE_DELIVERY` is still absent from `LIVE_CAPABILITIES`.

**ADR-0402's central argument survives this and is strengthened by it.** It made `workflow` publish an event rather than call a notifier precisely so *"a module that does not exist stops being a blocker and becomes a subscriber."* **The approved shell now gives that subscriber a specified home.**

### 3c · Reports — the only screen with nothing to reuse

**No module, no endpoint, no document.** Report definitions, blocks, queries, three renderings, narrative regeneration that preserves human edits, and shares that respect each viewer's permissions.

**It is also the least entangled.** Everything it renders comes from surfaces that exist or are listed above, and nothing else depends on it. **On the evidence it is the lowest-priority screen in the approved set, and the assessment says so rather than leaving it to be inferred from position.**

### 3d · Global Search — one object type of four

`knowledge_graph` `account-search` exists and works. **The approved specification needs accounts, people, calls and deals**, typed grouping, explainable ranking, and saved searches that can be monitored into notifications.

**People depends on §3a. Calls depend on conversation intelligence, which does not exist.** So Global Search is not independently buildable in full — but **the account group is, and the specification's own structure allows a group to be absent.**

## 4 · The recurring pattern, now at six

**Five instances were already recorded: A5's observations · E1's firmographic read · E1's connect route · the signal profile · `ai_reasoning_engine`. The sixth arrived with `sales_engagement`.**

**`sales_engagement` is fully built** — `application/`, `domain/`, `infrastructure/`, prompts, an evaluation harness with a dataset, and a `public/` exporting 25+ types including `Approach`, `ApproachBrief`, `NextAction`, `Recommendation`, `Risk` and `ProductFit`. **It has no `interface/` directory.** Neither does `ai_reasoning_engine`.

**The approved design has a home for every one of those types.** *"Ranked by expected effect on this quarter · you approve, Signora drafts."* *"Nothing sends without your approval."* The Copilot's six verbs are `Recommendation`, `Risk` and `NextAction` under different names.

> **The three-question heuristic returns the same answer it has returned five times: it exists · a customer cannot reach it · nothing consumes it.** The approved UI does not create this work — **it names the consumer that was missing.**

## 5 · Recommended implementation order

**Ordered by reuse, architectural readiness and dependency — not by the order screens appear.** No lane is named and nothing is assigned.

| | Screens | Why here |
|---|---|---|
| **1** | **Account 360 · AI Research** | Highest reuse in the repository — eight existing endpoints and one built interface layer. **Neither needs a decision from anybody** |
| **2** | **Companies · Signal Center · ICP Builder** | Existing modules, new capability, no new bounded context. Signal Center's triage state is the largest single item and is self-contained |
| **3** | **The Shell's services** | **Every later screen inherits them.** Building screens 4–16 before global scope exists is how sixteen copies of it get written |
| **4** | **AI Copilot** | Two built modules that need interface layers. **The cheapest large gain in the assessment** |
| **5** | **Opportunity Intelligence · Executive Dashboard** | Depend on aggregates and a probability model that do not exist yet |
| **6** | **CRM Integrations · Workflow Automation** | **Both blocked on a signature, not on engineering** — C-326 and ADR-0402 respectively |
| **7** | **People Intelligence · Global Search** | People blocks Search. **ADR-0400 unblocks both** |
| **8** | **Reports** | Nothing to reuse, nothing depends on it |

**Screens below priority 5 may remain planned. The design project contains more product than should be built at once, and saying so is part of the assessment.**

## 6 · Obsolete UI implementation

**Classified against the approved design. `KEEP` where the implementation already matches, `REPLACE` where the capability stays and the implementation changes, `DELETE` where the approved design supersedes it entirely.**

| | Count | Verdict |
|---|---|---|
| **KEEP** | `lib/` — 34 files: API client, auth, query hooks, permissions, theme, workspace provider | **None of it is presentational.** A redesign does not touch a query key |
| **REPLACE** | `components/` — 51 files across `commercial/`, `intelligence/`, `integrations/`, `shell/`, `ui/`, `timeline/` | The capability stays; the implementation converges to Design System v2's 18 canonical components |
| **DELETE** | **none identified** | — |

> **The honest finding is that there is very little obsolete UI, because there is very little UI.** Eleven routes, five of them authentication. **The repository has not built enough frontend to have made much of it obsolete** — which is the same finding `37-product-surface.md` made on 2026-07-31 and is the reason this transition is cheap rather than expensive.

**Nothing is marked *Superseded by Approved UI Specification* in this pass, because nothing yet qualifies.** The wording is reserved and will be applied when a screen is genuinely replaced rather than filled in.

## 7 · Obsolete UI tests

**Reviewed all 87. The recommendation is to delete none of them, and the reason is a property of how they were written.**

**There are no Storybook stories, no Cypress specs, no visual-regression baselines and no pixel snapshots in the repository.** `e2e/visual.spec.ts` states why and the reasoning survives the redesign intact:

> *"A pixel snapshot of a screen whose content is computed from today's dates fails daily and is re-baselined until it asserts nothing… What is asserted instead: **properties a customer would notice and a designer would call a bug**, none of which depends on a pixel."*

| | Verdict |
|---|---|
| `design-tokens.test.tsx` | **KEEP — and it becomes more valuable.** It asserts no component hardcodes a colour, which is exactly the property a token migration needs |
| `visual.spec.ts` · `consistency.spec.ts` · `accessibility.spec.ts` | **KEEP.** No sideways scroll, nothing clipped, no invisible text, screens agree with each other — all true of the approved design too |
| `no-mock-data.test.tsx` | **KEEP.** *"A page built against hand-written JSON encodes a shape the domain does not have."* **The single most relevant test in the suite during a UI convergence** |
| Component tests — 45 files | **REWRITE alongside their components**, not before and not separately |
| `unit/` · `contract/` — 12 files | **KEEP.** Not UI |

**No backend test is affected by anything in this document.**

## 8 · What this assessment does not resolve

**Three questions are the product owner's and are stated here rather than answered.** They are carried into `DECISION_PACKS.md` in the form the Product Office uses, not created here.

> **The approved product requires a Person entity.** ADR-0400 is prepared, verified and unsigned. **Nothing about People Intelligence, and half of Global Search, can proceed without it.**

> **The approved Shell requires notifications.** ADR-0040 is `Proposed` with no module. **This is now a shell dependency, not only a Workflow dependency.**

> **The approved Shell specifies services no module owns** — global scope, saved views, system status, impersonation, sandbox. **Whether these are a platform concern or a frontend concern decides whether an ADR is needed**, and that is a boundary question.
