# 16 — Architecture Risks

> Status: **Living document — Architectural Constitution — RATIFIED**
> Audience: All engineers, EMs, and technical stakeholders at Signora
> New in **v2**.

## Purpose

This is the Architecture Review Board's risk register: every material architectural risk identified while ratifying the technology stack and module boundaries, whether newly introduced by a decision, inherited from the original design, or simply not yet resolvable without input this Board does not have standing to invent (legal, compliance, GTM). Each risk has an owner-to-be-assigned, a severity/likelihood assessment, and a concrete mitigation or resolution path — this document exists specifically so open items are tracked, not silently forgotten.

## Responsibilities

- Enumerate every risk the Board identified during this revision.
- Assess severity and likelihood honestly, including risks introduced by the Board's own decisions.
- Give each risk a concrete next step, not just a description of the problem.
- Serve as the input to quarterly architecture review.

## Risk Register

### R-01 — AI Vendor Cost Exposure Without Budget Governance

**Category:** Cost / Operational · **Severity:** High · **Likelihood:** High

Signora runs three active AI vendors (Claude, OpenAI, Gemini) across two modules with very different cost profiles (AI Research Engine's multi-step agentic calls can be materially more expensive per invocation than AI Reasoning Engine's single structured call). No per-workspace or platform-wide cost ceiling, alerting, or budget-governance mechanism is defined.

**Impact if unmitigated:** A pathological entity (e.g., a noisy account generating excessive signals) or a bug in trigger logic could drive unbounded AI spend before anyone notices.

**Mitigation:** Define per-workspace and platform-wide AI spend budgets and alerting thresholds (via OpenTelemetry cost metrics, see [ADR-0018](adr/0018-monitoring-and-observability.md)) before AI Research Engine is enabled broadly. Owner: TBD.

---

### R-02 — Single-Region Deployment vs. Enterprise Data Residency

**Category:** Compliance / Enterprise Readiness · **Severity:** Medium · **Likelihood:** Medium (rises with enterprise deal count)

The ratified AWS topology ([ADR-0022](adr/0022-devops-infrastructure-and-deployment-topology.md)) is single-region by default. "Enterprise customers" is explicit project scope, and enterprise buyers frequently require data residency guarantees (EU-resident data, etc.) that a single-region deployment cannot satisfy.

**Impact if unmitigated:** Lost enterprise deals, or an ad hoc, unplanned multi-region migration under sales pressure.

**Mitigation:** Track as a deliberate future-state design (see [17-future-recommendations.md](17-future-recommendations.md)); do not solve pre-emptively, but ensure Workspace & Tenancy's schema does not make region-pinning structurally difficult to retrofit (e.g., avoid assumptions that break if `workspace_id` maps to a specific physical region later). Owner: TBD.

---

### R-03 — RLS Query Performance Not Load-Tested at Target Scale

**Category:** Performance · **Severity:** Medium · **Likelihood:** Medium

The stated scale target is millions of companies and hundreds of thousands of workspaces. PostgreSQL 17's RLS planner improvements ([ADR-0006](adr/0006-data-platform-primary-database-and-multi-tenancy.md)) reduce but do not eliminate RLS overhead on large, heavily-indexed tables (Observation is the leading concern). No load test at target scale exists yet.

**Impact if unmitigated:** Undetected performance cliff discovered in production rather than in testing.

**Mitigation:** Build a synthetic load-test harness simulating target-scale data volume before general availability; use results to validate or revise the partitioning plan in [12-scalability.md](12-scalability.md). Owner: TBD.

---

### R-04 — PII Classification, Retention, and Workspace Lifecycle Policy Undefined

**Category:** Compliance / Legal · **Severity:** High · **Likelihood:** High (certain to matter — Knowledge Graph stores personal data about individuals by design)

No formal PII classification, retention, or right-to-erasure policy exists, and workspace creation/suspension/deletion flows (including data disposition on offboarding) are undefined. This spans [10-security.md](10-security.md) and [11-tenancy.md](11-tenancy.md).

**Impact if unmitigated:** GDPR/CCPA (or equivalent) non-compliance risk; inability to honor a data-subject erasure request cleanly across thirteen modules' worth of derived data (observations, events, signals, scores, reasoning results all trace back to a person/entity).

