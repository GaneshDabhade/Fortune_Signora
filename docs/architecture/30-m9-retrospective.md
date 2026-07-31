# 30 — M9 Milestone Retrospective

> Status: **CLOSED — 2026-07-31.** M9 AI Reasoning Engine, T122–T130.
> Audience: a principal engineer arriving months from now who needs to know what changed, why, and what to carry forward.
> Anchors: [29-ai-reasoning-engine.md](29-ai-reasoning-engine.md) · [ADR-0030](adr/0030-the-decision-package.md) · [ADR-0031](adr/0031-evidence-citation-protocol.md) · [ADR-0029](adr/0029-operational-history-durability.md)

This is an engineering review, not a commit summary. It explains how the architecture *changed shape* between T122 and T130, and which of those changes were designed versus discovered.

---

## 1 · Original goals

M9 was authorised to answer one question:

> **What should a seller understand about this opportunity that the pipeline did not already compute — and how does Signora stay accountable for saying it?**

M9 is the first module that produces propositions its input did not contain. Everything before it derives, projects or restates. This one **concludes** — and the interesting half was never making a model reason. It was *remaining accountable for a conclusion that, by construction, cannot be checked against a fact.*

The product owner reframed the success criterion before implementation began, and the reframing set the whole milestone's direction:

> **Customers should never be asked to trust the AI. They should be shown enough to reach their own judgement.**

## 2 · What was actually implemented

Ten tasks, ~1,760 lines of module code against ~1,957 lines of test code — a test-to-source ratio above 1.1:1, which is what a module producing customer-facing claims should look like.

| Task | Delivered |
|---|---|
| T122 | Module scaffold, graph node, four import-linter contracts · a stale-docstring correction found by reconstruction |
| T123 | `ReasonedOutput` — the model's three fields, each a `GroundedStatement`; premise breadth as a **type invariant** |
| T124 | `SupportBasis` / `SupportLevel` — derived support that introduces **no new threshold** |
| T125 | `TemporalExplanation` — why now · why not earlier · what changed · freshness, all composed from recorded facts |
| T126 | Signal catalog extension — `limitations` and `suggested_validation` as reviewed artifacts |
| T127 | `DecisionPackage` and `Reason` — fifteen parts composed, `answers()` as the executable acceptance criterion |
| T128 | `reasoning@1`, the rubric extension, and — eventually — **the release** |
| T129 | Migration `0017`, `ai_reasoning`, forced RLS, no `UPDATE` grant |
| T130 | Model, repository, `PipelineReasoningContext`, composition root, event catalog, smoke stage 14j |

**The headline number: the model authors 3 of the Decision Package's 15 parts.** Proposition, summary, stated reasoning. The other twelve are read from immutable history, derived deterministically, or snapshotted from a reviewed catalog.

## 3 · Architectural discoveries

### The least-powerful-author rule became the milestone's spine

Ratified mid-milestone, and it reorganised everything after it:

> The database owns timestamps. Code owns derived facts. Domain experts own static knowledge. AI owns inference. **If a less powerful component can produce a field correctly, it owns that field.**

Power here means *freedom to be wrong in ways nothing can check*. Applying it to a Decision Package that had been sketched with ten model-authored fields reduced it to three. That is not a cost optimisation — a derived fact can be recomputed and defended to a customer; a generated one can only be believed.

**Its practical consequence is the one worth carrying:** because twelve parts need no model, *a failure to reach a model degrades a package rather than emptying it.* Availability of the least reliable component stopped being a availability constraint on the product.

### Grounding already permitted inference — only the prompt forbade it

Reconstruction of M8 found that none of the five `ViolationKind`s forbids a novel relational claim. What held M8 to restatement was `explanation_narration@1` rule 4 and a ratified stop condition — **a prompt and a process, not a mechanism.**

M9 therefore reused `GroundedOutput`, `verify()` and all five checks **unmodified**. That a substrate needed no change for a workload of a genuinely different shape is the strongest available evidence that M8 was factored correctly.

It also forced an honest restatement of what M9 inherits: grounding confirms a conclusion cites real facts and invents no figures. **It says nothing about whether the conclusion follows.** In M8 that was a residual risk; in M9 it is the central risk of the module.

### Evaluation is not a quality gate on models — and the difference is load-bearing

> **Evaluation measures compatibility with Signora's contract, not general model quality.**

