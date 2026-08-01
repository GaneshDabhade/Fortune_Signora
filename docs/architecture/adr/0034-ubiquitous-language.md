# ADR-0034: The Product's Ubiquitous Language — What a Customer Says, and What Engineering Says

## Status

**Accepted** — 2026-08-01, at the product owner's direction. Introduces no module, table, endpoint or dependency. It fixes **vocabulary**, and the boundary between two vocabularies that have until now been one.

It amends nothing. Every architecture document, every module name, every table and every API path in the repository remains correct — this ADR does not rename any of them, and says explicitly that it must not.

## Context

`CLAUDE.md` §4 has required a ubiquitous language since the first commit:

> *"Every module owns its own bounded context, its own ubiquitous language, and its own aggregates... Claude must use that document's glossary terms exactly as defined — never invent a synonym, never repurpose a term from one module inside another."*

That rule has been followed rigorously and it has one gap large enough to have gone unnoticed for thirteen modules: **it governs the language between engineers and says nothing about the language between the product and its customer.** DDD's ubiquitous language is a contract with the *domain expert*, and Signora has two kinds of domain expert — the architect, who thinks in modules and pipelines, and the seller, who thinks in accounts and deals. The repository has been serving only the first.

### What that cost, found by audit

**"Workspace" is Signora's word for a tenant.** It is the right word: [11-tenancy.md](../11-tenancy.md) builds RLS, the `workspace_id` column, `SET LOCAL app.workspace_id`, the `active_workspace_id` claim and the entire isolation model on it, and every one of those is correct and must not change.

It is also, today, **the word the product says to a customer** — because nothing ever said it should not be:

| Surface | What a customer reads |
|---|---|
| Empty state, every new account | *"You are not in a workspace yet"* · *"A workspace is where your accounts, evidence and decisions live"* · **"Create a workspace"** |
| Settings | *"Workspaces"* · *"Workspaces you belong to"* · *"New workspace"* · *"A workspace holds one company's revenue data"* · *"Workspaces are isolated from each other. Data never crosses between them."* |
| Application header | *"Active workspace"* |
| After a password sign-in | a redirect to **`/workspaces`** — a route that does not exist |

The last line is the finding that makes this an ADR rather than a copy edit. **The leak is not cosmetic: it produced a dead route in the first ten seconds of a new customer's life**, because the code was reasoning about a tenancy concept and the product needed a destination, and nobody noticed the two had drifted apart.

The second-worst is *"Workspaces are isolated from each other. Data never crosses between them."* That is a **true and correct statement of the tenancy architecture**, written into a dialog a salesperson reads. It answers a question nobody asked and raises one nobody wanted.

### Why prose could not have prevented this

Every one of those strings was written deliberately, by an engineer who had read the architecture, in a codebase whose constitution demands consistent vocabulary. They are not carelessness — they are what happens when **the only vocabulary that is written down is the internal one.** An engineer reaching for the right word finds `Workspace`, correctly, because it is the only word the repository has.

*A guard that cannot fail is documentation pretending to be code.* A glossary nobody can violate is the same thing. This ADR therefore ships with a test.

## Decision

**Signora has two vocabularies. Both are correct. Exactly one of them is customer-facing, and the boundary is enforced.**

### 1 · The customer-facing language

What a customer sees, says, and is asked about. **These are business terms; none names a mechanism.**

| Term | What it means to a customer | Internal counterpart |
|---|---|---|
| **Organization** | *"My company on Signora."* Created once, at sign-up; everything belongs to it. | **Workspace** (`workspace`, `workspace_id`, RLS scope) |
| **Team** | The colleagues in my Organization, and what each may do. | Membership · `WorkspaceRole` · Casbin subject |
| **Product** | What we sell. *(Not yet built — see §6)* | — |
| **ICP** | The kind of company we sell to. *(Not yet built)* | Signal relevance profile, in part |
| **Buying Committee** | The people who decide. *(Not yet built)* | Person entities *(deferred)* |
| **Account** | A company Signora is watching for me. | `Entity` of `EntityKind.COMPANY` |
| **Signal** | Something Signora believes about an Account, and why. | `Signal` — **the one term that is identical on both sides, deliberately** |
| **Opportunity** | An Account worth working, and what I decided about it. | `Opportunity` + workflow state |
| **Evidence** | The record underneath a claim, which I can open. | Business event · observation · claim · provider reading |
| **Research** | A deeper look at one Account, on demand. | `ResearchTask` · `ResearchFinding` · `ResearchSynthesis` |
| **Workflow** | Taking an Account on, handing it over, closing it, dismissing it. | Opportunity state transitions |

### 2 · The internal language — engineering only, and never on a screen

**Workspace · Tenant · RLS · Provider** *(Apollo, Bombora, CoreSignal, Crunchbase, BuiltWith, …)* **· Pipeline · Knowledge Graph · Entity · Claim · Observation · Business Event · Buying Score · Signal Catalog · Signal Profile · Scoring Model · Qualification Policy · Evidence Set · Prompt Registry · Inference · Outbox · Event Bus · Module · Port · Adapter · Composition root.**

Every one of these is correct, load-bearing, and must keep its name in code, in schema, in `docs/architecture/` and on the wire.

### 3 · The rule

> **A term is customer-facing only if a salesperson would use it unprompted to describe their own job.**

