# Session Handoff — end of M3A

> **Purpose:** start the next engineering session immediately, without reconstructing context.
> **Authoritative continuation point.** Updated at every milestone boundary.
> **As of:** 2026-07-29 · branch `main`
>
> Read this first. Then **[21-intelligence-pipeline.md](architecture/21-intelligence-pipeline.md)** — the flagship reference for how information moves through Signora — then [PROJECT_STATUS.md](../PROJECT_STATUS.md) §1–9 for the dashboard, and [IMPLEMENTATION_ROADMAP.md §5b](../IMPLEMENTATION_ROADMAP.md#5b-execution-sequence) for the execution order. Everything else is reference.

---

## 1 · Current project position

| | |
|---|---|
| **Last completed** | **M3A Knowledge Graph** — closed 2026-07-29 |
| **Next** | **M3B Observation Engine** — architecture proposal not yet written |
| **Phase** | Product Pipeline. Foundations and enablement are complete and frozen. Three pipeline stages built. |
| **Overall completion** | **~34%** by engineering effort (~110 of ~261–339 ew) |
| **Remaining** | ~151–229 ew · ~1.5–2.2 years at 3 engineers, ~4.7–6.5 at 1 |
| **Completed milestones** | M0 · M1.1 · M1.2 · M1.3A · M1.4 · M1.5 · M2.0 · M2.1 · M2.2 · M3A |
| **Branch** | `main` |

**Recent commits:** M3A close (this change) · `ae1c0be` identity domain and rule engine · `b2efb2e` M3A approved · `9981d72` M3A proposal · `f11c19c` handoff created · `b704422` M2.2 status

### Health

| Indicator | Value |
|---|---|
| Backend tests | **650 passing**, 0 failing, 0 skipped |
| Frontend tests | **101 passing** |
| Backend coverage | **95.54%** (CI gate 95%) |
| Security invariants | **99 / 99**, each proven to fail when its guarantee is removed |
| import-linter contracts | **7 kept, 0 broken** |
| `make smoke` | ✅ 18 stages, 69s |
| Migrations | 0000–0009, all reversible |
| mypy strict | Clean, 205 files |
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
| **Immutable tenant tables** | `claim` and `resolution_decision` are immutable. `signora_app` holds **no `UPDATE` grant** on either — an attempted overwrite fails with a permission error. `DELETE` remains, because both are derived and regeneration is the rollback for a broken mapper or rule. |
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

---

## 3 · Product Pipeline state

```
Raw Provider Record   ✅ M2.1   Provider Platform — syncs, watermarks, raw storage
        ↓
Claim                 ✅ M2.2   Provider Normalization — canonical evidence
        ↓
Knowledge Graph       ✅ M3A    identity resolution, relationships, claim sets
        ↓
Observation           🔄 M3B    ← NEXT: what changed, and when
        ↓
Business Event        ⏳ M4     funding, hiring surge, migration, exec change
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

**Three links exist and are verified against the live stack** (smoke stages 14b and 14c). A simulated provider payload enters through the Provider Port, is stored raw, becomes canonical claims, and is resolved to an entity whose decision explains itself — with no simulation-specific logic anywhere in that path.

Everything from M3B onward is unbuilt. See **[21-intelligence-pipeline.md](architecture/21-intelligence-pipeline.md)** for what each remaining stage adds and what it is forbidden from doing.

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

## 5 · M3B starting context

### What M3B inherits

**Input:** entities with resolved identity, plus the claims behind them. Concretely:

- `GraphQueries.claim_set(workspace_id, entity_id, attribute)` → every contributing claim with provider, value, `observed_at`, and provenance, plus a computed `agrees`
- `GraphQueries.entity_evidence(workspace_id, entity_id)` → the entity, its provider identities, and all their claims
- `GraphQueries.relationships(workspace_id, entity_id, kind=None, as_of=None)` → edges, with **`as_of` already in the API** as the seam for historical replay
- `GraphQueries.resolution_history(workspace_id, entity_id)` → why the entity is what it is

**Consume these through `modules.knowledge_graph.public`.** Nothing else. The import-linter contracts will fail the build on a deeper reach.

**Already exists and should be assumed:**
- Event bus with platform-owned idempotency — do not reimplement
- RLS, forced, with `SECURITY DEFINER` predicates — new tables inherit the pattern
- `make smoke`, extensible with a stage (14b ingestion+normalization, 14c identity resolution)
- The Tenant Isolation Policy — **register every new table in `tenancy_policy.py` or the build fails**
- Five fixture providers producing claims for a working scenario

**Expected output:** observations — *this changed, by this much, between these times, according to this provider* — consumed by the Business Event Engine and Timeline.

### The central challenge

**M3B is where time becomes first-class.**

M3A deliberately stores no collapsed current value, precisely so this milestone can see a *series*. A claim is a point; an observation is a difference between points, attributed to the source that reported it. The graph grouped the points by identity — that is all it did, and all it should have done.

The question this milestone has to answer carefully: **what counts as a change?** Apollo saying 120 and CoreSignal saying 145 is *disagreement*, not change. Apollo saying 120 in January and 145 in March is change. Distinguishing them is the whole job, and getting it wrong in either direction produces either phantom growth signals or missed ones.

### Architectural questions worth raising before coding

1. **Is an observation per-provider or cross-provider?** A per-provider series never confuses disagreement with change but produces several parallel series per attribute. A cross-provider one is what a seller intuitively wants and is exactly where phantom changes come from.
2. **What is the unit — attribute, entity, or claim-pair?** This determines whether "headcount grew" and "a technology was removed" are the same kind of thing.
3. **Are observations derived on read or stored?** Stored is explainable and cheap to read but must be invalidated when late-arriving claims land — and late arrival is normal, not exceptional (Bombora reports week 3 in week 5).
4. **How is a late-arriving claim handled?** It changes history. Does it produce a new observation, revise one, or supersede one? The immutability precedent points one way; confirm rather than assume.
5. **Does the Bombora weekly-intent series belong here?** Deferred from M2.0 and still open — see below.

### Two platform findings, open

Both concern `signora_platform/`, which is frozen (CLAUDE.md §20a). Neither was fixed inside M3A. **The first is the one that matters.**

| Finding | Effect | Resolution path |
|---|---|---|
| **`EventHandler` receives no session.** The registry's signature is `(envelope) -> None`, but a handler must do its work in the *same transaction* as the dispatcher's idempotency claim — a handler opening its own session would break exactly-once, which is the guarantee the whole bus is built on. | **No module handler is registered in the live registry.** The pipeline is exercised end to end through its real handlers in the integration suite and in `make smoke`, but the deployed worker consumes nothing. M3B will hit this the moment it needs a subscription. | A platform interface change — pass the session, or expose it via a context variable. **An RFC decision, not a coding-session one.** |
| **`PublishableEvent` cannot be satisfied by a frozen dataclass.** The Protocol declares settable members; every domain event is immutable, as the architecture requires. | Three modules now carry a `# type: ignore` at their publish site. Cosmetic, but spreading. | Declare the Protocol's members read-only. Widens what satisfies it; breaks nothing. |

### One scheduled follow-up

**Fixture enrichment (M2.0 work).** Crunchbase and CoreSignal development fixtures carry no domain, so those two providers cannot resolve to the same entity as Apollo/BuiltWith/Bombora. The rules are correct — the fixtures are impoverished. Real payloads from both vendors carry a website. Adding one to those generators would let cross-provider resolution be demonstrated at full breadth **without weakening any rule**.

### Deferred, and to stay deferred

- **Confidence scoring** — belongs to modules with enough context to justify it. `MatchStrength` is not this and must never become it.
- **Fuzzy / probabilistic identity matching** — a hidden heuristic. `entity.resolution_ambiguous` volume is the evidence that would justify it; speculation is not.
- **Resolved-value projections in the graph** — no consumer has asked for one. If M3B or M5B demonstrates it needs one, *that* is the evidence, and the rule it should use will be knowable by then.
- **Person entities** — claims carry role changes but no person *identifier*. There is no identity to resolve; adding people now means inventing one.
- **Manual merge/unmerge UI** — the domain supports it via supersession. The interface belongs with the business UI at M12, and `entity.superseded` waits for it.
- **Authentic provider payloads** — all five remain `Conditional`; replacement is a one-file change per provider.
- **Bombora's history question** — when an authentic payload arrives, establish whether the provider supplies weekly history *directly* or the platform must *accumulate* it. If the latter, that is an **Observation Engine** responsibility. Do not redesign until real evidence requires it.
- **Cloud infrastructure** — M14.5, immediately before GA.
- **Business UI** — M12, against real domain contracts.

---

## 6 · Key documents

| Document | What it is for |
|---|---|
| **[21-intelligence-pipeline.md](architecture/21-intelligence-pipeline.md)** | **Read first.** The flagship reference: how a fact travels from raw provider payload to recommendation, what each stage adds, and what each stage is forbidden from doing. Written for engineers, architects, future hires, customers, and investors. Authored at the M3A boundary, as planned — after three stages existed, so it documents working software rather than projections. |
| [22-knowledge-graph.md](architecture/22-knowledge-graph.md) | The M3A design, marked **as built**, including four departures from the approved proposal and why each was forced. |
| [06-events.md](architecture/06-events.md) | The event catalog. `claim.recorded` and the five Knowledge Graph events are current as of M3A. |
| [05-module-dependencies.md](architecture/05-module-dependencies.md) | The dependency graph, and the read-port pattern for reading another module's data. |
| [04-modules.md](architecture/04-modules.md) | Module ownership and vocabulary. Provider Normalization and Knowledge Graph entries reflect what was actually built, not the v2 placeholders. |

---

## 7 · Next session starting point

> **Completed:** M3A Knowledge Graph · **Next:** M3B Observation Engine
> **Branch:** `main` · everything committed, tree clean
> **Health:** 650 backend + 101 frontend tests passing · coverage 95.54% · 99 invariants · 7 contracts · smoke green over 18 stages
>
> **First actions:**
> 1. Read [21-intelligence-pipeline.md](architecture/21-intelligence-pipeline.md) — it is the shortest path to full context.
> 2. Verify the tree is clean and `make smoke` is green.
> 3. Prepare the **M3B architecture proposal** before any implementation, following the M3A pattern: domain model, evaluated alternatives with a recommendation, storage, events, module API, task breakdown, acceptance criteria, demonstration, DoD, rollback, operational readiness, risks. **Wait for approval.**
>
> **Settle these inside the proposal, not during implementation:** per-provider vs cross-provider observations · the unit of change · derived-on-read vs stored · how a late-arriving claim revises history.
>
> **Raise, do not work around:** the `EventHandler` session finding (§5) will block live subscriptions the moment M3B needs one. It is an RFC decision.
>
> **Do not:** reimplement anything in §2 · introduce mock business data · add a canonical attribute without an RFC · store a resolved attribute value in the Knowledge Graph · turn `MatchStrength` into a number · modify `signora_platform/` or the frontend foundation without a qualifying reason.

---

## Change log

| Date | Change |
|---|---|
| 2026-07-29 | v2 — updated at the M3A boundary. Adds the **Knowledge** contract block (identity-never-truth, deterministic resolution, `MatchStrength` is never a number, ambiguity merges nothing, decisions explain themselves) and the module-boundary enforcement contract. Rewrites §5 for M3B, records **two open platform findings** and one scheduled fixture follow-up, and points §6 at [21-intelligence-pipeline.md](architecture/21-intelligence-pipeline.md) as the document to read first. |
| 2026-07-28 | v1 — created at the M2.2 boundary. Establishes the handoff document as the authoritative continuation point. |
