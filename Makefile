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

.PHONY: smoke smoke-keep dr up down test certify certified kpi doc-drift state-check coverage-debt release-preflight runtime-composition demo demo-seed demo-users demo-narrate eval eval-reasoning eval-research

# These are invoked as `bash <script>` rather than `./<script>` deliberately.
# The executable bit is filesystem state, not repository state, and it does
# not survive every checkout: a Windows or WSL mount, a zip export, or a
# `git config core.fileMode false` clone all drop it. Commit 0309193 dropped
# it from both scripts, which would have made the milestone gate fail with
# "Permission denied" on a fresh clone — and under ADR-0027 this is the only
# gate there is. Invoking through bash removes the failure mode entirely and
# behaves identically on Linux, macOS, and WSL.

## Is the workstation ready for QE Release Mode? Classifies in under a second.
#
# Human Review Mode (`make demo`) and QE Release Mode want the same two ports,
# 3000 and 8000. The collision used to surface several minutes into a smoke run
# as "3 of 24 stages", which reads like a repository defect and is not one.
#
#   0 ready · 2 waiting on a review session · 3 blocked
release-preflight:
	@python3 infra/release-preflight.py

## Verify the whole platform end to end, then tear down.
#
# Preflighted, so a run that cannot possibly succeed says why immediately
# rather than after building a stack it will not be able to bind.
smoke: release-preflight
	@python3 infra/environment-lease.py run smoke -- bash ./infra/smoke.sh

## Same, but leave the stack running for inspection after a failure.
smoke-keep:
	@SMOKE_KEEP_STACK=1 bash ./infra/smoke.sh

## Disaster Recovery Validation against an already-running production stack.
dr: release-preflight
	@python3 infra/environment-lease.py run dr -- bash ./infra/disaster-recovery.sh

## Bring the local production stack up / down.
up:
	@python3 infra/environment-lease.py run up -- docker compose --env-file infra/.env.prod-local -f infra/docker-compose.prod.yml up -d --build --wait
down:
	@python3 infra/environment-lease.py run down -- docker compose --env-file infra/.env.prod-local -f infra/docker-compose.prod.yml down -v --remove-orphans

## Backend suite. Truncates its target database — hence the explicit opt-in.
test:
	@cd backend && SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1 uv run pytest --cov

## The Product Playground — twelve accounts through the real pipeline.
##
## **There is one product.** This runs the same pipeline the suite runs, over
## `playground@1` instead of `baseline@1`. No branch anywhere knows it is a
## playground; the only difference is which scenario file is named.
##
## `demo` brings the stack up and seeds. `demo-seed` re-seeds an already-running
## stack — which is also how you join the workspace after signing in, since
## Better Auth owns users and no credential ships in this repository.
## The development stack lives in `infra/`, not at the repository root — and
## migrations run under the **owner** identity, never the runtime one, so this
## passes the URL explicitly rather than inheriting whatever `backend/.env`
## happens to hold. A `.env` pointing at `signora_app` (the correct runtime
## value) would otherwise fail migrations with a permissions error that reads
## like a broken schema (CLAUDE.md §8).
DEV_COMPOSE := docker compose -f infra/docker-compose.yml
OWNER_DATABASE_URL := postgresql+asyncpg://signora:signora@localhost:5432/signora

## Everything a reviewer needs, in one command: stack up, schema migrated,
## Better Auth's own tables created, four sign-in accounts, twelve accounts of
## pipeline output. Credentials are in docs/RUNNING.md.
demo:
	@$(DEV_COMPOSE) up -d --wait
	@cd backend && SIGNORA_DATABASE_URL=$(OWNER_DATABASE_URL) uv run alembic upgrade head
	@cd frontend && npm run --silent auth:migrate
	@$(MAKE) demo-users
	@$(MAKE) demo-seed
	@echo ""
	@echo "  backend   cd backend && uv run uvicorn apps.api.main:create_app --factory --reload --port 8000"
	@echo "  frontend  cd frontend && npm run dev"
	@echo "  then      http://localhost:3000 — sign in as dana.reyes@northwind.example"
	@echo "  password  see docs/RUNNING.md"

demo-seed:
	@cd backend && SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1 uv run python -m tests.playground.seed

## The Playground's sign-in accounts, created through Better Auth's own sign-up
## and verification routes. Not a bypass: the accounts simply already exist.
demo-users:
	@cd frontend && npm run --silent demo:users

