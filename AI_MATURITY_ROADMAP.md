# AI_MATURITY_ROADMAP.md

> **Owner:** AI Systems Architect / CTO · **Audience:** Engineering, Product, Exec
> **Status:** Living document — level graduation reviewed at each milestone boundary
> **Anchors:** [14-ai-architecture.md](docs/architecture/14-ai-architecture.md) · [ADR-0012](docs/architecture/adr/0012-ai-platform-architecture.md) · [04-modules.md](docs/architecture/04-modules.md) · [PRODUCT_DIFFERENTIATORS.md](PRODUCT_DIFFERENTIATORS.md)

---

## Purpose

This document defines Signora's AI capability as a **progressive ladder**, not a feature list. Each level has explicit graduation criteria; a level is not "reached" because code shipped, but because its criteria are met and evidenced.

The organising principle throughout: **capability without evaluation is not capability.** A level whose output cannot be measured has not been achieved, regardless of how impressive it demos.

---

## Note on Level Ordering

The proposed level sequence placed **Signals (L4) before Business Events (L5)**. Signora's ratified pipeline runs the other way:

```
Observations → Business Events → Signals → Buying Score → Opportunities
```

Business events are the *interpretive* layer (a funding round happened); signals are the *scored* layer derived from correlating those events (this account is showing buying intent). Signals cannot precede the events they score.

This document follows the architecture ([04-modules.md](docs/architecture/04-modules.md), [06-events.md](docs/architecture/06-events.md)), which is the source of truth. Two further adjustments: **Knowledge Graph is given its own level** (L3) — it is moat #1 and too consequential to fold into normalization — and **Buying Score is given its own level** (L6), matching its status as a distinct module and named differentiator. Result: eleven levels rather than nine.

---

## The Ladder

| Level | Capability | Module(s) | Milestone | AI-native? |
|---|---|---|---|---|
| **L1** | Data Collection | Provider Platform | M2 | No — deterministic |
| **L2** | Normalization | Provider Normalization | M2 | Minimal |
| **L3** | Knowledge Graph | Knowledge Graph | M3 | ML-assisted |
| **L4** | Observations | Observation Engine | M4 | No — deterministic |
| **L5** | Business Events | Business Event Engine | M4 | ML/LLM-assisted |
| **L6** | Signals & Buying Score | Signal Engine, Buying Score Engine | M5 | Model-driven |
| **L7** | Opportunity Intelligence | Opportunity Engine | M6 | Rules + models |
| **L8** | AI Reasoning | AI Reasoning Engine | M7 | **LLM-native** |
| **L9** | Deep Research | AI Research Engine | M8 | **Agentic** |
| **L10** | Recommendations | Recommendation Engine | M9 | LLM + learned ranking |
| **L11** | Revenue Co-Pilot | Cross-module | Post-GA | Conversational + agentic |
| **L12** | Autonomous Revenue Intelligence | Cross-module | Long-horizon | Self-improving |

**Levels 1–7 are mostly not "AI" in the LLM sense, and that is deliberate.** They are the substrate that makes L8+ trustworthy. An LLM reasoning over a poorly-resolved entity graph produces confident nonsense — which is precisely the failure mode the market already distrusts. The unglamorous levels are what make the glamorous ones defensible.

---

## Level 1 — Data Collection

**AI capabilities:** None. Deterministic ingestion via the Provider Abstraction Layer.

**Models:** None.

**Agents:** None. Scheduled ARQ jobs and inbound webhooks.

**Prompt strategy:** N/A.

**Evaluation:** Ingestion success rate per provider · payload completeness · provenance coverage · per-provider cost and quota headroom.

**Customer value:** None directly — necessary precondition.

**Graduation criteria:**
- [ ] 5 providers integrated behind one port; no vendor SDK type outside its adapter
- [ ] Ingestion success rate >98% sustained over 7 days
- [ ] 100% of payloads carry provenance (provider, timestamp, adapter version)
- [ ] Per-provider quota and cost tracked; circuit breaking verified against a simulated outage
- [ ] Adding a 6th provider provably requires zero domain-layer changes

