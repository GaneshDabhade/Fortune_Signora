# ADR-0022: DevOps, Infrastructure & Deployment Topology

**Status:** Accepted · **Operating mechanism amended by [ADR-0027](0027-local-first-development.md) (2026-07-29):** GitHub Actions remains the ratified CI/CD platform *for when CI returns*, but **no CI is operating today** — all verification is local. The production topology below is unaffected and remains the target M14.5 provisions against.

## Context

[03-system-architecture.md](../03-system-architecture.md) defines a small number of horizontally scalable process types (API, workers). This ADR ratifies the concrete infrastructure realizing that shape: local development, CI/CD, and production hosting.

## Decision

**Docker** + **Docker Compose** for local development. **GitHub Actions** for CI/CD. **Traefik** as edge router/reverse proxy. **AWS** as the cloud provider, with **ECS** for compute, **RDS for PostgreSQL** as the managed database, **ElastiCache for Redis** as the managed cache/queue broker, **S3** for production object storage, **CloudWatch** for infrastructure-level log/metric aggregation, and **AWS Secrets Manager** for credential storage.

## Alternatives Considered

| Layer | Alternative | Why not chosen |
|---|---|---|
| Cloud provider | GCP, Azure | AWS was judged to have the deepest managed-service maturity for the specific combination Signora needs (RDS for PostgreSQL with RLS support, ElastiCache, mature ECS/Fargate container orchestration) and the broadest ecosystem for the enterprise customers this product targets, who commonly already have AWS relationships/commitments. |
| Compute | Kubernetes (EKS) | Kubernetes offers more portability and a richer ecosystem, but at Signora's process-topology simplicity (a handful of stateless service types, per [03-system-architecture.md](../03-system-architecture.md)) ECS's materially lower operational complexity was judged the better fit — directly consistent with Principle 1's preference for operational simplicity over infrastructure sophistication not yet justified by need. |
| Compute | Bare EC2 + custom orchestration | Would maximize control, but reintroduces orchestration/scaling/deployment concerns ECS already solves — against Principle 15's spirit even though ECS itself is AWS-native rather than a discrete "vendor" in the build-vs-buy table. |
| CI/CD | CircleCI, GitLab CI | GitHub Actions was chosen for tight integration with the GitHub-hosted repository (assumed source-control platform) and to avoid a second vendor relationship purely for CI, when GitHub Actions' capability is sufficient for Signora's build/test/deploy pipeline needs. |
| Edge routing | AWS Application Load Balancer alone, Nginx | Traefik's dynamic configuration (service discovery-aware routing, automatic TLS via Let's Encrypt) fits a containerized, horizontally-scaled ECS deployment more cleanly than hand-maintained Nginx configuration, while still working alongside an ALB at the AWS network-load-balancing layer where needed. |
| Secrets | HashiCorp Vault | Vault is more powerful and cloud-agnostic, but adds a service to operate; AWS Secrets Manager's native IAM integration and zero-additional-infrastructure operation were judged sufficient given AWS is already the ratified provider, with no cross-cloud portability requirement identified. |

## Tradeoffs

**We gain:** a fully-managed data/cache layer (RDS, ElastiCache) requiring no in-house database/Redis operations expertise, ECS's lower operational complexity than Kubernetes for Signora's actual process topology, and native AWS IAM-integrated secrets management.

**We give up:** Kubernetes' broader ecosystem/portability and Vault's cloud-agnostic secrets model — both accepted as reasonable simplicity tradeoffs given AWS is the committed provider and the process topology is genuinely simple (Principle 1).

## Risks

Single-cloud-provider dependency (AWS) — acceptable given no multi-cloud requirement has been identified, but noted alongside [16-architecture-risks.md](../16-architecture-risks.md) R-02 (multi-region/data-residency), since region strategy (not multi-cloud) is the more likely near-term driver of infrastructure evolution.

## Migration Strategy

- **ECS → Kubernetes**: containers are already Docker-based; a migration would primarily involve rewriting orchestration manifests, not application code, since ECS task definitions and Kubernetes deployments both consume the same container images.
- **RDS/ElastiCache → self-managed or another cloud's managed equivalent**: PostgreSQL and Redis are both standard, portable engines; migration is a data-migration exercise, not an application rewrite, provided connection configuration is externalized (which it is, via AWS Secrets Manager-sourced configuration, never hardcoded).

## Consequences

