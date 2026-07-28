# ADR-0024: Code Quality & Static Analysis Tooling

**Status:** Accepted

## Context

[CLAUDE.md](../../../CLAUDE.md) requires strong typing and consistent standards across the codebase; [05-module-dependencies.md](../05-module-dependencies.md) requires mechanical enforcement of module boundaries. This ADR ratifies the specific tools.

## Decision

**Ruff** for backend linting and formatting. **MyPy** (strict mode) for backend static typing. **pre-commit** for local enforcement before commit. **ESLint** for frontend linting. **Prettier** for frontend formatting. **import-linter** for module-boundary enforcement (referenced in [15-project-structure.md](../15-project-structure.md), ratified here as part of the code-quality tooling cluster).

## Alternatives Considered

| Layer | Alternative | Why not chosen |
|---|---|---|
| Backend lint/format | Black + Flake8 + isort (separate tools) | Ruff reimplements the combined functionality of Black, Flake8, isort, and more in a single, materially faster (Rust-based) tool from the same maintainers as uv ([ADR-0003](0003-package-and-dependency-management.md)) — consolidating three-plus tools into one reduces configuration surface and CI time with no loss of capability. |
| Backend static typing | Pyright (as the primary CI gate) | Pyright is excellent and arguably faster for editor integration, but MyPy remains the more configurable, CI-oriented standard with the deepest strict-mode ecosystem support; both can coexist (Pyright for editor experience, MyPy for the binding CI gate) without conflict — MyPy is ratified as the CI-enforced standard specifically. |
| Frontend lint/format | Biome (combined linter+formatter, Rust-based) | A credible, faster alternative following the same "Ruff for JS/TS" positioning, but as of this decision has less complete ESLint-plugin-ecosystem parity (particularly for Next.js/React-specific and accessibility-rule plugins) than the established ESLint + Prettier pairing — worth revisiting as Biome's plugin ecosystem matures. |

## Tradeoffs

**We gain:** a fast, consolidated backend tooling story (Ruff) reducing CI time and configuration surface, strict static typing enforcement (MyPy) as a binding CI gate, and a mature, plugin-rich frontend linting ecosystem (ESLint) matched with Prettier's uncontroversial formatting.

**We give up:** Biome's potential future speed/consolidation advantage on the frontend — noted as a revisit-later item, not adopted now given current plugin-ecosystem gaps.

## Risks

Low. Ruff and uv sharing a maintainer (Astral) is a mild correlated-vendor-risk factor (if Astral's projects lost momentum, both would be affected together) — a specific instance of [16-architecture-risks.md](../16-architecture-risks.md) R-11, judged acceptable given both tools' current strong adoption trajectory and standards-compliant (non-lock-in) configuration formats.

## Migration Strategy

Ruff, MyPy, ESLint, and Prettier configuration all live in standard config files (`pyproject.toml`, `.eslintrc`, `.prettierrc`) with no proprietary lock-in; a future swap (e.g., to Biome once mature) is a configuration-file change, not a codebase rewrite, since these tools enforce style/typing rules rather than being embedded in application code.

## Consequences

- `pre-commit` runs Ruff, MyPy, and import-linter locally before every commit; CI ([ADR-0022](0022-devops-infrastructure-and-deployment-topology.md)) re-runs all of them plus ESLint/Prettier as a non-bypassable gate.
- MyPy strict mode is non-negotiable across `backend/` — no module is exempted.
- The `.importlinter` contract file at the repository root is the binding, CI-enforced expression of [05-module-dependencies.md](../05-module-dependencies.md)'s dependency graph.
