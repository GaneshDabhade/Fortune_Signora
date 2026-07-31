# 33 — What is the AI Research Engine? A scope analysis before M10 T132

**Status:** Analysis — no recommendation is binding until the product owner rules.
**Date:** 2026-07-31 · **Repository position:** `29867ab`, M10 T131 complete, no implementation beyond scaffolding.

> **Method.** The roadmap was treated as a hypothesis, not as a settled input. Every claim below is
> sourced to a file and line in this repository. Where the roadmap and the repository disagree, the
> disagreement is reported rather than reconciled in the roadmap's favour.

---

## 0 · Why this document exists

Two assumptions were carried into M10 planning from the roadmap:

1. **M10 requires pgvector.**
2. **Agentic research requires external tool use.**

Neither was checked against the repository. This document checks both, and answers the question they
depend on: **what is the AI Research Engine's intended scope?**

---

## 1 · What the repository actually says

### 1.1 · The ratified dependency graph gives this module exactly two edges

[05-module-dependencies.md:67](05-module-dependencies.md) — the Dependency Matrix:

> | AI Research Engine | Opportunity Engine, AI Platform · **never the AI Reasoning Engine** |

The graph itself ([05-module-dependencies.md:28,34](05-module-dependencies.md)) draws `OP --> ARE`
and `ARE --> AIP`, and nothing else into this module. There is **no** edge from AI Research Engine to
Knowledge Graph, to Provider Platform, to Timeline, or to any external service. The approved
synchronous-read allowlist (§ *Synchronous vs. Asynchronous Dependencies*) contains four entries and
**none of them belongs to this module**.

### 1.2 · No document in this repository proposes external web research

A repository-wide search for `web search · websearch · browser · scrape · crawl · SERP · Tavily ·
Perplexity · SEC filing · annual report · news API` across `docs/` and the root planning documents
returns **zero** results proposing a capability. Every hit is unrelated:

| Hit | What it actually is |
|---|---|
| `browser` × 5 | Playwright E2E testing (ADR-0023), and one security diagram labelling the user's browser |
| `LinkedIn` × 6 | All in `PRODUCT_DIFFERENTIATORS.md`, and **all of them prohibitions** (§1.3) |

There is no ADR for a web-search vendor, a browser tool, a scraping capability, or an egress
allowlist. For a repository that has an ADR for its *caching layer* and its *feature-flag tool*, the
absence of one for public-internet access is not an oversight.

### 1.3 · The product strategy explicitly forbids building an external collection capability

[PRODUCT_DIFFERENTIATORS.md:202](../../PRODUCT_DIFFERENTIATORS.md):

> **Raw data breadth gap (ZoomInfo/Apollo/LinkedIn) →** never attempt to close it by building our own
> data-collection operation. Close it by broadening Provider Platform's provider roster.

[PRODUCT_DIFFERENTIATORS.md:213](../../PRODUCT_DIFFERENTIATORS.md):

> **LinkedIn Sales Navigator:** don't build a manual browse/search tool as the primary UX. Manual
> hunting is the behavior Signora exists to eliminate, not emulate.

[PRODUCT_DIFFERENTIATORS.md:326](../../PRODUCT_DIFFERENTIATORS.md):

> **A primary contact-database business.** We will never try to out-collect ZoomInfo/Apollo/LinkedIn
> on raw data ownership. We fuse and reason over their data; we do not compete to become them.

**Signora already has a ratified answer for acquiring external public information, and it is not an
agent with a browser — it is the Provider Platform** (ADR-0013: Apollo, CoreSignal, BuiltWith,
Similarweb, NeverBounce, under contract). Option B below would build a second, uncontracted
acquisition path alongside a bought one, which is Principle 14 inverted.

### 1.4 · The three tools the architecture does name are **all internal**

[14-ai-architecture.md:80](14-ai-architecture.md), the AI Research Engine internal design:

> `Agentic Tool Use: Knowledge Graph retrieval, pgvector semantic search, provider re-query via
> Provider Platform`

