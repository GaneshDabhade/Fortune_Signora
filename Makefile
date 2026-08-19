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

.PHONY: require-e2e-url refuse-slot-0 prod-local-env environments reachability event-catalog workstation validate unsaved review review-status review-end smoke smoke-keep dr up down test certify certified kpi doc-drift state-check coverage-debt release-preflight runtime-composition demo demo-prepare demo-seed demo-users demo-narrate eval eval-reasoning eval-research e2e e2e-quick e2e-smoke product-demo product-demo-record endurance review-product review-messy review-first-hour


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
##
## ⚡ **`prod-local-env` added 2026-08-07 — B-212.** `docker compose` fails hard
## when `--env-file` names a path that does not exist, and its message names
## neither the file's purpose nor how to make one. **A documented command
## referencing a file the repository neither shipped nor described** is the §2
## defect, and Lane A hit it running exactly the command the Makefile offers.
## **The check costs one `test -f` and replaces a compose error with the two
## lines that fix it.**
prod-local-env:
	@test -f infra/.env.prod-local || { \
	  echo ""; \
	  echo "  infra/.env.prod-local does not exist, and docker compose cannot start without it."; \
	  echo ""; \
	  echo "  It is gitignored and always will be — it holds this machine's RS256 signing keys."; \
	  echo "  Two commands create it:"; \
	  echo ""; \
	  echo "    cp infra/.env.prod-local.example infra/.env.prod-local"; \
	  echo "    cd frontend && npm run keys:generate >> ../infra/.env.prod-local"; \
	  echo ""; \
	  echo "  Only the two SIGNORA_JWT_* values are required; everything else defaults."; \
	  echo ""; \
	  exit 1; \
	}

up: prod-local-env
	@python3 infra/environment-lease.py run up -- docker compose --env-file infra/.env.prod-local -f infra/docker-compose.prod.yml up -d --build --wait
down: prod-local-env
	@python3 infra/environment-lease.py run down -- docker compose --env-file infra/.env.prod-local -f infra/docker-compose.prod.yml down -v --remove-orphans

## Backend suite. Truncates its target database — hence the explicit opt-in.
##
## **Leased, from 2026-08-05 ([B-317](docs/BUGS.md)).** Five targets already
## acquired the lease and this one did not, while being the one that truncates
## every table after every test. Two runs would delete each other's fixtures
## mid-suite and **neither would say so** — the Makefile recorded that exact
## failure beside the lease itself, as cycle 25's `pytest 134 passed` against a
## suite of 2589.
##
## The lease is now workstation-scoped, so this also refuses to start while
## another *clone* holds the environment ([B-118](docs/BUGS.md)).
##
## ⛔ **This target named NO database until 2026-08-15, and consented to
## truncation anyway** — [B-270](docs/BUGS.md), raised 🔴 by Lane A after running
## it. `environment-lease.py run` adds only its lease variable, so the database
## was whatever the shell already held, and `conftest.py`'s fallback is
## `localhost:5432/signora` — **slot 0, which is human review's.** A new shell
## plus the documented gate emptied it, with no mistake required.
##
## ⚡ **The Makefile already knew the answer**: `SIGNORA_DB` is resolved at line
## 140 from `infra/environments.py`. It simply was not passed.
test: refuse-slot-0
	@python3 infra/environment-lease.py run test -- sh -c 'cd backend && $(call DESTRUCTIVE_DB_ENV,$(SIGNORA_DB)) uv run pytest --cov'

