# Signora — Project Status

> **The canonical entry point for this repository.** If you read one document, read this one.
> **Last verified against the repository: 2026-07-31**, at `HEAD` `8109ed7`. Every figure below was taken from a run, a gate, or `git` — not carried forward from a plan.
>
> This is an **executive dashboard**, not a progress log. It answers: *where are we · what was completed · what changed architecturally · what is deferred · what's next · are we on track.* Dated history lives in the appendices and is never rewritten to match the present.

---

## 1 · Repository overview

**Signora** is an AI-powered Revenue Intelligence Platform: a modular monolith (Python 3.13 · FastAPI · PostgreSQL 17 · SQLAlchemy 2.x async) that turns provider payloads into commercial conclusions a seller can act on — and defend.

| | |
|---|---|
| **Current phase** | **Product Development** — nine pipeline stages built, through the AI Reasoning Engine |
| **Last completed milestone** | **M9 — AI Reasoning Engine**, closed 2026-07-31 |
| **Current milestone** | **M10 — AI Research Engine** · **Internal Research** *(ruled 2026-07-31 — see §10)* |
| **Latest commit** | `8109ed7` — *M10 T134 — retrieval that defines no new vocabulary…* |
| **Branch** | `main`, tree clean, pushed |
| **Verification** | **Local only** ([ADR-0027](docs/architecture/adr/0027-local-first-development.md)). There is no remote gate; a `git push` stores the repository and triggers nothing |
| **Overall completion** | **~57%** by engineering effort (~178 of ~261–339 ew) |
| **Projected to GA** | ~1.3–1.9 years at 3 engineers · ~2.0–2.8 at 2 · ~3.9–5.8 at 1 (80% capacity) |

**What works end to end today:** a simulated provider payload is ingested, normalised into claims, resolved into entities, diffed into observations, detected as business events, interpreted as workspace-specific signals, aggregated into a buying score, qualified into an opportunity a human commits to, narrated as a grounded explanation, and reasoned into a **Decision Package** a customer can disagree with — stored immutably, announced on the outbox, with complete provenance.

**What does not exist yet:** any user-visible surface for it. The pipeline runs **nine stages ahead of the UI** (M12). See §10.

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
| 1 | **M10** | **AI Research Engine** *(Internal Research)* | 🔵 **In progress — T135 complete** | — |
| 2 | M11 | Recommendation Engine | ⏳ Queued | — |
| 3 | M7 | Timeline | ⏳ Queued | — |
| 4 | M12 | Revenue Intelligence Platform + business UI | ⏳ Queued | — |
| 5 | M13 | Integrations — CRM, comms, calendar | ⏳ Queued | — |
| 6 | M14a | Notifications | ⏳ Queued | — |
| 7 | M14b | Billing, analytics, feature flags | ⏳ Queued | — |
| 8 | M14.5 | Cloud Infrastructure *(deferred from M1.3B)* | ⏳ Queued | — |
| 9 | M15 | GA readiness — load, SOC 2, PII, spend governance | ⏳ Queued | — |
| — | 🎯 | **General Availability** | | |

**Two foundations are frozen** and consumed rather than modified: `signora_platform/` (§20a) and the frontend foundation (§20c). **`ai_platform/` freezes after M10** — deliberately not after M9, because a port that has only served a single-call workload has never been asked for tool use or resumability ([28-ai-platform.md](docs/architecture/28-ai-platform.md), Condition 2).

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

### 🔵 Current — M10, AI Research Engine · **Internal Research** *(ruled 2026-07-31)*

| Task | Delivered |
|---|---|
| T131 | Module scaffold · graph node · four import-linter contracts (25 → 29) · six invariants |
| T132 | `EpistemicOrigin` · `ResearchTask` · `ResearchFinding` · `ResearchSynthesis` — three origins, three identity disciplines |
| T133 | Migration `0018` — **three tables because there are three data categories**; forced RLS, no `UPDATE` grant, tenancy registration |
| T134 | Internal retrieval — `ResearchFactSource` over `opportunity_engine.public`; business events and dissent, the two things M8's assembler omits |
| T135 | The planner — a closed derivation catalog, steps that cannot carry a conclusion, and **stopping as a legal answer** |

