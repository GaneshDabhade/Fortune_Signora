# ADR-0015: Communication, Email & Calendar Integrations

**Status:** Accepted

## Context

Recommendations need to reach sales users where they already work (chat, inbox, calendar), and email/calendar activity is itself a valuable observation source for the pipeline. This spans several related but distinct integration surfaces, bundled into one ADR because they were evaluated and ratified together as one connective-tissue decision.

## Decision

**Slack** and **Microsoft Teams** for team communication delivery. **Resend** for Signora-originated transactional email. **Gmail** and **Microsoft 365** for customer email-account integration (observation source + optional recommendation delivery). **Google Calendar** and **Outlook Calendar** for calendar integration (observation source + action scheduling).

## Alternatives Considered

| Category | Chosen | Alternative(s) considered | Why not chosen |
|---|---|---|---|
| Team communication | Slack, Teams | (a single-vendor bet on Slack only) | Rejected — Teams has substantial enterprise-market share, and given "Enterprise customers" is explicit scope, launching Teams-excluded would narrow enterprise addressability specifically where it matters most. |
| Transactional email | Resend | SendGrid, Postmark, AWS SES | SendGrid/Postmark are comparably mature, but Resend's developer experience and modern API design were judged a better fit for the team's ratified stack (React-Email-style templating aligns with the Next.js/TypeScript frontend, [ADR-0021](0021-frontend-application-stack.md)); AWS SES was considered as the "already in AWS" option but has a materially weaker developer experience and deliverability-reputation tooling out of the box. |
| Email account integration | Gmail, Microsoft 365 | (IMAP/SMTP generic integration) | A generic IMAP integration would cover more email providers, but Gmail and Microsoft 365 cover the overwhelming majority of B2B sales orgs' email infrastructure, and native OAuth-based API integration (vs. generic IMAP) gives materially better activity-signal fidelity for Observation Engine's purposes. |
| Calendar | Google Calendar, Outlook Calendar | (generic CalDAV) | Same rationale as email — native API integration over the two dominant providers outperforms a generic protocol integration for signal fidelity, and covers the same majority of the target market as the email decision above. |

## Tradeoffs

**We gain:** broad enterprise-communication-platform coverage (Slack + Teams), a modern transactional-email developer experience (Resend), and high-fidelity activity signals from the two dominant email/calendar ecosystems.

**We give up:** generic-protocol coverage (IMAP/CalDAV) of smaller or legacy email/calendar systems — accepted, since Gmail and Microsoft 365 cover the large majority of the target market, and generic-protocol support can be added later if a specific customer segment demands it.

## Risks

Each of these is a distinct OAuth grant, per-workspace, stored separately from Better Auth's sign-in credentials ([10-security.md](../10-security.md), [ADR-0010](0010-identity-and-access.md)) — the operational risk is credential-scope sprawl across six+ integration surfaces, mitigated by AWS Secrets Manager's per-credential scoping and the Integration Abstraction Layer's uniform adapter pattern.

## Migration Strategy

Each vendor is an adapter behind the Integration Abstraction Layer ([13-integrations.md](../13-integrations.md)); Novu ([ADR-0017](0017-notifications.md)) targets Slack/Teams as delivery channels without any of these integrations being aware of Novu's existence, keeping notification delivery and data-source integration cleanly separated concerns.

## Consequences

- Six distinct integration adapters (Slack, Teams, Resend, Gmail, Microsoft 365, Google Calendar, Outlook Calendar) plus the two CRM-adjacent categories from [ADR-0014](0014-crm-integration-strategy.md), all behind the same Integration Port pattern.
- Email/calendar integrations feed Observation Engine as an additional inbound signal source, distinct from and complementary to the five data providers in [ADR-0013](0013-company-intelligence-provider-strategy.md).
