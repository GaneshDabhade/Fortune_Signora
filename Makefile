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

.PHONY: environments reachability event-catalog workstation unsaved review review-status review-end smoke smoke-keep dr up down test certify certified kpi doc-drift state-check coverage-debt release-preflight runtime-composition demo demo-prepare demo-seed demo-users demo-narrate eval eval-reasoning eval-research e2e e2e-quick e2e-smoke product-demo product-demo-record endurance review-product review-messy review-first-hour


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
# **The collision it was built for is gone.** Human review runs on 3000/8000 and
# the production stack now runs on 3100/8100, so a review session and a
# certification run coexist — proven by running both at once. What remains are
# the preconditions that each cost a real incident: an unreachable development
# database once blocked pytest for 22 minutes with no diagnostic, and memory
# pressure from another environment turned a 130s smoke run into a 320s one.
#
#   0 ready · 3 blocked        (exit 2 is retired with the collision)
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
## **Not preflighted, deliberately.** `release-preflight` requires 3100/8100 to be
## *free* so smoke can bind them; `dr` requires the production stack to be *up* on
## exactly those ports. The preconditions are inverses, and wiring the preflight
## here made `dr` unrunnable — caught within one cycle of adding it. What `dr`
## needed was the lease, which it has.
dr:
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
## `playground@2` instead of `baseline@1`. No branch anywhere knows it is a
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
##
## **Leaves the two processes to you.** `make review` runs the same preparation
## and then starts them — see `demo-prepare` below for why the two share one
## definition rather than two.
demo: demo-prepare
	@echo ""
	@echo "  backend   cd backend && uv run uvicorn apps.api.main:create_app --factory --reload --port 8000"
	@echo "  frontend  cd frontend && npm run dev"
	@echo "  then      http://localhost:3000 — sign in as dana.reyes@northwind.example"
	@echo "  password  see docs/RUNNING.md"

## The preparation itself, with nothing said about what to do next.
##
## **Extracted so `make review` can reuse it rather than restate it** (L-1). The
## two differ only in what happens *after* the data exists — `demo` prints two
## commands for someone who wants the processes in their own terminals; `review`
## starts them. A second copy of these five steps would drift the day one of
## them changed, and the copy nobody was maintaining is the one somebody would
## have run.
demo-prepare:
	@$(DEV_COMPOSE) up -d --wait
	@cd backend && SIGNORA_DATABASE_URL=$(OWNER_DATABASE_URL) uv run alembic upgrade head
	@cd frontend && npm run --silent auth:migrate
	@$(MAKE) demo-users
	@$(MAKE) demo-seed

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

## **Every environment, derived from its identity.** The Environment Framework's
## model: ports, database, Redis index and compose project are all a function of
## an environment's name, so nothing is allocated by hand.
##
##     make environments              the matrix
##     make environments ARGS=--check the model agrees with RUNNING.md
environments:
	@python3 ./infra/environments.py $(ARGS)

## **Can a customer get to this screen?** The frontend sibling of
## `runtime-composition` — that asks whether the deployed worker consumes what a
## module projects; this asks whether any screen leads to a route.
##
## An entrance is a link from *outside* the route's own subtree. The Connection
## Center had two inbound links and was still unreachable: both were inside the
## connection flow, so a customer could reach it only by already being there.
reachability:
	@python3 ./infra/reachability.py $(ARGS)

## **Make this machine able to run Signora, and say what that cost.** (RS-2)
#
# Repository Health · Configuration Safety. Generates one RSA pair and writes
# both halves to the tiers that need them — the public half to the backend, the
# private half to the frontend — removing the transcription step where it used
# to go wrong. A mismatched pair mints tokens the API rejects with no clue why.
#
# It never overwrites an existing configuration without --force, and --force
# says what it is about to invalidate before doing it.
#
#     make workstation
#     make workstation ARGS=--check     report, change nothing
#     make workstation ARGS=--force     regenerate; signs everyone out
workstation:
	@python3 ./infra/workstation.py $(ARGS)

## **Does the platform emit an event the contract does not name?**
#
# Repository Health · Documentation Synchronization. The third sibling of
# `runtime-composition` (does the worker consume what a module projects?) and
# `reachability` (can a customer reach this screen?).
#
# **Advisory, and deliberately.** Its one finding today can only be cleared by
# editing a 🔴 file, so gating would make every lane's run red for a reason no
# lane could act on — and the cost of that is every other warning being skimmed.
#
#     make event-catalog
#     make event-catalog ARGS=--strict     # for a future gate; nothing uses it
event-catalog:
	@python3 ./infra/event-catalog.py $(ARGS)

