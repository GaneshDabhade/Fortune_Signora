# ADR-0020: Feature Flags — Flagsmith

**Status:** Accepted

## Context

Progressive rollout and experimentation infrastructure is bought commodity infrastructure per Principle 15, needed across both `backend/` (gating new pipeline behavior per workspace) and `frontend/` (gating UI features).

## Decision

**Flagsmith** for feature flag management.

## Alternatives Considered

| Alternative | Why not chosen |
|---|---|
| **LaunchDarkly** | The category leader with the strongest enterprise track record, but materially higher cost at scale than Flagsmith's self-hostable open-source option, with no clear capability gap for Signora's needs (workspace-scoped flag targeting, percentage rollouts, kill switches). |
| **Unleash** | A credible open-source alternative with a similar self-hosting story to Flagsmith; Flagsmith was preferred for its combined feature-flag-and-remote-config feature set and slightly broader multi-language SDK coverage matching Signora's Python backend + TypeScript frontend split. |
| **Hand-rolled flags (database-backed boolean columns)** | Rejected by Principle 15 — flag targeting rules, percentage rollouts, and audit history are a solved problem not worth re-implementing, and a hand-rolled version would lack the operational tooling (instant flag toggling without a deploy) that is the entire point of adopting a flag system. |

## Tradeoffs

**We gain:** self-hostable option (cost/data-residency flexibility), workspace-scoped flag targeting matching Signora's tenancy model, and SDK coverage across both the Python backend and TypeScript frontend.

**We give up:** LaunchDarkly's longer enterprise track record — acceptable given no specific capability gap was identified and cost/self-hosting flexibility was judged more valuable at this stage.

## Risks

[16-architecture-risks.md](../16-architecture-risks.md) R-11 (younger-project vendor risk) applies; mitigated by the self-hostable open-source option as an exit path.

## Migration Strategy

Flag evaluation is accessed through a thin internal interface in both `backend/platform/bought_infra_adapters/` and the frontend's equivalent client wrapper; a migration to LaunchDarkly or Unleash would touch only those integration points, not call sites throughout the codebase.

## Consequences

- Feature flag targeting rules are workspace-scoped by default, consistent with [11-tenancy.md](../11-tenancy.md)'s tenancy model, even though flags themselves are not RLS-enforced tenant data (they are Signora's own operational configuration, not customer data).
- Both backend pipeline behavior gating and frontend UI feature gating use the same Flagsmith instance and SDK family for consistency.
