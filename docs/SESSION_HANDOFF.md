# Session Handoff — end of M2.2

> **Purpose:** start the next engineering session immediately, without reconstructing context.
> **Authoritative continuation point.** Updated at every milestone boundary.
> **As of:** 2026-07-28 · commit `b704422` · branch `main`
>
> Read this first. Then [PROJECT_STATUS.md](../PROJECT_STATUS.md) §1–9 for the dashboard, and [IMPLEMENTATION_ROADMAP.md §5b](../IMPLEMENTATION_ROADMAP.md#5b-execution-sequence) for the execution order. Everything else is reference.

---

## 1 · Current project position

| | |
|---|---|
| **Last completed** | **M2.2 Provider Normalization** — closed 2026-07-28 |
| **Next** | **M3A Knowledge Graph** — [architecture proposal](architecture/22-knowledge-graph.md) written, **awaiting review** |
| **Phase** | Product Pipeline. Foundations and enablement are complete and frozen. |
| **Overall completion** | **~30%** by engineering effort (~100 of ~261–339 ew) |
| **Remaining** | ~161–239 ew · ~1.6–2.3 years at 3 engineers, ~4.9–6.8 at 1 |
| **Completed milestones** | M0 · M1.1 · M1.2 · M1.3A · M1.4 · M1.5 · M2.0 · M2.1 · M2.2 |
| **Branch / commit** | `main` @ `b704422` |

**Recent commits:** `b704422` status · `b939c41` M2.2 closed · `6f2b195` mappers · `62ddb45` claim domain · `6708e15` M2.1 complete · `984b1ce` M2.0 closed

### Health

| Indicator | Value |
|---|---|
| Backend tests | **564 passing**, 0 failing, 0 skipped |
| Frontend tests | **101 passing** |
| Backend coverage | **95.12%** (CI gate 95%) |
| Security invariants | **83 / 83**, each proven to fail when its guarantee is removed |
| import-linter contracts | **4 kept, 0 broken** |
| `make smoke` | ✅ 17 stages, 52s warm |
| Migrations | 0000–0008, all reversible |
| mypy strict | Clean, 175 files |
| Open production bugs | **0** |
| Technical debt | **0 outstanding** |

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
| **Immutable tenant tables** | `claim` is immutable. `signora_app` holds **no `UPDATE` grant** — an attempted overwrite fails with a permission error. `DELETE` remains, because claims are derived and regeneration is the rollback for a broken mapper. |

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

---

## 3 · Product Pipeline state

```
Raw Provider Record   ✅ M2.1   Provider Platform — syncs, watermarks, raw storage
        ↓
Claim                 ✅ M2.2   Provider Normalization — canonical evidence
        ↓
Knowledge Graph       🔄 M3A    ← NEXT: resolved entities
        ↓
Observation           ⏳ M3B    what changed, and when
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

**Two links exist and are verified against the live stack.** A simulated provider payload enters through the Provider Port, is stored raw, and becomes canonical claims — with no simulation-specific logic anywhere in that path.

Everything from M3A onward is unbuilt.

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

## 5 · M3A starting context

### What M3A inherits

**Input:** `Claim` rows — immutable, workspace-scoped, each carrying a `SubjectHint` (`provider_external_id`, optional `domain`, optional `legal_name`), a typed attribute and value, `observed_at`, and full source provenance. Claims arrive via the `claim.recorded` path from Provider Normalization.

**Already exists and should be assumed:**
- Event bus with platform-owned idempotency — do not reimplement
- RLS, forced, with `SECURITY DEFINER` predicates — new tables inherit the pattern
- `make smoke`, extensible with a stage
- The Tenant Isolation Policy — **register every new table in `tenancy_policy.py` or the build fails**
- Five fixture providers producing claims for a working scenario
- Deterministic replay: scenario, seed, manifest version, generator version, clock

**Expected output:** canonical entities — companies, people, technologies, and their relationships — with historical state, consumed by the Observation Engine.

### The central challenge

**M3A is the first module that must decide rather than preserve.**

Everything through M2.2 deliberately deferred judgement. Entity resolution cannot: Apollo's `acme-corp` and BuiltWith's `acme.example` either are the same company or are not, and something must choose.

That makes three properties non-negotiable, and they are in tension:

- **Explainable.** *Why* did these resolve together? A resolution nobody can explain is a resolution nobody can trust.
- **Revisable.** A wrong merge must be undoable **without destroying the claims underneath**. Claims are immutable; the *resolution* must not be.
- **Deterministic.** The same claims must resolve the same way on every run, or regression testing is meaningless.

### Architectural questions already identified

Raise and settle these **before** writing code:

1. **Is resolution a projection or a stored decision?** A projection recomputed from claims is always current and trivially revisable, but expensive and hard to explain at a point in time. A stored decision is explainable and stable but must be invalidated when claims arrive.
2. **What does "revisable" mean concretely?** If a merge was wrong, is the correction a new resolution superseding the old, or a mutation? **Given the immutability precedent, the former is very likely right** — and worth confirming before it is assumed.
3. **Where does conflicting evidence get resolved?** M2.2 deliberately preserved disagreement. Two providers reporting different headcounts: does the graph pick one, expose both, or defer to the Observation Engine? *This is the single most consequential M3A decision* — it determines whether disagreement survives into reasoning or dies here.
4. **Does the graph store attribute values, or only identity?** A graph holding both entities and their current attribute values duplicates claim data and must stay in sync. One holding only identity plus edges keeps claims authoritative but pushes work downstream.
5. **What is a person?** Claims carry role changes and contacts but no strong person identity. Whether people are first-class entities in M3A or deferred materially changes its scope.

### Deferred, and to stay deferred

- **Confidence scoring** — belongs to modules with enough context to justify it
- **Authentic provider payloads** — all five remain `Conditional`; fixtures are clearly marked and replacement is a one-file change per provider
- **Bombora's history question** — when an authentic payload arrives, establish whether the provider supplies weekly history *directly* or the platform must *accumulate* it. If the latter, that is an **Observation Engine** responsibility and a design input for M3B. Do not redesign until real evidence requires it.
- **Cloud infrastructure** — M14.5, immediately before GA
- **Business UI** — M12, against real domain contracts

---

## 6 · Future documentation

**"The Intelligence Pipeline"** — `docs/architecture/21-intelligence-pipeline.md`

**Authored after M3A.** Deliberately deferred so it documents working software rather than projections.

Explains how information evolves through the platform: each module's responsibility, inputs, outputs, why each boundary exists, how business value increases at every stage, and how explainability is preserved from raw payload to recommendation — with the canonical pipeline diagram.

**Audience:** engineers, architects, future hires, customers, investors. It must explain both *how* the platform works and *why this architecture differentiates Signora* from conventional Revenue Intelligence products.

Recorded in [IMPLEMENTATION_ROADMAP.md](../IMPLEMENTATION_ROADMAP.md).

---

## 7 · Next session starting point

> **Completed:** M2.2 Provider Normalization · **Next:** M3A Knowledge Graph
> **Branch:** `main` @ `b704422` · everything committed and pushed, tree clean
> **Health:** 564 backend + 101 frontend tests passing · coverage 95.12% · 83 invariants · 4 contracts · smoke green
>
> **Requires approval before implementation:**
> 1. The **M3A architecture proposal** — [22-knowledge-graph.md](architecture/22-knowledge-graph.md). Complete: domain model, four evaluated alternatives, recommendation, entity and relationship models, resolution strategy, evidence attachment, storage, events, API, T59–T66, AC-25–AC-29, demo, DoD, rollback, operational readiness, risks.
> 2. **Three questions inside it**: is the identity/truth split right · should `AMBIGUOUS` block downstream · is deferring person entities acceptable.
>
> **The proposal's core recommendation:** *the graph decides identity; the graph never decides truth.* Identity is irreducible — only the graph can answer it. Attribute conflict is not, and every downstream module has more context to weigh it. If that split is wrong, the design is wrong at its root and should be rejected before implementation.
>
> **Do not:** reimplement anything in §2 · introduce mock business data · add a canonical attribute without an RFC · modify `signora_platform/` or the frontend foundation without a qualifying reason.

---

## Change log

| Date | Change |
|---|---|
| 2026-07-28 | v1 — created at the M2.2 boundary. Establishes the handoff document as the authoritative continuation point. |