**The scope ruling landed before T132** and narrowed the milestone materially: research explores, compares and synthesises knowledge Signora already owns, and reaches no external source. See [33-ai-research-engine-scope.md](docs/architecture/33-ai-research-engine-scope.md) for the analysis and the ruling it records.

### ⏳ Next tasks

| Task | Scope |
|---|---|
| T136 | Agentic orchestration · cost budget · timeout (resolves R-09) · resumability |
| T137 | Prompt `research_synthesis@1` and its evaluation |
| T138 | `ai_research.completed` · composition root · smoke stage 14k · the **non-blocking contract proven by test** |

**Deterministic-first ordering, unchanged from M8 and M9:** storage before retrieval, retrieval before orchestration, generation and evaluation last. **Embeddings, pgvector, external retrieval and provider re-query are deferred**, each with a stated trigger.

---

## 4 · Repository health

| Indicator | Value | Target |
|---|---|---|
| **Backend tests** | **1669 passing**, 0 failing, 0 skipped | 0 skipped |
| **Frontend tests** | **101 passing**, 0 failing, 0 skipped | 0 skipped |
| **Backend coverage** | **95.82%** — varies ±0.02pp between runs | ≥95% (local gate) |
| **Security Invariants** | **316 / 316**, each proven to fail when its guarantee is removed | 100% verified |
| **import-linter contracts** | **29 kept, 0 broken** | 0 broken |
| **MyPy** | **strict, clean over 429 files** | clean |
| **`make smoke`** | ✅ **22 stages**, 101s, fresh images, clean teardown | green per milestone |
| **Migrations** | `0001`–`0018`, additive and reversible — `0018` proven by an applied downgrade/upgrade cycle | reversible |
| **Architecture drift** | **0** — no ratified ADR reversed | trending to 0 |
| **Open production bugs** | **0** | 0 |

**Every gate runs locally.** `pytest --cov` · `make smoke` · `mypy --strict` · `lint-imports` · the Security Invariants suite · migration reversibility. A gate moving from CI to local did not make it optional — it made the local run the only run, and therefore the one that decides.

**Caveat worth restating:** these numbers describe a system with zero production traffic. They are evidence of discipline, not of field reliability.

---

## 5 · Released AI prompts

A prompt is usable **exactly where a measurement says it is** — per `(model, dataset)`, never in general. Release is *derived* from the recorded evaluation, never declared.

| Prompt | v | Owner | Certified model | Dataset | Rubric | Evaluated | n | Coverage | Grounding / schema failures | State |
|---|---|---|---|---|---|---|---|---|---|---|
| `explanation_narration` | 1 | AI Platform | `llama3.1:8b` | `explanation_narration@1` | v1 | 2026-07-30 | 2 | 1.000 | 0 / 0 | ✅ **RELEASED** |
| `reasoning` | 1 | AI Reasoning Engine | `granite3.3:2b` | `explanation_narration@1` | v1 | 2026-07-31 | 2 | 0.833 | 0 / 0 | ✅ **RELEASED** |

**Three evaluation states, and they are distinct:** **READY** (earned release) · **REFUSED** (executed correctly, failed the gate — *evidence, not failure*) · **UNMEASURABLE** (could not execute faithfully, so no verdict was produced at all).

**`granite3.3:2b` is *currently certified*, not permanently preferred.** It was selected because it is the only model tested that stays entirely resident in 4 GiB of VRAM. Three of the four that did not pass failed on **citation form rather than reasoning** — see [ADR-0031](docs/architecture/adr/0031-evidence-citation-protocol.md), §7. The comparison should be re-run once that is corrected.

