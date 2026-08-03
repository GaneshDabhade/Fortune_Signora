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