*"I need to look at that account"* — yes. *"Add Priya to my organization"* — yes. *"Which workspace is this signal's business event in?"* — no. That test is deliberately about the **customer's** speech rather than about whether the word is jargon: *Signal* and *Opportunity* are both technical terms in this codebase and both are words a seller says every day, which is exactly why they are the same on both sides.

### 4 · What this changes, and what it explicitly does not

**Changes:** user-visible strings — labels, headings, empty states, dialog copy, toast messages, page titles, route paths a customer sees in the address bar.

**Does not change — stated because the temptation to "finish the rename" will be strong and would be wrong:**

- **No table, column, or migration.** `workspace_id` stays.
- **No API path.** `/workspaces/{workspace_id}/accounts/...` stays. The API is an engineering contract, and its consumer is the frontend, not a customer.
- **No JWT claim.** `active_workspace_id` stays ([ADR-0026](0026-jwt-boundary-architecture.md)'s claim set is closed and its stability is a security property).
- **No module, type, variable, port, or event name.** `WorkspaceQueryPort`, `workspace_tenancy`, `WorkspaceRole` all stay.
- **No architecture document.** [11-tenancy.md](../11-tenancy.md) is about tenancy and should say *workspace* on every line.

**A translation at the edge, never a rename through the stack.** Renaming inward would mean a schema migration, a claim change, an event-contract change and 29 import-linter contracts re-examined — to solve a copywriting problem. It would also destroy the thing that makes the internal language good: *workspace* is precise about isolation in a way *organization* is not, and a `RLS policy on organization_id` would read as though a customer's org chart controlled row visibility.

### 5 · Enforcement

A vocabulary that lives only in this document will leak again, the same way and for the same reason. `frontend/tests/components/vocabulary.test.tsx` scans user-visible strings in `app/` and `components/` for internal terms and fails on one.

It checks **strings a human reads** — JSX text, `title`/`description`/`label`/`placeholder`/`message` props, `aria-label` — and deliberately not identifiers, imports, types, hooks, query keys, API paths or comments, all of which *should* say `workspace`. That asymmetry is the whole point: the same file may legitimately contain `workspaceId` fifteen times and must never contain the word in a sentence.

**It is not a spell-checker.** It states one architectural property — *the customer's vocabulary and the platform's vocabulary are separate* — in the only form that survives a year of new screens written by people who never read this document.

### 6 · What this ADR does not decide

**It defines the words; it does not schedule the capabilities.** *Product*, *ICP* and *Buying Committee* appear in the customer-facing table with no implementation, deliberately: they are the terms those capabilities **will** use when they are built, recorded now so the first screen that needs one does not invent a synonym. Their sequencing is the [Consistency Review's](../../../PRODUCT_ROADMAP.md) recommendations 1–3 and remains the product owner's.

**It does not adopt Better Auth's organization plugin.** That plugin — already in the dependency tree, no new dependency — is the natural home for organization creation, roles and **invitations**, which the product currently lacks entirely. Adopting it adds tables and changes where membership is authoritative, which is a category-3 change needing its own ADR. **This ADR makes that decision cleaner rather than pre-empting it**, by fixing what the customer-facing concept is called before choosing what implements it.

## Consequences

**We gain:** a customer who never has to learn Signora's architecture to use it · a dead route removed from the first minute of the product · a documented answer to *"what do we call this?"* for every screen from here on · and an enforcement mechanism, so the answer holds without anyone remembering this document.

**We give up:** a single word for a single concept. `Organization` on screen and `workspace` in code is a translation an engineer has to hold in their head, and translations are a real cost — this one is paid at exactly one boundary, `frontend/`, and is why §4 forbids the rename spreading past it.

**We accept:** that the audit is only as good as its scan. The test covers the frontend, which is every surface a customer currently sees. **API error messages are the known gap** — `"Workspace {id} does not exist"` is a domain exception rendered into the error envelope, and a 404 body is technically customer-reachable. It is not fixed here because those sentences are also the engineer's diagnostic, and splitting them is a design question rather than a copy edit. **Recorded as the first thing to revisit if a customer ever reports one.**

## Alternatives considered

**Rename `workspace` to `organization` throughout.** One word, no translation, no test. Rejected: a migration, a claim change, an event-contract change and 29 contracts re-examined to solve a copywriting problem — and it would make the tenancy code less precise, since *organization* says nothing about isolation.

**Document the glossary and rely on review.** What §4 has been doing. It produced every string in the Context section, written by engineers who had read the constitution. **The absence of enforcement is the finding, not the absence of a glossary.**

**Use Better Auth's organization plugin now and let it define the vocabulary.** Tempting, and backwards: it would let a library's schema decide the product's language, and the vocabulary question would still be open for *Product*, *ICP*, *Account* and *Evidence*, none of which the plugin knows about.

**Ship the words without the tests.** Rejected on the codebase's own terms: *a guard that cannot fail is documentation pretending to be code.*

## References

- [CLAUDE.md](../../../CLAUDE.md) §4 — DDD rules, and the ubiquitous-language requirement this extends
- [11-tenancy.md](../11-tenancy.md) — what *workspace* means, and why it keeps the name
- [ADR-0026](0026-jwt-boundary-architecture.md) — the closed claim set, including `active_workspace_id`
- [ADR-0033](0033-authentication-methods.md) — sign-in methods; the flow whose redirect this ADR's audit found broken
- [PRODUCT_ROADMAP.md](../../../PRODUCT_ROADMAP.md) — the Consistency Review, and where *Product*, *ICP* and *Buying Committee* are scheduled