## The Product Playground — twelve accounts through the real pipeline.
##
## **There is one product.** This runs the same pipeline the suite runs, over
## `playground@4` instead of `baseline@1`. No branch anywhere knows it is a
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
##
## **One stack per lane, from 2026-08-05** — 436 change (2), approved by the
## product owner. `infra/environments.py --exports` resolves this clone to its
## environment (from `SIGNORA_ENVIRONMENT`, else the checked-out branch) and
## emits the project name and host ports. **Nothing here knows the arithmetic
## and no lane types a port**, which is the difference between an allocation and
## a convention — the allocation existed for days and nothing read it.
##
## On `integration`, `main` or a detached head no environment resolves and the
## exports name the historical shared stack, out loud.
SIGNORA_STACK := $(shell python3 infra/environments.py --exports | grep -v '^\#')
SIGNORA_PG_PORT := $(shell python3 infra/environments.py --exports | sed -n 's/^SIGNORA_POSTGRES_PORT=//p')
# 🔴 **[B-287](docs/BUGS.md), 2026-08-19, reported by Lane A.** One integration
# test held `redis://localhost:6379/0` as a literal — **slot 0, human review's**
# — so it raised `ConnectionRefusedError` in every lane. **The port was already
# derived one line up in spirit and simply never passed**, which is B-408's
# shape exactly: *"the mechanism already existed and nothing called it."*
SIGNORA_REDIS_PORT := $(shell python3 infra/environments.py --exports | sed -n 's/^SIGNORA_REDIS_PORT=//p')
# **The database this environment owns, from the allocation — TASK-455.**
# `OWNER_DATABASE_URL` said `/signora` on every slot, which is the name only
# slot 0 has. The `demo` environment is slot 7 with `signora_demo`, so
# `make demo` prepared a database nothing would read and then told the
# reviewer to open slot 0.
SIGNORA_DB := $(shell python3 infra/environments.py --exports | sed -n 's/^SIGNORA_DATABASE=//p')
SIGNORA_WEB := $(shell python3 infra/environments.py --exports | sed -n 's/^SIGNORA_WEB_PORT=//p')
SIGNORA_API := $(shell python3 infra/environments.py --exports | sed -n 's/^SIGNORA_API_PORT=//p')
DEV_COMPOSE := env $(SIGNORA_STACK) docker compose -f infra/docker-compose.yml
OWNER_DATABASE_URL := postgresql+asyncpg://signora:signora@localhost:$(SIGNORA_PG_PORT)/$(SIGNORA_DB)

# **Consent to truncation and the database being truncated, named together.**
# [B-270](docs/BUGS.md): the guard in `conftest.py` asks *"do you consent?"* and
# never *"which database?"*, and the answer to the first was correctly yes. So
# the two must not be separable here — **any recipe that sets
# `SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1` gets it from this and therefore names a
# database in the same breath.**
#
# ⚡ One definition, called with a database name, so `test` and the E2E targets
# cannot drift apart — [§2](CLAUDE.md), truth has exactly one representation.
DESTRUCTIVE_DB_ENV = SIGNORA_TEST_APP_DATABASE_URL=postgresql+asyncpg://signora_app:signora_app_local_dev@localhost:$(SIGNORA_PG_PORT)/$(1) \
                     SIGNORA_TEST_ADMIN_DATABASE_URL=postgresql+asyncpg://signora:signora@localhost:$(SIGNORA_PG_PORT)/$(1) \
                     SIGNORA_REDIS_URL=redis://localhost:$(SIGNORA_REDIS_PORT)/0 \
                     SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1

## 🔴 **Naming the database is not enough when the name is slot 0's.**
##
## **[B-270](docs/BUGS.md), second half, 2026-08-15.** `DESTRUCTIVE_DB_ENV` closed
## the *fallback* — a shell with no `SIGNORA_TEST_*` no longer reaches
## `conftest.py`'s `localhost:5432/signora`. ⛔ **It did NOT close the case where
## `SIGNORA_DB` legitimately RESOLVES to `signora`**: `infra/environments.py:295`
## falls back to the historical shared stack whenever the clone is not on a lane
## branch, and slot 0 is human review's.
##
## ⚠️ **That made the fix worse in one respect** — the target now names slot 0
## *explicitly*, so it reads as deliberate rather than as an oversight.
##
## ⚡ **Found from QE running `--exports` on `integration` and reporting
## `SIGNORA_POSTGRES_PORT=5432` in passing.** It was not the subject of their
## message.
##
## **Refusal, with an override that has to be typed.** `demo-seed` against slot 0
## is exactly what a reviewer wants and exactly what a lane must never do, and
## nothing in the environment can tell those apart — so the human says which.
##
## 🔴 **The test is the PORT, not the database name — corrected 2026-08-15 on
## [B-271](docs/BUGS.md), the same day the guard was written.**
##
## **The first version asked `SIGNORA_DB != signora`.** ⛔ **That premise is
## false**: `infra/docker-compose.yml:31` hardcodes `POSTGRES_DB: signora`, so
## **every lane's own stack holds a database of that name.** ⚡ **The port is what
## separates slots; the name never did.** ⛔ **A guard keyed on the name asks a
## question whose answer is the same everywhere.**
##
## ⚠️ **Found because QE reported B-271 as a `RUNNING.md` problem.** **It is also
## this guard's premise, and this office wrote both.**
refuse-slot-0:
	@test "$(SIGNORA_PG_PORT)" != "5432" || test "$(ALLOW_SLOT_0)" = "1" || { \
	  echo ""; \
	  echo "  REFUSED: port $(SIGNORA_PG_PORT) is slot 0 — human review's stack."; \
	  echo ""; \
	  echo "  This clone resolves to no lane environment, so infra/environments.py fell back"; \
	  echo "  to the historical shared stack. Check with:"; \
	  echo ""; \
	  echo "    python3 infra/environments.py --exports"; \
	  echo ""; \
	  echo "  On a lane branch you get that lane's own port and database. If you are on"; \
	  echo "  integration or a detached HEAD, you are not meant to be running this."; \
	  echo ""; \
	  echo "  If slot 0 really is the target — a reviewer seeding their own stack —"; \
	  echo "  say so on the command you actually ran, e.g.  make demo-seed ALLOW_SLOT_0=1"; \
	  echo ""; \
	  exit 1; \
	}

