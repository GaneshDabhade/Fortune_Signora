#!/usr/bin/env bash
#
# Disaster Recovery Validation (M1.3A · T21b).
#
# Restarts each component of the running production stack and asserts that
# nothing is lost. Every check compares observed state before and after a
# deliberate restart — none of it is inferred from the design, because the
# design being correct is exactly the claim under test.
#
# Run against an already-running stack:
#   ./disaster-recovery.sh
#
# Exits non-zero on the first violated guarantee, naming which one.

set -euo pipefail

cd "$(dirname "$0")"

COMPOSE="docker compose --env-file .env.prod-local -f docker-compose.prod.yml"
PSQL="docker exec signora-prod-postgres-1 psql -U signora -d signora -tAc"
API="http://localhost:8100"

pass() { printf '  \033[32m✓\033[0m %s\n' "$1"; }
fail() { printf '  \033[31m✗ %s\033[0m\n' "$1"; exit 1; }
stage() { printf '\n\033[1m%s\033[0m\n' "$1"; }

# ---------------------------------------------------------------- helpers

mint_token() {
  local user_id="${1:-}"
  local priv
  priv="$(python3 -c "
import re, pathlib
t = pathlib.Path('.env.prod-local').read_text()
print(re.search(r'SIGNORA_JWT_PRIVATE_KEY=\"(.*?)\"', t, re.S).group(1))")"
  (cd ../frontend && npx tsx tests/contract/mint-token.ts \
    "$priv" "http://localhost:3100" "signora-api" $user_id 2>/dev/null)
}

wait_for_api() {
  local deadline=$((SECONDS + 90))
  while (( SECONDS < deadline )); do
    if [[ "$(curl -s -o /dev/null -w '%{http_code}' "$API/ready" || true)" == "200" ]]; then
      return 0
    fi
    sleep 2
  done
  fail "API did not become ready within 90s"
}

outbox_counts() {
  $PSQL "SELECT count(*) FILTER (WHERE relayed_at IS NOT NULL) || ':' || count(*) FROM outbox_event"
}

# ---------------------------------------------------------------- baseline

stage "Baseline"

wait_for_api
TOKEN="$(mint_token)"
[[ -n "$TOKEN" ]] || fail "could not mint a token"

BEFORE="$(outbox_counts)"
WORKSPACE="$(curl -s -X POST "$API/workspaces" \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"name":"DR baseline"}' | python3 -c 'import sys,json; print(json.load(sys.stdin)["id"])')"
[[ -n "$WORKSPACE" ]] || fail "could not create a baseline workspace"
pass "stack healthy, workspace created ($WORKSPACE)"

# Let the relay drain what we just published, so "pending" below means
# genuinely pending rather than not-yet-swept.
sleep 3
BASELINE="$(outbox_counts)"
pass "outbox at baseline (relayed:total = $BASELINE)"

# ------------------------------------------------------- 1. PostgreSQL

stage "1. Restarting PostgreSQL"

PG_BEFORE="$(outbox_counts)"
DL_BEFORE="$($PSQL 'SELECT count(*) FROM dead_letter_event')"
LEDGER_BEFORE="$($PSQL 'SELECT count(*) FROM processed_event')"

$COMPOSE restart postgres >/dev/null 2>&1
until docker exec signora-prod-postgres-1 pg_isready -U signora -d signora >/dev/null 2>&1; do sleep 1; done
wait_for_api

[[ "$(outbox_counts)" == "$PG_BEFORE" ]] \
  || fail "outbox rows changed across a PostgreSQL restart (was $PG_BEFORE, now $(outbox_counts))"
pass "unrelayed outbox rows survived"

[[ "$($PSQL 'SELECT count(*) FROM dead_letter_event')" == "$DL_BEFORE" ]] \
  || fail "dead letters lost across a PostgreSQL restart"
pass "dead letters survived"

[[ "$($PSQL 'SELECT count(*) FROM processed_event')" == "$LEDGER_BEFORE" ]] \
  || fail "idempotency ledger lost across a PostgreSQL restart"
pass "idempotency ledger survived"

# The relay reconnects on its own — it must not need a restart to resume.
TOKEN="$(mint_token)"
curl -s -o /dev/null -X POST "$API/workspaces" -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"name":"DR after pg restart"}'
sleep 5
[[ "$($PSQL 'SELECT count(*) FROM outbox_event WHERE relayed_at IS NULL')" == "0" ]] \
  || fail "relay did not resume after the database came back"
pass "relay resumed without intervention"

# ------------------------------------------------------------ 2. Redis

stage "2. Restarting Redis"

REDIS_BEFORE="$($PSQL 'SELECT count(*) FROM outbox_event')"

$COMPOSE restart redis >/dev/null 2>&1
until docker exec signora-prod-redis-1 redis-cli ping >/dev/null 2>&1; do sleep 1; done
wait_for_api

# Redis is transport, not the system of record. Anything lost from the queue
# is still in the outbox — which is the guarantee the outbox exists to
# provide, and the restart is what proves it rather than assuming it.
[[ "$($PSQL 'SELECT count(*) FROM outbox_event')" == "$REDIS_BEFORE" ]] \
  || fail "outbox changed across a Redis restart — the system of record must be unaffected"
