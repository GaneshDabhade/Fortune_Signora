# ADR-0013: Company Intelligence Provider Strategy

**Status:** Accepted

## Context

"Multi-provider intelligence" is explicit product scope. Provider Platform ([04-modules.md](../04-modules.md)) needs a ratified initial set of data providers covering distinct intelligence categories, plus a documented view of future candidates and their specific triggers.

## Decision

Five active providers, each covering a distinct data category: **Apollo** (firmographic/contact), **CoreSignal** (bulk company/people enrichment), **BuiltWith** (technographic), **Similarweb** (web traffic/engagement), **NeverBounce** (email verification). **ZoomInfo, Bombora, Crunchbase, 6sense, PitchBook** are evaluated future candidates, not adopted now.

## Alternatives Considered

| Category | Chosen | Alternative(s) considered | Why not chosen (now) |
|---|---|---|---|
| Firmographic/contact | Apollo | ZoomInfo | ZoomInfo has a stronger enterprise data-depth reputation but at materially higher cost and heavier contractual commitment; Apollo covers the same category sufficiently for current stage, with ZoomInfo as a documented future upgrade path if data-quality gaps are found in production. |
| Intent data | *(none active)* | Bombora, 6sense | Deferred deliberately — Signora builds its own intent signal via Signal Engine/Buying Score Engine from observation-derived events; adding third-party intent data now, before that in-house model's gaps are empirically known, risks conflating "we need better data" with "we need better modeling." Revisit once Buying Score Engine's model formally calls for external intent as an input (see [17-future-recommendations.md](../17-future-recommendations.md)). |
| Company/funding data | *(none active)* | Crunchbase, PitchBook | Both overlap significantly with capability Signora is building in-house (Business Event Engine's funding-round detection from Apollo/CoreSignal-sourced data); adding either now would be paying for a data category Signora may already adequately derive, not filling a genuine gap. Revisit if in-house detection proves insufficient for funding-event coverage/accuracy. |
| Deliverability | NeverBounce | (category-specific, few strong alternatives at this scale) | NeverBounce was judged sufficient on accuracy/cost for the current stage; no compelling alternative displaced it. |

## Tradeoffs

**We gain:** five genuinely distinct data categories covered at launch, avoiding both data gaps and redundant spend on overlapping vendors; a clear, evidence-based (not speculative) path to each future candidate.

**We give up:** ZoomInfo's/PitchBook's greater data depth in their respective categories — accepted for now given cost and the availability of a documented upgrade path if gaps are found.

## Risks

Provider ToS/rate-limit changes are an ongoing operational risk inherent to any multi-provider strategy — mitigated structurally by Provider Platform's per-provider quota/health tracking ([04-modules.md](../04-modules.md)), not eliminated by vendor choice.

## Migration Strategy

Every provider is an adapter behind the shared Provider Port ([13-integrations.md](../13-integrations.md)); adding, replacing, or dropping any single provider (including the future candidates above, once triggered) requires no change to Provider Normalization, Knowledge Graph, or any downstream module.

## Consequences

- Provider Platform's registry is configured with these five providers at launch, each with independent credentials, quota, and scheduling configuration.
- Future-candidate evaluation triggers are documented in [13-integrations.md](../13-integrations.md) and [17-future-recommendations.md](../17-future-recommendations.md), so "should we add Bombora" has a pre-agreed answer rather than being re-litigated ad hoc.
