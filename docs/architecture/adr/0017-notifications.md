# ADR-0017: Notifications — Novu

**Status:** Accepted

## Context

Recommendation Engine and other modules need to deliver notifications (new recommendation, opportunity stage change, etc.) across multiple channels (in-app, email, Slack, Teams) without each module hand-rolling per-channel delivery logic.

## Decision

**Novu** as the notification infrastructure layer — a cross-channel notification orchestration platform, open-source/self-hostable.

## Alternatives Considered

| Alternative | Why not chosen |
|---|---|
| **Knock / Courier (proprietary notification-infrastructure SaaS)** | Comparable feature sets, but both are closed-source, hosted-only vendors; Novu's open-source, self-hostable option gives an exit path if pricing or roadmap direction ever becomes unfavorable, without giving up a managed-cloud option today. |
| **Hand-rolled per-channel delivery in each module** | Explicitly rejected by Principle 15 — notification orchestration (templating, channel fallback, user preference management, delivery tracking) is commodity infrastructure with no differentiation value, and duplicating it per module would violate the DRY-across-modules spirit of [04-modules.md](../04-modules.md)'s boundary discipline even though each module legitimately triggers notifications. |

## Tradeoffs

**We gain:** a single, channel-agnostic notification trigger interface used by every module (Recommendation Engine, Opportunity Engine, etc.) that needs to notify a user, with per-user channel-preference management handled centrally rather than duplicated.

**We give up:** the deeper channel-specific customization a hand-rolled integration per channel might offer — acceptable, since Novu's templating covers the product's notification needs without requiring bespoke per-channel logic.

## Risks

[16-architecture-risks.md](../16-architecture-risks.md) R-11 (younger-project vendor risk) applies; mitigated by Novu's self-hostable open-source option as a documented exit path distinct from most closed-source alternatives.

## Migration Strategy

Novu is accessed through `backend/platform/bought_infra_adapters/`; any module triggering a notification calls a single internal interface, never Novu's SDK directly — a migration to Knock/Courier or a self-hosted Novu instance would touch only that adapter.

## Consequences

- Slack and Microsoft Teams ([ADR-0015](0015-communication-email-and-calendar-integrations.md)) are configured as Novu delivery channels, distinct from and downstream of the data-source integration use of those same platforms.
- Every module that needs to notify a user does so via one shared internal trigger interface, never per-channel bespoke code.
