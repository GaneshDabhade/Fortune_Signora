# ADR-0016: Billing — Stripe

**Status:** Accepted

## Context

Per Principle 14–15, billing is bought commodity infrastructure carrying significant compliance liability (PCI) if self-built.

## Decision

**Stripe** for subscription billing, invoicing, and payment processing.

## Alternatives Considered

| Alternative | Why not chosen |
|---|---|
| **Chargebee / Recurly (billing-specific platforms)** | Strong subscription-management feature sets, but Stripe's combination of payments infrastructure *and* billing/subscription primitives in one platform avoids integrating two separate vendors (a payments processor plus a billing layer on top) for no clear benefit at Signora's scale. |
| **Roll our own billing on top of a raw payments processor** | Explicitly rejected by Principle 14 — billing/subscription logic (proration, dunning, tax handling) is a solved, compliance-sensitive problem with no differentiation value to Signora. |
| **Paddle (merchant-of-record model)** | Paddle's merchant-of-record approach simplifies global tax compliance, which is a genuine advantage, but was judged less critical than Stripe's broader ecosystem maturity and the team's ability to control the checkout/billing experience directly — worth revisiting if international tax complexity becomes a significant operational burden. |

## Tradeoffs

**We gain:** a single, mature, widely-integrated payments-and-billing platform with strong ecosystem support (accounting integrations, tax add-ons) and no need to separately integrate a payments processor and a billing layer.

**We give up:** Paddle's merchant-of-record tax-compliance simplification — accepted for now, revisit if international expansion makes tax handling a significant burden.

## Risks

Low — Stripe is category-leading and low-risk from a vendor-viability perspective (the inverse of [16-architecture-risks.md](../16-architecture-risks.md) R-11's concern).

## Migration Strategy

Billing/subscription logic is accessed through `backend/platform/bought_infra_adapters/`, isolating Stripe-specific API calls from Workspace & Tenancy's subscription-state model; a migration to another billing vendor would touch only that adapter.

## Consequences

- Workspace & Tenancy tracks subscription/plan state as a reference to Stripe's subscription object, not as duplicated billing logic — Stripe remains the system of record for billing state.
- Webhook-driven subscription state changes (upgrades, downgrades, payment failures) flow into Workspace & Tenancy via the Integration Abstraction Layer's inbound webhook handling pattern.