M9 proved this twice over. A 7b model failed where a 2b model passed. The 8b model that M8 certified could not complete M9's benchmark at all. **A capable model can be unsuitable here, and a modest one sufficient** — which is exactly why the criteria are pass/fail definitions rather than a score, and why `REFUSED` is a legitimate outcome rather than a failure.

### Three evaluation states, not two

`READY` · `REFUSED` · `UNMEASURABLE`. The third was discovered, not designed: a run that cannot execute faithfully must produce **no verdict**, never a verdict averaged over the cases that happened to survive. Conflating an outage with a quality regression would retire a prompt nothing was ever wrong with.

## 4 · ADRs

| ADR | Status | What it settles |
|---|---|---|
| [ADR-0030](adr/0030-the-decision-package.md) | Accepted 2026-07-30 | The Decision Package, partitioned by author, under **Deterministic Explainability**. Replaces this document's original `ReasonedConclusion` |
| [ADR-0031](adr/0031-evidence-citation-protocol.md) | **Proposed 2026-07-31, deliberately unimplemented** | The renderer emits `[token]`; the parser accepts `token`. An M8 defect M9 surfaced and did not fix |
| [ADR-0029](adr/0029-operational-history-durability.md) | Accepted 2026-07-30 | Carried in from M8's close; its implementation is what lets `Infer`'s recorder survive M9's rollbacks |

