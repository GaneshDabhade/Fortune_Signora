# Session Handoff — end of M6

> **Purpose:** start the next engineering session immediately, without reconstructing context.
> **Authoritative continuation point.** Updated at every milestone boundary.
> **As of:** 2026-07-29 · branch `main`
>
> Read this first. Then **[21-intelligence-pipeline.md](architecture/21-intelligence-pipeline.md)** — the flagship reference for how information moves through Signora — then [PROJECT_STATUS.md](../PROJECT_STATUS.md) §1–9 for the dashboard, and [IMPLEMENTATION_ROADMAP.md §5b](../IMPLEMENTATION_ROADMAP.md#5b-execution-sequence) for the execution order. Everything else is reference.

---

## 1 · Current project position

| | |
|---|---|
| **Last completed** | **M10 AI Research Engine** — T131–T138, closed 2026-07-31. *Internal Research; every citable thing deterministic.* |
| **Inserted, and open** | **M9.5 Evidence Citation Protocol** (ADR-0031). Steps A–D landed; **Step F is incomplete** |
| **Last completed** | **M12.2 the account brief** — closed 2026-08-01. Identity, score breakdown, commitment and narration; the Decision Package is *blocked*, not skipped |
| **Current** | **M12.3 evidence and actions.** *What to check* shipped; citation resolution and stage transitions remain |
| **Head at handoff** | see `git log` — M12.3 the what-to-check slice |
| **Latest certification** | [`d954c930`](../certification/reports/d954c930319a.md) — CERTIFIED, 2026-07-31 |
| **Phase** | **Product implementation.** Ten pipeline stages built and frozen behind them; the surface is being exposed. |
| **Overall completion** | **~60%** by engineering effort (~187 of ~261–339 ew) |
| **Completed milestones** | M0 · M1.1 · M1.2 · M1.3A · M1.4 · M1.5 · M2.0 · M2.1 · M2.2 · M3A · M3B · M4 · M5A · M5B · M6 · M8 · M9 · **M10** |
| **Branch** | `main`, clean, pushed |

**🔴 Read this before anything else:** **`reasoning@1` has no released model.** M9.5 moved the rendering protocol to v2, which withdrew every protocol-1 release by derivation. `explanation_narration@1`, `research_planning@2` and `research_synthesis@2` re-earned theirs; `reasoning@1` did not — `granite3.3:2b` refuses under protocol 2 and `llama3.1:8b` is UNMEASURABLE on this hardware. **The Decision Package stage would refuse in production.** Do not tune the prompt, the delimiter, the schema or the timeout to make it pass.

**Recent commits:** `d954c93` the first business screen · `d08f8d7` the first customer endpoint · `22cafac` the attention list read path · `0cc82c6` product surface roadmap · `0c6d144` certification cites itself

### Health

| Indicator | Value |
|---|---|
| Backend tests | **1320 passing**, 0 failing, 0 skipped |
| Frontend tests | **101 passing** |
| Backend coverage | gate **≥95%** · currently **~95.3%** |
| Security invariants | **269 / 269**, each proven to fail when its guarantee is removed |
| import-linter contracts | **21 kept, 0 broken** |
| `make smoke` | ✅ **21 stages**, 40 checks, 84–203s — includes the cross-tier JWT contract (15b) since 2026-07-29 |
| Migrations | 0000–0014, all reversible |
| mypy strict | Clean, 361 files |
| Open production bugs | **0** |
| Technical debt | **0 outstanding** · **2 platform findings raised** (§5) |

**Local prerequisites:** Docker · `uv` on `PATH` (`~/.local/bin`) · Postgres and Redis via `infra/docker-compose.yml`. Tests need `SIGNORA_DATABASE_URL` (migration identity) and `SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1` — the suite truncates every table, and the flag is a deliberate guard.

---

## 2 · Architecture state

Permanent contracts. Each is enforced by automated test, not convention. **Changing any of these requires an RFC.**

### Foundations

| Contract | Established | What it guarantees |
|---|---|---|
| **Platform Runtime** | M1.1 | Transactional outbox, relay, dispatch, platform-owned idempotency, retry, dead-lettering, worker pools. Consumers are idempotent on `event_id`; nothing assumes exactly-once or cross-entity ordering. |
| **Authentication Boundary** | M1.2 | Better Auth in Next.js is the sole authentication authority. The Python tier **only verifies** RS256 JWTs and is cryptographically incapable of minting one. Algorithms pinned to exactly `["RS256"]`. |
| **Deployment Foundation** | M1.3A | Production images, per-tier database identities, concurrency-safe migration runner, restart-safe stack. `/ready` returns **503** when not ready — orchestrators route on the code, not the body. |
| **Platform Smoke Test** | M1.4 | One command verifies the whole platform. Required before every milestone and release. |
| **Local-First verification** | 2026-07-29 | Every gate runs locally ([ADR-0027](architecture/adr/0027-local-first-development.md), CLAUDE.md §20c-2). GitHub is version control, backup, and future collaboration only; Actions are disabled and the three workflows are retained at `workflow_dispatch`. **A `git push` stores the repository and triggers nothing.** CI returns only when the architecture, Intelligence Pipeline, Workflow Pipeline and AI Platform have all stabilised **and** it is explicitly requested. |
| **Platform Freeze** | M1.3A | `signora_platform/` changes only for a security fix, production defect, or approved change. **One change since:** the relay's transient-failure handling. |
| **Frontend Foundation** | M1.5 | Design system, components, shell, routing, query layer — consumed, not modified. Exceptions: production defect, **accessibility issue**, security issue, approved change. |

### Tenancy and data

| Contract | What it guarantees |
|---|---|
| **Tenant Isolation Policy** | Every table declared tenant-owned or platform infrastructure — **classification is never inferred**. Tenant tables carry a non-null identifier, RLS enabled **and forced**, and policies covering SELECT/INSERT/UPDATE separately. A table in neither list fails the build. |
| **Migration / runtime credential separation** | Runtime services never execute under migration or owner credentials. Each tier holds its own least-privileged role: `signora_app` (API, workers), `signora_auth` (frontend), `signora_relay` (outbox), owner (migrations only). |
| **Platform Infrastructure Policy** | `outbox_event`, `processed_event`, `dead_letter_event`, `alembic_version` are owned by platform services. The application **publishes and cannot read**; only the relay consumes. Isolation is by grant, since these tables span workspaces and have no RLS. |
| **Immutable tenant tables** | `claim`, `resolution_decision`, `observation`, `business_event`, `signal`, `signal_profile`, `buying_score`, `workspace_scoring_model`, `opportunity`, `opportunity_state`, and `workspace_opportunity_policy` are immutable. **Workflow required no exception** — M6 added three tables and none of them needed the grant. `signora_app` holds **no `UPDATE` grant** on any of them — an attempted overwrite fails with a permission error. `DELETE` remains, because all are derived and regeneration is the rollback for a broken mapper or rule. |
| **Shared vocabulary** | `provider_normalization/public` — the canonical attributes, their value types, and the frozen claim views — is a **platform-wide contract** every downstream pipeline module may depend on (ratified 2026-07-29). A vocabulary dependency, not a data-access one: claim *data* still travels through read ports. Extending it still requires an RFC. |
| **Module boundaries, enforced** | Since M3A, import-linter carries a contract per module pair: no module may import another's `domain/`, `application/`, `infrastructure/`, or `interface/`, and upstream modules cannot import downstream ones. Data crosses via a **read port on `public/`** — a Protocol plus frozen views, never an ORM instance. |

### Provider layer

| Contract | What it guarantees |
|---|---|
| **Provider neutrality** | The Provider Platform never knows which provider — or whether it is simulated. It knows only that it holds a Provider Port implementation. |
| **Pipeline neutrality (AC-21)** | **Behavioural, not informational.** Metadata may exist (`ProviderResponse.simulated`, `ProviderDescriptor.simulated`, `ProviderName`) provided no business behaviour changes, no branching occurs, and no simulation-specific execution path exists. Asserted directly: nothing branches on simulation state or provider identity. |
| **Provider Independence (AC-20)** | Each generator and mapper is independently removable. Scenarios compose providers; **providers never depend on each other**. |
| **Identical adapter contract** | Simulated and production adapters satisfy the same Port, verified by **one shared contract suite run against both**. This is the keystone test — the only mechanism catching drift between the two paths. |
| **Payload provenance** | A simulated payload's shape must come from official documentation, a vendor sandbox, a recorded test account, or a sanitized production response. **Never invented.** All five providers are currently `Conditional` with clearly-marked development fixtures. |

### Evidence

| Contract | What it guarantees |
|---|---|
| **Evidence-first architecture** | **Normalization preserves evidence; it does not determine truth.** No identity resolution, no reconciliation, no ranking, no confidence. Truth belongs downstream. |
| **The Claim model** | The unit of evidence: *this provider asserted this attribute had this value, as of this time, and here is the raw record.* Disagreement survives — two providers reporting different headcounts produce two claims. |
| **No confidence at normalization** | Normalization has no authority to estimate it. A number invented there would propagate into buying scores as though it meant something. |
| **Canonical vocabulary** | 15 attributes, closed and explicitly typed. **Adding one requires an RFC**; adding a mapper is routine. That asymmetry lets integrations evolve while the platform's language stays stable. |
| **Evidence chain** | Every claim carries provider, raw record id, `observed_at`, mapper version, and payload provenance. Zero orphans, asserted by join. **The chain begins at normalization and must never be weakened.** |
| **Fail loudly** | Unknown, missing, and unparseable are distinct rejection reasons, each naming its field path. A vendor shape change surfaces as a rising rejection rate, diagnosable without reading source. |

### Knowledge

| Contract | What it guarantees |
|---|---|
| **Identity, never truth** | **The Knowledge Graph resolves identity. The Knowledge Graph does not resolve truth.** `entity` has **no attribute columns** — asserted structurally. `ClaimSet` returns every contributing claim rather than a chosen value. Ratified 2026-07-28; changing it requires an RFC. |
| **Deterministic resolution** | Three rules in precedence order — provider's own key, exact domain, legal name plus country. No fuzzy matching, no similarity thresholds, no probabilistic scoring. The same claims in any order produce the same graph. |
| **`MatchStrength` is never a number** | A semantic category describing the *rule*, never a score. It must never participate in a weighted calculation or underpin heuristic resolution. **The type itself refuses** numeric conversion and ordering — `int()`, `float()`, `<`, `>` all raise. Ratified 2026-07-29. |
| **Ambiguity merges nothing** | Two matching candidates produce an `AMBIGUOUS` decision naming both and **merge nothing** — enforced by a database CHECK constraint, not by the code path that writes the row. An under-merge is a visible duplicate; an over-merge silently mixes two customers' intelligence. |
| **Decisions explain themselves** | Every binding traces to a decision naming its rule **and the value that matched**. Corrections supersede rather than mutate; on an immutable table the pointer necessarily points **backwards** (`supersedes`), because a forward one would require an `UPDATE` grant. |

### Change

| Contract | What it guarantees |
|---|---|
| **The layering principle** | *Claims preserve evidence · the Knowledge Graph resolves identity · the Observation Engine detects change · the Business Event Engine determines business meaning · the Signal Engine determines commercial meaning.* **Each stage answers one question and refuses the next one.** Ratified 2026-07-29. |
| **Change, never significance** | No threshold exists in the Observation Engine. A Security Invariant reads its derivation and use case as **syntax trees** and fails if magnitude is ever compared against a constant — so the prose explaining that there is no threshold cannot be mistaken for one. |
| **Per-provider series only** | Change is computed **within one provider's series**. Two providers reporting different values is *disagreement*, not movement; merging would manufacture growth that never happened. `derive` takes a single `provider`, so the bug is not expressible. |
| **Restraint** | **Re-assertion is never an observation** — the dominant case in a polling pipeline. The **first value establishes a baseline** and produces nothing: Signora merely learned, and `entity.created` already says that once per company. |
| **Derived identity** | An observation's id is a UUIDv5 over the observed facts — never allocated, and deliberately **not keyed on claim ids**, which are minted when a mapper runs. Deduplication is a primary-key conflict, and regenerating claims cannot duplicate the table. |
| **Refinement, not rewriting** | A late-arriving claim makes an earlier observation *less precise*, not false. The finer observations name the coarser one; it stays readable as what was believed then. |

### Business meaning

| Contract | What it guarantees |
|---|---|
| **Business relevance, never commercial judgement** | The Business Event Engine answers *"why is this business-relevant?"* and never *"should we engage this account?"*. No priority, score, urgency, or rank on `business_event` — enforced by a column-name invariant. Ratified 2026-07-29. |
| **Taxonomy is data; rules are code** | The taxonomy — types, meanings, and **every materiality threshold** — is a versioned repository artifact reviewed like code. Correlation logic is Python. Meaning evolves slowly; derivation may evolve fast, and a better rule must not change what a hiring surge *is*. |
| **No threshold in code** | Rule modules are parsed as **syntax trees**; any numeric literal in a comparison other than `0` or `1` fails the build. Declared parameters and read parameters are reconciled in both directions, and every type has exactly one rule, validated at engine construction. |
| **Agreement is evidence, not truth** | Each provider's series is evaluated alone, so no rule combines two providers' values. Two providers reaching one conclusion produce **one** event recording both — a set, never a coefficient. This is the pipeline's only cross-provider reasoning, and it is deliberately narrow. |
| **The taxonomy is a product asset** | Every type passes the CRO test: *would they immediately understand what this means?* No provider, implementation, or engineering terminology — asserted by invariant, including that business domains never name a data-model term. |
| **Two versions, never conflated** | `taxonomy_version` is meaning; `payload_version` is wire shape. Conflating them means tuning a threshold breaks a consumer contract, so nobody ever tunes a threshold. |

### Commercial meaning

| Contract | What it guarantees |
|---|---|
| **The global/subjective boundary** | *Business events describe objective business phenomena; signals describe customer-specific commercial hypotheses.* Signals are the **first subjective layer**. Everything above the Signal Engine is globally true; everything below stays traceable back to globally true information. Ratified 2026-07-29. |
| **Ownership decides where configuration lives** | Not technology. Signora's language — the business event taxonomy and the signal catalog — ships as versioned repository artifacts. The customer's commercial position — the signal profile — lives in versioned, immutable, attributed rows. Apply this criterion whenever a similar question arises. |
| **The signal vocabulary stays global** | A workspace configures *relevance* and **can never invent a type** — structurally unrepresentable, since `ProfileEntry.signal_type` is typed as `SignalType`. This is what makes AI prompting, benchmarking, analytics, documentation, and support work across customers. |
| **No commercial verdict in the Signal Engine** | No score, priority, likelihood, or rank. Relevance is a category with no numeric meaning; the module contains no numbers beyond windows and counts. |
| **Contradiction is preserved** | Opposing hypotheses coexist for one account and are never reconciled — the claim-disagreement principle one layer up. |
| **Composites enrich, never replace** | Constituent signals are generated and stored independently; the composite **names** them and adds context on top of history rather than collapsing it. |
| **Hypotheses are phrased as possibilities** | *may*, *might*, *suggests* — asserted by invariant. A type stating its hypothesis as fact has drifted into the Business Event Engine's territory. |
| **Two replay modes, never conflated** | Historical (reproduce what we told them) and current (what would we say now). Both first-class. |
| **Customer-authored data is different** | `signal_profile` cannot be regenerated from anything. Signals are derived and rebuildable; profiles need the operational rigour of customer-owned data. |
| **Downstream references business events directly** | Signals, Buying Scores, Opportunities, and AI explanations reference **business event types**, not re-derived meaning from observations. A module that reconstructs *"this looks like a hiring surge"* from raw observations has forked the vocabulary, and two definitions of one concept diverge within a year. Ratified 2026-07-29. |

### Commercial attention

| Contract | What it guarantees |
|---|---|
| **Prioritization, never resolution** | *Buying scores prioritize commercial attention. They do not predict purchasing behaviour, estimate probability, or resolve contradiction. They summarize **explainable** commercial attention.* Deciding which contradictory hypothesis is true needs evidence this module lacks and judgement belonging to AI Reasoning and to humans. Ratified 2026-07-29. |
| **Opposing readings never net** | Attention is **unsigned for every posture** — a negative contribution is unrepresentable, not merely discouraged. Netting would score a fought-over account like an inert one (4 versus 45 under the shipped model), and those are the two most different accounts in the book. Contradiction is marked `contested`, with the outweighed reading's signals **named**. |
| **A score is a projection, never a replacement** | No account attributes on `buying_score`, no account representation on `BuyingScoreQueries` — both asserted by invariant. An account's truth lives in claims, the Knowledge Graph, observations, and business events. |
| **The ledger is the score** | Read the dependency as **ledger → score**. `BuyingScore.projected_from` is the only constructor and takes the ledger first; a score whose value disagrees with its ledger is refused at construction as a *corrupt explanation*. Reproduction uses **no clock and no configuration**, in integer arithmetic end to end. |
| **The business event is the unit of contribution** | Not the signal. An event is attributed to the highest-weighted signal citing it; the others stay in the ledger with a zero contribution and a stated reason. Double counting is structurally impossible, and **nothing is silently dropped** — a zero with a reason is information; an absent row is a mystery. |
| **Step decay, because a stored score must be honest** | A score is exactly correct between `computed_at` and `valid_until`. Any decay changing continuously with wall-clock time breaks that promise the instant after the score is written. Bands are **fractions of each type's own relevance window**, reusing the catalog's judgement rather than inventing a second one. The decisive argument was **semantic consistency, not accuracy**. |
| **Staleness is evidence-derived** | Shelf-life expiry is the one input arriving without an event. The sweep reads `valid_until` — a boundary each score derived from its own evidence — rather than polling an interval somebody guessed. It is **workspace-scoped**: a cross-tenant sweep cannot be served under forced RLS without a role that bypasses it, and no such role may exist. |
| **Three layers of configuration ownership** | Signal catalog (Signora — *what hypotheses mean*) · signal profile (customer — *which we care about*) · **scoring model** (customer — *how much attention each earns*). Separate rows, deliberately: folding weights into the profile would mean tuning a score churns the explanation of every historical signal. |
| **Posture is Signora's; weights are the customer's** | A workspace tunes weights, multipliers, bands, and the ceiling. It may never invert what a signal type *means* — there is no `posture` field in the overrides and no column in the table. |
| **No signals, no score** | An account nothing has been observed about gets **no reading**, not a zero. A zero is a statement, and Signora has not made one. |

### Commercial commitment

| Contract | What it guarantees |
|---|---|
| **Intelligence suggests; humans commit** | A buying score may **create** an opportunity; **only a human may progress one beyond the machine-authored boundary.** `TRACKING` is the sole machine-authored stage, enforced **three ways** — the type system (`next_state` demands an `actor_id` with no default), the domain, and a database CHECK. Ratified 2026-07-29. |
| **Three categories of platform data** | **Derived intelligence** (rebuildable, machine-authored) · **customer configuration** (declarative, irreplaceable) · **workflow state** (accumulated, irreplaceable). They must never blur. |
| **A rebuild regenerates intelligence only** | Until M6 *"rebuild the pipeline"* was universally safe. It is now safe **for derived intelligence**; `opportunity`, `opportunity_state`, `workspace_opportunity_policy`, `signal_profile`, and `workspace_scoring_model` are never rebuilt. Asserted by test, not remembered. |
| **Opportunities outlive their score** | The score is why it was *opened*, never why it stays open. Nothing happening at a company is not evidence a deal is dead. Cooling evidence is **surfaced, never acted upon** — creation is automatic, closure never is. |
| **Workflow stores no derived intelligence** | No current score, no signals, no recomputed judgement. An opportunity cites the score that caused it and reads everything else live; `evidence_state` is derived at read time and never stored. |
| **History is never rewritten** | Append-only state, each row the *complete* workflow state rather than a delta — so the status **is** the audit log and the two cannot disagree. No `UPDATE` grant, and no `delete` on the repository either: derived tables offer deletion because regeneration is their rollback, and workflow has none. |
| **The citation cannot be orphaned** | `ON DELETE RESTRICT` on the originating score. Immutability governs *updates* and says nothing about deletes — and because every upstream id is derived from evidence, a rebuild reproduces identical score ids, so regeneration does not sever it either. |
| **Every state names its actor and reason** | *"Someone changed it"* is not an explanation. Workflow explains itself as thoroughly as intelligence does. |
| **Dismissal is distinct from a lost deal** | One is feedback about Signora's judgement, the other a sales outcome. Collapsing them would destroy the only signal the platform gets about its own qualification quality. |
| **Four ownership layers** | Signal catalog (Signora) · signal profile · scoring model · **opportunity policy** (all customer). Each module owns its own customer-authored policy, versioned alongside its output — which is also what keeps any of them extractable. |

---

## 3 · Product Pipeline state

```
Raw Provider Record   ✅ M2.1   Provider Platform — syncs, watermarks, raw storage
        ↓
Claim                 ✅ M2.2   Provider Normalization — canonical evidence
        ↓
Knowledge Graph       ✅ M3A    identity resolution, relationships, claim sets
        ↓
Observation           ✅ M3B    what changed, according to whom
        ↓
Business Event        ✅ M4     what it means, in language a CRO recognises
        ↓  ─────────── the global / customer-specific boundary ───────────
Signal                ✅ M5A    why it might matter to *this* customer
        ↓  ───────────── the first intentional reduction ─────────────
Buying Score          ✅ M5B    how much attention it deserves, explainably
        ↓  ────── intelligence suggests · humans commit ──────
Opportunity           ✅ M6     ★ what Sales actively tracks — first sellable moment
        ↓
Timeline              ⏳ M7     the account narrative
        ↓
AI Reasoning          ⏳ M9     why, with evidence
        ↓
Recommendation        ⏳ M11    what to do next
```

**Eight links exist and are verified against the live stack** (smoke stages 14b–14h). A simulated provider payload enters through the Provider Port, is stored raw, becomes canonical claims, is resolved to an entity whose decision explains itself, any change in what a provider asserts becomes an observation attributed to that provider, and a material change becomes a typed business event a CRO could read — *"Started using CloudERP"*, *"Raised 24M USD in a series b round"* — and, for a workspace that says it cares, that event becomes a commercial hypothesis with its own two-part explanation — which becomes one number per account whose every point can be traced back through the ledger to the vendor payload that started it — and, finally, an account a seller commits to tracking, whose commitment survives the number that suggested it. No simulation-specific logic exists anywhere in that path.

Everything from M8 onward is unbuilt. See **[21-intelligence-pipeline.md](architecture/21-intelligence-pipeline.md)** for what each remaining stage adds and what it is forbidden from doing.

---

## 4 · Design philosophy for the remaining pipeline

The principles that got the project here, in the order they matter:

1. **Preserve evidence.** Information discarded during processing can never be recovered. When preserving evidence and simplifying downstream code conflict, preserve evidence.
2. **Delay interpretation.** Each module should do its own job and no downstream module's. Interpretation performed early is interpretation that cannot be revised.
3. **Prefer explainability.** Every conclusion must trace to the evidence that produced it. That chain is the product — any system can produce a score.
4. **Every module must increase business understanding.** Nothing exists merely to move data. If a stage only reshapes, question whether it should exist.
5. **AI reasons over structured evidence.** It never invents facts. It explains conclusions using observations earlier modules already proved.
6. **Prefer deterministic behaviour over hidden heuristics.** A magic number nobody can justify will be trusted by four modules within a year.
7. **Prefer explicit domain concepts over generic data processing.** `TECHNOLOGY_REMOVED` beats `is_live: false`.
8. **Architecture before implementation.** Think about the domain, challenge the first design, consider alternatives, then pick the simplest model that fully covers the problem.
9. **Raise architectural questions before coding, never implement around uncertainty.** This has happened repeatedly and has been right every time.

**Process discipline that must continue:** every guard proven to fail when its guarantee is removed · documentation updated in the same change · Security Invariants extended per milestone · `make smoke` green before closing · PROJECT_STATUS updated before the next milestone begins.

---

## 5 · M8 starting context

### What M8 inherits

**Input:** tracked accounts a human has committed to. Through `modules.opportunity_engine.public`:

- `OpportunityQueries.tracked(workspace_id, entity_id)` — the open opportunity, its current state, the live score, and a derived `evidence_state`
- `OpportunityQueries.explanation(...)` — the opportunity, its complete state history, and the `BuyingScoreExplanation` for the originating score, which already carries the ledger and one `SignalExplanation` per contributing signal
- `OpportunityQueries.history(...)` · `.for_entity(...)` · `.policy(...)` · `.artifact()`

Subscribe to `opportunity.created` and `opportunity.stage_changed`.

**The whole chain is walkable from one call:** opportunity → buying score → contribution ledger → signals → business events → observations → knowledge → claims → raw provider records. Nothing downstream needs to re-derive any of it.

**Already exists and should be assumed:** event bus with platform-owned idempotency · forced RLS · `make smoke`, extensible with a stage (14b–14i) · the Tenant Isolation Policy — **register every new table in `tenancy_policy.py` or the build fails**.

### The central challenge

**M8 is a substrate milestone, not a pipeline stage.** It builds the AI Provider Abstraction Layer, the Internal Prompt Registry, and an evaluation harness — the things M9 (Reasoning) and M10 (Research) are built on. Nothing about it answers a business question, and it should not try to.

Two contracts already ratified constrain it:

1. **All vendor access goes through the abstraction layer** (`14-ai-architecture.md`, ADR-0012). No domain or application code ever touches a model SDK.
2. **AI output is untrusted until validated** against an expected Pydantic v2 structure, and must never trigger a privileged or irreversible action without validation and, where the architecture calls for it, human confirmation. **After M6 that has a sharper meaning:** the only irreversible thing in the platform is workflow, and *intelligence suggests, humans commit* now governs AI exactly as it governs scoring.

### The four open questions, now answered

All four were settled inside the proposal. Recorded here so they are not re-opened.

1. **Where do prompt versions live?** Repository artifacts beside the taxonomy, scoring model and policy — the ownership criterion's fifth application. **Immutable once released**, enforced by content hash: editing a shipped version fails the build, because it would silently invalidate every result claiming that version.
2. **What can the harness assert?** Two different things that were being conflated. **Deterministic correctness** — schema, grounding, citation, quantities, workspace — verified on every call against recorded fixtures, mutation-proven, **never calling a model**. **Probabilistic quality** — golden sets, `make eval`, outside the test gate. A Security Invariant needing a GPU is not a guarantee.
3. **Module or platform concern?** Split by whether it contains judgement: the **container** is infrastructure that *refuses* a mixed-workspace set, the **contents** are the caller's domain choice. Generalises — when a concern is part tenancy and part domain, the tenancy half is a type that refuses and the domain half is a caller that chooses.
4. **Cost and latency?** Usage yes, money no. Tokens, latency, retries are facts about what happened; a price is true for a week. Pricing is applied outside the port at reporting time.

### Two platform findings, open — RFCs queued

Both concern `signora_platform/`, which is frozen (CLAUDE.md §20a). **Neither is to be worked around inside a product milestone.**

| Finding | Effect | Resolution path |
|---|---|---|
| **`EventHandler` receives no session.** A handler must work in the *same transaction* as the dispatcher's idempotency claim, but the registry's signature is `(envelope) -> None`. | **No module handler is registered in the live registry.** The pipeline is exercised end to end through its real handlers in the integration suite and `make smoke`, but the deployed worker consumes nothing. Also leaves M5B's staleness sweep unscheduled. | RFC: **EventHandler transaction participation.** |
| **`PublishableEvent` cannot be satisfied by a frozen dataclass.** | Eight modules now carry a `# type: ignore` at their publish site. | RFC: **PublishableEvent immutability compatibility.** |

### Known limits — and which are debt

A **known limitation** is a deliberate scope boundary that behaves correctly; **architectural debt** is something that will have to be undone.

| Item | Kind | Note |
|---|---|---|
| No worker registration; no sweep scheduler | **Debt** — platform, RFC queued | The deployed worker consumes nothing. Product milestones must not route around it. |
| Eight `# type: ignore` at publish sites | **Debt** — platform, RFC queued | Small, contained, identical in every module. |
| One-open-opportunity-per-account is application-enforced | **Known limitation** | "Open" means *the latest state row is not terminal*, which no index can express. A derived `generation` plus a unique index converts the concurrent case into a conflict; the residual is checked in the transaction. Denormalising openness would restore the `UPDATE` grant to buy a constraint. |
| Signal relevance is denormalized at generation | **Known limitation** | A workspace downgrading a type from primary to supporting sees the change in newly generated signals, not existing ones. *Ignoring* a type takes effect immediately. Deliberate in M5A. |
| Demonstrations use a workspace-authored threshold and historical replay | **Known limitation** | The scenario's evidence is thin and short-lived; rather than tune product defaults to make demos pass, the demonstrations configure a workspace and ask as of a moment derived from the evidence. Fixed by the scheduled M2.0 simulation work, not by code. |
| Provider fixtures are `Conditional` | **Known limitation** | Clearly marked; payload provenance contract holds. |
| AC-40 (M4) partial | **Known limitation** | Re-evaluation on `observation.superseded` wired at contract level. |

### Carried forward

- **Scheduled simulation work (M2.0), four items.** A scenario with genuine multi-week movement · fixture enrichment so Crunchbase and CoreSignal carry a domain · an intent trajectory sustaining above the elevated threshold for enough weeks · **evidence recent and rich enough that several hypotheses are concurrently live and buying scores clear the shipped qualification threshold**, so the contested scoring path and out-of-box qualification are both exercised at wall-clock now.

### Deferred, and to stay deferred

- **Account fit / ICP** — deferred out of M5A, M5B **and M6**. It needs resolved entity attribute values, which the Knowledge Graph deliberately does not provide, so it needs a **resolution policy** — a first-class architectural decision deserving its own milestone. *Do not solve it opportunistically inside a milestone about something else.*
- **Automatic closure of anything a human is working on** — no argument survives the creation/closure asymmetry.
- **Prediction anywhere** — a buying score is not a probability; no column, field, or event payload may imply otherwise. Guarded by invariant.
- **Commercial verdicts upstream of M5B** · **thresholds in rule, strategy, scoring, or qualification code** — guarded by syntax-tree invariants in M4, M5A, M5B and M6.
- **Per-workspace vocabulary types, postures, or stages** — configuration is relevance, weights and thresholds; the vocabularies and their meanings stay global. Per-workspace stages are a CRM concern, trigger M13.
- **Opportunity value, forecast, close date, notes, tasks, activities** — CRM features. M13 integrates with the system that owns them rather than rebuilding it.
- **Multiple concurrent opportunities per account** — real multi-product selling has them; the trigger is M13, where the external system's model becomes the constraint.
- **Cross-account ranking** · **learned weights or thresholds** · **score-derived alerting** · **inferred relevance** · **runtime-editable artifacts** (trigger: a non-engineer must tune without a release, realistically M12) · **fuzzy identity matching** · **person entities** · **manual merge UI (M12)** · **authentic provider payloads** · **cloud infrastructure (M14.5)** · **business UI (M12)**.

---

## 6 · Key documents

| Document | What it is for |
|---|---|
| **[21-intelligence-pipeline.md](architecture/21-intelligence-pipeline.md)** | **Read first.** The flagship reference: how a fact travels from raw provider payload to recommendation, what each stage adds, and what each stage is forbidden from doing. Written for engineers, architects, future hires, customers, and investors. Authored at the M3A boundary, as planned — after three stages existed, so it documents working software rather than projections. |
| [22-knowledge-graph.md](architecture/22-knowledge-graph.md) | The M3A design, marked **as built**, including four departures from the approved proposal and why each was forced. |
| [23-observation-engine.md](architecture/23-observation-engine.md) | The M3B design, marked **as built**. Contains the four evaluated architectures and why cross-provider observation series were rejected — the single most important rejection in the module. |
| [24-business-event-engine.md](architecture/24-business-event-engine.md) | The M4 design, marked **as built**. Contains the taxonomy/rules reasoning and what the CRO test changed before implementation. |
| [25-signal-engine.md](architecture/25-signal-engine.md) | The M5A design, marked **as built**. Contains the global-vs-workspace analysis and the ownership criterion for where configuration lives — the reasoning to reuse whenever a similar question arises. |
| [26-buying-score-engine.md](architecture/26-buying-score-engine.md) | The M5B design, marked **as built**. Contains the reduction analysis (*what is reduced · what stays recoverable · what must never be discarded*), the four-way decay evaluation and the reversal it produced, and three recorded departures. **Read the decay section before proposing any time-dependent artifact** — it generalises. |
| [27-opportunity-engine.md](architecture/27-opportunity-engine.md) | The M6 design, marked **as built**. Contains the intelligence-versus-workflow analysis, the three evaluated state models and why supersession was rejected, and the explicit answer to whether workflow outlives the intelligence that created it. **Read it before adding anything a human authors.** |
| [06-events.md](architecture/06-events.md) | The event catalog. `claim.recorded` and the five Knowledge Graph events are current as of M3A. |
| [05-module-dependencies.md](architecture/05-module-dependencies.md) | The dependency graph, and the read-port pattern for reading another module's data. |
| [04-modules.md](architecture/04-modules.md) | Module ownership and vocabulary. Provider Normalization and Knowledge Graph entries reflect what was actually built, not the v2 placeholders. |

---

## 7 · Next session starting point

### M12.1.5 — Playground v2, and why it interrupted the brief

**Read [docs/RUNNING.md](RUNNING.md) first** — it documents how to start the stack, seed twelve accounts, sign in, and reach `/opportunities` and the account brief without guessing. It also lists exactly what the demo showcases.

**The decision to carry forward:** *the demo dataset had become the constraint on product work.* Every account read "evidence expired"; the account whose story was *stale evidence* showed a fresh ledger. Design decisions, UX reviews and prompt evaluations were all being made against data that could not exercise them (D17).

`playground@2` fixes it — twelve recognisable companies, twelve invented business situations, anchored on today so freshness varies on its own. **`playground@1` is superseded, retained and unedited**: a published dataset is immutable, and every result recorded against it would otherwise become uncheckable.

#### The finding that outlives the dataset

Building it surfaced **three declared capabilities with no possible input**:

- Only Apollo claimed `LEGAL_NAME`, so the naming resolver's `AGREED` and `DISPUTED` — the states M12.2 built the product to display — could never occur.
- Neither Crunchbase nor CoreSignal offered a domain. A registry could reach an existing company only by naming it *identically*, so disagreeing produced a second company; and **every workforce fact resolved to a nameless entity of CoreSignal's own.** The account a seller could see and the account the hiring evidence described were two different rows.
- Crunchbase declared `acquisitions` in `known_fields` since M2.2 and never translated them, leaving `acquisition_announced`, `consolidation_underway` and its scoring weight dead at the source.

All three are fixed. **The class is the finding:** each passed every test it had, and none could run. A fixture set rich enough to demonstrate the product is the first thing that exercises every declared attribute end to end — so it belongs *before* the surfaces that depend on it.

### What comes next

1. **Citation resolution (J3)** — a ledger line and a narration sentence open to the fact beneath them. Both already carry `signal_id` and `business_event_id` on the wire and neither can be opened. **This is the largest remaining trust gap**: the brief's whole argument is *you can check this*, and the check stops one level short.
2. **Stage transitions and assignment (J4)** — and it forces **D23**, because an owner is a UUID with no read path to a person.
3. **The list slice** — Review 1's R1-01, R1-02, R1-05 and D20 are all about *which* account you pick, not what you do after. They belong together and not in M12.3.
4. **F-11 needs a ruling** before it can be fixed: the one-line change loosens a grounding check inside a frozen module.
5. **The Decision Package stays unbuilt** until `reasoning@1` earns a release.

### The thing M12.3 proved, which is worth more than the feature

**The answer to *"what should I do?"* was already in the repository.** `limitations` and `suggested_validation` have been in `signals@1.json` since M5A, versioned and reviewed like code, and nothing had ever displayed them. No model was needed, no new table, no new module — an interface layer over an artifact that already existed.

**Before reaching for new intelligence, check what the deterministic half already knows and has never been asked.** That is the second time in three slices this has paid: F-10 was fixed by generalising a principle the same file had already articulated.

### What this inherits

- **Three working endpoints** and the pattern to copy: `modules/*/interface/` with one `apps/api/composition/<surface>.py` per read surface — a shared composition module gives a router transitive dependencies on modules it never touches, and import-linter refuses it.
- **A frozen design system**, plus `components/intelligence/` for business vocabulary — the design system must never learn what a buying score is.
- **`make demo`** — a review environment that runs the real pipeline. Twelve accounts, all nine signal types, all four identity states, all three evidence states, none of them declared.
- **A certification command.** `make certify` records the gates; run it at the milestone boundary, not per commit.
- **Twenty design observations** in [38-product-design-principles.md](architecture/38-product-design-principles.md). D19 and D20 are the newest and both are product-visible.

### The habits worth keeping

**A refusal is a finding.** M10 stopped on a REFUSED prompt rather than tuning around it, and the investigation produced the Prompt Rendering Protocol, the certification framework, and a correction to ADR-0031's own prediction.

**A demo that flatters the product is worth nothing.** `playground@1` produced four qualified accounts of twelve and that was reported as the product working. It was partly a scoring artifact, and saying so is what produced M12.1.5.

**Build the data before the surface that depends on it.** Three capabilities were unreachable for months because nothing had ever asked them for a real answer.

**Say what is broken, prominently.** `reasoning@1` is unreleased and the dashboard says so in §1, §5, §7 and §10. A green certification is evidence the gates passed, never that the product is correct.

---

## Change log

| Date | Change |
|---|---|
| 2026-07-31 | v20 — **M10 T138: the research lifecycle closes.** retrieve → plan → execute → synthesise → store → publish, with `ai_research.completed` cataloged (closing **F-4**: `artifact_ref` and `model_provenance` were categories of field, not fields) and **smoke stage 14k**. **The synthesis is grounded against findings, not facts** — the narrator's evidence set holds one entry per finding, so it *cannot* reach past a finding to reinterpret the business event beneath, because that event is not in the set it was given. **Nothing is stored until everything succeeded**, proven by test: an unreleased synthesis prompt leaves no task row and no findings, rather than a run that found things and said nothing. **`research_synthesis@1` is REFUSED and stays unreleased** — one grounding failure, identical across three runs, where the model stripped the `research_finding:` prefix on one case and not the other. Not tuned around; it is ADR-0031's clearest instance yet. **R-09 is answered by measurement**: two model calls, 32.8 s + 20.8 s ≈ **54 s steady-state, ~70 s cold**, 0 retries in nine calls — and the shape matters more than the number, because the plan cannot name a derivation twice so the cost is two calls rather than *N*. Six mutations survived, all real: both synthesis validators were untested, the codec's `datetime` branch was unreachable from any current derivation, and nothing exercised re-saving a finding an earlier run had already established. |
| 2026-07-31 | v19 — **M10 T137: the first model call, and `research_planning@1` RELEASED** for `llama3.1:8b` after **eight consecutive passing runs** — 2 cases, 0 grounding failures, 0 schema failures, coverage 1.000. **M10 owns its own golden dataset** for a mechanical reason: the derivation catalog consumes `business_event` and `dissenting_signal`, M8's set holds neither, and every step a planner produced against it would be refused by its own schema. **R-09 is now half-measured and the half is recorded**: one planning call is **32.8 s median steady-state, 48.3 s cold**, ~890 in / ~200 out tokens, 0 retries — against a 60 s policy timeout, so the cold-start margin is real. A task timeout still cannot be set until synthesis exists. **`granite3.3:2b` was measured and REFUSED** on this prompt — 2 schema failures in each of three runs — which is a capability finding and the reason planning's certified model is not the reasoner's. **F-1 escalated to High**: three released prompts, two models, one registry slot, and at T137 it blocked a measurement rather than a request. The **plan-ordering question was settled from repository evidence** (A — preserve model output): `ai_reasoning.stated_reasoning` and `ai_narration.statements` both round-trip unordered, a materialized AI artifact is a historical fact, and canonicalisation buys nothing because a finding's identity sorts its citations. Two mutations survived and both were real: the request path could call `Infer.measure` and skip the release rule — the guarding invariant scanned only `modules/ai_platform`, now widened repository-wide — and my own T132 network-client invariant fired on the composition root, whose stated justification T137 disproved; narrowed to *a client may exist only in a file that hands it to the provider registry*, which still refuses a fetch client inside `evaluation/`. |
| 2026-07-31 | v18 — **M10 T136: the orchestrator, and three derivations that introduce no authority.** `CORROBORATION`, `DISSENT` and `RECENCY` are pure functions of the facts they are given — no clock, no database, no model, and **no threshold**: counting is a measurement, sufficiency is a judgement, and a judgement compiled into a comparison is a business rule nobody reviewed. Dissent reports the *set* of relevances present rather than a strongest one, because ordering a category is how a category becomes a score. **Type↔rule pairing is asserted at import**, both directions, the Business Event Engine's check applied here. **R-09 is deliberately still open**: a full plan over 35 facts runs in microseconds, measured — but the term that dominates a research task is the model call, no prompt exists until T137, and wrapping microseconds in a timeout would make the risk *look* addressed while the part that takes minutes stayed unmeasured. There is likewise **no step counter**: the plan reaching the orchestrator is already bounded by the catalog. Nine mutations; four survived and three of those were real — recency read *first fact* rather than *earliest* because every fixture was ascending, the orchestrator's use of a rule's version was invisible while every rule sits at version 1, and the import-time pairing call was untested because the tests invoked it directly. |
| 2026-07-31 | v17 — **M10 T135: the planner, and the module becomes agentic.** It answers one question — *which comparison is worth performing next?* — and **has nowhere to put an answer**: no field for a conclusion, `extra="forbid"`, so a model that answers rather than selects has its output refused. `DerivationType` is closed, and each member exists because retrieval already exposes what it needs. **Closure is not reimplemented**: a plan is a `GroundedOutput`, its targets *are* its reason's citations, and M8's `check()` already refuses a target the model was never shown — including an invented figure in the justification, which would otherwise sit in the audit trail as the reason work was done. **Two limits, neither a tuned number**: one step per derivation (so plan length is bounded by the catalog, not a constant), and **an empty plan is legal** — stopping is a planning answer, and an agent that cannot stop does not terminate. A draft called a plan INFERRED; corrected — a plan asserts nothing about the customer's world, so it is model-authored **operational history** like `ResearchTask`, and classifying machinery would make the epistemic ladder mean less. Seven mutations, all fatal. |
| 2026-07-31 | v16 — **M10 T134: internal retrieval.** `ResearchFactSource` in `domain/`, `OpportunityFactSource` over `opportunity_engine.public` — the module's only pipeline edge, and enough. **It defines no fact type of its own**: the AI Platform already publishes `EvidenceFact`, and a second shape for one idea would mean two canonical forms and eventually two digests. It emits only what M8's assembler omits — **business events**, which carry `corroborating_providers`, the one place provider agreement is visible and which nothing in the product surfaces; and **dissent**, which the buying score preserves through six stages and the assembler correctly drops. **Disjointness by kind is a Security Invariant**, because two modules emitting one kind would make a citation resolve to two different sentences. Per-fact helpers were written and discarded — annotating them required naming types that arrive *inside* another module's contract, so keeping the types flowing removed eight `type: ignore`s. **A contract hole was closed:** T131 omitted `modules.ai_platform.infrastructure` from M10's forbidden list, which M9 forbids; retrieval nearly reused M8's `assemble` through it. Six mutations, five fatal, one equivalent mutant identified and one control correctly surviving. |
| 2026-07-31 | v15 — **M10 T133: migration `0018`.** Three tables, **because there are three data categories** rather than three types — `research_task` is operational history, `research_finding` derived intelligence, `research_synthesis` a materialized AI artifact — and a pipeline rebuild treats each differently. No foreign key points anywhere, and the inward reason was not obvious: a finding's identity excludes its task, so `task_id` records the run that *first* derived it, and a CASCADE would erase facts a later run also produced. **Found while writing the test meant to prove a constraint fires: `array_length('{}', 1)` returns NULL, so `array_length(x, 1) >= 1` cannot reject an empty array.** Proven end to end — a `signal` citing no business events inserts successfully. Nine shipped constraints across five tables and six milestones carry the broken form; only `0018`'s two were repaired, with `cardinality()`. See [36-empty-array-checks.md](architecture/36-empty-array-checks.md). Five mutations run, all fatal after one was retried when its edit silently failed to apply. |
| 2026-07-31 | v14 — **M10 scope ruled: Internal Research**, and T131–T132 delivered. Two roadmap assumptions were tested against the repository and both failed — pgvector has no corpus to retrieve over, and every tool the architecture names is internal. The milestone shrank from ~12–16 ew to ~6–9, *as a consequence of correction rather than of cutting*, and **neither open product question blocks it**. T132 installed the three-way origin/identity split the Knowledge Contract's Rule 1 requires: a task mints (an act), a finding derives `uuid5` from content (a computation), a synthesis mints (a model call). **A finding has no free-text field** — because DERIVED describes how content was produced and promotion does not exist, the model plans which comparison to run and deterministic code computes the answer. **Rule 12 is enforced by absence:** a synthesis has no address, so no consumer can cite model-authored prose even deliberately. Eleven mutations run; two survived and both were real — a self-referential assertion that could not see its own constant change, and the same gap found still open in the Signal Engine. |
| 2026-07-31 | v13 — **M9 COMPLETE.** `reasoning@1` **released** against `granite3.3:2b` — 2 cases, 0 grounding failures, 0 schema failures, coverage 0.833, recorded after eight consecutive passing runs with **no change to the benchmark, dataset, rubric, schema, timeout or release criteria**. The assumption that M9 required a hosted model was **disproved by measurement**: the constraint was 4 GiB of VRAM, not reasoning capability — `llama3.1:8b` ran 58% on CPU and timed out, while a 1.9 GB model at 100% GPU passed eight times. On this hardware *stronger* means *larger* means *slower*. **[ADR-0031](architecture/adr/0031-evidence-citation-protocol.md) written and deliberately not implemented:** the renderer emits `[token]` while the parser accepts `token`, so three models were REFUSED for following *"cite by their exact reference strings"* literally — an **M8** defect that has been passing on one model's formatting habit since M8. `granite3.3:2b` is recorded as *currently certified*, not permanent. Full [M9 retrospective](architecture/30-m9-retrospective.md) written: nine stated assumptions proved false, five unreachable guards removed, eleven mutations run with six exposing real gaps. |
| 2026-07-30 | v12 — **M9 T130 complete; M9 implementation finished.** The Decision Package is now produced, stored and announced end to end: `AIReasoningModel`, `SqlDecisionPackageRepository`, the `PipelineReasoningContext` adapter, `build_reason`, `ai_reasoning.completed` cataloged, and **smoke stage 14j** (109 tests, no model call). **T128's architectural half closed:** both evaluation entry points route through `build_provider_registry`, and the Ollama-specific `/api/tags` probe was **removed** — it gated a hosted release run on a local runtime and was never what prevented a fake (composition is). A new Security Invariant enforces that the evaluation framework names no vendor in executable code, with prose exempt and a positive control. `reasoning@1` was run against `claude-sonnet-4-5` and returned **UNMEASURABLE — no adapter serves that model**, because no credential is configured; **no release was manufactured**, and a test now fails if one ever appears unearned. Four T130 findings, all from the repository refusing something: `public/` cannot publish a filesystem prompt loader (layering), `SignalQueries` already owned the catalog (parameter removed), `signora_app` cannot read `outbox_event` (relay identity used), and a redundant deduplication was deleted after a mutation showed it protected nothing. Eleven mutations run; six exposed real gaps and became permanent tests. 1563 tests, coverage 95.75%, 295 invariants, 25 contracts, smoke green over 22 stages. |
| 2026-07-30 | v11 — **M9 T122–T129 complete; T130 is the last task.** Records the three evaluation states (READY / REFUSED / UNMEASURABLE), `reasoning@1` authored and unreleased after an UNMEASURABLE local run, the ruling that release is earned against the hosted production model, and the T129 finding that **provider-neutral evaluation already exists** — `build_provider_registry` registers both vendors and `for_model` resolves without naming one, so only the eval entry points' hand-rolled registration needs routing through it. §7 rewritten for T130 with the full remaining work and the settled decisions that must not be re-opened. |
| 2026-07-30 | v10 — **ADR-0029 ratified and implemented; M8 architecturally closed with no findings outstanding.** Operational history commits on its own transaction — AC-69 now holds in production, not only in the domain. `ai_narration` keeps the caller's transaction, deliberately. A failed operational write is observable rather than silent. §7 now points at M9. |
| 2026-07-30 | v9 — **M8 complete.** T121 composes the validated platform: migration `0016` (`ai_narration`), the narration use case, `ai.narration_completed`, the composition root, and smoke stage 14i. Records the **fifth data category** — the materialized AI artifact — and the ruling that it is a historical fact rather than current truth, therefore immutable. §1 and §7 rewritten for M9. Superseded by v10. |
| 2026-07-30 | v8 — **M8 T111–T120 built; the evaluation harness run against a real model.** `explanation_narration@1` passed against `llama3.1:8b` (2 cases, 0 grounding failures, 0 schema failures, coverage 1.000) and is released for that model and refused for every other — the first objective AI-quality signal in the project. Records the rootless Ollama install this workstation needs, the two open harness gaps (retries not surfaced in the report; two structurally identical golden cases), and the observed cost (29.4 s cold load, 43–52 s per case, first call retried at the 60 s policy timeout). §1 and §7 rewritten: this file had been telling the next session to begin at T111, ten tasks after implementation actually started. |
| 2026-07-30 | v7.2 — **Pre-flight synchronization before T111.** Records **statelessness** as the AI Platform's second permanent principle — ratified in review but, until now, present only in conversation. Promotes [28-ai-platform.md](architecture/28-ai-platform.md) to **RATIFIED** and folds the confirmed decisions (module location, dependency direction, freeze-after-M10, Claude-only production adapter, one event, the binding stop condition) into its approval record. §1, §5 and §7 corrected: this file previously told the next session to *write* a proposal that already existed. `make smoke` and `make dr` now invoke through `bash` rather than the executable bit, which commit `0309193` had dropped. Coverage is quoted as **~95.3%** — the earlier "correction" to 95.25% was chasing ±0.02pp run-to-run noise, not fixing an error. |
| 2026-07-29 | v7.1 — **Local-First Development** adopted before M8 implementation ([ADR-0027](architecture/adr/0027-local-first-development.md), CLAUDE.md §20c-2 and the new *repository tells the truth* principle in §2). Actions disabled; three workflows retained at `workflow_dispatch`. The cross-tier JWT contract test moved into `make smoke` (stage 15b) and now **fails when skipped**. Corrected two pre-existing drifts: smoke has **21 stages, not 23**, and coverage measures **95.25%**. |
| 2026-07-29 | v7 — updated at the M6 boundary. Adds the **Commercial commitment** contract block (intelligence suggests, humans commit · three data categories · a rebuild regenerates intelligence only · opportunities outlive their score · workflow stores no intelligence · history never rewritten · the citation cannot be orphaned · every state names its actor and reason · dismissal distinct from a lost deal · four ownership layers). Rewrites §5 for M8, records the eighth `# type: ignore` and the application-enforced open-per-account rule, and notes that CLAUDE.md §19 now binds a **Milestone Definition of Done** ending in a pushed, clean tree. |
| 2026-07-29 | v6 — updated at the M5B boundary. Adds the **Commercial attention** contract block (prioritization never resolution · opposing readings never net · a score is a projection · the ledger is the score · the business event is the unit of contribution · step decay · evidence-derived staleness · three ownership layers · posture is Signora's · no signals, no score). Adds a **known limits** table distinguishing *limitation* from *debt*. Rewrites §5 for M6, records the sweep-scheduler consequence of the `EventHandler` finding, and keeps both platform findings as **queued RFCs**. |
| 2026-07-29 | v5 — updated at the M5A boundary. Adds the **Commercial meaning** contract block (the global/subjective boundary · ownership decides where configuration lives · the vocabulary stays global · no commercial verdict · contradiction preserved · composites enrich · hypotheses phrased as possibilities · two replay modes · customer-authored data is different). Rewrites §5 for M5B, keeps the two platform findings as **queued RFCs**, and records a fourth item of scheduled M2.0 simulation work. |
| 2026-07-29 | v4 — updated at the M4 boundary. Adds the **Business meaning** contract block (business relevance never commercial judgement · taxonomy is data, rules are code · no threshold in code · agreement is evidence · the taxonomy as a product asset · two versions never conflated). Rewrites §5 for M5A, keeps the two platform findings as **queued RFCs**, and records three items of scheduled M2.0 simulation work. |
| 2026-07-29 | v3 — updated at the M3B boundary. Adds the **Change** contract block (the layering principle, change-never-significance, per-provider series only, restraint, derived identity, refinement) and the shared-vocabulary contract. Rewrites §5 for M4, records the two platform findings as **queued RFCs** rather than obstacles, and lists the scheduled M2.0 simulation work. |
| 2026-07-29 | v2 — updated at the M3A boundary. Adds the **Knowledge** contract block (identity-never-truth, deterministic resolution, `MatchStrength` is never a number, ambiguity merges nothing, decisions explain themselves) and the module-boundary enforcement contract. Rewrites §5 for M3B, records **two open platform findings** and one scheduled fixture follow-up, and points §6 at [21-intelligence-pipeline.md](architecture/21-intelligence-pipeline.md) as the document to read first. |
| 2026-07-28 | v1 — created at the M2.2 boundary. Establishes the handoff document as the authoritative continuation point. |
