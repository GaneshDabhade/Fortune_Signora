# ADR-0027: Local-First Development — Verification Belongs on the Developer's Machine During the Architecture Phase

**Status:** Accepted — 2026-07-29

## Context

Signora is in an architecture-first phase. Fifteen milestones have shipped, each closed by a Definition of Done ([CLAUDE.md](../../../CLAUDE.md) §19) whose quality gates are **already executed locally**: Pytest with a coverage gate, `make smoke` against the real production images, MyPy strict, import-linter, and the Security Invariants suite.

[ADR-0022](0022-devops-infrastructure-and-deployment-topology.md) ratified GitHub Actions as the CI/CD platform, and three workflows were built at M1.1–M1.5 (`backend.yml`, `frontend.yml`, `smoke.yml`), each triggered on `push` to `main` and on `pull_request`. In practice they re-ran, remotely and several minutes later, exactly the checks that had already passed locally before the commit was made. Every push started five jobs, one of which rebuilds both Docker images from scratch.

The observable cost was notification noise and Actions minutes. The architectural cost is larger and is the reason this ADR exists: **it made `git push` mean something other than "store the repository safely."**

## Decision

**Until explicitly reversed, all verification is local.**

GitHub serves exactly three purposes: **version control · remote backup · future collaboration.** It is not part of the build system, the test system, the release system, or the deployment system.

Concretely:

- GitHub Actions is **disabled at the repository level**.
- All three workflow files are **retained**, with every job definition preserved unchanged, and their only trigger set to `workflow_dispatch`. Nothing self-triggers.
- No CI provider, release automation, publishing pipeline, scheduled workflow, remote evaluation, or deployment automation may be introduced.
- Milestone verification is `pytest` · `make smoke` · `mypy --strict` · `lint-imports` · Security Invariants · the coverage gate — all on the developer's machine.

**A `git push` performs one action: it stores the repository remotely.**

### The conditions under which CI returns

All five, together:

1. The architecture has stabilised.
2. The Intelligence Pipeline has stabilised.
3. The Workflow Pipeline has stabilised.
4. The AI Platform has stabilised.
5. CI is **explicitly requested**.

Until all five hold, the correct quantity of CI is **zero**.

## Alternatives Considered

| Alternative | Why not chosen |
|---|---|
| **Keep CI as it was** | It verified nothing the local gate did not, several minutes later and on a machine nobody was watching. A second copy of a passing check is not a second signal; it is the same signal, delayed. |
| **Disable Actions at repository level only** | Correct and instant, but invisible in the repository — a clone, a fork, or a new collaborator sees three live-looking workflows. This project enforces every other rule structurally and in-repo, and a policy living only in a settings page is exactly the kind of thing it otherwise refuses. Adopted as *half* the decision, not all of it. |
| **Change triggers to `workflow_dispatch` only** | Visible and version-controlled, but does not cover a workflow added later by a tool or a collaborator. Also adopted as half the decision. Together the two cover both the immediate and the structural failure. |
| **Delete the workflows** | The job definitions are correct and were expensive to get right — the service-container topology, the least-privilege role creation, the migration up/down/up reversibility check. Deleting them would mean rebuilding that knowledge from memory when CI returns. Retention costs nothing once nothing triggers them. |
| **Silence the email notifications** | Treats the symptom. The jobs would keep running and keep consuming minutes; the only change would be that nobody saw the failures. |
| **Reduce CI to a smaller subset** | Rejected on the same reasoning as the roadmap's no-speculative-ports ruling: the correct response to automation with no demonstrated need is none of it, not a smaller amount of it. |

## Tradeoffs

**We gain:** one verification path instead of two, so a green local run is definitive rather than provisional; no remote execution triggered by storing code; no Actions minutes; and, most consequentially, engineering attention stays on architecture rather than on pipeline maintenance during the phase where the architecture is the asset being built.

**We give up:** verification on a clean, known machine — the property that catches *"it passes on my laptop"* — and automatic verification of contributions from a second developer. Both are real, and both are priced correctly at a single-developer, pre-collaboration, pre-deployment stage. The first is partially recovered by `make smoke`, which builds and runs the production images from scratch and is therefore substantially less laptop-dependent than a bare test run.

## Risks

- **Local environment drift.** A check may pass locally for a reason that would not hold elsewhere. Mitigated by `make smoke` building the real images, and accepted as the explicit cost above.
- **A skipped test looks like a passing one.** The cross-tier JWT contract test skips when the frontend's dependencies are absent, and CI was what guaranteed they were present. Mitigated in the same change: `make smoke` now runs it and **fails if it is skipped**, so the guarantee is asserted rather than assumed.
- **This ADR being forgotten.** Mitigated by [CLAUDE.md](../../../CLAUDE.md) §20e, which binds it for every future session, and by the header comment in each retained workflow.

## Relationship to Existing Decisions

This ADR **amends the operating mechanism** of three earlier decisions without reversing any of their substance. Each retains its ratified content; only *where* enforcement runs changes.

| ADR | What it decided | What changes |
|---|---|---|
| [0022](0022-devops-infrastructure-and-deployment-topology.md) | GitHub Actions as the CI/CD platform | The choice stands for when CI returns. It is not operating now. |
| [0023](0023-testing-strategy.md) | Pytest, Vitest, Playwright; the full suite gates a merge | The suite and the gate stand. The gate is local. |
| [0024](0024-code-quality-and-static-analysis.md) | Ruff, MyPy strict, ESLint, Prettier, import-linter as binding gates | All still binding, all still non-bypassable. Enforced locally, and by `pre-commit` where installed. |

Nothing in this decision touches [ADR-0022](0022-devops-infrastructure-and-deployment-topology.md)'s production topology, which remains the target M14.5 provisions against, or the Infrastructure Contract ([CLAUDE.md](../../../CLAUDE.md) §20b) that keeps the application deployable to it. **Deferring the pipeline is not deferring deployability.**

## Consequences

- Documentation that described CI as the currently authoritative enforcement mechanism has been corrected to say *local*. Documentation recording what was true at an earlier milestone — change logs, completed acceptance criteria, the M1.2 validation record — has been **left intact and dated**, because rewriting history to match the present would be a different kind of untruth.
- `make smoke` gains the cross-tier JWT contract check, so the one capability that existed only inside a CI job now has a local home.
- Every future milestone's Definition of Done is satisfied entirely on a developer machine.
- When CI returns, it returns by re-enabling Actions and restoring the triggers in three files. No job definition needs to be rewritten.