## Everything a reviewer needs, in one command: stack up, schema migrated,
## Better Auth's own tables created, four sign-in accounts, twelve accounts of
## pipeline output. Credentials are in docs/RUNNING.md.
##
## **Leaves the two processes to you.** `make review` runs the same preparation
## and then starts them — see `demo-prepare` below for why the two share one
## definition rather than two.
demo: demo-prepare
	@echo ""
	@echo "  backend   cd backend && uv run uvicorn apps.api.main:create_app --factory --reload --port $(SIGNORA_API)"
	@echo "  frontend  cd frontend && npm run dev"
	@echo "  then      http://localhost:$(SIGNORA_WEB) — sign in as dana.reyes@northwind.example"
	@echo "  sign up   http://localhost:$(SIGNORA_WEB)/sign-up — the verification link"
	@echo "            prints to the frontend console; requireEmailVerification stays on"
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

demo-seed: refuse-slot-0
	@cd backend && $(call DESTRUCTIVE_DB_ENV,$(SIGNORA_DB)) uv run python -m tests.playground.seed

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
demo-narrate: refuse-slot-0
	@cd backend && $(call DESTRUCTIVE_DB_ENV,$(SIGNORA_DB)) uv run python -m tests.playground.narrate

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

## **Stage 1 validation, against a database this run creates.** (the RE-03 sibling)
#
# Repository Health · Configuration Safety. A bare `pytest` resolves its target
# from the shell, which on a multi-lane workstation points at a shared database
# carrying whichever lane migrated it last. That produced three misleading
# failure lists in one day — one of them 13 Security Invariants reporting a
# missing `workspace_id` on a table whose migration creates one.
#
# Creates signora_validate_<commit>, migrates it, runs the suite, drops it.
#
#     make validate
#     make validate ARGS=--quick     no coverage; faster for a first look
# Run inside the backend venv: it provisions the database through
# `tests/certification/database.py`, which imports asyncpg.
validate:
	@cd backend && uv run python ../infra/validate.py $(ARGS)

## **The files that decide whether a commit may be promoted, type-checked.**
#
# ⛔ **[B-435](docs/BUGS.md): `infra/` was outside the TYPE gate.** `mypy` runs
# from `backend/`, so the promotion guard, the state check, the coordination
# generator and the release preflight — the tools that decide what ships — were
# read by no type checker at all.
#
# ⚠️ **Corrected 2026-08-17: this comment claimed those files "have no test
# suite behind them either", and that is FALSE.** ✅ **Measured rather than
# assumed**: `certification-guard.py` has 9 test files, `review.py` 64,
# `validate.py` 34, `workstation.py` 11, `state-check.py` and `coordination.py`
# 5 each. **Exactly four `infra/` tools have none** — `doc-drift.py`,
# `pipeline-dashboard.py`, `production-readiness.py`, `runtime-composition.py`
# — and all four are advisory. ⛔ **The false version was the more alarming
# one, which is why it survived a reading: a claim that overstates the danger
# is not the safe direction to be wrong in** (`CLAUDE.md` §2).
#
# ⚡ **What it caught on the day it was written**, none of which any other gate
# could see: `sys.stderr` with no `import sys`, in an error branch that only
# runs when the tool has something to report · `holders` bound twice in one
# function in `release-preflight.py`, `list[Holder]` and `list[str]`, working
# only because the branch that rebinds it always returns · `BY_NAME` bound
# three times in `environments.py`, one dead and one a no-op · `named` bound
# twice in `state-check.py`.
#
# ✅ **Widened from a named list to the whole directory, 2026-08-17.** It began
# as seven files because the other nineteen carried twenty-three errors, and
# gating them the same day would have meant one unreviewable change or ignores
# that make the gate decorative. **Those twenty-three are now fixed, so the
# caveat is gone**: a new file in `infra/` is covered the moment it lands,
# rather than the moment somebody remembers to add it here.
#
# ⚡ **What the second pass caught**: `_load()` in `review.py` returning a
# corrupt `session.json` as if it were a session, so every caller's `[...]`
# raised far from the cause · `_coverage_json()` declaring `dict` and able to
# return a list · `len(c) > 7` guarding a branch three lines under
# `if len(c) < 8: continue`, which is Decorative Logic (`CLAUDE.md` §2) · the
# same regex searched twice per field to narrow it, so a future edit to one
# copy and not the other crashes on `.group`.
#
# ⛔ **No ignores, no `--follow-imports=skip`, no per-file relaxation.** A gate
# that has been made to pass by lowering it is the thing it exists to catch.
types-infra:
	@cd backend && uv run mypy --strict ../infra/

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

