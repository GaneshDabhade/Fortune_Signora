# 48 — The customer journey, end to end

> **A record, not an instruction.** Lane B, 2026-08-03, as Product Journey owner. Written by walking the repository as a new customer would walk the product, and verifying every claim against code rather than against documentation.
>
> **Its purpose is to find where completed capabilities fail to connect.** Several of this repository's largest improvements came from that, not from new features.

---

## 1 · The finding that outranks everything else in this document

**A customer can complete onboarding, declare what they sell, describe who buys it, name the companies they want watched — and nothing will ever happen.**

**The deployed worker registers two consumers.** Verified twice, from `apps/worker/subscriptions.py`:

| Consumer | Registered |
|---|---|
| `timeline.project` | **Yes** — nine event types, added yesterday by [B-301](../BUGS.md) |
| `ai_research_engine.run_requested` | **Yes** — its own event, a self-loop |
| `provider_platform.sync_declared_targets` | **No** |
| `knowledge_graph.resolve_identity` | **No** |
| `observation_engine.observe_changes` | **No** |
| `business_event_engine.detect` | **No** |
| `signal_engine.generate` | **No** |
| `buying_score_engine.compute` | **No** |
| `opportunity_engine.qualify` | **No** |

> **Seven pipeline stages have handlers that are written, tested, and never registered.** The pipeline is wired end to end in `backend/tests/pipeline.py` — **a test file is its only composition root.**

**This is not a new discovery; it is the same one, measured.** [C-012](../LANE_COORDINATION.md) has recorded *"the deployed worker consumes nothing"* since M3A and is `WAITING` on an RFC. **What is new is what it means for the journey**, which nobody had traced: `commercial_profile.target_accounts_changed` is published into the outbox, the relay delivers it, and **no consumer exists** — so the first hand-off in the product is also the last.

**Timeline makes it visible rather than fixing it.** Timeline now projects nine event types faithfully. **Six of them have no producer in a deployed environment**, because the stages that would publish them never run. A customer's account history will show the target-account declaration and nothing after it.

**Every screen downstream is therefore correct and permanently empty**: the attention list, the account brief, contributions, validation, evidence. **They are not broken — they are honest about a pipeline that never ran.**

---

## 2 · The journey, stage by stage, against the code

**Legend — `✅` reachable and works · `◐` built, reachable, empty without §1 · `⚠` gap · `✖` absent**

| # | Stage | State | Evidence |
|---|---|---|---|
| 1 | Landing · sign up · verify · sign in | ✅ | Better Auth in Next.js; R6-01…04 and R12-01 fixed. **R6-05 open:** *nothing tells a new account what to do next* |
| 2 | Create an organization | ✅ | `POST /workspaces`; R7-03 fixed — a signed-in user with no workspace is handled |
| 3 | Invite the team | ✅ | Lane A's Team Management, phases 1–3 |
| 4 | Say what you sell | ✅ | Product catalog — *Settings → Your business* |
| 5 | Say who buys it | ✅ | ICP editor, and now **ICP-01's list** |
| 6 | Say who decides | ✅ | Buying committee |
| 7 | Say what you are pushing | ✅ | Commercial focus |
| 8 | Name companies to watch | ✅ **and it is the cliff** | Target accounts. Publishes `target_accounts_changed`. **Nothing consumes it** (§1) |
| 9 | **Signora finds and watches them** | **✖** | The consumer exists and is unregistered. **This is where the product stops** |
| 10 | Companies resolve into entities | ◐ | `knowledge_graph` — never runs |
| 11 | Changes become observations | ◐ | `observation_engine` — never runs |
| 12 | Observations become business events | ◐ | `business_event_engine` — never runs |
| 13 | Business events become signals | ◐ | `signal_engine` — never runs |
| 14 | Signals become a buying score | ◐ | `buying_score_engine` — never runs |
| 15 | Scores become opportunities | ◐ | `opportunity_engine` — never runs |
| 16 | *"What should I work on?"* | ◐ | `/` — built, reviewed, **permanently empty** |
| 17 | *"Why this account?"* | ◐ | The brief, with evidence, validation, research, contributions |
| 18 | *"What happened?"* | ◐ | Timeline, mounted in `CX-03` |
| 19 | Record a decision | ◐ | `WorkflowActions`, `DecisionHistory` |
| 20 | Connect a CRM | ⚠ | M13 complete; **every system reads *Not available yet*** pending a HubSpot developer application |
| 21 | Be told something changed | ✖ | **M14a Notifications** — blocked on `04-modules.md` + [C-302](../LANE_COORDINATION.md) |
| 22 | See who a colleague is | ✖ | **[C-307](../LANE_COORDINATION.md)** — `Ownership` renders *Taken* |
| 23 | Manage your profile | ✖ | Blocked on the same tenancy ruling |
| 24 | Sign out | ✅ | |

