# ADR-0008: Search & Vector Retrieval — Meilisearch + pgvector

**Status:** Accepted

## Context

Timeline needs full-text/faceted search over entity and event history ([04-modules.md](../04-modules.md)); Knowledge Graph and AI Research Engine need semantic (embedding-based) retrieval over entities, relationships, and prior research artifacts ([14-ai-architecture.md](../14-ai-architecture.md)). These are two related but distinct retrieval needs.

## Decision

**Meilisearch** for full-text/faceted search. **pgvector** (PostgreSQL extension) for vector/semantic search, colocated in the primary database.

## Alternatives Considered — Search

| Alternative | Why not chosen |
|---|---|
| **Elasticsearch / OpenSearch** | The category leader with the largest-scale track record, but materially heavier to operate (JVM-based cluster management, shard/replica tuning) than Signora's search needs justify at current and near-term scale — Timeline's search surface is faceted/full-text over structured records, not full-scale log analytics. |
| **Algolia** | Excellent DX and hosted simplicity, but a bought SaaS with per-record/per-search pricing that scales unfavorably against Signora's target of millions of companies indexed, and less control over self-hosting for cost/data-residency reasons ([16-architecture-risks.md](../16-architecture-risks.md) R-02). |
| **PostgreSQL full-text search (`tsvector`)** | Would avoid a second technology, but Meilisearch's typo-tolerance, relevance ranking, and faceting are materially better out-of-the-box for the kind of sales-user-facing search Timeline needs, without the query-tuning burden of hand-built `tsvector` ranking. |

## Alternatives Considered — Vector Search

| Alternative | Why not chosen |
|---|---|
| **Pinecone / Weaviate / Qdrant (dedicated vector databases)** | Purpose-built and highest ceiling for pure vector-search performance at extreme scale, but each introduces a second datastore with its own consistency, backup, and multi-tenancy story — directly against Principle 6. pgvector keeps embeddings in the same transactional, RLS-enforced database as everything else, at a scale (Signora's near-term embedding volume, not general-purpose vector-search-at-any-scale) where pgvector's performance is adequate. |
| **Elasticsearch's vector/kNN support** | Would consolidate search and vector needs into one system, but ties the vector-search decision to the search-engine decision, and Elasticsearch was already rejected above on operational-weight grounds. |

## Tradeoffs

**We gain:** Meilisearch's low operational overhead and strong out-of-the-box relevance for Timeline's use case; pgvector's transactional colocation with the rest of Signora's data, meaning embeddings inherit RLS-based tenant isolation ([11-tenancy.md](../11-tenancy.md)) automatically, with no separate access-control model to maintain.

**We give up:** Elasticsearch's proven scale ceiling and Pinecone/Weaviate/Qdrant's purpose-built vector-search performance — both explicitly tracked as **Risk R-08** in [16-architecture-risks.md](../16-architecture-risks.md), with load testing scheduled as a Horizon-1 action in [17-future-recommendations.md](../17-future-recommendations.md) specifically to validate or falsify this tradeoff before it becomes a production surprise.

## Risks

R-08 (untested at target scale) is the primary risk. Both choices were made with an explicit, documented fallback rather than as an irreversible bet.

## Migration Strategy

- **Meilisearch → Elasticsearch/OpenSearch**: Timeline's search interface is isolated behind its own query abstraction ([15-project-structure.md](../15-project-structure.md)); a migration would reindex into the new engine behind the same interface.
- **pgvector → dedicated vector DB**: embedding storage is isolated per owning module (Knowledge Graph, AI Research Engine); a migration would move embedding storage/query out of those modules' `infrastructure/` layers to a new adapter, without changing domain logic that merely asks "find semantically similar X."

Both migrations are scoped, evidence-triggered actions per [12-scalability.md](../12-scalability.md) and [17-future-recommendations.md](../17-future-recommendations.md) Horizon 3 — not adopted pre-emptively.

## Consequences

- Timeline's query API is backed by Meilisearch, kept in sync via event-driven indexing from `observation.recorded`, `business_event.detected`, etc. ([06-events.md](../06-events.md)).
- Embedding vectors are stored on owning modules' own workspace-scoped, RLS-enforced tables.
- Both Meilisearch and pgvector load testing at target scale is a named Horizon-1 action ([17-future-recommendations.md](../17-future-recommendations.md)).