- `infra/` holds Docker Compose (local) and Terraform/IaC (AWS) definitions — infrastructure is code-reviewed like application code.
- CI (GitHub Actions) runs Ruff, MyPy, ESLint, Prettier, import-linter, Pytest, Vitest, and Playwright ([ADR-0023](0023-testing-strategy.md), [ADR-0024](0024-code-quality-and-static-analysis.md)) on every PR before merge.
- All production secrets (provider/AI vendor/integration credentials, database credentials) are sourced from AWS Secrets Manager, never committed or hardcoded, per [10-security.md](../10-security.md).

---

## As Built — Local Production Stack (M1.3A)

The cloud topology below is realised first as a **local production stack**: the same images, the same identities, the same startup ordering, running under Docker Compose (`infra/docker-compose.prod.yml`). This is not a development convenience — it is where every *application*-level deployment question is answered before AWS is introduced, so that a failure in M1.3B has exactly one remaining suspect.

### Images

| Image | Base | User | Contents |
|---|---|---|---|
| backend | `python:3.13-slim` | uid 1000, non-root | Virtualenv + source. One image, three entry points (API, worker, relay, migration runner) — they share every dependency and differ only in command. |
| frontend | `node:22-slim` | `node` (uid 1000) | Next.js standalone output only — no build toolchain, no dev dependencies. |

Both are multi-stage: the builder holds the compiler and package manager, the runtime holds neither. **No secret is baked into either image, and none can be** — every value arrives from the environment at start, so the image is byte-identical across environments and what differs is only what is handed to it.

### Startup ordering

```
postgres ──┐
           ├──► migrate (runs to completion) ──► api ──► frontend
redis ─────┘                                 ├──► worker
                                             └──► relay
```

`migrate` is a **discrete step that exits**, and every database-touching service waits on `service_completed_successfully`. No process ever starts against a half-migrated schema, and no running service holds the ability to apply a migration.

### Identities in the running stack

Each process connects under its own least-privileged role — verified from inside the containers, not assumed from configuration:

| Process | Role |
|---|---|
| `migrate` | owner (`signora`) — the only service given the migration credential |
| `api`, `worker` | `signora_app` |
| `relay` | `signora_relay` (for the outbox) |
| `frontend` | `signora_auth` |

### Migration runner

`apps/migrate/main.py` provides two guarantees `alembic upgrade head` does not:

- **Concurrency safety.** A session-scoped PostgreSQL advisory lock serialises parallel invocations. Deployments start replicas simultaneously and a rollback may start a new task while an old one is draining; two Alembic processes on one database produce partially applied migrations and a version table that agrees with neither. Verified with four simultaneous runners against an empty schema: one proceeded, three waited, the schema reached head exactly once.
- **Identity enforcement.** It refuses to run under a runtime role, exiting non-zero with a message naming the fix. A mistake in a task definition fails at the migration step rather than silently granting the application role DDL.

### Health and readiness

- `/health` — liveness. Does not touch the database, so a database blip never causes an orchestrator to restart a healthy process.
- `/ready` — readiness, covering database *and* authentication. **Returns 503 when not ready**, not 200 with bad news in the body: every orchestrator that will run this routes on the status code and never reads the body, so a degraded API answering 200 keeps receiving traffic it cannot serve.
- Frontend `/api/health` — Better Auth connectivity, signing-key pair match, JWT configuration, OAuth configuration.

### Disaster recovery

`infra/disaster-recovery.sh` restarts PostgreSQL, Redis, the API, workers, and the relay in turn, asserting before and after each that nothing is lost: unrelayed outbox rows, dead letters, the idempotency ledger, acknowledged writes and their events, authentication state, tenant isolation, and per-entity event ordering. Redis is treated as transport rather than a system of record — anything lost from the queue is still in the outbox and is re-relayed, which the restart proves rather than assumes.

### Platform Smoke Test (M1.4)

`make smoke` verifies the whole stack in one command: build → startup → migrations → identities → image hygiene → health → readiness → authentication → JWT verification → authorization → RLS → event bus → relay → workers → Security Invariants → teardown. Sixteen stages, each failing fast and naming itself; ~45 seconds warm.

**Required before every milestone and every release, and the first step of incident triage.** It runs in CI on every merge to `main` and on pull requests.

Two design points:

- **The Security Invariants run last.** The suite truncates every table between tests, so anything asserted after it would be asserted against an empty database — which is how the disaster-recovery script's ordering checks originally passed vacuously.
- **Every stage was verified to fail when its guarantee was deliberately removed** — a 200 from `/ready` with the database down, a relay that dies on a transient error, an unpinned JWT algorithm, the API connecting as the owner, a secret baked into an image. A stage that has never failed may be asserting nothing.

With cloud infrastructure deferred to M14.5, this command is also the standing proof that the Infrastructure Contract still holds. Across the pipeline milestones it is the only thing that will notice the application has stopped being deployable.