[AI_MATURITY_ROADMAP.md:258](../../AI_MATURITY_ROADMAP.md), Level 9:

> planning, retrieval across the graph and prior artifacts, provider re-query, synthesis into a
> structured brief

**Not one named tool reaches the public internet.** The most external of the three — provider
re-query — reaches a *contracted* provider through Signora's own abstraction layer.

### 1.5 · There is no corpus to embed

This is the finding that settles the pgvector question, and it comes from the migrations, not the docs.

**Knowledge Graph** (migration `0009`) — the module ADR-0008 names as needing semantic retrieval:

| Table | Columns that could carry natural language |
|---|---|
| `entity` | **none** — `id`, `kind` (a 32-char enum), audit columns |
| `identity_binding` | `domain`, `legal_name`, `country` — short identifiers, not prose |
| `relationship` | **none** — typed edge, `valid_from`/`valid_to`, evidence claim ids |
| `resolution_decision` | `reasons` JSONB — structured rule/field/value/strength records |

**Provider Normalization** (migration `0008`) — `claim` is an `attribute`/`value` JSONB pair with a
typed `claim_domain`, an `observed_at`, and a `mapper_version`.

**Signora's knowledge is a typed claim ledger and a typed edge graph.** The only unbounded text in the
system is the raw provider `payload` JSONB (migration `0007`), which is deliberately *not* the
queryable surface — normalization exists precisely to turn it into typed claims.

**Embedding retrieval answers "what is semantically near this text?" over a document corpus.** Asked
of an enum `kind`, a typed relationship, and an attribute/value pair, the question is a category
error: a structured query answers it *exactly*, *deterministically*, and — decisively — *citably*,
which an approximate-nearest-neighbour hit is not.

### 1.6 · The AI Platform's port refuses embeddings, in writing

`backend/modules/ai_platform/domain/provider.py:272`:

> `embeddings and vision are absent because no caller needs them — a wider [port] …`

[28-ai-platform.md:526](28-ai-platform.md), *Deferred, with reasons*:

> **Embeddings, pgvector, semantic retrieval** — ratified in ADR-0012, needed by M10's research
> retrieval, and with no caller in M8. **Building it now is the speculative port the ruling forbids.**
>
> **Tool use / function calling** — M10's mechanism. Building it in M8 would be building the agentic
> engine early, and **it carries its own security surface deserving its own review.**

That security review has not happened. It is a precondition, not a task.

### 1.7 · pgvector does not exist anywhere in this repository

No extension in any migration · no vector column · no embedding table · no dependency. The Knowledge
Graph shipped in **M3A** without embeddings, and the **eight milestones since — M3B, M4, M5A, M5B,
M6, M7, M8, M9 — have not needed them.**

---

## 2 · A contradiction inside the architecture set, reported not reconciled

[14-ai-architecture.md:80](14-ai-architecture.md) names three tools. **Two of them require dependency
edges that [05-module-dependencies.md](05-module-dependencies.md) does not grant:**

| Named tool | Edge it requires | Edge exists? |
|---|---|---|
| Knowledge Graph retrieval | `ARE → KG` | ❌ Not in the graph, not in the sync allowlist |
| pgvector semantic search | storage only (own tables) | ✅ Permitted — but see §1.5 |
| provider re-query via Provider Platform | `ARE → PP` | ❌ Not in the graph, not in the sync allowlist |

This is a genuine disagreement between two ratified documents, and it is not mine to settle in either
direction. **The graph is the authority on dependencies** — it is the document `import-linter`
enforces, it was updated at T131, and adding an edge to it is a Category-1 architectural change
requiring an RFC (CLAUDE.md §5).

**The practical consequence: the tool list in 14-ai-architecture.md describes a module that the
dependency graph would refuse to let compile.** One of the two documents is wrong, and finding out
which is a decision for you.

> **Not incidentally, the graph's version is buildable today and the other is not.** §3.1 shows the
> single ratified edge already reaches everything the other two would have fetched.

---

## 3 · The options

### 3.0 · What "research" means in each

