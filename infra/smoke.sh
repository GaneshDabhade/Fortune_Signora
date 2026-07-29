#!/usr/bin/env bash
#
# Platform Smoke Test (M1.4) — the platform foundation completion gate.
#
#   make smoke
#
# Builds, starts, migrates, verifies every layer of the local production
# stack, exercises the demo flow, breaks a dependency and watches recovery,
# runs the Security Invariants, and tears down.
#
# This exists because every defect found in M1.2 and M1.3A — six of them,
# including a worker that could never start — was invisible to a fully
# passing test suite and obvious within seconds of running the real stack.
# A green suite is a claim about parts; this is a claim about the system.
#
# With cloud infrastructure deferred to M14.5, this is also the standing
# proof that the Infrastructure Contract still holds. Across the pipeline
# milestones it is the only thing that will notice the application has
# stopped being deployable.
#
# Exits non-zero on the first failed guarantee, naming the stage.

set -euo pipefail
cd "$(dirname "$0")"

COMPOSE="docker compose --env-file .env.prod-local -f docker-compose.prod.yml"
PG="docker exec signora-prod-postgres-1"
PSQL="$PG psql -U signora -d signora -tAc"
API="http://localhost:8000"
FRONTEND="http://localhost:3000"

STAGE=""
STARTED_AT=$SECONDS

stage() { STAGE="$1"; printf '\n\033[1m%s\033[0m\n' "$1"; }
pass()  { printf '  \033[32m✓\033[0m %s\n' "$1"; }
fail()  { printf '  \033[31m✗ %s\033[0m\n' "$1"; printf '\n\033[31m\033[1mSMOKE FAILED at: %s\033[0m\n\n' "$STAGE"; exit 1; }

cleanup() {
  local code=$?
  if [[ "${SMOKE_KEEP_STACK:-0}" != "1" ]]; then
    $COMPOSE down -v --remove-orphans >/dev/null 2>&1 || true
  fi
  exit $code
}
trap cleanup EXIT

http_code() { curl -s -o /dev/null -w '%{http_code}' "$@" || true; }

mint_token() {
  local priv
  priv="$(python3 -c "
import re, pathlib
t = pathlib.Path('.env.prod-local').read_text()
print(re.search(r'SIGNORA_JWT_PRIVATE_KEY=\"(.*?)\"', t, re.S).group(1))")"
  (cd ../frontend && npx tsx tests/contract/mint-token.ts \
     "$priv" "http://localhost:3000" "signora-api" ${1:-} 2>/dev/null)
}

wait_for() {  # wait_for <url> <expected-code> <seconds>
  local deadline=$((SECONDS + $3))
  while (( SECONDS < deadline )); do
    [[ "$(http_code "$1")" == "$2" ]] && return 0
    sleep 2
  done
  return 1
}

# ============================================================ 0. Preflight

stage "0. Preflight"

command -v docker >/dev/null || fail "docker is required"
command -v npx    >/dev/null || fail "node/npx is required (to mint a token via the real issuance path)"

if [[ ! -f .env.prod-local ]]; then
  # Generated rather than committed: these are signing keys, and a key in a
  # repository is a key that has leaked.
  python3 - <<'PY' || fail "could not generate signing keys"
import re, subprocess, pathlib
out = subprocess.run(["npm","run","--silent","keys:generate"], cwd="../frontend",
                     capture_output=True, text=True).stdout
priv = re.search(r"(-----BEGIN PRIVATE KEY-----.*?-----END PRIVATE KEY-----)", out, re.S)
pub  = re.search(r"(-----BEGIN PUBLIC KEY-----.*?-----END PUBLIC KEY-----)", out, re.S)
assert priv and pub, "keys:generate produced no key pair"
pathlib.Path(".env.prod-local").write_text(
    f'SIGNORA_JWT_PRIVATE_KEY="{priv.group(1)}"\n'
    f'SIGNORA_JWT_PUBLIC_KEY="{pub.group(1)}"\n'
    'BETTER_AUTH_SECRET=smoke-test-secret\n')
PY
  pass "generated an ephemeral signing key pair"
else
  pass "signing keys present"
fi

# Start from nothing, so a stale container can never make this pass.
$COMPOSE down -v --remove-orphans >/dev/null 2>&1 || true
pass "previous stack removed"

# ================================================================ 1. Build

stage "1. Build"

$COMPOSE build >/dev/null 2>&1 || fail "production images failed to build"
pass "API, worker, relay, and frontend images built"

