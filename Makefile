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

.PHONY: smoke smoke-keep dr up down test

## Verify the whole platform end to end, then tear down.
smoke:
	@./infra/smoke.sh

## Same, but leave the stack running for inspection after a failure.
smoke-keep:
	@SMOKE_KEEP_STACK=1 ./infra/smoke.sh

## Disaster Recovery Validation against an already-running production stack.
dr:
	@./infra/disaster-recovery.sh

## Bring the local production stack up / down.
up:
	@docker compose --env-file infra/.env.prod-local -f infra/docker-compose.prod.yml up -d --build --wait
down:
	@docker compose --env-file infra/.env.prod-local -f infra/docker-compose.prod.yml down -v --remove-orphans

## Backend suite. Truncates its target database — hence the explicit opt-in.
test:
	@cd backend && SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1 uv run pytest --cov