```bash
make eval                                       # explanation_narration@1
SIGNORA_OLLAMA_MODEL=granite3.3:2b make eval-reasoning   # reasoning@1
```

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
| **[ADR-0031](docs/architecture/adr/0031-evidence-citation-protocol.md)** | **The renderer and parser disagree about the citation protocol.** `render.py` emits `[token]`; `EvidenceRef.parse` accepts only `token`; the prompt says *"cite by their exact reference strings"*. Three of five models were REFUSED for **obeying literally**, across two independent model families. Passing since M8 on one model's bracket-stripping habit. **PROPOSED, deliberately unimplemented** — it is an M8 defect, and fixing it invalidates both released prompts | 🔴 **High** | M8 / M9.5 |
| **F-1** | **One `ollama_model` setting, two certified prompts.** The registry holds a single Ollama model; narration is certified for `llama3.1:8b` and reasoning for `granite3.3:2b`. **No single process configuration serves both request paths.** M10 adds a third prompt | 🟠 Medium | M10 |
| **F-2** | **The Evidence Set question.** *(Narrowed by [32](docs/architecture/32-knowledge-ontology.md) and [34](docs/architecture/34-knowledge-contract.md), then **downgraded by the Internal Research ruling**.)* The immediate exposure is closed by design: a `ResearchSynthesis` has **no address**, so no consumer can cite model-authored prose even deliberately, and `ResearchFinding` is DERIVED with `EvidenceRef.kind = research_finding`. What remains open is the *deferred* question — **may an ATTESTED external claim be cited?** — which arrives with external retrieval and not before | 🟠 **Medium** *(was High)* | Deferred with external retrieval |
| **F-3** | Signal catalog `limitations` / `suggested_validation` are **engineering-authored pending domain review** | 🟠 Medium | Unassigned |
| **F-4** | `ai_research.completed`'s reserved payload carries `artifact_ref` / `model_provenance` — **the same v2 placeholders M9 found and replaced** at T127 | 🟢 Low | M10 |
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
| R-09 | **AI Research timeout value undefined** | M9 ships no research integration, so nothing has ever measured it. **T136 resolves it by measurement**, not by choosing a number |
| R-10 | AI output quality regression | Substantially mitigated: golden sets, rubrics, `ai_inference`, two evaluated prompts. **Not** closed — no human-rated sample yet |
| **New** | **Two new capability surfaces in M10** — agentic loop and *internal* tool use. Was four; embeddings and pgvector were deferred by the Internal Research ruling. M8 flagged tool use as *"carrying its own security surface deserving its own review"*, and internal tools reduce that surface without removing it |
| **New** | **Fixture-shaped coverage.** Six M9 mutations survived because one seeded scenario cannot vary contested scores, shared events or shared caveats. Every future module inherits that fixture | |

### 🟢 Low

JWT key rotation requires a deploy · token revocation bounded by a 15-min TTL · Casbin policy is coarse RBAC · no API versioning scheme (deliberate, with one first-party client) · `reasoning@1` coverage margin 0.667 against a 0.66 floor — an **observation**, explicitly not a reason to modify the prompt.

---

## 9 · Recent milestone summary — M9

**Full review: [30-m9-retrospective.md](docs/architecture/30-m9-retrospective.md).** Fourteen sections, written for an engineer arriving months later.

**What changed.** M9 is the first module that produces propositions its input did not contain. Everything before it derives, projects or restates; this one **concludes** — and the interesting half was never making a model reason, but *remaining accountable for a conclusion that cannot be checked against a fact.*

**The number that summarises it:** the model authors **3 of the Decision Package's 15 parts**. Support, temporal explanation, alternative readings, limitations and validation steps are all derived, composed or read from a reviewed catalog.

**Ownership moved five times**, always toward the component that already knew the fact — limitations to the signal catalog, rejected hypotheses to derivation rather than storage, the catalog itself to `SignalQueries`.

**Two ADRs:** [ADR-0030](docs/architecture/adr/0030-the-decision-package.md) (accepted) and [ADR-0031](docs/architecture/adr/0031-evidence-citation-protocol.md) (proposed, unimplemented). **No ratified ADR was reversed.**

**T128's assumption was disproved by measurement.** `reasoning@1` was believed to require a hosted model. It required **4 GiB of VRAM**: `llama3.1:8b` needs 5.6 GB and ran 58% on CPU, missing the 60s timeout. A 1.9 GB model resident 100% in GPU passed **eight consecutive times**. On this hardware *stronger → larger → more CPU offload → slower*, so the answer was a **smaller** model. No architectural change was required.

