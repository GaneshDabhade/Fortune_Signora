# 412 — Backend capability matrix, dependency graph and implementation waves

> **Lane C — Product Office, 2026-08-04.** The Product Transition Directive (Revision 2) makes the **module** the planning unit and the screen a consumer. [411](411-ui-convergence-assessment.md) assessed by screen; **this document is the same evidence organised the way work is actually allocated.**
>
> Measured against `origin/integration`. **No screen is designed here, and no lane is named.**

## 1 · The measurement

| | |
|---|---|
| Backend modules | **16** |
| HTTP endpoints | **46**, across **12** routers |
| Modules with an `interface/` layer | **12 of 16** |
| Modules with **no way in** | **4** — `ai_reasoning_engine` · `sales_engagement` · `provider_normalization` · `provider_platform` |

**The last two are correct as they are** — normalization and synchronization are pipeline stages, not request surfaces. **The first two are the defect**, and [411](411-ui-convergence-assessment.md) §4 records why.

## 2 · Capability matrix, by module

**`Screens` names the approved screens that consume this module. `Gap` is backend capability only.**

| Module | API | Ev | Screens consuming it | Gap | State |
|---|---|---|---|---|---|
| **`workspace_tenancy`** | **13** | 2 | App Shell · Settings | SSO/SCIM · API keys · webhooks · audit export · seats | 🟠 |
| **`commercial_profile`** | **13** | 1 | ICP Builder · Account 360 · Companies | Criterion lift vs closed-won · fitted weights · backtest · TAM | 🟠 |
| **`opportunity_engine`** | 5 | 2 | Opportunity Intelligence · Executive Dashboard · Companies · Account 360 | Probability model · quarter aggregates · movement · competitors | 🟠 |
| **`integrations`** | 4 | 0 | CRM Integrations · App Shell | **The inbound read path — [409](409-inbound-source-port-contract.md) defines it** · field mapping · sync health | 🟠 |
| **`knowledge_graph`** | 2 | **6** | Global Search · Companies · Account 360 · People | **Person as an entity** · 3 more searchable types | 🔴 |
| **`signal_engine`** | 2 | 2 | Signal Center · Account 360 · ICP Builder | **Triage state** — assign, snooze, dismiss-with-reason · rule precision | 🟠 |
| **`ai_research_engine`** | 2 | 2 | AI Research · Account 360 | Sections · preserved edits · recorded refusals | 🟩 |
| **`ai_platform`** | 1 | 1 | AI Copilot · Account 360 | Nothing structural | 🟩 |
| **`buying_score_engine`** | 1 | 1 | Account 360 · Opportunity Intelligence · Executive Dashboard · Companies | Nothing structural | 🟩 |
| **`observation_engine`** | 1 | 2 | Account 360 · People · Opportunity Intelligence | Nothing structural | 🟩 |
| **`business_event_engine`** | 1 | 2 | Account 360 · Signal Center | Nothing structural | 🟩 |
| **`timeline`** | 1 | 0 | Account 360 · People | Workspace-scoped read *(named in `51-sales-workspace.md` §3)* | 🟠 |
| **`sales_engagement`** | **0** | 0 | AI Copilot · Opportunity Intelligence · Companies | **An `interface/` layer. Nothing else** | 🟠 |
| **`ai_reasoning_engine`** | **0** | 1 | AI Copilot | **An `interface/` layer. Nothing else** | 🟠 |
| **`provider_normalization`** | — | 1 | *(none — pipeline stage)* | CRM claim vocabulary, **if [ADR-0300](adr/0300-inbound-source.md) part 3 is ruled on** | — |
| **`provider_platform`** | — | **4** | *(none — pipeline stage)* | The runner for the inbound port | — |
| **`workflow`** | — | — | Workflow Automation | **The whole module. [ADR-0402](adr/0402-a-rule-is-data.md) specifies it** | 🔴 |
| **`notifications`** | — | — | App Shell · Signal Center · Global Search · Workflow | **The whole module. [ADR-0040](adr/0040-notifications.md) is `Proposed`** | 🔴 |
| ***shell services*** | — | — | **All 16** | Global scope · saved views · system status · impersonation · sandbox. **No module owns these** | 🔴 |

> **Five modules are 🟩 — they need nothing structural at all.** Between them they carry Account 360 and AI Research, which is why those are wave 1.

## 3 · The dependency graph

**Read it as *what unblocks what*, not as module dependencies — the ratified graph in [05](05-module-dependencies.md) is unchanged and this does not amend it.**

```
                     ┌─────────────────────────┐
                     │  ADR-0400 · Person       │ ◀── the only architectural blocker
                     └────────────┬─────────────┘
                          │                │
                  knowledge_graph      observation_engine
                          │                │
                  ┌───────┴────────┐       │
            People Intelligence   Global Search (3 of 4 types)
                          │
                     AI Copilot (committee reasoning)

  ┌──────────────────────┐        ┌──────────────────────────┐
  │  ADR-0040 · Notify   │        │  O3 · shell services      │
  └──────────┬───────────┘        └────────────┬──────────────┘
             │                                  │
      App Shell notifications          global scope · saved views
      Signal Center routing            status · impersonation · sandbox
      monitored searches                          │
      workflow subscribers              ─── ALL 16 SCREENS ───

  ┌──────────────────────┐        ┌──────────────────────────┐
  │  C-326 · ADR-0300    │        │  ADR-0402 · rule is data │
  └──────────┬───────────┘        └────────────┬──────────────┘
             │                                  │
   integrations inbound port              workflow module
   provider_platform runner               Workflow Automation
   CRM Integrations · E1 · E2

  interface/ layers ──▶ sales_engagement ──┐
  (no decision needed)  ai_reasoning_engine ┴──▶ AI Copilot
```

