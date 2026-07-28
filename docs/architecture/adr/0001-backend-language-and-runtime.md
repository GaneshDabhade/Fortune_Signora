# ADR-0001: Backend Language & Runtime — Python 3.13+

**Status:** Accepted

## Context

[02-principles.md](../02-principles.md) requires a language that supports Clean Architecture idiomatically (Principle 4), ports-and-adapters for providers/AI/integrations (Principles 9–11), and strong typing given the domain's transformation-pipeline complexity ([08-technology-stack.md](../08-technology-stack.md)). The language must also have a mature ecosystem for the specific workload Signora's core differentiation depends on: AI/LLM orchestration, agentic tool use, and data-pipeline processing.

## Decision

Python 3.13+ is Signora's backend language and runtime.

## Alternatives Considered

| Alternative | Why not chosen |
|---|---|
| **TypeScript / Node.js** | Excellent for the API/IO layer, but the AI/ML ecosystem (vendor SDKs, agentic frameworks, embeddings/vector tooling) is secondary to Python's in maturity and first-party vendor support; would mean routing AI workloads through the least-mature ecosystem for exactly the modules that matter most (AI Research Engine, AI Reasoning Engine). |
| **Go** | Best-in-class for raw throughput and operational simplicity, but weaker ecosystem for AI/LLM tooling, and its lack of a rich structural-typing/Protocol system plus more verbose error handling would add friction to Clean Architecture's ports-and-adapters pattern relative to Python's Protocols. |
| **Java / Kotlin (JVM)** | Mature, strongly-typed, excellent for large teams — but heavier operational footprint, slower iteration speed, and a materially less current AI/agentic ecosystem than Python as of this decision. |

## Tradeoffs

**We gain:** first-tier AI/LLM vendor SDK support (Anthropic, OpenAI, Google all ship Python SDKs as primary, often before other languages), the deepest available ecosystem for embeddings/agentic tooling, strong typing via type hints + MyPy strict mode, and Protocol-based structural typing that maps cleanly onto ports-and-adapters ([15-project-structure.md](../15-project-structure.md)).

**We give up:** Python's historically weaker raw throughput per core versus Go, and GIL-related concurrency constraints for CPU-bound work — mitigated because Signora's workload is overwhelmingly I/O-bound (database, provider APIs, AI vendor calls), where `asyncio` (via FastAPI, [ADR-0002](0002-web-framework-and-api-style.md)) is the right concurrency model regardless of language choice.

## Risks

- Python's type system is optional/gradual, not enforced by the compiler — mitigated by mandatory MyPy strict mode in CI ([ADR-0024](0024-code-quality-and-static-analysis.md)).
- CPU-bound pipeline stages (if any emerge, e.g., heavy scoring computation in Signal Engine/Buying Score Engine) may need to be offloaded to a compiled extension or a separate worker strategy if profiling shows a bottleneck — not a concern today.

## Migration Strategy

Because every module follows Clean Architecture with domain logic isolated from infrastructure ([15-project-structure.md](../15-project-structure.md)), a future language migration for a specific extracted module (per Principle 5) would only require reimplementing that module's infrastructure layer against the same domain contracts — not a full-system rewrite. No migration is planned or anticipated.

## Consequences

- Every module's `domain/` and `application/` layers use type hints throughout; MyPy strict mode is non-negotiable ([ADR-0024](0024-code-quality-and-static-analysis.md)).
- `asyncio`-based concurrency is the default execution model across FastAPI and ARQ.