| | A — Internal | B — External | C — Hybrid |
|---|---|---|---|
| Sources | Signora's own ledger, graph, scores, signals, opportunity history, prior artifacts | Company sites, SEC, news, LinkedIn, analyst reports | A, escalating to B when A is insufficient |
| Egress | Model vendor only (as M9 today) | Model vendor **+ uncontracted third parties** | Both, conditionally |
| Epistemic origin produced | DERIVED (Rule 9 — inference directing attention) | **ATTESTED** | Both |

### 3.1 · The claim that makes Option A non-trivial

Option A is not "research with the interesting part removed." **The one ratified edge already reaches
the entire evidence chain.**

`OpportunityExplanation` (`opportunity_engine/application/queries.py:64`) carries the opportunity, its
complete history, `originating_score`, `current_score`, and `evidence_state`. Its own docstring:

> the buying score explanation already carries the contribution ledger and one `SignalExplanation` per
> contributing signal, **so a caller walks from a tracked account to a raw provider payload without
> writing a join**

So through `opportunity_engine.public` alone, a research agent reaches: opportunity → state history →
buying score → contribution ledger → every contributing signal → the business events beneath them →
the observations beneath those → the claims → the raw payload. **The full derivation chain, already
workspace-scoped, already citable, already immutable.**

What research adds over M9 is not *access*. It is **choice**:

| M9 — AI Reasoning | M10 — AI Research, Option A |
|---|---|
| A **fixed** context assembled by `PipelineReasoningContext` | A context the agent **plans and extends** |
| One structured call | Multi-step, iterative, budgeted, resumable |
| Answers a question the pipeline already framed | **Decides which questions are worth asking** about this account |
| Point-in-time | Cross-temporal — what changed over six months, what the relationship graph implies |
| Consumes the current score | Can read **superseded** scores, retired signals, resolution decisions |
| Cannot surface provider disagreement | **Can** — two providers' conflicting claims are both in the ledger and nothing surfaces them today |

Every architectural property M10 exists to prove — planning, tool selection, iteration, cost budget,
timeout, resumability, per-step provenance, the non-blocking contract — is exercised in full. **The
tools are internal queries instead of HTTP fetches. Nothing else about the agent changes.**

And one property gets *better*: a finding that cites a `claim_id` is checkable by the customer against
a row. A finding that cites a URL is checkable only by trusting that a model read the page correctly.

### 3.2 · The fourteen dimensions

| # | Dimension | **A — Internal** | **B — External** | **C — Hybrid** |
|---|---|---|---|---|
| 1 | **Architectural fit** | ✅ Fits the ratified graph exactly — two edges, no new ones | ❌ Needs an unratified egress capability and an RFC | ⚠️ Fits until it escalates, then becomes B |
| 2 | **Consistency with existing ADRs** | ✅ Consistent with 0008, 0012, 0013, 0025 | ❌ Contradicts ADR-0013's acquisition path; no ADR authorises egress | ⚠️ Needs B's ADRs, deferred not avoided |
| 3 | **Knowledge Contract** | ✅ **Rule 9 exactly** — inference directs attention without conferring status | ❌ Requires the open ATTESTED ruling (34 §*Consequences*, item 1) | ❌ Same ruling, same blocker |
| 4 | **Deterministic Explainability** | ✅ Every finding cites a row a customer can open | ⚠️ A URL is checkable but **not derived** — the definitional gap 31 §*Questions* names | ⚠️ Mixed provenance in one artifact — the hardest case to explain |
| 5 | **Need for embeddings** | ❌ **None** — no corpus (§1.5); structured queries are exact | ✅ Genuine — retrieved pages *are* a corpus | ✅ Genuine, on the external half |
| 6 | **Need for pgvector** | ❌ **None** — and none for ≥1 milestone after (§4.1) | ✅ Follows from 5 | ✅ Follows from 5 |
| 7 | **Need for tool use** | ✅ **Yes** — internal tools. Same port capability, no egress | ✅ Yes, plus HTTP, plus an allowlist, plus injection hardening | ✅ Yes, both |
| 8 | **Need for disclosure policy** | ❌ **None new.** Egress is model-vendor-only — identical in kind to M9 today | 🔴 **Blocking.** A query naming a customer's account is a disclosure to a party with no contract | 🔴 Blocking, at the escalation boundary |
| 9 | **Need for external providers** | ❌ None beyond the model vendor already in use | ✅ A search/fetch vendor — **new ADR, new contract, new dependency** | ✅ Same |
| 10 | **Evaluation complexity** | ⚠️ Moderate — but *verifiable*: internal claims have ground truth in the ledger | 🔴 High — "factual accuracy on verifiable claims >90%" (L9) against a live, changing web is not reproducible | 🔴 Highest — two methodologies plus escalation-decision quality |
| 11 | **Operational cost** | ⚠️ Model tokens only; bounded by the 1800s `ai_research` budget | 🔴 Model tokens + per-search fees + retrieved-page tokens (the largest term) | 🔴 A's floor, B's ceiling, less predictable than either |
| 12 | **Customer value** | ✅ High and defensible: *"here is what your own data says that nobody had assembled"* | ✅ High and vivid — but **duplicates what a rep can already Google**, and is where competitors are strongest | ✅ Highest ceiling, latest arrival |
| 13 | **Implementation effort** | ~6–9 ew *(estimate)* | ~14–18 ew *(estimate)* | ~16–20 ew *(estimate)* |
| 14 | **Future extensibility** | ✅ **A is a strict subset of C.** Nothing built for A is discarded when B arrives | ⚠️ Inverts the safe order — the unratified half ships first | ✅ By construction, but pays for it up-front |