---

## 3 · Time to first value

> **A customer reaches first value at step 9, and step 9 does not run.**

**Steps 1–8 are eight screens of declaration before Signora does anything.** Even with the pipeline running, that is a long walk — and the repository already knows it: [R6-05](39-product-review-findings.md) records that *nothing tells a new account what to do next*, and there is **no onboarding flow, no checklist, no guided first run.** [C-007](../LANE_COORDINATION.md) designed one and it is deliberately unscheduled.

**The shortest honest path to value is not to add onboarding. It is §1.** With the pipeline running, a customer who names three companies gets an attention list the next morning. Without it, no amount of onboarding polish reaches anything.

**Three of the eight declarations are not prerequisites and read as though they are.** Target accounts *"cites no product, so it needs no catalog"* — a customer could name companies first and describe their business later. **The screen orders them catalog → ICP → committee → focus → accounts, and only the first two are genuinely ordered.**

---

## 4 · Where two finished capabilities fail to meet

**The question the product owner asked — *"then what?"* — applied at every seam. Four answers are missing, and none is a new feature.**

| Seam | *Then what?* today |
|---|---|
| **Declare target accounts → discovery** | **Nothing.** §1 |
| **ICP declared → anything** | **Nothing consumes an ICP.** `commercial_profile/public/` publishes only `TargetAccountReader`. A customer describes their ideal buyer and no screen, score or search uses it. **ICP-01's identity/version split exists precisely so a consumer can cite one** — and there is no consumer |
| **Decision recorded → next account** | *"Recording a decision leaves you exactly where you were"* — **[R10-02](39-product-review-findings.md), open.** `AccountSequence` and `nextInSequence` are built |
| **Opportunity won → anything** | **Nothing.** No CRM write-back, no notification, no learning loop. M13 is inbound-only by design |

**The seam worth naming:** *"who buys this"* and *"which companies to watch"* are **two independent lists a customer maintains by hand**, and the product never uses the first to suggest the second. **That is discovery, and it is unbuilt** — recorded in [README](../../README.md) as an unowned capability with a stated trigger.

---

## 5 · What is missing, after checking that it is

**Every candidate was checked against the repository first, per the product owner's instruction. Six survived; four did not.**

| | Verdict |
|---|---|
| **Pipeline composition** (§1) | **Missing, and it is the only 🔴.** Not a feature — a composition root |
| **Onboarding / first-run guidance** | **Missing.** R6-05 and C-007. **Second priority, not first** — guidance toward a pipeline that does not run is worse than none |
| **Notifications** | **Missing**, blocked. M14a |
| **People have no names** | **Missing**, blocked. C-307 |
| **ICP has no consumer** | **Missing.** The largest unbuilt *connection* |
| **CRM write-back** | **Missing and correctly deferred.** M13 is inbound-only |
| ~~Search · filter · sort~~ | **Not missing yet.** With no accounts flowing, a filter over an empty list is speculative. **Trigger: the first workspace with more than a screenful** |
| ~~Bulk actions · exports · saved views~~ | **Not missing.** No evidence of a customer with the volume that makes them useful |
| ~~AI assistance in onboarding~~ | **Not missing — premature.** [ADR-0028](adr/0028-model-runtime-by-environment.md); and asking a model to invent an ICP is the top rung of the least-powerful-author rule |
| ~~Reporting / analytics~~ | **Not missing.** Nothing to report on until §1 |

