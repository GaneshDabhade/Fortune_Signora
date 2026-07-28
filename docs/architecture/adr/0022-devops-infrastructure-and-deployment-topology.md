# ADR-0022: DevOps, Infrastructure & Deployment Topology

**Status:** Accepted

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
