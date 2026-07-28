# ADR-0018: Monitoring & Observability — OpenTelemetry + Grafana + Sentry

**Status:** Accepted

## Context

The async, event-driven pipeline ([07-data-flow.md](../07-data-flow.md)) spans many modules and ARQ workers; tracing a single `correlation_id` end-to-end and monitoring per-stage latency/throughput ([12-scalability.md](../12-scalability.md)) is essential and was left largely unspecified in v1.

## Decision

**OpenTelemetry** for instrumentation (traces, metrics, logs) across FastAPI and ARQ. **Grafana** for dashboards/visualization. **Sentry** for error tracking/exception monitoring.

## Alternatives Considered

| Alternative | Why not chosen |
|---|---|
| **Datadog (all-in-one APM)** | Excellent, mature, all-in-one platform, but proprietary instrumentation and materially higher cost at scale; OpenTelemetry's vendor-neutral instrumentation standard avoids locking trace/metric instrumentation code to a specific backend, while Grafana (open-source/self-hostable or Grafana Cloud) provides comparable visualization without the lock-in. |
| **New Relic** | Similar tradeoff to Datadog — capable, but proprietary and costly relative to an OpenTelemetry-native approach. |
| **Self-built dashboards on raw Prometheus without Grafana** | Would avoid one dependency, but Grafana's dashboarding/alerting maturity is exactly the kind of commodity capability Principle 15 says to buy/adopt rather than build. |
| **Sentry replaced by generic APM error tracking (e.g., folded into Datadog)** | Sentry's error-tracking-specific UX (issue grouping, release tracking, source-map-aware stack traces for the Next.js frontend, [ADR-0021](0021-frontend-application-stack.md)) is materially better purpose-built than a generic APM's error view; kept as a distinct, best-of-breed tool alongside OpenTelemetry/Grafana rather than folded into one platform. |

## Tradeoffs

**We gain:** vendor-neutral instrumentation (OpenTelemetry) that can be redirected to any compatible backend without re-instrumenting code, mature dashboarding (Grafana), and best-of-breed error tracking (Sentry) across both backend and frontend.

**We give up:** the single-pane-of-glass convenience of an all-in-one platform like Datadog — accepted in favor of avoiding both proprietary instrumentation lock-in and Datadog-scale cost.

## Risks

Operating three separate tools (OpenTelemetry collector, Grafana, Sentry) instead of one platform is more moving parts to configure and maintain than a single bought APM — mitigated by OpenTelemetry Collector's standard configuration and Grafana Cloud/Sentry's managed-hosting options reducing self-hosted operational burden if needed.

## Migration Strategy

Because OpenTelemetry is vendor-neutral, switching the trace/metrics *backend* (e.g., to Datadog or another APM) later would require only reconfiguring the OpenTelemetry Collector's exporter, not re-instrumenting application code — this portability is the specific reason OpenTelemetry was chosen over instrumenting directly against a proprietary SDK.

## Consequences

- Every FastAPI request and ARQ job is instrumented with OpenTelemetry, propagating `workspace_id` and `correlation_id`/`causation_id` ([06-events.md](../06-events.md), [07-data-flow.md](../07-data-flow.md)) as span attributes.
- Grafana dashboards are the primary tool for the scaling triggers defined in [12-scalability.md](../12-scalability.md) (queue depth, per-stage latency).
- Sentry captures unhandled exceptions across both `backend/` and `frontend/`, linked to release versions for regression tracking.