---

## 6 · Recommended order, by customer impact

| # | Slice | Why first |
|---|---|---|
| **J1** | **Register the seven consumers in the deployed worker** | **Every ◐ in §2 becomes ✅ in one change.** Sixteen screens stop being empty. Gated by [C-012](../LANE_COORDINATION.md) — the RFC has been open since M3A, and **this document is the evidence for how much it costs** |
| **J2** | **A guided first run** | C-007, designed. **Only after J1** |
| **J3** | **An ICP consumer** | The largest unbuilt connection. Needs a decision about which module discovers companies |
| **J4** | **Decision → next account** | R10-02. `nextInSequence` exists; the transition does not. **Small, Lane A's** |
| **J5** | Notifications · profiles | Both blocked on rulings already raised |

---

## 6a · Who consumes an ICP — and the answer is almost nobody, directly

**The product owner asked for a dependency graph. Building it produced a finding that changes what "wire the ICP in" means.**

**Twelve candidate consumers were tested against one question: *does this module need the customer's description, or does it need to know whether a company matches it?***

| Candidate | Verdict | Why |
|---|---|---|
| **Company discovery** | ✅ **The primary consumer** — and **unbuilt**. Recorded in [README](../../README.md) as an unowned capability | An ICP *is* the search criteria. This is the one module that consumes the description itself |
| **AI Research** | ✅ **Consumes the description** | *"Research this company against who we sell to"* — the ICP is prompt context, and a description in a prompt is exactly what a description is for |
| **Search** | ✅ eventually | Same shape: criteria, not a verdict |
| **Buying Score** | ⚠️ **Consumes a match, never the ICP** | *"This company matches your ideal customer"* is a legitimate contribution to a score. **But that is a match result**, and computing it is not this module's |
| **Signal Engine** | ❌ **and it is the closest call** | Relevance is already customer-specific via `signal_profile`. **But *"who we sell to"* and *"what we find interesting"* are different questions**, and merging them would put an ICP inside a module whose output is deliberately globally traceable |
| **Provider Platform** | ❌ | It synchronizes **named subjects**. [ADR-0036](adr/0036-target-account-contract.md) fixed that boundary deliberately — discovery would *produce* subjects from an ICP, which is a different capability |
| **Knowledge Graph** | ❌ | Resolves identity. An ICP is not an identity |
| **Observation · Business Event** | ❌ **By rule** | Everything above the Signal Engine is *globally true*; an ICP is customer-specific. Consuming it there would make an observation depend on who is looking |
| **Opportunity Engine** | ❌ | Records human commitment |
| **Notifications** | ❌ | Notifies about events, not descriptions |
| **Timeline** | ❌ | Records what happened |
| **Workflows · agents** | — | Future, and they would consume a match |

> **The ICP's missing consumer is not a wiring gap. It is a missing capability with no owner: *matching*.**

**Both modules that would consume an ICP most valuably — discovery and matching — are unbuilt**, and matching is blocked by something already named: [C-002](../LANE_COORDINATION.md), the anticorruption layer between the customer's free-text *"mid-market fintech"* and Provider Normalization's canonical vocabulary. **Commercial Profile's own design records this**: it *"records a description; it never matches anybody against it"*, and matching *"is not built, is not this module's, and has no owner today."*

**So `J3 — an ICP consumer` in §6 is wrong as written**, and this review corrects itself: **the slice is not *"wire the ICP into the pipeline."*** It is *"decide who owns matching, and answer C-002."* Wiring an ICP into a scorer before matching exists would put free-text comparison inside a module that must stay globally traceable — the exact failure the boundary test in `commercial_profile` refuses at the syntax-tree level.

---

## 6b · The pipeline is internal; the customer's mental model is not

**The product owner's suggestion, tested against the code rather than agreed with.**