*Effort figures are my estimates from the task decomposition, not measurements. They are offered for
relative shape, not for planning precision.*

### 3.3 · The two dimensions that decide it

**Dimension 4 (Deterministic Explainability)** is the product's stated value proposition:

> *Customers should never be asked to trust the AI. They should be shown enough to reach their own
> judgement.* — [31-m10-design-review-evidence.md](31-m10-design-review-evidence.md) §*What is
> genuinely at stake*

An internal finding hands the customer a row id. An external finding hands them a claim that a model
read a page correctly. **These are not the same kind of checkability**, and the difference is exactly
the open ruling.

**Dimension 14 (Extensibility)** decides the *ordering* independently of the ruling: **A is a strict
subset of C.** The planner, the budget, the step ledger, the resumability, the artifact schema, the
provenance chain, the non-blocking contract, the evaluation harness — every one is shared. Adding
external retrieval later adds a tool and a policy; it does not revisit a single thing A builds.

**The reverse is not true.** Building B first ships the half that needs a legal ruling, a new vendor,
a new ADR, an injection-hardening review and an unratified graph edge — *before* the half that needs
none of them. And per [31 §*Comparison*](31-m10-design-review-evidence.md), the external route is the
**only one of the five evidence options that is not reversible after shipping**: once generated
external content is stored as evidence and cited by shipped packages, the distinction between derived
and attested premises is unrecoverable from the rows.

---

## 4 · The three assumptions, challenged directly

### 4.1 · "M10 requires pgvector"

**Evidence supporting it.** ADR-0008 names AI Research Engine as a pgvector consumer and
[14-ai-architecture.md:61–62](14-ai-architecture.md) ratifies OpenAI Embeddings across three modules.
This is real ratification and I am not dismissing it.

**Evidence contradicting it — five findings.**

1. **ADR-0008's own justification is self-defeating on day one.** It scopes pgvector to *"semantic
   retrieval over ... prior research artifacts."* At M10 T132 there are **zero prior research
   artifacts.** The stated purpose cannot be served by the milestone that builds it.
2. **There is no corpus** (§1.5). The Knowledge Graph stores an enum `kind` and typed edges. There is
   no text to embed.
3. **ADR-0008 assigns embedding storage to the owning module** — *"isolated per owning module
   (Knowledge Graph, AI Research Engine)."* Knowledge Graph embeddings are **Knowledge Graph's to
   build**, and M10 building them would be one module creating another's table (CLAUDE.md §8).
