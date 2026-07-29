# Session Handoff — end of M4

> **Purpose:** start the next engineering session immediately, without reconstructing context.
> **Authoritative continuation point.** Updated at every milestone boundary.
> **As of:** 2026-07-29 · branch `main`
>
> Read this first. Then **[21-intelligence-pipeline.md](architecture/21-intelligence-pipeline.md)** — the flagship reference for how information moves through Signora — then [PROJECT_STATUS.md](../PROJECT_STATUS.md) §1–9 for the dashboard, and [IMPLEMENTATION_ROADMAP.md §5b](../IMPLEMENTATION_ROADMAP.md#5b-execution-sequence) for the execution order. Everything else is reference.

---

## 1 · Current project position

| | |
|---|---|
| **Last completed** | **M4 Business Event Engine** — closed 2026-07-29 |
| **Next** | **M5A Signal Engine** — architecture proposal not yet written |
| **Phase** | Product Pipeline. Foundations and enablement are complete and frozen. Five pipeline stages built. |
| **Overall completion** | **~41%** by engineering effort (~131 of ~261–339 ew) |
| **Remaining** | ~130–208 ew · ~1.3–1.9 years at 3 engineers, ~4.0–5.7 at 1 |
| **Completed milestones** | M0 · M1.1 · M1.2 · M1.3A · M1.4 · M1.5 · M2.0 · M2.1 · M2.2 · M3A · M3B · M4 |
| **Branch** | `main` |

**Recent commits:** M4 close (this change) · `2718272` M4 proposal · `e73c120` M3B closed · `719ca64` M3B proposal · `817c672` M3A closed

### Health

| Indicator | Value |
|---|---|
| Backend tests | **822 passing**, 0 failing, 0 skipped |
| Frontend tests | **101 passing** |
| Backend coverage | **95.39%** (CI gate 95%) |
| Security invariants | **154 / 154**, each proven to fail when its guarantee is removed |
| import-linter contracts | **11 kept, 0 broken** |
| `make smoke` | ✅ 20 stages, 71s |
| Migrations | 0000–0011, all reversible |
| mypy strict | Clean, 254 files |
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
| **Immutable tenant tables** | `claim`, `resolution_decision`, `observation`, and `business_event` are immutable. `signora_app` holds **no `UPDATE` grant** on any of them — an attempted overwrite fails with a permission error. `DELETE` remains, because all are derived and regeneration is the rollback for a broken mapper or rule. |
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
        ↓
Signal                🔄 M5A    ← NEXT: commercially meaningful — to us
        ↓
Buying Score          ⏳ M5B    continuous propensity
        ↓
Opportunity           ⏳ M6     ★ first sellable moment
        ↓
Timeline              ⏳ M7     the account narrative
        ↓
AI Reasoning          ⏳ M9     why, with evidence
        ↓
Recommendation        ⏳ M11    what to do next
```

**Five links exist and are verified against the live stack** (smoke stages 14b–14e). A simulated provider payload enters through the Provider Port, is stored raw, becomes canonical claims, is resolved to an entity whose decision explains itself, any change in what a provider asserts becomes an observation attributed to that provider, and a material change becomes a typed business event a CRO could read — *"Started using CloudERP"*, *"Raised 24M USD in a series b round"* — with no simulation-specific logic anywhere in that path.

Everything from M5A onward is unbuilt. See **[21-intelligence-pipeline.md](architecture/21-intelligence-pipeline.md)** for what each remaining stage adds and what it is forbidden from doing.

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

## 5 · M5A starting context

### What M5A inherits

**Input:** typed business events in Signora's business language. Through `modules.business_event_engine.public`:

- `BusinessEventQueries.business_events(workspace_id, entity_id, type_key=None, since=None)`
- `BusinessEventQueries.business_event_evidence(workspace_id, event_id)` → the event plus the observations behind it
- `BusinessEventQueries.history(workspace_id, event_id)` → the supersession chain, oldest first
- `BusinessEventQueries.taxonomy()` → the eleven types, their meanings, and their `why_it_matters` sentences

Each event carries `summary` (a sentence a CRO reads), `facts` (what the rule computed), `corroborating_providers`, `occurred_at` and its window, and `taxonomy_version`. Subscribe to `business_event.detected`; also handle `business_event.superseded`, or an extended phenomenon will be counted twice.

**Also available:** `knowledge_graph.public.GraphQueries` for entity context — relationships (`USES_TECHNOLOGY`, with `as_of`), claim sets, resolution history — which is what makes *"they run a competitor's stack"* expressible.

**Already exists and should be assumed:** event bus with platform-owned idempotency · forced RLS with `SECURITY DEFINER` predicates · `make smoke`, extensible with a stage (14b–14e) · the Tenant Isolation Policy — **register every new table in `tenancy_policy.py` or the build fails**.

**Expected output:** signals — weighted indicators of buying intent — consumed by the Buying Score Engine and Timeline.

### The central challenge

**M5A is the first module permitted to answer "should we engage?"**

Every module so far has refused it. M4 states what happened in business terms and stops; whether *"Acme is in a hiring surge"* is worth a seller's attention depends on who is selling, what they sell, and to whom — none of which any earlier module knows.

Two things M4 deliberately left on the table are M5A's to pick up:

- **Weighting corroboration.** M4 records *which* providers independently reached a conclusion. Turning that into confidence is a commercial rule.
- **Combining evidence across types.** A hiring surge plus buying intent on your category plus a competitor's technology is a different proposition from any one alone. That correlation is the module's whole value.

### Architectural questions worth raising before coding

1. **Is a signal per business event, or per correlation of several?** The interesting ones are correlations, and that changes identity, supersession, and volume all at once.
2. **Where does workspace-specific configuration live?** Unlike a business event, a signal is inherently *relative to the seller*. The taxonomy is global; signal weighting probably is not — and that is the first genuinely per-workspace configuration in the platform.
3. **Is scoring a rule or a model?** Deterministic rules have carried the pipeline this far. A learned model is defensible here but changes explainability fundamentally — and explainability is the product.
4. **How does a signal decay?** A hiring surge from eight months ago is weaker evidence than last week's. Decay is a rule that must be stated, not implied.
5. **What happens when a business event is superseded?** A signal built on the smaller view has to react. The precedent across four modules says supersede rather than mutate.
6. **Is a signal immutable?** `claim`, `resolution_decision`, `observation`, and `business_event` all are. Confirm that still holds when a signal's weight changes because its configuration changed.

### Two platform findings, open — RFCs queued

Both concern `signora_platform/`, which is frozen (CLAUDE.md §20a). **Neither is to be worked around inside a product milestone.** Product milestones consume platform capabilities; they do not redesign them.

| Finding | Effect | Resolution path |
|---|---|---|
| **`EventHandler` receives no session.** A handler must do its work in the *same transaction* as the dispatcher's idempotency claim, but the registry's signature is `(envelope) -> None`. | **No module handler is registered in the live registry.** The pipeline is exercised end to end through its real handlers in the integration suite and in `make smoke`, but the deployed worker consumes nothing. | RFC: **EventHandler transaction participation.** |
| **`PublishableEvent` cannot be satisfied by a frozen dataclass.** The Protocol declares settable members; every domain event is immutable, as the architecture requires. | Five modules now carry a `# type: ignore` at their publish site. | RFC: **PublishableEvent immutability compatibility.** |

### Carried forward from M4

- **AC-40 is partial.** Re-evaluation triggered by `observation.superseded` is wired at the contract level only — `citing_observations` and the replacement logic exist and are exercised. Closing the loop belongs with the first real late-arrival scenario.
- **Scheduled simulation work (M2.0), now three items.** A scenario with genuine multi-week movement · fixture enrichment so Crunchbase and CoreSignal carry a domain · an intent trajectory that sustains above the elevated threshold for enough weeks to produce a `BUYING_INTENT_SURGE`. All three are simulation artifacts, deliberately not edited mid-milestone.

### Deferred, and to stay deferred

- **Commercial judgement upstream of M5A** — no priority, score, or urgency in the Business Event Engine, guarded by a column-name invariant.
- **Thresholds in rule code** — guarded by a syntax-tree invariant over every rule module.
- **Materiality inside the Observation Engine** — guarded the same way.
- **Runtime-editable taxonomy** — trigger recorded: when a non-engineer must tune a threshold without a release, realistically M12.
- **Per-workspace taxonomy overrides** — a large change touching identity, replay, and review at once. No customer has asked.
- **`TECHNOLOGY_MIGRATION`** — a correlation between two *business events*, not between observations. A candidate for M5A rather than M4.
- **Cross-provider consensus observations** — no consumer has asked; if M5A demonstrates it needs one, that is the evidence.
- **Confidence scoring anywhere before M5A** — `MatchStrength` is not this and must never become it.
- **Fuzzy / probabilistic identity matching** · **resolved-value projections** · **person entities** · **manual merge UI (M12)** · **authentic provider payloads** · **cloud infrastructure (M14.5)** · **business UI (M12)**.

---

## 6 · Key documents

| Document | What it is for |
|---|---|
| **[21-intelligence-pipeline.md](architecture/21-intelligence-pipeline.md)** | **Read first.** The flagship reference: how a fact travels from raw provider payload to recommendation, what each stage adds, and what each stage is forbidden from doing. Written for engineers, architects, future hires, customers, and investors. Authored at the M3A boundary, as planned — after three stages existed, so it documents working software rather than projections. |
| [22-knowledge-graph.md](architecture/22-knowledge-graph.md) | The M3A design, marked **as built**, including four departures from the approved proposal and why each was forced. |
| [23-observation-engine.md](architecture/23-observation-engine.md) | The M3B design, marked **as built**. Contains the four evaluated architectures and why cross-provider observation series were rejected — the single most important rejection in the module. |
| [24-business-event-engine.md](architecture/24-business-event-engine.md) | The M4 design, marked **as built**. Contains the taxonomy/rules reasoning and what the CRO test changed before implementation. |
| [06-events.md](architecture/06-events.md) | The event catalog. `claim.recorded` and the five Knowledge Graph events are current as of M3A. |
| [05-module-dependencies.md](architecture/05-module-dependencies.md) | The dependency graph, and the read-port pattern for reading another module's data. |
| [04-modules.md](architecture/04-modules.md) | Module ownership and vocabulary. Provider Normalization and Knowledge Graph entries reflect what was actually built, not the v2 placeholders. |

---

## 7 · Next session starting point

> **Completed:** M4 Business Event Engine · **Next:** M5A Signal Engine
> **Branch:** `main` · everything committed, tree clean
> **Health:** 822 backend + 101 frontend tests passing · coverage 95.39% · 154 invariants · 11 contracts · smoke green over 20 stages
>
> **First actions:**
> 1. Read [21-intelligence-pipeline.md](architecture/21-intelligence-pipeline.md) — it is the shortest path to full context, and it tracks what is *built* rather than intended.
> 2. Verify the tree is clean and `make smoke` is green.
> 3. Prepare the **M5A architecture proposal** before any implementation, following the M3A/M3B/M4 pattern: domain model, evaluated alternatives with a recommendation, storage, events, module API, task breakdown, acceptance criteria, demonstration, DoD, rollback, operational readiness, risks. **Wait for approval.**
>
> **Settle these inside the proposal, not during implementation:** signal per event or per correlation · where per-workspace configuration lives · scoring as rule or model · decay · reaction to a superseded business event · immutability under a configuration change.
>
> **Raise, do not work around:** the two platform findings in §5 are **RFC work items**, not obstacles to route around inside a product milestone. Product milestones consume platform capabilities; they do not redesign them.
>
> **Do not:** reimplement anything in §2 · introduce mock business data · add a canonical attribute or a business event type without review · store a resolved attribute value in the Knowledge Graph · turn `MatchStrength` into a number · put a materiality threshold in the Observation Engine · put a business threshold in rule code rather than the taxonomy · put commercial judgement in the Business Event Engine · modify `signora_platform/` or the frontend foundation without a qualifying reason.

---

## Change log

| Date | Change |
|---|---|
| 2026-07-29 | v4 — updated at the M4 boundary. Adds the **Business meaning** contract block (business relevance never commercial judgement · taxonomy is data, rules are code · no threshold in code · agreement is evidence · the taxonomy as a product asset · two versions never conflated). Rewrites §5 for M5A, keeps the two platform findings as **queued RFCs**, and records three items of scheduled M2.0 simulation work. |
| 2026-07-29 | v3 — updated at the M3B boundary. Adds the **Change** contract block (the layering principle, change-never-significance, per-provider series only, restraint, derived identity, refinement) and the shared-vocabulary contract. Rewrites §5 for M4, records the two platform findings as **queued RFCs** rather than obstacles, and lists the scheduled M2.0 simulation work. |
| 2026-07-29 | v2 — updated at the M3A boundary. Adds the **Knowledge** contract block (identity-never-truth, deterministic resolution, `MatchStrength` is never a number, ambiguity merges nothing, decisions explain themselves) and the module-boundary enforcement contract. Rewrites §5 for M3B, records **two open platform findings** and one scheduled fixture follow-up, and points §6 at [21-intelligence-pipeline.md](architecture/21-intelligence-pipeline.md) as the document to read first. |
| 2026-07-28 | v1 — created at the M2.2 boundary. Establishes the handoff document as the authoritative continuation point. |