**The screens are already customer-intent driven, and the repository fixed this deliberately.** [R8-01](39-product-review-findings.md) — *"the navigation was the data model, not the workflow"* — is **fixed**, and D38 retired an Overview page in favour of *"which accounts should I work on today?"* **No screen is named after a pipeline stage.**

**The API is not.** `/accounts/{id}/validation`, `/accounts/{id}/score`, `/accounts/{id}/timeline` are stage names. A customer never asks for *"validation"*; they ask *"how confident are you?"*

**Where that costs something today, measured:** the account brief makes **five requests** — score, validation, narration, research, timeline — because the API is shaped by producer, and the customer is asking one question. Each is individually correct and cursor-paginated; together they are a screen assembling a pipeline.

**This already has a module, and it is not started.** *Revenue Intelligence Platform* is defined in [04-modules.md](04-modules.md) as the **composition/read module** — *"synchronous query when composing a workspace intelligence view"*. **The customer-intent read model is RIP's job**, and the pressure the product owner identified is the evidence for building it rather than for a new abstraction.

**Nothing should change today.** Five requests on one screen is not a defect at this scale, and collapsing them before RIP exists would put composition in whichever caller did it first.

---

## 6c · Time to first value, step by step

**Each of the eight declarations asked: *is this required before the customer receives value?***

| Step | Required first? | Evidence |
|---|---|---|
| Sign up · verify · organization | **Yes** | Tenancy is the boundary everything else hangs off |
| **Name companies to watch** | **Yes — and it should be first, not eighth** | It *"cites no product, so it needs no catalog"*. **It is the only declaration the pipeline consumes** |
| Product catalog | **No** | Required by ICP and committee, not by discovery or watching |
| ICP | **No** | Nothing consumes it (§6a). **Today it is stored information, not operational intelligence** |
| Buying committee | **No** | No consumer |
| Commercial focus | **No** | No consumer |

> **A customer could reach first value after three steps: sign up, create an organization, name three companies.** The other five are ordered as prerequisites and are not — they are inputs to capabilities that do not exist yet.

**The screen presents them in one column in a fixed order**, which reads as a required sequence. **That is a presentation choice, not a domain constraint**, and it is the cheapest available improvement to time-to-first-value: **reorder, and let the rest be discovered later.** It needs no backend change and no new capability.

**What it does not fix** is that step 9 does not run (§1). **Reordering eight declarations in front of a pipeline that never executes moves a customer to disappointment faster.** Sequence matters: §1 first.

---

## 6d · The execution model, challenged before anybody wires it

**Fourteen questions asked of today's architecture. It answers most of them already, and two are genuinely open.**

| | Today |
|---|---|
| **Retries · dead-lettering** | ✅ Built and proven — ARQ, `dead_letter_event` with the full envelope, `replayed_at` rather than deletion |
| **Replayable** | ✅ By construction. Every consumer is idempotent on `event_id`; Timeline derives its identity from it |
| **Observable** | ✅ `correlation_id` end to end, OpenTelemetry, structured logs |
| **Resumable** | ✅ The outbox is the durable record; a worker restart loses nothing |
| **Prioritized** | ✅ Pools partition by cost and latency, declared since M1.1 |
| **Conditional execution** | ✅ A consumer that finds nothing to do returns and marks done |
| **Cancellable** | ⚠️ **Open.** Nothing stops an in-flight run. No customer has asked, and a provider spend cap would be the trigger |
| **Customer-visible progress** | ⚠️ **Open, and the more likely of the two.** *"Signora is looking at your companies"* has no representation. **`research_request_state` is the shape** — a request with appended progress — and it exists for exactly one capability |
| **Scheduled · partial reruns** | ❌ Not built. **`provider_watermark` is the mechanism** and it is per-subject since `0029` |
| **Event-sourced · workflow-driven** | ❌ **And should stay that way.** The outbox is a delivery mechanism, not a source of truth; every stage's output is a durable row. Making the pipeline workflow-driven would add an orchestrator above modules designed to be independently extractable |