# ============================================================== 2. Startup

stage "2. Startup"

$COMPOSE up -d --wait >/dev/null 2>&1 || fail "stack did not reach healthy — see: $COMPOSE logs"
for svc in postgres redis api worker relay frontend; do
  state="$($COMPOSE ps --format '{{.Service}} {{.State}}' | awk -v s="$svc" '$1==s {print $2}')"
  [[ "$state" == "running" ]] || fail "$svc is '$state', expected running"
done
pass "all six services running from production images"

# =========================================================== 3. Migrations

stage "3. Migrations"

# Captured first, then matched. `... | grep -q X` exits as soon as it
# matches, which SIGPIPEs `docker compose logs`; under `set -o pipefail`
# that becomes a pipeline failure. The check would then pass or fail on
# buffering timing — which is exactly how it behaved before this comment.
MIGRATE_LOG="$($COMPOSE logs migrate 2>&1)"

grep -q '"message":"migrations applied"' <<<"$MIGRATE_LOG" \
  || fail "migration runner did not report completion"
pass "migrations applied as a discrete step"

grep -q '"role":"signora"' <<<"$MIGRATE_LOG" \
  || fail "migrations did not run under the migration identity"
pass "ran under the migration identity, not a runtime role"

HEAD="$($PSQL 'SELECT version_num FROM alembic_version')"
[[ -n "$HEAD" ]] || fail "no schema version recorded"
pass "schema at head ($HEAD)"

# The runner must refuse a runtime credential. Asserted live rather than
# trusted: this is what stops a task definition mistake granting the
# application role DDL.
if $COMPOSE run --rm --no-deps \
     -e SIGNORA_DATABASE_URL="postgresql+asyncpg://signora_app:signora_app_local_dev@postgres:5432/signora" \
     migrate >/dev/null 2>&1; then
  fail "migration runner accepted a runtime identity"
fi
pass "refuses to migrate under a runtime identity"

# =========================================================== 4. Identities

stage "4. Identities"

check_role() {  # check_role <service> <env-var> <expected-role>
  local actual
  actual="$($COMPOSE exec -T "$1" printenv "$2" 2>/dev/null | sed 's|.*//\([^:]*\):.*|\1|')"
  [[ "$actual" == "$3" ]] || fail "$1 connects as '$actual', expected '$3'"
  [[ "$actual" != "signora" ]] || fail "$1 connects as the database owner — RLS does not apply"
}

check_role api      SIGNORA_DATABASE_URL       signora_app
check_role worker   SIGNORA_DATABASE_URL       signora_app
check_role relay    SIGNORA_RELAY_DATABASE_URL signora_relay
check_role frontend SIGNORA_AUTH_DATABASE_URL  signora_auth
pass "each tier connects under its own least-privileged identity"

# ========================================================= 5. Image hygiene

stage "5. Image hygiene"

for svc in api frontend; do
  [[ "$($COMPOSE exec -T $svc id -u)" != "0" ]] || fail "$svc runs as root"
done
pass "no service runs as root"

for img in signora-prod-api signora-prod-frontend; do
  n=$(docker history --no-trunc "$img" 2>/dev/null \
      | grep -icE "PRIVATE KEY|CLIENT_SECRET|BETTER_AUTH_SECRET=|PASSWORD=" || true)
  [[ "$n" == "0" ]] || fail "$img has $n secret-bearing layer(s)"
done
pass "no secret baked into either image"

[[ "$($COMPOSE exec -T api sh -c 'ls -a /app | grep -c "^\.env" || true')" == "0" ]] \
  || fail ".env present inside the API image"
[[ "$($COMPOSE exec -T api sh -c 'command -v uv gcc cc 2>/dev/null | wc -l')" == "0" ]] \
  || fail "build toolchain present in the runtime image"
pass "no .env, no build toolchain in the runtime layer"

# =============================================== 6-7. Health and readiness

stage "6. Health and readiness"

[[ "$(http_code $API/health)" == "200" ]]        || fail "/health not green"
[[ "$(http_code $API/ready)"  == "200" ]]        || fail "/ready not green"
[[ "$(http_code $FRONTEND/api/health)" == "200" ]] || fail "frontend health not green"
pass "all probes green"

# Liveness must not depend on the database, and readiness must — asserted
# by taking the database away rather than by reading the code.
$COMPOSE stop postgres >/dev/null 2>&1
sleep 3
[[ "$(http_code $API/health)" == "200" ]] \
  || fail "/health went red when the database stopped — a blip would restart healthy processes"