## **Is this environment ready?** One command, one verdict, one exit code.
##
## Composes the checks that already exist — workstation, environments,
## state-check, reachability, runtime-composition — and re-implements none of
## them: each runs as a subprocess and each remains runnable alone.
##
## It repairs NOTHING. `workstation.py` is invoked as `--check`, and no check
## here carries a flag that writes. A doctor that fixed things would be making
## governance decisions on behalf of every tool it wraps, which is the reason
## state-check refuses to repair.
##
## Blocking failures set the exit code; advisory findings are reported and do
## not. A check not run is printed as `not run` with its reason — absence is
## never allowed to read as a pass.
##
##     make doctor
##     make doctor ARGS=--full     also runs `make validate` (minutes)
##     make doctor ARGS=--list     what it would run, and runs nothing
doctor:
	@python3 ./infra/doctor.py $(ARGS)

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
## ⛔ **`DESTRUCTIVE_DB_ENV` here is REDUNDANCY, never the guarantee.**
##
## **The real isolation is `backend/tests/certification/database.py`**: the run
## creates a disposable `signora_certify_<sha12>` and `__main__.py:446` applies
## its three URLs with `os.environ.update(...)` before any gate is spawned —
## built for [B-106](docs/BUGS.md) and covered by `test_disposable_database.py`.
##
## 🔴 **Do not remove that as duplication of this line.** This target was briefly
## and wrongly recorded as exposed in [B-270](docs/BUGS.md), because the parent's
## environment was measured and the variables are injected into the child. **The
## correction cost a killed certification run.**
certify: release-preflight
	@python3 infra/environment-lease.py run certify -- sh -c 'cd backend && $(call DESTRUCTIVE_DB_ENV,$(SIGNORA_DB)) uv run python -m tests.certification'

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
## ⚡ **Derived, not hardcoded — B-408, 2026-08-07.** These two read
## `http://localhost:3400` and `signora_lane_b`: **Lane B's row, defaulted for
## every lane in the repository.** `SIGNORA_WEB` and `SIGNORA_DB` are resolved
## from `environments.py` twenty lines above and were simply not consumed here,
## so a lane running `make e2e` seeded its **own** PostgreSQL — the port was
## already derived — under **another lane's database name**, and pointed
## Playwright at **another lane's dev server**.
##
## ⛔ **Not cross-lane data loss, and the reason is worth keeping**: the port
## *was* derived, so the wrong database name resolves to a database that does
## not exist on this clone's server and the seed fails loudly. **Slotting is
## what turned a destructive default into a confusing one.**
##
## ⚠️ **The mechanism already existed and nothing called it.** `environments.py`
## `current()` says so in its own docstring — *"a wrong guess here points a
## suite at another lane's database, which is the class of defect the whole
## change exists to end."* **It was right, and these two lines were the gap.**
E2E_URL ?= http://localhost:$(SIGNORA_WEB)
E2E_DB  ?= $(SIGNORA_DB)
## ⛔ **B-183, 2026-08-11 — a third owner credential used to sit here and it was
## read by nothing.** `SIGNORA_DATABASE_URL=…//signora:signora@…` was in this
## block; the seeder takes `SIGNORA_TEST_ADMIN_DATABASE_URL` and
## `SIGNORA_TEST_APP_DATABASE_URL` (`tests/playground/seed.py:261`), and
## `playwright.config.ts` declares **no `webServer`**, so nothing `make e2e`
## starts ever read it. **Removed rather than left**: an unread variable holding
## the highest-privilege credential is not harmless, it is a value waiting for
## its first reader — which is precisely how [B-183] happened one file over.
##
## ⚠️ **The API under test is the lane's own dev server, configured from its own
## `backend/.env`.** That is why B-183's fix is in `.env.example` and not here:
## the Playwright journeys ran with RLS disarmed because the *server* was
## started as the owner, and no line in this file could have changed that.
E2E_ENV := $(call DESTRUCTIVE_DB_ENV,$(E2E_DB)) \
           SIGNORA_APP_URL=$(E2E_URL)

