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
- **Governance describes reality; it never quietly changes it** (ratified 2026-08-03, product owner). **Any behavioural change requires an explicit architectural or product decision *before* governance is updated** — the document records the decision, it does not constitute it.

  **Found by nearly committing the opposite.** A description of the lanes' strategic direction implied a module ownership swap between two lanes, both mid-flight. Written into the governance files as prose, it would have reassigned two bounded contexts through a documentation edit that nobody would have recognised as a decision — and the next reader would have inferred it from commit history rather than from a ruling.

  This is the general form of *the repository itself should always tell the truth* above, applied to the **direction of causation.** That rule says a document must not misdescribe reality. This one says a document must not *become* the reality. A governance edit that changes what the software or the organisation does is a decision wearing a document's clothes, and the tell is simple: **if applying the edit would change what somebody does tomorrow, it needed a decision yesterday.**

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
- **The brand is Fortune. The product is Signora. They are two concepts and the repository keeps them apart** (ratified 2026-08-04, product owner; drafted by Lane C on that instruction). The pattern is Microsoft→Teams, Adobe→Photoshop: **a customer buys from the Fortune portfolio and uses Signora.**

  > **Wherever the product speaks — the assistant, notifications, emails, tooltips, help, empty states, system messages, UI copy, API documentation, prompts, examples — it is `Signora`, alone.** *Signora found · Signora recommends · Ask Signora.* **Never *"Fortune Signora recommends"*.**
  >
  > **`Fortune Signora` is the combined brand, reserved for branding surfaces** — landing and marketing pages, splash, logo, **application and browser title**, installer, licence, copyright, legal, press. **Once the application is open, the experience belongs to Signora.** The AI assistant is `Signora`, never `Fortune Signora`.

  **Prospective, never a rename exercise.** No repository-wide sweep, no standalone cosmetic commit. **The inventory is [421](docs/architecture/421-product-naming-inventory.md), and it is empty: `git grep "Fortune Signora"` returns zero matches.**

  **This is [ADR-0034](docs/architecture/adr/0034-ubiquitous-language.md) applied to the product's own name**, landing in the same place: **the translation lives at the frontend edge and never travels inward.** No module, table, column, package, API path or architecture document is renamed — `signora_platform`, `signora-frontend` and `signora_app` are correct and stay.

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
- Endpoints must not perform work that belongs in the background. **The rule and its subject are [02-principles.md §13](docs/architecture/02-principles.md), which is authoritative and is deliberately not restated here**: it governs *work **not required to complete within the request/response cycle*** — provider polling, normalization, the observation/event/signal/opportunity pipeline, AI reasoning, recommendation generation. That work is dispatched to background workers (`docs/architecture/07-data-flow.md`), and a handler responds once the request has been durably accepted.

  > ⚠️ **This bullet previously paraphrased Principle 13 and widened it** — *"provider polling"* became *"provider calls"*, forbidding something the architecture permits. **Repaired 2026-08-06 by [D-112](docs/DECISION_REGISTER.md), ruling [C-104](docs/LANE_COORDINATION.md), by reference rather than by a better paraphrase: a second paraphrase is the same defect one generation later.**

  **A synchronous outbound call is permitted only where all four hold**, and they are cumulative rather than indicative:

  **①** the call's result **is** the response — not a side effect of producing it;
  **②** nothing about the customer's data is read into the pipeline, stored, normalized, or made visible to any other module;
  **③** the call is bounded by an explicit timeout owned by the calling module;
  **④** the vendor is reached only through a port that module owns.

  **`POST /workspaces/{id}/connections/{id}/check` is the worked example and currently the only one** ([C-104](docs/LANE_COORDINATION.md)). It asks whether a door opens and closes it again.

  ⛔ **This is not a latency exemption.** ***Quick* is not one of the four**, and a stage that ingests a single record fails ② however fast it is. **①+② are the load-bearing pair — a pipeline stage fails both, not one.**
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
- **AI execution has three modes, and development's is deterministic** (ratified 2026-08-04, product owner; `docs/architecture/adr/0028-model-runtime-by-environment.md` as amended, assessed in `docs/architecture/431-ai-execution-modes.md`).

  | Mode | Provider |
  |---|---|
  | **Development** — **the default** | **The deterministic mock provider.** Backend, frontend, business logic, workflows, API and repository tests |
  | **Evaluation** | **Configurable** — mock · Ollama · Anthropic · OpenAI · Azure OpenAI · Bedrock · Vertex AI · future adapters. **Locally the mock is the default; evaluation never forces a provider** |
  | **Production** | **Customer-configured.** The only mode whose behaviour represents production |

  > **Development must never require a locally running LLM** unless a developer is explicitly testing provider integration. **No implementation may assume Ollama is installed unless a developer explicitly selects it.** A fresh clone is productive with no local model.

  **Three concerns, and they must not share an execution path: functional correctness · provider integration · model quality.** Business logic is testable without any LLM; prompt quality is measurable without business workflows; provider integration is testable without prompt quality.

  **The mock follows the contract; the contract never follows the mock.** It implements **only** what `AIProviderAdapter` already defines — **no streaming, no tool calling, no speculative provider features.** When the port evolves, the mock evolves **in the same change and never before it**.

  > ⚠️ **The mock must never be available in production, and this is a repository invariant rather than a convention.** **A production deployment configured to use it fails fast with a diagnostic naming the cause.** A production service answering from a deterministic stub is **indistinguishable from one that is working** — which is strictly worse than the outage it would be hiding.

  **Ollama remains supported and stops being assumed.** It is still **never a production dependency, never a fallback, and never a cost tier**, and Claude must never configure a deployed service to reach a local runtime.

  **Every evaluation record captures provider · model · version where available · prompt version · protocol version.** **Provider is operational metadata about a run, never an input to a decision** — business behaviour still may not branch on a vendor, and the harness still names a *model*.

  > ⚠️ **Amended 2026-08-05: `execution mode` was the sixth field and is removed.** **Lane B declined to build it, out loud and with a reason, rather than dropping it silently** — *"an evaluation run is in Evaluation mode by construction, so the field would carry one value on every row it could ever have."* **The product owner accepted the challenge**: *"if a field is constant for every possible record then it carries no information."*
  >
  > **§2 already forbade it** — a column with one possible value is the decorative class. **The fact anybody needs is whether a real model was measured, and `provider` answers it.** **If the mode is ever meant to vary, the row that needs it says how.**
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
- **Documentation is part of the implementation, not a follow-up to it** (ratified 2026-08-01). **A slice is not complete until the implementation, its tests, and its module's documentation are consistent with each other.** Two of the three passing is an unfinished slice, not a finished one with paperwork outstanding.

  **The reason is rotation.** Lanes are temporary execution resources and modules are permanent boundaries (§20e), so **the lane that implements the next slice of a module is usually not the one that implemented the last.** It inherits the module's design doc, its ADRs and the Slice Handoff — and nothing else. Under permanent ownership a drifted design doc was an inconvenience a session could work around from memory; under rotation **it is the mechanism by which the next assignee is actively misled**, and it will be believed, because there is nothing else to believe.

  The test to apply before calling a slice done: **could a lane that has never seen this module continue the work without reading commit history?** If the answer needs *"well, you'd have to know that…"*, the missing sentence belongs in the module's design doc before the slice closes.

  This is not a licence to write more documents (§12 above still binds). It is a requirement that the ones that exist stay true.

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
- **Implementation, tests and the module's documentation are consistent** — a slice with two of the three is unfinished (§12). **A different lane could continue the work without reading commit history.**
- Any affected `docs/architecture/` document is updated in the same change.
- No module boundary, tenancy, security, or event-contract rule has been bypassed, worked around, or silently weakened.
- The change has been reviewed against the checklist in §18.
- Nothing was left half-implemented, commented out, or gated behind an unused flag "for later."

**Quality is the lane's, before it is QE's** (ratified 2026-08-02, product owner, after three candidates were rejected on coverage a lane could have seen in seconds). **A slice is implementation-complete only when all of these hold** — and the lane, not QE, establishes them:

| | |
|---|---|
| **Implementation complete** | The requirement, at the scope required |
| **Tests complete** | Golden path *and* realistic failure modes (§11) |
| **Coverage expectations met** | **`make coverage-debt ARGS="<your module>"`** — no file the slice introduced sits at 0%, and the slice does not push the repository under the floor |
| **Type checking clean** | `mypy --strict` · `tsc --noEmit` |
| **Import contracts clean** | `lint-imports` |
| **Migrations verified** | Reversible to base and back, if the slice adds one |
| **Documentation updated** | The module's design doc, consistent with the code (§12) |
| **Self-validation performed** | The lane ran its own gates on the **rebased** branch |
| **Independently demonstrable** | §2 — showable without naming a module, a table or a port |
| ⚡ **Customer journey automated *and executed*** | **For every customer-visible slice: a Playwright scenario that completes the journey — written by the implementing lane, and *run by it before the push*** ([D-114](docs/DECISION_REGISTER.md)). ⚡ **`python3 infra/certification-guard.py --journeys` names which specs the change selects; the mapping is deterministic and not a judgement call.** ⛔ **The responsibility does not end with writing the tests. It includes executing them** ([D-113](docs/DECISION_REGISTER.md), [`ENGINEERING_LAWS.md`](ENGINEERING_LAWS.md) L-15 gate 8). **A UI slice is not complete until its scenario is written and passing.** ⛔ **A journey, never a control** — *button exists* and *modal opens* are component tests and belong in `frontend/tests/components/`. ⚡ **Headed is the default for local development and review; QE chooses the mode for certification** — **[D-134](docs/DECISION_REGISTER.md), and see *The headed-execution policy* below** |
| ⚡ **Visually reviewed in headed mode** | **Before handover to QE, the implementing lane runs the completed journey headed and watches it** ([D-134](docs/DECISION_REGISTER.md)). ⛔ **The purpose is not verification — the assertions already did that. It is continuous product review.** **What is being watched: screen transitions · navigation flow · animations and interactions · loading states · empty states · error states · form validation · responsiveness where applicable · and overall consistency with the finalized design system ([D-128](docs/DECISION_REGISTER.md)).** ⚡ **The journey is implementation evidence** — it demonstrates that the complete customer experience works end to end, **not merely that the assertions passed** |
| **UI states covered** | **Loading · empty · error · permissions · accessibility where applicable.** ⚠️ **And the error state is the one that gets skipped** — [P-A](docs/DOMAIN_DISCOVERY_REGISTER.md): *a failed read must never render as an empty result*, which [C-226](docs/LANE_COORDINATION.md) found six times on one screen |
| **Engineering Laws satisfied** | **The eleven handover gates in [`ENGINEERING_LAWS.md`](ENGINEERING_LAWS.md) §L-15** — reuse audit · behaviour preservation · data preservation · migration contract · backward compatibility · architecture consistency · runtime composition · customer journey · documentation · QE impact · no blocking defect |
| **Ready for QE validation** | All of the above **before** the handover, not after the rejection |

> **QE validates that this happened. QE does not make it happen.** A coverage gap found at certification is the same gap that was visible to the lane in seconds — `make coverage-debt` reads the data `pytest --cov` already wrote and names the file. **Quality moves left because it is cheaper there, not because QE minds looking.**

### The headed-execution policy

**Ratified 2026-08-06, product owner, [D-134](docs/DECISION_REGISTER.md). Drafted by Lane C on that instruction, which is the only route by which this file is amended.**

> ## **Headed is the default mode for local development and review. Certification may run headless.**

**The reason is not debugging.** ⚡ ***"The purpose is not only verification, but also continuous product review."*** **A passing assertion says a control was found and clicked. It says nothing about whether the transition was jarring, the empty state was designed, the error state existed, or the screen matched the approved design** — and **those are the defects this repository keeps finding by *using* the product rather than by testing it** (§20e: *every defect that has mattered in this project was found by using the product, not by the suite*).

| | |
|---|---|
| **Local development · review** | ⚡ **Headed.** **The lane watches the journey it built, as a customer would see it** |
| **Certification · QE** | **Headless, for speed and stability.** **QE chooses, unchanged** |

⚠️ **This is a change, not a restatement.** **`playwright.config.ts` reads `headless: process.env.HEADED !== '1'` — headless is today's default and `HEADED=1` opts in** — **and the line above previously described that as *"headed by default"*, which was not true of the repository** (§2). ⛔ **The text is corrected here and the behaviour is [TASK-476](docs/BACKLOG.md); a rule stated before the mechanism exists is the defect this file warns about, so the row exists rather than the claim.**

**The Playwright journey is implementation evidence.** It demonstrates that the complete customer experience works from beginning to end — **and a lane reporting a journey complete has watched it, not only run it.**

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

What the freeze does **not** prohibit: adding a new subscription, registering a new event type, adding a worker pool, **declaring a new authorization `Resource`**, or extending the Security Invariants suite. Those are uses of the platform, not changes to it.

> ⚠️ **`Resource` added 2026-08-05, ruled by the product owner at [C-224](docs/LANE_COORDINATION.md), and the distinction is the whole of it.**
> **Adding a `Resource` enum member is a *declarative registration*, never an authorization grant.** **Authorization is granted only through `policy.csv`** — *"a `Resource` entry without policy grants provides no runtime capability."*
>
> **The conflict this settles:** the enum sat in `signora_platform/**` (🔴, product owner + ADR) while `policy.csv` is a registry every lane extends. **One registration, two files, opposite authorities** — a policy row naming an absent member is unreachable, and a member with no policy row denies everyone. **They were never governing the same thing: one declares that a resource exists, the other decides who may act on it.**
>
> **Evidence, and it is why the ruling ratifies rather than changes:** **every `Resource` after `workspace` and `member` was added by a feature lane** — twelve of them, three carrying an inline §20a justification. **The practice was already this; the rule now says so.** **Do not reopen this** unless a future architectural change genuinely invalidates the assumption.

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

### The rulebook, and where each rule lives

> **This file is the repository's operating system. It states the rules; it does not carry the procedures.**
>
> **`CLAUDE.md` answers *"what are the rules?"* Every other document answers *"how do I perform this responsibility?"*** Where another document owns operational content, this one **references** it and never restates it — a rule written in two places is a rule that will eventually contradict itself, and the copy nobody is maintaining is the one somebody will read.