pass "liveness stayed green with the database down"

READY_CODE="$(http_code $API/ready)"
[[ "$READY_CODE" == "503" ]] \
  || fail "/ready returned $READY_CODE with the database down, expected 503 (orchestrators route on the code, not the body)"
pass "readiness returned 503 with the database down"

$COMPOSE start postgres >/dev/null 2>&1
until $PG pg_isready -U signora -d signora >/dev/null 2>&1; do sleep 1; done
wait_for "$API/ready" 200 90 || fail "API did not recover after the database returned"
pass "recovered without intervention"

# ======================================================= 8. Authentication

stage "8. Authentication"

TOKEN="$(mint_token)"
[[ -n "$TOKEN" ]] || fail "could not mint a token via the real frontend issuance path"
[[ "$(http_code $API/workspaces -H "Authorization: Bearer $TOKEN")" == "200" ]] \
  || fail "a token minted by the real issuer was rejected by the real API"
pass "frontend-minted token accepted by the API (cross-tier contract holds live)"

[[ "$(http_code $API/workspaces)" == "401" ]] || fail "an unauthenticated request was not rejected"
pass "unauthenticated requests rejected"

# ==================================================== 9. JWT verification

stage "9. JWT verification"

# Forged against the running API, not a unit-test verifier.
HEADER_NONE="$(printf '{"alg":"none","typ":"JWT"}' | base64 -w0 | tr '+/' '-_' | tr -d '=')"
CLAIMS="$(printf '{"sub":"3f6c8a1e-0000-4000-8000-000000000001","iss":"http://localhost:3000","aud":"signora-api","exp":9999999999}' | base64 -w0 | tr '+/' '-_' | tr -d '=')"
[[ "$(http_code $API/workspaces -H "Authorization: Bearer ${HEADER_NONE}.${CLAIMS}.")" == "401" ]] \
  || fail "alg:none token was accepted"
pass "alg:none rejected"

HEADER_HS="$(printf '{"alg":"HS256","typ":"JWT"}' | base64 -w0 | tr '+/' '-_' | tr -d '=')"
[[ "$(http_code $API/workspaces -H "Authorization: Bearer ${HEADER_HS}.${CLAIMS}.c2ln")" == "401" ]] \
  || fail "HS256 token was accepted — algorithm confusion is open"
pass "algorithm confusion rejected"

[[ "$(http_code $API/workspaces -H "Authorization: Bearer not.a.token")" == "401" ]] \
  || fail "malformed token was accepted"
pass "malformed token rejected"

# ===================================================== 10-11. Demo flow

stage "10. Demo flow, authorization, and tenant isolation"

CREATED="$(curl -s -X POST $API/workspaces -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"name":"Smoke Test Workspace"}')"
WS_ID="$(printf '%s' "$CREATED" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("id",""))')"
[[ -n "$WS_ID" ]] || fail "workspace creation failed: $CREATED"
pass "workspace created through the real API ($WS_ID)"

[[ "$(http_code $API/workspaces/$WS_ID -H "Authorization: Bearer $TOKEN")" == "200" ]] \
  || fail "owner cannot read their own workspace — isolation is too aggressive"
pass "owner can read their own workspace (Casbin allows the read)"

OUTSIDER="$(mint_token 9a1b2c3d-0000-4000-8000-00000000dead)"
CODE="$(http_code $API/workspaces/$WS_ID -H "Authorization: Bearer $OUTSIDER")"
[[ "$CODE" == "404" ]] \
  || fail "a non-member received $CODE, expected 404 — 403 confirms the workspace exists and permits enumeration"
pass "non-member receives 404, never 403"

OUT_LIST="$(curl -s $API/workspaces -H "Authorization: Bearer $OUTSIDER" \
  | python3 -c 'import sys,json; print(len(json.load(sys.stdin)["items"]))')"
[[ "$OUT_LIST" == "0" ]] || fail "a non-member's workspace list returned $OUT_LIST items"
pass "RLS scopes the list to the caller's own workspaces"

# ============================================ 12-14. Event bus, relay, workers

stage "12. Event bus, relay, and workers"

# The relay sweeps on an interval; give it a bounded window rather than a
# fixed sleep, so a slow machine does not produce a false failure.
DEADLINE=$((SECONDS + 30))
while (( SECONDS < DEADLINE )); do
  [[ "$($PSQL 'SELECT count(*) FROM outbox_event WHERE relayed_at IS NULL')" == "0" ]] && break
  sleep 2
