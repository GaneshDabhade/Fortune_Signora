# CLAUDE.md — Signora Engineering Constitution

> This file governs how Claude Code behaves while working in this repository. It is binding, not advisory. It does not describe what Signora does as a product — that lives in `docs/architecture/`. This file describes how work gets done here.
>
> The architecture itself is defined by **every document in `docs/architecture/`**, plus the ratified Architecture Decision Records in `docs/architecture/adr/`. That set is the single source of truth for *what the architecture is* — including the full, ratified technology stack (no open technology choices remain; see `docs/architecture/08-technology-stack.md` and its linked ADRs). This file is the single source of truth for *how Claude must behave* while implementing it. Where this file references a rule, the linked document is authoritative on the details; this file is authoritative on the behavior it demands from Claude.
>
> **The numbered documents fall into three groups**, and knowing which is which is how a session decides what binds it:
>
> | Range | What it is | Binding? |
> |---|---|---|
> | **`01`–`21`** | System architecture — principles, modules, dependencies, events, tenancy, security, API conventions, and `21-intelligence-pipeline.md`, **the reference to read first** | Yes |
> | **`22`–`29`**, plus `33` | **Module designs**, one per module, each marked *as built*. Read the one you are working in | Yes, for that module |
> | **`30`+** | **Records and cross-cutting notes** — retrospectives, design-review evidence, product surface, design decisions, review findings. Dated; never rewritten | As history, not as instruction |
>
> **Corrected 2026-08-01.** This sentence said the architecture was `01-overview.md` **through `17-future-recommendations.md`**. There are 39 numbered documents and 36 ADRs. A session reading its constitution literally could not see documents `18`–`39` — including every module design and the entire product-surface design. Harmless while one session held the whole tree in context; **a correctness defect the moment a second session starts cold**, which is why it is fixed here before Lane B begins.

---

## 1. Project Overview

Signora is implemented as a modular monolith governed by the architecture package in `docs/architecture/`. Claude operates in this repository as a **disciplined implementing engineer working inside an already-agreed architecture**, not as an architect inventing one. Every session begins from the assumption that the architecture is already decided; Claude's job is to implement it correctly, consistently, and incrementally.

Before writing any code in a session, Claude must know which module it is working in and must have read that module's relevant sections of the architecture set. If it is unclear which module a task belongs to, resolving that ambiguity against `docs/architecture/04-modules.md` is the first step of the task, not an afterthought.

## 2. Engineering Philosophy

- **Every field has the least powerful author capable of producing it correctly** (ratified 2026-07-30). *The* decision rule for where anything belongs, and the general form of several principles below.

  > **The database owns timestamps. Code owns derived facts. Domain experts own static knowledge. AI owns inference.**
  >
  > **If a less powerful component can produce a field correctly, it owns that field.**

  Power here means *freedom to be wrong in ways nothing can check*. A `DEFAULT now()` cannot be mistaken; a derivation can be wrong but is reproducible and testable; a reviewed catalog entry can be wrong but a domain expert signed it and a diff shows the change; a model can be wrong fluently, unrepeatably, and only where inference was genuinely required. Climbing the ladder buys capability and pays in defensibility, so **climb only as far as correctness actually requires**.

  This is why the Decision Package's model authors three fields of fifteen, why release is derived from evaluations rather than declared, why `evidence_state` is computed rather than stored, why signal limitations live in the catalog rather than in a prompt, and why the same rule already reads *"if the system already knows something deterministically, never ask a model to invent it again"* — that is this principle at its top rung. When it is unclear where something belongs, ask what the *least* powerful author capable of getting it right would be, and stop there.

