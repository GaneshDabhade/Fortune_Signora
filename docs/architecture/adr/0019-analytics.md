# ADR-0019: Analytics — PostHog

**Status:** Accepted

## Context

Product/usage analytics (feature adoption, funnel analysis, workspace-level engagement with recommendations) is bought commodity infrastructure per Principle 15, distinct from Signora's own domain analytics (Revenue Intelligence Platform's reporting, which is a built, competitive-advantage capability, not this decision's concern).

## Decision

**PostHog** for product analytics.

## Alternatives Considered

| Alternative | Why not chosen |
|---|---|
| **Amplitude / Mixpanel** | Mature, capable product-analytics platforms, but both are hosted-only with usage-based pricing that scales less favorably than PostHog's self-hostable option at a hundreds-of-thousands-of-workspaces target; PostHog's additional bundled capability (session replay, feature-flag-adjacent tooling, though Flagsmith remains the ratified feature-flag choice — [ADR-0020](0020-feature-flags.md)) was a secondary but real factor. |
| **Building in-house analytics on the existing event bus** | Rejected — Signora's Internal Event Bus ([06-events.md](../06-events.md)) carries *domain* events (business events, signals, opportunities), not product-usage telemetry; repurposing it for product analytics would conflate two different concerns with different retention, PII, and query-pattern needs, and product analytics itself is explicitly commodity per Principle 15. |

## Tradeoffs

**We gain:** self-hostable option (cost/data-residency flexibility, relevant to [16-architecture-risks.md](../16-architecture-risks.md) R-02), a modern feature set, and clean separation from Signora's own domain event bus.

**We give up:** Amplitude's/Mixpanel's longer track record at extreme analytics scale — acceptable, since product-usage analytics volume is a different (typically much larger but much lower-value-per-event) profile than pipeline domain events, and PostHog is proven at comparable scale.

## Risks

Low — tracked generally under [16-architecture-risks.md](../16-architecture-risks.md) R-11, though PostHog has a substantial enough market position to be a lower-severity instance of that risk than some other choices in this stack.

## Migration Strategy

PostHog's client SDK is integrated at the frontend/API boundary, not woven into domain logic; a migration to another analytics vendor would touch only that integration point.

## Consequences

- Product-usage analytics (PostHog) and domain pipeline events (Internal Event Bus, [06-events.md](../06-events.md)) remain two distinct, non-overlapping systems with different purposes — never conflated.
- PostHog data is treated as containing user-behavior PII and is subject to the same pending data-classification/retention policy work as the rest of the system ([16-architecture-risks.md](../16-architecture-risks.md) R-04).