done

PUBLISHED="$($PSQL 'SELECT count(*) FROM outbox_event')"
RELAYED="$($PSQL 'SELECT count(*) FROM outbox_event WHERE relayed_at IS NOT NULL')"
(( PUBLISHED >= 2 )) || fail "expected at least 2 events from workspace creation, found $PUBLISHED"
pass "events published in the causing transaction ($PUBLISHED)"

[[ "$PUBLISHED" == "$RELAYED" ]] || fail "$((PUBLISHED - RELAYED)) event(s) never relayed"
pass "every event relayed through Redis ($RELAYED/$PUBLISHED)"

OUT_OF_ORDER="$($PSQL "
  SELECT count(*) FROM outbox_event created
  JOIN outbox_event caused ON caused.causation_id = created.event_id
  WHERE caused.relayed_at < created.relayed_at")"
[[ "$OUT_OF_ORDER" == "0" ]] || fail "$OUT_OF_ORDER event(s) relayed before their cause"
pass "per-entity ordering preserved"

# Matched on the structured level field, not on the word "error" anywhere
# in the line. Logs are JSON, and a substring match flags benign records
# such as {"logger":"signora_platform.observability.errors","message":"error
# tracking disabled"} — which is an INFO line reporting correct behaviour.
WORKER_LOG="$($COMPOSE logs worker 2>&1)"
if grep -qE '"level":"(ERROR|CRITICAL)"|Traceback \(most recent call last\)' <<<"$WORKER_LOG"; then
  grep -E '"level":"(ERROR|CRITICAL)"|Traceback' <<<"$WORKER_LOG" | head -5
  fail "worker logged an error — see: $COMPOSE logs worker"
fi
pass "workers consuming without error"

RELAY_LOG="$($COMPOSE logs relay 2>&1)"
if grep -qE '"level":"(ERROR|CRITICAL)"|Traceback \(most recent call last\)' <<<"$RELAY_LOG"; then
  grep -E '"level":"(ERROR|CRITICAL)"|Traceback' <<<"$RELAY_LOG" | head -5
  fail "relay logged an error — see: $COMPOSE logs relay"
fi
pass "relay running without error (survived the database restart in stage 6)"

# ================================================== 14b. Provider ingestion

stage "14b. Provider ingestion and normalization"

# The M2.1 and M2.2 demonstrations, run against the live stack. A Provider
# Port implementation is consumed by the real Provider Platform, its raw
# records are translated into canonical claims by Provider Normalization,
# and every claim traces back to the record it came from — with no
# simulation-specific logic anywhere in that path.
if (cd ../backend && \
    SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1 \
    SIGNORA_DATABASE_URL="postgresql+asyncpg://signora:signora@localhost:5433/signora" \
    SIGNORA_TEST_APP_DATABASE_URL="postgresql+asyncpg://signora_app:signora_app_local_dev@localhost:5433/signora" \
    SIGNORA_TEST_ADMIN_DATABASE_URL="postgresql+asyncpg://signora:signora@localhost:5433/signora" \
    uv run pytest tests/integration/test_provider_ingestion.py tests/normalization/test_normalization_pipeline.py -q >/tmp/smoke_ingestion.log 2>&1); then
  pass "$(grep -oE '[0-9]+ passed' /tmp/smoke_ingestion.log | tail -1) against the running stack"
else
  tail -20 /tmp/smoke_ingestion.log
  fail "provider ingestion failed against the running stack"
fi

# ================================================== 14c. Knowledge Graph

stage "14c. Identity resolution"

# The M3A demonstration. Claims from five providers are resolved into
# entities: those sharing a domain reach one entity, one that offers no
# matchable identity stays separate rather than being merged on a
# coincidence, a retired technology's edge is closed rather than deleted,
# and disagreeing claims remain individually retrievable.
#
# The last of those is the point of the whole architecture: the graph adds
# knowledge without destroying evidence.
if (cd ../backend && \
    SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1 \
    SIGNORA_DATABASE_URL="postgresql+asyncpg://signora:signora@localhost:5433/signora" \
    SIGNORA_TEST_APP_DATABASE_URL="postgresql+asyncpg://signora_app:signora_app_local_dev@localhost:5433/signora" \
    SIGNORA_TEST_ADMIN_DATABASE_URL="postgresql+asyncpg://signora:signora@localhost:5433/signora" \
    uv run pytest tests/knowledge_graph -q >/tmp/smoke_graph.log 2>&1); then
  pass "$(grep -oE '[0-9]+ passed' /tmp/smoke_graph.log | tail -1) against the running stack"