- **Types should make incorrect architecture impossible** (ratified 2026-07-30). Whenever practical, express an architectural constraint through the type system rather than documentation alone — prefer a violation that is *unrepresentable* over one that is merely discouraged. This has repeatedly produced stronger designs than convention: `MatchStrength` refuses numeric conversion, `ProfileEntry.signal_type` makes an invented signal type unconstructable, `next_state` demands an `actor_id` with no default, a negative contribution cannot be built, and the AI Provider Registry exposes no vendor-keyed lookup. When reviewing a design, ask what a violation would look like in code; if the answer is "ordinary code that happens to be wrong", look for a type that would refuse it.
- **Hidden inputs are architecture defects** (ratified 2026-07-30). Any input that influences behaviour without being part of the declared contract is an architectural concern, not an implementation detail — because it makes the same declared inputs produce different results, which defeats replay, regression testing, and every guarantee proven by removal. Found and eliminated so far: insertion order · hash seed · assembly timestamps · implicit caches · implicit conversation state · provider identity. When implementation reveals one, name it and remove it rather than documenting it.
- **A guard that cannot fail is not protection — it is documentation pretending to be code** (ratified 2026-07-30). When implementation reveals a condition that cannot occur, or a branch that cannot influence behaviour, **remove it or replace it with something that genuinely protects**. Confidence must come from enforceable behaviour, never from a reassuring comment. This is what a *surviving* mutation usually means: not a missing assertion but a guard that was never load-bearing, and the comment justifying it is then a false claim sitting in the codebase.
- **Truth has exactly one authoritative representation; everything else derives from it** (ratified 2026-07-30). When implementation reveals two independent representations of one fact, **remove one rather than synchronising both** — synchronisation is maintenance, derivation is architecture, and duplicated truth eventually becomes contradictory truth. Applied so far: the JSON Schema derives from the validating type · release state derives from evaluations · provider resolution derives from model registration · evidence identity derives from the canonical form · `evidence_state` derives from the live score. A stored copy of a derivable fact is a defect waiting for the two to disagree.
- **Behaviour exists exactly once** (ratified 2026-07-30). Comments may *explain* behaviour, tests may *verify* it, architecture may *require* it — only code may **implement** it. When the same behaviour appears simultaneously in a branch, a default, and an assumption, remove copies until one executable source remains. **Defaults are behaviour**, and a default duplicated across a request and the policy that governs it is the same defect wearing a quieter coat.
- **If the system already knows something deterministically, never ask a model to invent it again** (ratified 2026-07-30). **The top rung of the least-powerful-author rule above**, stated separately because it is the rung most often climbed by accident. Use AI only where inference is genuinely required; everything else comes from deterministic computation, versioned configuration, or reviewed repository artifacts. This is not a cost argument — it is a *trust* argument. A derived fact can be recomputed, defended and independently validated by a customer; a generated one can only be believed. Every regeneration of something already known adds hallucination surface, evaluation burden and latency while **subtracting** defensibility. Applied so far: the evidence digest is computed, not asked · release is derived from evaluations, not declared · coverage is measured from citations, not rated · *why now* comes from `BuyingScore.trigger`, not from a paraphrase. Ask of any proposed model-authored field: *does the platform already know this?* If it does, deriving it is not the cheaper option — it is the correct one.
- **Determinism outranks convenience** (ratified 2026-07-30). Where the two conflict, determinism wins — every time, without a case-by-case argument. The evidence set is closed, grounding is deterministic, release is derived from measurements, the digest is computed over a canonical form, and no operational record depends on chance. The reason is not purity: a system whose behaviour varies with something outside its declared inputs cannot be replayed, regression-tested, or explained to a customer, and each of those is a product capability rather than an engineering preference. A convenient shortcut that costs determinism is not a shortcut; it is a future incident nobody can reproduce.
- **Immutability is the default for anything that records a fact** (ratified 2026-07-30). Prompts, evidence, fingerprints, digests, materialized AI artifacts, operational history, and every historical record describe something that **was** true. They are never edited: a change is a new version, a new row, a new artifact naming the one it supersedes. An editable record of the past is a record nobody can cite — and the rows most worth editing are always the inconvenient ones. Enforce it where enforcement lives: no `UPDATE` grant, no `UPDATE` policy, frozen types, and no repository method that offers one.
- **A module owns everything required to realize its behaviour** (ratified 2026-07-30). Its domain, ports, infrastructure, configuration, errors, published contracts, tests, and its artifacts — prompts, taxonomies, policies, evaluations. **The platform composes modules; it never becomes the owner of their internals.** When something a module needs starts accumulating in the substrate every module already imports, the substrate has stopped being a substrate. The question to ask of any new value, type or file is *whose behaviour does this govern* — and the answer names the owner.
- **Materialized AI artifacts are historical facts, not current truth** (ratified 2026-07-30). A persisted model output records *what the platform actually produced at that moment* — against that prompt, that model and that evidence. It is therefore **immutable**: prompt evolution or better evidence produces a **new** artifact, never an edit to an existing one, because editing one would destroy the only record of what a customer was actually shown and silently invalidate every evaluation and audit that cites it. This makes them a distinct data category — neither derived intelligence (rebuildable), customer configuration (irreplaceable), workflow state (unreproducible), nor operational history (the platform's account of its own behaviour). Every one must remain attributable without reconstruction: which evidence, which prompt, which model, which inference, when.
- **Observability is a product capability, not an operational afterthought** (ratified 2026-07-30). A system cannot be improved using information it never recorded, and the record cannot be added retroactively — the runs that would have explained the problem are gone. Whenever a change introduces new behaviour, ask what a future engineer will need in order to **understand, measure, debug, audit or explain** it, and make the operational history answer those questions *without reconstruction*. This is why `ai_inference` records failures as faithfully as successes: a failed inference must never be less observable than a successful one.
- **Ownership and configuration always align** (ratified 2026-07-30). The module that owns a behaviour also owns the configuration governing it. Separating the two eventually produces a platform responsible for everything — because every module's settings accumulate in the one place every module already imports, and a substrate that knows every module's configuration surface is no longer a substrate. When a new value is needed, the first question is *whose behaviour does this govern*, and the answer names the owner.
- **Beware Decorative Logic** (named 2026-07-30). Decorative Logic is implementation that *appears* to enforce a property but whose removal does not change the property it claims to protect. It is more dangerous than dead code, because it gives engineers confidence that something is enforced when it is not — and the comment beside it is then a false claim that survives review. **A surviving mutation is the primary way it is found.** When one is discovered, strengthen the underlying invariant or assert the real property; never restore the branch to make the mutation die. Found four times in M8 alone: a canonicalisation guard, a numeric-extraction guard, quantity scoping, and an authentication branch.
- Correctness and clarity outrank cleverness. Code is read far more often than it is written, by people who were not in this conversation.
- This codebase is written to be maintained by a staff-level engineering organization for years, not to demo well once.
- Boring, explicit, well-understood solutions are preferred over novel ones. Novelty must be justified by a real constraint, not by preference.
- Minimalism is a discipline, not an accident: implement what the task requires, at the scope the task requires, and no more.
- Consistency across the codebase is worth more than local optimization. A module that looks like every other module is more valuable than a module that is 10% cleverer.
- When a decision is genuinely architectural — not just an implementation detail — it does not belong to a single coding session. It belongs to the RFC process described in `docs/architecture/01-overview.md`.
- **The repository itself should always tell the truth.** Everything committed here — code, configuration, documentation, status, workflow files — is read by someone who was not in the conversation that produced it, and they have no way to check it against anything but itself. A workflow that looks live but is disabled, a dashboard describing the previous milestone, a document asserting a gate that no longer runs, a config file implying enforcement that was never installed: each is a defect of the same kind, and each is more damaging than the absent version, because it is trusted. This cuts both ways — **a record of what was true then must not be rewritten to match now.** Correct a claim about the present; date a record of the past. Falsifying history to make the repository look consistent is the same failure wearing the opposite coat.
- **Every completed slice is demoable by a non-engineer** (ratified 2026-08-01, on the product owner's direction, binding from M12.3). A slice is finished when it can be shown to a salesperson, a founder or a designer **without explaining the architecture**. If demonstrating it requires naming a module, a table, a port or an event, it is infrastructure that has not yet reached a customer — which may be correct work, but it is not a completed product slice and must not be reported as one.

  This is a **check on sequencing, not a ban on foundations.** The pipeline ran nine stages ahead of any user-visible surface and that was a real cost, recorded in `31-m10-design-review-evidence.md` before it was felt. The rule that follows: when a slice's demonstration needs a paragraph of architecture, look for the smaller slice inside it that does not.

  It also sets the **shape of a review**: the demonstration is the product owner's, so a slice ends with *how to see it*, in the words a customer would use — not with a summary of what was built.

## 3. Architecture Principles

The fifteen principles in `docs/architecture/02-principles.md` (modular architecture over microservices, DDD, event-driven communication, Clean Architecture per module, extractable service boundaries, single PostgreSQL database, RLS-based shared-database tenancy, workspace-based tenancy, provider/AI/integration abstraction layers, an internal event bus, async background processing, and build-only-the-advantage / buy-the-commodity) are **non-negotiable constraints on every change Claude makes**, not background context.

Claude must:
- Treat every one of these principles as a hard constraint when designing or reviewing an implementation approach.
- Cite the specific principle when a design choice is non-obvious, in code comments only when the rationale itself is non-obvious (see §6), and always in PR/commit descriptions.
- Never silently work around a principle because compliance is inconvenient for the task at hand. If a principle appears to block a legitimate need, that is a signal to stop and raise it, not to route around it.

## 4. Domain Driven Design Rules

- Every module owns its own bounded context, its own ubiquitous language, and its own aggregates, as defined in `docs/architecture/04-modules.md`. Claude must use that document's glossary terms exactly as defined — never invent a synonym, never repurpose a term from one module inside another.
- **The product has a second ubiquitous language, and it is the customer's** (ratified 2026-08-01, `docs/architecture/adr/0034-ubiquitous-language.md`). The rule above governs the language *between engineers*; it was silent on the language *between the product and the person paying for it*, and that silence shipped screens telling a salesperson *"You are not in a workspace yet"* and explaining Row-Level Security in a dialog. **A customer says Organization, Team, Product, ICP, Buying Committee, Account, Signal, Opportunity, Evidence, Research, Workflow. The platform says workspace, tenant, provider, pipeline, entity, claim, observation, business event, buying score, outbox, port, adapter.** Both are correct; exactly one reaches a screen. The test is *"would a salesperson use this word unprompted to describe their own job?"* — which is why `Signal` and `Opportunity` are deliberately identical on both sides. **The translation lives at the frontend edge and never travels inward:** no table, column, API path, JWT claim, module, type or architecture document is renamed, because `workspace` is precise about isolation in a way `organization` is not. Enforced by `frontend/tests/components/vocabulary.test.tsx`, because a glossary nobody can violate is documentation pretending to be code.
- Domain logic lives in a module's domain layer and is expressed in domain vocabulary, not in database or transport vocabulary. A repository, a controller, or an event handler is never the place to make a domain decision.
- Aggregates are the unit of consistency. Claude must not design a change that requires two modules' aggregates to be updated as if they were one transaction — that need is a signal the event-driven boundary is being violated (see §5).
- Anemic domain models (structs with no behavior, all logic pushed into services) are a smell in a DDD codebase. Domain behavior belongs on domain objects unless there is a specific, stated reason it doesn't.
- Claude must not introduce a second definition of a concept a module already owns. If a concept looks like it already exists elsewhere in the domain model, that must be checked before adding a new one.

## 5. Module Boundaries

Module boundaries are defined in `docs/architecture/04-modules.md`, the allowed dependency graph in `docs/architecture/05-module-dependencies.md`, and their physical enforcement in `docs/architecture/15-project-structure.md`.

Claude must:
- Only import from another module's `public/` contract — never from its `domain/`, `application/`, or `infrastructure/` layers.
- Only add a new cross-module dependency if it matches an edge already present in the dependency graph, or is proposed and approved as a graph change first.
- Default to event-driven communication between modules. Treat a synchronous, direct call into another module as the rare, justified exception described in `05-module-dependencies.md` — never the default way to "just get the data."
- Never query another module's database tables directly, under any circumstance, including "temporary" debugging code that could ship.
- Implement one module at a time per unit of work. A single task that appears to require simultaneous changes to two modules' domain logic is a signal to re-examine the boundary before proceeding, not a reason to push through.
- Keep modules independent enough that any one of them could, in principle, be extracted into its own service without changing its domain or application layers (Principle 5). Write code as if that were a live possibility, because it is the architecture's stated intent.

## 6. Coding Standards

- Follow Clean Architecture inside every module: domain at the center, application orchestrating it, infrastructure and interface layers at the edges, dependencies always pointing inward. Never let a domain layer import an infrastructure concern.
- Prefer interfaces (ports) over concrete implementations at every boundary where a module depends on infrastructure, a provider, an AI vendor, an integration, or another module's contract. Concrete infrastructure types must never leak into domain or application signatures.
- **A port belongs to the module that owns the language it represents** (ratified 2026-07-30). A port is **not** shared platform infrastructure: it is a module's vocabulary expressed as a contract, so it lives in that module's `domain/` and is published through its `public/`. Infrastructure *depends on* the port; the port does not belong to infrastructure, and it never moves to `signora_platform/` because more than one module consumes it. This was learned twice — `15-project-structure.md` placed both the Provider Port and the AI Provider Port in platform packages that were never built, and the implementation put each in its owning module both times. Apply it whenever a new port is introduced.
- Use dependency injection to wire concrete implementations into ports at the composition boundary (interface/entry-point layer) — never construct infrastructure dependencies inside domain or application code.
- **Configuration is always a typed Settings object owned by the module that owns the behaviour** (ratified 2026-07-30). The rule is *not* "configuration must go through `signora_platform/settings.py`" — that file is **one implementation** of this principle, holding the platform's own configuration, and `AISettings` in `modules/ai_platform/infrastructure/` is another. Every module that needs configuration declares its own typed object; no module reads `os.environ`; a Settings object is constructed **only at the composition root**, which injects it into that module's infrastructure. **No module ever learns where another module's configuration came from.** This preserves module ownership, the platform freeze (§20a), dependency inversion, and testability at once — and it is what stops the substrate from slowly becoming the registry of every module's configuration surface.
- Use type hints/strong typing everywhere the language supports it. Untyped code is not acceptable in this codebase — Python code is written with full type hints and must pass MyPy strict mode; TypeScript code must not use `any` without explicit, reviewed justification (`docs/architecture/adr/0024-code-quality-and-static-analysis.md`).
- Do not add abstractions, configuration flags, or generalization for hypothetical future needs. Build for the requirement in front of you, structured so it *can* extend, not pre-extended for cases that don't exist yet.
- Do not write comments that explain what code does; write comments only when the *why* is genuinely non-obvious (a constraint, a workaround, an invariant). Default to no comments.
- Match existing patterns in the module you're working in before introducing a new one. Consistency within a module takes priority over a marginally better local pattern.
- Never introduce a new framework, library, or major dependency without explicit approval — this includes seemingly small utility libraries that duplicate something the standard library or an already-approved dependency already does.

## 7. API Standards

- Every API endpoint belongs to exactly one module and is implemented in that module's interface layer. It delegates to that module's application layer immediately — it does not contain business logic itself.
- Every request handler resolves and verifies workspace context before touching any workspace-owned data, per `docs/architecture/11-tenancy.md`. A workspace identifier supplied by a client is never trusted without server-side membership verification.
- Endpoints that would trigger pipeline processing (provider calls, AI reasoning, etc.) synchronously are not permitted — that work is dispatched to background workers per `docs/architecture/07-data-flow.md` and `docs/architecture/02-principles.md` (Principle 13). An API handler responds once the request has been durably accepted, not once downstream processing has completed.
- API contracts (request/response shapes, error shapes, versioning approach) must be applied consistently across modules. Do not invent a new response envelope or error shape per module.
- The API is REST, built with FastAPI, documented via auto-generated OpenAPI, with every request/response shape a Pydantic v2 model (`docs/architecture/adr/0002-web-framework-and-api-style.md`, `docs/architecture/adr/0004-data-validation-and-serialization.md`). Do not hand-write API documentation that duplicates what OpenAPI generation already produces, and do not introduce a second API paradigm (GraphQL, gRPC) without an RFC and a new ADR.
- Authorization for every endpoint is a Casbin policy check wired as a FastAPI dependency, evaluated before the request reaches application-layer code, and always includes `workspace_id` in the policy tuple (`docs/architecture/adr/0010-identity-and-access.md`).
- Every endpoint follows the conventions in `docs/architecture/19-api-conventions.md`: the single error envelope with a stable `code` and `correlation_id`, cursor-based pagination for all collections, and purpose-built response schemas — never a domain entity or SQLAlchemy model returned directly.
- Domain and application layers never raise `HTTPException` or know HTTP status codes. Domain exceptions are mapped centrally in `signora_platform/api/`.
- A caller who is not a member of the workspace they name gets `404`, never `403`. This is a security property (it prevents workspace enumeration), not an inconsistency to tidy up.

## 8. Database Standards

- There is exactly one PostgreSQL database (Principle 6). Claude must never introduce a second datastore, a per-module database, or a cache used as a system of record without an explicit, approved exception.
- Every workspace-owned table has a non-nullable `workspace_id` column with `FORCE ROW LEVEL SECURITY` enabled and a policy scoped to it, per `docs/architecture/11-tenancy.md`. This is not optional for new tables.
- Every unit of work (request or event handler) must establish `SET LOCAL app.workspace_id` from a verified source before executing any query against workspace-owned tables. `SET` (not scoped to the transaction) must never be used for this.
- Even with RLS in place, queries must still explicitly filter by `workspace_id` as defense-in-depth — RLS is the authoritative control, not the only one.
- A module owns its own tables. No other module's code may write to them directly, and ideally no other module's database role can either.
- **Platform infrastructure tables are owned exclusively by platform services.** `outbox_event`, `processed_event`, `dead_letter_event`, `alembic_version`, and any future internal scheduler tables are not module data. A business module must never query one — not to check whether an event was relayed, not to inspect a dead letter, not for debugging. These tables span every workspace and deliberately carry no RLS, so the grant is the only thing separating tenants there: the application role publishes (`INSERT`) and cannot read, and only the relay identity (`signora_relay`) consumes. Claude must never restore a read grant to `signora_app` to make code work, and never add module code that reads an infrastructure table (`docs/architecture/11-tenancy.md`, migration `0006`).
- **Every new table is classified before it ships.** Add it to `TENANT_OWNED_TABLES` or `PLATFORM_INFRASTRUCTURE_TABLES` in `backend/tests/security_invariants/tenancy_policy.py`, in the same change that creates it. Tenant-owned tables must satisfy the full Tenant Isolation Policy: a non-nullable tenant identifier, RLS enabled **and forced**, policies covering `SELECT`/`INSERT`/`UPDATE` separately, no runtime role able to bypass RLS, and a regression test proving enforcement rather than asserting configuration. Classification is never inferred from the presence of a `workspace_id` column — a table that simply forgot the column would be exempted by omission, which is exactly how tenancy gaps reach production.
- Any schema change must be accompanied by a corresponding update to the relevant architecture documentation in the same change — undocumented schema drift is treated as a bug, per Claude Rules (§21).
- Migrations are additive and reversible by default; destructive migrations (drops, non-backward-compatible column changes) require explicit confirmation before being applied, consistent with the general caution this project applies to hard-to-reverse actions.
- **Migration credentials and runtime credentials are separate identities, always.** This is a permanent engineering rule, not a deployment preference:
  - **Runtime services must never execute using migration or owner credentials.** A service connected as the owner is exempt from Row-Level Security on every table it touches, which silently voids the entire tenancy model no matter how correct the policies are.
  - **Schema migrations execute only under the migration identity** — as a discrete release step, never from inside a running service.
  - **Runtime services execute only under the least-privileged application identity** for their tier: `signora_app` for the API and workers, `signora_auth` for the authentication tier. Each tier's credential must be unable to reach the other's data.
  - Claude must never widen a runtime role's privileges to make a task work, never run migrations from application code, and never introduce a connection string that lets a service connect as the owner — including in local development or test configuration, where an over-privileged connection makes isolation tests pass vacuously.
- The database is PostgreSQL 17+; the ORM is SQLAlchemy 2.x (async); migrations are Alembic (`docs/architecture/adr/0006-data-platform-primary-database-and-multi-tenancy.md`, `docs/architecture/adr/0005-orm-and-schema-migrations.md`). Every migration touching a workspace-owned table must include its RLS policy and `FORCE ROW LEVEL SECURITY` statement in the same migration that creates the table, not a follow-up. SQLAlchemy models live only in a module's `infrastructure/` layer — never imported by `domain/`, `application/`, or `public/`.

## 9. Event Standards

- All inter-module communication defaults to domain events published on the Internal Event Bus, using the envelope and catalog defined in `docs/architecture/06-events.md`. Every event carries `workspace_id`, `correlation_id`, and `causation_id`.
- Event consumers must be idempotent on `event_id`. Claude must never write a handler that assumes exactly-once or in-order-across-entities delivery.
- New event types or payload changes are documented in `docs/architecture/06-events.md` in the same change that introduces them. A breaking payload change requires a version bump and a stated deprecation window, not a silent shape change.
- Events are published in the same transaction as the state change that causes them (transactional outbox), never published speculatively before the causing write is committed. Dispatch to consumers happens via the outbox relay into Redis/ARQ (`docs/architecture/adr/0011-background-processing-and-event-bus-transport.md`) — never publish directly to Redis, bypassing the outbox.
- Claude must not use an event as a disguised synchronous request/response mechanism (publish-and-block-for-a-reply). If a synchronous answer is genuinely required, use the narrow approved synchronous interfaces in `docs/architecture/05-module-dependencies.md`.
- All background/async work, including event dispatch, runs through ARQ. Never introduce a second job-queue mechanism for a single feature "because it's simpler here."

## 10. AI Standards

- All AI/LLM vendor access (Claude, OpenAI, Gemini; Azure OpenAI reserved for future use) goes exclusively through the AI Provider Abstraction Layer described in `docs/architecture/14-ai-architecture.md` and `docs/architecture/adr/0012-ai-platform-architecture.md`. Claude must never call a model vendor's SDK or API directly from domain or application code.
- **Model-centric resolution is a permanent principle** (ratified 2026-07-30). Business intent is *"execute against this model"*, never *"execute against this vendor"* — the model-to-vendor mapping is an operational concern belonging entirely inside the AI Platform. The provider registry therefore exposes **`for_model(model)` and no vendor-keyed lookup**, so business code that cannot *name* a vendor cannot branch on one. Prefer this shape wherever a similar choice arises: state the capability needed, let the resolver decide who supplies it.
- **Failure attribution must be truthful** (ratified 2026-07-30). An error must never name a component that was not involved. A malformed request rejected before provider resolution has no vendor, and stamping one on it puts a false lead in the first place an engineer looks during an incident — **an incorrect attribution is worse than none, because it misdirects the investigation.** Failure hierarchies are therefore split by *what was actually reached*: `AIPlatformError` covers everything, with vendor-bearing failures a distinct branch. Apply this whenever a new failure hierarchy is introduced.
- **Operational facts and commercial policy stay separate** (ratified 2026-07-30). Records describe what happened — tokens, latency, retries, timings — and never what it cost. A price is a contract term that changes without the code changing, so a currency figure written onto an operational row is correct briefly and wrong permanently. Pricing is applied at reporting time over stored facts, which also lets a rate change re-price history correctly.
- **Vendor neutrality is a permanent principle** (ratified 2026-07-30). **Business behaviour must never depend on which model vendor served a call.** Vendor selection is *configuration*, never business logic: the deterministic pipeline behaves identically whether the configured provider is Ollama, Claude, GPT, Gemini, Bedrock, or one that does not exist yet. The AI Platform adapts to vendor-specific APIs **internally**; everything outside it stays vendor-neutral. Vendor identity is recorded as provenance on every inference and **never consulted for a decision** — no `if vendor == …` outside an adapter, asserted directly, the same rule as pipeline neutrality (AC-21) in the provider layer.
- **Model runtime is decided by environment** (`docs/architecture/adr/0028-model-runtime-by-environment.md`): **Ollama for development** — prompt engineering, the evaluation harness, `make smoke`, offline demos, regression — and **hosted commercial models in production**. Ollama is never a production dependency, never a fallback, and never a cost tier. Claude must never configure a deployed service to reach a local runtime.
- **Prompts are first-class engineering artifacts.** Every prompt carries a version, an owner, its evaluation history, its supported models, its supported datasets, and its release history. **A prompt is not "released" until it has been evaluated against the supported `(model, dataset)` combinations**, and it may never be used with a pairing absent from that record — developing against a small local model does not demonstrate behaviour on a frontier hosted one. A released version is immutable: a change is a new version, never an edit, because editing one silently invalidates every result that claims it.
- **Scripted fakes and real models solve different problems, and the separation is permanent.** Deterministic engineering behaviour — Security Invariants, schema validation, retry, error handling, provider abstraction, replay, failure paths — is verified against **fakes and recorded fixtures, and must never call a model**. AI-quality behaviour — grounding, prompt evaluation, prompt regression, output validation — is exercised against a **real model**, because those checks exist to catch failures a fake cannot naturally produce: a fake never invents a quantity unless it is told to. Never merge the two: a guarantee that needs a model to verify is not a guarantee, and a quality measurement taken against a fake measures the fake.
- **Evaluation measures compatibility with Signora's contract, not general model quality** (ratified 2026-07-30). A prompt evaluation answers *"can this model reliably satisfy structured output, grounding, citation fidelity and deterministic validation, behind this prompt?"* — never *"is this a good model?"* A highly capable model can be unsuitable here, and a modest one sufficient. This is why the criteria are pass/fail definitions rather than a score, why `REFUSED` is a legitimate and useful outcome, and why a benchmark result must never be read as a verdict on a vendor. Equally: **the pinned evaluation model is part of the benchmark.** Performance on a given machine is an *observation* to report; changing the model is an *architectural decision* that belongs to the product owner, never to a coding session working around slow hardware.
- AI output is untrusted content until validated against an expected Pydantic v2 structure. It must never be used to trigger a privileged or irreversible action without explicit validation and, where the architecture calls for it, human confirmation.
- Prompt templates are versioned artifacts in the Internal Prompt Registry, reviewed like code, with the version recorded against every research/reasoning result produced.
- Context assembled for a research or reasoning request must be scoped strictly to the current workspace. Claude must never construct a prompt that could include another workspace's data.
- Vendor-specific behavior (formatting, tool-calling conventions, response parsing) stays entirely inside the adapter implementing the AI Provider Abstraction Layer's port — it never leaks into AI Research Engine's or AI Reasoning Engine's domain logic.
- AI Research Engine (agentic, multi-step) and AI Reasoning Engine (structured, single-call) are distinct modules with distinct latency/cost/failure profiles. Never fold research-style agentic logic into AI Reasoning Engine's request path, and never make AI Reasoning Engine block indefinitely on AI Research Engine — it proceeds without it after the documented timeout (`docs/architecture/05-module-dependencies.md`).
- Embeddings use OpenAI Embeddings; vectors are stored in pgvector on the owning module's own workspace-scoped, RLS-enforced tables — embeddings are not exempt from tenancy rules.

## 11. Testing Standards

- No change ships without tests. This is a hard rule, not a judgment call left to convenience or time pressure.
- Domain and application layers are unit tested using fakes/test doubles for infrastructure ports — if a domain test requires a real database, provider, or AI vendor, that is a sign the Clean Architecture boundary has leaked (§6).
- Integration tests exercise a module against a real (test) database and real event dispatch. End-to-end tests exercise full pipeline flows as described in `docs/architecture/07-data-flow.md`.
- Tests must cover the failure paths (transient provider failure, malformed AI output, RLS/workspace-boundary violations attempted, idempotent re-delivery of an event) — not only the golden path.
- A task is not complete if tests are failing, skipped, or commented out to make a change appear to pass. Never weaken or delete a test to make it pass without understanding why it failed.
- **The Security Invariants suite (`backend/tests/security_invariants/`) is permanent.** It states architectural guarantees — token verification, Casbin enforcement, workspace isolation, RLS, per-tier database privileges, event durability, idempotency, retry, dead-lettering — rather than feature behaviour. Claude must never delete, skip, or weaken one of these tests to make a change pass; a failure there means a guarantee the architecture depends on has stopped holding. New guarantees are added to it as the system grows, and deliberate overlap with feature tests is intended so that rewriting a feature cannot remove its guarantee.
- Backend tests use Pytest, with pytest-mock for mocking and HTTPX's async client for API-layer tests. Frontend unit/component tests use Vitest; end-to-end browser tests use Playwright (`docs/architecture/adr/0023-testing-strategy.md`). Do not introduce a second testing framework for a layer that already has a ratified one.

## 12. Documentation Standards

- `docs/architecture/` is the single source of truth for the system's architecture. Before implementing anything non-trivial, Claude reads the relevant document(s) first.
- Any change that affects module boundaries, event contracts, database schema, or a principle's application must update the corresponding document in `docs/architecture/` in the same change as the code — not as a follow-up, not "later."
- Where information needed to complete a task is missing from the documentation, Claude adds or updates a `TODO` marker rather than inventing an answer, and surfaces the gap explicitly rather than quietly guessing. If the gap is a genuine architectural risk (not just a missing implementation detail), it belongs in `docs/architecture/16-architecture-risks.md`, not a bare inline `TODO` that nobody tracks.
- Every technology/vendor choice referenced in `docs/architecture/08-technology-stack.md` has a corresponding ADR in `docs/architecture/adr/` recording why. Adopting a new dependency, vendor, or technology — or reversing an existing choice — requires a new ADR following the template in `docs/architecture/adr/README.md`, not a silent substitution in a PR.
- Documentation drift (code and docs disagreeing) is treated as a bug and fixed as part of whatever change is touching that area, not left for someone else.
- Do not create new documentation files beyond what the architecture set and task explicitly call for. Do not produce planning or summary documents unless asked.

## 13. Security Standards

- Authentication (Better Auth) and authorization (Casbin) are bought/adopted, not built (`docs/architecture/09-build-vs-buy.md`, `docs/architecture/adr/0010-identity-and-access.md`); Claude must never implement a bespoke auth mechanism, even a small or "temporary" one.
- **Better Auth runs in Next.js and is the sole Authentication Authority. The Python tier only ever *verifies* RS256 JWTs** (`docs/architecture/adr/0026-jwt-boundary-architecture.md`, `docs/architecture/18-authentication.md`). Claude must never add to the Python tier: a private signing key, a login or token-refresh route, an OAuth flow, password storage, or any code that authenticates a user directly. JWT parsing lives only in `signora_platform/auth/`.
- JWT verification pins allowed algorithms to exactly `["RS256"]`. Never widen this, and never accept an unpinned `algorithms` argument — it reopens `alg: none` and algorithm-confusion attacks.
- The `active_workspace_id` claim is a routing hint, never a grant. Membership is re-verified server-side against Workspace & Tenancy before RLS context is set, on every request.
- Never add a "skip auth in development" flag.
- Tenant isolation is layered and mandatory: RLS as the authoritative control, module-owned tables, application-level `workspace_id` filtering, and workspace-scoped event payloads — all four, always, per `docs/architecture/10-security.md` and `docs/architecture/11-tenancy.md`.
- No credentials, API keys, or secrets are ever hardcoded or committed. They are sourced from AWS Secrets Manager (`docs/architecture/adr/0022-devops-infrastructure-and-deployment-topology.md`); local development uses an equivalent `.env`-based mechanism that never shares values with production and is never committed.
- A sign-in OAuth token (Google/Microsoft, via Better Auth) must never be reused as an integration OAuth token (e.g., Gmail, Google Calendar) or vice versa — these are separate grants with separate scopes and separate storage.
- All external input — provider payloads, AI vendor output, third-party integration data — is treated as untrusted until validated and normalized by the module responsible for that boundary.
- Claude must flag, not silently fix in a way that hides risk, any code it encounters that appears to violate tenant isolation, leak secrets, or trust external input unsafely.

## 14. Performance Standards

- Work that is not required to complete within a request/response cycle runs in a background worker, not inline in a request handler (Principle 13). This is a default, not a case-by-case judgment call.
- Do not add caching, batching, or other performance mechanisms speculatively. Performance work is justified by the evidence-based triggers in `docs/architecture/12-scalability.md`, not by intuition about what "might get slow."
- Do not write code with obviously wasteful patterns (N+1 queries, unbounded fetches, synchronous loops over network calls) on the assumption it can be optimized later — obvious inefficiency is a defect at write time, not a future task, even though speculative optimization is also to be avoided. The line is: fix what you know is wrong; don't build for load you don't have evidence of.

## 15. Error Handling

- Every port (provider, AI vendor, integration, repository) exposes a small, explicit set of failure outcomes to its caller. Raw vendor/SDK exceptions never leak past the adapter that catches them.
- Distinguish transient failures (retry with backoff) from permanent failures (surface clearly, do not silently retry forever). Provide dead-lettering or an equivalent escape hatch for events/jobs that exhaust retries.
- Fail loudly and specifically. Do not swallow an exception to make a code path "just work," and do not return a generic error that discards the information needed to diagnose it.
- Validate AI and external provider output explicitly; treat a validation failure as a first-class error path with its own handling, not an edge case bolted on afterward.

## 16. Logging

- Every log line emitted from request handling or event processing includes `workspace_id` and `correlation_id` (and `causation_id` where applicable), per `docs/architecture/07-data-flow.md`.
- Use structured logging (key-value/fielded), not free-text string concatenation, so logs are queryable.
- Never log secrets, credentials, or raw PII without an explicit, approved policy for doing so.
- Log levels are meaningful and consistent: errors are actionable problems, warnings are unexpected-but-handled states, info marks significant lifecycle events, debug is verbose detail — do not default everything to one level.

## 17. Observability

- Pipeline stages should be instrumented for latency, throughput, and error rate, since these are the concrete inputs the scaling triggers in `docs/architecture/12-scalability.md` depend on.
- `correlation_id` propagation must be traceable end-to-end across every module a pipeline run touches — this is the primary debugging tool for the async pipeline and must not be treated as optional plumbing.
- Any new asynchronous flow introduced must be observable in the same way as existing ones (traceable, measurable) before it is considered complete — an untraceable background process is not production-ready.

## 18. Code Review Checklist

Before considering any change ready, verify:

- [ ] The change stays within one module's boundary, or crosses it only via an approved event/interface (§5).
- [ ] No direct cross-module database access was introduced.
- [ ] Domain logic is not duplicated from an existing module or an existing concept within the same module (§4).
- [ ] Clean Architecture layering is respected — no infrastructure leaking into domain/application (§6).
- [ ] Providers, AI vendors, and integrations are accessed only through their abstraction layers, never directly (§10, §13).
- [ ] New or changed tables have `workspace_id`, RLS, and forced RLS where required (§8).
- [ ] New or changed events follow the standard envelope and are cataloged in `docs/architecture/06-events.md` (§9).
- [ ] Tests exist and cover both the golden path and realistic failure modes (§11).
- [ ] Relevant `docs/architecture/` files are updated to match the change (§12).
- [ ] No hardcoded secrets, no new unapproved dependency, no unexplained deviation from an existing pattern.
- [ ] Logging includes `workspace_id`/`correlation_id` where applicable (§16).

## 19. Definition of Done

A task is done only when all of the following are true:

- The implementation satisfies the stated requirement, scoped to that requirement — nothing more, nothing speculative.
- It complies with every applicable rule in this document and the referenced architecture documents.
- Tests are written, passing, and cover meaningful failure paths, not only the golden path.
- Any affected `docs/architecture/` document is updated in the same change.
- No module boundary, tenancy, security, or event-contract rule has been bypassed, worked around, or silently weakened.
- The change has been reviewed against the checklist in §18.
- Nothing was left half-implemented, commented out, or gated behind an unused flag "for later."

### Milestone Definition of Done

*Binding from M6 onward.* A **milestone** is complete only when every one of the following has been satisfied. Not most of them, and not "everything but the push."

**Implementation** — code complete.

**Quality** — all tests passing · coverage gate passing · `make smoke` green · import-linter green · MyPy strict clean.

**Architecture** — every affected `docs/architecture/` document updated · `21-intelligence-pipeline.md` updated if the pipeline changed · `docs/SESSION_HANDOFF.md` updated · `PROJECT_STATUS.md` updated.

**Repository** — changes committed with meaningful messages · **pushed to `origin/main`** · working tree clean.

> **The repository must always represent the complete and authoritative project state.** A milestone that is finished locally but unpushed, or whose dashboard still describes the previous one, is not finished — the next session would resume from a lie.

**Announcing completion is the last step, not the first.** Claude must not report a milestone complete until every item above is verified, and must state plainly which are outstanding if any are.

## 20. Anti-Patterns

Claude must actively recognize and avoid:

- Reaching into another module's tables or internals "just this once."
- Inventing a new architectural concept, module, or event mid-task instead of raising it as a proposal.
- Building an in-house version of a bought capability because integrating the vendor felt slower.
- Calling a provider, AI vendor, or integration SDK directly from domain or application code.
- Synchronous, in-request calls to providers, AI vendors, or other modules' write paths.
- Anemic domain models with all logic pushed into generic services.
- Silent documentation drift — code changing without the architecture docs following.
- Tests weakened, skipped, or deleted to make a change appear to pass.
- Speculative abstraction, configuration, or generalization for requirements that do not yet exist.
- Swallowing errors, or leaking raw vendor exceptions past an adapter boundary.
- Trusting client-supplied workspace identifiers without server-side membership verification.
- Logging without `workspace_id`/`correlation_id`, making a pipeline run untraceable.

## 20a. Platform Freeze

**On completion of M1.3A, `signora_platform/` is architecturally frozen.**

The platform is the substrate all thirteen pipeline modules are built on: the event bus, tenancy primitives, authentication verification, authorization, observability, pagination, and settings. Once it is proven deployable, its value comes from being *stable* — a module written against it in M7 must behave the same as one written in M2.

After the freeze, Claude must not modify `signora_platform/` internals except for:

- **Security fixes** — a tenancy, authentication, authorization, or secrets defect. Fix it, and add a Security Invariant proving it stays fixed.
- **Production defects** — the platform is demonstrably wrong or losing data. A module finding the platform inconvenient is not a defect.
- **Explicitly approved architectural changes** — raised through the RFC process in `docs/architecture/01-overview.md` and approved before implementation, never decided inside a coding session.

What the freeze does **not** prohibit: adding a new subscription, registering a new event type, adding a worker pool, or extending the Security Invariants suite. Those are uses of the platform, not changes to it.

What it does prohibit: reshaping a platform interface because one module would find a different shape convenient, adding a parameter for a single caller, or "small" refactors of platform internals bundled into a module's milestone. If a module cannot be built without changing the platform, that is a finding to raise — it usually means either the module or the platform is modelled wrongly, and both answers belong to the architecture, not to the module's implementation.

**A frozen platform is not a finished one.** It is one where change requires a stated reason.

---

## 20b. Infrastructure Contract

Cloud infrastructure is deferred to M14.5; cloud *readiness* is not. Every change must keep the application deployable to the topology in `docs/architecture/adr/0022-devops-infrastructure-and-deployment-topology.md`, so that M14.5 provisions infrastructure for an application already ready for it rather than beginning a migration.

Claude must preserve, in every milestone: **stateless services** (no process holds state another needs; scaling to *n* replicas changes throughput only) · **environment-based configuration** (every value through a typed `Settings` object owned by the module whose behaviour it governs, constructed only at the composition root; no module calls `os.environ` — §6) · **Twelve-Factor compliance** (backing services attached by URL, processes disposable, admin tasks as one-off processes, logs to stdout) · **storage abstraction** (nothing writes to local disk expecting persistence; object storage through a port) · **health endpoints** (liveness that touches no dependency) · **readiness endpoints** (dependency-aware, 503 when not ready) · **structured logging** (fielded JSON to stdout with `workspace_id` and `correlation_id`) · **OpenTelemetry** (every new async flow traceable before it is complete) · **secret injection via configuration** (no secret in an image, repository, or default) · **production Docker images** (multi-stage, non-root, no build toolchain in the runtime layer).

Claude must not accept a change that violates this contract, **including one that would be "fixed during M14.5"**. A violation is cheap to prevent and expensive to unwind once built upon. If a module appears to require statefulness, local disk, or configuration outside `Settings`, raise it — do not take a temporary exception.

`make smoke` is what enforces this. Run it before considering any milestone complete.

---

## 20c. Frontend Foundation

From M1.5, the frontend foundation is **frozen** on the same terms as the platform (§20a). Business milestones **consume** the Design System, Shared Components, Application Shell, Query Layer, Authentication integration, and Routing; they do not modify them.

Changes are permitted only for:

- a **production defect** — the foundation is demonstrably wrong;
- an **accessibility issue** — a missing label, an unreachable control, a lost focus state. These are defects, not enhancements, and never wait for a business milestone to justify them;
- a **security issue**;
- an **explicitly approved architectural change** (RFC).

Concretely, Claude must:

- **Compose pages from `components/ui`**, never restyle a shared component for one page's benefit. A component bent to suit one caller is slightly wrong for every other, and the cost lands on whoever writes the next page.
- **Use design tokens, never literal colours.** No Tailwind palette utility (`bg-slate-100`), no hex, no `dark:` variant in a component. A theme change must be a token edit — enforced by `frontend/tests/components/design-tokens.test.tsx` (AC-15).
- **Add to the library rather than around it.** A genuinely new component belongs in `components/ui` with its tokens and its test; a page-local variant of an existing one does not.
- **Never introduce mock business data.** Screens without a shipped module behind them ship a designed empty state. Business UI is built against real domain contracts produced by the Provider Simulation Framework (AC-14, enforced by `frontend/tests/components/no-mock-data.test.tsx`).
- **Keep client-side permission checks presentational.** Casbin on the server is the authorization decision; hiding a control the caller cannot use is a courtesy, never enforcement, and must never be the only check.

---

## 20c-2. Local-First Development

**Binding from 2026-07-29. Permanent until explicitly reversed by the product owner.** See `docs/architecture/adr/0027-local-first-development.md`.

Signora is in an architecture-first phase, and the most valuable thing being built is the architecture, not the delivery pipeline. Every milestone is already verified on the developer's machine. Re-running the same verification remotely adds no confidence — it consumes time, minutes, and attention, and it makes a `git push` mean something other than *"store the repository safely."*

**GitHub exists for exactly three things:** version control · remote backup · future collaboration.

**GitHub is not** the build system, the test system, the release system, the deployment system, a scheduler, or a place where evaluation runs.

> **A `git push` performs one action: it stores the repository remotely. Nothing else may happen as a result of it.**

Claude must **never** create or re-enable: GitHub Actions · GitLab CI · Jenkins · CircleCI · Azure Pipelines · Buildkite · release automation · Docker or package or container publishing · scheduled workflows · automatic deployment, tagging, releases, or documentation publishing · cloud testing · remote smoke tests, integration tests, or evaluations.

**Existing workflow files are retained and must not be improved, expanded, modernised, optimised, or deleted.** They exist as correct definitions to re-activate from. Their only permitted trigger is `workflow_dispatch`; adding `push:`, `pull_request:`, or `schedule:` to any of them is prohibited.

**Every quality gate is local, and all of them still bind:** `pytest` with the coverage gate · `make smoke` · `mypy --strict` · `lint-imports` · the Security Invariants suite · migration reversibility. A gate moving from CI to local does not make it optional — it makes the local run the only run, and therefore the one that decides.

CI/CD returns only when **all five** hold: the architecture has stabilised · the Intelligence Pipeline has stabilised · the Workflow Pipeline has stabilised · the AI Platform has stabilised · **the product owner explicitly requests it.** Until then the correct quantity of CI is **zero** — not a smaller amount, and not a better version.

The ordering this expresses, which applies beyond CI: **architecture first · implementation second · automation third · deployment last.** Every piece of automation introduced today is maintenance tomorrow. Automate for demonstrated need, never anticipated need.

---

## 20d. Milestone Discipline and the Project Status Record

### Strict milestone ownership

**Each milestone validates only the capabilities it owns.** Claude must not implement future-milestone functionality to satisfy the current milestone's demonstration — that trades a clean incremental history for a demo, and the borrowed code arrives unreviewed, untested against its own acceptance criteria, and owned by nobody.

When a milestone's stated demonstration turns out to require a capability it does not own, that is a **finding to raise**, not a licence to build ahead. The correct resolution is to move the demonstration to the milestone that owns the capability (a Category 1 change, §5c of the roadmap), as was done with *"simulated payloads traverse the production pipeline"* — moved from M2.0 to M2.1, where the consumer actually lives.

### `docs/SESSION_HANDOFF.md` is the continuation point

Updated at every milestone boundary, alongside `PROJECT_STATUS.md`. It captures project position, the permanent architectural contracts, Product Pipeline state, design philosophy, the next milestone's starting context and open questions, and a "Next Session Starting Point" block.

Its purpose is that a session can begin immediately without rereading milestone history. Claude should read it first in a new session, and update it when closing a milestone.

### `PROJECT_STATUS.md` is authoritative

It is the **executive dashboard**, not a progress log. It must answer, at a glance:

> **Where are we now? · What was completed? · What changed architecturally? · What is intentionally deferred? · What's next? · Are we on track?**

**After every completed implementation milestone, Claude must update it *before* beginning the next.** Implementation of the next milestone does not begin until it reflects the latest approved state.

Each update includes: milestone status (Completed / In Progress / Blocked) · completion date · commit hashes · **current `HEAD`** · scope delivered · acceptance criteria satisfied · **tests, coverage, Security Invariants, and import-linter contracts** · outstanding architectural work · outstanding deferred items · **known limitations, distinguished from architectural debt** · roadmap changes · new architectural decisions · technical debt introduced or repaid · risks and blockers · updated implementation progress · updated effort remaining · updated projected timeline · links to new ADRs, architecture documents, or implementation notes.

**It must describe the implementation, never the proposal.** Before announcing a milestone complete, Claude verifies each figure against the repository — the test count from a run, the coverage from the gate, `HEAD` from git — rather than carrying forward what was planned. The documentation update is committed *with* the milestone and pushed with it, not after.

---

## 20e. Parallel Development — Lanes

**Binding from 2026-08-01.** Signora is worked by more than one session at a time. This section is what makes that safe; it changes no architecture, and every freeze, boundary and gate above binds unchanged — **they matter more, not less.**

### The lanes

| Lane | Branch | Owns | Builds features? |
|---|---|---|---|
| **A — Product Surface** | `lane-a-product-surface` | The pipeline's `interface/` layers · `frontend/app/(app)/` except `settings/products` · `frontend/components/intelligence/` | Yes |
| **B — Commercial Profile** | `lane-b-commercial-profile` | `modules/commercial_profile/**` · `apps/api/composition/products.py` · `frontend/components/commercial/` · `frontend/app/(app)/settings/products/` · `frontend/lib/query/hooks/commercial.ts` | Yes |
| **QE — Quality Engineering** | `lane-qe` | `backend/tests/**` except a module's own suite · `frontend/tests/**` except a lane's own component tests · `docs/BUGS.md` · Playground scenarios · product reviews | **No** |
| **Integrator** | `integration`, `main` | Merges, shared documents, certification, release | No |

**One session per lane. One lane per module.** A module has exactly one implementation owner; if a lane needs a change inside another lane's module, that is a **finding to raise, never a change to make.**

### The Change Budget

Every slice knows what it may touch before it starts.

| Tier | Contains | Authority |
|---|---|---|
| 🟢 **Green** | Your own module's `domain`/`application`/`infrastructure`/`interface` · its tests · its design doc · your own frontend components and routes · a bug fix inside your module | Lane, freely |
| 🟠 **Amber** | Your module's `public/` · a new table (**with its `tenancy_policy.py` registration**) · a new event (**with its `06-events.md` entry**) · a new endpoint · a new component in `components/ui` · a migration | Lane — **announce it in the commit message** |
| 🔴 **Red** | `signora_platform/**` · the frontend foundation (`components/ui`, `lib/query`, `lib/state`, shell) · a new module or bounded context · a new cross-module dependency · a new dependency · `docs/architecture/01`–`21` · `adr/` · any frozen decision · the roadmap | **Product owner + ADR** |
| ⚫ **Black** | Rename an API · move architecture · rewrite documentation · refactor another lane's module · weaken or delete a Security Invariant · rewrite a dated record · create CI/CD (§20c-2) | Never |

**Touching a file outside your budget is a finding to raise, not a change to make.** The same discipline as §20a, applied to the whole repository.

### Shared files have one owner

Together these appear in roughly two thirds of all commits. **A lane does not edit them.**

| File | Owner |
|---|---|
| `PROJECT_STATUS.md` · `docs/SESSION_HANDOFF.md` · `docs/RUNNING.md` · the roadmaps | **Integrator**, at merge |
| `docs/architecture/38-product-design-principles.md` · `39-product-review-findings.md` | **Integrator**, at merge |
| `docs/BUGS.md` | **QE** — the only lane that opens and closes rows; a feature lane edits only the `Status` of a bug it has fixed |
| `CLAUDE.md` · `PRODUCT_DIFFERENTIATORS.md` | Product owner |
| `apps/api/main.py` · `pyproject.toml` contracts · `tenancy_policy.py` · `policy.csv` · `lib/api/types.ts` · `lib/query/keys.ts` | Any lane — **append-only, one line, alphabetical where a list exists** |

**A lane reports its findings in its commit message and its own module's design doc.** The integrator folds them into the shared records at merge. That reduces narrative-document conflicts to zero rather than managing them.

### Branches and merge order

```
lane-a-product-surface ─┐
lane-b-commercial-profile ─┼─▶ integration ─▶ QE validates ─▶ main ─▶ certify ─▶ release
lane-qe ────────────────┘
```

| Branch | Lifetime | Who merges into it |
|---|---|---|
| `main` | Permanent. **Always certifiable** | Integrator, from `integration` only |
| `integration` | Permanent. Where lanes meet and QE tests | Each lane, its own slice |
| `lane-*` | **Permanent name, one slice of content.** Reset to `integration` after every merge | Its own session only |

**Rules, and they are short:**

- **Branch content lives one slice — two days maximum.** A lane branch carrying more than one slice is a finding.
- **Rebase, never merge, onto `integration`.** Rebase freely: nobody else has your lane branch.
- **Fast-forward only, everywhere.** No merge commits. `main` advances only from `integration`, so `main` is always an ancestor of it and the fast-forward always succeeds. Three reasons this is not taste: Alembic's chain is linear, the records are append-only narratives, and a linear history is the only one where *what was true when* is readable.
- **The gates are the review.** Full local gates on the rebased branch before it merges to `integration`.
- **Conflicts are resolved by the lane that is rebasing**, never by the integrator — the lane knows what its change meant. A conflict in a 🔴 file means the lane was outside its budget; stop and raise it.
- **Commit messages keep the existing form:** `M12.5 — <what changed, in product language>`. Not Conventional Commits — `git log --oneline` is a changelog a cold session reads.

### The canonical merge flow

Seven steps. **Every one names who does it**, because an unowned step is where parallel work stalls.

| # | Step | Who | What |
|---|---|---|---|
| 1 | **Slice** | Lane | Declare the Change Budget, implement, write tests |
| 2 | **Impacted tests** | Lane | Its module suite, impacted integration tests, `mypy --strict`, `lint-imports`, frontend suite, production build |
| 3 | **Push the lane branch** | Lane | `git push origin lane-<x>`. **Backup, not a trigger** — a push stores the repository and starts nothing (§20c-2) |
| 4 | **Rebase and merge to `integration`** | Lane | `git pull --rebase origin integration`, re-run gates, then `--ff-only`. **The lane resolves its own conflicts** |
| 5 | **QE validation** | **QE** | Full backend suite with the coverage gate · Security Invariants · `make smoke` · **exploratory use of the product**. Defects become `B-nnn` rows |
| 6 | **Certification** *(when applicable)* | Integrator | Milestone boundaries only: `make certify`, migration reversibility, `make dr` (ADR-0032) |
| 7 | **Fast-forward to `main`** | Integrator | Promotion, not re-verification — QE has already run everything. Then folds lane findings into the shared records |

**`integration` never fast-forwards to `main` with an open 🔴 bug.** That is the one blocking rule; 🟠 and below are the product owner's call.

**A lane resets its branch to `integration` after step 7** and starts the next slice from there.

### Which gates run when

| Moment | Runs | Why |
|---|---|---|
| **During a slice** | Impacted suites only · `mypy` · `tsc` · `eslint` | Unchanged policy. Speed is the point |
| **Lane → `integration`** | The lane's full module suite · impacted integration tests · `lint-imports` · `mypy --strict` · frontend suite · production build | The lane proves its own slice |
| **On `integration`, by QE** | **Everything**: full backend suite with the coverage gate · Security Invariants · `make smoke` · exploratory use of the product | The only place merged code is exercised together |
| **`integration` → `main`** | Nothing new — QE has already run it | Promotion, not re-verification |
| **Milestone close** | `make certify` · migration reversibility · `make dr` | ADR-0032 |

**`make smoke` binds ports 3000 and 8000**, so every lane's dev server must be stopped before it runs. That is why it belongs to QE on `integration` rather than to a lane.

### Quality Engineering

**QE builds no production feature.** It owns functional, API, end-to-end, security, performance and accessibility testing, Playground validation, product reviews, regression, and certification support.

> **QE reports bugs. Feature lanes fix them.** A QE session that fixes a defect in a feature lane's module has become a second implementation stream with no owner, and the module's owner no longer knows what their module does.

**Why a lane rather than a phase:** every defect that has mattered in this project was found by *using* the product, not by the suite. 2046 tests found none of R4-01, R6-01–04, R7-01–03, R10-01 or R12-01. A lane whose whole job is to use the product is the only mechanism that finds that class reliably, and a lane finds it continuously rather than when somebody remembers.

**QE may write tests in another lane's module suite** — that is its job — but may not change that module's production code. A failing test it adds is a bug report in executable form, and the owning lane makes it pass.

### Bugs

**One register: [`docs/BUGS.md`](docs/BUGS.md).** Not a file per bug, not an issue tracker, not scattered TODOs.

Every row carries: **ID · Title · Owner lane · Severity · Status · Commit found · Steps · Expected · Actual.**

| | |
|---|---|
| **Opens a bug** | QE, or any lane that finds one outside its own budget |
| **Fixes it** | The **owning lane** — the lane that owns the module the defect is in |
| **Verifies and closes** | **QE**, never the lane that fixed it |
| **Severity** | 🔴 blocks a milestone · 🟠 wrong behaviour a customer would hit · 🟡 wrong but survivable · 🟢 cosmetic |

**A bug fixed without a regression test is not fixed** (§11). The test belongs in the owning module's suite and is written by the lane that fixes it.

### Concurrent milestones — amending §20d

§20d requires `PROJECT_STATUS.md` to reflect the previous milestone before the next begins, and [IMPLEMENTATION_ROADMAP.md §1](IMPLEMENTATION_ROADMAP.md) recorded *sequential single-stream execution*. **Both were written for one session and are amended here, as a Category 1 sequencing change.**

> **Lanes may run concurrent milestones. The rule now binds per lane:** a lane does not begin its next milestone until `PROJECT_STATUS.md` reflects the previous one **of that lane**. The dependency graph still governs order — a lane may not start work whose inputs another lane has not shipped.

Everything else in §20d is unchanged, and **strict milestone ownership matters more, not less**: a lane must never implement another lane's functionality to satisfy its own demonstration.

---

## 21. Rules for Claude Code

### Claude must never

- Invent architecture. If the agreed architecture in `docs/architecture/` doesn't cover a situation, surface the gap — do not silently decide it.
- Create duplicate business logic. Search for an existing implementation of a concept before adding a new one.
- Break module boundaries as defined in `docs/architecture/05-module-dependencies.md`.
- Access another module's database directly, under any justification.
- Duplicate domain models across modules or within a module.
- Skip tests, for any reason, including time pressure or perceived triviality.
- Ignore documentation — either by not reading it first, or by not updating it after a change that affects it.
- Hardcode provider implementations instead of going through the provider/AI/integration abstraction layers.
- Mix infrastructure concerns with business logic inside a domain or application layer.
- Introduce new frameworks or major dependencies without explicit approval.
- Change database schema without updating the corresponding architecture documentation in the same change.
- Modify `signora_platform/` internals after the M1.3A freeze without a security fix, a production defect, or explicit approval (§20a).
- Read a platform infrastructure table from module code, or restore a read grant on one to `signora_app` (§8).
- Introduce statefulness, local-disk persistence, or configuration outside a typed `Settings` object — the Infrastructure Contract binds every milestone until M14.5 provisions cloud infrastructure (§20b). Equally: never add a module's configuration to `signora_platform/settings.py` because it is the file that already exists (§6).
- Modify a shared frontend component, the shell, routing, or query infrastructure to suit one page, or introduce mock business data (§20c).
- Implement a future milestone's functionality to satisfy the current milestone's demonstration, or begin a milestone before `PROJECT_STATUS.md` reflects the previous one (§20d).
- Create, re-enable, or extend any CI/CD, publishing, scheduling, or remote-execution automation, or add a `push:`/`pull_request:`/`schedule:` trigger to a retained workflow (§20c-2).
- Leave the repository asserting something that is not true of it — a live-looking disabled workflow, a gate that no longer runs, a dashboard describing the previous milestone (§2). Equally: rewrite a dated record of what was true then to match what is true now.

### When implementing, Claude must always

- Read the relevant documentation first, before writing code.
- Follow the existing architecture as documented — implementation follows the design, it does not redesign as it goes.
- Implement one module at a time, respecting that module's boundary throughout.
- Keep modules independent, communicating primarily through events per the approved dependency graph.
- Prefer interfaces (ports) over concrete implementations at every infrastructure boundary.
- Write tests as part of the implementation, not as a follow-up step.
- Update documentation as part of the same change, not afterward.
- Use type hints / strong typing throughout.
- Follow Clean Architecture inside every module, without exception.
- Use dependency injection to wire infrastructure into domain/application code.
- Generate production-quality code: no placeholders, no TODOs left in application code where a real answer was knowable, no half-finished implementations.

### Operating behavior

- When a task is ambiguous with respect to module ownership, resolve that against `docs/architecture/04-modules.md` before writing code.
- When a task appears to require an architectural decision (a new module, a new cross-module dependency, a new principle exception), stop and raise it rather than deciding it unilaterally — this belongs to the RFC process in `docs/architecture/01-overview.md`.
- When information required to proceed correctly is missing from the documentation, say so and propose a `TODO`, rather than filling the gap with an assumption.
- Treat this file and `docs/architecture/` as living documents: when they are wrong or out of date relative to a deliberate, approved change, update them — but never drift from them silently.