4. **The port refuses it in writing** (§1.6), and M8 deferred it *by name* as "the speculative port the
   ruling forbids."
5. **ADR-0012 ratified OpenAI Embeddings and OpenAI is not reachable.** There is no OpenAI adapter
   (`ai_platform/infrastructure/adapters/` holds `anthropic.py` and `ollama.py`), no credential, and
   **no code anywhere that reads an OpenAI key** — `AIVendor.OPENAI` exists as an enum value and
   nothing else. This is the same wall that made the M9 hosted evaluation UNMEASURABLE. Building
   against an unreachable vendor produces an adapter no test can exercise.

**Can it be deferred until research artifacts exist?** **Yes, and the deferral is self-timing.** The
first milestone with a real corpus of prior artifacts is the *second* one that produces them.
pgvector arrives when there is something to retrieve — which is a measured trigger, exactly the shape
[12-scalability.md](12-scalability.md) requires, rather than a date.

**Verdict: unsupported by repository evidence. Speculative infrastructure.** Building it now would be
the pattern the roadmap forbids twice and that M8 already refused once.

### 4.2 · "Agentic means external tools"

**Evidence supporting it.** [04-modules.md:285](04-modules.md) says *"synthesizing public and
provider-sourced information"*, and `PRODUCT_ROADMAP.md:173` describes *"structured brief with
sources."* Both readings are available.

**Evidence contradicting it — four findings.**

1. **Every tool the architecture names is internal** (§1.4). Three named tools across two documents,
   none of them reaching the public internet.
2. **"Public information" has a ratified acquisition path, and it is the Provider Platform** (§1.3,
   ADR-0013). *Public* and *externally fetched* are not synonyms here — Apollo and CoreSignal deliver
   public company information under contract. Reading "public" as "the model browses the web" imports
   a mechanism the sentence does not state.
3. **The product strategy prohibits the collection operation** external research would require (§1.3),
   in three separate places.
4. **The split's own justification never mentions external access.**
   [14-ai-architecture.md:17–23](14-ai-architecture.md) distinguishes the two modules on five axes —
   *shape, latency, cost profile, failure mode, scaling lever*. Every one is satisfied by an agent
   over internal knowledge. **The module was split on operational characteristics, not on where its
   data comes from.**

**Could an agent over Signora-owned knowledge satisfy M10's architectural intent?** **Yes — and it
satisfies the graduation criteria more rigorously.** Of L9's seven criteria
([AI_MATURITY_ROADMAP.md:270–277](../../AI_MATURITY_ROADMAP.md)), five are indifferent to data source
(timeout, non-blocking contract, cost budget, step provenance, Temporal triggers), one is a human
survey (rep-rated usefulness), and one — **"factual accuracy on verifiable claims >90%"** — is
*easier and more honest* internally, because an internal claim has ground truth in a row while an
external claim has ground truth on a page that may have changed since retrieval.

**Verdict: unsupported.** "Agentic" is a *control-flow* property — plan, act, observe, iterate, stop.
It is orthogonal to whether the actions cross the network boundary.

### 4.3 · "The 12–16 ew estimate remains valid"

**No — it prices a different milestone.** The estimate ([IMPLEMENTATION_ROADMAP.md:219,821](../../IMPLEMENTATION_ROADMAP.md))
prices research including embeddings, pgvector, a port extension, external retrieval, and their
evaluation. Removing what §4.1 and §4.2 find unsupported removes, by my decomposition:

| Removed | Why |
|---|---|
| Embeddings adapter + a new ADR + an unreachable vendor | §4.1 |
| pgvector migration, extension, index tuning, R-08 load testing | §4.1 |
| External retrieval vendor, contract, adapter, egress allowlist | §4.2 |
| Prompt-injection hardening for retrieved third-party content | §4.2 |
| The disclosure-policy precondition and its blocking wait | §4.2, 34 §11 |
| A non-reproducible factual-accuracy methodology against a live web | Dimension 10 |

**~6–9 ew** for Option A, on the same decomposition that produced the original figure. **And it is not
merely smaller — it is unblocked**: neither open product question gates it (§5).