else
  tail -20 /tmp/smoke_graph.log
  fail "identity resolution failed against the running stack"
fi

# ================================================ 14d. Observation Engine

stage "14d. Change detection"

# The M3B demonstration. The assertion that matters most is the negative
# one: running the same sync twice produces zero new observations. A
# change-detection engine that fires on a no-op sync is worse than none,
# because every downstream stage would react to noise it cannot tell from
# signal.
if (cd ../backend && \
    SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1 \
    SIGNORA_DATABASE_URL="postgresql+asyncpg://signora:signora@localhost:5433/signora" \
    SIGNORA_TEST_APP_DATABASE_URL="postgresql+asyncpg://signora_app:signora_app_local_dev@localhost:5433/signora" \
    SIGNORA_TEST_ADMIN_DATABASE_URL="postgresql+asyncpg://signora:signora@localhost:5433/signora" \
    uv run pytest tests/observation_engine -q >/tmp/smoke_observation.log 2>&1); then
  pass "$(grep -oE '[0-9]+ passed' /tmp/smoke_observation.log | tail -1) against the running stack"
else
  tail -20 /tmp/smoke_observation.log
  fail "change detection failed against the running stack"
fi

# ============================================== 14e. Business Event Engine

stage "14e. Business event detection"

# The M4 demonstration. Observations become typed business events written
# in language a CRO would recognise — and every threshold that decided
# them lives in the versioned taxonomy rather than in a rule.
if (cd ../backend && \
    SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1 \
    SIGNORA_DATABASE_URL="postgresql+asyncpg://signora:signora@localhost:5433/signora" \
    SIGNORA_TEST_APP_DATABASE_URL="postgresql+asyncpg://signora_app:signora_app_local_dev@localhost:5433/signora" \
    SIGNORA_TEST_ADMIN_DATABASE_URL="postgresql+asyncpg://signora:signora@localhost:5433/signora" \
    uv run pytest tests/business_event_engine -q >/tmp/smoke_business.log 2>&1); then
  pass "$(grep -oE '[0-9]+ passed' /tmp/smoke_business.log | tail -1) against the running stack"
else
  tail -20 /tmp/smoke_business.log
  fail "business event detection failed against the running stack"
fi

# ================================================= 15. Security Invariants

stage "15. Security Invariants"

# LAST: the suite truncates every table between tests, so anything asserted
# after it would be asserted against an empty database. The consent flag is
# required by the suite itself — this stack is disposable, a deployed one is
# not.
if (cd ../backend && \
    SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1 \
    SIGNORA_DATABASE_URL="postgresql+asyncpg://signora:signora@localhost:5433/signora" \
    SIGNORA_TEST_APP_DATABASE_URL="postgresql+asyncpg://signora_app:signora_app_local_dev@localhost:5433/signora" \
    SIGNORA_TEST_ADMIN_DATABASE_URL="postgresql+asyncpg://signora:signora@localhost:5433/signora" \
    uv run pytest -m security_invariant -q >/tmp/smoke_invariants.log 2>&1); then
  pass "$(grep -oE '[0-9]+ passed' /tmp/smoke_invariants.log | tail -1) against the running stack"
else
  tail -25 /tmp/smoke_invariants.log
  fail "Security Invariants failed against the running stack"
fi

# ============================================================= 16. Teardown

stage "16. Teardown"

$COMPOSE down -v --remove-orphans >/dev/null 2>&1 || fail "teardown failed"
LEFTOVER="$(docker ps -a --filter 'name=signora-prod' --format '{{.Names}}' | wc -l)"
[[ "$LEFTOVER" == "0" ]] || fail "$LEFTOVER container(s) left behind"
pass "stack removed, no orphans"

SMOKE_KEEP_STACK=1  # already torn down; stop the trap doing it again
trap - EXIT

printf '\n\033[32m\033[1mPLATFORM SMOKE TEST PASSED\033[0m  (%ds)\n' "$((SECONDS - STARTED_AT))"
printf 'Build · startup · migrations · identities · image hygiene · health · readiness ·\n'
printf 'auth · JWT · authorization · RLS · event bus · relay · workers · ingestion ·\n'
printf 'normalization · identity resolution · change detection · business events ·\n'
printf 'invariants · teardown\n\n'