## **What would you lose if this disk died right now?** (RS-1, L-18)
#
# Awareness, never enforcement — it always exits 0, and no gate consults it. A
# lane mid-experiment is doing exactly what the law permits; the point is that a
# session should not *end* without somebody deciding whether the work on disk is
# temporary or worth keeping.
#
# `.gitignore` is the disposability classifier, so anything reported is, by the
# repository's own declaration, not disposable.
#
#     make unsaved
#     make unsaved ARGS=--workstation    every Signora clone on this machine
unsaved:
	@python3 ./infra/unsaved.py $(ARGS)

## **A product review, in one command.** Prepare, validate, seed, start both
## tiers, open the browser, and record the session.
#
# The reviewer types this and nothing else — no port, no database, no compose
# project, no second terminal. Every value is derived from the `review` profile
# in `infra/environments.py`, so the day an allocation changes, nothing here or
# in `infra/review.py` is edited.
#
# Each run leaves a record in `review/sessions/`: the commit, whether that
# commit was certified, the dataset, the accounts, and the open defects a
# reviewer should expect to meet. `make review-end` finalizes it.
#
#     make review
#     make review-status
#     make review-end
#     make review-end ARGS='--note "Timeline empty state reads oddly"'
review:
	@python3 ./infra/review.py start

review-status:
	@python3 ./infra/review.py status

review-end:
	@python3 ./infra/review.py end $(ARGS)

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

## The customer journeys, in a real browser, against this lane's own stack.
##
## **Leased, because a browser suite mutates whatever it is pointed at.** It
## adds products, watches companies and records permanent decisions — so two
## runs against one database contaminate each other exactly as cycle 25's
## second operation contaminated a certification. `environment-lease.py` already
## solves that and is reused unchanged; nothing new locks anything
## (docs/RELEASE_ENGINEERING.md §7).
##
## **Re-seeded first, so a run is reproducible.** The workflow journeys record
## real decisions, which changes what the next run reads. Seeding is seconds and
## the alternative is a suite whose result depends on how many times it has been
## run before — `make e2e-quick` skips it when iterating on one spec.
##
## **SIGNORA_APP_URL has no default and the suite refuses ports 3000/8000.**
## Those are Human Review's, and a suite that writes must never reach them.
##
##     make e2e                        the whole suite, re-seeded
##     make e2e ARGS="--project=firefox"
##     make e2e-quick                  no re-seed
##     make e2e-smoke                  the shortest proof the product is alive
E2E_URL ?= http://localhost:3400
E2E_DB  ?= signora_lane_b
E2E_ENV := SIGNORA_TEST_APP_DATABASE_URL=postgresql+asyncpg://signora_app:signora_app_local_dev@localhost:5432/$(E2E_DB) \
           SIGNORA_TEST_ADMIN_DATABASE_URL=postgresql+asyncpg://signora:signora@localhost:5432/$(E2E_DB) \
           SIGNORA_DATABASE_URL=postgresql+asyncpg://signora:signora@localhost:5432/$(E2E_DB) \
           SIGNORA_APP_URL=$(E2E_URL) \
           SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1

e2e:
	@python3 infra/environment-lease.py run e2e -- sh -c 'cd backend && $(E2E_ENV) uv run python -m tests.playground.seed && cd ../frontend && SIGNORA_APP_URL=$(E2E_URL) npx playwright test $(ARGS)'

e2e-quick:
	@python3 infra/environment-lease.py run e2e -- sh -c 'cd frontend && SIGNORA_APP_URL=$(E2E_URL) npx playwright test $(ARGS)'

e2e-smoke:
	@python3 infra/environment-lease.py run e2e -- sh -c 'cd frontend && SIGNORA_APP_URL=$(E2E_URL) npx playwright test --grep @smoke'

## Signora, demonstrated rather than verified — a real browser, at human pace.
##
## **A different product from `make e2e`, and separated because the goals
## conflict**: a regression suite wants to be fast and headless, a
## demonstration wants to be watched. One continuous story, narrated as it
## goes, against real pipeline output.
##
##     make product-demo          watch it
##     make product-demo-record   headless, and keep the video and trace
##
## **Demo modes are not built and the architecture already allows them.** The
## `demo` project matches every spec under `tests/e2e/demo/`, and `ARGS` reaches
## Playwright — so a future sales, investor, engineering or AI journey is a new
## file plus a tag, and `make product-demo ARGS="--grep @investor"` selects it.
## Nothing needs redesigning to add one; that is the whole check the product
## owner asked for, and no more was built (2026-08-03).
##
## The recording lands in `frontend/test-results/` and is the artifact worth
## keeping: a replayable account of how Signora behaves, for somebody who was
## not in the room.
product-demo:
	@python3 infra/environment-lease.py run product-demo -- sh -c 'cd backend && $(E2E_ENV) uv run python -m tests.playground.seed && cd ../frontend && HEADED=1 SIGNORA_APP_URL=$(E2E_URL) npx playwright test --project=demo --reporter=list $(ARGS)'

