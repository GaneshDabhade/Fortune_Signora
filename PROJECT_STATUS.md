# Signora — Project Status

> **The canonical entry point for this repository.** If you read one document, read this one.
> **Last verified against the repository: 2026-07-31**, at `HEAD` `a565077`. Test, coverage and contract figures are verified against a local run; the certification manifest is re-cut at milestone close (ADR-0032).
>
> This is an **executive dashboard**, not a progress log. It answers: *where are we · what was completed · what changed architecturally · what is deferred · what's next · are we on track.* Dated history lives in the appendices and is never rewritten to match the present.

---

## 1 · Repository overview

**Signora** is an AI-powered Revenue Intelligence Platform: a modular monolith (Python 3.13 · FastAPI · PostgreSQL 17 · SQLAlchemy 2.x async) that turns provider payloads into commercial conclusions a seller can act on — and defend.

| | |
|---|---|
| **Current phase** | **Product implementation** — the pipeline is built; the surface is being exposed |
| **Last completed milestone** | **M10 — AI Research Engine**, closed 2026-07-31 |
| **Current milestone** | **M12.2 — the account brief** *(resumed after M12.1.5; Decision Package deferred until `reasoning@1` is released — see §10)* |
| **Latest commit** | `2fdc40b` — *M12.2 — the brief learns what changed* |
| **Latest certification** | [`d954c930`](certification/reports/d954c930319a.md) — **CERTIFIED**, 2026-07-31 *(predates M12.2; re-cut at milestone close)* |
| **Branch** | `main`, tree clean, pushed |
| **Verification** | **Local only** ([ADR-0027](docs/architecture/adr/0027-local-first-development.md)). There is no remote gate; a `git push` stores the repository and triggers nothing |
| **Overall completion** | **~60%** by engineering effort (~187 of ~261–339 ew) — M10 (12–16 ew) closed, M9.5 (~3 ew) inserted and **not** closed, M12.1 in progress |
| **Projected to GA** | ~1.3–1.9 years at 3 engineers · ~2.0–2.8 at 2 · ~3.9–5.8 at 1 (80% capacity) |

**What works end to end today:** a simulated provider payload is ingested, normalised into claims, resolved into entities, diffed into observations, detected as business events, interpreted as workspace-specific signals, aggregated into a buying score, qualified into an opportunity a human commits to, narrated as a grounded explanation, reasoned into a **Decision Package**, and **researched into deterministic findings with a written brief** — all stored immutably, announced on the outbox, with complete provenance.

**What a customer can now do:** sign in, choose a workspace, and open **two business screens** — the attention list (*"which accounts should I work on today"*) and the account brief (*"why this one"*), the second of which shows a score **with the arithmetic that produced it**, line by line, reproducible with a division. That is the point at which Signora stops being rankable and starts being arguable.

**🔴 What is currently broken in production, and must not be hidden:** **`reasoning@1` has no released model.** M9.5 changed the rendering protocol, which withdrew every protocol-1 release by derivation; `explanation_narration@1` re-earned its release, and `reasoning@1` did not — `granite3.3:2b` refuses under protocol 2 and `llama3.1:8b` remains UNMEASURABLE on this hardware. **The Decision Package stage would refuse at runtime.** Tests and smoke pass because they supply registry doubles. See §7.

---

## 2 · Milestone progress