**Mitigation:** This requires legal/compliance input the Review Board does not have standing to invent — escalate explicitly rather than resolve unilaterally. Once policy is set, technical design should address cascade deletion/anonymization across the full derivation chain (an entity's observations → events → signals → scores → opportunities → reasoning → recommendations). Owner: TBD (Legal + Engineering).

---

### R-05 — AI Prompt Data-Classification Policy Undefined

**Category:** Security / Compliance · **Severity:** High · **Likelihood:** Medium

No policy defines which categories of workspace data are permitted to be included in prompts sent to Claude/OpenAI/Gemini. This matters more once a workspace holds regulated data categories. See [10-security.md](10-security.md), [14-ai-architecture.md](14-ai-architecture.md).

**Impact if unmitigated:** A regulated customer's data could be sent to a third-party AI vendor in a way that violates a contractual or regulatory commitment before anyone notices.

**Mitigation:** Define an explicit data-classification taxonomy and an allowlist/blocklist enforced in AI Research Engine's and AI Reasoning Engine's context-assembly step, before onboarding customers with regulated data categories. Owner: TBD.

---

### R-06 — Cross-Workspace Admin/Support Access Model Undefined

**Category:** Security · **Severity:** Medium · **Likelihood:** High (support will need this early)

No formal model exists for how platform admin/customer-support tooling gets narrowly-scoped, audited, cross-workspace access without becoming a routine RLS-bypass path. See [11-tenancy.md](11-tenancy.md).

**Impact if unmitigated:** Ad hoc, under-audited admin access patterns get built reactively once support needs them, likely with weaker controls than a deliberately designed model would have.

**Mitigation:** Design a time-boxed, audit-logged elevated-access mechanism before any customer-facing support tooling is built. Owner: TBD.

---

### R-07 — API and Pipeline Latency SLOs Undefined

**Category:** Operational · **Severity:** Low · **Likelihood:** High

No P95/P99 latency targets exist for the API tier or for pipeline stage-to-stage latency (provider ingestion to recommendation). See [12-scalability.md](12-scalability.md).

**Impact if unmitigated:** No objective basis for autoscaling policy, alerting thresholds, or "is this actually slow" conversations.

**Mitigation:** Define initial SLOs from early production telemetry (OpenTelemetry/Grafana) rather than guessing pre-launch; revisit quarterly. Owner: TBD.

---

### R-08 — Meilisearch and pgvector Not Validated at Target Scale

**Category:** Performance · **Severity:** Medium · **Likelihood:** Low-Medium

Neither Meilisearch (full-text/faceted search) nor pgvector (vector search) has been load-tested against Signora's target scale (millions of companies, hundreds of thousands of workspaces). Both were selected on ecosystem/operational-simplicity grounds ([ADR-0008](adr/0008-search-and-vector-retrieval.md)) with an explicit acknowledgment that neither has the largest-scale track record of its category leader (Elasticsearch, dedicated vector DBs).

**Impact if unmitigated:** A late-discovered scale ceiling in either would force a disruptive mid-flight migration.

**Mitigation:** Load-test both against synthetic target-scale data before general availability; the fallback migration paths (Elasticsearch, a dedicated vector DB) are documented in [ADR-0008](adr/0008-search-and-vector-retrieval.md) precisely so this risk has a known exit if triggered. Owner: TBD.

---

### R-09 — AI Research Engine Timeout Value Undefined

**Category:** Product / Operational · **Severity:** Low · **Likelihood:** High

The exact timeout AI Reasoning Engine waits for AI Research Engine before proceeding without it (see [14-ai-architecture.md](14-ai-architecture.md)) is not yet set.

**Impact if unmitigated:** An arbitrary or untested default could either (a) make every reasoning call slow, waiting on research that rarely finishes in time, or (b) rarely benefit from research at all.

**Mitigation:** Set an initial value from early production research-completion-time telemetry; tune from there. Owner: TBD.

---

### R-10 — No AI Evaluation Methodology

**Category:** Product Quality · **Severity:** High · **Likelihood:** High

No golden test sets, human-review sampling process, or regression testing exists for AI Research Engine or AI Reasoning Engine output quality. See [14-ai-architecture.md](14-ai-architecture.md).

**Impact if unmitigated:** Prompt or model changes ship without any objective quality signal; regressions are discovered by customers, not by evaluation.

**Mitigation:** This is the single highest-leverage AI-quality investment available and should be built early — see [17-future-recommendations.md](17-future-recommendations.md). Owner: TBD.

---

### R-11 — Vendor Concentration on Less-Mainstream Infrastructure Choices

**Category:** Operational / Vendor Risk · **Severity:** Low-Medium · **Likelihood:** Low

Several ratified choices (Better Auth, Meilisearch, ARQ, Novu, Flagsmith) are smaller, younger projects/companies than their more established alternatives (Auth0/Clerk, Elasticsearch, Celery, a bundled notification suite, LaunchDarkly). Each was selected deliberately on merits documented in its ADR, but smaller vendors/projects carry higher long-term-viability risk than incumbents.

**Impact if unmitigated:** A vendor's decline, acquisition, or project abandonment could force an unplanned migration.

**Mitigation:** Every such choice is deliberately kept behind an abstraction layer where the architecture calls for it (identity, AI, providers, integrations), and each ADR documents a concrete migration path. This is an accepted, monitored risk, not a mitigated-to-zero one — revisit vendor health at each quarterly architecture review. Owner: Architecture owner (standing).

---

### R-13 — Better Auth Is TypeScript-Native; The Backend Is Python

**Category:** Implementation / Blocking · **Severity:** High · **Likelihood:** Certain (already encountered) · **Status:** Open — blocks the Workspace & Tenancy HTTP layer

[ADR-0010](adr/0010-identity-and-access.md) ratifies Better Auth for authentication, describing it as "framework-native." That framing holds for the Next.js frontend ([ADR-0021](adr/0021-frontend-application-stack.md)) but not for the FastAPI backend ([ADR-0002](adr/0002-web-framework-and-api-style.md)): Better Auth is a TypeScript library with no official Python SDK. The ADR did not resolve how a Python API verifies sessions Better Auth issues.

**Impact:** The Workspace & Tenancy module's `interface/` layer cannot be built until this is settled, because every route depends on resolving an authenticated principal. Domain, application, infrastructure, and public layers are complete and tested; only the HTTP surface is blocked.

**Options to evaluate (none yet chosen):**

1. **Better Auth in Next.js issues a JWT the FastAPI backend verifies** using a shared signing key. Keeps Better Auth's ratified role intact; the backend needs only standard JWT verification and never handles credentials. Lowest coupling; requires care that token lifetime/revocation semantics stay correct.
2. **Shared session store** — Better Auth writes sessions to PostgreSQL or Redis; FastAPI reads them directly. Simple, but couples the backend to Better Auth's session schema, which is an internal detail of a third-party library and may change across versions.
3. **Reconsider the vendor for the API tier** — revisit the bundled alternatives ADR-0010 rejected (Clerk/WorkOS/Auth0), which ship first-class Python SDKs. Highest cost; would require superseding ADR-0010 and reopening its "policy ownership over turnkey speed" reasoning.

**Recommendation:** Option 1. It preserves ADR-0010's decision and its rationale, keeps credential handling out of the Python tier entirely, and is a well-understood integration pattern. Options 2 and 3 should not be adopted without an ADR superseding or amending ADR-0010.

**Mitigation:** Resolve before building any authenticated route. Owner: TBD.

---

### R-12 — Enterprise Compliance Readiness Gap (SOC 2 / Equivalent)

**Category:** Compliance / Enterprise Readiness · **Severity:** Medium · **Likelihood:** High (certain to matter — "Enterprise customers" is explicit scope)

No compliance program (SOC 2 Type II or equivalent) is in place or referenced anywhere in this architecture set. Enterprise buyers routinely require this as a purchasing gate.

**Impact if unmitigated:** Enterprise deals stall or are lost at security review.

**Mitigation:** This is a program, not a single architectural decision, but the architecture should not make it harder than necessary — the logging/observability ([ADR-0018](adr/0018-monitoring-and-observability.md)), secrets management ([ADR-0022](adr/0022-devops-infrastructure-and-deployment-topology.md)), and tenant isolation ([11-tenancy.md](11-tenancy.md)) decisions in this revision are all compatible with a future SOC 2 audit. Formal program ownership sits outside engineering alone. Owner: TBD (Leadership + Engineering).

## Design Rationale

Every risk here was surfaced honestly, including risks the Board's own decisions introduce (R-01, R-11) — a risk register that only lists inherited problems and never self-critiques its own recommendations is not trustworthy. Risks requiring non-engineering input (R-04, R-12) are marked as escalations, not silently deferred.

## Best Practices

- Review this register at every quarterly architecture review; update severity/likelihood as real data arrives.
- Assign an owner to every risk before the next review cycle — "TBD" is a starting state, not a resting state.
- Close a risk by updating its status here and linking the resolving PR/ADR, never by deleting the entry (keep the historical record).

## Anti-Patterns

- Treating an unassigned-owner risk as "not real."
- Resolving R-04 or R-05 unilaterally in code without the compliance/legal input they require.
- Adding a new architectural decision without checking whether it introduces a new entry for this register.

## Future Evolution

This register should grow and shrink as risks are resolved or newly identified — it is a living instrument, not a one-time audit output.

## Decision Summary

Thirteen material risks are tracked: three introduced or highlighted by this revision's own decisions (R-01 AI cost governance, R-03 RLS at scale, R-11 vendor concentration), and the remainder inherited open items now given explicit severity, likelihood, and mitigation ownership rather than being left as unlabeled `TODO`s. R-04, R-05, and R-12 require input beyond engineering's mandate and are explicitly flagged as escalations. R-13 was found during implementation and is the only risk currently *blocking* delivery of a module.
