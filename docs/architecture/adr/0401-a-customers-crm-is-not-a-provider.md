# ADR-0401: A customer's CRM is not a provider

## Status

**PROPOSED — 2026-08-04, drafted by Lane C — Product Office.** **Not ratified, and nothing is implemented.**

> **Prepared ahead of allocation, so the lane that owns [Epic E1](../401-epic-e1-crm-read.md) inherits this decision rather than making it accidentally on its third day.** Lane C prepares decisions; the product owner makes them.
>
> **It blocks phase 3 of E1 and nothing earlier.** Acquisition and the consumption edge proceed regardless — see [401-epic-e1-crm-read.md](../401-epic-e1-crm-read.md) §8.

## Context

**E1 connects a customer's CRM and reads from it. Nothing in the repository says what the result *is*.**

**The code would accept the wrong answer without complaint.** `ClaimSource.provider` is a plain `str`, and `Claim` already carries a `workspace_id` — so a HubSpot record can become a claim with no type change, no migration and no new concept. **It would work on the first day.** By the hundredth, every downstream conclusion would rest on it and the decision would be irreversible in practice.

**The repository already draws the distinction that decides this, in prose, in the module that owns it:**

> `integrations/domain/connection.py:3` — *"a **provider** is Signora's supplier and Signora holds the credential; an **integration** is the **customer's own system** and the customer holds it. That is a business relationship, not a synchronization mechanism."*

**That sentence is about ownership of a credential. This ADR extends it to the data**, because the same asymmetry applies and nothing has yet said so.

| | A provider asserts | A customer's CRM asserts |
|---|---|---|
| **What it is** | An observation of the world | **The customer's own record of their own business** |
| **Authority** | Contested; resolved against other providers | **Authoritative in this workspace, meaningless outside it** |
| **When wrong** | Signora resolves, or marks it ambiguous | **Only the customer can correct it — and they are entitled to be wrong** |
| **Falsifiable** | Yes — another provider can disagree | **No.** *"We call Acme a customer"* is true by virtue of being said |

**The Knowledge Graph is built to adjudicate between sources describing the same world.** Feeding it a customer's private opinion asks it to adjudicate between a description of the world and a statement that cannot be false. **It would do so, silently, and a `closed-lost` from 2023 would compete with an observation from last week inside identity resolution.**

**What the architecture already fixes and this ADR does not reopen:** claim provenance and the evidence chain · identity resolution and ambiguity states (ADR-0035) · the connection/grant separation · `ExecutionContext` · Provider Platform's ownership of synchronization.

## Decision

> **CRM data is a workspace-scoped fact about the customer's business. It is never a claim, and it never enters the Knowledge Graph as evidence.**

**The two are joined by a link, not by a merge.** A CRM account *references* a resolved entity; it does not *contribute* to resolving one. **Resolution stays a question about the world, and the link stays a question about this customer's records.**

| | |
|---|---|
| **New** | A **workspace-scoped CRM read model** — accounts, opportunities, and their link to a resolved entity |
| **Reused unchanged** | Identity resolution — **to find the link**, never to accept a claim |
| **Reused unchanged** | Connection, grant, secret storage, `ExecutionContext`, sync, pacing, watermarks, sync events |
| **Explicitly not created** | **A `ClaimSource` whose `provider` is a CRM slug** |

**Precedence, stated once so it is not re-argued per field:** for facts about **the customer's own commercial relationship** — is this an account, is it a customer, whose is it, what stage — **the CRM wins outright.** For facts about **the world** — headcount, industry, technology, funding — **the CRM is not consulted at all.** **No field is contested by both**, and that is the test of whether the boundary was drawn correctly.

**When they appear to disagree, both are shown.** *"Your CRM says Acme is a customer; Signora observed a 40% headcount reduction"* is not a conflict — **it is two true statements, and it is the product working.**

## Alternatives considered

| | Option | Why not |
|---|---|---|
| **A** ✅ | **Workspace-scoped read model, linked to entities, never a claim** | **Recommended.** Preserves the graph's meaning, reuses resolution for linking, keeps the customer's records under the customer's authority, and **makes the precedence rule stateable in one sentence** |
| **B** | **CRM records become claims with `provider = "hubspot"`** | **Free to build and very hard to reverse.** A non-falsifiable statement enters an adjudication designed for falsifiable ones. **Stale CRM data would compete with observations**, and the ambiguity states would report disagreements that are not disagreements |
| **C** | **A separate `crm` bounded context** | Defensible, and **rejected on cost, not on principle.** The read model has no independent lifecycle, no invariants of its own and one consumer; `CLAUDE.md` §6's bar for a new context is not met. **Revisit if E2 write-back adds command-side behaviour** |
| **D** | **Store CRM data on the entity itself** | **Breaks tenancy** — an entity is shared across workspaces and *"Acme is a customer"* is true in one. **The most damaging option**, and the easiest to reach by accident |

> **B is the option a lane arrives at by writing the adapter first**, because the claim pipeline is the path of least resistance and every type already fits. **That is precisely why this ADR is drafted before the adapter and not after it.**

## Consequences

**Positive.** The graph keeps meaning one thing. **D3 — *which accounts are already customers* — becomes a read model query rather than an inference**, and it is **S**. Tenancy is preserved by construction. **A customer's CRM staleness never degrades Signora's own intelligence**, which is the failure mode most competitors ship with.

**Negative.** A second store of account-shaped data, and **two things a seller might call "an account."** The UI must never present them as one thing — **and naming is [ADR-0034](0034-ubiquitous-language.md)'s, not this ADR's.** A CRM record whose entity never resolves stays unlinked and is visible only in CRM terms; **that is honest, and it should be visible rather than hidden.**

**Neutral.** No new bounded context (alternative C). No change to any existing module's domain logic. **Entirely additive.**

## Open questions

> **❓1 · Does E1 read records or activity?**
>
> **This ADR assumes records** — accounts and opportunities. **The `Capability` enum models `CRM_ACTIVITY` only; [ADR-0014](0014-crm-integration-strategy.md) says *"opportunity/activity sync"*; D3 needs records.** Analysed in [401-epic-e1-crm-read.md](../401-epic-e1-crm-read.md) §5, where records are recommended. **If activity is chosen instead, this ADR's reasoning is unchanged** — activity is even more clearly not a claim about the world — **but the read model's shape is different.**

> **❓2 · What does a seller call each of these?**
>
> Two account-shaped things reach one screen. **[ADR-0034](0034-ubiquitous-language.md) owns this and a test enforces it.** Not settled here, and it should be settled before phase 4 renders anything.

> **❓3 · Does E2 write-back change the answer?**
>
> Writing *into* a customer's CRM adds command-side behaviour and may meet the bar alternative C does not. **Not a reason to create the context now** — it is a reason to keep the read model's boundary clean enough that promoting it later is cheap.

## Compliance

**`Proposed`. Nothing to comply with yet.** On ratification: **no `ClaimSource` may carry a catalog slug** — assertable structurally, and the cheapest guard in the decision · the CRM read model is workspace-scoped and joins to entities **by link, never by contributing to resolution** · **a test asserts a CRM record cannot reach identity resolution as evidence.**