> **Today's architecture supports thirteen of fourteen without redesign.** The one genuinely missing thing is **customer-visible progress**, and it is a read model rather than an execution change — which is worth knowing before §1 lands, because the first thing a customer will ask after *"nothing happened"* stops being true is *"is it working yet?"*

---

## 7 · Future pressure

**Five years, and the pressure is not where the roadmap assumes.**

| | |
|---|---|
| **Composition** | **The repository has no test that asserts what the deployed application does.** [B-301](../BUGS.md) and §1 are the same defect at different scales, and [C-301](../LANE_COORDINATION.md) is the fix. **Every future module can ship this** |
| **Onboarding** | Eight declarations do not scale to enterprise, where different people own different declarations. **Today's model assumes one person fills in everything** |
| **Discovery** | The product asks a customer to name companies. **At enterprise scale nobody types a target list** — it comes from a CRM, a territory, or a model over the ICP |
| **Identity** | Two capabilities already block on per-person data (C-302, C-307). **Every collaborative feature after them will too** |
| **AI** | The daily surface is deterministic by rule and AI lives on the brief. **The first request to put a generated sentence on a row is the pressure**, and the rule is worth defending |

---

## 8 · What this review changed, and what it did not

**Nothing was implemented.** One thing was **not** built as a result: no journey gap here needs a new bounded context. **Every ✖ in §2 is a missing connection, a missing composition, or an existing blocker** — which is the outcome the product owner predicted and the reason this review was worth running before more building.

**The honest summary in one line:** *Signora is a well-built product whose stages are not connected in the environment a customer would use.*


---

## 9 · Running the product, rather than reading it — 2026-08-03

**The Complete Product Experience Audit began by looking for what to build, and found that the hardest part already exists.**

### The reuse finding, and it is emphatic

**Provider simulators and realistic customer organizations are built and in use.** `make demo` brings up the stack, migrates, creates sign-in accounts through Better Auth's own routes, and seeds **twelve accounts through the real pipeline** — provider simulation → ingestion → normalization → knowledge graph → observations → business events → signals → buying scores → opportunities.

> **No branch anywhere knows it is a playground.** The only differences from the pipeline suite are which scenario file is named and where its timeline is anchored.

**Building new simulators would have duplicated `signora_platform/simulation` — the Provider Simulation Framework, shipped at M2.0 — and the Playground around it.** The audit's first act was to check, and the check is the deliverable: **do not build them.**

### What running it proved, and what it did not

**Seeded into Lane B's own database rather than the shared review stack**, since 3000/8000 belong to human product review:

```
raw_provider_record  14004      signal         6311
claim                53847      buying_score   4090
entity                8652      opportunity    3956
observation          18745      timeline_entry   156   ← the finding
```

**The pipeline works.** Twelve accounts, twelve qualified opportunities, four re-scored because their evidence had aged — **produced by band arithmetic from scenario dates, not declared.**

**Two composition gaps, and they are not the same gap.**

| | |
|---|---|
| **The deployed worker** | Seven consumers unregistered (§1). **A customer's product does nothing** |
| **The Playground** | Timeline never composed — **[B-302](../BUGS.md)**. *"What has happened"* is empty on all twelve accounts, in the one environment the product owner reviews the product in |

**The second was invisible to §1's analysis** and only appeared by running the product. `tests/pipeline.py` mentions Timeline exactly once, in a docstring.

### What this audit could not do, stated rather than implied

**A screen-by-screen visual audit needs a browser and a human**, and the review stack is not this lane's to occupy. **The twenty-seven deliverables that depend on seeing rendered screens — micro-interactions, spacing, hover and focus behaviour, dark mode, responsive breakpoints, animation, premium feel — are not in this document, and claiming them from source would be exactly the assumption this repository keeps catching.**

**What is here is what running the product actually evidenced:** the pipeline produces realistic output, the simulators exist, and two composition roots are each missing the same module.

> **The audit's most useful output is a subtraction.** It was scoped to build simulators and populate organizations; both already existed, and the effort that would have gone into rebuilding them produced [B-302](../BUGS.md) instead.
