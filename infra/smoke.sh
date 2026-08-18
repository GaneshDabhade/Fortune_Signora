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
API="http://localhost:8100"
FRONTEND="http://localhost:3100"

STAGE=""
STARTED_AT=$SECONDS

# **Where the time actually went.**
#
# The certification record stored one number — `24 stages in 1096s` — and across
# 28 runs that number sat between 104s and 193s twice-excepted: **4830s and
# 1096s, both completing all 24 stages.** Slow, not broken, and neither
# explainable after the fact.
#
# Content was not the cause: the 4830s run changed documentation and one
# frontend test. So the variance is environmental, and a total cannot say which
# environment. **One accumulator on the existing `stage()` is the whole
# instrument** — no new structure, and it answers *which stage* on the next
# occurrence rather than on the one after somebody adds logging.
STAGE_STARTED=$SECONDS
STAGE_TIMES=()

stage() {
  if [[ -n "$STAGE" ]]; then
    STAGE_TIMES+=("$((SECONDS - STAGE_STARTED))|$STAGE")
  fi
  STAGE="$1"
  STAGE_STARTED=$SECONDS
  printf '\n\033[1m%s\033[0m\n' "$1"
}

#: Emits the breakdown, slowest first. **Printed on success and on failure** —
#: a run that died at stage 2 is exactly when the timing of stages 0 and 1
#: matters most.
stage_timings() {
  if [[ -n "$STAGE" ]]; then
    STAGE_TIMES+=("$((SECONDS - STAGE_STARTED))|$STAGE")
  fi
  [[ ${#STAGE_TIMES[@]} -gt 0 ]] || return 0
  printf '\n\033[1mStage timings\033[0m  (slowest first)\n'
  printf '%s\n' "${STAGE_TIMES[@]}" | sort -t'|' -k1 -rn | head -6 |
    while IFS='|' read -r seconds name; do
      printf '  %5ds  %s\n' "$seconds" "$name"
    done
}
pass()  { printf '  \033[32m✓\033[0m %s\n' "$1"; }
fail()  { printf '  \033[31m✗ %s\033[0m\n' "$1"; stage_timings; printf '\n\033[31m\033[1mSMOKE FAILED at: %s\033[0m\n\n' "$STAGE"; exit 1; }

cleanup() {
  local code=$?
  if [[ "${SMOKE_KEEP_STACK:-0}" != "1" ]]; then
    $COMPOSE down -v --remove-orphans >/dev/null 2>&1 || true
  fi
  exit $code
}
SMOKE_BUILD_LOG="$(mktemp -t smoke-build-XXXXXX.log)"
trap cleanup EXIT

http_code() { curl -s -o /dev/null -w '%{http_code}' "$@" || true; }

mint_token() {
  local priv
  priv="$(python3 -c "
import re, pathlib
t = pathlib.Path('.env.prod-local').read_text()
print(re.search(r'SIGNORA_JWT_PRIVATE_KEY=\"(.*?)\"', t, re.S).group(1))")"
  (cd ../frontend && npx tsx tests/contract/mint-token.ts \
     "$priv" "http://localhost:3100" "signora-api" ${1:-} 2>/dev/null)
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

# ⛔ **The output is KEPT, and B-188 is what discarding it cost.** This read
# `>/dev/null 2>&1`, so a failure printed *"production images failed to build"*
# and nothing else — **and a transient Docker hiccup is then indistinguishable
# from a genuine compile error.** ⚡ QE had to re-run the build by hand to learn
# that the tree was fine, which is the one thing a gate exists to save you.
#
# ⚠️ **[B-140](../docs/BUGS.md) is the same defect in a different stage** — *a
# failing gate reported its verdict and discarded its evidence.*
if ! $COMPOSE build >"$SMOKE_BUILD_LOG" 2>&1; then
  printf '\n  \033[31m--- last 40 lines of the build ---\033[0m\n'
  tail -40 "$SMOKE_BUILD_LOG" | sed 's/^/    /'
  printf '\n'
  fail "production images failed to build (full log: $SMOKE_BUILD_LOG)"
fi
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
CLAIMS="$(printf '{"sub":"3f6c8a1e-0000-4000-8000-000000000001","iss":"http://localhost:3100","aud":"signora-api","exp":9999999999}' | base64 -w0 | tr '+/' '-_' | tr -d '=')"
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

# ⛔ **`slug` is required and this script did not send it** — B-1024, found by
# QE running this gate against a candidate that had added the field. **The API
# changed underneath its caller**, and this is the only gate that exercises the
# real API over HTTP, which is why every type check and unit suite stayed green.
#
# ⚠️ **Not fixed by defaulting the field.** 📁 A slug is *"permanent once
# created"* (screen `03`) and the API deliberately refuses to invent one: *"the
# client suggests, a person edits, and the value stored is the one they
# accepted."* ✅ **This script sends one, as a browser would.**
#
# ⚡ **Derived per run, and a fixed value would also work HERE** — measured:
# `smoke.sh:135` runs `down -v --remove-orphans` before `up -d --wait`, so every
# run starts on an empty volume. ⛔ **`disaster-recovery.sh` does not** — it
# restarts services against a stack that is already up, so its database persists
# and a fixed slug fails with `WorkspaceSlugTakenError` on the second run.
# ✅ **One habit across both gates**, rather than remembering which lifecycle
# each has. `$$` is the shell's own pid and needs no clock.
SMOKE_SLUG="smoke-test-workspace-$$"
CREATED="$(curl -s -X POST $API/workspaces -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{\"name\":\"Smoke Test Workspace\",\"slug\":\"$SMOKE_SLUG\"}")"
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

# ===================================================== 14f. Signal Engine

stage "14f. Commercial interpretation"

# The M5A demonstration, and the first stage that is not globally true.
# Two workspaces read byte-identical business events differently, each
# explains itself in two halves, and each can be challenged independently.
if (cd ../backend && \
    SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1 \
    SIGNORA_DATABASE_URL="postgresql+asyncpg://signora:signora@localhost:5433/signora" \
    SIGNORA_TEST_APP_DATABASE_URL="postgresql+asyncpg://signora_app:signora_app_local_dev@localhost:5433/signora" \
    SIGNORA_TEST_ADMIN_DATABASE_URL="postgresql+asyncpg://signora:signora@localhost:5433/signora" \
    uv run pytest tests/signal_engine -q >/tmp/smoke_signal.log 2>&1); then
  pass "$(grep -oE '[0-9]+ passed' /tmp/smoke_signal.log | tail -1) against the running stack"
else
  tail -20 /tmp/smoke_signal.log
  fail "commercial interpretation failed against the running stack"
fi

# =============================================== 14g. Buying Score Engine

stage "14g. Commercial attention"

# The M5B demonstration, and the pipeline's first intentional reduction.
# Many live hypotheses become one number — which must reproduce from its own
# ledger exactly, count each business event once, prioritise contradiction
# without netting it, and walk back to a raw provider payload.
if (cd ../backend && \
    SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1 \
    SIGNORA_DATABASE_URL="postgresql+asyncpg://signora:signora@localhost:5433/signora" \
    SIGNORA_TEST_APP_DATABASE_URL="postgresql+asyncpg://signora_app:signora_app_local_dev@localhost:5433/signora" \
    SIGNORA_TEST_ADMIN_DATABASE_URL="postgresql+asyncpg://signora:signora@localhost:5433/signora" \
    uv run pytest tests/buying_score_engine -q >/tmp/smoke_score.log 2>&1); then
  pass "$(grep -oE '[0-9]+ passed' /tmp/smoke_score.log | tail -1) against the running stack"
else
  tail -20 /tmp/smoke_score.log
  fail "commercial attention failed against the running stack"
fi

# ================================================ 14h. Opportunity Engine

stage "14h. Commercial commitment"

# The M6 demonstration, and the pipeline's first workflow stage. Everything
# before it derives; this records that a human committed. The assertions
# that matter: only TRACKING is machine-authored, nothing closes an
# opportunity automatically, and regenerating derived intelligence leaves
# workflow untouched.
if (cd ../backend && \
    SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1 \
    SIGNORA_DATABASE_URL="postgresql+asyncpg://signora:signora@localhost:5433/signora" \
    SIGNORA_TEST_APP_DATABASE_URL="postgresql+asyncpg://signora_app:signora_app_local_dev@localhost:5433/signora" \
    SIGNORA_TEST_ADMIN_DATABASE_URL="postgresql+asyncpg://signora:signora@localhost:5433/signora" \
    uv run pytest tests/opportunity_engine -q >/tmp/smoke_opportunity.log 2>&1); then
  pass "$(grep -oE '[0-9]+ passed' /tmp/smoke_opportunity.log | tail -1) against the running stack"
else
  tail -20 /tmp/smoke_opportunity.log
  fail "commercial commitment failed against the running stack"
fi

# ================================================== 14i. AI Platform

stage "14i. Grounded explanation"

# The M8 demonstration, and the first stage that produces language. It
# deliberately does **not** call a model: `make eval` is the only command in
# this repository that does, and folding a probabilistic run into the
# deployment gate is how a smoke test becomes something people re-run until it
# passes (28-ai-platform.md, "the two-tier guarantee"). Ollama is a
# development runtime and never a production dependency (ADR-0028), so a stack
# built from production images must not need one.
#
# What it proves is the half that *is* deterministic, and it is the half worth
# gating on: the composition root wires, evidence assembles from the real
# pipeline, a grounded narration is stored with complete provenance, the event
# reaches the outbox — and an invented proposition is refused rather than
# stored. That last one is the milestone's real demonstration: the guard is
# deterministic even though the thing it guards is not.
if (cd ../backend && \
    SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1 \
    SIGNORA_DATABASE_URL="postgresql+asyncpg://signora:signora@localhost:5433/signora" \
    SIGNORA_TEST_APP_DATABASE_URL="postgresql+asyncpg://signora_app:signora_app_local_dev@localhost:5433/signora" \
    SIGNORA_TEST_ADMIN_DATABASE_URL="postgresql+asyncpg://signora:signora@localhost:5433/signora" \
    uv run pytest tests/ai_platform -q >/tmp/smoke_ai_platform.log 2>&1); then
  pass "$(grep -oE '[0-9]+ passed' /tmp/smoke_ai_platform.log | tail -1) against the running stack"
else
  tail -20 /tmp/smoke_ai_platform.log
  fail "grounded explanation failed against the running stack"
fi

# ============================================ 14j. AI Reasoning Engine

stage "14j. Defensible conclusion"

# The M9 demonstration, and the first stage that produces something a customer
# may *disagree* with rather than merely learn from. Like 14i it deliberately
# does **not** call a model: `make eval` is the only command in this repository
# that does, and a deployment gate needing a GPU is a gate people learn to skip.
#
# What it proves is the claim M9 exists to make: **twelve of the fifteen parts
# of a Decision Package are assembled from real pipeline rows without a model
# having said anything.** Support, temporal, alternative readings, limitations
# and validation all come from modules that already owned those facts, so a
# failure to reach a model degrades the package rather than emptying it.
#
# It also gates the release rule on the request path: `reasoning@1` is authored
# and unreleased, so `Reason.execute` refuses it and stores nothing. That
# refusal is the rule working, and it is asserted rather than worked around.
if (cd ../backend && \
    SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1 \
    SIGNORA_DATABASE_URL="postgresql+asyncpg://signora:signora@localhost:5433/signora" \
    SIGNORA_TEST_APP_DATABASE_URL="postgresql+asyncpg://signora_app:signora_app_local_dev@localhost:5433/signora" \
    SIGNORA_TEST_ADMIN_DATABASE_URL="postgresql+asyncpg://signora:signora@localhost:5433/signora" \
    uv run pytest tests/ai_reasoning_engine -q >/tmp/smoke_ai_reasoning.log 2>&1); then
  pass "$(grep -oE '[0-9]+ passed' /tmp/smoke_ai_reasoning.log | tail -1) against the running stack"
else
  tail -20 /tmp/smoke_ai_reasoning.log
  fail "defensible conclusion failed against the running stack"
fi

# ============================================ 14k. AI Research Engine

stage "14k. Researched account"

# The M10 demonstration: a provider payload becomes a research artifact —
# findings derived, brief written, all of it stored and announced. Like 14i and
# 14j it deliberately does **not** call a model.
#
# What it proves is M10's claim: **every citable thing is deterministic.** The
# findings are computed from real pipeline rows by pure functions; the model
# only chooses which comparisons to run and writes the brief, and neither
# produces a fact anyone may cite. It also gates storage on completion — an
# unreleased synthesis prompt leaves no task row and no findings, rather than a
# run that found things and said nothing.
if (cd ../backend && \
    SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1 \
    SIGNORA_DATABASE_URL="postgresql+asyncpg://signora:signora@localhost:5433/signora" \
    SIGNORA_TEST_APP_DATABASE_URL="postgresql+asyncpg://signora_app:signora_app_local_dev@localhost:5433/signora" \
    SIGNORA_TEST_ADMIN_DATABASE_URL="postgresql+asyncpg://signora:signora@localhost:5433/signora" \
    uv run pytest tests/ai_research_engine -q >/tmp/smoke_ai_research.log 2>&1); then
  pass "$(grep -oE '[0-9]+ passed' /tmp/smoke_ai_research.log | tail -1) against the running stack"
else
  tail -20 /tmp/smoke_ai_research.log
  fail "researched account failed against the running stack"
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

# =========================================== 15b. Cross-tier JWT contract

stage "15b. Cross-tier JWT contract"

# The only check that the two tiers agree on the claim set, rather than each
# agreeing with itself. It lives in the normal suite but **skips silently**
# when the frontend's dependencies are absent, and CI was what used to
# guarantee they were present (ADR-0027). Here a skip is a failure: the stage
# exists to turn "quietly did not run" into "did not pass".
#
# In the destructive tail with the invariants, for the same reason they are
# here: this suite truncates every table between tests, so anything asserted
# after it would be asserted against an empty database.
if (cd ../backend && \
    SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1 \
    SIGNORA_DATABASE_URL="postgresql+asyncpg://signora:signora@localhost:5433/signora" \
    uv run pytest tests/integration/test_jwt_cross_tier_contract.py \
      -q >/tmp/smoke_jwt_contract.log 2>&1); then
  grep -qE '[0-9]+ passed' /tmp/smoke_jwt_contract.log \
    || { tail -5 /tmp/smoke_jwt_contract.log; \
         fail "cross-tier contract test did not run (skipped) — run 'npm ci' in frontend/"; }
  pass "token minted by the real frontend path verifies with the real Python verifier"
else
  tail -15 /tmp/smoke_jwt_contract.log
  fail "cross-tier JWT contract broken — the two tiers disagree on the claim set"
fi

# ============================================================= 16. Teardown

stage "16. Teardown"

$COMPOSE down -v --remove-orphans >/dev/null 2>&1 || fail "teardown failed"
LEFTOVER="$(docker ps -a --filter 'name=signora-prod' --format '{{.Names}}' | wc -l)"
[[ "$LEFTOVER" == "0" ]] || fail "$LEFTOVER container(s) left behind"
pass "stack removed, no orphans"

SMOKE_KEEP_STACK=1  # already torn down; stop the trap doing it again
trap - EXIT

stage_timings

printf '\n\033[32m\033[1mPLATFORM SMOKE TEST PASSED\033[0m  (%ds)\n' "$((SECONDS - STARTED_AT))"
printf 'Build · startup · migrations · identities · image hygiene · health · readiness ·\n'
printf 'auth · JWT · authorization · RLS · event bus · relay · workers · ingestion ·\n'
printf 'normalization · identity resolution · change detection · business events ·\n'
printf 'signals · buying scores · opportunities · grounded explanation ·
defensible conclusion · researched account · invariants · teardown\n\n'