**No ratified ADR was reversed.** One (ADR-0012's placement of the AI Provider Port) was found factually wrong about the repository and corrected as documentation, not behaviour.

## 5 · Ownership changes

Every one moved a fact *closer to the component that already knew it*:

| Fact | Was going to be | Became |
|---|---|---|
| `limitations`, `suggested_validation` | M9 fields | **`SignalTypeDefinition`** — the signal catalog, reviewed by domain experts |
| Rejected hypotheses | A stored M9 table | **Derived** on demand by `SignalQueries.unsupported_types()`, using the rules that already decide signal generation |
| The catalog in force | Injected into M9's adapter | **Read from `SignalQueries.catalog()`** — one authority, so a package cannot state limitations from a version that never applied |
| Temporal answers | Re-derived in M9 | **Composed** from `BuyingScore.trigger`, `basis_at`, `delta`, `trend` |
| Prompt→`Infer` binding | M9's composition root | **The application composition root** — `public/` cannot publish a filesystem loader |

The rule that produced all five, stated by the product owner mid-milestone:

> *Whenever implementation discovers a field naturally belongs elsewhere, prefer moving ownership rather than copying information into M9.*

## 6 · Deterministic logic moved out of AI

This is the concrete content of Deterministic Explainability. Each of these was a plausible model-authored field and is now computed:

- **Support** — from distinct corroborating providers and `EvidenceState`. Two yes/no questions, both already derived elsewhere, so **Support introduces no new threshold at all.**
- **Why now** — from `BuyingScore.trigger`, not a paraphrase. Re-deriving causality would be a guess about the least checkable thing there is.
- **Why not earlier / what changed** — from `basis_at`, `supersedes`, `delta`, `trend`.
- **Freshness** — from `EvidenceState` and `valid_until`.
- **Alternative readings** — from the grounding rules that already decide whether a signal exists. *A model asked to list alternatives it discarded is confabulating: it did not enumerate and reject them, it generated plausible ones after the fact.*
- **Limitations and validation steps** — from a reviewed, versioned catalog.
- **Contradiction** — carried from `dissenting_signal_ids`, and **never netted into the support level**.

Two deliberate exclusions are as important as the inclusions. **Contention does not lower Support** — a fought-over account warrants more attention, not average attention, and netting it away would resolve one stage later exactly what six stages preserved. **Event count does not enter Support either** — *how many is enough* is a threshold nobody can justify, and a magic number nobody can justify will be trusted by four modules within a year.

## 7 · Guards removed because stronger invariants already existed

Five, each found by a test that could not reach it:

1. **Empty-evidence check in `ReasoningContext`** — `EvidenceSet` already refuses to be built with no facts.
2. **Contested-without-dissent check in `DecisionPackage`** — `SupportBasis` already refuses it.
3. **`isinstance` assert behind a `_compose(record: object)` signature** — a lying signature *and* a guard that could not fail; replaced with the real type.
4. **A redundant deduplication in `context.py`** — `_catalog_text` already collapses repeats; two deduplications where one suffices is duplicated truth in miniature.
5. **The `/api/tags` reachability probe** — documented as the thing preventing a fake substitution, when composition is what prevents it. It gated a *hosted* release run on a *local* runtime.

Where a removal left a question a future reader would ask, **a comment marks where the guard was and why it is absent**. Documented impossibility beats redundant validation.

> **A guard that cannot fail is not protection — it is documentation pretending to be code.** The comment beside it is then a false claim that survives review.

## 8 · Mutations that exposed genuine improvements

Eleven mutations were run across the milestone. **Six exposed real gaps**; the rest were behaviour-neutral or proved a domain type made the mutation unreachable.

The most instructive cluster came at T130, and they share one cause: **the seeded scenario cannot vary the property under test.**

| Mutation | Why it survived | What it would have cost |
|---|---|---|
| `contested` forced to `False` | The fixture's score is not contested | **Every customer told nothing disagreed** with their conclusion — undoing six stages of preserved contradiction at the final write |
| `contributing_events` counting signals | The fixture has one event per signal | Double-counting an event cited by two signals |
| `dissenting_signals` dropped on write | Default fixture has zero dissent | Dissent lost at persistence |
| Providers stored unsorted | Only one provider in the fixture | Set-iteration order leaking into a stored artifact's bytes |
| `latest_for` ordered ascending | Only one package stored | The superseded package returned as current |
| Catalog dedup removed | No two shipped types share a caveat | A customer reading the same limitation twice |

**The lesson generalises well beyond M9:** *a property a fixture cannot vary is a property the fixture cannot test*, and a passing suite over such a fixture reads as coverage while asserting nothing. The fix was not a bigger fixture — it was **unit-testing the pure functions against constructed cases the integration scenario cannot express.**

One mutation survives correctly: forcing `supporting_evidence` non-empty is unreachable because `DecisionPackage.__post_init__` already refuses it. **A surviving mutation on an unreachable branch is the type system reporting success.**

## 9 · Repository assumptions that proved false

This is the section worth re-reading. Every item was believed, stated, and wrong.

| Assumption | What the repository said |
|---|---|
| *M9 needs a new grounding rule for inference* | None of the five `ViolationKind`s ever forbade it. Only a prompt did |
| *`ai_platform.public` should publish the prompt loader* | The layering contract refuses: `public/` sits **below** `infrastructure/`, and a filesystem loader is infrastructure |
| *M9's adapter needs a `SignalCatalog` parameter* | `SignalQueries.catalog()` already owned it |
| *A test can read `outbox_event` to verify publication* | `signora_app` holds no read grant. The Platform Infrastructure Policy, working |
| *The `/api/tags` probe prevents a fake being substituted* | Composition prevents it. The probe only produced a nicer message for one vendor |
| *`reasoning@1` requires a hosted model* | **It required 4 GiB of VRAM.** Eight consecutive EARNED runs on a 2b model that fits |
| *A stronger local model would do better* | On this hardware "stronger" means "larger" means "more CPU offload" means "slower" |
| *Three models refused because they reason poorly* | They refused because they **followed instructions literally** — ADR-0031 |
| *ADR-0012 placed the AI Provider Port in a platform package* | It did; the implementation put it in the owning module, twice. The ADR was wrong about the repository |

**Nine assumptions. Nine refusals. Every refusal improved the architecture.**

## 10 · Lessons to carry into M10

1. **Ask who the least powerful author is, before writing the field.** M10 (AI Research Engine) is agentic and will be *far* more tempted to generate what the platform already knows.
2. **A failure to reach a model must degrade, never empty.** M10's latency and failure profile is worse than M9's by design; build the deterministic part first, as M9 did, so there is something to degrade *to*.
3. **Evaluate before releasing, and evaluate per `(model, dataset)`.** Five models, one pass — developing against one model demonstrates nothing about another.
4. **Whenever an evaluation criterion can instead become an invariant, prefer the invariant.** Premise breadth was a rubric item at T123 and became a `@model_validator`. *Evaluation should measure what cannot be prevented; architecture should prevent everything else.*
5. **Keep the application layer thin enough that thinness is testable.** `reason.py` has a test forbidding `if support`, `if contested`, `if trend`, `len(events)`. Substantial logic there means it belongs to another owner.
6. **Do not fix a finding in the milestone that discovered it.** ADR-0031 is documented and unimplemented, deliberately.
7. **Report the observation; escalate the decision.** Hardware performance is an observation. Model selection is an architectural decision belonging to the product owner.

## 11 · Remaining technical debt

| Item | Severity | Note |
|---|---|---|
| **[ADR-0031](adr/0031-evidence-citation-protocol.md) unresolved** | **High** | The renderer/parser protocol mismatch. Currently masked by one model's formatting habit. Fixing it requires re-evaluating both released prompts |
| `support_level` / `contested` duplicate the `support` JSONB | Low | Neutralised — written from one object, never read back, asserted structurally. If the query surface proves unnecessary, drop both columns |
| Signal catalog `limitations` are **engineering-authored pending domain review** | Medium | Marked as such in the artifact. A reviewed catalog whose text nobody reviewed is a claim about provenance that is not true yet |
| `PublishableEvent` Protocol vs frozen domain events | Low | Requires a `type: ignore` at every publish site. A platform finding, raised, not fixed |
| Coverage margin 0.667 vs 0.66 floor | Low | Recorded as an engineering observation. **Not** a reason to modify `reasoning@1` |

## 12 · Open architectural questions

1. **One `ollama_model` setting, two certified prompts.** `build_provider_registry` registers a single Ollama model. `explanation_narration@1` is certified for `llama3.1:8b`; `reasoning@1` for `granite3.3:2b`. **No single process configuration can currently serve both request paths.** M10 adds a third prompt and will force this.
2. **How is a conclusion's *soundness* ever measured?** Grounding checks inputs. Nothing checks whether the conclusion follows, and nothing can mechanically. Dissent-acknowledgement is currently the only proxy.
3. **When does the domain review of the signal catalog happen**, and who signs it?
4. **Does the release rule need a staleness dimension?** A release earned against a model tag today says nothing about that tag after a vendor updates it.

## 13 · Risks for future milestones

- **R-A · The masked-defect class.** ADR-0031 passed unnoticed from M8 to M9 because one model's habit compensated. Ask of any protocol shared by two components: *what test compares them?*
- **R-B · Fixture-shaped coverage.** Six mutations survived because one seeded scenario cannot express contested scores, shared events or shared caveats. Every future module inherits this fixture.
- **R-C · Hardware as a silent architectural constraint.** 4 GiB of VRAM determined which models are usable, and it was invisible until measured. M10's agentic workload is multi-call and will hit this harder.
- **R-D · Certification drift.** `granite3.3:2b` is *currently certified*, not preferred. If that distinction is lost, a stopgap becomes a standard by default.

## 14 · Did M9 achieve its objectives?

**Yes, and with one qualification worth stating.**

The module produces conclusions its input did not contain, and it remains accountable for them: every statement grounded, every premise named, contradiction preserved, provenance complete, the whole package immutable and attributable without reconstruction. `answers()` populates all eleven customer questions, asserted executably, and **eight of the eleven are answerable with no model having spoken.**

The qualification: **accountability here means *inspectable*, not *verified*.** Signora can prove what a conclusion rested on, when, from which evidence, under which prompt and model. It cannot prove the conclusion follows. M9 did not solve that — it made it *visible*, which was the honest goal.

---

## The defining characteristic

One pattern recurred at every scale of this milestone, and it is the thing most worth carrying forward:

> **The repository improved the architecture by refusing incorrect assumptions.**

It refused through import-linter contracts (a composition root that broke its own boundary), through surviving mutations (six properties a fixture could not vary), through unreachable guards (five branches that could not fail), through database grants (a test reaching for an infrastructure table), through a layering contract (a loader that could not be published), through evaluation verdicts (four models refused, and three of them for a reason that turned out to be Signora's fault), and through reconstruction itself (nine stated assumptions, nine wrong).

**Not one of those refusals was worked around.** Each was investigated first, and each investigation produced either a better design or a documented finding. That is the discipline: *treat every repository "no" as evidence before treating it as an obstacle* — and the corollary that made it work, **never resume from memory; always resume from the repository.**

The most valuable single artifact M9 produced is arguably not the Decision Package. It is ADR-0031 — a latent platform defect that had been silently passing since M8, found only because a REFUSED verdict was investigated instead of optimised away.
