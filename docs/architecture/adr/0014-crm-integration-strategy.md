# ADR-0014: CRM Integration Strategy

**Status:** Accepted

## Context

Sales teams are heterogeneous in CRM choice. Signora's value is diminished if it only serves one CRM ecosystem, but each additional CRM adapter adds real integration and support-surface cost.

## Decision

Four active CRM integrations at launch: **Salesforce, HubSpot, Pipedrive, Zoho**. **Microsoft Dynamics 365** is a ratified future candidate, deferred to enterprise pipeline demand.

## Alternatives Considered

| Alternative | Why not chosen (now) |
|---|---|
| **Salesforce-only at launch** | Would minimize initial integration cost, but Salesforce does not dominate the SMB/mid-market segment (HubSpot and Pipedrive are common there), and launching CRM-exclusive would materially narrow addressable market at exactly the stage market breadth matters most. |
| **Build a generic CRM abstraction requiring customer-side mapping configuration instead of named adapters** | Would reduce Signora's own adapter-maintenance burden, but shifts integration complexity onto customers, working against ease-of-adoption — direct, named adapters behind the Integration Abstraction Layer keep the burden on Signora's engineering, which is the point of Principle 11. |
| **Dynamics 365 at launch** | Real enterprise demand exists for Dynamics, but it was judged lower-priority than covering the broader SMB/mid-market CRM landscape (HubSpot/Pipedrive/Zoho) at initial launch; adding it is a scoped, low-risk future addition given the Integration Abstraction Layer's adapter model. |

## Tradeoffs

**We gain:** broad initial market applicability across CRM ecosystems without waiting for a fifth-CRM launch blocker.

**We give up:** deeper initial investment in any single CRM's advanced feature surface (e.g., Salesforce's custom-object ecosystem) in favor of breadth — each adapter targets the common integration surface (opportunity/activity sync) rather than CRM-specific advanced customization, which can deepen per-CRM over time based on customer demand.

## Risks

CRM vendor API changes/deprecations are an ongoing maintenance cost proportional to the number of adapters — accepted as a direct consequence of the four-CRM breadth decision, mitigated by each adapter's isolation behind the shared Integration Port ([13-integrations.md](../13-integrations.md)).

## Migration Strategy

Each CRM is an adapter behind the Integration Abstraction Layer; adding Dynamics 365 (or any future CRM) requires no change to Revenue Intelligence Platform's or any other module's domain logic — only a new adapter implementation.

## Consequences

- Revenue Intelligence Platform's outbound sync logic is written against the Integration Port, never against a specific CRM's API shape.
- Dynamics 365's addition is tracked as a demand-triggered, not calendar-triggered, roadmap item ([17-future-recommendations.md](../17-future-recommendations.md)).