---

## Level 2 — Normalization

**AI capabilities:** Minimal. Rule-based mapping; light fuzzy matching for field-level reconciliation.

**Models:** None initially. Deterministic rules are correct here — normalization must be reproducible and auditable, and a model that occasionally maps a field differently would poison every downstream stage silently.

**Agents:** None.

**Prompt strategy:** N/A.

**Evaluation:** Normalization coverage (% fields mapped) · conflict rate between providers · field-level confidence calibration.

**Customer value:** None directly.

**Graduation criteria:**
- [ ] Every provider's payload maps to the canonical shape
- [ ] Field-level provenance and confidence recorded
- [ ] Conflicts between providers detected and recorded rather than silently resolved
- [ ] Normalization is reproducible: same input → same output, always

---

## Level 3 — Knowledge Graph

**AI capabilities:** Entity resolution — matching records across providers into one canonical entity. **The hardest technical problem in the system and moat #1.**

**Models:** Hybrid, in this order:
1. Deterministic blocking on strong keys (domain, registration number)
2. Fuzzy/probabilistic matching on names, addresses, metadata
3. **Embeddings (OpenAI) + pgvector** for semantic similarity on ambiguous cases
4. LLM adjudication reserved for the genuinely ambiguous residual — expensive, so it must be the tail, not the default

**Agents:** None. Batch and streaming resolution pipelines.

**Prompt strategy:** For the LLM-adjudication tail only: structured comparison prompts returning a match/no-match decision **with reasoning**, so a merge is always explainable.

**Evaluation:** Precision and recall against a human-labelled entity set · merge reversal rate · duplicate rate · % of decisions requiring LLM adjudication (cost proxy).

**Customer value:** One truthful record per company — the foundation of trust in everything above it.

**Graduation criteria:**
- [ ] Labelled evaluation set built (≥1,000 entity pairs, human-adjudicated)
- [ ] Precision >95%, recall >90% on that set
- [ ] Duplicate rate <2% in production
- [ ] Every merge decision auditable, with reasoning retained
- [ ] Merges reversible — an incorrect merge must be undoable without data loss
- [ ] Embeddings stored in workspace-scoped, RLS-enforced tables (no tenancy exemption for vectors)

---

## Level 4 — Observations

**AI capabilities:** None. Deterministic recording of atomic, timestamped, provenance-tracked facts.

**Models:** None.

**Agents:** None.

**Prompt strategy:** N/A.

**Evaluation:** Observation completeness vs. graph deltas · dedup accuracy · provenance integrity (must be 100%).

**Customer value:** Indirect — but this is the layer that makes **Evidence Before Opinion** enforceable. Every recommendation Signora ever makes terminates its evidence chain here.

**Graduation criteria:**
- [ ] Every graph change produces an observation with unbroken provenance
- [ ] Deduplication verified; no double-counting under event redelivery
- [ ] Observations immutable once recorded
- [ ] An arbitrary observation can be traced back to its originating provider payload

---

## Level 5 — Business Events

**AI capabilities:** Classification of observations into domain-meaningful events (funding round, executive change, hiring surge, product launch, expansion, M&A) plus correlation of related observations into a single event.

**Models:**
- Rule-based detection for structurally unambiguous events (a funding field populated is a funding round)
- **LLM classification for free-text sources** — news, job postings, press releases — where structure is absent
- Embedding similarity for correlating observations describing the same real-world occurrence

**Agents:** None. Stateless classification per observation batch.

**Prompt strategy:** Few-shot classification against the versioned taxonomy, returning **structured Pydantic-validated output** with a confidence score and the observation ids that justify the classification. Prompt templates versioned in the Internal Prompt Registry; taxonomy version recorded on every detection.

**Evaluation:** Precision/recall per event type on a labelled set · false-positive rate per type (tracked separately — a noisy event type poisons everything above it) · correlation accuracy · classification cost per 1,000 observations.

