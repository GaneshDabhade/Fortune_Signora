# Session Handoff — end of M3B

> **Purpose:** start the next engineering session immediately, without reconstructing context.
> **Authoritative continuation point.** Updated at every milestone boundary.
> **As of:** 2026-07-29 · branch `main`
>
> Read this first. Then **[21-intelligence-pipeline.md](architecture/21-intelligence-pipeline.md)** — the flagship reference for how information moves through Signora — then [PROJECT_STATUS.md](../PROJECT_STATUS.md) §1–9 for the dashboard, and [IMPLEMENTATION_ROADMAP.md §5b](../IMPLEMENTATION_ROADMAP.md#5b-execution-sequence) for the execution order. Everything else is reference.

---

## 1 · Current project position

| | |
|---|---|
| **Last completed** | **M3B Observation Engine** — closed 2026-07-29 |
| **Next** | **M4 Business Event Engine** — architecture proposal not yet written |
| **Phase** | Product Pipeline. Foundations and enablement are complete and frozen. Four pipeline stages built. |
| **Overall completion** | **~37%** by engineering effort (~119 of ~261–339 ew) |
| **Remaining** | ~142–220 ew · ~1.4–2.1 years at 3 engineers, ~4.4–6.2 at 1 |
| **Completed milestones** | M0 · M1.1 · M1.2 · M1.3A · M1.4 · M1.5 · M2.0 · M2.1 · M2.2 · M3A · M3B |
| **Branch** | `main` |

**Recent commits:** M3B close (this change) · `719ca64` M3B proposal · `817c672` M3A closed · `ae1c0be` identity domain and rule engine · `9981d72` M3A proposal

### Health

| Indicator | Value |
|---|---|
| Backend tests | **729 passing**, 0 failing, 0 skipped |
| Frontend tests | **101 passing** |
| Backend coverage | **95.10%** (CI gate 95%) |
| Security invariants | **124 / 124**, each proven to fail when its guarantee is removed |
| import-linter contracts | **9 kept, 0 broken** |
| `make smoke` | ✅ 19 stages, 69s |
| Migrations | 0000–0010, all reversible |
| mypy strict | Clean, 227 files |
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
| **Immutable tenant tables** | `claim`, `resolution_decision`, and `observation` are immutable. `signora_app` holds **no `UPDATE` grant** on any of them — an attempted overwrite fails with a permission error. `DELETE` remains, because all are derived and regeneration is the rollback for a broken mapper or rule. |
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
Business Event        🔄 M4     ← NEXT: what it means — funding, hiring surge, migration
        ↓
Signal                ⏳ M5A    commercially meaningful
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

**Four links exist and are verified against the live stack** (smoke stages 14b, 14c, 14d). A simulated provider payload enters through the Provider Port, is stored raw, becomes canonical claims, is resolved to an entity whose decision explains itself, and any change in what a provider asserts becomes an observation attributed to that provider — with no simulation-specific logic anywhere in that path.

Everything from M4 onward is unbuilt. See **[21-intelligence-pipeline.md](architecture/21-intelligence-pipeline.md)** for what each remaining stage adds and what it is forbidden from doing.

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

## 5 · M4 starting context

### What M4 inherits

**Input:** observations — *this changed, by this much, between these times, according to this provider*. Through `modules.observation_engine.public`:

- `ObservationQueries.observations(workspace_id, entity_id, attribute=None, since=None)`
- `ObservationQueries.series(workspace_id, entity_id, provider, attribute)` — one provider's changes to one attribute, oldest first
- `ObservationQueries.observation_evidence(workspace_id, observation_id)` — the observation plus the claims behind it, for citation and export

Each observation carries **previous value, current value, direction, magnitude, provider, observed window, and entity** — everything needed to reason directly, without reconstructing transitions from claim history. Subscribe to `observation.recorded`; also handle `observation.superseded`, or a refined observation will be counted twice.

**Also available:** `knowledge_graph.public.GraphQueries` for entity context (claim sets, relationships, `as_of`), and the canonical vocabulary from `provider_normalization.public`.

**Already exists and should be assumed:**
- Event bus with platform-owned idempotency — do not reimplement
- RLS, forced, with `SECURITY DEFINER` predicates — new tables inherit the pattern
- `make smoke`, extensible with a stage (14b ingestion+normalization, 14c identity resolution, 14d change detection)
- The Tenant Isolation Policy — **register every new table in `tenancy_policy.py` or the build fails**

**Expected output:** business events, typed against a curated taxonomy, consumed by the Signal Engine and Timeline.

### The central challenge

**M4 is the first module that decides what matters.**

Every module so far has deliberately refused that. M3B computes magnitude, direction, duration, and provider attribution and stops — because materiality is not a property of a change, it is a property of a change *in a commercial context*: a headcount move of five is noise at Acme and a signal at a 12-person startup.

So the threshold lives here, and the design question is **where exactly it lives**. A constant in detection code is unversioned, untestable against a taxonomy, and invisible in the evidence chain; a seller asking *"why was I told this?"* would get an answer that bottoms out in a magic number. A curated, versioned taxonomy makes the rule reviewable — and makes *"this is a hiring surge because growth exceeded the threshold for this segment"* a sentence with an argument in the middle of it.

### Architectural questions worth raising before coding

1. **Is the taxonomy data or code?** A versioned artifact reviewed like a prompt template, or Python with tests? Both are defensible; the choice decides who can change a threshold and how it is audited.
2. **Does a business event cite observations, or subsume them?** Citation preserves the chain; subsumption is convenient and lossy.
3. **How many observations make one business event?** *"Sustained hiring growth"* spans several. That means a business event has a window, and possibly needs re-evaluation as new observations arrive.
4. **How does corroboration work?** Two providers independently reporting growth is stronger evidence. M3B deliberately kept their series separate; M4 is the first module with the context to weigh them — but consensus is a rule that should be stated, not implied.
5. **What happens when an observation is superseded?** A business event built on the coarser observation has to react. Confirm rather than assume.
6. **Is a business event immutable?** The precedent across `claim`, `resolution_decision`, and `observation` says yes, with append-only correction — confirm it still holds when a taxonomy version changes.

### Two platform findings, open — RFCs queued

Both concern `signora_platform/`, which is frozen (CLAUDE.md §20a). **Neither is to be worked around inside a product milestone.** RFCs are to be prepared at the appropriate platform milestone.

| Finding | Effect | Resolution path |
|---|---|---|
| **`EventHandler` receives no session.** The registry's signature is `(envelope) -> None`, but a handler must do its work in the *same transaction* as the dispatcher's idempotency claim — opening its own session would break exactly-once, the guarantee the whole bus is built on. | **No module handler is registered in the live registry.** The pipeline is exercised end to end through its real handlers in the integration suite and in `make smoke`, but the deployed worker consumes nothing. | RFC: **EventHandler transaction participation.** |
| **`PublishableEvent` cannot be satisfied by a frozen dataclass.** The Protocol declares settable members; every domain event is immutable, as the architecture requires. | Four modules now carry a `# type: ignore` at their publish site. | RFC: **PublishableEvent immutability compatibility.** |

### Scheduled simulation work (M2.0)

Both are simulation artifacts, deliberately not edited mid-milestone:

- **A scenario with genuine multi-week movement.** The baseline reports each subject once per provider, so it contains occurrences but no *transitions*. M3B's negative assertions run through the real pipeline; the positive case is constructed explicitly in its demonstration.
- **Fixture enrichment.** Crunchbase and CoreSignal fixtures carry no domain, so those providers cannot resolve to the same entity as Apollo/BuiltWith/Bombora. The rules are correct; the fixtures are impoverished. Real payloads from both vendors carry a website.

### Deferred, and to stay deferred

- **Materiality inside the Observation Engine** — it belongs to M4, in a taxonomy. Adding a threshold to M3B is guarded by a Security Invariant that reads its source as a syntax tree.
- **Cross-provider consensus observations** — no consumer has asked. If M4 or M5A demonstrates it needs one, *that* is the evidence, and the rule will be knowable by then.
- **Trend and velocity derivation** — interpretation over a series; the Signal Engine has the context.
- **Confidence scoring** — belongs to modules with enough context to justify it. `MatchStrength` is not this and must never become it.
- **Fuzzy / probabilistic identity matching** — a hidden heuristic. `entity.resolution_ambiguous` volume is the evidence that would justify it.
- **Resolved-value projections in the graph** — no consumer has asked for one.
- **Person entities** — claims carry role changes but no person *identifier*; adding people now means inventing one.
- **Manual merge/unmerge UI** — M12; `entity.superseded` waits for it.
- **Authentic provider payloads** — all five remain `Conditional`; replacement is a one-file change per provider.
- **Bombora's history question** — when an authentic payload arrives, establish whether the provider supplies weekly history *directly* or the platform must *accumulate* it.
- **Cloud infrastructure** — M14.5, immediately before GA.
- **Business UI** — M12, against real domain contracts.

---

## 6 · Key documents

| Document | What it is for |
|---|---|
| **[21-intelligence-pipeline.md](architecture/21-intelligence-pipeline.md)** | **Read first.** The flagship reference: how a fact travels from raw provider payload to recommendation, what each stage adds, and what each stage is forbidden from doing. Written for engineers, architects, future hires, customers, and investors. Authored at the M3A boundary, as planned — after three stages existed, so it documents working software rather than projections. |
| [22-knowledge-graph.md](architecture/22-knowledge-graph.md) | The M3A design, marked **as built**, including four departures from the approved proposal and why each was forced. |
| [23-observation-engine.md](architecture/23-observation-engine.md) | The M3B design, marked **as built**. Contains the four evaluated architectures and why cross-provider observation series were rejected — the single most important rejection in the module. |
| [06-events.md](architecture/06-events.md) | The event catalog. `claim.recorded` and the five Knowledge Graph events are current as of M3A. |
| [05-module-dependencies.md](architecture/05-module-dependencies.md) | The dependency graph, and the read-port pattern for reading another module's data. |
| [04-modules.md](architecture/04-modules.md) | Module ownership and vocabulary. Provider Normalization and Knowledge Graph entries reflect what was actually built, not the v2 placeholders. |

---

## 7 · Next session starting point

> **Completed:** M3B Observation Engine · **Next:** M4 Business Event Engine
> **Branch:** `main` · everything committed, tree clean
> **Health:** 729 backend + 101 frontend tests passing · coverage 95.10% · 124 invariants · 9 contracts · smoke green over 19 stages
>
> **First actions:**
> 1. Read [21-intelligence-pipeline.md](architecture/21-intelligence-pipeline.md) — it is the shortest path to full context, and it tracks what is *built* rather than intended.
> 2. Verify the tree is clean and `make smoke` is green.
> 3. Prepare the **M4 architecture proposal** before any implementation, following the M3A/M3B pattern: domain model, evaluated alternatives with a recommendation, storage, events, module API, task breakdown, acceptance criteria, demonstration, DoD, rollback, operational readiness, risks. **Wait for approval.**
>
> **Settle these inside the proposal, not during implementation:** taxonomy as data or code · citation vs subsumption of observations · multi-observation events and their windows · corroboration across providers · reaction to a superseded observation · immutability under a taxonomy version change.
>
> **Raise, do not work around:** the two platform findings in §5 are **RFC work items**, not obstacles to route around inside a product milestone. Product milestones consume platform capabilities; they do not redesign them.
>
> **Do not:** reimplement anything in §2 · introduce mock business data · add a canonical attribute without an RFC · store a resolved attribute value in the Knowledge Graph · turn `MatchStrength` into a number · put a materiality threshold in the Observation Engine · modify `signora_platform/` or the frontend foundation without a qualifying reason.

---

## Change log

| Date | Change |
|---|---|
| 2026-07-29 | v3 — updated at the M3B boundary. Adds the **Change** contract block (the layering principle, change-never-significance, per-provider series only, restraint, derived identity, refinement) and the shared-vocabulary contract. Rewrites §5 for M4, records the two platform findings as **queued RFCs** rather than obstacles, and lists the scheduled M2.0 simulation work. |
| 2026-07-29 | v2 — updated at the M3A boundary. Adds the **Knowledge** contract block (identity-never-truth, deterministic resolution, `MatchStrength` is never a number, ambiguity merges nothing, decisions explain themselves) and the module-boundary enforcement contract. Rewrites §5 for M3B, records **two open platform findings** and one scheduled fixture follow-up, and points §6 at [21-intelligence-pipeline.md](architecture/21-intelligence-pipeline.md) as the document to read first. |
| 2026-07-28 | v1 — created at the M2.2 boundary. Establishes the handoff document as the authoritative continuation point. |