**The defining characteristic**, and the thing most worth carrying forward:

> **The repository improved the architecture by refusing incorrect assumptions** — through import-linter contracts, surviving mutations, unreachable guards, database grants, a layering rule, and four evaluation refusals. **Not one was worked around.** Nine stated assumptions proved false; five guards were removed for being unreachable; eleven mutations were run and six exposed genuine gaps.

---

## 10 · Current milestone — M10, AI Research Engine

| | |
|---|---|
| **Objective** | Agentic, multi-step research on a qualified opportunity — planning questions, retrieving iteratively over **Signora's own ledger**, and synthesising an artifact M9 consumes as **optional, non-blocking** enrichment |
| **Scope** | **Internal Research**, ruled 2026-07-31. Research explores, compares and synthesises knowledge Signora already owns and reaches no external source. External retrieval is a future extension, explicitly outside M10 |
| **Expected outcome** | Findings that cite rows a customer can open · a planner whose choices are recorded as attention, never status · a budgeted, resumable, timed-out orchestration · `ai_research.completed` cataloged · and — the structural payoff — **the evidence that lets `ai_platform` freeze** |
| **Scale** | ~6–9 ew *(estimated)*, down from the roadmap's 12–16. **Smaller as a consequence of correction, not of cutting** — the removed items were the ones with no repository support |
| **Status** | 🔵 **In progress — T131–T135 complete** |

### Why the milestone shrank

Two roadmap assumptions were tested against the repository and both failed ([33-ai-research-engine-scope.md](docs/architecture/33-ai-research-engine-scope.md)):

- **"M10 requires pgvector."** There is no corpus. Migration `0009` gives `entity` a 32-char enum `kind` and no text at all; relationships are typed edges; normalization stores attribute/value claims. Embedding retrieval over that is a category error — a structured query answers it exactly, deterministically, and citably. ADR-0008 also scopes pgvector to *"retrieval over prior research artifacts"*, of which M10 produces the first.
- **"Agentic means external tools."** Every tool the architecture names is internal, and `PRODUCT_DIFFERENTIATORS.md` prohibits building a collection operation in three places. Public information already has a ratified acquisition path: the Provider Platform, under contract.

**Agentic is a control-flow property** — plan, act, observe, iterate, stop — and is orthogonal to whether the actions cross the network boundary.

### The three-way split T132 installed

| Object | Origin | Identity | Because |
|---|---|---|---|
| `ResearchTask` | *not knowledge* | minted | A run happened. Running twice is twice |
| `ResearchFinding` | **DERIVED** | `uuid5` over content | Recomputing must insert nothing |
| `ResearchSynthesis` | **INFERRED** | minted | A model was called. Calling twice is twice |

**The ruling that findings are DERIVED is load-bearing, not a label.** DERIVED describes how content was produced, and promotion does not exist (Rule 8) — so the model plans *which comparison is worth running* (attention, Rule 9) and deterministic code computes the answer. A finding therefore has **no free-text field**, which is exactly the shape every other DERIVED object in this repository already has.

### Open questions

1. **How does one process serve three certified prompts?** *(F-1)* Let M10's real need shape the answer; do not invent it prematurely.
2. **Where does cost governance live?** *(R-01)* The register says before research is enabled broadly.
3. **What is the research timeout?** *(R-09)* Never measured. **T136 resolves it by measurement.**

**Two questions that previously blocked M10 no longer do.** The ATTESTED ruling is not raised, because internal findings are DERIVED; the disclosure question is not raised, because egress stays model-vendor-only. Both return with external retrieval, and not before.

### Sequencing question, still open

**The pipeline now runs nine stages ahead of any user-visible surface.** The Decision Package is produced, stored and announced — and **no human can see it until M12**. M11 (6–8 ew) and M7 (6–8 ew) are both cheaper and closer to a visible surface. The counter-argument is real: M10 is the only remaining consumer needed to freeze `ai_platform`.

**A short M9.5 remains recommended** — resolve ADR-0031 while it invalidates *two* prompts rather than three, settle F-1, and re-run the model comparison. M10's smaller scope does not change that argument; ADR-0031's cost still grows with every prompt released.

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
