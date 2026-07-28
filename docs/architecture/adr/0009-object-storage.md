# ADR-0009: Object Storage — MinIO / AWS S3

**Status:** Accepted

## Context

Signora needs blob storage for artifacts that don't belong in PostgreSQL: raw provider payload archives (Provider Platform, for replay/debugging), AI research artifact attachments, exported reports, and similar unstructured content. Per Principle 15, object storage is bought commodity infrastructure, not built.

## Decision

**MinIO** (S3-compatible) for local development and self-hosted parity; **AWS S3** in production.

## Alternatives Considered

| Alternative | Why not chosen |
|---|---|
| **Google Cloud Storage / Azure Blob Storage** | Comparable capability, but the ratified cloud provider is AWS ([ADR-0022](0022-devops-infrastructure-and-deployment-topology.md)); using a different provider's storage would add unnecessary cross-cloud networking/latency/billing complexity for no compensating benefit. |
| **PostgreSQL large objects / `bytea`** | Would avoid a second technology, but blob storage in the primary transactional database directly conflicts with keeping PostgreSQL free for pipeline-critical writes and RLS-scoped queries ([12-scalability.md](../12-scalability.md)) — the same rationale that ruled out PostgreSQL-as-cache in [ADR-0007](0007-caching-layer.md) applies here even more strongly given blob sizes. |
| **A self-hosted-only approach with no S3-compatible abstraction (MinIO everywhere, including production)** | Rejected because it would mean operating and scaling blob storage ourselves in production instead of using AWS's managed, effectively-unlimited-scale S3 — directly against Principle 15 (buy commodity infrastructure). |

## Tradeoffs

**We gain:** using the S3 API as the common interface across local development (MinIO) and production (S3) means the same client code and adapter work unchanged in both environments — no environment-specific storage code path. AWS S3 in production gives effectively unlimited, fully-managed scale with no operational burden.

**We give up:** nothing material — this is a low-risk, high-consensus category where "buy the commodity, use the S3 API as the portable interface" is close to an industry default, not a contrarian choice.

## Risks

Low. The main risk is data-residency requirements for specific enterprise customers ([16-architecture-risks.md](../16-architecture-risks.md) R-02), addressed at the AWS region/bucket-policy level, not by changing the storage technology itself.

## Migration Strategy

Because both MinIO and S3 speak the same S3 API, and object storage access is isolated behind `backend/platform/bought_infra_adapters/` ([15-project-structure.md](../15-project-structure.md)), migrating to another S3-compatible provider (e.g., Cloudflare R2, Backblaze B2) would require only reconfiguring the adapter's endpoint/credentials, not application-code changes.

## Consequences

- All blob storage access goes through a single S3-compatible client abstraction, never a provider-specific SDK feature that isn't S3-API-compatible.
- Blob object keys are `workspace_id`-prefixed and access-controlled at the application layer (S3 itself has no RLS-equivalent) — object storage access is only ever performed by already-workspace-scoped application code, never exposed directly to clients without a signed, scoped URL.
- Docker Compose local development runs MinIO as a service, giving developers full S3-API parity without an AWS account.
