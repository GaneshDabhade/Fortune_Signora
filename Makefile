# Signora — top-level developer commands.
#
# `make smoke` is the platform foundation completion gate (M1.4): one
# command that verifies the entire local production stack. It is required
# before every milestone and every release.
#
# All verification is local (CLAUDE.md §20c-2, ADR-0027). The full milestone
# gate is:
#
#   make smoke                               whole stack, production images
#   make test                                suite + coverage gate
#   cd backend && uv run mypy .              strict types
#   cd backend && uv run lint-imports        module boundaries
#   cd backend && uv run pytest -m security_invariant
#
# There is no remote gate. A green local run is the decision, not a preview
# of one.

.PHONY: smoke smoke-keep dr up down test eval eval-reasoning

# These are invoked as `bash <script>` rather than `./<script>` deliberately.
# The executable bit is filesystem state, not repository state, and it does
# not survive every checkout: a Windows or WSL mount, a zip export, or a
# `git config core.fileMode false` clone all drop it. Commit 0309193 dropped
# it from both scripts, which would have made the milestone gate fail with
# "Permission denied" on a fresh clone — and under ADR-0027 this is the only
# gate there is. Invoking through bash removes the failure mode entirely and
# behaves identically on Linux, macOS, and WSL.

## Verify the whole platform end to end, then tear down.
smoke:
	@bash ./infra/smoke.sh

## Same, but leave the stack running for inspection after a failure.
smoke-keep:
	@SMOKE_KEEP_STACK=1 bash ./infra/smoke.sh

## Disaster Recovery Validation against an already-running production stack.
dr:
	@bash ./infra/disaster-recovery.sh

## Bring the local production stack up / down.
up:
	@docker compose --env-file infra/.env.prod-local -f infra/docker-compose.prod.yml up -d --build --wait
down:
	@docker compose --env-file infra/.env.prod-local -f infra/docker-compose.prod.yml down -v --remove-orphans

## Backend suite. Truncates its target database — hence the explicit opt-in.
test:
	@cd backend && SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1 uv run pytest --cov

## Prompt evaluation against a real model. Deliberately NOT part of `make test`.
#
# The only command in this repository that requires a model. Everything else —
# the suite, the Security Invariants, the smoke test — is offline and
# deterministic by design, and folding a probabilistic run into the test gate
# is how a project ends up with a flaky suite people learn to re-run until it
# passes (28-ai-platform.md, "the two-tier guarantee").
#
# **The provider is resolved by model, never named** (ruled 2026-07-30). Both
# commands pass `AISettings` to the AI Platform's registry builder and ask for
# a model; which vendor serves it is that module's business. So:
#
#     make eval                                    # the configured dev runtime
#     make eval ARGS="--model claude-sonnet-4-5"   # the hosted production model
#
# The second needs SIGNORA_ANTHROPIC_API_KEY in the environment and nothing
# else — no code change, no flag, no vendor branch. A model no adapter serves
# reports UNMEASURABLE rather than a verdict, because a missing credential is
# not a finding about a prompt.
#
# Development runs use the local runtime (ADR-0028); a run that cannot execute
# fails rather than skipping, because a harness that fell back to a fake would
# measure the fake. Add `--record` to append the measurement to the prompt
# manifest, which is the only way a prompt earns its release.
eval:
	@cd backend && uv run python -m modules.ai_platform.evaluation $(ARGS)

## The same, for the AI Reasoning Engine's own prompt and output type.
#
# M9 owns a second entry point because M8's cannot import `ReasonedOutput`
# without breaking the reverse-dependency contract. Everything else — harness,
# datasets, rubric, release recorder, provider registry — is reused unchanged.
eval-reasoning:
	@cd backend && uv run python -m modules.ai_reasoning_engine.evaluation $(ARGS)