Execution order is authoritative; milestone IDs are stable labels and deliberately **not** renumbered ([roadmap §5b](IMPLEMENTATION_ROADMAP.md#5b-execution-sequence)).

| # | Milestone | Purpose | Status | Closed |
|---|---|---|---|---|
| — | M0 | Secure multi-tenant foundation | ✅ Complete | 2026-07-28 |
| — | M1.1 | Platform runtime — event bus, workers | ✅ Complete | 2026-07-28 |
| — | M1.2 | Authentication boundary | ✅ Complete | 2026-07-28 |
| — | M1.3A | Deployment foundation | ✅ Complete | 2026-07-28 |
| — | M1.4 | Platform smoke test | ✅ Complete | 2026-07-28 |
| — | M1.5 | Frontend foundation | ✅ Complete | 2026-07-28 |
| — | M2.0 | Provider Simulation Framework | ✅ Complete | 2026-07-29 |
| — | M2.1 | Provider Platform | ✅ Complete | 2026-07-29 |
| — | M2.2 | Provider Normalization | ✅ Complete | 2026-07-29 |
| — | M3A | Knowledge Graph | ✅ Complete | 2026-07-29 |
| — | M3B | Observation Engine | ✅ Complete | 2026-07-29 |
| — | M4 | Business Event Engine | ✅ Complete | 2026-07-29 |
| — | M5A | Signal Engine | ✅ Complete | 2026-07-29 |
| — | M5B | Buying Score Engine | ✅ Complete | 2026-07-29 |
| — | M6 | Opportunity Engine — **first sellable moment** | ✅ Complete | 2026-07-29 |
| — | M8 | AI Platform — abstraction, prompts, eval harness | ✅ Complete | 2026-07-30 |
| — | **M9** | **AI Reasoning Engine — Decision Package** | ✅ **Complete** | **2026-07-31** |
| — | **M10** | **AI Research Engine** *(Internal Research)* | ✅ **Complete** | **2026-07-31** |
| — | **M9.5** | **Evidence Citation Protocol + Certification** *(ADR-0031/0032, unplanned)* | 🟠 **Open — Step F incomplete** | — |
| — | **M12.1** | **Account attention list — first customer surface** | ✅ **Complete** | **2026-07-31** |
| — | **M12.1.5** | **Playground v2 — a demo environment worth reviewing against** *(inserted)* | ✅ **Complete** | **2026-07-31** |
| 1 | **M12.2** | Identity ✅ · score ✅ · commitment ✅ · **narration ✅** · package 🚫 | 🔵 **In progress** | — |
| 3 | M12.3 | Evidence resolution and workflow actions | ⏳ Queued | — |
| 4 | M12.4 | Research on demand | ⏳ Queued | — |
| — | M11 | Recommendation Engine | 🟣 **Deferred 2026-07-31** — *not cancelled*; resumes on a product trigger, see §10 | — |
| 5 | M7 | Timeline | ⏳ Queued | — |
| 6 | M13 | Integrations — CRM, comms, calendar | ⏳ Queued | — |
| 7 | M14a | Notifications | ⏳ Queued | — |
| 8 | M14b | Billing, analytics, feature flags | ⏳ Queued | — |
| 9 | M14.5 | Cloud Infrastructure *(deferred from M1.3B)* | ⏳ Queued | — |
| 10 | M15 | GA readiness — load, SOC 2, PII, spend governance | ⏳ Queued | — |
| — | 🎯 | **General Availability** | | |

**Two foundations are frozen** and consumed rather than modified: `signora_platform/` (§20a) and the frontend foundation (§20c). **`ai_platform/` is frozen as of M10's close (2026-07-31)** — deliberately not after M9, because a port that had only served a single-call workload had never been asked for tool use or resumability ([28-ai-platform.md](docs/architecture/28-ai-platform.md), Condition 2).

---

## 3 · Task progress

### ✅ M9 — complete, T122–T130

| Task | Delivered |
|---|---|
| T122 | Module scaffold · graph node · four import-linter contracts |
| T123 | `ReasonedOutput` — the model's three fields, premise breadth as a **type invariant** |
| T124 | `SupportBasis` / `SupportLevel` — derived support introducing **no new threshold** |
| T125 | `TemporalExplanation` — why now · why not earlier · what changed · freshness |
| T126 | Signal catalog extension — `limitations`, `suggested_validation` |
| T127 | `DecisionPackage` + `Reason` — fifteen parts, `answers()` as executable acceptance |
| T128 | `reasoning@1` · rubric extension · **release earned** |
| T129 | Migration `0017` — `ai_reasoning`, forced RLS, no `UPDATE` grant |
| T130 | Model · repository · context adapter · composition root · event · smoke stage 14j |

### ✅ M10 — complete, T131–T138 · **Internal Research** *(ruled 2026-07-31)*

| Task | Delivered |
|---|---|
| T131 | Module scaffold · graph node · four import-linter contracts (25 → 29) · six invariants |
| T132 | `EpistemicOrigin` · `ResearchTask` · `ResearchFinding` · `ResearchSynthesis` — three origins, three identity disciplines |
| T133 | Migration `0018` — **three tables because there are three data categories**; forced RLS, no `UPDATE` grant, tenancy registration |
| T134 | Internal retrieval — `ResearchFactSource` over `opportunity_engine.public`; business events and dissent, the two things M8's assembler omits |
| T135 | The planner — a closed derivation catalog, steps that cannot carry a conclusion, and **stopping as a legal answer** |
| T136 | The orchestrator — three deterministic derivations, type↔rule pairing checked at import, and **no counter, no timeout** *(see R-09 below)* |
| T137 | `research_planning@1` — prompt, M10's own golden dataset, evaluation entry point, and **release EARNED** on `llama3.1:8b` after eight consecutive passing runs |
| T138 | The lifecycle closed — synthesis, persistence, `ai_research.completed`, composition root, smoke stage 14k. **`research_synthesis@1` REFUSED**, and R-09 answered by measurement |

**`research_synthesis@1`'s refusal is what forced M9.5.** It was the third prompt blocked by the citation protocol defect, and the milestone stopped rather than tuning around it.

**The scope ruling landed before T132** and narrowed the milestone materially: research explores, compares and synthesises knowledge Signora already owns, and reaches no external source. See [33-ai-research-engine-scope.md](docs/architecture/33-ai-research-engine-scope.md) for the analysis and the ruling it records.

### 🟠 M9.5 — Evidence Citation Protocol *(ADR-0031, unplanned, **not closed**)*

| Step | Delivered |
|---|---|
| A | Three refusals recorded — the ADR's evidence base existed only as prose until this step |
| B | The **Prompt Rendering Protocol** made a first-class concept; every evaluation records it, every release is bound to it |
| C | Protocol **2** — the citation presented as a copyable unit; three releases withdrew themselves by derivation |
| D | `research_planning@2` and `research_synthesis@2` — the workaround deleted, both **RELEASED** |
| **F** | 🟠 **Incomplete.** `explanation_narration@1` re-released; **`reasoning@1` refused on every available model** |

### ✅ M12.1 — complete

| Step | Delivered |
|---|---|
| 1–2 | `attention_list` — the first workspace-wide read path; plural buying-score read; identity-keyed cursor |
| 3 | `GET /workspaces/{id}/accounts` — router, schemas, authorization, 20 full-stack tests |
| 5 | `/opportunities` — the first business screen, composed from the frozen design system |
| 6 | ⏳ Performance review — deferred to M12.3, where the row gains an affordance worth measuring |

### 🔵 M12.2 — Account Identity and the score breakdown shipped

| Delivered | |
|---|---|
| **`AccountIdentity`** | A read model, not a string. `Entity` stores no name — naming an account is the truth-resolution the graph declined to make, so it happens once, at read time, in `select_name` |
| **`GET …/account-identities`** | Batched; a page costs one request. Returns the name **and** whether sources agreed |
| **`EntityName`** | The canonical way Signora renders a company. Agreement is invisible; **disputed names are marked** |
| **`GET …/accounts/{id}/score`** | The score **with its full ledger** — every business event that contributed, what each added, and why the ones that added nothing added nothing |
| **`/opportunities/[accountId]`** | The account brief. `68 of 120 points` beside the number: a customer checks the score with a division rather than trusting it |
| **`GET …/accounts/{id}/opportunity`** | What Signora committed to, and what has happened since — **the movement the list structurally cannot show**, because the list only knows about today |
| **`GET …/accounts/{id}/narration`** | The grounded explanation, statement by statement, each with the evidence it rests on and the model and prompt that wrote it |
| **Tests** | 20 resolver · 7 identity endpoint · 14 score endpoint · 13 commitment endpoint · 44 component · 3 Security Invariants |
| ⏳ **Next** | **F-10 first** — a customer-visible false statistic, found by the narration slice. Then F-11, which needs a ruling before it can be fixed |
| 🚫 **Deferred** | **The Decision Package panel.** `reasoning@1` has no released model; building UI around an unavailable capability would ship a panel that cannot be filled (§7) |

### 🔵 M12.1.5 — Playground v2, inserted 2026-07-31

A demo environment worth reviewing a product against. Requested by the product owner after M12.2's brief showed that **the dataset, not the architecture, had become the constraint** (D17).

| Delivered | |
|---|---|
| **`playground@2`** | Twelve recognisable companies, twelve **invented** business situations, spanning five months. `playground@1` is superseded, retained and unedited |
| **The epoch belongs to the runner** | A scenario declares offsets and no date; the seeder anchors it relative to today. Asserted by a test, because a date baked into the narrative is what made v1 demonstrate seven-month-old evidence |
| **Two scoring passes** | Opportunities qualify against scores as they stood five weeks ago; the scheduled sweep last ran three days ago. **Current, cooling and stale all occur and none is declared** |
| **Three unreachable capabilities fixed** | See §5 — each was complete in every layer except the one that had to supply the evidence |
| **Product review** | Recorded as D19 and D20 in [38-product-design-principles.md](docs/architecture/38-product-design-principles.md) |

### ⏳ Next tasks

| Task | Scope |
|---|---|
| M12.2 | **Narration** — the brief's missing narrative half, and the only AI capability with a current release |
| M12.2 | The Decision Package panel, **on the trigger `reasoning@1` earns a release** and not before |
| M12.3 | Evidence resolution, stage transitions, assignment — and the list's missing hierarchy (D20) |

**Deterministic-first ordering, unchanged from M8 and M9:** storage before retrieval, retrieval before orchestration, generation and evaluation last. **Embeddings, pgvector, external retrieval and provider re-query are deferred**, each with a stated trigger.

---

### The standing rule for every M12.x slice

> **No frontend screen is complete until a human has reviewed it in the demo environment.**
>
> **And every user-visible feature gets a recorded product review before the next one starts** — as the five people who would use it and as the designers whose products set the bar. Findings land in [39-product-review-findings.md](docs/architecture/39-product-review-findings.md) with a priority and a milestone, and are implemented immediately **only** when they fix a correctness bug, materially reduce cognitive load, or are essential to the current milestone.

Set by the product owner on 2026-08-01. Gates prove a screen is correct; only a person opening it can say whether it is *persuasive*, and every finding in [38-product-design-principles.md](docs/architecture/38-product-design-principles.md) from D9 onward came from looking rather than from a test.

---

## 4 · Repository health

> **Not transcribed. Cited.** Every figure below comes from
> [`certification/manifest.json`](certification/manifest.json) — written by
> `make certify`, never by hand (ADR-0032). A number in this table that nobody
> measured is the defect the certification record exists to remove, so this
> section names its evidence and stops.

**Latest certification — [`d954c930`](certification/reports/d954c930319a.md) · 2026-07-31 · CERTIFIED**

| Gate | Recorded |
|---|---|
| **pytest** | 1861 passed |
| **coverage** | 95.80% *(floor 95%)* |
| **Security Invariants** | 321, each proven to fail when its guarantee is removed |
| **import-linter** | 29 kept, 0 broken |
| **MyPy** | strict, clean over 455 files |
| **`make smoke`** | 24 stages in 151s, fresh images, clean teardown |
| **Scenario — `baseline@1` research lifecycle** | 149 assertions |

**Conditions the certification is bound to:** rendering protocol **v2** · migration head **`0018`** · scenario set `e2bfe02e` · `research_planning@2` and `research_synthesis@2` released for `llama3.1:8b`.

> **This certification predates the M9.5 Step F measurements.** Re-running `make certify` now would record the same gates and the same verdict — certification does not read prompt *health*, only the releases the pipeline requests, and M10's two are current. That `reasoning@1` has no release is a finding the certification record does not and should not carry; it is stated in §1 and §7 instead. **A certification is evidence that the gates passed, never that the product is correct.**

**A certification expires by derivation, not by decision.** Change the rendering protocol, re-release a prompt, add a migration or edit a scenario, and the recorded run stops describing the repository — `is_certified` reads false and the report says *awaiting re-certification*. Nothing is edited, and nothing can be marked certified by hand: `satisfied` and `is_certified` are derived, exactly as `passed` and `earns_release` are for prompts.

| Indicator | Value | Target |
|---|---|---|
| **Frontend tests** | **101 passing**, 0 failing, 0 skipped | 0 skipped |
| **Migrations** | `0001`–`0018`, additive and reversible — `0018` proven by an applied downgrade/upgrade cycle | reversible |
| **Architecture drift** | **0** — no ratified ADR reversed | trending to 0 |
| **Open production bugs** | **0** | 0 |

*Frontend tests and migration reversibility are not yet certification gates — they are verified per milestone and remain transcribed here until `make certify` measures them.*

**Every gate runs locally.** `make certify` runs them in one pass and records the result; each remains individually runnable. A gate moving from CI to local did not make it optional — it made the local run the only run, and therefore the one that decides.

**Caveat worth restating:** these numbers describe a system with zero production traffic. They are evidence of discipline, not of field reliability — which is why every certification report ends with that sentence.

---

## 5 · Released AI prompts

A prompt is usable **exactly where a measurement says it is** — per `(model, dataset)`, and since M9.5 per **rendering protocol** too. Release is *derived* from the recorded evaluation, never declared.

| Prompt | Model | Protocol | Grounding / schema failures | Coverage | State |
|---|---|---|---|---|---|
| `explanation_narration@1` | `llama3.1:8b` | **2** | 0 / 0 | 1.00 | ✅ **Released** |
| `research_planning@2` | `llama3.1:8b` | **2** | 0 / 0 | 1.00 | ✅ **Released** |
| `research_synthesis@2` | `llama3.1:8b` | **2** | 0 / 0 | 1.00 | ✅ **Released** |
| `reasoning@1` | `granite3.3:2b` | 2 | **2** / 0 | 0.00 | 🔴 **REFUSED** |
| `reasoning@1` | `llama3.1:8b` | 2 | — | — | ⚪ **UNMEASURABLE** — times out on this hardware |
| `research_planning@1` · `research_synthesis@1` | — | 1 | — | — | ⚫ Superseded by `@2`; measurements retained |

**Every refusal above is in a manifest**, not only in prose — which is M9.5 Step A's whole purpose and what makes this table checkable.

**🔴 `reasoning@1` is the open blocker.** M9's Decision Package cannot be produced in production until it earns a release. Nothing has been tuned to make it pass: not the prompt, the delimiter, the schema, the timeout or the rubric. See the correction appended to [ADR-0031](docs/architecture/adr/0031-evidence-citation-protocol.md).

---

## 6 · Current AI architecture

A dashboard, not a specification. Authoritative detail: [28-ai-platform.md](docs/architecture/28-ai-platform.md) · [29-ai-reasoning-engine.md](docs/architecture/29-ai-reasoning-engine.md) · [ADR-0030](docs/architecture/adr/0030-the-decision-package.md).

| Component | State | What it guarantees |
|---|---|---|
| **AI Platform** (`modules/ai_platform`) | ✅ Built, **freezes after M10** | The one path to a model. Domain and application know nothing of the pipeline; the single reach into `opportunity_engine.public` happens in `infrastructure/` behind a Protocol |
| **Provider Registry** | ✅ Built, provider-neutral | Resolves **by model** — `for_model(model)`, with **no vendor-keyed lookup**. Business code that cannot *name* a vendor cannot branch on one. Ollama + Anthropic registered; a new vendor is an adapter registration |
| **Prompt Registry** | ✅ Built, per-directory | Each module owns its prompts. A version is immutable and fingerprinted; the loader refuses to start if the file disagrees with its fingerprint |
| **Evaluation** | ✅ Built, offline-refusing | The **only** command requiring a real model. Names no vendor in executable code (enforced by Security Invariant). A run that cannot execute produces **no verdict** rather than a partial average |
| **Grounding** | ✅ Built, unchanged since M8 | Five `ViolationKind`s. Validates that every citation resolves **inside a closed evidence set** — it does **not** validate that a fact in the set is true |
| **Decision Package** (M9) | ✅ Built | Fifteen parts; **the model authors three**. Eleven customer questions answered, eight without a model having spoken |
| **AI Reasoning Engine** | ✅ Built | Structured, single-call. Exactly one inference per package, enforced by test |
| **AI Research Engine** | 🔵 **In progress** — M10 | Agentic, multi-step, minutes not seconds — over **Signora's own ledger**. Ruled **Internal Research** 2026-07-31: no external retrieval, and embeddings and pgvector deferred, because the Knowledge Graph stores typed edges and enum kinds rather than a corpus to embed |

**The organising principle**, ratified 2026-07-30:

> **Every field has the least powerful author capable of producing it correctly.** The database owns timestamps. Code owns derived facts. Domain experts own static knowledge. AI owns inference.

Its practical consequence: because twelve of fifteen parts need no model, **a failure to reach a model degrades a Decision Package rather than emptying it.**

---

## 7 · Active architectural findings

Only open items. Closed findings live in the milestone records (Appendix A) and the change log (Appendix B).

| ID | Finding | Severity | Owner milestone |
|---|---|---|---|
| **[ADR-0031](docs/architecture/adr/0031-evidence-citation-protocol.md)** | **Protocol 2 shipped, and did not remove over-copying.** The renderer and parser no longer disagree — the citation is presented exactly as `EvidenceRef.parse` accepts it, and no prompt instructs a transformation. But `granite3.3:2b` now copies the token **plus the em dash plus the summary**: protocol 1 *closed* the citation with a bracket, protocol 2 opens it at the line start and never terminates it. **`reasoning@1` therefore has no released model**, and M9's Decision Package cannot be produced in production. A protocol 3 that terminates the citation is the obvious hypothesis and belongs to a ratified amendment, not to the session that found this. *(Historical statement of the original defect retained in the ADR.)* | 🔴 **High** | **M9.5, open** | `render.py` emits `[token]`; `EvidenceRef.parse` accepts only `token`; the prompt says *"cite by their exact reference strings"*. Three of five models were REFUSED for **obeying literally**, across two independent model families. Passing since M8 on one model's bracket-stripping habit. **T138 produced its clearest instance yet**: `research_synthesis@1` was REFUSED because the model stripped the `research_finding:` prefix on one case and not the other — same prompt, same model, same run. **PROPOSED, deliberately unimplemented** — an M8 defect whose fix invalidates every released prompt, now three | 🔴 **High** | M8 / M9.5 |
| **F-1** | **One `ollama_model` setting versus several certified prompts.** ⚪ **Dormant rather than resolved.** Three of the four live prompts are now certified for `llama3.1:8b` alone, so one configuration currently serves every *released* path. It returns the moment `reasoning@1` earns a release on a different model — which is the likely outcome, since `llama3.1:8b` cannot measure it at all on this hardware | 🟠 **Medium** *(was High)* | M9.5 |
| **F-2** | **The Evidence Set question.** *(Narrowed by [32](docs/architecture/32-knowledge-ontology.md) and [34](docs/architecture/34-knowledge-contract.md), then **downgraded by the Internal Research ruling**.)* The immediate exposure is closed by design: a `ResearchSynthesis` has **no address**, so no consumer can cite model-authored prose even deliberately, and `ResearchFinding` is DERIVED with `EvidenceRef.kind = research_finding`. What remains open is the *deferred* question — **may an ATTESTED external claim be cited?** — which arrives with external retrieval and not before | 🟠 **Medium** *(was High)* | Deferred with external retrieval |
| **F-8** | **Three declared capabilities had no possible input, found by building a demo dataset (M12.1.5).** Only Apollo claimed `LEGAL_NAME`, so the naming resolver's `AGREED` and `DISPUTED` states — which M12.2 built the product to display — could never occur. Neither Crunchbase nor CoreSignal offered a domain, so a registry could reach an existing company only by naming it *identically*, and **every workforce fact resolved to a nameless entity of CoreSignal's own**: the account a seller could see and the account the hiring evidence described were two different rows. Crunchbase declared `acquisitions` in `known_fields` since M2.2 and never translated them, leaving `acquisition_announced`, `consolidation_underway` and its scoring weight dead at the source. **All three are fixed**; the finding kept open is the *class* — every one passed the tests it had, and none could run | 🟠 Medium | **Fixed M12.1.5; class unassigned** |
| **F-10** | **The pipeline computed *"grew headcount 3678%"*, and every layer faithfully passed it on.** `_HeadcountRule` pools `EMPLOYEE_COUNT` and `OPEN_ROLES` into one series, so a ratio is taken from an open-roles baseline of 900 to an employee count of 34,000 — then labelled `employee_count`. The module's docstring guards the *provider* axis (*"nothing can combine them into a synthetic truth"*) and not the attribute axis. **Grounding could not catch it: the figure is in the evidence, and the model invented nothing.** Every component satisfied its own contract while a false statistic crossed the whole system. Present since M4; invisible to every gate because `baseline@1` never gave one entity both measures in one window, and **twelve varied accounts found it on the first run**. *Fix:* evaluate per attribute rather than pooled | 🔴 **High** | **Business Event Engine — next slice** |
| **F-11** | **A zero-padded figure can never ground its unpadded form.** `_normalise` folds thousands separators and trailing decimal zeros, not leading ones — so evidence carrying `2026-08-01` yields `08`/`01` while a model writing *"August 1, 2026"* yields `1`, and the statement is refused. Correct by the letter of the check, wrong by its purpose; any date in the first nine days of a month fails. **Initially misdiagnosed as a golden-set variety problem** — the success rate went from 2/12 to 10/12 on a *date* change, not a prompt change. Grounding refused rather than admitted, which is the right direction to be wrong in. *Fix:* `lstrip("0")` in `_normalise`; **not applied** — `ai_platform/` is frozen and this loosens a guarantee, which is the product owner's call | 🟠 Medium | **AI Platform — needs a ruling** |
| **F-3** | Signal catalog `limitations` / `suggested_validation` are **engineering-authored pending domain review** | 🟠 Medium | Unassigned |
| **F-5** | `PublishableEvent` Protocol vs frozen domain events — requires a `type: ignore` at every publish site | 🟢 Low | Unassigned |
| **F-6** | **Nine `CHECK` constraints cannot reject what they were written to reject.** `array_length('{}', 1)` returns NULL, and a `CHECK` fails only on FALSE — so `array_length(x, 1) >= 1` accepts the empty array. Proven end to end: a `signal` citing **no** business events inserts successfully. Affects `observation`, `business_event`, `signal`, `buying_score`, `ai_narration`, `ai_reasoning` across six milestones. **No production defect** — every write path goes through a domain type that refuses the empty case — but nine comments claim a guarantee that does not hold. Repaired only in migration `0018`, which found it. See [36](docs/architecture/36-empty-array-checks.md) | 🟠 Medium | `T-CK1`, unscheduled |
| **F-7** | **Four `uuid5` namespaces and most derivation inputs survive mutation.** Documentation says *"never change it"*; nothing enforces it. See [35](docs/architecture/35-deterministic-identity.md) | 🟠 Medium | `T-ID1` / `T-ID2`, unscheduled |

**Resolved and recorded here because the dashboard previously claimed otherwise:** the cross-workspace read path on `outbox_event` is **closed**. Migration `0006` revokes all from `signora_app` and grants `INSERT` only; the relay identity holds `SELECT`. This document described it as "raised rather than applied" until 2026-07-31 — a claim the repository had already falsified.

---

## 8 · Known risks

Full register with mitigations and owners: [16-architecture-risks.md](docs/architecture/16-architecture-risks.md).

### 🔴 High

| ID | Risk | Note |
|---|---|---|
| R-01 | **AI vendor cost exposure without budget governance** | M8 made cost *measurable*; nothing governs it. The register says explicitly: define budgets **before AI Research Engine is enabled broadly.** M10 is the caller that makes this real |
| R-04 | PII classification / retention undefined | **Escalated to Legal.** Long lead time |
| R-05 | AI prompt data-classification policy undefined | **Escalated to Legal.** **M10 does not widen it** — under the Internal Research ruling, egress stays model-vendor-only, identical in kind to M8 and M9 today. *This row previously said research reaches public sources; that was the roadmap's assumption, not the ruling* |
| ADR-0031 | Citation protocol inconsistency | §7. Grows more expensive with every prompt released |

### 🟠 Medium

| ID | Risk | Note |
|---|---|---|
| R-09 | **AI Research timeout value undefined** | **Both halves now measured (T138).** A complete research task is **two model calls and nothing else of consequence**: planning **32.8 s** median (48.3 s cold), synthesis **20.8 s** median, derivations in microseconds — so **~54 s steady-state and ~70 s cold** end to end on this hardware, for a 2-fact account. Token cost is ~890 in / ~200 out for planning and ~760 in / ~125 out for synthesis; retries were 0 across nine measured calls. **The shape is the finding: the cost is two calls, not *N*** — the plan cannot name a derivation twice, so it is bounded by the catalog. The `ai_research` queue budget of 1800 s is ~26× the measured cold task. **Still not converted into a threshold**: this is a local 8 B model on 4 GiB of VRAM against the smallest realistic account, and production runs hosted models (ADR-0028). What is now known is the *shape*; the number belongs to the first hosted measurement |
| R-10 | AI output quality regression | Substantially mitigated: golden sets, rubrics, `ai_inference`, two evaluated prompts. **Not** closed — no human-rated sample yet |
| **New** | **Two new capability surfaces in M10** — agentic loop and *internal* tool use. Was four; embeddings and pgvector were deferred by the Internal Research ruling. M8 flagged tool use as *"carrying its own security surface deserving its own review"*, and internal tools reduce that surface without removing it |
| **New** | **Fixture-shaped coverage.** Six M9 mutations survived because one seeded scenario cannot vary contested scores, shared events or shared caveats. Every future module inherits that fixture | |

### 🟢 Low

JWT key rotation requires a deploy · token revocation bounded by a 15-min TTL · Casbin policy is coarse RBAC · no API versioning scheme (deliberate, with one first-party client) · `reasoning@1` coverage margin 0.667 against a 0.66 floor — an **observation**, explicitly not a reason to modify the prompt.

---

## 9 · Recent milestone summary — M10, closed 2026-07-31

| | |
|---|---|
| **Delivered** | T131–T138. Retrieval over `opportunity_engine.public` · a closed derivation catalog · three deterministic derivations · a planner that chooses work and cannot conclude · synthesis grounded against *findings* rather than facts · migration `0018`'s three tables · `ai_research.completed` · smoke stage 14k |
| **Architectural outcome** | **Every citable thing M10 produces is deterministic.** The model chooses which comparisons to run and writes the brief; neither produces a fact anyone may cite. `ResearchSynthesis` has no address, so narration structurally cannot become evidence. `ai_platform` is frozen on this evidence — a port that has now served an agentic, resumable workload |
| **Major findings** | The **Internal Research ruling** narrowed the milestone before T132 and removed every item with no repository support. `research_synthesis@1`'s refusal was the third prompt blocked by the citation protocol and **forced M9.5** rather than being tuned around. R-09 was answered by measurement — two model calls, ~54 s steady-state — and deliberately not converted into a threshold |
| **Deferred** | External retrieval · browser tools · public web search · embeddings · pgvector · provider re-query · ATTESTED findings — each with a stated trigger. `T-ID1`, `T-ID2`, `T-CK1` remain unscheduled |
| **Engineering lesson** | **A refusal is a finding, not an obstacle.** The milestone stopped on a REFUSED prompt, investigated instead of optimising, and the investigation produced a first-class repository concept (the Prompt Rendering Protocol) plus a certification framework. It also produced a *correction*: protocol 2 fixed less than predicted, and that is recorded rather than quietly absorbed |

**M9's full review: [30-m9-retrospective.md](docs/architecture/30-m9-retrospective.md).** Fourteen sections, written for an engineer arriving months later.

**What changed.** M9 is the first module that produces propositions its input did not contain. Everything before it derives, projects or restates; this one **concludes** — and the interesting half was never making a model reason, but *remaining accountable for a conclusion that cannot be checked against a fact.*

**The number that summarises it:** the model authors **3 of the Decision Package's 15 parts**. Support, temporal explanation, alternative readings, limitations and validation steps are all derived, composed or read from a reviewed catalog.

**Ownership moved five times**, always toward the component that already knew the fact — limitations to the signal catalog, rejected hypotheses to derivation rather than storage, the catalog itself to `SignalQueries`.

**Two ADRs:** [ADR-0030](docs/architecture/adr/0030-the-decision-package.md) (accepted) and [ADR-0031](docs/architecture/adr/0031-evidence-citation-protocol.md) (proposed, unimplemented). **No ratified ADR was reversed.**

**T128's assumption was disproved by measurement.** `reasoning@1` was believed to require a hosted model. It required **4 GiB of VRAM**: `llama3.1:8b` needs 5.6 GB and ran 58% on CPU, missing the 60s timeout. A 1.9 GB model resident 100% in GPU passed **eight consecutive times**. On this hardware *stronger → larger → more CPU offload → slower*, so the answer was a **smaller** model. No architectural change was required.

**The defining characteristic**, and the thing most worth carrying forward:

> **The repository improved the architecture by refusing incorrect assumptions** — through import-linter contracts, surviving mutations, unreachable guards, database grants, a layering rule, and four evaluation refusals. **Not one was worked around.** Nine stated assumptions proved false; five guards were removed for being unreachable; eleven mutations were run and six exposed genuine gaps.

---

## 10 · Current milestone — M12, the product surface

> **M12 was brought forward ahead of M11 and M7** on 2026-07-31, a Category 1 roadmap change and the product owner's to make. The reason is recorded evidence rather than preference: [31-m10-design-review-evidence.md](docs/architecture/31-m10-design-review-evidence.md) predicted this in a dissent — *"the pipeline runs nine stages ahead of any user-visible surface"* — and by M10's close it had come true. Full design: [37-product-surface.md](docs/architecture/37-product-surface.md).

| | |
|---|---|
| **Objective** | Make ten stages of pipeline reachable by a customer. Not more intelligence — **the first intelligence anyone can see** |
| **Shape** | Four slices. **M12.1** the attention list · **M12.2** the account brief · **M12.3** evidence resolution and workflow actions · **M12.4** research on demand |
| **Constraint** | No BFF, no new persistence, no new platform abstraction. The read paths exist; each module's `interface/` and the frontend are what is missing |
| **Scale** | ~13–17 ew across the four slices |

### M12.1 — in progress

Delivered: the first workspace-wide read path (`attention_list`), `GET /workspaces/{id}/accounts` with 20 full-stack tests, and `/opportunities` — **the first business screen in the repository's history.** Step 6, the performance review, is not yet measured.

### M12.2 — next, and re-ordered on usability evidence

**Entity names ship before the account brief.** The roadmap had M12.2 as the brief; building M12.1 produced the evidence to change that order.

**Why.** The attention list currently names each account by a truncated identifier — `6b8efd21` where a company name belongs — because no module in the ratified dependency graph can reach both workflow and entity names. **A seller cannot triage a list of identifiers**, so M12.1's screen is presently demonstrable rather than usable. Resolving names is a *smaller* change than the brief (one Knowledge Graph read endpoint plus a frontend join) and it is what converts M12.1 from a proof into a tool. Shipping it first makes the existing screen useful weeks before the brief would.

Recorded as **D2** in [38-product-design-principles.md](docs/architecture/38-product-design-principles.md).

*Both halves shipped: names, then the score breakdown. The narration and Decision Package panels remain.*

### M12.1.5 — inserted 2026-07-31, because the data had become the constraint

**A Category 1 insertion and the product owner's call.** M12.2's brief was the first surface with enough detail to expose what the demo dataset could not do: every account read *"evidence expired"*, and the account whose story was *stale evidence* showed a fresh ledger (D17). Design decisions, UX reviews and prompt evaluations were all being made against data that could not exercise them.

**Scope:** a demonstration dataset optimised for product review rather than for unit testing — twelve recognisable companies, twelve invented business situations, anchored on today so freshness varies on its own; complete identity coverage; determinism preserved; and the same pipeline, with no demo-only path.

**What it cost, and what it found.** The dataset itself was the smaller half. Building it surfaced **three declared capabilities with no possible input** (§7, F-8) — the naming resolver's multi-source states, every workforce fact's route to the company it described, and the entire acquisition chain. Each was complete in every layer except the one that had to supply the evidence, and each passed the tests it had.

**The rule this establishes:** a fixture set rich enough to demonstrate the product is also the first thing that exercises every declared attribute end to end. It belongs *before* the surfaces that depend on it, not after.

### M11 — deferred 2026-07-31, and why it is not cancelled

**`Recommendation Engine → AI Reasoning Engine`** is the ratified edge, and **`reasoning@1` has no released model**. M11 would layer a new AI module on a stage that cannot run, to produce recommendations surfacing on a product with one screen.

The product argument stands on its own: a recommendation answers *"what should I do?"*, which only becomes the user's question once they can answer *"which accounts?"* and *"why this one?"* — J1 ships, J2 and J3 do not. **Signora's differentiator is that a human can check every claim, not that it recommends**; shipping recommendations before the evidence surface ships the commodity half first.

**Trigger to resume — product maturity, deliberately not engineering effort:**

1. `reasoning@1` holds a current release, and
2. a design partner using the account brief asks *"so what do I do?"* — feedback showing the gap has moved from *what is true* to *what to do*.

*"When M12 is finished"* was rejected as a trigger: it would resume M11 on a schedule, and the deferral exists precisely because M11's value depends on a product state rather than a date. Full rationale in [37-product-surface.md](docs/architecture/37-product-surface.md).

### 🔴 The open blocker, restated

**`reasoning@1` has no released model.** This is M9.5's, not M12's, and it does not block M12 — but it means the shipped pipeline would refuse at the Decision Package stage, and no amount of green gates changes that. It must not be closed by tuning.

---

## Appendix A — Milestone records *(historical)*

> Dated records of what was true when written. **Corrected only for factual errors about the past, never rewritten to match the present.** Recent milestones are covered in more depth by [30-m9-retrospective.md](docs/architecture/30-m9-retrospective.md) and [docs/SESSION_HANDOFF.md](docs/SESSION_HANDOFF.md).

### Completed milestones

### ✅ M0 — Secure Multi-Tenant Foundation · closed 2026-07-28

| Delivered | Evidence |
|---|---|
| Full architecture documentation set | 19 docs + 27 ADRs; 651 cross-links verified |
| Product strategy | [PRODUCT_DIFFERENTIATORS.md](PRODUCT_DIFFERENTIATORS.md) |
| Engineering constitution | [CLAUDE.md](CLAUDE.md) |
| Workspace & Tenancy module | All 5 layers, 5 use cases, 4 REST endpoints |
| Platform: db, event_bus (publisher), auth, authorization, api, pagination | ~1,288 LOC |
| PostgreSQL RLS tenant isolation | 4 migrations, reversible, adversarially tested |
| JWT auth boundary (ADR-0026) | RS256, pinned algorithms, forged-attack tests |
| Casbin authorization | Workspace-scoped policy, unit-tested |
| CI pipeline definition | ruff, mypy, import-linter, pytest |
| Execution roadmap | 4 planning documents |

**Three defects found by testing, not review:** superuser RLS bypass · membership policy that delegated enforcement to application code · `platform` shadowing a stdlib module. All fixed, documented, and covered by regression tests proven to fail against the pre-fix state.

### ✅ M1.1 — Platform Runtime · closed 2026-07-28

All 11 tasks delivered. **Demo Checklist: 13/13 passed. AC-1 passed.**

| Delivered | Evidence |
|---|---|
| Coverage measurement + CI gate (T1, T2) | 95.01% measured, gate at 95%, Redis service in CI |
| Structured JSON logging with redaction (T3) | 23 tests; JWT/bearer/secret redaction proven |
| Event bus dispatch schema (T6) | Migration 0004: `processed_event`, `dead_letter_event`, relay columns |
| Outbox relay (T7) | 12 integration tests; concurrent-relay safety via `SKIP LOCKED` |
| Dispatch + platform-owned idempotency (T8) | 14 integration tests; exactly-once proven under concurrency |
| ARQ worker fleet, 7 pools (T9) | Per-stage pools; `ai_research` at concurrency 2 / 1800s timeout |
| Retry + dead-lettering (T10) | Capped exponential backoff; DLQ replay retains history |
| OpenTelemetry, Sentry, metrics (T4, T5, T11) | Trace context survives the relay hop; 8 pipeline metrics |

**Findings during delivery:**
- **Dead code removed.** The pagination refactor left `list_for_workspace` (no caller at all) and `list_for_user` (test-only caller) behind. Both deleted rather than covered with tests.
- **Coverage exclusion is narrow and justified.** Only `apps/worker/relay_main.py` (an `asyncio.run` entry point) is omitted. The *logic* inside the worker — `dispatch_event`'s retry and dead-letter policy, pool resolution — is tested directly.

### ✅ M1.2 — Authentication Boundary · closed 2026-07-28

All 7 tasks plus 3 added requirements delivered. **Demo Checklist 10/10. AC-2 passed.** [Architecture Validation Report](docs/architecture/ARCHITECTURE_VALIDATION_M1_2.md) issued: all seven confirmations hold.

| Delivered | Evidence |
|---|---|
| Next.js 15 scaffold, tooling, CI (T12) | ESLint, Prettier, tsc, Vitest, Playwright all green |
| Signing-key management (T15, done before T14 per approval) | Pair-match validation; 10 unit tests |
| Better Auth + Google/Microsoft OAuth (T13) | `auth` schema (migration 0005), password auth disabled |
| RS256 JWT issuance (T14) | **Cross-tier contract test: a real frontend-minted token verifies with the real Python verifier** |
| Typed API client (T16) | Token refresh, standard error envelope |
| Frontend shell (T17) | Sign-in, workspace create/list, sign-out |
| E2E auth journey (T18) | Playwright; skips cleanly without OAuth credentials |
| **Auth observability** (added) | 10 `AUTH_*` events across both tiers, shared vocabulary |
| **Auth health** (added) | Both tiers; key-pair match, JWT config, OAuth config, DB |

**First user-visible outcome in the project.** Design-partner onboarding is unblocked once M14.5 provides a deployed environment.

**Findings:**
- Two toolchain workarounds recorded in the validation report (ESLint flat-config bridge, `@vitejs/plugin-react` peer conflict). Neither is architectural.
- A skip condition in the contract test initially hid it — the frontend path was resolved one directory too shallow, so it silently skipped rather than running. Caught by running verbosely; a test that skips when it should run is worse than one that fails.
- **One defect found during validation and fixed:** `signora_auth` was created by migration 0005 but never connected as — the frontend defaulted to the database *owner*, which bypasses RLS on every application table and defeated the schema isolation the migration exists to create. Both tiers' permissions were individually correct; nothing asserted the relationship between them. Fixed and verified against a live database.

---

### Milestone records — written at each close

### ✅ M6 — Opportunity Engine · **CLOSED** 2026-07-29

| Field | Value |
|---|---|
| **Status** | ✅ **Completed** |
| **Completion date** | 2026-07-29 |
| **Commits** | `c638d1c` (proposal) · `8034cfb` (ratification + binding milestone DoD) · `6cec891` (T102–T110) |
| **`HEAD` at close** | `6cec891` |
| **Exit gate** | ✅ **`make smoke` passed** — 95s, fresh images, clean Compose stack, **20 stages**, 261 invariants green against the running system |
| **Effort** | ~8–12 ew scoped · delivered within range |

**The milestone in one line.** Signora's **first workflow module** — and the first sellable moment: the point where derived intelligence becomes something a person commits to.

**The permanent principle it establishes:**

> **Intelligence suggests. Humans commit.**
>
> A buying score may **create** an opportunity. **Only a human may progress one beyond the machine-authored boundary.** Commercial intelligence informs workflow; it never owns it.

**The distinction the milestone turned on.** Every module before M6 *derives*: delete its table, re-run the pipeline, and the same rows return byte for byte. An opportunity records that a human committed, and nothing reproduces that. That introduces **workflow state** as a third category of platform data, and with it an operational contract: until now *"rebuild the pipeline"* was universally safe; it is now safe **for derived intelligence only** — asserted by test rather than remembered.

**The lifecycle question, answered explicitly.** An opportunity **always outlives** the score that created it. A score is a reading with a stated expiry; an opportunity is a commitment. Nothing happening at a company is not evidence that a deal is dead. Cooling evidence is surfaced (`CURRENT`/`COOLING`/`STALE`, derived at read time, never stored) and **never acted upon** — creation is automatic, closure never is.

**Scope delivered.** `opportunity_policy@1` artifact · `Opportunity` (written once) and `OpportunityState` (append-only, complete state per row) · five stages with `TRACKING` the only machine-authored one · migration 0014 (three tables, forced RLS, no `UPDATE` grant) · customer-authored qualification policy with artifact fallback · `QualifyOpportunity` and `TransitionOpportunity` · membership verified server-side on every assignment · derived `evidence_state` · `OpportunityQueries` · `opportunity.created` and `opportunity.stage_changed` · smoke stage 14h.

**Acceptance criteria satisfied.** AC-58 through AC-65, plus tenancy, event-contract, and Security Invariant criteria. **29 new Security Invariants**, each proven to fail when its guarantee was removed.

**Architectural decisions recorded.** Workflow required **no exception to immutability** — no `UPDATE` grant on any of the three tables, and no `delete` on the repository either (derived tables offer deletion so regeneration can be their rollback; workflow has no regeneration). The machine/human boundary is enforced **three ways**: the type system, the domain, and a database CHECK. Reopening is a transition with `CLOSED_WON` terminal; `DISMISSED` stays distinct from `CLOSED_LOST` because one is feedback about Signora and the other a sales outcome.

**Two departures from the approved proposal**, recorded in [27-opportunity-engine.md](docs/architecture/27-opportunity-engine.md): the state log records **complete state rather than deltas** (a delta row can contradict the row before it; a state row cannot) · the citation is protected by **`ON DELETE RESTRICT`** (immutability governs updates and says nothing about deletes, and derived tables deliberately keep `DELETE`).

**Technical debt introduced.** None.

**Known limitation.** The simulated scenario produces a modest buying score, and Signora's shipped threshold correctly declines it. The demonstration has the *workspace* author its own threshold rather than lowering a product default to make a demo pass — both behaviours are asserted. **No product default was tuned.**

---

### ✅ M5B — Buying Score Engine · **CLOSED** 2026-07-29

| Field | Value |
|---|---|
| **Status** | ✅ **Completed** |
| **Completion date** | 2026-07-29 |
| **Commits** | `bc78021` (proposal) · `8c6333b` (ratification + decay reversal) · this change (T93–T101) |
| **Exit gate** | ✅ **`make smoke` passed** — 87s, fresh images, clean Compose stack, **22 stages**, 223 invariants green against the running system |
| **Effort** | ~8–12 ew scoped · delivered within range |

**The milestone in one line.** The pipeline's **first intentional reduction** — many live commercial hypotheses become one number per account, and everything the number discards stays recoverable through the ledger that produced it.

**The permanent principle it establishes:**

> **Buying scores prioritize commercial attention. They do not predict purchasing behaviour. They do not estimate probability. They do not resolve contradiction. They summarize *explainable* commercial attention.**
>
> A buying score may **summarize** intelligence; it must **never replace** it.

**The decision the milestone turned on.** *Prioritizing* is not *resolving*. Deciding which of two contradictory hypotheses is true needs evidence this module does not have and judgement belonging to AI Reasoning and to humans; ordering attention while the contradiction stands needs neither. That rules out the obvious implementation: **opposing hypotheses never cancel arithmetically**, because netting would score a fought-over account like an inert one — under the shipped model, 4 versus 45.

**Scope delivered.** `scoring_model@1` artifact (posture, weights, relevance multipliers, age bands, ceiling) · `ContributionLedger` as a first-class domain object with reproduction and no-double-count invariants checked at construction · `BuyingScore` projected from its ledger, immutable, with derived identity · migration 0013 (`buying_score`, `workspace_scoring_model`, forced RLS, no `UPDATE` grant) · customer-authored scoring models with artifact fallback · event-unit attribution · step decay · contradiction detection with named dissent · `ComputeBuyingScore` · the evidence-derived staleness sweep · `BuyingScoreQueries` · `buying_score.updated` · smoke stage 14g.

**Acceptance criteria satisfied.** AC-50 through AC-57, plus tenancy, event-contract, and Security Invariant criteria. **16 new Security Invariants**, each proven to fail when its guarantee was removed.

**Architectural decisions recorded.** Step decay over linear, exponential and none — *the decisive argument was semantic consistency, not accuracy*: a stored score promises to be exactly correct until `valid_until`, and only a discrete curve can keep that promise without continuous recomputation, which the platform has rejected. Also: the third ownership layer (`workspace_scoring_model` beside `signal_profile`, never inside it), posture as Signora's and weights as the customer's, the business event as the unit of contribution, and account fit deferred to M6.

**Three departures from the approved proposal**, each recorded in [26-buying-score-engine.md](docs/architecture/26-buying-score-engine.md): the sweep is workspace-scoped rather than cross-tenant (a cross-workspace query cannot be served under forced RLS without a role that bypasses it, and no such role may exist) · the score records `model_artifact_version` + `scoring_model_version` rather than four version numbers · the Signal Engine is reached through a `SignalReader` port rather than concretely.

**Technical debt introduced.** None. One unrelated defect repaid: `test_migration_runner.py` pinned the head revision to `"0012"`, so a test about *concurrency* failed on every new migration; it now reads head from the Alembic script directory.

**Carried forward.** The scheduled M2.0 simulation work — evidence recent enough that several hypotheses are concurrently live — is now the gating item for exercising the contested, multi-signal path at wall-clock now rather than through historical replay. **No fixture was tuned to make the demonstration look better.**

**M5B required no change to M5A and no new edge in the dependency graph** — the strongest available evidence that the Signal Engine boundary was drawn in the right place.

---

### ✅ M5A — Signal Engine · **CLOSED** 2026-07-29

| Field | Value |
|---|---|
| **Status** | ✅ **Completed** |
| **Completion date** | 2026-07-29 |
| **Commits** | `cde2218` (proposal) · this change (T84–T92) |
| **Exit gate** | ✅ **`make smoke` passed** — 76s, fresh images, clean Compose stack, **21 stages**, 186 invariants green against the running system |
| **Effort** | ~8–13 ew scoped · delivered within range |

**The milestone in one line.** The first module in Signora that produces something **true for only one customer** — and the point at which the platform stops describing the world and starts interpreting it commercially.

**The permanent principle it establishes:**

> **Business events describe objective business phenomena. Signals describe customer-specific commercial hypotheses.**
>
> Signals are therefore the **first subjective layer** in the intelligence pipeline. Everything above the Signal Engine remains globally true; everything below remains traceable back to globally true information. That subjectivity stays explicit, explainable, and constrained.

**Acceptance criteria satisfied**

| AC | Status |
|---|---|
| **AC-42** Customer-specific interpretation | ✅ Two workspaces, byte-identical business events, different signals — asserted through the real pipeline |
| **AC-43** No commercial scoring | ✅ Column-name invariant on `signal`; relevance is a category with no numeric meaning; no number in the module beyond windows and counts |
| **AC-44** Contradiction preserved | ✅ Opposing hypotheses coexist for one entity; nothing suppressed or reconciled |
| **AC-45** Two-part explainability | ✅ Every signal names both its evidence and the profile entry that made it relevant, in one call |
| **AC-46** Unbroken chain | ✅ Signal → business events → observations → entity → claims → raw records; zero orphans at every hop |
| **AC-47** Configuration is auditable | ✅ Profiles immutable, versioned, attributed; one current profile per workspace enforced by a partial unique index |
| **AC-48** Replay is explicit | ✅ Historical and current modes both work and are never conflated |
| **AC-49** The vocabulary stays global | ✅ A workspace-invented type is **unrepresentable** — `ProfileEntry.signal_type` is typed as `SignalType` |
| **AC-6** · **AC-1** · **AC-13** | ✅ Tenancy · event contract · invariants extended 154 → 186 |

**Scope delivered.** Signal catalog artifact, schema, and startup validation · domain and deterministic identity · profile model with versioning, supersession, and catalog-default fallback · two detection strategies · migration 0012 · `GenerateSignals` with relevance resolution and supersession · read port with four-question explanations · two event contracts · demonstration, smoke stage 14f, and 32 new Security Invariants.

**Architectural decisions.**

- **Global catalog, per-workspace relevance profile.** A workspace configures relevance over Signora's vocabulary and **can never invent a signal type** — the constraint that keeps AI prompting, benchmarking, analytics, and support able to speak about signals across customers.
- **Ownership decides where configuration lives, not technology.** The catalog is Signora's and ships as a repository artifact; the profile is the customer's and lives in versioned rows. A customer cannot be asked to wait for a release to say what matters to them.
- **Profiles are immutable and versioned.** An edited profile would make every historical signal unexplainable — *"why was I told this?"* would have no answer, because the reason changed underneath it.
- **Relevance is a category, never a number**, so the module contains no scores at all. This forced two corrections to the v2 event catalog: `signal.generated` **lost its `score`**, and **`signal.scored` was removed** — its only possible producer is a scoring model in M5B.
- **Composites enrich rather than replace.** Constituent signals are generated and stored in their own right, and the composite **names them**. Refined during review from "both stand" to a navigable hierarchy.
- **Catalog entries declare a detection *strategy*, not a procedure.** Adopted during review, and it proved to be more than terminology: the catalog now holds domain semantics only, so an improved implementation never changes what a signal *means*.
- **Replay has two first-class modes** — historical (reproduce what we told them) and current (what would we say now). Never conflated, and the second is what will let a customer preview a configuration change against their own history.

**Signal profiles are the first genuinely customer-authored data in the platform.** Unlike every other table, `signal_profile` cannot be regenerated from anything — it is a statement a customer makes about their own commercial position. Signals are derived and rebuildable; profiles are not, and they need backup and restore treatment derived tables do not. Asserted directly: a signal rebuild leaves the profile intact.

**One honest limit in the demonstration.** The baseline scenario's evidence is months old and every catalog type declares a shorter shelf life, so its hypotheses are formed, remain readable, and are **no longer live** — asserted explicitly. That is the lifecycle working, but it means the live-set behaviour is exercised by the negative case only. A scenario with recent evidence is now the fourth item of scheduled M2.0 simulation work.

**Technical debt.** None introduced. None outstanding.

---

### Records: what was 'next' when written

### ✅ M8 — AI Platform · **COMPLETE**

The AI Provider Abstraction Layer, the Internal Prompt Registry, and an evaluation harness — everything the reasoning and research modules will be built on.

**Built and pushed:** ADR-0028 (model runtime by environment) · the module scaffold and its five import-linter contracts · the AI Provider Port, failure taxonomy and model-keyed registry · the closed evidence set with a type-tagged digest · the five grounding checks · the Prompt Registry with content-hash identity and a derived release rule · Ollama and Anthropic adapters behind one contract suite · `application/infer.py`, the only path to a model · migration `0015` and the `ai_inference` operational record · the evaluation harness, rubric, golden dataset and `make eval`.

**Verified against a real model 2026-07-30.** `explanation_narration@1` passed evaluation against `llama3.1:8b` — 2 cases, 0 grounding failures, 0 schema failures, coverage 1.000 — and is **released for that model and refused for every other**, including `claude-sonnet-4-5`. Production runs hosted models, so the prompt M8 ships is deliberately not yet usable in production; closing that gap is an evaluation run, not a code change.

**Retry reporting closed before T121.** The first real run needed three calls for two cases — a cold model load pushed one past the 60 s policy timeout — and nothing in Signora's own report said so. `RunLog` now surfaces retries per case, in aggregate, and in the durable manifest record, and is deliberately excluded from the release criteria: retrying is what the platform is supposed to do about a transient failure.

**T121 completed the composition.** Migration `0016` adds `ai_narration` — a **fifth data category, the materialized AI artifact**: immutable, forced RLS, provenance denormalized so a row answers *which evidence · which prompt · which model · which inference · when* without a join. `ai.narration_completed` is cataloged with its producer. Smoke stage **14i** proves the chain end to end and deliberately calls no model.

**[ADR-0029](docs/architecture/adr/0029-operational-history-durability.md) closed the last finding.** `Infer` wrote an `ai_inference` row on every outcome but shared the caller's transaction, so a grounding failure that propagated rolled the record back — AC-69 held in the domain and **not in production**, and the ungrounded rate would have read 0% forever, confidently. Operational history now commits on its own transaction: *operational history answers "what happened?", business data answers "what became true?"*, and those take different lifetimes. `ai_narration` deliberately keeps the caller's transaction — a narration nobody committed was never shown to anyone. A failed operational write is itself observable (ERROR line plus `signora.ai.recording_failures`); the recorder never fails its caller, but never loses a record silently either.

**M8 is architecturally closed.** Nothing outstanding.

**Five permanent principles ratified during implementation** and recorded in CLAUDE.md §2/§6/§10: types make incorrect architecture impossible · hidden inputs are architecture defects · a guard that cannot fail is documentation pretending to be code · truth has exactly one authoritative representation · behaviour exists exactly once · ownership and configuration always align · observability is a product capability · evaluation measures compatibility with Signora's contract, not general model quality.

**Why it follows M6.** Opportunities are the first artifact expensive enough to justify agentic research and model reasoning. M8 builds the substrate; M9 and M10 use it.

**Recorded for later, not for M8:**

- **Account fit / ICP** was deferred out of M5A, M5B and M6. It needs **resolved entity attribute values**, which the Knowledge Graph deliberately does not provide — so it needs a *resolution policy*, a first-class architectural decision with its own principles. It deserves its own milestone rather than being smuggled into one that is about something else.

**Awaiting:** architecture proposal and approval, as with every prior milestone.

---

### Records: queue as written

Sequential execution — each begins only when the previous milestone's Demo Checklist passes.

| # | Milestone | Effort | Gate |
|---|---|---|---|
| 3–4 | M2.1 Provider Platform · M2.2 Provider Normalization | ~14–20 ew | Per roadmap |
| 5–6 | M3A Knowledge Graph · M3B Observation Engine | ~17–23 ew | AC-6 tenancy under load |
| 7–10 | M4 Business Events · M5A Signals · M5B Buying Scores · M6 Opportunities | ~29–43 ew | **M6 is the first sellable moment** |
| 11–14 | M8 AI Platform · M9 AI Reasoning · M10 AI Research · M11 Recommendations | ~41–56 ew | AC-8, AC-9 |
| 15–16 | M7 Timeline · M12 Revenue Intelligence Platform + business screens | ~30–43 ew | Business UI lands here |
| 17–19 | M13 Integrations · M14a Notifications · M14b Billing | ~24–34 ew | Per roadmap |
| 20 | **M14.5** Cloud Infrastructure *(deferred from M1.3B)* | ~6 ew | AC-3B · rollback executed and timed |
| 21 | M15 GA readiness | ~20–27 ew | AC-11, AC-12 |

**Full order and rationale:** [IMPLEMENTATION_ROADMAP.md §5b](IMPLEMENTATION_ROADMAP.md#5b-execution-sequence). Milestone IDs are stable labels, not sequence numbers — they are deliberately non-monotonic so that PRODUCT_ROADMAP, AI_MATURITY_ROADMAP, and every ADR cross-reference stays valid.

### Dependency corrections applied

| Correction | Why |
|---|---|
| **AI Reasoning Engine reinstated** (position 12) | Ratified module, and load-bearing: `AI Reasoning → Recommendation Engine`, and RIP lists it as a dependency. Omitted, it would never be built and two downstream modules would lose an input. |
| **Timeline moved before Revenue Intelligence Platform** (15 before 16) | `05-module-dependencies.md:76` records *"Revenue Intelligence Platform → Timeline: synchronous query"*. RIP consumes Timeline, so Timeline must precede it. |
| **Integrations (M13) reinstated** (position 17) | Ratified scope with its own architecture document and product milestone. Dropping it silently would remove committed customer-facing capability. |

None adds, removes, or substitutes a module, contract, or technology — each restores a ratified dependency.

### Module boundary rulings

**Company Domain** → part of Knowledge Graph. **Activities** → part of Timeline unless later separated. **Assignments** → unassigned; no owning context, nothing scheduled. **Workspace & Tenancy** → complete at M0, removed from the active order, retained as documented foundational work.
| 3 | **M14.5** Cloud Infrastructure *(deferred from M1.3B)* | ~6 ew | ❌ | AC-3B · rollback executed and timed |
| 4 | M15 GA readiness | ~20–27 ew | ✅ load at volume | Per roadmap |

### Cloud infrastructure is deferred, not removed

**M1.3B has moved to M14.5, immediately before GA readiness.** Sequencing only: the target production architecture is unchanged, the scope is unchanged, and nothing is redesigned. [ADR-0022](docs/architecture/adr/0022-devops-infrastructure-and-deployment-topology.md) remains ratified.

Deferred: Terraform, ECS, RDS and ElastiCache provisioning, Secrets Manager integration, the cloud deployment pipeline, cloud rollback validation, production monitoring dashboards, Auto Scaling.

**Why.** M1.3A already produced a running production stack. Cloud infrastructure adds *reachability*, not capability — it makes no pipeline module work, and until the pipeline exists there is nothing to reach. Building it now means carrying a deployed environment through ~200 ew that does not need one.

**What it costs, plainly.** No externally reachable environment until M14.5. Design partners cannot use the product remotely before then; a demo is a local stack or a screen share. Accepted deliberately.

**What keeps it cheap:** the [Infrastructure Contract](IMPLEMENTATION_ROADMAP.md#5a-infrastructure-contract) — ten requirements, all satisfied today, enforced every milestone. The failure mode of "we'll add ops later" is discovering at M14.5 that stateful services and hardcoded configuration accumulated for two years. `make smoke` is what will notice.

### Why M1.3 was split

M1.3A proves the **application** is deployable; M14.5 proves **AWS** is configured. Run together, a failure gives no signal about which one is wrong — and every application-level fault (a container that will not start, a migration runner racing two replicas, a readiness probe green before the database is reachable) costs minutes locally and an afternoon inside ECS.

### Why M1.4 exists

Verification is currently spread across a backend suite, a frontend suite, a cross-tier contract test, and a checklist a human reads. Each is individually green while the *composition* goes unverified — which is exactly where the M1.2 credential defect lived. One command turns "everything passes" into a claim about the system rather than about its parts.

### M2.0 — why it precedes every pipeline module

A permanent platform capability, not throwaway tooling — used for local development, integration testing, E2E testing, demos, AI evaluation, regression testing, performance benchmarking, and customer onboarding demos.

**It also builds the Provider Port**, as its first concrete implementation. That satisfies the YAGNI ruling and validates the port with working code before any vendor adapter is written or contract signed.

**Binding rule:** simulated providers implement *exactly* the same adapter contract as production providers. Switching is configuration only; no `if simulated:` branching may exist in any layer; the ingestion pipeline is byte-identical in both modes.

**Highest-risk control:** the simulator must never activate in production — it would fabricate customer intelligence. Guarded by an environment check, unambiguous ingestion logging, health-endpoint visibility, and an alert, all test-enforced.

---

---

## Appendix B — Change log

| Date | Change |
|---|---|
| 2026-07-31 | v28 — **M9 AI Reasoning Engine COMPLETE.** `reasoning@1` **released** against `granite3.3:2b`: 2 cases, 0 grounding failures, 0 schema failures, coverage 0.833, recorded after **eight consecutive passing runs** with **no change to the benchmark, dataset, rubric, schema, timeout or release criteria** — only `SIGNORA_OLLAMA_MODEL`. **The assumption that M9 needed a hosted model was disproved by measurement.** The constraint was **4 GiB of VRAM**, not reasoning capability: `llama3.1:8b` needs 5.6 GB and ran 58% on CPU, missing the 60 s timeout; a 1.9 GB model resident 100% in GPU passed eight times. On this hardware *stronger* means *larger* means *more CPU offload* means *slower* — the answer was a **smaller** model, which is the opposite of where the investigation started. No architectural change was required; `SIGNORA_OLLAMA_MODEL` already reached the registry. **[ADR-0031](docs/architecture/adr/0031-evidence-citation-protocol.md) written and deliberately NOT implemented:** the renderer emits `[token]` while `EvidenceRef.parse` accepts only `token`, and the prompt says *"cite by their exact reference strings"* — so three of five models were REFUSED for **obeying literally**. It is an **M8** defect that has been passing since M8 on one model's bracket-stripping habit, and fixing it requires re-evaluating both released prompts. `granite3.3:2b` is therefore recorded as **currently certified, not permanent**. Coverage sits at 0.667 against a 0.66 floor in seven of eight runs — recorded as an engineering observation, explicitly **not** a reason to modify the prompt. **Full [M9 retrospective](docs/architecture/30-m9-retrospective.md)**: nine stated assumptions proved false, five unreachable guards removed, eleven mutations run with six exposing genuine gaps — including one that would have told every customer nothing disagreed with their conclusion. 1564 tests, coverage ~95.8%, 295 invariants, 25 contracts, smoke green over 22 stages. |
| 2026-07-30 | v27 — **M9 T130 complete; M9 implementation finished, milestone not yet closed.** The Decision Package is produced, stored and announced end to end. **The principle the milestone establishes:** *every field has the least powerful author capable of producing it correctly* — which leaves the model authoring **3 of 15** parts, and makes a failure to reach a model degrade a package rather than empty it. T130 delivered the SQLAlchemy model, `SqlDecisionPackageRepository`, the `PipelineReasoningContext` adapter, `build_reason`, `ai_reasoning.completed` in the event catalog, and **smoke stage 14j** (109 tests, calling no model). **T128's architectural half closed:** both evaluation entry points now resolve providers through `build_provider_registry`, so `--model claude-sonnet-4-5` is configuration alone; the Ollama-specific `/api/tags` probe was **removed** rather than made conditional — it gated a *hosted* release run on a *local* runtime, and it was never what prevented a fake being substituted (composition is). A new Security Invariant enforces structurally that the evaluation framework names no vendor in executable code, prose exempt, with a positive control. **`reasoning@1` remains unreleased.** Run against the production model it returned **UNMEASURABLE — no adapter serves that model**, because no credential is configured here; a release could have been hand-written into the manifest in a minute and would have been a lie, so it was not, and a test now fails if one appears unearned. **Four findings, every one from the repository refusing something:** `public/` cannot publish a filesystem prompt loader (the layering contract was right, and binding prompts to an `Infer` is the application composition root's job); `SignalQueries` already owned the catalog, so a second injected copy was removed before it could disagree with itself; `signora_app` cannot read `outbox_event`, so the test uses the relay identity as the Platform Infrastructure Policy requires; and a redundant deduplication was deleted after a mutation proved it protected nothing. Eleven mutations run, six exposing real gaps that became permanent tests — including one that would have silently told every customer their evidence was single-sourced. 1563 tests, coverage 95.75%, 295 invariants, 25 contracts, `make smoke` green over 22 stages in 117s. |
| 2026-07-29 | v25 — **M5A Signal Engine complete.** The first module producing something true for only one customer. Permanent principle ratified: *business events describe objective business phenomena; signals describe customer-specific commercial hypotheses* — signals are the first subjective layer, everything above stays globally true, everything below stays traceable back. **Ownership, not technology, decides where configuration lives:** the signal catalog is Signora's and ships as a repository artifact; the profile is the customer's and lives in immutable, versioned, attributed rows. **A workspace can never invent a signal type** — unrepresentable, not merely discouraged. Relevance is a category with no numeric meaning, so the module holds no scores at all, forcing two catalog corrections: `signal.generated` loses its `score` and `signal.scored` is removed. Composites **enrich rather than replace** — constituents are stored independently and named by the composite. Catalog entries declare a detection *strategy*, keeping domain semantics separate from mechanics. Replay has two first-class modes, historical and current, never conflated. `signal_profile` is the first customer-authored table in the platform and cannot be regenerated from anything. 905 tests, coverage 95.50%, 186 invariants, 13 contracts, `make smoke` green over 21 stages. |
| 2026-07-29 | v24 — **M4 Business Event Engine complete.** The first module whose output reads as intelligence, and the first whose correctness is a product judgement. Permanent boundary: *answers "why is this business-relevant?", never "should we engage?"* — no priority, score, urgency, or rank, enforced by a column-name invariant. **Taxonomy is data; rules are code**, and the split is machine-enforced: rule modules are parsed as **syntax trees** and any numeric literal in a comparison other than 0 or 1 fails the build, with parameter declarations reconciled in both directions. Agreement is evidence, never truth — each provider's series is evaluated alone and two providers reaching one conclusion produce one event recording both. Taxonomy and payload versions kept separate so tuning a threshold never breaks a consumer contract. `business_event_type.published` removed: a repository artifact has no runtime publication to announce. **The CRO test changed three of nine proposed type names before implementation** — `EXECUTIVE_CHANGE` and `REVENUE_BAND_SHIFT` split by direction, `INTENT_SURGE` renamed — leaving eleven types across six business domains. Two limitations recorded rather than engineered around: the baseline scenario produces no intent surge under defensible thresholds, and AC-40 re-evaluation is wired at contract level only. 822 tests, coverage 95.39%, 154 invariants, 11 contracts, `make smoke` green over 20 stages. |
| 2026-07-29 | v23 — **M3B Observation Engine complete.** Permanent layering principle ratified: *claims preserve evidence · the graph resolves identity · the Observation Engine detects change · the Business Event Engine determines business meaning · the Signal Engine determines commercial meaning.* Change is computed **within one provider's series** — cross-provider comparison rejected as the central error, since disagreement merged into a series manufactures growth that never happened. First values establish a baseline and produce no observation. Observation identity is derived from observed facts, so deduplication is a primary-key conflict and a mapper fix cannot duplicate the table. Late arrival refines by append-only supersession. `entity.evidence_attached` approved and added to the Knowledge Graph; the canonical vocabulary formally recognised as a platform-wide contract. A Security Invariant reads derivation as a **syntax tree** to prove no threshold has crept in. Two defects found by running rather than by tests, one of them by `make smoke` against a fresh stack. 729 tests, coverage 95.10%, 124 invariants, 9 contracts, `make smoke` green over 19 stages. |
| 2026-07-29 | v22 — **M3A Knowledge Graph complete.** The first module that must *decide*. Permanent invariant ratified: *the Knowledge Graph resolves identity, not truth* — `entity` carries no attribute columns, and `ClaimSet` returns every contributing claim rather than a chosen value. `MatchStrength` ratified as a semantic category that can never become a number, with the type itself refusing numeric conversion and ordering. Ambiguity merges nothing, enforced by a database CHECK constraint. Migration 0009: four workspace-owned tables, forced RLS, `resolution_decision` immutable. Per-module-pair import-linter contracts added, immediately catching **two real boundary violations in shipped code** (M2.1 and M2.2), both fixed with read ports. **Two platform findings raised, not worked around** — `EventHandler` receives no session, so no module handler is registered in the live registry; and `PublishableEvent` cannot be satisfied by a frozen dataclass. One correction to the approved demonstration recorded honestly: three of five providers resolve together, not five, because the other two supply no matchable identity. 650 tests, coverage 95.54%, 99 invariants, 7 contracts, `make smoke` green over 18 stages. **[21-intelligence-pipeline.md](docs/architecture/21-intelligence-pipeline.md) authored.** |
| 2026-07-28 | v9 — **Platform Foundation approved and closed.** Eight platform contracts ratified (Platform Runtime, Authentication Boundary, Deployment Foundation, Platform Smoke Test, Security Invariants, Tenant Isolation Policy, Platform Infrastructure Policy, Platform Freeze). **M1.5 Frontend Foundation inserted** after M1.4 — frontend platform only, no business screens, no mock data. Business UI deferred until M2.0 produces real domain data. Cloud infrastructure confirmed at M14.5 with all task IDs and ADR references intact. Three dependency findings raised against the approved order (two graph inversions, five omitted modules, three unratified module names) — flagged, not silently reconciled. Sequencing only; the approved architecture is unchanged. |
| 2026-07-30 | v17 — **[ADR-0029](docs/architecture/adr/0029-operational-history-durability.md) ratified and implemented; M8 architecturally closed.** *Operational history answers "what happened?"; business data answers "what became true?"* — different categories of truth, therefore different lifetimes. `SqlInferenceRecorder` now owns a session factory and commits independently, so a grounding failure that rolls the unit of work back no longer discards the record of the call that failed. **AC-69 holds in production, not only in the domain.** The independent session stays an implementation detail: `Infer` sees only the `InferenceRecorder` port. The recorder scopes from `record.workspace_id`, taken from the verified evidence set, so a cross-workspace write is **unrepresentable** rather than merely refused. `ai_narration` keeps the caller's transaction and the asymmetry is asserted with a positive control. **A failed operational write is itself observable** — ERROR line plus the module-owned `signora.ai.recording_failures` counter; the recorder never fails its caller, but never loses a record silently. Options B and C explicitly rejected in the ADR because they appear to solve the problem and do not: a savepoint is inside the transaction that rolls back, and so is an outbox insert. Four mutations bite. Three further M8 principles recorded in CLAUDE.md §2 (determinism outranks convenience · immutability is the default for anything recording a fact · a module owns everything required to realize its behaviour). Verified: 1425 passed, 0 skipped · 280 invariants · 22 contracts · mypy strict clean over 383 files · coverage 95.36% · `make smoke` green. |
| 2026-07-30 | v16 — **M8 complete: T121 composes the validated platform.** Migration `0016` adds `ai_narration` — a **fifth data category, ratified 2026-07-30: the materialized AI artifact**, neither derived intelligence nor configuration nor workflow nor operational history, but a grounded explanation deliberately persisted for auditability, UX and provenance. Immutable (no `UPDATE` grant, no `UPDATE` policy, "current" derived from timestamps), forced RLS, provenance denormalized so a row answers *which evidence · which prompt · which model · which inference · when* without a join, `inference_id` deliberately carrying no foreign key because operational history and a customer-visible artifact have different lifetimes, and the subject addressed as `subject_kind`/`subject_id` so the pipeline's vocabulary stays out of the substrate's schema. `ai.narration_completed` cataloged with its producer, carrying **identity and counts, never the prose**. Smoke stage **14i** proves the chain end to end and deliberately calls no model — `make eval` remains the only command that does. **The stop condition was checked and not triggered:** grounding makes a proposition the pipeline did not compute inexpressible, so the M8/M9 boundary is mechanical. Nine mutations, all bitten. **One open finding, material and raised rather than fixed:** `Infer` writes an `ai_inference` row on every outcome, but `tenant_scoped_session` wraps `session.begin()`, so a grounding failure that propagates rolls the record back — AC-69 holds in the domain and *not* in production, which would make the ungrounded rate read 0% forever. Verified: 1417 passed, 0 skipped · 277 invariants · 22 contracts · mypy strict clean over 382 files · coverage 95.35% · `make smoke` green over 14i and 15. |
| 2026-07-30 | v15 — **M8 T111–T120 built, and the evaluation harness run against a real model.** Every model call in Signora now passes through one validated path; there is no way to obtain unvalidated model output. `ai_inference` (migration `0015`) makes the platform accountable for its own behaviour — a fourth data category, immutable, forced RLS, no `UPDATE` grant, with three PostgreSQL constraints stating what a row may claim and deliberately no SQL copy of the outcome enum. **First genuine evaluation:** `explanation_narration@1` passed against `llama3.1:8b` (2 cases, 0 grounding failures, 0 schema failures, coverage 1.000, floor 0.66) and is now released for that model and refused for every other — AC-74 satisfied, R-10 exercised for the first time. Ollama installed **rootless** into `~/.local` (no `sudo` available; SHA-256 verified rather than piping a script to a shell). Observations recorded rather than tuned away: 29.4 s cold load, 43–52 s per case, and **the first call hit the 60 s policy timeout and was retried** — the retry policy working, with a thin margin on this hardware. Three defects found and fixed: two in T118 that T119's table exposed (a provider failure recorded no vendor; a failed call recorded zero retries), and one in T120's own tests, which asserted the refusal-to-run-without-a-model guarantee by *inheriting* an absent runtime and broke the moment one was installed. Three false documentation claims corrected (`migrations/env.py` twice, `test_tenancy_policy.py` once). Two harness gaps raised, not fixed: the report does not surface retries, and the golden set's two cases are structurally identical. Verified: 1392 passed, 0 skipped · 274 invariants · 22 contracts · mypy strict clean over 377 files · coverage 95.36% · `make smoke` green. |
| 2026-07-30 | v14 — **Pre-flight repository synchronization; M8 design RATIFIED.** No architecture changed and no code written — this commit exists so the repository represents the architecture already approved. **Statelessness** recorded as the AI Platform's second permanent principle, with its consequences for `infer.py`, adapters, the registry, request lifecycle, replayability and future Business Capability Verification. `28-ai-platform.md` promoted from *approved in direction* to **RATIFIED**. `SESSION_HANDOFF.md` corrected — it had been instructing the next session to write a proposal that already existed. Current `HEAD` added per §20d. `make smoke`/`make dr` invoke through `bash`, removing dependence on an executable bit that commit `0309193` had dropped and that does not survive every checkout. Coverage now quoted as **~95.3%** rather than to two decimals: two identical runs measured 95.25% and 95.27%, so the earlier precision was false. Verified: 1089 passed, 0 skipped · 261 invariants · 17 contracts · mypy strict clean, 330 files · smoke green, 21 stages, 40 checks. |
| 2026-07-29 | v13 — **Local-First Development adopted ([ADR-0027](docs/architecture/adr/0027-local-first-development.md), CLAUDE.md §20c-2).** GitHub Actions disabled at repository level; all three workflows retained with `workflow_dispatch` as their only trigger and every job definition preserved. **A `git push` now stores the repository and triggers nothing.** The cross-tier JWT contract test gained a local home as `make smoke` stage 15b, which **fails if it is skipped** — the gap CI was silently covering. Documentation asserting CI as the current authority corrected to *local*; dated records of what was true at earlier milestones deliberately left intact. Two pre-existing drifts found while verifying: `make smoke` had **21 stages, not 23**, and measured coverage is **95.25%**. Re-verified locally: 1089 passed, 0 skipped · coverage 95.25% · 261 invariants · 17 contracts · mypy strict clean over 330 files · smoke green, 21 stages, 84s. |
| 2026-07-28 | v8 — **M1.4 Platform Smoke Test complete; platform foundation closed.** `make smoke`: 16 stages, ~46s, in CI, every stage proven to fail when deliberately broken. Two defects found by it — a relay that died permanently on a transient database failure (first and only post-freeze platform change, under the production-defect exemption), and two bugs in the smoke script itself that would have made it lie. **Cloud infrastructure deferred from M1.3B to M14.5** — sequencing only, nothing removed or redesigned — with a ten-point Infrastructure Contract (roadmap §5a) binding every milestone until then. 313 tests, coverage 95.63%. |
| 2026-07-28 | v7 — **M1.3A Deployment Foundation complete.** Production images (multi-stage, non-root, no secrets), concurrency-safe migration runner refusing runtime identities, 6-service production Compose stack, and Disaster Recovery Validation across Postgres/Redis/API/workers. Four defects found by running the stack rather than by tests — most seriously a worker that could never start while the whole suite passed. `signora_platform/` frozen. ADR-0022 updated with as-built topology. 310 tests, coverage 95.65%. |
| 2026-07-28 | v6 — **M1.2 approved.** Security Invariants suite established: 47 permanent invariants across authentication, authorization, database, and platform, each proven to fail when its guarantee is deliberately removed; wired into CI as a separately-reported job. Migration/runtime credential separation adopted as a permanent engineering rule (CLAUDE.md §8). M1.3 split into M1.3A Deployment Foundation and M1.3B Cloud Infrastructure; M1.4 Platform Smoke Test added; AC-3 split into AC-3A/3B/3C and AC-13 added. `@vitejs/plugin-react` recorded as scheduled technical debt. One architectural question raised for decision: platform-table read scope. |
| 2026-07-28 | v5 — **M1.2 Authentication Boundary complete.** 7 tasks plus 3 added requirements; 242 backend and 29 frontend tests; Demo Checklist 10/10; AC-2 passed; Architecture Validation Report issued. One defect found during validation: `signora_auth` created but never connected as, with the frontend defaulting to the database owner. |
| 2026-07-28 | v4 — **M1.1 Platform Runtime complete.** 11 tasks, 82 new tests (198 total), coverage 95.01% CI-gated, Demo Checklist 13/13, AC-1 passed. Dead code from the pagination refactor removed. 06-events.md updated to v3. |
| 2026-07-28 | v3 — sequential single-stream execution adopted; calendar restated by team size; Demo Checklist added as a completion gate; progressive AI regression assertion model defined; simulator identical-adapter-contract rule recorded |
| 2026-07-28 | v2 — M1 split into M1.1/M1.2/M1.3; M2.0 Provider Simulation Framework added; per-milestone Demo Scenario, User-Visible Outcome, DoD, Rollback, Operational Readiness introduced; R-14 identified; estimate revised to 225–305 ew |
| 2026-07-28 | v1 — Initialized. M0 closed. Roadmap documents created. |