**Customer value:** "Signora noticed my account raised a Series B." First interpretive layer; first genuinely proprietary output.

**Graduation criteria:**
- [ ] Taxonomy v1 published and versioned
- [ ] Labelled evaluation set per event type (≥200 examples each)
- [ ] **Precision >85% per event type**, no type below 75%
- [ ] Every detected event traces to its source observations
- [ ] Confidence scores calibrated — an 0.9 means roughly 90% correct in practice
- [ ] Prompt-injection mitigation verified for free-text sources (provider text is untrusted input)

---

## Level 6 — Signals & Buying Score

**AI capabilities:** Two distinct judgments, deliberately separated: **per-signal scoring** (how strong is this indicator) and **account-level composite scoring** with time decay (is this account worth pursuing now).

**Models:**
- Weighted scoring models per signal type, initially expert-configured
- Time-decay functions (event recency matters enormously; a six-month-old hiring surge is not a signal)
- **Learned weighting from conversion outcomes once volume permits** — this is where the moat begins compounding

**Agents:** None.

**Prompt strategy:** Minimal at this level. Scoring should be **deterministic and explainable**, not LLM-generated — a score a customer cannot reproduce is a score they will not trust, which is precisely the 6sense/Demandbase failure mode Signora is positioned against.

**Evaluation:** Score-to-conversion correlation · calibration curves (do 80th-percentile accounts convert ~4× the 20th?) · decay-parameter sensitivity · rep-rated relevance.

**Customer value:** A prioritized account list with an explainable number. **Plus the inverse — explicit deprioritization**, which almost no competitor offers.

**Graduation criteria:**
- [ ] Every score decomposes into contributing signals, each tracing to events and observations
- [ ] Score-to-conversion correlation measurable and positive
- [ ] Time decay validated against real conversion timing
- [ ] **Rep-rated relevance >80%**
- [ ] Deprioritization reasoning implemented and rep-rated as useful
- [ ] Score reproducible: same inputs → same score, and the difference explainable when inputs change

---

## Level 7 — Opportunity Intelligence

**AI capabilities:** Qualification of sufficiently strong buying scores into actionable opportunities; lifecycle management.

**Models:** Threshold and rules-based initially; learned qualification thresholds once outcome data accumulates.

**Agents:** None.

**Prompt strategy:** N/A at this level.

**Evaluation:** Opportunity-to-meeting conversion · false-qualification rate · qualification threshold sensitivity.

**Customer value:** "Here are the accounts to pursue this week, and why." Answers three of Signora's four founding questions.

**Graduation criteria:**
- [ ] Qualification thresholds explicit, configurable, and documented
- [ ] Every opportunity traces to its buying score and onward to source evidence
- [ ] **Rep acceptance rate >60%**
- [ ] Opportunity lifecycle (created → pursued → won/lost/expired) tracked for feedback
- [ ] False-qualification rate measured, not merely assumed low

---

## Level 8 — AI Reasoning 🧠 **First LLM-native level**

**AI capabilities:** Structured reasoning over an opportunity, its buying score, contributing signals, and graph context — producing explanation, prioritization rationale, and suggested angle, **with evidence citations**.

**Models:** Claude, OpenAI, Gemini via the AI Provider Abstraction Layer. Static per-task routing initially; cost/latency/quality-aware routing later (Horizon 2).

**Agents:** None — single structured request/response. Deliberately: bounded latency and predictable cost are what make this usable in a rep's daily flow.

**Prompt strategy:**
- Versioned templates in the **Internal Prompt Registry**, reviewed like code
- Structured context assembly, strictly workspace-scoped
- **Structured output validated against a Pydantic schema before anything downstream trusts it**
- Confidence/uncertainty as first-class output fields — the model must be able to say "thin evidence"
- Model, model version, and prompt version recorded on every result

**Evaluation:** **The evaluation harness ships before this engine.** Golden test sets, human-review sampling, CI-enforced regression testing on prompt change, evidence-completeness as a release gate.