## ⛔ **A portless `E2E_URL` is REFUSED, never defaulted** — [B-1014](docs/BUGS.md).
##
## `environments.py current()` returns `None` on `integration`, `main` **and a
## detached head**, and says so in its own docstring. No environment derived means
## no `SIGNORA_WEB_PORT` on line 151, which means `SIGNORA_WEB` is empty, which
## makes the line above `http://localhost:` — **port 80.**
##
## ⚠️ **Certification runs detached at the pinned SHA**, so this is not an edge
## case for the browser gate; it is the certification path itself. Lane A lost 33
## tests to `ERR_CONNECTION_REFUSED` and **the run reported them as ordinary
## failures** — a gate reporting red about nothing, which is worse than no gate,
## because it looks exactly like a broken product.
##
## ✅ **Refusing beats recovering.** Guessing a port would point the suite at
## whatever happens to be listening — which is the defect `current()` was written
## to end: *"a wrong guess here points a suite at another lane's database."*
require-e2e-url:
	@case '$(E2E_URL)' in \
	  *:[0-9]*) : ;; \
	  *) \
	    printf '\n  \033[31mREFUSED\033[0m — E2E_URL has no port: %s\n\n' '$(E2E_URL)' >&2; \
	    printf '  No environment was derived, so SIGNORA_WEB_PORT was never set.\n' >&2; \
	    printf '  environments.py returns None on integration, main and a DETACHED HEAD.\n\n' >&2; \
	    printf '  Running anyway would hit port 80 and report every browser test as a\n' >&2; \
	    printf '  failure — red about nothing. B-1014.\n\n' >&2; \
	    printf '  Name the environment explicitly:\n\n' >&2; \
	    printf '      SIGNORA_ENVIRONMENT=lane-a make %s\n\n' '$(firstword $(MAKECMDGOALS))' >&2; \
	    exit 1 ;; \
	esac

e2e: require-e2e-url
	@python3 infra/environment-lease.py run e2e -- sh -c 'cd backend && $(E2E_ENV) uv run python -m tests.playground.seed && cd ../frontend && SIGNORA_APP_URL=$(E2E_URL) npx playwright test $(ARGS)'

e2e-quick: require-e2e-url
	@python3 infra/environment-lease.py run e2e -- sh -c 'cd frontend && SIGNORA_APP_URL=$(E2E_URL) npx playwright test $(ARGS)'

e2e-smoke: require-e2e-url
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
product-demo: require-e2e-url
	@python3 infra/environment-lease.py run product-demo -- sh -c 'cd backend && $(E2E_ENV) uv run python -m tests.playground.seed && cd ../frontend && HEADED=1 SIGNORA_APP_URL=$(E2E_URL) npx playwright test --project=demo --reporter=list $(ARGS)'

product-demo-record: require-e2e-url
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
review-product: require-e2e-url
	@python3 infra/environment-lease.py run e2e -- sh -c 'cd backend && $(E2E_ENV) uv run python -m tests.playground.seed && cd ../frontend && SIGNORA_APP_URL=$(E2E_URL) npx tsx tests/review/walk.ts'

## Review 2 — the accounts the product is not proud of, and the reading load.
##
##     make review-messy
##
## Opens the contested, disputed, expired and unnamed accounts rather than the
## tidy one at the top, and measures words-per-screen against actions-per-screen
## — because "too much text" is a number, not an opinion.
review-messy: require-e2e-url
	@python3 infra/environment-lease.py run e2e -- sh -c 'cd backend && $(E2E_ENV) uv run python -m tests.playground.seed && cd ../frontend && SIGNORA_APP_URL=$(E2E_URL) npx tsx tests/review/messy.ts'

## Review 3 — the first hour, for somebody the product has never met.
##
##     make review-first-hour
##
## Registers a brand new person through the real sign-up form and follows them
## until they reach value or run out of things to click. **No seeding** — a
## seeded shortcut would skip precisely the hour under review.
review-first-hour: require-e2e-url
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
endurance: require-e2e-url
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