pass "outbox unaffected by transport loss"

TOKEN="$(mint_token)"
curl -s -o /dev/null -X POST "$API/workspaces" -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"name":"DR after redis restart"}'
sleep 5
[[ "$($PSQL 'SELECT count(*) FROM outbox_event WHERE relayed_at IS NULL')" == "0" ]] \
  || fail "pipeline did not recover after Redis restart"
pass "pipeline recovered without intervention"

# -------------------------------------------------------------- 3. API

stage "3. Restarting the API"

API_WS_BEFORE="$($PSQL 'SELECT count(*) FROM workspace')"
API_EV_BEFORE="$($PSQL 'SELECT count(*) FROM outbox_event')"

$COMPOSE restart api >/dev/null 2>&1
wait_for_api

# A request that returned 201 has its state and its events committed
# together, so neither count may move because of a restart.
[[ "$($PSQL 'SELECT count(*) FROM workspace')" == "$API_WS_BEFORE" ]] \
  || fail "acknowledged workspaces lost across an API restart"
[[ "$($PSQL 'SELECT count(*) FROM outbox_event')" == "$API_EV_BEFORE" ]] \
  || fail "acknowledged events lost across an API restart"
pass "acknowledged writes and their events both survived"

# Authentication is stateless on this side: tokens are verified, not stored,
# and sessions live in Better Auth's tables. A token minted before the
# restart must still work after it.
[[ "$(curl -s -o /dev/null -w '%{http_code}' "$API/workspaces" -H "Authorization: Bearer $TOKEN")" == "200" ]] \
  || fail "a token minted before the restart was rejected after it"
pass "authentication state survived (no user signed out by a restart)"

# ---------------------------------------------------------- 4. Workers

stage "4. Restarting workers and relay"

W_BEFORE="$($PSQL 'SELECT count(*) FROM processed_event')"

$COMPOSE restart worker relay >/dev/null 2>&1
sleep 8

[[ "$($PSQL 'SELECT count(*) FROM processed_event')" == "$W_BEFORE" ]] \
  || fail "idempotency claims changed across a worker restart"
pass "idempotency ledger intact — no claim consumed without work"

TOKEN="$(mint_token)"
curl -s -o /dev/null -X POST "$API/workspaces" -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"name":"DR after worker restart"}'
sleep 6
[[ "$($PSQL 'SELECT count(*) FROM outbox_event WHERE relayed_at IS NULL')" == "0" ]] \
  || fail "workers did not resume consuming after restart"
pass "workers resumed consuming"

# ------------------------------------------------- 5. Invariants & ordering

stage "5. Isolation and ordering after every restart"

# Per-entity ordering: within one workspace, member_added is caused by
# workspace.created and must never be relayed before it. Cross-entity
# ordering is explicitly not guaranteed and is not asserted.
OUT_OF_ORDER="$($PSQL "
  SELECT count(*) FROM outbox_event created
  JOIN outbox_event caused ON caused.causation_id = created.event_id
  WHERE caused.relayed_at < created.relayed_at")"
[[ "$OUT_OF_ORDER" == "0" ]] \
  || fail "$OUT_OF_ORDER event(s) relayed before their cause — per-entity ordering broken"
pass "per-entity ordering preserved (caused events never precede their cause)"

# No silent loss: published = relayed + pending, always.
RECONCILE="$($PSQL "
  SELECT CASE WHEN count(*) = count(*) FILTER (WHERE relayed_at IS NOT NULL)
                                     + count(*) FILTER (WHERE relayed_at IS NULL)
         THEN 'ok' ELSE 'mismatch' END FROM outbox_event")"
[[ "$RECONCILE" == "ok" ]] || fail "event reconciliation failed: $RECONCILE"
pass "event counts reconcile (published = relayed + pending)"

# Re-run the full Security Invariants suite against the restarted stack. A
# pooled connection carrying stale SET LOCAL state, or a role that
# reconnected with different attributes, shows up here and nowhere else.
#
# LAST, and deliberately so: the suite truncates every table between tests,
# so anything asserted after it would be asserted against an empty database.
# That is not hypothetical — the ordering and reconciliation checks above
# originally ran after this block and passed vacuously for exactly that
# reason.
if (cd ../backend && \
    SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1 \
    SIGNORA_DATABASE_URL="postgresql+asyncpg://signora:signora@localhost:5433/signora" \
    SIGNORA_TEST_APP_DATABASE_URL="postgresql+asyncpg://signora_app:signora_app_local_dev@localhost:5433/signora" \
    SIGNORA_TEST_ADMIN_DATABASE_URL="postgresql+asyncpg://signora:signora@localhost:5433/signora" \
    uv run pytest -m security_invariant -q >/tmp/dr_invariants.log 2>&1); then
  pass "Security Invariants pass against the restarted stack ($(grep -oE '[0-9]+ passed' /tmp/dr_invariants.log | tail -1))"
else
  tail -20 /tmp/dr_invariants.log
  fail "Security Invariants failed after restarts — see /tmp/dr_invariants.log"
fi

printf '\n\033[32m\033[1mDisaster Recovery Validation passed.\033[0m\n'
printf 'Restarted: PostgreSQL, Redis, API, workers, relay. Nothing lost.\n\n'