**But the estimate is not the finding.** The finding is that the removed items are the ones with no
repository support, and that the milestone *becomes smaller as a consequence of being corrected*
rather than by being cut.

---

## 5 · What this does to the two open product questions

Both were carried into M10 as blockers. **Under Option A, neither blocks — and one is not raised at all.**

| Question | Under A | Under B / C |
|---|---|---|
| **May an ATTESTED external claim be cited?** | ⚪ **Not raised.** Option A produces no ATTESTED knowledge. Findings are DERIVED, cite existing rows, and fall under Rule 9 | 🔴 Blocking — must be ruled before the artifact schema is designed |
| **Tool-use disclosure policy** | ⚪ **Not raised.** Egress is model-vendor-only, identical in kind to M9 shipping today | 🔴 Blocking — a new egress class to uncontracted parties |

**A correction I owe on the second, from my own prior work.** In
[34-knowledge-contract.md §11](34-knowledge-contract.md) I attached the disclosure question to **R-05**.
That was imprecise. R-05 ([16-architecture-risks.md:70](16-architecture-risks.md)) is the *AI Prompt
Data-Classification Policy* — **which categories of workspace data may be placed in a prompt sent to a
model vendor**. It governs outbound-to-vendor and it is live today, for M8 and M9, unchanged by M10.

The disclosure question I identified is **adjacent but distinct**: *may workspace data be embedded in
a query to a party with no contract?* No risk-register entry covers it. Under Option A it does not
arise; under B or C it needs its own entry. **The distinction matters because it changes who is
blocked:** R-05 does not block M10 under any option, and the egress question blocks only B and C.

The consequence is that **Option A can begin at T132 with no ruling from you at all** — which was the
sequencing property I reported at T131 and can now state more strongly: it is not that the blocked
tasks come last, it is that under Option A **there are no blocked tasks.**

---

## 6 · Findings

**F-1 · The tool list in `14-ai-architecture.md:80` names two dependencies the ratified graph
forbids.** A documentation defect in one of the two documents. It must be resolved before any tool is
built, because it determines what a tool is permitted to reach (§2).

**F-2 · Provider re-query is architecturally harder than it appears, and should be deferred even under
an expanded Option A.** A synchronous re-query from research would return a raw provider payload that
**never passed Provider Normalization** — no typed claim, no entity binding, no ledger row. A finding
citing it would cite something outside the evidence chain, which is Deterministic Explainability
broken from the inside. The correct shape is an *event* requesting a sync, the pipeline running
normally, and research reading the resulting claims — which is asynchronous and does not fit inside
one bounded research task. **This is a real design problem, not an edge to grant.**

**F-3 · Nothing surfaces provider disagreement today.** Two providers can assert conflicting values for
one attribute; both sit in the claim ledger; no module reads them against each other. This is
concrete, high-value, entirely internal, and **exactly the kind of finding a research agent should
produce**. Offered as evidence that Option A has real work to do, not as scope.

**F-4 · ADR-0031 remains unaddressed and M10 will amplify it.** Three of five models were REFUSED on
citation *form*, not reasoning. A multi-step agentic workload exercises grounding far harder than a
single call. The M9.5 recommendation ([31 §7](31-m10-design-review-evidence.md)) is unchanged and
strengthened by this analysis.

---

## 7 · Recommendation

**Option A — Internal Research — as M10's full scope. Option C as the ratified future path, entered
only on evidence. Option B rejected as an independent capability in any milestone.**

Answering the seven questions directly:

**1 · What is the minimum viable Research Engine?**
An agent that **plans a set of questions about one qualified opportunity, answers them by iterative
retrieval over Signora's own ledger, and synthesises a structured artifact in which every finding
cites an existing row** — bounded by a timeout and a cost budget, every step recorded, resumable, and
non-blocking to AI Reasoning. That is a genuine agent by every architectural property the module split
was justified on, and it needs no capability this repository has not already ratified.