## Narrate the seeded accounts with the real released prompt and model.
##
## **Opt-in, and separate from `demo` on purpose.** Seeding is offline and takes
## seconds; this is one real inference per account against a local Ollama and
## takes minutes. Folding it in would make a one-command demo fail on any
## machine without a model runtime.
##
## Nothing is scripted: the real prompt registry, the real release rule, the
## real provider. If `explanation_narration@1` were not released for the
## configured model this refuses, exactly as production would.
demo-narrate:
	@cd backend && SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1 uv run python -m tests.playground.narrate

## Advisory: did a slice change production code without updating its module's
## documentation? (CLAUDE.md §12)
##
## Deliberately advisory — it exits 0 unless given --strict. It sees whether a
## file changed, never whether what it says is true, and a check that claimed
## otherwise would be worse than none: a passing run would be read as "the docs
## are fine". QE runs it during validation and raises what it finds with the
## lane; it does not gate a promotion.
##
##     make doc-drift                       # integration..HEAD
##     make doc-drift ARGS="main..HEAD"
##     make doc-drift ARGS="--strict"
doc-drift:
	@python3 ./infra/doc-drift.py $(ARGS)

## Gate, not advisory: may this commit be promoted? (CLAUDE.md §20e)
##
## Certification binds to an immutable commit; promotion promotes that commit and
## no other. This refuses anything else, and exits non-zero when it does — the
## rule cannot be kept by care alone, because `git merge --ff-only integration`
## promotes whatever the branch points at when the command runs.
##
##     make certified                       # is `main`'s head certified?
##     make certified ARGS="<sha>"          # may this commit be promoted?
##     make certified ARGS="--audit-main"   # the guarantee, across the branch
certified:
	@python3 ./infra/certification-guard.py $(ARGS)

## Engineering KPIs, derived from the repository rather than reported about it.
##
## Every figure comes from the certification manifest, git history and the
## registers — nothing is entered by hand, for the same reason no gate result is.
## They measure how the process runs, never whether the software is correct.
##
##     make kpi
##     make kpi ARGS="--markdown"      # the block PROJECT_STATUS.md carries
kpi:
	@python3 ./infra/kpi.py $(ARGS)

## What does the deployed worker actually consume? (B-301)
#
# The fifth validation layer, and the one no module's suite covers: a
# composition root. Each module tests its half and assumes the wiring, so a
# handler nothing calls passes every gate — which is how Timeline shipped
# complete and consumed nothing, through four certified promotions.
#
# Reports; does not fail. Most unwired consumers are deliberate (C-012).
#
#     make runtime-composition
#     make runtime-composition ARGS="--strict"
runtime-composition:
	@python3 ./infra/runtime-composition.py $(ARGS)

## Where is the coverage debt, and is it growing? (CLAUDE.md §19)
#
# Reads the data `pytest --cov` already wrote — it runs nothing, so it is
# seconds. **A lane runs this before handing over**, which is the whole point:
# coverage stops being something QE discovers four cycles later.
#
#     make coverage-debt                    # whole repository, worst first
#     make coverage-debt ARGS="timeline"    # one module
#     make coverage-debt ARGS="--new"       # files never executed by a test
coverage-debt:
	@python3 ./infra/coverage-debt.py $(ARGS)

## Advisory: do the governance documents agree with the repository?
## Run at Repository Closeout, before declaring Repository Ready (CLAUDE.md
## §20e). Reports; never repairs — each inconsistency it finds has more than
## one correct resolution, and choosing between them is a governance decision.
state-check:
	@python3 ./infra/state-check.py $(ARGS)

## Release Certification (ADR-0032). Runs every gate, then records what happened
## as durable repository evidence in `certification/manifest.json`.
##
## Deliberately NOT part of `make test`, for the reason `make eval` is not: it
## brings the production stack up and down, it takes minutes, and it writes to
## the repository. Nothing here re-asserts a guarantee a gate already proves —
## certification's contribution is the record, not a second opinion.
##
## There are no options. A mode that skipped a gate would produce a run that
## cannot certify, and a command whose convenient path yields worthless evidence
## teaches people to use it.
certify: release-preflight
	@python3 infra/environment-lease.py run certify -- sh -c 'cd backend && SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1 uv run python -m tests.certification'

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

## The same again, for the AI Research Engine's planning prompt.
#
# M10 owns a third entry point for the same reason M9 owns a second, and its
# own dataset for a different one: the derivation catalog consumes
# `business_event` and `dissenting_signal`, while M8's golden set holds none of
# either — a planner evaluated against it could only produce steps its own
# schema refuses.
eval-research:
	@cd backend && uv run python -m modules.ai_research_engine.evaluation $(ARGS)