| Rule area | Stated here | Performed in |
|---|---|---|
| **Engineering principles** | §2 · §3 | — |
| **How an implementation is built** | §19 *(the gates)* · §20e *(the handoff)* | [`ENGINEERING_LAWS.md`](ENGINEERING_LAWS.md) — **the Repository Engineering Standard.** Thirteen laws: reuse, evidence, document-first, independent slices, customer capability, journey integrity, production path, behaviour and data preservation, evolution over replacement, migration contracts, debt classification, operational readiness |
| **Testing rules** | §11 | [`backend/tests/README.md`](backend/tests/README.md) · [`frontend/tests/README.md`](frontend/tests/README.md) |
| **Documentation rules** | §12 | the owning document itself |
| **Definition of Done · slice completion** | §19 · §20e *Completion* | — |
| **Change Budget** | §20e | — |
| **Work allocation** | §20e *Nobody assigns; lanes pull* | [`docs/BACKLOG.md`](docs/BACKLOG.md) — **the READY queue**, prioritized by the product owner |
| **Product-Led Domain Discovery** | §20e *Four responsibilities* — **Lane C prepares** | [`docs/DOMAIN_DISCOVERY_REGISTER.md`](docs/DOMAIN_DISCOVERY_REGISTER.md) — the register · [`PRODUCT_OFFICE.md` §5e](docs/PRODUCT_OFFICE.md) — the method. **The primary planning methodology from 2026-08-05, [D-076](docs/DECISION_REGISTER.md)** |
| **Claiming a task** | §20e *The Task Claim Protocol* | the claim commit itself — **atomic, because a push is** |
| **Task lifecycle states · who sets each** | §20e *Execution ownership ends at `IN VALIDATION`* | [`docs/BACKLOG.md`](docs/BACKLOG.md) · [`docs/ACTIVE_ASSIGNMENTS.md`](docs/ACTIVE_ASSIGNMENTS.md) — the two legends |
| **Lane assignment** | §20e *Modules are permanent* | [`docs/ACTIVE_ASSIGNMENTS.md`](docs/ACTIVE_ASSIGNMENTS.md) — **the execution board**, written by the claiming lane |
| **Implementation area vs integration cadence** | §20e *Implementation ownership and integration cadence are independent* | — |
| **Startup workflow** | §20e *Startup* | — |
| **Cross-lane communication** | §20e *The slice* | [`docs/LANE_COORDINATION.md`](docs/LANE_COORDINATION.md) |
| **Bug reporting** | §20e *Bugs* | [`docs/BUGS.md`](docs/BUGS.md) |
| **Coordination items** | §20e *Coordination* | [`docs/LANE_COORDINATION.md`](docs/LANE_COORDINATION.md) |
| **Environments** | §20e *Startup* step 6 | [`docs/RUNNING.md`](docs/RUNNING.md#running-a-lane) — **the allocation table** |
| **Test data policy** | §20e *Test data* | [`20-provider-simulation.md`](docs/architecture/20-provider-simulation.md) |
| **QE responsibilities** | §20e *The QE lifecycle* | [`docs/QUALITY_ENGINEERING.md`](docs/QUALITY_ENGINEERING.md) |
| **The repository cycle, end to end** | §20e *The QE lifecycle* | [`docs/REPOSITORY_RELEASE_CHECKLIST.md`](docs/REPOSITORY_RELEASE_CHECKLIST.md) — **the runbook** |
| **Removing an operational blocker** | §20e *QE removes its own blockers* | [`docs/RUNNING.md`](docs/RUNNING.md) — the prerequisites |
| **Promotion workflow** | §20e *Completion* | [`docs/QUALITY_ENGINEERING.md`](docs/QUALITY_ENGINEERING.md) |
| **Slice Handoff** | §20e *The Slice Handoff* | the commit message |
| **Repository certification** | §20e *Certification* · *Certification is attached to a commit* | [ADR-0032](docs/architecture/adr/0032-release-certification.md) · `make certify` · `infra/certification-guard.py` |
| **Repository state and metrics** | §20e *Repository state, and the assignment board* | `PROJECT_STATUS.md` · [`SESSION_HANDOFF.md`](docs/SESSION_HANDOFF.md) |
| **Release summary** | §20e *Repository Closeout* | `PROJECT_STATUS.md` |
| **Repository Closeout** | §20e *Repository Closeout* + its checklist | [`docs/QUALITY_ENGINEERING.md`](docs/QUALITY_ENGINEERING.md) — the playbook |
| **Repository state validation** | §20e *Repository State Validation* | `infra/state-check.py` |
| **Assignment board** | §20e *Repository state, and the assignment board* | [`docs/ACTIVE_ASSIGNMENTS.md`](docs/ACTIVE_ASSIGNMENTS.md) |
| **Branch synchronization** | §20e *Completion* step 12 | — |

**When a new repository-wide rule is needed, it belongs here** — not in the document that happened to prompt it. When a *procedure* is needed, it belongs in the document that owns the responsibility, and this table gains a row.

### Modules are permanent. Lanes are not.

**Parallel development exists to increase implementation velocity and to do nothing else.** It does not change the architecture, it does not change module boundaries, and it does not decentralize product decisions.

> **A module is a permanent architectural boundary. A lane is a temporary execution resource.**
>
> **A lane never owns a module. A lane is *assigned* an implementation slice inside one**, and the assignment changes while the architecture does not.

```
             Today                    Tomorrow                 Next week
  Lane 2  →  Commercial Profile   →   Timeline             →   Provider Platform
             slice 4                  slice 2                  slice 5
```

**Say *current assignee*, not *owner*, whenever the subject is active development work.** *Owner* is reserved for what genuinely does not move: the module that owns a table, an event, a bounded context, a piece of vocabulary. Confusing the two is how a temporary allocation starts to read like an architectural fact — and how the next lane assigned to that module believes it inherited a boundary that was only ever a rota.

**The invariant that makes it safe is unchanged:** *one session per lane, and* **one assignee per module at a time.** If a lane needs a change inside a module it is not assigned, that is a **finding to raise, never a change to make** — [`LANE_COORDINATION.md`](docs/LANE_COORDINATION.md) if it is a dependency, [`BUGS.md`](docs/BUGS.md) if it is a defect.

**Current assignments live in [`docs/ACTIVE_ASSIGNMENTS.md`](docs/ACTIVE_ASSIGNMENTS.md)**, the execution board — the one place they are recorded, and the first thing a session reads after this file. This document says how assignment works; it deliberately names no assignee, because it would be wrong within a week. [`README.md`](README.md)'s module registry describes what modules *are*, and deliberately does not repeat who is on them.

> **Rotation makes the repository's documentation load-bearing in a way fixed ownership never did.** Under permanent ownership the context of a module lived in one long-running session. Under rotation the lane arriving at *Timeline slice 2* has none of the context the lane that built slice 1 had, and **the only continuity is what was written down** — the module's design doc, its ADRs, and the Slice Handoff. A design doc that has drifted was previously an inconvenience; it is now the mechanism by which the next assignee is misled.

| Lane | Builds features? | Notes |
|---|---|---|
| **Implementation lanes** | Yes | **Implementing one slice at a time**, claimed from the backlog. Earlier slices may still be with QE — a lane never idles waiting for validation. Branch: `lane-*`, permanent by name |
| **QE — Quality Engineering & Integration** | **No** | **One lifecycle, seven stages, below.** Holds `lane-qe`, **`integration` and `main`** |
| **Lane C — Product Office & Architecture Office** | **No** | **Prepares.** Owns no module, no bounded context and no runtime. Below |

**QE and Lane C are the two permanent assignments**, because their responsibility is the repository rather than any module in it.

### Four responsibilities, and they do not overlap

**Ratified 2026-08-03, product owner.** Lane C was created **instead of** a third implementation lane, on evidence: 23 of 38 open coordination items were the product owner's and 16 `READY` tasks sat unclaimed with two lanes available. **Implementation capacity was not the constraint; decision throughput was**, and a third implementation lane would have added a third consumer of the same queue.

| | | |
|---|---|---|
| **Implementation lanes** | **Build** | Production code inside their assigned modules |
| **QE** | **Certifies** | Quality, certification, release, repository health, environment isolation, the review platforms, reproducibility, regression prevention |
| **Lane C** | **Prepares** | Architectural options · implementation plans · ADR drafts · technical investigations · dependency analysis · migration strategies · decomposition · sequencing · repository consistency reviews · capability audits · roadmap refinement |
| **Product owner** | **Decides** | Priority, product direction, commercial priority, release sequencing, and every ruling |

> **The routing model, and it is the reason Lane C exists.** Implementation used to stop and the product owner started investigating; now the investigation is delegated and implementation almost never stops for research.
>
> ```
>   implementation lane  ─▶  Lane C investigates  ─▶  Lane C prepares
>                                                     alternatives
>                                                          │
>   implementation resumes  ◀──  product owner decides  ◀───┘
> ```

#### Platform Foundation — Lane C's second responsibility

**Ratified 2026-08-04, product owner, resolving [C-010](docs/LANE_COORDINATION.md) / TASK-006.** *"Do not create another engineering lane. Lane C's responsibilities are formally expanded to include Platform Foundation work that belongs to no product bounded context."*

> **The gap it closes.** `infra/`, the `Makefile` and repository process had **no assignable lane**, and four defects landed there — [B-007](docs/BUGS.md), [B-012](docs/BUGS.md), [B-013](docs/BUGS.md), [B-014](docs/BUGS.md). **Environment Framework phases 1 and 2 were written by whoever was nearest**, and phase 3 is larger than both.

| Lane C now builds | Lane C still never builds |
|---|---|
| `infra/**` · the `Makefile` · environment profiles and launchers · doctor and cleanup tooling · the demo lifecycle · `signora_platform/simulation/**` | **Anything in `backend/modules/`** · business logic · a feature a customer buys · `frontend/` product screens |

**QE keeps its gates, and this ruling did not move them** *(clarified 2026-08-04, Lane C, on QE's question — a **Category 1 repository clarification**, deriving one reading from two rules that both already exist)*.

| | Whose |
|---|---|
| **A defect in a gate that stops QE certifying** — `certification-guard.py` · `validate.py` · `smoke.sh` · `state-check.py` · `disaster-recovery.sh` · the compose files | **QE's to fix, unchanged.** *"A gate that cannot run is not a gate"* (§20e, **QE removes its own blockers**), and **§20e already classes fixing a gate as a slice** |
| **New tooling** — the Environment Framework, launchers, profiles, doctor, cleanup, the demo lifecycle, developer tooling | **Lane C's to build** |

> **D-022 filled a gap; it did not take QE's instruments.** `infra/` had **no assignable lane** and four defects landed there — that is what was resolved. **QE's gates were never in that gap: they have always been QE's**, and §20e says so in the sentence that makes fixing one a slice rather than a Closeout.
>
> **The test is not the directory. It is whether the change alters what a gate *means* or merely whether it *runs*.** A repair so QE can certify is QE's; a new capability is Lane C's. **And the symmetry is the point: Lane C may not verify governance it authored, and QE may not be made to wait on Lane C to repair the instrument it certifies with.**

**Every existing constraint still binds, and three matter most:** **`signora_platform/` stays frozen** (§20a) **except `simulation/`** · **§20c-2 is absolute** — a launcher, a profile or a *preview environment* must never become CI by another name · **test data still enters the way a customer's data enters** (§20e). **Lane C is rowed on the execution board for Platform Foundation work, and referenced as before for coordination.**

> **The separation that created Lane C is unchanged — it prepares decisions and the product owner makes them.** Owning tooling does not make it an implementation lane for product work, and **it may not verify governance it authored.** A Platform Foundation slice is validated, certified and promoted by QE exactly like any other.

**Beyond Platform Foundation, Lane C owns no production module and no bounded context.** It does not write production code until explicitly assigned, and **it must never silently become the owner of roadmap priority, commercial priority, release sequencing or product direction** — those are the product owner's, and a lane that prepares a decision is not the lane that takes it.

**Where the line falls in practice**, because the first case arrived within hours of Lane C existing:

| Lane C may | Lane C may not |
|---|---|
| **Decompose an already-approved epic** into implementation-ready `TASK-nnn` rows | **Introduce scope** the product owner has not approved |
| Record which lane a task belongs to, by module ownership | **Reorder** the queue, or change a task's priority |
| Answer a coordination item and thereby unblock work | Decide *whether* the work is worth doing |

> **The test is whether the product owner would recognise the outcome as their own decision, already made.** Decomposition makes an approved decision executable; prioritisation makes a new one. **The first is Lane C's whole purpose; the second is never delegated** — and a row in `BACKLOG.md` must say which it is, as [`TASK-400`](docs/BACKLOG.md) does: *"already approved by the product owner — not new scope."*

**Lane C is the first lane that needs no runtime.** A clone, a branch, the documentation and repository access — **no ports, no database, no Redis index, no MinIO bucket, no compose project.** Its row in [`RUNNING.md`](docs/RUNNING.md#running-a-lane) records the absence rather than an allocation.

**Responsibilities migrating from QE to Lane C**, as Lane C becomes operational: ADR drafting · engineering-policy drafting · roadmap and epic decomposition · implementation planning and specifications · cross-module architecture review · product consistency review · feature sequencing · task preparation · capability analysis · competitive architecture studies · decision preparation. **QE keeps quality, certification, release engineering, repository health, environment isolation, the Human Review and Product Review platforms, reproducibility and regression prevention.**

> **This is a separation, not a reduction.** QE had accumulated architectural and planning work because there was nowhere else for it — which is how the coordination register came to hold items filed under QE that were decisions in disguise.

#### No module changes owner

**Stated as a line rather than left as an absence**, because the absence is what caused the ambiguity that produced this section:

> **No production module changes owner. No bounded context changes owner. No implementation responsibility moves.** Lane A owns exactly what it owned before this section existed; so does Lane B; so does QE. **Descriptions of a lane's strategic direction are direction, never reassignment**, and **any future ownership transfer requires its own explicit decision** — raised as a coordination item, ruled by the product owner, never arriving inside a governance edit (§2, *governance describes reality*).

> **The Integrator was a fourth role and is now QE's responsibility** (2026-08-01, product owner). It was never a separate session; describing it as one meant every merge, certification and status update was owned by nobody in particular. **QE validates, certifies, integrates, promotes, closes out, synchronizes and declares** — one sequence performed by one lane.
>
> **This reversed a separation this document asserted earlier the same day** — *"QE's authority is to withhold approval, not to promote, because a role that both judges the work and ships it can always ship it."* The reversal is deliberate and the reasoning replaces it: **the conflict of interest that argument protected against requires something to rush, and QE has nothing to ship.** QE builds no customer feature, owns no milestone of product scope, and gains nothing from a promotion. What it gains is that **one authority runs the same gates in the same order every time**, which is worth more here than a separation whose only holder had no independent work of its own.
>
> **What still constrains QE is the gate, not another role:** the lifecycle below is not QE's to shorten, and **QE never manually overrides a failing gate.**

### Implementation ownership and integration cadence are independent

**Ratified 2026-08-02, product owner.** A lane is no longer assigned a single slice. It is assigned an **implementation area** — Provider Platform, Timeline, AI Platform, Product Surface, Commercial Profile — and it keeps that area across several related slices, because **engineering context is expensive to rebuild and cheap to keep.**

**That must not slow integration, and these are two different clocks:**

| | |
|---|---|
| **Implementation ownership** | **Coarse and long-running.** A lane holds an implementation area until it is **complete**, becomes **blocked**, or is **explicitly reassigned.** Nothing else ends it — and in particular, **certification does not.** Promoting PP-01 leaves Provider Platform exactly where it was: with Lane A |
| **Integration cadence** | **Fine and continuous.** Every **independently complete** slice flows through the full lifecycle the moment it is testable, whether or not more slices are coming in the same area |

```
  Lane A owns Provider Platform  ──────────────────────────────────────────▶  until complete

     PP-01 ──▶ IN VALIDATION ──▶ certified ──▶ promoted        ownership unchanged
        └────────▶ PP-02 ──▶ IN VALIDATION ──▶ certified ──▶ promoted
                      └────────▶ PP-03 ──▶ …

  implementation and validation run at the same time, deliberately
```

**Neither side waits for the other.** The lane does not wait for certification before starting the next slice (*Continuous execution*). **QE does not wait for the implementation area to finish before validating** — a slice reaching `IN VALIDATION` is validated, certified, promoted and closed out on its own, and *"more is coming in this area"* is never a reason to hold it.

**Why the fine clock is the valuable one:** `main` receives PP-01, PP-02 and PP-03 as three certified increments rather than one large one weeks later, so **a defect is found next to the code that introduced it**, merge complexity stays small because each slice becomes the baseline before the next grows onto it, and the repository's account of itself moves continuously rather than in one jump at the end of a module.

> **Large ownership buys engineering continuity. Small slices buy continuous integration. They are complementary, and the repository is optimised for both at once** — a lane holding one area for weeks, and a repository that has never been more than one slice away from a certified state.

**Repository state is refreshed after every promoted executable slice**, not when the area finishes: `PROJECT_STATUS.md`, [`SESSION_HANDOFF.md`](docs/SESSION_HANDOFF.md), [`ACTIVE_ASSIGNMENTS.md`](docs/ACTIVE_ASSIGNMENTS.md), certification metrics, milestone and roadmap progress, repository health. **The repository always describes the latest promoted state.**

**This changes nothing about certification scope.** Only executable change opens a cycle; documentation, claims, planning and board maintenance still accumulate until an executable slice reaches `IN VALIDATION` (*A cycle is warranted by executable change, not by movement*).

### The QE lifecycle

**QE's responsibility is not repository testing. It is the complete repository lifecycle** (ratified 2026-08-02, product owner). **Seven stages, always in this order:**

> **QE's responsibility resumes only when feature work returns to `integration` for validation.** Between promotions, an `AVAILABLE` lane claims and builds without QE's involvement, and QE is genuinely idle. That is the model working.
>
> **Scheduling is not one of them** (ratified 2026-08-02, product owner). **QE validates, certifies, integrates, promotes, closes out, synchronizes and declares. It does not decide who works on what.** Quality, integration, certification and promotion belong together — each is a judgement about the repository as a whole. **Work allocation is a product decision**, and routing it through QE meant every idle lane waited on the one session that was busy certifying. See *Nobody assigns; lanes pull* below.

| # | Stage | What it is | Deterministic? |
|---|---|---|---|
| **1** | **Validate feature lanes** | Repository-wide functional · API · integration · end-to-end · Security Invariants · coverage · regression · accessibility · performance · exploratory use of the product · product review. QE **creates, maintains, extends and retires** repository-wide automated tests; **lanes own the tests specific to the slices they implement**. **Every slice at `IN VALIDATION` is taken at once — never held because more are expected in the same implementation area** | No — judgement, and findings become `B-nnn` rows |
| **2** | **Execute repository-wide certification** | `make certify` · migration reversibility · `make dr` ([ADR-0032](docs/architecture/adr/0032-release-certification.md)) **against the pinned commit from the Certification Snapshot** | **Yes.** The gates are the decision |
| **3** | **Integrate validated work into `integration`** | Fast-forward only. Reconcile [`BUGS.md`](docs/BUGS.md) and [`LANE_COORDINATION.md`](docs/LANE_COORDINATION.md), verify the Slice Handoff's claims, fold findings into `38`/`39`. **A branch that will not fast-forward is returned to its lane** | Yes — `--ff-only` succeeds or it does not |
| **4** | **Promote the certified commit to `main`** | `git merge --ff-only <certified-sha>` — **never `integration`**, whose head may have moved. **Certification passed, so this happens**: no approval, and no waiting state between stages 2 and 4 | **Yes** |
| **5** | **Execute Repository Closeout** | The eleven mandatory activities below, in order, **every one measured from the promoted repository** | Yes — the checklist is complete or it is not |
| **6** | **Synchronize repository branches** | Fast-forward `integration` and **every idle lane**. **A lane in active development is never touched** | Yes |
| **7** | **Declare Repository Ready** | The next development cycle may begin. **Not before** | Yes |

> **The repository is not ready until all seven have completed successfully. Stopping after certification, or after promotion, is an incomplete repository cycle** — not a finished one with paperwork outstanding. A cycle that ends at stage 4 leaves the repository asserting a state that is no longer true, which is the defect class §2 exists to prevent.

### Certification is attached to a commit, never to a branch

**Ratified 2026-08-02, product owner. This is the repository's central release guarantee:**

> **Every commit on `main` was itself certified, by the repository-wide certification process, before it was promoted.**
>
> Not *"a nearby `integration` state passed"*. Not *"the branch was green around then"*. **That commit, individually.**

**A branch is a moving pointer; a certification is a statement about an immutable tree.** Binding one to the other means the thing certified and the thing shipped are only accidentally the same — and they stop being the same the first time a lane pushes while QE is measuring. That is not a hypothetical: it happened during the cycle that produced this rule, and only luck kept the two identical.

#### The Certification Snapshot

**Every cycle opens by taking one, before any gate runs:**

| Field | What |
|---|---|
| **`integration` commit SHA** | The **full** SHA. This is *the* certified commit, and everything below is measured against it |
| **Certification start time** | When the snapshot was taken |
| **Migration head** | At that commit |
| **Repository metrics** | Measured at that commit, and nowhere else |
| **Active milestone** | What the cycle is closing |
| **Certification identifier** | The record the run writes |

**Every measurement in the cycle derives from that one snapshot. If the snapshot changes, certification restarts** — a cycle cannot be half-measured at one commit and half at another, because the resulting record describes a repository that never existed.

#### `integration` keeps moving, and that is fine

**Feature lanes go on merging while QE certifies. QE never chases the head.**

```
integration   A ─▶ B ─▶ C ─▶ D ─▶ E ─▶ F
                        ▲     └──────────┘
                        │      the next cycle's input
              certification begins at C
                        │
                        ▼
              C passes  ─▶  promote C            ← never D, E or F
```

**QE certifies `C` and promotes `C`.** `D`, `E` and `F` belong to the **next** cycle automatically, by virtue of arriving after the snapshot. **Continuous development never invalidates an in-progress certification**, and an in-progress certification never blocks a lane from merging.

#### The promotion equality rule

```
promoted commit SHA  ==  certified commit SHA
```

**These are identical or the promotion is aborted.** There is no tolerance, no *"but nothing important landed since"*, and no re-reading of a record against a different commit. **Promotion is `git merge --ff-only <certified-sha>` — never `git merge --ff-only integration`**, because the second one promotes whatever the branch happens to point at when the command runs.

**Enforced, not documented:** `python3 infra/certification-guard.py` refuses a promotion whose target is not a certified commit, and `infra/state-check.py` re-checks it at Closeout. **A guard that cannot fail is documentation pretending to be code** (§2).

#### The one bounded exception, and it is checked

**A Closeout commit cannot be certified**, and no amount of discipline changes that: **a certification record cannot contain its own commit hash**, so the commit that *writes* the record is always created after the run it records. Pretending otherwise would make the invariant false in a way nobody could see.

**So the guarantee is stated exactly, and enforced exactly:**

> **No commit reaches `main` except inside a certified snapshot.**
>
> Every commit on `main` is **the certified commit itself**, **an ancestor of one that was promoted**, or **a Closeout commit that provably changes nothing executable.**

**The middle case is not a loophole; it is what a fast-forward does.** Promotion moves `main` to the certified SHA and its ancestors arrive with it — they are intermediate states of the snapshot whose *tip* the gates ran against, and they can never be individually certified because they were never individually a candidate. **What the rule forbids is a commit that is an ancestor of nothing certified**, which is precisely what a lane pushing after the snapshot produces, and precisely what the audit reports.

**Provably, not by assertion.** `infra/certification-guard.py --audit-main` walks every commit on `main` since ratification and checks *paths, not commit messages* — a commit calling itself a Closeout while touching `backend/` is refused. A Closeout commit may touch **documents and certification records only.**

**`infra/` is deliberately not in that set.** `smoke.sh`, `disaster-recovery.sh`, `state-check.py` and the compose files decide whether a gate passes, so changing one changes what certification means. **Fixing a gate is a slice, not a Closeout** — found the hard way, as [B-014](docs/BUGS.md), by running the audit against the two commits QE had just written.

#### Everything downstream uses the promoted commit

**Repository Closeout operates on the promoted commit and never on a newer `integration` head.** `PROJECT_STATUS.md`, [`SESSION_HANDOFF.md`](docs/SESSION_HANDOFF.md), [`ACTIVE_ASSIGNMENTS.md`](docs/ACTIVE_ASSIGNMENTS.md), repository metrics, certification metrics, milestone progress and roadmap progress **all describe that one commit.** A dashboard mixing figures from the promoted commit with figures from a later one describes no repository at all.

#### A cycle is warranted by executable change, not by movement

**Ratified 2026-08-02, product owner.** Certification runs when `integration` carries **meaningful executable change** — production implementation, infrastructure, migrations, executable tooling, governance tooling, architectural behaviour.

**Documentation, claim commits, planning updates and execution-board maintenance accumulate** until they accompany executable work. Certifying them alone spends a full gate run proving a markdown table is still true, **which is how a team learns to skip cycles** — and the habit of skipping is the one thing this model cannot survive.

**`make certified ARGS="--next-cycle"` answers it**, by the same test `--audit-main` applies to a Closeout commit: *does anything here change what the software does?*

> **Observations found during certification do not expand its scope.** Unless one is a **blocking defect**, it is recorded, prioritized in [`BACKLOG.md`](docs/BACKLOG.md), and addressed if it becomes a recurring bottleneck. A cycle certifies the commit it pinned, and nothing else.

#### The next cycle is never ambiguous

**Immediately after Repository Ready, QE compares the latest `integration` SHA with the latest certified SHA.** Differ → **a new certification cycle is available, and its input is exactly the commits in between.** Identical → there is nothing to certify. **There is never a question about which repository state is awaiting certification**, which is the property the whole rule exists to produce.

### QE removes its own blockers

**Ratified 2026-08-02, product owner.** A gate that cannot run is not a gate, and under [ADR-0027](docs/architecture/adr/0027-local-first-development.md) the local run is the *only* run — so a missing local tool is a missing guarantee, not an inconvenience.

**When the repository's documented prerequisites are not installed and installing them is within QE's authority, QE installs and configures them rather than stopping the workflow.** `make`, `build-essential`, Docker, Docker Compose, and anything else [`RUNNING.md`](docs/RUNNING.md) lists as required.

**Escalate only when installation is genuinely blocked** — operating-system permissions, organizational policy, or an unavailable dependency. **"It needed installing" is not a reason to leave a gate unrun**, and a workstation gap must never be recorded as a repository defect ([B-011](docs/BUGS.md) is the worked example of both halves).

**What this does not license:** installing a *new project dependency* (🔴, §6 — that needs an ADR), changing what the repository requires, or working around a failing gate by changing the environment until it passes. **The authority is to make the documented gate runnable, never to make it pass.**

### Nobody assigns; lanes pull

**Ratified 2026-08-02, product owner.** Work allocation was QE's, and it made QE responsible for five things where four belong together.

| | |
|---|---|
| **Quality engineering · integration · certification · promotion** | **One authority, and correctly so.** Each is a judgement about the repository as a whole, and one session running the same gates in the same order beats a separation whose only holder has nothing of its own to ship |
| **Work scheduling** | **Not one of those.** It is a product decision about value, and it has nothing to do with whether a commit is fit to promote |

> **The bottleneck is arithmetic, not authority.** With QE scheduling, an idle lane waits for the one session that is busy certifying — so **every additional lane increases the wait rather than the throughput**, which is the opposite of what lanes exist to do. Three roles, cleanly separated: **the product owner plans, feature lanes execute, QE assures and releases.**

```
  Product Owner          feature lanes              QE
  ─────────────          ─────────────              ──
  owns priority     ──▶  pull from READY      ──▶   validate · certify
  writes BACKLOG.md      claim in                   integrate · promote
                         ACTIVE_ASSIGNMENTS         close out · declare
                         then build                 never schedules
```

**The rules, and they are short:**

- **[`docs/BACKLOG.md`](docs/BACKLOG.md) is the authoritative work queue**, in priority order, and **the queue order *is* the priority.** The product owner owns it. **Every task carries a permanent `TASK-nnn`**, and every other document refers to work by that id rather than by its title.
- **A lane may claim only a `READY` item.** `WAITING` needs somebody to answer; `BLOCKED` needs somebody to build. Neither is claimable, and both are listed so nothing disappears.
- **Claim before implementing, by the Task Claim Protocol below.** The claim is a **standalone commit, pushed to `integration`**, and it is not yours until you have pulled and confirmed nobody beat you to it. **A claim nobody else can see is two lanes about to build the same thing** — which is why it goes to the ref every lane pulls, not to your own.
- **Claim from the top.** If the top item cannot be taken — it needs a module another lane is inside, or a decision nobody has made — **say so in its backlog note and take the next one.** Skipping quietly is re-prioritizing, and priority is not a lane's to hold.
- **A lane never reorders, reprioritizes, removes, or inserts `READY` work without the product owner.** It may claim, it may record why it skipped the first `READY` task, and it may move a task it holds through the lifecycle. A defect goes to [`BUGS.md`](docs/BUGS.md), a dependency to [`LANE_COORDINATION.md`](docs/LANE_COORDINATION.md), and anything else is a conversation with the product owner.
- **QE writes nothing in the backlog and allocates nothing.** At Closeout it reconciles the *board* — removing what has been promoted — and stops there.

**One lane per module still binds**, and it is what makes a claim refusable: if the item you are about to take needs a module somebody else is inside, you cannot take it, and the note saying so is more useful to the product owner than a silent skip.

### Module assignment is authoritative

**Ratified 2026-08-04, product owner**, after [C-213](docs/LANE_COORDINATION.md) became unfixable by any lane: it named an owner that had been correct on 2026-08-03 and had moved by 2026-08-04, so **the lane that could act would not and the lane named could not.**

> **When module assignment changes, responsibility moves with it.** Coordination items, backlog ownership and implementation responsibility **all follow the module. Historical authorship does not.**

**Write *current module assignee*, never *owner*, wherever responsibility is meant to move with the module.** **Reserve *owner* for what genuinely does not move** — the module that owns a table, an event, a bounded context, a piece of vocabulary. §20e already draws that distinction; **C-213 is what it costs when a register ignores it.**

**One implementation module → one implementation lane → one current assignee → one source of truth.** **Dual ownership of an implementation module is not permitted**, and a board showing two lanes on one module is a finding, not a negotiation.

> **Why a stale assignee is worse than a missing one.** A row with no owner is visibly unclaimed and somebody asks. **A row naming a lane that has moved on looks answered** — every lane reads it, believes it, and routes around the work. **C-213 blocked TASK-205 for two days on one word.**

### Distributed Product Development — preparation moves to the implementing lane

**Ratified 2026-08-04, product owner directive. Drafted by Lane C on that instruction.** **The reasoning, the measurements and the transition mechanics are [429](docs/architecture/429-distributed-delivery-model.md); this section is what binds.**

> **The organisation evolves from centralized planning to distributed execution with centralized governance.**
>
> **Preparation moves to the lane that will implement it. Review stays with Product Office. Certification stays with QE.**

**The premise was measured before it was recorded.** **12 of 32 task rows carry Lane C's `TASK-4xx` block** — 37.5% of the queue authored by the one office that may not implement any of it — while `integration` stood still for eleven polls and lanes idled on work that existed only on a Product Office branch. **A queue with one author has one author's throughput, however many lanes consume it.** *The issue is not planning quality; the issue is centralized preparation.*

```
  Approved design ─▶ owning lane prepares ─▶ Lane C reviews ─▶ lane implements ─▶ QE certifies
                                                   │
                                            approve · revise
```

#### The three responsibilities, and they still do not overlap

| | | |
|---|---|---|
| **Product Development lanes** | **Prepare *and* build** | **The complete lifecycle of their assigned modules** — studying the approved UI, workflows, backend capability, repository reuse, proposed API changes, implementation plans, implementation, tests, module documentation, module health, technical debt, **and a continuously `READY` pipeline for what they own** |
| **Lane C — Product Office** | **Governs and reviews** | Architecture · governance · repository health · roadmap · backlog governance · ADR lifecycle · module ownership · dependency management · priority management · release planning · cross-module consistency · Platform Foundation · design conformance · repository conventions · development process · **review of implementation preparation** |
| **QE** | **Certifies** | **Unchanged in every respect** |

> **Lane C no longer prepares every implementation slice. It reviews preparation created by the lanes that own the modules.** **Lane C may approve, reject, request changes, reprioritize, split, merge or defer** — and **may not become another implementation team.**
>
> **A review that rewrites is preparation wearing a review's clothes**, and it restores the bottleneck it was created to remove. **The test before Lane C edits rather than comments: would the package, as submitted, breach a rule the repository can name?** If the answer is *"it is not how I would have done it"*, **the correct output is approval.**

**A Product Development lane may not:** change architecture · redefine module boundaries · modify repository governance · invent a bounded context · ratify an ADR independently · **bypass Product Office review.** **Every one of those was already forbidden**; the list is restated because the lane's new authority makes the boundary worth re-drawing.

#### Three new lifecycle states

**Preparation now happens inside the implementing lane, so it needs states the backlog did not have.**

| State | Set by | Means | Claimable? |
|---|---|---|---|
| **`PREPARING`** | **The owning lane** | Authoring the implementation package | **No** |
| **`UNDER REVIEW`** | **The owning lane**, on submitting | With Product Office. **The lane does not wait** — it prepares the next or implements an already-`READY` slice | **No** |
| **`REVISION REQUESTED`** | **Lane C** | Governance requires a change, **and the reasons are named.** Returns to `PREPARING` | **No** |

**`READY` is now set by Lane C on approval**, where it was the product owner's. **This is narrower than it looks and transfers no priority:** §20e already grants Lane C *"decompositions of already-approved scope — never new scope, never a reordering."* **`READY` states that a package is fit to implement; position in the queue states what it is worth, and that remains the product owner's.**

> ⚠️ **`REVISION REQUESTED` (Lane C, on a plan) and `CHANGES REQUESTED` (QE, on an implementation) are two states and are never collapsed into one.** Different authority, different stage, different subject — and a board using one word for both cannot answer *"is this waiting on Product Office or on QE?"*

#### The READY pipeline is the owning lane's to maintain

**Every Product Development lane continuously maintains roughly five `READY` slices for its own modules.** **Running dry is a finding, and it is Lane C's to investigate** — synchronization delay · governance dependency · ownership ambiguity · an architectural decision · an external dependency · a missing product decision · sequencing · repository health.

> **Maintaining implementation flow is a Product Office responsibility.** **Lane C removes bottlenecks before creating further governance work** — and *"Product Office had other work"* is never the reason a lane was idle.

#### Transition — per module, and event-driven

**This applies to new work only.** Anything **claimed, in progress, with QE or awaiting promotion continues under the existing model until naturally complete.** **A module switches when its current backlog is exhausted**, so no lane changes model mid-slice.

### Ownership is determined by architecture, and recorded in one registry

**Ratified 2026-08-04, product owner**, on [430](docs/architecture/430-module-ownership-transition-plan.md).

> **[`docs/coordination/modules.toml`](docs/coordination/modules.toml) is the authoritative module ownership registry.** Every ownership view — the execution dashboard, the transition plan, the board — **derives from it.** **No document restates an assignee**, and a coordination item, backlog row or defect names its **module**; the assignee is joined at render time.
>
> **This is what C-213 cost and what closes it:** an assignee copied into a row, correct on 2026-08-03 and stale by 2026-08-04, blocking TASK-205 for two days. **A stale assignee is now unrepresentable rather than merely detectable.**

**Ownership is determined in this precedence:** **① product architecture · ② bounded context · ③ long-term maintenance responsibility · ④ repository continuity · ⑤ historical implementation evidence.**

> **Git history is evidence. It is not governance.** Recent commits describe who was *available*, not who should be *responsible* — **and promoting that accident to governance would make ownership a function of scheduling**, which is the exact confusion between *a lane is temporary* and *a module is permanent* that this section exists to prevent.

**Ownership optimises for cohesion, never for arithmetic.** **An uneven split is acceptable when it reflects the product's natural architecture** — continuity, repository knowledge, reuse, implementation quality and long-term maintainability are what it buys, and **capacity is managed through epic sequencing rather than by redistributing modules to even a count.**

#### Do not divide ownership across an interface that has not yet stabilized

**A standing rule, ratified 2026-08-04 after [C-213](docs/LANE_COORDINATION.md).**

> **Two modules with a published-but-unbuilt contract between them belong to one lane.**

**A boundary across a *built* contract is ordinary** — that is what `public/` is for. **A boundary across one that still has to be designed is a coordination item on day one**, because neither lane may invent the other's shape and neither can proceed without it. **C-213 is the worked example**: `commercial_profile` held the export, `sales_engagement` held the only consumer, the contract was published and unbuilt, and **the slice stopped for two days on a change that took minutes once one lane held both.**

**When ownership is genuinely unclear, leave it unassigned and mark it *review at first implementation*.** **Ownership becomes obvious when implementation reaches a module; predicting it earlier buys nothing and can be wrong** — **evidence over prediction.**

### Executable work comes from `integration`, and from nowhere else

**Ratified 2026-08-04, product owner**, after Lane A idled for several reporting cycles waiting on three artifacts that existed only on a Product Office branch.

> **An implementation lane derives executable work from exactly three things: `origin/integration` · a `READY` task row · certified repository state.**
>
> **Product Office branches are planning artifacts, not execution contracts.** **A lane does not monitor one, does not wait on one, and does not treat work found on one as claimable.**

**Why the rule is worth stating rather than assuming.** Lane A behaved correctly throughout — it polled, it reported, it did not invent work. **But its unblock conditions named a Lane C branch**, so it waited on a ref the Task Claim Protocol never consults, and **no gate could see that it was waiting on nothing claimable.**

**The corollary, and it is Lane C's:** **prepared work that has not reached `integration` does not exist for planning purposes.** It is not buffer, it is not capacity, and reporting it as either overstates what any lane can do (`CLAUDE.md` §20e, the five states).

#### Synchronization becomes the highest repository priority

> **Whenever an implementation lane has been idle for more than one reporting cycle because `READY` work exists only outside `integration`, synchronizing that work becomes the highest repository priority** — above further preparation, above new initiatives, above every planning activity.

**It outranks the Product Office's own queue**, because a lane idling on work that has already been written is the most expensive state the repository can be in: **the cost is paid twice — once in the idle lane, and once in the preparation that ages while it waits.**

**Lane C reports this condition itself and does not wait to be told.** It was reported by Lane A on 2026-08-04, not by the office that caused it.

### The Task Claim Protocol

**Ratified 2026-08-02, product owner. Mandatory before any production code is written.**

**Pulling created a race the pushing model did not have.** Two `AVAILABLE` lanes read the same queue at the same moment, both see `TASK-002` at the top, and both start building. Nothing about that is caught by care: each lane behaved correctly in isolation. **The repository must prevent duplicate implementation through process, not convention.**

**The claim is made atomic by the one mechanism that is already atomic here — a push to a shared remote.** A claim is not an intention; it is a commit that either lands before somebody else's or does not.

| # | Step | What |
|---|---|---|
| 1 | **Synchronize** | `git fetch origin && git checkout integration && git pull --ff-only` |
| 2 | **Rebase** | `git checkout <lane-branch> && git rebase integration`. Resolve your own conflicts |
| 3 | **Read your queue first** | **[`docs/coordination/queues/lane-<a\|b>.toml`](docs/coordination/queues/)** — `current`, then `next`, then `future`, **in that order.** It is written by Lane C, holds **every task you are eligible to start**, and its `blocked` array names the rest with each blocker's owner. **Ids only; execution state is still the backlog's** |
| 3b | **Then read [`BACKLOG.md`](docs/BACKLOG.md)** | The whole `READY` section, in order. **The queue tells you which rows are yours; the row tells you what the work is.** If the two disagree, **the backlog wins on state and the queue wins on ownership** — and **report the disagreement**, because one of them is stale |
| 4 | **Select** | The **highest** entry in your queue that is **not already claimed.** If your queue is empty or absent, fall back to the backlog: the highest `READY` task in a module [`modules.toml`](docs/coordination/modules.toml) assigns to you, with **no active assignee**, **no unmet dependency**, and **not already claimed** |
| 5 | **Record the claim** | Update **only your own row** in [`ACTIVE_ASSIGNMENTS.md`](docs/ACTIVE_ASSIGNMENTS.md), naming the `TASK-nnn`, and mark the task `CLAIMED` in the backlog |
| 6 | **Commit it alone** | **A standalone commit containing nothing but the claim.** `Claim TASK-002 — <title>` |
| 7 | **Push the claim to `integration`** | `git checkout integration && git merge --ff-only <lane-branch> && git push origin integration`, then push your lane branch. **This is the moment the claim exists** — and it must exist *where every other lane will look* |
| 8 | **Pull and rebase again** | `git pull --rebase origin integration`, and look at what came back |
| 9 | **If somebody else claimed it first** | **Abandon your claim** — drop the commit, return to step 3, take the next eligible task. **Do not negotiate, do not split the task, do not proceed in parallel** |
| 10 | **Only now, implement — and immediately** | A successful claim is recorded *and* synchronized. **Not before, and no pause after**: the task moves to `IN PROGRESS` as work starts |

> **No production code may be written before a successful claim has been recorded and synchronized.** Not a line, not a scaffold, not *"just the types while I decide"*. **The claim is what makes the work yours**, and code written before it is code that may have to be thrown away — which is precisely the waste the protocol exists to prevent.

**Why a standalone commit.** A claim mixed into an implementation commit cannot land before the implementation, so it cannot arbitrate anything — it announces a decision already acted on. **Alone, it is cheap to abandon**: `git reset --hard origin/integration` costs nothing when nothing was built on it.

**Why step 8 is not optional.** A push proves your claim was written; it does not prove it was *first*. Step 8 is where you learn, and step 9 is what you do about it. **A lane that pushes and starts building has not run this protocol** — it has recorded a claim and assumed it won.

> **Why the claim goes to `integration` and not only to the lane branch** (corrected 2026-08-02, after watching it fail). **`integration` is the one ref every lane pulls** — it is step 1 of Startup. A claim pushed only to `lane-a-product-surface` is invisible to every other lane, so the queue still reads as unclaimed and **the race the protocol exists to prevent is still open.** Observed live: two lanes ran the protocol exactly as written, one claim reached `integration` and the other did not, and the second task sat there looking free while somebody was building it.
>
> **This is the one thing a feature lane may push to `integration`**, and it is bounded so tightly that a machine checks it: **a claim commit touches [`ACTIVE_ASSIGNMENTS.md`](docs/ACTIVE_ASSIGNMENTS.md) and [`BACKLOG.md`](docs/BACKLOG.md) and nothing else.** A commit calling itself a claim while carrying code is refused by `infra/certification-guard.py --audit-claims`. Everything else still arrives on `integration` the same way it always has: QE fast-forwards a validated lane branch.

**Losing a race costs one commit and no code.** That is the entire point of the ordering, and it is why the protocol reads as more ceremony than it costs.

### Governance is stable; it evolves reactively

**Ratified 2026-08-02, product owner, and it binds this file as much as any other.**

**The model is now sufficient for scaling**: certification, promotion, task claiming, repository state and validation are all deterministic. **What the repository is short of is product, not process.**

> **The order of work is: build product functionality · observe real execution · improve governance only when execution reveals an actual bottleneck.**

**Change governance only when one of these is true:**

| | |
|---|---|
| **A real defect exposed a weakness** | Something broke, or a check failed to catch something it should have |
| **Multiple lanes hit the same friction** | One lane's inconvenience is not evidence; two lanes' is |
| **Determinism is threatened** | A result could differ between two runs, or between two readers |
| **Automation can replace manual judgement** | A rule kept by discipline can be kept by a machine instead |

**Do not redesign a stable process without evidence, and do not add a refinement because one is possible.** Every rule here costs a cold session reading time and a lane compliance effort, and the repository is now past the point where more process buys more safety.

**Treat governance as infrastructure and implementation as the primary driver of value.** The repository's success is measured by engineering throughput, feature completion, repository quality and certification reliability — **never by the number of governance refinements introduced.**

#### The governance freeze — ratified 2026-08-05, product owner

> **Product delivery takes priority over governance refinement.** **When we discover a governance weakness during execution, we improve it. We do not pause product development searching for theoretical perfection.**

**Prohibited unless a significant issue is discovered *during implementation*:** **large governance redesigns · workflow redesigns · execution-model redesigns · organizational restructuring.**

**Permitted, always:** **small corrections · bug fixes · clarifications · incremental improvements.**

> **The test is the same one this section already applies, tightened by one word: a governance change now needs an *observed* execution problem, not a foreseeable one.** **Every lane spends the overwhelming majority of its time implementing product functionality rather than refining process** — and **the governance exists to support engineering, never to become engineering.**

**Lane C's standing responsibilities under the freeze**: **backlog health · queue health · execution flow · bottleneck identification · implementation-package review · dependency coordination · keeping every implementation lane continuously supplied with work · protecting repository architecture.** **Evolving the delivery model is not among them**, and **[434](docs/architecture/434-execution-queue-governance-package.md) is the last such initiative until execution produces evidence for another.**
### Execution ownership ends at `IN VALIDATION`

**Ratified 2026-08-02, product owner.** Two refinements on one day, and they are one idea: **every lifecycle state has exactly one owner, and a lane's ownership stops the moment the work becomes something QE can take.**

| State | Set by | Means |
|---|---|---|
| **`PREPARING`** | **The owning lane** | Authoring the implementation package. **Not claimable** |
| **`UNDER REVIEW`** | **The owning lane** | With Product Office. **Not claimable** |
| **`REVISION REQUESTED`** | **Lane C** | Governance requires a change, and the reasons are named. **Returns to `PREPARING`** |
| `READY` | **Lane C**, on approving *(was: product owner — see *Distributed Product Development*)* | Claimable. **Fitness, not priority** — the queue's order remains the product owner's |
| `CLAIMED` | **The lane**, by the Task Claim Protocol | It is yours. **Implementation begins immediately** |
| `IN PROGRESS` | **The lane**, as work starts | Being built. **A claim flows straight into this** — there is no pause between them unless another rule explicitly requires one |
| `IN VALIDATION` | **The lane**, the moment it pushes | Implementation, tests, module documentation and Slice Handoff are all complete. **The lane's responsibility for this task has ended** |
| `CHANGES REQUESTED` | **QE**, during validation | Something did not hold. Returned to the implementing lane, with the corrections named |
| `VERIFIED` · `CERTIFIED` · `PROMOTED` · `DONE` | **QE, exclusively** | Validation passed · `make certify` passed · `main` fast-forwarded · closed out. **A feature lane never writes one of these** |

**QE does not update the execution status of work it did not write, and a lane does not update the repository's judgement of it.** The previous arrangement had QE setting a lane's execution state, which is bookkeeping rather than judgement — and **a state nobody is clearly responsible for is the one that goes stale.**

#### Continuous execution — a lane never idles waiting for QE

> **The moment a lane sets `IN VALIDATION`, it returns to [`BACKLOG.md`](docs/BACKLOG.md) and claims the next `READY` task.** It does not wait for validation, certification, promotion, Closeout, or Repository Ready.

**Waiting serializes exactly the parallelism lanes exist to create.** A lane blocked on certification is idle engineering capacity, and the cost grows with every lane added — which is the same arithmetic that moved scheduling out of QE earlier the same day. **Repository quality is preserved by the gates, not by making people wait for them.**

**Only four things stop a lane claiming again:**

1. **No `READY` task exists.**
2. **A higher-priority task has been explicitly assigned** by the product owner.
3. **An architectural dependency blocks implementation** — a [`C-`](docs/LANE_COORDINATION.md) item whose answer the work would have to assume.
4. **QE has returned one of this lane's tasks as `CHANGES REQUESTED`** and it must be addressed first.

**Anything else is a lane idling with work available, which is a finding.**

#### Two kinds of blocker, and they behave differently

**Ratified 2026-08-02, product owner.** Both stop a slice; **only one stops thinking.**

| | **Implementation blocker** | **Architectural blocker** |
|---|---|---|
| **Why** | The architecture exists and something is temporarily unavailable | **No accepted architecture exists for the next step** |
| **Looks like** | Waiting on another module, another slice, QE, or infrastructure already designed | Runtime composition · platform contracts · shared infrastructure · repository-wide runtime · the execution model |
| **What happens** | **Resumes automatically** the moment the dependency is satisfied | **Implementation stops. Architecture discussion begins**, and implementation resumes only once a direction is accepted |
| **Who moves it** | Whoever holds the dependency | The product owner |

**The test is not how big the change is — it is whether anybody has decided.** A dependency on work that is agreed and unbuilt is an implementation blocker however large; a dependency on a decision nobody has made is architectural however small the code would be.

> **A lane recognises which it has hit and does not convert one into the other.** *"I could just add it"* is how an architectural blocker becomes a silent design decision inside a feature slice — and the change that follows is always small, which is exactly why nobody notices it was a decision.

**When raising an architectural blocker, the item carries six things**, because a blocker reported without them costs a second round-trip before anybody can rule on it:

**the problem · the affected modules · the alternatives · a recommendation · the trade-offs · the implementation impact.**

**A lane's recommendation is architectural input and never implementation authority.** Proposing a direction is expected; proceeding on it is not.

**The loop, and it has no branch a lane may add to:**

```
  implement  ─▶  IN VALIDATION  ─▶  rescan BACKLOG.md  ─┬─▶  READY exists  ─▶  claim  ─▶  implement
                                                        └─▶  none          ─▶  AVAILABLE, and wait
```

**A lane never invents work · never reprioritizes · never reopens completed work · never waits for permission while `READY` work exists.** And the symmetric rule, which matters just as much: **a lane never begins work when no `READY` task exists.** Both halves protect the same thing — **the product owner owns priority**, and a lane that manufactures its own next task has taken it, however useful the task looked.

**`AVAILABLE` with an empty queue is a correct repository state, not a stalled one** (ratified 2026-08-02, product owner). The remaining work is being implemented, awaiting QE, blocked, or awaiting a decision — and **each of those has an owner who is not this lane.** Saying so and stopping is the honest report; finding something to do is not.

> ⚠️ **But "my queue is empty" is now a claim with a file behind it** (2026-08-05, [D-070](docs/DECISION_REGISTER.md)). **Read `docs/coordination/queues/lane-<a|b>.toml` before reporting it.** On 2026-08-05 both lanes reported empty queues **while both queue files named a current task**, and Lane B's report at [C-329](docs/LANE_COORDINATION.md) reasoned about five coordination items without mentioning `TASK-408` — which was sitting in its own queue as `current`.
>
> **The lanes were not wrong to look where they looked.** The procedure pointed at the backlog, the backlog rows name **modules**, and ownership had to be joined from the registry to see them. **Derivable is not visible**, and the office that made it derivable owns that. **Step 3 above is the fix**; this note is why it is there.

#### What continuous execution means for the branch

**A lane branch may carry more than one slice — but only when every earlier one is `IN VALIDATION`.** The rule it refines is unchanged in intent: *one slice being written at a time*. Two slices simultaneously **under construction** on one branch is still a finding, because neither can be validated without the other.

**Rebase, gate and push each slice as it completes**, exactly as before. QE takes the branch as it stands; stacked slices are validated together, and a `CHANGES REQUESTED` on the earlier one is fixed in place rather than by unwinding the later.

#### `CHANGES REQUESTED` — the feedback path

**QE names the corrections; the implementing lane makes them.** *"QE reports bugs, feature lanes fix them"* is unchanged — this is that rule with a state attached, so a returned slice cannot be mistaken for one nobody looked at.

**The lane pauses its current work only if it must.** It addresses what was asked, re-runs its gates, pushes, and returns the task to `IN VALIDATION`. **A returned slice is a normal engineering loop, not a stop.**

### The Change Budget

Every slice knows what it may touch before it starts.

| Tier | Contains | Authority |
|---|---|---|
| 🟢 **Green** | **Your assigned module's** `domain`/`application`/`infrastructure`/`interface` · its tests · its design doc · the frontend components and routes that serve your slice · a bug fix inside it | Lane, freely |
| 🟠 **Amber** | Your assigned module's `public/` · a new table (**with its `tenancy_policy.py` registration**) · a new event (**with its `06-events.md` entry**) · a new endpoint · a new component in `components/ui` · a migration | Lane — **announce it in the commit message** |
| 🔴 **Red** | `signora_platform/**` · the frontend foundation (`components/ui`, `lib/query`, `lib/state`, shell) · a new module or bounded context · a new cross-module dependency · a new dependency · `docs/architecture/01`–`21` · `adr/` · any frozen decision · the roadmap | **Product owner + ADR** |
| ⚫ **Black** | Rename an API · move architecture · rewrite documentation · **refactor a module you are not assigned** · weaken or delete a Security Invariant · rewrite a dated record · create CI/CD (§20c-2) | Never |

**Touching a file outside your budget is a finding to raise, not a change to make.** The same discipline as §20a, applied to the whole repository.

### Shared files have one owner

Together these appear in roughly two thirds of all commits. **A lane does not edit them.**

**One responsibility each. If information already has an authoritative home, reference it — never copy it.**

| File | Its one responsibility | Who writes it |
|---|---|---|
| `CLAUDE.md` | **Repository governance** | Product owner |
| [`docs/RUNNING.md`](docs/RUNNING.md) | **Development environments** — ports, databases, Redis indices, variables | **QE** |
| [`docs/BUGS.md`](docs/BUGS.md) | **The defect register** | **Any lane opens. The module's current assignee fixes. Only QE sets `VERIFIED`** |
| [`docs/LANE_COORDINATION.md`](docs/LANE_COORDINATION.md) | **Cross-lane coordination** — dependencies and pending contracts, nothing else | **Any lane opens. The named owner answers. The requesting lane closes.** **Lane C moves an item through `IN ANALYSIS` → `READY FOR PRODUCT DECISION`** |
| [`docs/QUALITY_ENGINEERING.md`](docs/QUALITY_ENGINEERING.md) | **QE's operating procedure** — how the lane validates, reviews and reports | **QE** |
| [`docs/REPOSITORY_RELEASE_CHECKLIST.md`](docs/REPOSITORY_RELEASE_CHECKLIST.md) | **The lifecycle runbook** — every command and tick-box from validation to Repository Ready | **QE** |
| `PROJECT_STATUS.md` | **The executive dashboard** — *"where are we?"*, measured | **QE**, at Closeout |
| [`docs/SESSION_HANDOFF.md`](docs/SESSION_HANDOFF.md) | **Operational context** — *"what should the next session know?"* | **QE**, at Closeout |
| [`docs/BACKLOG.md`](docs/BACKLOG.md) | **The READY queue** — *"what is available, and in what order?"* | **Product owner owns scope and order** — unchanged, and the order *is* the priority. **A Product Development lane writes preparation rows for its own modules** — `PREPARING` → `UNDER REVIEW` — **and its claims** *(from 2026-08-04, Distributed Product Development)*. **Lane C sets `READY` on approval and `REVISION REQUESTED` on rejection**, and still writes decompositions of already-approved scope — **never new scope, never a reordering.** QE writes nothing |
| [`docs/ACTIVE_ASSIGNMENTS.md`](docs/ACTIVE_ASSIGNMENTS.md) | **The execution board, and nothing else** — who is working · on which `TASK-nnn` · on which branch · at what execution status. **It does not define priority** | **The claiming lane**, at once. **QE** reconciles it at Closeout |
| [`docs/DOMAIN_DISCOVERY_REGISTER.md`](docs/DOMAIN_DISCOVERY_REGISTER.md) | **The screen → domain map and the architectural radar** — *"which domain capabilities and platform services does each approved screen require, and where is each of those?"*. **It indexes assessments; it never restates one, and a row is never a task** | **Lane C**, continuously *(2026-08-05, [D-076](docs/DECISION_REGISTER.md))* |
| `docs/architecture/38` · `39` | Design decisions · review findings | **QE**, at merge |
| The roadmaps | *Scope* is the product owner's · *progress* is QE's | Both, as marked |
| `PRODUCT_DIFFERENTIATORS.md` | Product strategy | Product owner |
| `docs/architecture/adr/**` *(drafts)* | **ADR preparation** — a draft is a recommendation, never a ratification | **Lane C** drafts; the product owner ratifies |
| `apps/api/main.py` · `pyproject.toml` contracts · `tenancy_policy.py` · `policy.csv` · `lib/api/types.ts` · `lib/query/keys.ts` | Registries every lane extends | Any lane — **append-only, one line, alphabetical where a list exists** |

**Two registers are deliberately writable by every lane** — `BUGS.md` and `LANE_COORDINATION.md` — because a defect nobody may record and a dependency nobody may raise are the two failures that cost most. Both are **append-only with allocated ids**, so a conflict is two lanes claiming one number and QE renumbers the later at merge.

**A lane reports its findings in its commit message and its own module's design doc.** QE folds them into the shared records at merge. That reduces narrative-document conflicts to zero rather than managing them — **which only works if the commit message actually carries them**, hence the Slice Handoff below.

### Branches and promotion — the canonical workflow

> **This section is the single authoritative statement of how work moves through the repository.** [`README.md`](README.md) and [`docs/QUALITY_ENGINEERING.md`](docs/QUALITY_ENGINEERING.md) point here and must not restate it. Where any other document disagrees with this one, this one is right and the other is a defect.

```
  the lane                              QE — one lifecycle, seven stages, in order
  ────────                              ──────────────────────────────────────────

  feature      ─▶  lane      ─▶  1 validate  ─▶  2 certify  ─▶  3 integrate  ─▶  4 promote
  development      validation     the lanes       the tree       into              to main
                                                                 integration          │
                                                                                      ▼
        7 Repository Ready  ◀──  6 synchronize branches  ◀──  5 Repository Closeout
```

**Nine stages, two of them the lane's and seven QE's, and a development cycle is complete only when every one has finished — not at promotion.** Stage 5 is **Repository Closeout**, and it is not administration: future development reads the repository's account of itself, and a dashboard describing an earlier state is a defect of the same class as a workflow that looks live (§2).

**That is the normal engineering process, end to end.** It does not stop at certification, it does not stop at promotion, and **there is no manual step inside it.** **Human product review happens on `main`, after stage 7 — it reviews what has shipped and never gates the shipping**, because a gate a person holds is not a deterministic gate.

**Two roles, and one direction.** Feature lanes create value; **QE is the only lane that may merge, certify, promote, or write what the repository says about itself.** No feature lane pushes to `main`. No feature lane bypasses QE.

> **Promotion is deterministic, and it is not an approval.**
>
> **Every required gate passes → the certified commit is promoted to `main`.** No further sign-off is sought, none is required, and **no separate approval workflow may be introduced.** The gates *are* the decision — the same principle as *"a green local run is the decision, not a preview of one"* (§20c-2).
>
> **Any required gate fails → promotion does not occur.** There is no partial promotion and no expedited path.
>
> **There is never an intermediate manual decision between successful certification and promotion.** A pause for judgement there would mean the gates did not decide, which makes every prior claim about determinism false. What QE cannot do is promote with a gate unrun, override a failing one, or shorten the sequence because a slice looks small. **The authority is to run the gates faithfully and act on the result**, not to judge whether the result matters.

| Branch | Lifetime | Who moves it |
|---|---|---|
| `main` | Permanent. **Every commit on it was individually certified** | **QE only**, fast-forwarded to a **certified SHA** |
| `integration` | Permanent. Where lanes meet. **It keeps moving during certification, deliberately** | **QE**, for all work. **A lane may fast-forward it with a claim-only commit** — that is the arbitration point, and it is the only exception |
| `lane-*` | **Permanent name.** One slice under construction, plus any earlier slices still `IN VALIDATION`. Reset to `integration` once QE has promoted them | Its own session only |

> **The lane still rebases and still resolves its own conflicts; QE performs the fast-forward.** This is the reading that satisfies both rules at once, and it is not a compromise: **a fast-forward after a clean rebase has no conflicts by construction**, so QE never adjudicates code it did not write, and every arrival on `integration` still passes through one authority. A lane that hands QE a branch which will not fast-forward has not finished step 4.

**Rules, and they are short:**

- **A slice lives two days maximum.** A branch may carry more than one **only when the earlier ones are `IN VALIDATION`** — waiting for QE is not a reason to stop working (*Continuous execution*). **Two slices under construction at once is still a finding.**
- **Rebase, never merge, onto `integration`.** Rebase freely: nobody else has your lane branch.
- **Fast-forward only, everywhere.** No merge commits. `main` advances only to a **certified commit on `integration`'s history**, so `main` is always an ancestor of it and the fast-forward always succeeds. Three reasons this is not taste: Alembic's chain is linear, the records are append-only narratives, and a linear history is the only one where *what was true when* is readable.
- **The gates are the review.** Full local gates on the rebased branch before QE fast-forwards it.
- **Conflicts are resolved by the lane that is rebasing**, never by QE — the lane knows what its change meant. A conflict in a 🔴 file means the lane was outside its budget; stop and raise it.
- **Commit messages keep the existing form:** `M12.5 — <what changed, in product language>`. Not Conventional Commits — `git log --oneline` is a changelog a cold session reads. **The last commit of a slice also carries a Slice Handoff** (below).
- **QE never develops a customer feature while integrating.** Validate · certify · integrate · promote · close out · synchronize · declare — in that order, and nothing else in between.

**Every lane's ports, database and Redis index are allocated by the permanent convention in [`docs/RUNNING.md` § Running a lane](docs/RUNNING.md#running-a-lane). No lane invents ports and no lane shares a database.** That table is the one place allocations are recorded; adding a lane means claiming its row there, not choosing numbers.

### A lane's day — startup, slice, completion

Three sequences. **Every step names who does it.**

#### 1 · Startup — before any implementation, every time

**Mandatory. A lane that skips it is building on a base QE has already reported defects against.**

| # | Step | What |
|---|---|---|
| 1 | **Pull `integration`** | `git checkout integration && git pull origin integration`. **No implementation begins from a stale `integration`** |
| 2 | **Rebase the lane branch** | `git checkout <lane-branch> && git rebase integration`. Resolve your own conflicts |
| 3 | **Read [`docs/BUGS.md`](docs/BUGS.md)** | Every `OPEN` and `FIXING` row, not only those assigned to you — a defect in a module you depend on may be about to block you |
| 4 | **Take the rows assigned to your lane** | If one belongs naturally to today's work, **fix it first, with a regression test**. If it is deferred, **record the reason in the commit message**. Never silently ignore an assigned bug |
| 5 | **Read [`docs/LANE_COORDINATION.md`](docs/LANE_COORDINATION.md)** | **Every open item, not only your own.** Another lane's pending contract change is something to discover now, not at merge |
| 6 | **Read [`docs/RUNNING.md`](docs/RUNNING.md#running-a-lane)** | Use **only** your assigned ports, PostgreSQL database, Redis index and environment variables. **Never invent a local convention** — that table is authoritative |
| 7 | **Claim your slice** | If you are carrying one, confirm it. If you are `AVAILABLE`, **run the Task Claim Protocol above — all ten steps, and no production code until step 10.** Then confirm: the `TASK-nnn` · milestone · slice · **the module and its architectural boundaries** · what it depends on · which coordination items touch it |
| 8 | **Read your own uncommitted history** | `git log integration..HEAD` — what is already on this branch that you have forgotten, or that a previous session left |
| 9 | **Only then begin the slice** | |

> **Assigned defects are the front of the backlog, not the back.** QE validates every merge, so a lane that starts new work while carrying open rows accumulates them faster than it retires them — and the rows that survive longest are always the ones a customer would hit. Rows are retired the way *Bugs* below requires.
>
> **Silence reads as *nobody looked*.** A deferral with a stated reason is a decision; an unmentioned row is an omission.

#### 2 · The slice

| # | Step | What |
|---|---|---|
| 1 | **Declare the Change Budget** | 🟢 freely · 🟠 announce in the commit message · 🔴 stop and raise · ⚫ never |
| 2 | **Implement, with tests** | The golden path *and* the realistic failure modes (§11) |
| 3 | **Run the impacted gates only** | Your module suite · `mypy` · `tsc` · `eslint`. Speed is the point during a slice |

**When the work turns out to depend on another module, never continue on an assumption — do not guess, do not infer, do not implement one.** Open or update an item in [`docs/LANE_COORDINATION.md`](docs/LANE_COORDINATION.md), name that module's current assignee in the implementation report, and **wait for agreement whenever the dependency touches architecture or a public contract** — an API, an event payload, a read or write port, a schema, a module boundary.

> **Architecture is agreed explicitly or it is inferred, and inferred architecture is two lanes shipping incompatible halves of one contract.** A lane may proceed past an open item only where proceeding encodes no assumption about the answer.

#### 3 · Completion

| # | Step | Who | What |
|---|---|---|---|
| 1 | **Complete the slice** | Lane | **Implementation, tests and the module's documentation, consistent** — a slice with two of the three is unfinished (§12) |
| 2 | **Run the impacted tests** | Lane | Its module suite, impacted integration tests, `mypy --strict`, `lint-imports`, frontend suite, production build |
| 3 | **Rebase onto `integration`** | Lane | `git pull --rebase origin integration`. **The lane resolves its own conflicts** |
| 4 | **Re-run the gates on the rebased branch** | Lane | Rebasing changes the program. The gates that passed before it were never run on what is about to merge |
| 5 | **Write the Slice Handoff** | Lane | In the final commit message. **See below — this is what QE writes the project status from** |
| 6 | **Push the lane branch and tell QE** | Lane | `git push origin <lane-branch>`. **Backup, not a trigger** — a push stores the repository and starts nothing (§20c-2). QE does not poll |
| 6a | **Set `IN VALIDATION`** | Lane | In [`BACKLOG.md`](docs/BACKLOG.md) and its own board row. **The lane's responsibility for this task ends here** |
| 6b | **Claim the next `READY` task** | Lane | Immediately, by the Task Claim Protocol. **Do not wait for anything below this line** — only the four conditions in *Continuous execution* stop a lane claiming again |
| 7 | **Validate** — *lifecycle 1* | **QE** | Repository-wide backend suite · frontend suite · Security Invariants · coverage gate · `make smoke` · **exploratory use of the product** · product review, run on the lane's rebased branch. Defects become `B-nnn` rows. **Passing sets `VERIFIED`; failing sets `CHANGES REQUESTED` and returns the task to the implementing lane with the corrections named** |
| 8 | **Certify** — *lifecycle 2* | **QE** | `make certify`, migration reversibility, `make dr` ([ADR-0032](docs/architecture/adr/0032-release-certification.md)), **all against the pinned SHA**. **The commit certified here is the commit promoted at step 10** — identical, or the promotion aborts |
| 9 | **Integrate** — *lifecycle 3* | **QE** | `--ff-only` into `integration`. A branch that will not fast-forward goes back to the lane at step 3. Reconcile the registers; verify the Slice Handoff's claims |
| 10 | **Promote** — *lifecycle 4* | **QE** | `git merge --ff-only <certified-sha>` into `main`, after `infra/certification-guard.py` confirms that SHA is certified. **Certification passed, so this happens** — no approval, no pause, no waiting state |
| 11 | **Repository Closeout** — *lifecycle 5* | **QE** | **Mandatory, never optional.** The eleven activities in *Repository Closeout* below, in order, **every figure measured from the promoted commit** — never from a lane's report and never from a newer `integration` head. Includes the release summary |
| 12 | **Synchronize the branches** — *lifecycle 6* | **QE** | Fast-forward `integration` to `main` if it lags · fast-forward **every idle lane branch** · **leave lanes in active development alone** — they rebase at the start of their next slice. Verify every branch shares the promoted baseline |
| 13 | **Reconcile the board** | **QE** | Mark promoted claims `COMPLETE`, then **remove them** — no lane stays recorded against work that has reached `main` — and return those lanes to `AVAILABLE`. **QE does not allocate what they do next**: they claim from [`BACKLOG.md`](docs/BACKLOG.md) |
| 14 | **Declare Repository Ready** — *lifecycle 7* | **QE** | Only once [`REPOSITORY_RELEASE_CHECKLIST.md`](docs/REPOSITORY_RELEASE_CHECKLIST.md) is complete. The next development cycle may begin. **Not before** |
| 15 | **Human product review** | Product owner | On `main`, in the demo environment (3000/8000). **No frontend screen is complete until a human has reviewed it there** (§2). **After Repository Ready, never gating it** |
| 16 | **Release** | — | Deferred to M14.5. There is no release today ([ADR-0027](docs/architecture/adr/0027-local-first-development.md)) |

**`integration` never fast-forwards to `main` with an open 🔴 bug.** That is the one blocking rule; 🟠 and below are the product owner's call.

**A lane resets its branch to `integration` once QE confirms the promotion.** That is *housekeeping*, not a gate: **the next slice began at step 6b**, and by the time promotion lands the lane is usually several commits into it. A lane whose branch still holds unpromoted work simply rebases at its next slice boundary, exactly as it always has.

### Repository state, and the assignment board

> **Feature lanes do not maintain repository-wide state.** A lane maintains **its module's documentation, its Slice Handoff, and its rows in [`BUGS.md`](docs/BUGS.md), [`LANE_COORDINATION.md`](docs/LANE_COORDINATION.md) and [`ACTIVE_ASSIGNMENTS.md`](docs/ACTIVE_ASSIGNMENTS.md)**. **Everything describing the repository as a whole is QE's, exclusively** — `PROJECT_STATUS.md`, `SESSION_HANDOFF.md`, repository health, certification status, roadmap and milestone progress, completed slices, repository statistics, overall completion.
>
> **The reason is not authority; it is arithmetic.** A lane can only report what it did. Repository-wide state is a property of everything merged together, which only the session that ran the gates on `main` has ever seen. **A dashboard assembled from lane reports is a sum of intentions.**

**QE writes these, immediately after promoting, measured from `main`.**

| Record | The one question it answers | What it must contain |
|---|---|---|
| `PROJECT_STATUS.md` | **"Where are we?"** — the **executive dashboard**, not an engineering journal | Repository state · current milestone · overall completion · milestone progress · repository health · certification status · current blockers · active work · recently completed work · recommended next work. **Concise, and always representing `main`.** Historical implementation detail belongs to the architecture records and `git log`, not here |
| [`docs/SESSION_HANDOFF.md`](docs/SESSION_HANDOFF.md) | **"What should the next session know?"** — operational context | Current repository state · current certification state · active lanes · open blockers · pending work · repository recommendations. **It must not duplicate the dashboard**; where a figure is the dashboard's, it references rather than restates |
| [`docs/ACTIVE_ASSIGNMENTS.md`](docs/ACTIVE_ASSIGNMENTS.md) | **"Who is doing what, right now?"** — the **execution board** | Which lane · which module · which milestone · which slice · status · blockers · dependencies · **expected next action**. Completed assignments marked `COMPLETE`, **then removed**, and the lane returned to `AVAILABLE`. **No lane may remain assigned to work that has reached `main`, and no stale assignment is left behind** |

**Every figure in all three is read from the promoted commit** — the test count from a run, coverage from the gate, `HEAD` from git. **Never copied from a lane's report.**

> **Three documents, three questions, no overlap.** If the same sentence would be true in two of them, it belongs in one and is referenced from the other (§2, *truth has exactly one authoritative representation*). This is the one-responsibility rule applied to the records that describe the repository itself, and it is the rule most easily lost — because restating a figure is always easier than linking to it.

**A lane's Slice Handoff is input to these records; it is never the record.** A lane offers a claim, QE publishes a measurement, and where they differ the measurement is what ships.

> **This is the whole reason the roles merged.** The lane that ran the gates is the only one that saw the numbers, and a status document written by anybody else is a transcription of somebody's intent.

**`ACTIVE_ASSIGNMENTS.md` is the single authoritative record of execution state.** [`README.md`](README.md)'s module registry deliberately does not repeat it: a module is permanent and an assignment is weekly, and two tables stating one fact eventually disagree (§2, *truth has exactly one authoritative representation*).

**When QE commits directly to `main`** — governance, a shared document, a milestone record — **it fast-forwards `integration` and every idle lane branch in the same action.** Found by rehearsing this flow rather than by reading it: the first governance commit landed on `main` and left `integration` and two lanes a commit behind, which would have made the next lane rebase onto a stale base and re-do the merge. **Every branch at one commit is the resting state**, and anything else is a signal.

#### The Slice Handoff

**Two readers, and neither was in the room when the slice was built.** QE writes the project status and would otherwise reconstruct the milestone, the scope and the limitations from a diff — which is how a status document starts describing what a lane *intended*. **And the next lane assigned to that module inherits nothing else**: under rotating assignment the handoff plus the module's design doc *are* the continuity, so `Limitations` and `Coordination` are being written for a session that does not exist yet.

**So the last commit of every slice carries a `Slice-Handoff` block.** In the commit message, not a file: a shared queue file would conflict between lanes, and a commit message travels with the change forever and is greppable — `git log --grep="Slice-Handoff"`.

```
M12.6 — the ICP declaration

<the usual body: what changed and why, in product language>

Slice-Handoff:
  Milestone:     M12.6 — slice 2 of 5
  Lane:          B — Commercial Profile
  Delivered:     A customer can declare which kind of company buys each
                 product, versioned the way the catalog is.
  Demo:          Settings → Products → an ICP on any product row
  Reuse:         reused    — ProductCatalog, useProducts, VersionedEntry
                 extended  — Product gains an icp association
                 new       — IcpDeclaration; no equivalent exists (L-1 audit)
  Preserved:     behaviour — product catalog unchanged, its suite untouched
                 data      — additive table; no existing row modified
  Reachable:     Settings → Products. Owner edits; member sees it read-only
  Rollback:      0021 down-migration drops icp_declaration.
                 LIMITATION: declared ICPs are not recoverable
  Budget:        green modules/commercial_profile/**
                 amber migration 0021, table icp_declaration
                       (registered in tenancy_policy.py)
  Tests:         +34 in tests/commercial_profile; lane suite green
  Bugs:          fixes B-001 (regression test in signal_engine suite)
                 defers B-007 — needs Lane A's resolution slice first
  Coordination:  opened C-009 (ICP→product read port, owner Lane A)
                 closed  C-006 — milestone assigned, see ADR-0036
  Docs:          27-opportunity-engine.md updated for the new stage;
                 ADR-0035 amended; 06-events.md +1 event
  Limitations:   ICP is declared; nothing consumes it yet
  Findings:      none
```

**`Reuse`, `Preserved`, `Reachable` and `Rollback` are the [`ENGINEERING_LAWS.md`](ENGINEERING_LAWS.md) fields** — L-1, L-8/L-9, L-6 and L-11 respectively. **Their meaning lives there and is not restated here**; the handoff is where they become checkable, because a commit message travels with the change forever and is greppable.

**Every field is required; `none` is a valid value and silence is not.** `Delivered` and `Demo` are written **in the customer's vocabulary** (§4, ADR-0034) — they become the sentence a non-engineer reads in `PROJECT_STATUS.md`, and a line naming a module, a table or a port has not described a product slice.

**`Docs` names what a lane arriving cold would need**, and QE checks it is not empty on a slice that changed behaviour — under rotation the module's design doc is the next assignee's only inherited context (§12). **`Bugs` must account for every row against the module**, fixed or deferred with its reason (Startup step 4). **`Coordination` names every item the slice opened or closed** — QE audits the register against it, because an item closed in a commit but left `OPEN` in the file is worse than one that was never raised. **`Limitations` is where a lane states what it knowingly left undone** — QE reports it as a known limitation rather than discovering it as a defect three slices later.

> **The handoff is input, never the record.** QE measures every figure from the promoted commit. A lane that reports a test count is offering a claim; QE publishes a measurement.

### The Standard Lane Report

**Ratified 2026-08-04, product owner. It binds every lane without exception — Lane A, Lane B, Lane C and QE.** Drafted by Lane C on the product owner's instruction, which is the only route by which this file is amended.

> **The product owner must never read several pages to learn whether a lane needs attention.** The first screen answers six questions and nothing else: **what is this lane doing · is it blocked · does it need me · is it waiting · can it continue · what happens next.**

**Every status update, pause, completion report, blocker report and handoff opens with this block and closes with the two below.** The engineering discussion between them is **unchanged in depth, evidence and repository analysis** — only its position moves.

```text
Lane:
Role:
Current Module:
Current Epic:
Current Slice:

Overall Status:            🟢 ACTIVE · 🟡 WAITING · 🟠 BLOCKED · 🔵 VALIDATING
                           🟣 MONITORING · ⚪ READY FOR NEW WORK · ✅ COMPLETED

Current Activity:          one sentence
Waiting On:                None · Product Owner · Lane A · Lane B · Lane C · QE
                           · External System · Architecture · Repository State
                           · Multiple (list)
Blocking Reason:           one sentence, or None.
Needs Product Owner?       YES — with one sentence of why · or NO
Can Continue Without PO?   YES — naming what continues · or NO — naming why
Next Immediate Action:     one sentence
Estimated Repository Impact:  Small · Medium · Large · Repository-wide
```

**Then the Executive Summary.** The report closes with **Lane State** — current status · completed this report (≤5) · remaining work (≤5) · waiting on, with an explicit owner · requires Product Owner (YES/NO) · priority (P0–P3) · next update — and then **exactly one** Product Owner Action:

| | |
|---|---|
| 🟢 **NO ACTION REQUIRED** | Continue reading only if interested |
| 🟡 **OPTIONAL REVIEW** | Useful information. **No engineering blocked** |
| 🟠 **REVIEW SOON** | A decision is needed later. **Engineering still progressing** |
| 🔴 **ACTION REQUIRED NOW** | **Engineering cannot proceed** |

#### The rules

- **Every field is present; `None` and `NO` are values and silence is not.** An absent field reads as *nobody looked*.
- **Do not invent statuses.** **A lane that needs an eighth has a state the model does not describe, and that is a finding to raise.**
- **`Blocking Reason` and `Waiting On` are different questions.** A blocker stops the work; *waiting on* names who owes an answer. **A lane can be 🟡 WAITING on QE and not blocked at all.**
- **Never hide a waiting state, a blocker or a decision inside narrative.** **If a lane does not need the product owner, say so explicitly** — and then **ask nothing later in the report.**
- **Not every report is urgent, and the format must show that.** Implementation, monitoring, polling, validation, background preparation, blocked work and decisions are different states and must read differently. **A report that sounds the same every time carries no information in its tone.**
- **Any progress figure is the lane's estimate and is marked as one.** It never contradicts `PROJECT_STATUS.md`, which is QE's and measured from the promoted commit.
- **`Next Immediate Action` is input, never authority.**

#### The five states of a decision, which reports must never conflate

**Adopted 2026-08-04 after Lane A challenged a Lane C report and was right.**

| State | Set by | A lane may act? |
|---|---|---|
| **PREPARED** | Lane C | **No** — a recommendation is not a decision |
| **READY FOR PRODUCT OWNER** | Lane C | **No** |
| **PRODUCT OWNER APPROVED** | **Product owner** | **In principle — see below** |
| **MERGED TO INTEGRATION** | QE | **Yes** |
| **AVAILABLE FOR IMPLEMENTATION** | — | **Yes, and only here** |

> **A decision is authoritative when the product owner rules it. It is *actionable* when `integration` records it.** Those are different days, and **every lane reports both.**

**The Task Claim Protocol claims from `integration`**, so **a `TASK-nnn` existing only on a lane branch is invisible to every lane.** Never write *"ratified"* alone where *"ruled, not yet on `integration`"* is the truth, and **never write *"unblocked"* to mean *"a ruling exists"*.**

#### What each lane reports under Distributed Product Development

**Ratified 2026-08-04, product owner directive.** **The Standard Lane Report block above is unchanged and still opens every report.** These are the sections that follow it, and they differ by lane because the lanes now answer different questions.

| Lane | Adds |
|---|---|
| **Product Development lanes** *(A · B)* | **Module Dashboard** — module · epic · active tasks · **preparing · under review · READY** · in progress · QE · completed · blocked. **Task Dashboard** — task · module · epic · status · stage · next action · ETA. Then **repository health · risks · waiting on · next planned slice** |
| **Lane C** | The existing Executive Summary and Portfolio Dashboard, **plus four repository-wide views only the Product Office can produce**: **Repository Execution Dashboard** *(module · owner · preparing · under review · READY · in progress · QE · completed · blocked)* · **Epic Dashboard** · **Lane Dashboard** *(including capacity)* · **Bottleneck Dashboard** — **naming governance, synchronization, ownership, architecture and external bottlenecks separately.** Plus the **Review Queue** — every package awaiting Product Office review — and the **Synchronization Queue** — everything approved and not yet on `integration` |
| **QE** | Its existing reporting plus **certification queue · promotion queue · repository health · failed gates · release readiness · regression summary** |

> **The two queues are the model's instrumentation, and they are Lane C's because only Lane C can see them.** **A Review Queue that grows is Product Office becoming the bottleneck again at approval instead of at authorship** — the one risk this model takes. **A Synchronization Queue that grows is the failure the model was created to end.** Reporting both every cycle is what makes either visible before a lane goes idle.

> **This is not a second Slice Handoff, and the two never restate each other** (§2). **The Slice Handoff lives in a commit message and addresses QE and the next assignee.** The Standard Lane Report lives in a *report* and addresses the product owner.
>
> **Lane C additionally carries a Portfolio Dashboard and a UI Implementation Dashboard** inside its Executive Summary ([`PRODUCT_OFFICE.md`](docs/PRODUCT_OFFICE.md) §11a, §11b) — **the repository-wide views, which only the Product Office produces. No other lane owes one.**

### Repository Closeout

**Repository Closeout is a mandatory engineering phase, never optional** (ratified 2026-08-02, product owner). It is lifecycle stage 5, it runs immediately after every successful promotion, and **the repository is not ready for the next cycle until all of it has finished.**

**Eleven activities, in this order:**

| # | Activity | What it means |
|---|---|---|
| 1 | **Refresh `PROJECT_STATUS.md`** | The executive dashboard — repository state · current milestone · overall completion · milestone progress · repository health · certification status · current blockers · active work · recently completed · recommended next work |
| 2 | **Refresh [`SESSION_HANDOFF.md`](docs/SESSION_HANDOFF.md)** | The operational context the next session needs — and **not a second copy of the dashboard** |
| 3 | **Refresh [`ACTIVE_ASSIGNMENTS.md`](docs/ACTIVE_ASSIGNMENTS.md)** | Promoted claims marked `COMPLETE` **and then removed**; the lane returned to `AVAILABLE`. **QE reconciles the board; it does not fill it** — a lane's next row is written by that lane when it claims |
| 4 | **Refresh certification state** | The record is current for the promoted commit. A fast-forward promotes the tree that was certified, so it carries over — **if anything changed the conditions it names, it is re-cut here** |
| 5 | **Refresh repository metrics** | Every figure in *Repository metrics* below, **re-measured** |
| 6 | **Refresh milestone progress** | Which milestone, which slices closed, what remains |
| 7 | **Refresh roadmap progress** | Against [`IMPLEMENTATION_ROADMAP.md`](IMPLEMENTATION_ROADMAP.md). *Scope* is the product owner's; *progress* is QE's |
| 8 | **Refresh repository health** | Gate status, open defects by severity, coordination register size, technical debt |
| 9 | **Publish the release summary** | Features delivered · bugs fixed · ADRs accepted · migrations · architectural changes · metrics · remaining blockers · recommended next work. **A section of `PROJECT_STATUS.md`, not a new document** |
| 10 | **Synchronize branches** | *Lifecycle stage 6.* **Rebase `integration` onto `main`, always.** Closeout commits land on `main` and never on `integration`, so **every cycle diverges the two by construction** — leaving `integration` alone means the next promotion cannot fast-forward. Replay whatever arrived during the cycle on top of the promoted commit, then fast-forward **every idle lane**. **A lane in active development is not touched**; it rebases at its next Startup, which its Startup already requires |
| 11 | **Declare Repository Ready** | *Lifecycle stage 7.* Only once [`REPOSITORY_RELEASE_CHECKLIST.md`](docs/REPOSITORY_RELEASE_CHECKLIST.md) is complete |

> **Every one of these is derived from the promoted repository. Nothing is ever copied from a feature lane's report.** QE's measurements are authoritative precisely because they are taken from the integrated repository after certification, and **a lane has never seen that repository.**

**The step-by-step runbook — every command, in order — is [`docs/REPOSITORY_RELEASE_CHECKLIST.md`](docs/REPOSITORY_RELEASE_CHECKLIST.md).** This section states *what must happen*; that document is *how QE performs it*, and it carries the tick-boxes. They are deliberately not both: a checklist in two places is a checklist that will disagree with itself.

> **The checklist exists to prevent omissions, not to document intent.** Ticking an item that was not done is worse than having no checklist, because the next session trusts it. **An unticked box is not a failure — an untrue tick is.**

### Repository metrics

**Every promotion re-measures. Previous measurements are never reused.**

| | |
|---|---|
| **Re-measured every time** | pytest totals · frontend totals · Security Invariants · `mypy --strict` · `lint-imports` contracts · coverage · `make smoke` status · certification status · migration head · architecture metrics (modules, ADRs, documents) |

> **Repository metrics are measured. They are never transcribed.** A figure carried forward from the last cycle describes a repository that no longer exists, and it is indistinguishable — to every future reader — from one that was taken today.

### Repository State Validation

**Advisory, run before declaring Repository Ready:** `python3 infra/state-check.py`.

It compares what the governance documents *say* against what git, the migrations directory and the certification manifest *are* — the dashboard against `main`'s commit, the certification conditions against the migration head, the assignment board against its own rules, the bug register's blocking rule, the handoff against the dashboard, the coordination register against its own shrink expectation.

**It reports and never repairs.** Every inconsistency it finds has more than one correct resolution — a stale dashboard might need updating, or the promotion might not have finished — and **choosing between them is a governance decision, not a script's.**

**It checks agreement, never quality.** That `PROJECT_STATUS.md` names the right commit says nothing about whether what it says is true.

### Which gates run when

| Moment | Runs | Why |
|---|---|---|
| **During a slice** | Impacted suites only · `mypy` · `tsc` · `eslint` | Unchanged policy. Speed is the point |
| **Lane → QE** | The lane's full module suite · impacted integration tests · `lint-imports` · `mypy --strict` · frontend suite · production build | The lane proves its own slice |
| **Lifecycle 1 — validation, by QE** | **Everything**: full backend suite with the coverage gate · Security Invariants · frontend suite · `make smoke` · exploratory use of the product | The only place merged code is exercised together |
| **Lifecycle 2 — certification, by QE** | `make certify` · migration reversibility · `make dr`, **at the pinned SHA** | ADR-0032. **The last gate before anything moves** |
| **Lifecycle 3–4 — integrate, promote** | `infra/certification-guard.py` — **is this exact commit certified?** | The only thing standing between an uncertified commit and `main` |
| **Lifecycle 5–7 — closeout, sync, declare** | `python3 infra/state-check.py` (advisory) | Agreement between the documents and the repository |

**`make smoke` binds the human-review ports (3000 and 8000)**, so the review stack and every lane's dev server must be stopped before it runs. That is why it belongs to QE rather than to a lane. **The step-by-step runbook for QE's validation pass is [`docs/QUALITY_ENGINEERING.md`](docs/QUALITY_ENGINEERING.md); the runbook for the whole cycle is [`docs/REPOSITORY_RELEASE_CHECKLIST.md`](docs/REPOSITORY_RELEASE_CHECKLIST.md).**

### Quality Engineering and Integration

**QE builds no customer feature.** Its remit is the repository lifecycle above, and the first stage is what qualifies it for the rest.

**Quality Engineering** — every shared test suite · functional, API, integration, end-to-end, security, regression, performance and accessibility testing · the Security Invariants · exploratory testing · product and UX review · Playground quality · certification. **Expand these incrementally, and only when a capability can provide value immediately: never build an empty framework because it may be needed one day.** Two of those responsibilities — performance and accessibility — are **owned and not yet built**, recorded as [C-014](docs/LANE_COORDINATION.md) rather than stubbed.

**Integration Authority** — the only lane that may merge a validated branch into `integration`, run repository-wide certification, validate milestone completion, promote to `main`, update the repository-wide status documents, **publish measured repository statistics**, and **declare Repository Ready**.

> **QE reports bugs. Feature lanes fix them.** A QE session that fixes a defect in a feature lane's module has become a second implementation stream with no owner, and the module's owner no longer knows what their module does. **Integrating is not implementing** — the same rule binds QE while it holds the merge.

**Why a lane rather than a phase:** every defect that has mattered in this project was found by *using* the product, not by the suite. 2046 tests found none of R4-01, R6-01–04, R7-01–03, R10-01 or R12-01. A lane whose whole job is to use the product is the only mechanism that finds that class reliably, and a lane finds it continuously rather than when somebody remembers.

**QE may write a test in any module's suite** — that is its job — but may not change that module's production code. A failing test it adds is a bug report in executable form, and the module's current assignee makes it pass.

### Identifiers are allocated from a block, never from the highest number seen

**Ratified 2026-08-02, product owner, after `B-024` was allocated twice — seven minutes apart, by two lanes, on separate branches.** Neither push conflicted: they edited different regions of one file and git merged them happily. **Nothing was careless.** Both lanes read the register, both saw `B-023` as the highest, both took the next number. **The allocation model was the defect.**

> **A lane allocates only from its own block. Two lanes therefore cannot choose the same number — not "are unlikely to", cannot.**

| Actor | `B-` bugs | `C-` coordination | `TASK-` | ADR |
|---|---|---|---|---|
| **Historic** — allocated before this rule | `001`–`099` | `001`–`099` | `001`–`099` | `0001`–`0099` |
| **QE** | `100`+ | `100`+ | — *(QE writes nothing in the backlog)* | `0100`+ |
| **Lane A** | `200`+ | `200`+ | `200`+ | `0200`+ |
| **Lane B** | `300`+ | `300`+ | `300`+ | `0300`+ |
| **Lane C** *(Product Office)* | `400`+ | `400`+ | `400`+ | `0400`+ |
| **Lane D** | `500`+ | `500`+ | `500`+ | `0500`+ |
| **Lane E** | `600`+ | `600`+ | `600`+ | `0600`+ |
| **Product owner** | `900`+ | `900`+ | `900`+ | `0900`+ |

**Within your block, take the next free number.** Across blocks, nobody needs to look at anybody else.

**Why blocks rather than the alternatives.** A central allocator recreates the bottleneck that scheduling was moved out of QE to remove. A leased or ledger-based scheme makes a collision *detectable* — it still has to be resolved by hand, and the lane still has to get the resolution right. **A block makes it unrepresentable**, which is the standard §2 already prefers: *"a violation that is unrepresentable over one that is merely discouraged."* It is also the boring, proven answer — IANA, MAC addresses, database sequence caching and per-node CIDR allocation are all the same idea.

**Chronological traceability is not lost.** It never lived in the number: every row carries `Found`, and `git log` carries the rest. **`B-301` after `B-105` is not out of order; it is a different allocator.**

**Enforced twice.** `infra/state-check.py` refuses a duplicate in any class — `B-`, `C-`, `TASK-` and ADR filenames — so a fat-finger *inside* a block is caught even though a collision *across* blocks is impossible. **The range prevents; the check detects.**

**Migrations are deliberately exempt**, and are the one identifier that must stay dense: Alembic's `down_revision` is a linear chain, so a gap is not a cosmetic oddity but a broken migration graph. **The existing practice is correct and stays** — a lane that finds its number taken renumbers on rebase and says so in the commit message, as Lane A did twice for `0026`. **The chain is the identity; the filename follows it.**

**Renumbering an existing identifier is QE's, at merge, and only to break a tie** — the later claim moves, decided by author timestamp. This should now never occur.

### Bugs

**One register: [`docs/BUGS.md`](docs/BUGS.md).** Not a file per bug, not an issue tracker, not scattered TODOs.

Every row carries: **ID · Title · Module · Current assignee · Severity · Status · Commit found · Steps · Expected · Actual.** **A defect belongs to a module; whoever is currently assigned that module fixes it.**

| | |
|---|---|
| **Opens a bug** | **Every lane, not only QE.** Reporting is a universal duty |
| **Fixes it** | The lane **currently assigned** the module the defect is in |
| **Verifies and closes** | **QE**, never the lane that fixed it |
| **Severity** | 🔴 blocks a milestone · 🟠 wrong behaviour a customer would hit · 🟡 wrong but survivable · 🟢 cosmetic |

**Severity says how much it hurts. A second question says whether the repository can move** (ratified 2026-08-02, product owner):

| Class | What it is | Priority |
|---|---|---|
| **Blocking Quality Defect** | **Prevents promotion.** Coverage below the floor · a failing test · a failing type check · a broken migration · an import-contract violation · a Security Invariant failure | **The owning lane's highest priority.** Addressed **before significant new feature work**, unless another lane can make meaningful independent progress meanwhile |
| **Non-blocking defect** | Functional and UX improvements · technical debt · future hardening | Normal prioritisation |

> **This is a flow rule, not a stop-work order.** A blocking defect holds **every** lane's finished work hostage, because every candidate is cut from the same `integration` — [B-024](docs/BUGS.md) held 9 commits on `integration` and 25 on a lane that had never touched the affected modules. **Restoring flow is worth more than one more slice**, and it is usually far smaller.

**Finding a defect outside your assignment is not permission to fix it — it is an obligation to report it.** Finding a bug never grants implementation ownership. Open the row with every field above filled, then **carry on inside your Change Budget**. Do not fix it, do not work around it silently, and do not leave it in a comment or a commit message where nothing tracks it.

> **No defect disappears because the lane that found it could not fix it.** That is the single failure the register exists to prevent, and it is the one a busy lane commits by accident.

**A bug fixed without a regression test is not fixed** (§11). The test belongs in the **affected module's** suite and is written by the lane that fixes it — so it survives the next reassignment.

### Coordination

**One register: [`docs/LANE_COORDINATION.md`](docs/LANE_COORDINATION.md).** It exists to stop two lanes independently encoding contradictory architectural assumptions, and it does nothing else — it is not a roadmap, not a bug tracker, not an ADR, and **not a discussion log**.

**An item exists only when another module's assignee or the product owner must answer something before implementation can safely continue.** If you can proceed without encoding an assumption about the answer, you do not need an item. If the answer would change a public contract, a schema, an event payload or a module boundary, **you may not proceed** — that is the whole case the register serves.

**Every lane reads every open item before beginning a slice** (*Startup* step 5), and a Slice Handoff names the items it opened and closed.

**Every item carries a lifecycle state**, so a reader can see *where* a decision is stuck rather than only that it is (ratified 2026-08-03, product owner):

| State | Set by | Means |
|---|---|---|
| `OPEN` | Whoever raises it | Raised, nobody has looked |
| `READY FOR LANE C` | The raising lane | **Investigation is warranted and nothing else blocks it.** Claimable |
| `IN ANALYSIS` | **Lane C**, on claiming | Being investigated |
| `READY FOR PRODUCT DECISION` | **Lane C** | **Options, trade-offs and a recommendation are prepared.** Waiting only on a ruling |
| `READY FOR IMPLEMENTATION` | **Product owner**, on ruling | Decided. The implementing lane may proceed |
| `CLOSED` | The requesting lane | The dependency no longer exists |

**`AWAITING LANE C` is used only while Lane C has no session.** It is deliberately distinct from `READY FOR LANE C`: one says *nobody can take this yet*, the other says *it is ready to be taken*. **An item assigned to a lane that cannot answer is worse than one visibly unowned**, because it looks like progress.

```
Coordination  →  Agreement  →  Implementation  →  ADR  →  Coordination closed
```

> **A coordination item is a temporary implementation question on its way to becoming permanent architecture.** The register should therefore **shrink** over time. A row open for months is either a decision nobody will make or a question that was never really blocking — **both are findings**, and a register that only grows has become the discussion log it is not allowed to be.

**A defect is not a dependency.** Something behaving wrongly today is a `B-` row; something not yet built or agreed is a `C-` row.

### Repository certification

**Certification is deterministic, and it is a record rather than an opinion.** It states that a specific commit satisfied specific guarantees under specific conditions ([ADR-0032](docs/architecture/adr/0032-release-certification.md)); nothing in the system can *declare* a version certified, exactly as nothing can declare a prompt released.

**QE certifies a commit, immediately before promoting that same commit.** The gates are the decision: **if certification succeeds, promotion occurs, and no further approval is sought or required.** Equally — **a failing gate is never overridden, and the sequence is never shortened because a slice looks small.** QE's authority is to run the gates faithfully and act on the result, not to judge whether the result matters.

**Certification refreshes the measurements.** Whenever QE certifies, every repository figure that has moved is re-read and republished — pytest totals, frontend totals, Security Invariants, MyPy statistics, import-linter contracts, coverage, smoke status, migration head, the certification manifest. **A stale measurement surviving a successful certification is the defect certification exists to remove**, and it is how a dashboard starts describing a repository that no longer exists.

**A certification expires by derivation, not by decision.** Change the rendering protocol, re-release a prompt, add a migration or edit a scenario and the recorded run stops describing the repository: `is_certified` reads false on its own. **Nothing can be marked certified by hand.**

**`make certify` has no options**, deliberately: a mode that skipped a gate would produce a run that cannot certify, and a command whose convenient path yields worthless evidence teaches people to use it.

### Test data enters the way a customer's data enters

**A lane may create whatever data its slice needs to be validated. It may not create it by a route a customer does not have.**

Never: insert rows directly into production tables · bypass a business rule, Better Auth, authorization, or an API · disable validation · add a development-only shortcut. Data arriving by a private door proves the door, not the product — and every guarantee the pipeline makes about that row is unproven for it.

**The only approved doors are the Playground, the Provider Simulation Framework, and the approved infrastructure seeders** — and the architectural principles still bind inside them: the simulator behaves exactly like a production provider, never bypasses the Provider Port, and holds no privileged downstream knowledge ([20-provider-simulation.md](docs/architecture/20-provider-simulation.md)).

> **If realistic data is hard to generate, improve the simulation. Never weaken the product to make data easy.** The difficulty is usually the product telling you something true about a path a customer will also find hard.

### Concurrent milestones — amending §20d

§20d requires `PROJECT_STATUS.md` to reflect the previous milestone before the next begins, and [IMPLEMENTATION_ROADMAP.md §1](IMPLEMENTATION_ROADMAP.md) recorded *sequential single-stream execution*. **Both were written for one session and are amended here, as a Category 1 sequencing change.**

> **Lanes may run concurrent milestones.** The dependency graph still governs order — a lane may not start work whose inputs another lane has not shipped.

**Amended again, 2026-08-02.** This paragraph said *a lane does not begin its next milestone until `PROJECT_STATUS.md` reflects the previous one of that lane*, making a lane's next slice wait on QE's Closeout. **That is exactly the idle capacity *Continuous execution* removes**, and the rule is withdrawn: **a lane claims its next `READY` task the moment it sets `IN VALIDATION`**, whatever the dashboard currently says.

**What §20d actually protects survives intact**, and it was never the waiting: `PROJECT_STATUS.md` must describe the promoted repository rather than a lane's intentions, and **QE alone writes it, measured from `main`**. A lane starting its next slice changes nothing about that — it is not the author of that record and never was.

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
- **Promote a commit that was not itself certified.** Certification binds to an immutable commit; promotion promotes **that** commit, never `integration`'s current head, and `promoted == certified` or the promotion aborts (§20e). Equally: never re-read a certification record against a different commit, and never restart a cycle's measurements at a newer one.
- Declare a repository cycle finished before all seven lifecycle stages have completed. **Stopping at certification, or at promotion, is an incomplete cycle** — Repository Closeout is mandatory, and Repository Ready is declared only from a complete [`REPOSITORY_RELEASE_CHECKLIST.md`](docs/REPOSITORY_RELEASE_CHECKLIST.md) (§20e).
- Leave a documented prerequisite uninstalled and a gate consequently unrun, where installing it was within authority (§20e, *QE removes its own blockers*). Equally: install a **new project dependency** without an ADR, or change the environment until a failing gate passes.

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