**Customer value:** "I know why this account matters and I can defend it in the room."

**Graduation criteria:**
- [ ] **Evaluation harness operational and CI-wired before the engine ships** (resolves R-10)
- [ ] Golden set ≥200 cases with human-adjudicated quality ratings
- [ ] **Factual accuracy >90%**; zero fabricated evidence citations tolerated
- [ ] **Evidence-completeness 100%** — a reasoning result with a broken chain never reaches a user
- [ ] Confidence calibrated against measured accuracy
- [ ] Latency P95 within the product SLA (to be set from telemetry — R-07)
- [ ] Cost per reasoning call tracked and within per-workspace budget (R-01)
- [ ] Prompt-injection resistance tested with adversarial provider-sourced content
- [ ] Vendor failover verified: any one of the three vendors can be unavailable without an outage

---

## Level 9 — Deep Research 🔬 **Agentic**

**AI capabilities:** Multi-step, tool-using research on a qualified opportunity — planning, retrieval across the graph and prior artifacts, provider re-query, synthesis into a structured brief.

**Models:** Frontier models via the abstraction layer, with tool-calling. Higher cost and latency tolerance than L8, deliberately.

**Agents:** **Yes — the first true agentic workload.** Bounded by an explicit research timeout (R-09) and a per-task cost budget. Every step logged with provenance so the artifact's reasoning chain is reconstructable.

**Prompt strategy:** Planning prompt decomposing the research question; per-tool prompts for retrieval and provider queries; synthesis prompt producing a structured artifact. All versioned; every agentic step recorded.

**Evaluation:** Research completeness vs. human analyst baseline · factual accuracy on verifiable claims · rep-rated usefulness · cost and latency distribution · timeout rate.

**Customer value:** An analyst-grade account brief in minutes. The differentiator most likely underestimated today and decisive in three years.

**Graduation criteria:**
- [ ] Research timeout empirically set from production latency data (resolves R-09)
- [ ] **Non-blocking contract proven**: AI Reasoning completes correctly when research times out, degrading gracefully
- [ ] Per-task cost budget enforced; runaway research impossible (R-01)
- [ ] Every agentic step logged; artifact provenance fully reconstructable
- [ ] **Rep-rated usefulness >4/5** on a sample of ≥100 briefs
- [ ] Factual accuracy on verifiable claims >90%
- [ ] Temporal migration trigger conditions monitored ([12-scalability.md](docs/architecture/12-scalability.md))

---

## Level 10 — Recommendations

**AI capabilities:** Converting validated reasoning into a specific, prioritized, actionable next step — who, what, when, which channel, why.

**Models:** LLM for action generation and phrasing; **learned ranking from acceptance and outcome data** as it accumulates.

**Agents:** None. Human always in the loop — recommendations are proposed, never executed autonomously.

**Prompt strategy:** Action-generation templates constrained to a defined action vocabulary; output validated; prioritization deterministic where possible so ordering is explainable.

**Evaluation:** **Acceptance rate** (the leading trust indicator) · dismissal-with-reason analysis per signal/event type · pipeline generated per recommendation acted on (the North Star) · win-rate and cycle-length lift vs. baseline.

**Customer value:** "Signora tells me what to do next, specifically."

**Graduation criteria:**
- [ ] Every recommendation carries its full evidence chain
- [ ] **Acceptance rate >50%** sustained, and improving
- [ ] Dismissal reasons captured and attributed to source signal/event type
- [ ] **Feedback loop live**: `recommendation.status_changed` feeding Signal Engine (this is where compounding starts)
- [ ] Pipeline attribution measurable
- [ ] No recommendation triggers a privileged or outbound action without human confirmation

---

## Level 11 — Revenue Co-Pilot 🚀 *Post-GA*

**AI capabilities:** Conversational interface over the entire intelligence graph. Ask questions in natural language, get evidence-backed answers; agentic multi-account analysis; proactive briefings.

**Models:** Frontier models with tool access to every module's query interface.

