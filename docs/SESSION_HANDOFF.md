# Session Handoff — end of M5A

> **Purpose:** start the next engineering session immediately, without reconstructing context.
> **Authoritative continuation point.** Updated at every milestone boundary.
> **As of:** 2026-07-29 · branch `main`
>
> Read this first. Then **[21-intelligence-pipeline.md](architecture/21-intelligence-pipeline.md)** — the flagship reference for how information moves through Signora — then [PROJECT_STATUS.md](../PROJECT_STATUS.md) §1–9 for the dashboard, and [IMPLEMENTATION_ROADMAP.md §5b](../IMPLEMENTATION_ROADMAP.md#5b-execution-sequence) for the execution order. Everything else is reference.

---

## 1 · Current project position

| | |
|---|---|
| **Last completed** | **M5A Signal Engine** — closed 2026-07-29 |
| **Next** | **M5B Buying Score Engine** — architecture proposal not yet written |
| **Phase** | Product Pipeline. Foundations and enablement are complete and frozen. Six pipeline stages built. |
| **Overall completion** | **~45%** by engineering effort (~142 of ~261–339 ew) |
| **Remaining** | ~119–197 ew · ~1.2–1.8 years at 3 engineers, ~3.7–5.3 at 1 |
| **Completed milestones** | M0 · M1.1 · M1.2 · M1.3A · M1.4 · M1.5 · M2.0 · M2.1 · M2.2 · M3A · M3B · M4 · M5A |
| **Branch** | `main` |

**Recent commits:** M5A close (this change) · `cde2218` M5A proposal · `026a2fa` M4 closed · `2718272` M4 proposal · `e73c120` M3B closed

### Health

| Indicator | Value |
|---|---|
| Backend tests | **905 passing**, 0 failing, 0 skipped |
| Frontend tests | **101 passing** |
| Backend coverage | **95.50%** (CI gate 95%) |
| Security invariants | **186 / 186**, each proven to fail when its guarantee is removed |
| import-linter contracts | **13 kept, 0 broken** |
| `make smoke` | ✅ 21 stages, 76s |
| Migrations | 0000–0012, all reversible |
| mypy strict | Clean, 278 files |
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
| **Platform Freeze** | M1.3A | `signora_platform/` changes only for a security fix, production defect, or approved change. **One change since:** the relay's transient-failure handling. |
| **Frontend Foundation** | M1.5 | Design system, components, shell, routing, query layer — consumed, not modified. Exceptions: production defect, **accessibility issue**, security issue, approved change. |

### Tenancy and data

| Contract | What it guarantees |
|---|---|
| **Tenant Isolation Policy** | Every table declared tenant-owned or platform infrastructure — **classification is never inferred**. Tenant tables carry a non-null identifier, RLS enabled **and forced**, and policies covering SELECT/INSERT/UPDATE separately. A table in neither list fails the build. |
| **Migration / runtime credential separation** | Runtime services never execute under migration or owner credentials. Each tier holds its own least-privileged role: `signora_app` (API, workers), `signora_auth` (frontend), `signora_relay` (outbox), owner (migrations only). |
| **Platform Infrastructure Policy** | `outbox_event`, `processed_event`, `dead_letter_event`, `alembic_version` are owned by platform services. The application **publishes and cannot read**; only the relay consumes. Isolation is by grant, since these tables span workspaces and have no RLS. |
| **Immutable tenant tables** | `claim`, `resolution_decision`, `observation`, `business_event`, `signal`, and `signal_profile` are immutable. `signora_app` holds **no `UPDATE` grant** on any of them — an attempted overwrite fails with a permission error. `DELETE` remains, because all are derived and regeneration is the rollback for a broken mapper or rule. |
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
        ↓
Buying Score          🔄 M5B    ← NEXT: how much it matters, overall
        ↓
Opportunity           ⏳ M6     ★ first sellable moment
        ↓
Timeline              ⏳ M7     the account narrative
        ↓
AI Reasoning          ⏳ M9     why, with evidence
        ↓
Recommendation        ⏳ M11    what to do next
```

**Six links exist and are verified against the live stack** (smoke stages 14b–14f). A simulated provider payload enters through the Provider Port, is stored raw, becomes canonical claims, is resolved to an entity whose decision explains itself, any change in what a provider asserts becomes an observation attributed to that provider, and a material change becomes a typed business event a CRO could read — *"Started using CloudERP"*, *"Raised 24M USD in a series b round"* — and, for a workspace that says it cares, that event becomes a commercial hypothesis with its own two-part explanation. No simulation-specific logic exists anywhere in that path.

Everything from M5B onward is unbuilt. See **[21-intelligence-pipeline.md](architecture/21-intelligence-pipeline.md)** for what each remaining stage adds and what it is forbidden from doing.

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

## 5 · M5B starting context

### What M5B inherits

**Input:** commercial hypotheses, already interpreted for this workspace. Through `modules.signal_engine.public`:

- `SignalQueries.signals(workspace_id, entity_id, signal_type=None, live_only=True)` — `live_only` applies all three ways a hypothesis stops being current: superseded, past its shelf life, or of a type the workspace no longer holds
- `SignalQueries.explanation(workspace_id, signal_id)` — the signal, its definition, the profile entry that made it relevant, the business events behind it, and the constituents it enriches
- `SignalQueries.history(...)` · `SignalQueries.profile(...)` · `SignalQueries.catalog()`

Each signal carries `relevance` (a category), `occurred_at`, `relevant_until`, `rationale`, `contributing_event_ids`, `contributing_event_types`, `constituent_signal_ids`, and both versions. Subscribe to `signal.generated`; also handle `signal.superseded`, or a strengthened hypothesis will be counted twice.

**Also available:** `BusinessEventQueries` for the facts underneath, and `GraphQueries` for entity context.

**Already exists and should be assumed:** event bus with platform-owned idempotency · forced RLS · `make smoke`, extensible with a stage (14b–14f) · the Tenant Isolation Policy — **register every new table in `tenancy_policy.py` or the build fails**.

### The central challenge

**M5B is the first module permitted to answer "how much does this matter?"**

M5A contains no scores at all, by design. Three things it deliberately left on the table are M5B's to pick up, and each is a stated, reviewable rule rather than an implementation detail:

1. **Weighting relevance categories.** `PRIMARY`/`SUPPORTING`/`CONTEXTUAL` is an ordinal the Signal Engine refuses to turn into a number. M5B must, and where that mapping lives is the same ownership question M5A answered — probably the customer's, alongside the profile.
2. **Resolving contradiction.** A `CONTRACTION_RISK` and an `EXPANSION_OPPORTUNITY` can be live for one account. Every module so far has preserved that; **M5B is the first that must produce a single number anyway.** How it does so is the most consequential decision in the milestone.
3. **Applying decay.** A signal declares `relevant_until`; how much a hypothesis is worth *within* that window, as it ages, is propensity.

**One requirement recorded during M5A:** deduplicate on contributing **business events**, not on signals. A composite and its constituent rest on the same grounds read two ways, and counting both would double-count the evidence.

### Architectural questions worth raising before coding

1. **Where does the weighting configuration live?** Following the ownership criterion, probably with the customer — which would make it the second customer-authored table, and raise whether it belongs *in* the signal profile or beside it.
2. **How is contradiction resolved, and is the resolution explainable?** A number that silently nets an expansion signal against a contraction one is unexplainable. Whatever the rule, a customer must be able to see it.
3. **Is a score a stored artifact or a projection?** It changes continuously as signals expire — a stored score is stale the moment the clock moves, and a projection cannot publish `buying_score.updated`.
4. **What does trend mean, and over what window?** The v2 catalog gives `buying_score.updated` a `trend`. Deriving it needs score history, which is a design decision about storing scores at all.
5. **Is a score immutable?** The precedent across six tables says yes, with append-only history. Confirm it survives a configuration change and continuous decay.
6. **Does M5B need entity context, or only signals?** Account fit — *"does this look like our customers?"* — was deferred out of M5A. If it belongs anywhere it is here or M6, and it should be settled deliberately.

### Two platform findings, open — RFCs queued

Both concern `signora_platform/`, which is frozen (CLAUDE.md §20a). **Neither is to be worked around inside a product milestone.**

| Finding | Effect | Resolution path |
|---|---|---|
| **`EventHandler` receives no session.** A handler must work in the *same transaction* as the dispatcher's idempotency claim, but the registry's signature is `(envelope) -> None`. | **No module handler is registered in the live registry.** The pipeline is exercised end to end through its real handlers in the integration suite and `make smoke`, but the deployed worker consumes nothing. | RFC: **EventHandler transaction participation.** |
| **`PublishableEvent` cannot be satisfied by a frozen dataclass.** | Six modules now carry a `# type: ignore` at their publish site. | RFC: **PublishableEvent immutability compatibility.** |

### Carried forward

- **AC-40 (M4) is partial.** Re-evaluation triggered by `observation.superseded` is wired at contract level only; `citing_observations` and the replacement logic exist and are exercised.
- **Scheduled simulation work (M2.0), now four items.** A scenario with genuine multi-week movement · fixture enrichment so Crunchbase and CoreSignal carry a domain · an intent trajectory sustaining above the elevated threshold for enough weeks · **evidence recent enough that signals are still within their shelf life**, so the live-set path is exercised positively rather than only by its absence.

### Deferred, and to stay deferred

- **Commercial verdicts upstream of M5B** — no score, priority, or likelihood in the Signal Engine, guarded by a column-name invariant.
- **Thresholds in rule or strategy code** — guarded by syntax-tree invariants in both M4 and M5A.
- **Per-workspace signal or business event *types*** — configuration is relevance only; the vocabularies stay global.
- **Inferred relevance** — a good idea with no behaviour to learn from yet. The sequencing is explicit profiles first, with inference later *proposing* changes a human accepts.
- **ICP / account-fit filtering** — deferred out of M5A; settle its home in M5B or M6.
- **Runtime-editable taxonomy / catalog** — trigger recorded: when a non-engineer must tune without a release, realistically M12.
- **`signal_profile.updated`** — M5B may want it; adding it before a consumer exists would be a contract nobody keeps.
- **Confidence scoring before M5B** · **fuzzy identity matching** · **resolved-value projections** · **person entities** · **manual merge UI (M12)** · **authentic provider payloads** · **cloud infrastructure (M14.5)** · **business UI (M12)**.

---

## 6 · Key documents

| Document | What it is for |
|---|---|
| **[21-intelligence-pipeline.md](architecture/21-intelligence-pipeline.md)** | **Read first.** The flagship reference: how a fact travels from raw provider payload to recommendation, what each stage adds, and what each stage is forbidden from doing. Written for engineers, architects, future hires, customers, and investors. Authored at the M3A boundary, as planned — after three stages existed, so it documents working software rather than projections. |
| [22-knowledge-graph.md](architecture/22-knowledge-graph.md) | The M3A design, marked **as built**, including four departures from the approved proposal and why each was forced. |
| [23-observation-engine.md](architecture/23-observation-engine.md) | The M3B design, marked **as built**. Contains the four evaluated architectures and why cross-provider observation series were rejected — the single most important rejection in the module. |
| [24-business-event-engine.md](architecture/24-business-event-engine.md) | The M4 design, marked **as built**. Contains the taxonomy/rules reasoning and what the CRO test changed before implementation. |
| [25-signal-engine.md](architecture/25-signal-engine.md) | The M5A design, marked **as built**. Contains the global-vs-workspace analysis and the ownership criterion for where configuration lives — the reasoning to reuse whenever a similar question arises. |
| [06-events.md](architecture/06-events.md) | The event catalog. `claim.recorded` and the five Knowledge Graph events are current as of M3A. |
| [05-module-dependencies.md](architecture/05-module-dependencies.md) | The dependency graph, and the read-port pattern for reading another module's data. |
| [04-modules.md](architecture/04-modules.md) | Module ownership and vocabulary. Provider Normalization and Knowledge Graph entries reflect what was actually built, not the v2 placeholders. |

---

## 7 · Next session starting point

> **Completed:** M5A Signal Engine · **Next:** M5B Buying Score Engine
> **Branch:** `main` · everything committed and pushed, tree clean
> **Health:** 905 backend + 101 frontend tests passing · coverage 95.50% · 186 invariants · 13 contracts · smoke green over 21 stages
>
> **First actions:**
> 1. Read [21-intelligence-pipeline.md](architecture/21-intelligence-pipeline.md) — it is the shortest path to full context, and it tracks what is *built* rather than intended.
> 2. Verify the tree is clean and `make smoke` is green.
> 3. Prepare the **M5B architecture proposal** before any implementation, following the established pattern: domain model, evaluated alternatives with a recommendation, storage, events, module API, task breakdown, acceptance criteria, demonstration, DoD, rollback, operational readiness, risks. **Wait for approval.**
>
> **Settle these inside the proposal, not during implementation:** where weighting configuration lives · how contradiction is resolved *explainably* · stored score vs projection · what trend means · immutability under continuous decay · whether account fit belongs here.
>
> **Raise, do not work around:** the two platform findings in §5 are **RFC work items**, not obstacles to route around inside a product milestone. Product milestones consume platform capabilities; they do not redesign them.
>
> **Do not:** reimplement anything in §2 · introduce mock business data · add a canonical attribute, business event type, or signal type without review · store a resolved attribute value in the Knowledge Graph · turn `MatchStrength` or `Relevance` into a number · put a materiality threshold in the Observation Engine · put a business threshold in rule or strategy code rather than in the taxonomy or catalog · put commercial judgement in the Business Event Engine · put a commercial verdict in the Signal Engine · let a workspace invent a vocabulary type · modify `signora_platform/` or the frontend foundation without a qualifying reason.

---

## Change log

| Date | Change |
|---|---|
| 2026-07-29 | v5 — updated at the M5A boundary. Adds the **Commercial meaning** contract block (the global/subjective boundary · ownership decides where configuration lives · the vocabulary stays global · no commercial verdict · contradiction preserved · composites enrich · hypotheses phrased as possibilities · two replay modes · customer-authored data is different). Rewrites §5 for M5B, keeps the two platform findings as **queued RFCs**, and records a fourth item of scheduled M2.0 simulation work. |
| 2026-07-29 | v4 — updated at the M4 boundary. Adds the **Business meaning** contract block (business relevance never commercial judgement · taxonomy is data, rules are code · no threshold in code · agreement is evidence · the taxonomy as a product asset · two versions never conflated). Rewrites §5 for M5A, keeps the two platform findings as **queued RFCs**, and records three items of scheduled M2.0 simulation work. |
| 2026-07-29 | v3 — updated at the M3B boundary. Adds the **Change** contract block (the layering principle, change-never-significance, per-provider series only, restraint, derived identity, refinement) and the shared-vocabulary contract. Rewrites §5 for M4, records the two platform findings as **queued RFCs** rather than obstacles, and lists the scheduled M2.0 simulation work. |
| 2026-07-29 | v2 — updated at the M3A boundary. Adds the **Knowledge** contract block (identity-never-truth, deterministic resolution, `MatchStrength` is never a number, ambiguity merges nothing, decisions explain themselves) and the module-boundary enforcement contract. Rewrites §5 for M3B, records **two open platform findings** and one scheduled fixture follow-up, and points §6 at [21-intelligence-pipeline.md](architecture/21-intelligence-pipeline.md) as the document to read first. |
| 2026-07-28 | v1 — created at the M2.2 boundary. Establishes the handoff document as the authoritative continuation point. |
