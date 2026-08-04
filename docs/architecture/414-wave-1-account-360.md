# 414 — Wave 1 · Account 360 — implementation preparation

> **Prepared by Lane C — Product Office. No code was written and none should be.** Every claim verified against `origin/integration` on 2026-08-04.
>
> **Approved UI** — **Account 360**. The [Fortune Signora Design Project](410-approved-ui-specification.md) is authoritative for frontend behaviour. **This package does not state what the screen looks like. It states what the backend must provide for it.**

## 0 · A correction to [412](412-backend-capability-matrix.md), made before anything is built

**I placed Account 360 in wave 1 on the grounds that it *"needs no decision from anybody."* That is true of what it can deliver and false of the screen as a whole.**

**The approved screen has 27 sections. Reading them individually rather than counting endpoints: eleven are served by modules that exist, and the rest are not.** Two of them are blocked by **O1**, the Person decision, which I named as the wave 6 blocker without noticing it also reaches into wave 1.

> **So wave 1 is a *bounded subset* of Account 360, and the boundary is stated here rather than discovered during implementation.** This is `CLAUDE.md` §2's rule applied to my own recommendation: *"when a slice's demonstration needs a paragraph of architecture, look for the smaller slice inside it."*

**The subset is still the right first slice.** It converts eleven sections of existing, unreachable intelligence into a customer-visible surface, and it needs no ruling to do it.

## 1 · Section-by-section

**🟩 served today · 🔴 blocked by a decision · ⬜ no source exists · ➡️ a later wave already owns it**

| Section | Source | |
|---|---|---|
| **Header identity** — name, employees | `knowledge_graph` `account-identities` | 🟩 |
| **Health score** — value, trend, 24-point fall | `buying_score_engine` `/score` — `score`, `trend`, `score_change`, `trigger`, `contested`, `is_current` | 🟩 |
| **Why the score moved** — contribution bars | `ContributionResponse` — `posture`, `relevance`, `evidence_age`, `points`, `counted`, **`dissenting`**, `reason` | 🟩 |
| **Observations** — what changed and when | `observation_engine` — `attribute`, `previous_value`, `current_value`, `direction`, `magnitude`, `observed_at`, `supersedes` | 🟩 |
| **Business events with evidence** | `business_event_engine` — `type_key`, `summary`, `corroborating_providers`, nested observations | 🟩 |
| **Detected signals** — 6 in 30 days | `signal_engine` `/validation` · `/signal-catalog` | 🟩 |
| **Research** — company, strategic priorities, financial posture, relationship history | `ai_research_engine` `GET /research` | 🟩 |
| **The account summary paragraph** | `ai_platform` `/narration` — `statements`, `facts`, **`evidence_unchanged`**, `prompt`, `model`, `vendor` | 🟩 |
| **Opportunities** — 3 open, 4 closed in 12 months | `opportunity_engine` `/accounts/{id}/opportunity` | 🟩 |
| **Timeline** — 412 entries | `timeline` — `kind`, `occurred_at`, `source_module`, `source_ref`, `detail` | 🟩 |
| **Technology stack** — Salesforce, SAP, Azure, Okta | `knowledge_graph`, `EntityKind.TECHNOLOGY` | 🟩 |
| **Competitors** — Cadenza, Orbital, in-house build | `commercial_profile` `GET /competitors` — **[ADR-0403](adr/0403-signal-engine-reads-a-declaration.md), ratified and shipped** | 🟩 |
| **Contacts** — 24 known, 6 on the committee | **Person** — ✅ **ADR-0400 ratified 2026-08-04** | 🟠 |
| **Org chart** — confirmed vs inferred | **Person** — ✅ **ADR-0400 ratified 2026-08-04** | 🟠 |
| **Next actions** — *"Approve the drafted procurement intro"* | `sales_engagement` — built, no `interface/` | ➡️ **wave 2** |
| **Meetings** — QBR, procurement introduction | `MEETINGS` is in `LIVE_CAPABILITIES`; **nothing is connected** | ➡️ **wave 5** |
| **Product usage** — licence utilisation, weekly actives, support tickets, NPS | **No telemetry source anywhere in the repository** | ⬜ |
| **Intent** — category research, competitor page visits, pricing page visits | `ProviderCapability.BEHAVIOURAL_INTENT` **exists and no provider is wired** | ⬜ |
| **Calls and threads** — QBR recording, talk ratio, the 28 July thread | **Conversation intelligence does not exist** | ⬜ |
| **Documents** — proposal v4, MSA 2021, one-pagers | **No document store** | ⬜ |
| **Notes** — `/` commands, `@` mentions | **No notes model; mentions need Person** | ⬜ |
| **Key facts** — account tier, procurement threshold, security review status, data residency | **Mixed.** Some are customer declarations; none is declared today | ⬜ |
| **Relationship history** — 2021 to today, collapsed to milestones | Derivable from `timeline` + `opportunity_engine`; **no aggregate exists** | ⬜ |