**Agents:** Conversational agent with retrieval tools, plus scheduled proactive-briefing agents. **Almost certainly Temporal-orchestrated** by this point.

**Prompt strategy:** System prompt encoding Signora's domain vocabulary and reasoning norms; retrieval-augmented over graph, timeline, and prior artifacts; strict workspace scoping enforced at the tool layer, never by prompt instruction alone.

**Evaluation:** Answer accuracy on a benchmark question set · hallucination rate (target: zero fabricated evidence) · task completion rate · session depth.

**Customer value:** "I ask Signora questions the way I'd ask my best analyst."

**Graduation criteria:**
- [ ] L8–L10 sustained at target quality for ≥2 quarters — do not build this on an unproven base
- [ ] Benchmark question set with human-adjudicated answers
- [ ] Zero cross-workspace leakage under adversarial prompting (dedicated red-team exercise)
- [ ] Cost per session within budget
- [ ] Every answer evidence-cited; "I don't know" is an acceptable and expected output

---

## Level 12 — Autonomous Revenue Intelligence 🌐 *Long-horizon*

**AI capabilities:** The system improves its own scoring, detection, and reasoning from accumulated outcome data — a genuine learning system rather than a configured one.

**Models:** Continuously retrained scoring and qualification models; prompt optimization driven by evaluation data; multi-vendor routing learned from cost/latency/quality outcomes.

**Agents:** Autonomous monitoring agents; self-evaluating reasoning; automated prompt-regression detection.

**Prompt strategy:** Prompts become **optimized artifacts rather than hand-written ones**, with the registry retaining full lineage — every version traceable to the evaluation data that produced it.

**Evaluation:** Continuous online evaluation; automated regression detection; **measured self-improvement rate** — does quarter-over-quarter accuracy actually rise?

**Customer value:** Signora gets measurably better the longer a customer uses it, and better across customers as the platform learns — the flywheel fully turning.

**Graduation criteria:**
- [ ] Demonstrated quarter-over-quarter quality improvement attributable to learning, not manual tuning
- [ ] Cross-customer learning strictly at the **pattern/model level** — no customer's proprietary data ever influences another's view. Non-negotiable; it is both a trust commitment and an RLS invariant ([11-tenancy.md](docs/architecture/11-tenancy.md))
- [ ] Automated regression detection catching quality drops before customers do
- [ ] Human override always available; autonomy is never irreversible

---

## Cross-Level Invariants

Hold at **every** level. A level that violates one has not graduated, whatever its metrics say.

1. **Evidence before opinion.** Every AI output traces to source observations. No exceptions, no "we'll add provenance later."
2. **Validate before trust.** AI output is untrusted content until schema-validated. It never triggers a privileged action unvalidated.
3. **Workspace scoping is absolute.** Context assembly never crosses a tenant boundary. Enforced structurally, not by prompt instruction.
4. **Provenance on everything.** Model, model version, prompt version recorded on every result.
5. **Vendor-agnostic.** All model access through the AI Provider Abstraction Layer. No vendor SDK in domain or application code.
6. **Cost-governed.** Per-workspace and platform budgets enforced before any level is broadly enabled (R-01).
7. **Calibrated, not confident.** Uncertainty stated honestly. Overclaiming once costs a rep's trust for months.
8. **Evaluation precedes capability.** A level without measurement has not been reached.

---

## Current Position

**Signora is at Level 0.** No AI capability is implemented. The foundation supporting it — tenancy, auth, the event bus outbox, the shared API layer — is complete and production-grade.

**Next AI-relevant work**, per [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md):
1. Event bus relay (unblocks L1)
2. AI Provider Abstraction Layer + Prompt Registry (Stream B, ahead of need)
3. **AI Evaluation Harness — before any engine ships**

**The single most important sequencing decision in this document:** the evaluation harness is built *before* the reasoning engines, not after. It is the difference between AI quality that is managed and AI quality that is hoped for — and it is the one place where a schedule-driven reordering should be refused.
