# ADR-0003: Package & Dependency Management — uv

**Status:** Accepted

## Context

Python's historically fragmented packaging tooling (pip, pip-tools, Poetry, PDM, conda) creates real developer-experience and CI-speed costs. Signora's team needs fast, reproducible installs across local development, CI, and container builds, with reliable lockfile-based dependency resolution.

## Decision

**uv** for package and dependency management, project/venv management, and Python version management across the backend.

## Alternatives Considered

| Alternative | Why not chosen |
|---|---|
| **pip + pip-tools** | The historical baseline; correct but slow, with no integrated venv/Python-version management, requiring extra tooling (pyenv, virtualenv) to match uv's single-tool scope. |
| **Poetry** | Mature and widely adopted, with good lockfile semantics, but materially slower dependency resolution and installs than uv (often 10–100x), which compounds across CI runs, local onboarding, and container builds at team scale. |
| **PDM** | Similar feature set to Poetry with PEP 621 compliance, but smaller ecosystem/community than both Poetry and uv, with less momentum as of this decision. |
| **conda / mamba** | Better suited to heavy scientific/binary dependency management (e.g., CUDA-linked ML training stacks) than a web-service backend; unnecessary complexity for Signora's dependency profile, which is standard pure-Python/wheel packages. |

## Tradeoffs

**We gain:** materially faster installs and CI (uv's Rust-based resolver is the fastest in the Python ecosystem as of this decision), a single tool covering dependency management, virtual environments, and Python version pinning, and native `pyproject.toml`/PEP 621 compliance requiring no proprietary lockfile format lock-in beyond the standard `uv.lock`.

**We give up:** uv is a comparatively young project (from Astral, also maintainers of Ruff — see [ADR-0024](0024-code-quality-and-static-analysis.md)) relative to Poetry's longer track record — accepted as Risk R-11 in [16-architecture-risks.md](../16-architecture-risks.md), mitigated by uv's adherence to standard `pyproject.toml` (no proprietary project format), which keeps a migration off uv cheap if ever needed.

## Risks

See [16-architecture-risks.md](../16-architecture-risks.md) R-11 (vendor/project concentration on younger tooling). uv's standards-compliance is the specific mitigation: dependency declarations live in standard `pyproject.toml`, not a uv-proprietary format, so switching resolvers does not require rewriting dependency declarations.

## Migration Strategy

Because uv consumes and produces standard `pyproject.toml`, migrating to Poetry or PDM if uv's trajectory changed would require only regenerating a lockfile in the target tool's format — a low-cost, mechanical migration, not a rewrite.

## Consequences

- `backend/pyproject.toml` and `uv.lock` are the single source of truth for backend dependencies.
- CI and Docker builds use `uv sync` for reproducible installs.
- Pre-commit hooks and local developer setup are standardized on `uv run` for consistent environment execution.