**2 · What belongs in M10?**
Domain types with epistemic origin in the type system · storage with forced RLS and no `UPDATE` grant ·
internal retrieval tools over `opportunity_engine.public` · the planner and step ledger · cost budget
and timeout (resolving R-09 with measurements) · resumability · per-step provenance · the artifact and
`ai_research.completed` · prompt and evaluation · the **non-blocking contract proven by test** —
reasoning must complete correctly when research times out.

**3 · What should be deferred, and on what trigger?**

| Deferred | Trigger that ends the deferral |
|---|---|
| Embeddings + pgvector | A measured corpus of prior artifacts that structured queries cannot serve |
| External retrieval | The ATTESTED ruling **and** evidence internal research is insufficient |
| Provider re-query | F-2 designed properly, as an event |
| Cost *governance* (R-01) | A pricing table and a budget owner — a product decision |
| Temporal migration | The triggers in [12-scalability.md](12-scalability.md) |

**4 · Should embeddings be implemented now?** **No.** No corpus, no caller, an unreachable vendor, a
port that refuses them in writing, and a target table owned by another module.

**5 · Should pgvector be implemented now?** **No.** Same reasons, plus ADR-0008's own stated purpose
— retrieval over prior artifacts — cannot be served by the milestone that first produces them.

**6 · Should external tool use be implemented now?** **No.** No ADR authorises it, the product strategy
prohibits the collection operation it implies, it is the only evidence option that is irreversible
after shipping, and it is blocked on a ruling that has not been given. **Internal tool use — yes,
fully.**

**7 · Would deferring external research weaken the architecture, or reduce scope?**

**Neither, precisely.** It does not weaken the architecture: every structural property M10 exists to
prove is exercised in full by an internal agent, and Deterministic Explainability is *stronger*,
because a finding citing a `claim_id` is checkable against a row while a finding citing a URL is
checkable only by trusting a model.

And it is not simply a scope reduction, because **A is a strict subset of C** — nothing built is
thrown away when external retrieval arrives, and everything built makes that arrival cheaper.

**The honest characterisation: it defers a product capability while completing an architectural one,
in the order that keeps the irreversible decision last.** The customer-facing loss is real and should
be named — *"research the web for me"* is a vivid demo and `PRODUCT_ROADMAP.md` sells it. But it is
also the capability where competitors are strongest and where the differentiator is weakest, and
[PRODUCT_DIFFERENTIATORS.md](../../PRODUCT_DIFFERENTIATORS.md) already says so.

> **What Signora can do that nobody else can is not read the web. It is read its own ledger.**

---

## 8 · What would change this recommendation

Stated so the analysis can be falsified rather than defended:

1. **A product requirement that a brief must contain information Signora does not hold.** If the value
   is *"tell me what happened at this company that no provider reported"*, Option A cannot deliver it
   and the analysis is wrong about scope — though still right about *ordering*.
2. **Evidence that the internal ledger is too thin to research.** Measurable before T132: count the
   distinct claims, signals and relationships behind a representative opportunity. **If the answer is
   small, Option A's value is small, and I would want that measured rather than assumed.**
3. **A ruling that ATTESTED claims are citable**, which would make Option C's cost drop sharply.
4. **A demonstrated retrieval need that structured queries cannot serve**, which would restore the
   embeddings case on evidence rather than on ratification.

---

## 9 · What I need from you

**A scope ruling: A, B, or C.** T132's domain types encode the answer — `ResearchFinding`'s epistemic
origin is `DERIVED` under A and `ATTESTED` under B or C, and that is a type-level difference, not a
field. I do not want to write it twice, and I do not want to guess.

**Two documentation decisions that follow from it:**

- **F-1** — which document is corrected: the tool list, or the dependency graph.
- **Whether this analysis is ratified as M10's design document.** M8 and M9 each had one before
  implementation began; M10 has an ontology, a contract and two reviews, but no ratified milestone
  design. I recommend this document, amended with your ruling, becomes it.

**Unchanged and still outstanding:** the M9.5 recommendation (ADR-0031 + F-1 from
[31](31-m10-design-review-evidence.md)), which this analysis strengthens rather than revises.