**Four decisions gate eleven screens. Nothing else in the assessment gates anything.**

> **The graph's shape is the finding.** Screens do not depend on each other — **they depend on four rulings and two interface layers.** That is why waves are organised around unblocking rather than around screen value.

## 4 · Implementation waves

**Each wave maximises reuse and minimises dependency risk. A wave is not a milestone and names no lane.**

### Wave 1 — needs no decision from anybody

> **Account 360.** *(One screen. See both corrections below.)*

**Eleven sections across eight modules, five of them 🟩 and needing nothing structural.** **Nothing in this wave waits on a signature, a port, or a module that does not exist.**

> ⚠️ **Correction 1, 2026-08-04, before anything was built.** *"Needs no decision from anybody"* is true of what wave 1 **delivers** and false of Account 360 as a whole. **Its 27 sections are eleven served, two blocked by O1, two owned by later waves and seven with no source at all.** [414](414-wave-1-account-360.md) draws the boundary and is the package.

> ⚠️ **Correction 2, same day — AI Research moves to wave 3.** It was placed here because `ai_research_engine` is built and has a router. **The built endpoint researches one account; the approved screen researches a cohort and reports what its members share** — a different question, and the screen also inherits shell scope, which is **O3**. [416](416-ai-research-scope-gap.md) measures it. **The built endpoint still reaches a customer in wave 1, as Account 360's Research section.**

> **Both corrections came from reading the approved screen's sections instead of counting the endpoints that appeared to serve it.** The rule that follows is in [416](416-ai-research-scope-gap.md) §6: **an endpoint's existence is evidence about the backend, never about the screen.**

**Why it is first and not merely easy:** Account 360 is the flagship record page, and it is the surface that makes every 🟩 module *reachable by a customer for the first time*. **It converts existing intelligence into product without adding any.**

### Wave 2 — the two interface layers

> **AI Copilot**

**`sales_engagement` and `ai_reasoning_engine` are built, tested, prompt-versioned and unreachable.** The pattern is now at six instances and the fix has never once been a domain change.

**Placed second because it is the cheapest large gain in the assessment**, and because it needs no ruling — an interface layer over a module's own `public/` is 🟠, not 🔴.

### Wave 3 — the shell, and it is a prerequisite not a screen

> **Shell services · Companies · Signal Center · ICP Builder · AI Research**

**AI Research joins here** ([416](416-ai-research-scope-gap.md)): it inherits shell scope, so it cannot precede the service that supplies it, and **its substantive gap — cohort-scoped research — is larger than the screen and independent of O3.**

**The shell is here because every later wave inherits it.** Global scope is applied before a module renders; building waves 4–6 first means writing it sixteen times. **O3 decides whether it needs an ADR, and that is the only thing holding it.**

**The three screens beside it are existing modules gaining new capability** — no new bounded context, no new dependency edge. Signal Center's triage state is the largest single item in the wave and is entirely self-contained.

### Wave 4 — aggregates

> **Opportunity Intelligence · Executive Dashboard**

**Both need a probability model and quarter aggregates that do not exist.** They share almost all of it, which is why they are one wave rather than two — building either separately produces the second copy the reuse rules exist to prevent.

### Wave 5 — the ruled work

> **CRM Integrations · Workflow Automation**

**Both are blocked on a signature rather than on engineering.** C-326 has [409](409-inbound-source-port-contract.md) waiting; ADR-0402 is complete with five alternatives assessed. **The moment either is ruled, its wave is ready** — which is why they sit together and late.

### Wave 6 — Person

> **People Intelligence · Global Search**

**ADR-0400 unblocks both, and nothing else does.** Global Search's account group is buildable in wave 3 if wanted; the full four-type surface is here.

### Wave 7 — Reports

> **Reports**

**Nothing to reuse, and nothing depends on it.** Everything it renders comes from surfaces delivered in waves 1–4. **It is last on evidence, not on taste.**

## 5 · What the waves deliberately do not do

**They do not implement sixteen screens sequentially**, and they do not follow the design project's file order — Reports appears in the middle of the project and last here; Account 360 appears seventh and is first.

**They do not front-load the visually impressive.** Executive Dashboard is the screen a buyer sees first and sits in wave 4, because **it needs aggregates that would otherwise be built twice.**

**No wave contains a screen whose blocker is inside it.** A wave that begins by waiting is not a wave.

## 6 · Reuse report

**The rule the directive restates — *the approved UI is not permission to duplicate backend capability* — was applied to every gap in [411](411-ui-convergence-assessment.md). What it found:**

| | |
|---|---|
| **Reuse, unchanged** | 46 endpoints · 27 event types · the whole intelligence pipeline · outbox, relay, dispatch, idempotency, dead-lettering, ARQ · `ResolveExecutionContext` · the Signal Catalog · the Integrations Catalog · `live_capabilities` |
| **Extend an existing module** | 10 of the 16 gaps |
| **New module, genuinely** | **2** — `workflow` and `notifications`, **both already specified in a prepared ADR** |
| **New bounded context invented by this transition** | **None** |

> **Not one screen produced a new module that was not already on the books.** The approved UI named consumers for capability that existed; it did not ask for a second copy of any of it.