product-demo-record:
	@python3 infra/environment-lease.py run product-demo -- sh -c 'cd backend && $(E2E_ENV) uv run python -m tests.playground.seed && cd ../frontend && SIGNORA_APP_URL=$(E2E_URL) npx playwright test --project=demo --reporter=list $(ARGS)'
	@echo ""
	@echo "  video and trace:  frontend/test-results/"

## Walk the product as a demanding customer would, in a browser you can watch.
##
## **Not a test, and it can never fail.** Product Experience Engineering
## (product owner, 2026-08-03): the question is *"would I buy this?"*, not
## *"does it work?"* — so this asserts nothing, reads every screen back as
## text, and leaves the judgement to a person.
##
##     make review-product            headed, at human pace
##     make review-product PACE=2000  slower, for a demonstration
review-product:
	@python3 infra/environment-lease.py run e2e -- sh -c 'cd backend && $(E2E_ENV) uv run python -m tests.playground.seed && cd ../frontend && SIGNORA_APP_URL=$(E2E_URL) npx tsx tests/review/walk.ts'

## Review 2 — the accounts the product is not proud of, and the reading load.
##
##     make review-messy
##
## Opens the contested, disputed, expired and unnamed accounts rather than the
## tidy one at the top, and measures words-per-screen against actions-per-screen
## — because "too much text" is a number, not an opinion.
review-messy:
	@python3 infra/environment-lease.py run e2e -- sh -c 'cd backend && $(E2E_ENV) uv run python -m tests.playground.seed && cd ../frontend && SIGNORA_APP_URL=$(E2E_URL) npx tsx tests/review/messy.ts'

## Review 3 — the first hour, for somebody the product has never met.
##
##     make review-first-hour
##
## Registers a brand new person through the real sign-up form and follows them
## until they reach value or run out of things to click. **No seeding** — a
## seeded shortcut would skip precisely the hour under review.
review-first-hour:
	@python3 infra/environment-lease.py run e2e -- sh -c 'cd frontend && set -a && . ./.env.local && set +a && SIGNORA_APP_URL=$(E2E_URL) npx tsx tests/review/first-hour.ts'

## A working day in one tab — endurance, not regression.
##
## **The one question the suite cannot answer**: a seven-minute run says nothing
## about what a tab looks like after an afternoon. This holds one open, repeats
## one identical cycle of a seller's work, and records what happens to it.
##
##     make endurance                       twenty minutes
##     make endurance MINUTES=180           an afternoon
##     make endurance MINUTES=480 HEADED=1  a working day, watchable
##
## **Not part of `make e2e`, and never will be.** A gate nobody can afford to
## run is a gate that gets skipped; this is run deliberately, before a release
## or when a session-length question is actually being asked.
##
## It observes and does not assert — the judgement is arithmetic in
## `frontend/tests/endurance/trend.ts`, unit-tested without a browser, and the
## exit code carries it. Samples land in `frontend/test-results/endurance/` as
## they are taken, so a session killed at hour six still has hours one to five.
endurance:
	@python3 infra/environment-lease.py run e2e -- sh -c 'cd backend && $(E2E_ENV) uv run python -m tests.playground.seed && cd ../frontend && SIGNORA_APP_URL=$(E2E_URL) npx tsx tests/endurance/record.ts'

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

## The same again, for Sales Engagement's commercial synthesis passes.
#
# A fourth entry point for the same reason M9 and M10 own theirs: the platform's
# would have to import this module's `Pass`, its context protocol and its dataset
# shape, and no upstream module depends on a downstream one.
#
# Its dataset is different in kind rather than merely in content. Every other
# golden set is a transcript of what providers *reported*; `approach@1` is a
# transcript of what the deterministic layer *decided*, because layer 2 is never
# shown raw evidence. A synthesis evaluated against evidence would be measuring a
# system Signora does not run.
#
# Runs each case twice by default: the input is a closed set, so two runs differ
# only by the model, and a pass that behaves once and fabricates on the second
# attempt is one a single run structurally cannot detect.
eval-approach:
	@cd backend && uv run python -m modules.sales_engagement.evaluation $(ARGS)
