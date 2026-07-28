"""Worker pool definitions.

Pools are partitioned by *cost and latency profile*, not by module, because
that is what actually needs isolating. A slow, expensive AI research task
running at the same concurrency as fast normalization work would either
starve normalization or bankrupt the AI budget — docs/architecture/12-scalability.md
calls for this partitioning from day one rather than after the divergence
is observed, since the divergence is already known.

Pools are declared here for the full pipeline even though most of their
consumers do not exist yet. A pool with no subscriptions is harmless (its
queue is simply empty), and declaring them upfront means adding a module
does not also require touching deployment configuration.
"""

import os
from dataclasses import dataclass
from typing import Final

DEFAULT_POOL_ENV_VAR: Final = "SIGNORA_WORKER_POOL"


@dataclass(frozen=True)
class WorkerPool:
    name: str
    max_jobs: int
    """Concurrent jobs per worker process. Low for AI pools to respect
    vendor rate limits and bound spend; high for I/O-bound stages."""

    job_timeout_seconds: int
    description: str


INGESTION: Final = WorkerPool(
    name="ingestion",
    max_jobs=20,
    job_timeout_seconds=300,
    description="Provider Platform, Provider Normalization — I/O-bound, high concurrency",
)

GRAPH: Final = WorkerPool(
    name="graph",
    max_jobs=10,
    job_timeout_seconds=600,
    description="Knowledge Graph, Observation Engine — entity resolution is CPU-heavier",
)

INTELLIGENCE: Final = WorkerPool(
    name="intelligence",
    max_jobs=10,
    job_timeout_seconds=300,
    description="Business Event, Signal, Buying Score, Opportunity Engines",
)

AI_REASONING: Final = WorkerPool(
    name="ai_reasoning",
    max_jobs=4,
    job_timeout_seconds=180,
    description="AI Reasoning Engine — bounded single-call latency, vendor rate limits",
)

AI_RESEARCH: Final = WorkerPool(
    name="ai_research",
    max_jobs=2,
    job_timeout_seconds=1800,
    description=(
        "AI Research Engine — agentic, multi-step, minutes not seconds. "
        "Lowest concurrency and longest timeout of any pool; the leading "
        "candidate for Temporal migration once ARQ's non-resumable job "
        "model becomes a measured constraint."
    ),
)

READ_MODEL: Final = WorkerPool(
    name="read_model",
    max_jobs=20,
    job_timeout_seconds=120,
    description="Timeline, Revenue Intelligence Platform — projection updates",
)

DEFAULT: Final = WorkerPool(
    name="default",
    max_jobs=10,
    job_timeout_seconds=300,
    description="Consumers that have not yet been assigned a specific pool",
)

POOLS: Final[dict[str, WorkerPool]] = {
    pool.name: pool
    for pool in (
        INGESTION,
        GRAPH,
        INTELLIGENCE,
        AI_REASONING,
        AI_RESEARCH,
        READ_MODEL,
        DEFAULT,
    )
}


class UnknownPoolError(Exception):
    """The configured pool name does not exist.

    Fails at startup rather than silently falling back to a default: a
    typo'd pool name that quietly ran the wrong queue would be very hard to
    notice and would leave the intended queue undrained.
    """

    def __init__(self, name: str) -> None:
        super().__init__(f"Unknown worker pool '{name}'. Valid pools: {', '.join(sorted(POOLS))}.")


def resolve_pool(name: str | None = None) -> WorkerPool:
    """The pool this process should run, from argument or environment."""
    resolved = name or os.environ.get(DEFAULT_POOL_ENV_VAR, DEFAULT.name)
    if resolved not in POOLS:
        raise UnknownPoolError(resolved)
    return POOLS[resolved]


# Provider syncs get their own pool (M2.1). They are I/O-bound, slow, and
# rate-limited by third parties — sharing a pool with fast internal work
# would let one throttled provider starve everything behind it.
PROVIDER_SYNC_POOL = WorkerPool(
    name="provider_sync",
    max_jobs=4,
    job_timeout_seconds=600,
    description=(
        "Provider syncs. I/O-bound, slow, and rate-limited by third parties — "
        "sharing a pool with fast internal work would let one throttled provider "
        "starve everything queued behind it."
    ),
)
POOLS[PROVIDER_SYNC_POOL.name] = PROVIDER_SYNC_POOL