**Eleven 🟩 · two 🟠 · two ➡️ · seven ⬜.**

> ✅ **Amended 2026-08-04.** The two 🔴 were contacts and the org chart, blocked on O1. **ADR-0400 is ratified, so they are no longer blocked — they are unbuilt.** **They stay out of wave 1 regardless**: wave 1 is a read composition over what exists, and `EntityKind.PERSON` does not exist yet. **The boundary is unchanged; only its reason is.**

## 2 · What wave 1 delivers

> **The eleven 🟩 sections, and nothing else.**

**It is a read-only composition over twelve modules and one new capability.** No domain change, no migration, no new event, no new bounded context. **Every endpoint it needs already exists** — the work is a route, a composition root, and a page.

**The one genuinely new thing is the batch.** The screen renders eleven sections; **eleven sequential requests is the N+1 that `CLAUDE.md` §14 calls a defect at write time**, and `knowledge_graph`'s router already states the principle it is defending: *"a page of fifty accounts must cost one request, not fifty… there is deliberately no single-account variant."*

**That is a composition question, not a module question**, which is why it belongs in `apps/api/composition/` — where `accounts.py` already assembles exactly this kind of read.

## 3 · What must NOT be built

**Nothing on this list is a gap to fill opportunistically.**

| | Why not |
|---|---|
| **A contacts table, or a `PERSON` member on `EntityKind`** | ⚠️ **Reason changed 2026-08-04, prohibition unchanged.** O1 is now ruled, so this is no longer taking a decision — **it is Epic C's slice, and wave 1 is a read composition that builds no new domain.** Adding Person here would be a second implementation of it |
| **Product usage, intent, calls, documents, notes** | ⬜ means *no source*, not *no endpoint*. **Building a screen section against invented data is exactly what `no-mock-data.test.tsx` exists to refuse** |
| **A second narration, score or research call** | All three exist and are published. **Reuse, do not re-derive** |
| **A single-account identity lookup** | The batch endpoint answers a request for one perfectly well, and `knowledge_graph` says so in the file |
| **Any write path** | Account 360 in wave 1 is read-only. `TransitionOpportunity` is the opportunity's write surface and belongs to its own slice |

## 4 · How the absent sections appear

**The approved design already answers this, and it is the reason wave 1 is honest rather than partial.**

> App Shell §18 and the Account 360 specification both require **absence to be stated**: *"a collapsed section still states its count and its worst status, so collapsing never hides a risk"*, and a facet with zero matches *"stays visible at 45% so the absence is information."*

**So a ⬜ section renders as a designed empty state naming what would fill it** — the same discipline `live_capabilities` enforces on the Connection Center, and the same rule [ADR-0402](adr/0402-a-rule-is-data.md) applies to a rule that matches and reaches nobody: *"this has matched 14 times; you are not being told about it yet."*

**This is not a workaround. It is the approved behaviour**, and it means wave 1 ships a screen that tells the truth rather than a screen with holes in it.

## 5 · Acceptance

**Every figure traces to an endpoint that exists today** · **one request renders the page** · **eleven sections carry real data and the rest carry a stated absence** · **no new module, table, event or migration** · **`no-mock-data` and `design-tokens` pass unchanged** · **the page is demonstrable to a non-engineer without naming a module** (`CLAUDE.md` §2).

## 6 · Open questions

> **🟢 Does the batch belong in `composition/` or as a per-module fan-out at the frontend edge?** **Engineering's**, and not escalated — both satisfy §14, and `accounts.py` is the existing precedent.

> **🟡 Do the seven ⬜ sections stay visible-and-empty, or are they absent from wave 1's page entirely?** **The approved design says visible.** Recorded because it is the one place where shipping the approved behaviour costs more than shipping less, and somebody may reasonably want the smaller page first.

**Neither blocks the slice.** O1 blocks two sections and nothing else in it.
