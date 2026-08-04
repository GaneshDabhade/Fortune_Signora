# 405 — Cross-cutting concerns for prepared epics

> **Observability · testing · operations · deployment — for every implementation package Lane C prepares.**
>
> **Written once rather than five times.** These sections were missing from [400](400-epic-c-people.md), [401](401-epic-e1-crm-read.md), [402](402-epic-f-workflow.md), [403](403-epic-d-risk.md) and [404](404-epic-g-copilot.md); duplicating them into each would have created five copies of one fact, which is the drift `CLAUDE.md` §2 forbids. **Each package links here and states only its own deltas** — §6.
>
> **No code was written.** Everything below is what the repository already provides, and the per-epic rows are what a lane must decide **because** it exists.

---

## 1 · The rule that governs this whole document

> **`signora_platform/observability/metrics.py`:** *"Every metric here exists because **a specific decision depends on it**… a trigger nobody can measure is a trigger that never fires."*

**That is the standard, and it is stricter than "add observability."** A package does not earn an observability section by listing logs, metrics and traces. **It earns one by naming the decision each measurement serves.** Everything in §6 is written that way, and anything that could not be is absent.

**The same file names the failure mode worth avoiding:** *"Metric names are fixed here rather than at call sites so dashboards and alerts bind to one definition. **A renamed metric silently empties a dashboard, which reads as 'the system is healthy' rather than as a break.**"*

---

## 2 · Observability — what exists, and what it already guarantees

| Concern | Provided by | The guarantee, in the platform's own words |
|---|---|---|
| **Correlation** | `observability/context.py` — `contextvars` | *"Every line carries correlation context… only tractable if one identifier threads through all of them"* |
| **Structured logging** | `observability/logging.py` (137 lines) | **JSON, with structural redaction** |
| **Secret redaction** | same | *"Redaction is applied **structurally** here rather than left to each call site, because **'remember not to log the token' is a rule that holds until the one time it doesn't**"* |
| **Metrics** | `observability/metrics.py` — 8 pipeline metrics under `signora.*` | Names fixed centrally; see §1 |
| **Tracing** | `observability/tracing.py` — OpenTelemetry, vendor-neutral (ADR-0018) | **Trace continuity across the relay hop** — *"an API request commits an event; a separate relay picks it up; a third worker handles it. Without explicit propagation those appear as three unrelated traces, and the pipeline becomes undebuggable exactly when it is hardest to debug"* |
| **Errors** | `observability/errors.py` — Sentry (ADR-0018) | Receives detail the API deliberately withholds from a customer |

**Existing metrics — reuse before adding:** `signora.outbox.relayed` · `.relay_failures` · `.lag_seconds` · `signora.dispatch.latency_ms` · `signora.events.handled` · `.redelivered` · `.dead_lettered` · `signora.handler.retries`.

> **Any epic consuming or publishing events is already measured end to end.** [Epic F](402-epic-f-workflow.md) in particular should add **nothing** for delivery — the outbox, dispatch and dead-letter metrics already cover the substrate it reuses.

### ⚠️ The gap this backfill found

**Redaction is credential-shaped, and that is all it is:**

```
password | secret | token | authorization | api[_-]?key | private[_-]?key | credential | cookie
```

plus free-text patterns for **JWTs** and **`Bearer …`** — added because *"tokens reach logs most often inside an exception message or a URL rather than as a named field, so key-based redaction alone is not sufficient."*

> **Nothing in that pattern matches a person's name, an email address or a phone number.** **The guarantee *"no line ever carries a secret"* is intact and does not extend to personal data**, because personal data was never in the repository to protect ([Epic C](400-epic-c-people.md) §1 — `EntityKind` has no `PERSON`).
>
> **[Epic C](400-epic-c-people.md) changes that on its first commit.** A `Person` in an exception context, a repository log line, or a Sentry event **puts a real person's name in a log aggregator**, and the module carrying the heaviest compliance obligation would be the one place structural redaction does not reach. **This is a phase-1 obligation, not a hardening task** — the pattern exists to be extended, and doing it after the first `Person` exists is doing it late.

---

## 3 · Testing — the stack, and the parts specific to this repository

**[ADR-0023](adr/0023-testing-strategy.md), Accepted:** **Pytest** + **pytest-mock** + **HTTPX** (async, matching the async application) · **Vitest** · **Playwright**.

**What is not in the ADR and matters more to a prepared epic:**

| Mechanism | What it is | Where it binds |
|---|---|---|
| **Security Invariants** | `backend/tests/security_invariants/` — **tests that parse source as a syntax tree.** `signal_engine`'s refuses any numeric literal in a comparison other than `0` or `1` | **The repository's answer to *"a rule nobody can check is a rule nobody keeps."*** ⚠️ **[B-318](../BUGS.md) finds they match text, so a comment fails one and an alias evades one** |
| **Structural boundary tests** | `tests/commercial_profile/test_boundary.py` — **refuses field names** that would turn a declaration into a scoring model | The pattern [C](400-epic-c-people.md), [F](402-epic-f-workflow.md) and [D](403-epic-d-risk.md) all reuse |
| **Mutation testing** | Used in M9.5 Step B; surfaced a mutation *"that could not be killed at protocol 1"* | Not a standing gate — **used where a guarantee is load-bearing** |
| **Evaluation harness** | `make eval` · `eval-reasoning` · `eval-research` — **releases bind to (model, dataset) pairs** | [G](404-epic-g-copilot.md), and [C-410](../LANE_COORDINATION.md) |
| **Runtime composition** | `make runtime-composition` — *does the deployed worker consume what it declares?* | ⚠️ **Reports 2 of 9 wired** ([TASK-901](../BACKLOG.md)) |
| **Certification** | `make certify` · `certified` · `release-preflight` · `state-check` · `doc-drift` · `coverage-debt` | **QE's, and no lane's to change** |

> **A prepared package does not restate the pyramid.** It names **which guarantee is load-bearing** and **what refuses it structurally** — because a boundary defended only by review is a boundary that survives until the reviewer is busy.

---

## 4 · Operations

| | |
|---|---|
| **Environment leases** | `infra/environment-lease.py`. ⚠️ **[B-317](../BUGS.md) 🟠 — `make test` takes no lease, so two runs in one lane silently collide.** Every package's testing plan inherits this |
| **Disaster recovery** | `make dr` · `infra/disaster-recovery.sh` |
| **Demo / Playground** | `make demo` · `demo-seed` · `demo-narrate`. ⚠️ **[B-319](../BUGS.md) 🟠 — the Playground produces no attribute transitions**, so a shipped capability renders empty ([Epic C](400-epic-c-people.md), A5) |
| **Review environments** | `make review` · `review-status` · `review-end` |

> **Every prepared epic that ships a screen must say what the Playground shows for it.** [B-319](../BUGS.md) is the example that already cost a slice: **the endpoint was correct and its screen would have been empty.** *"Does the demo demonstrate it?"* belongs in a definition of done, not in a bug report afterwards.

---

## 5 · Deployment

**[ADR-0022](adr/0022-devops-infrastructure-and-deployment-topology.md)** — topology · `infra/docker-compose.prod.yml` · **[ADR-0028](adr/0028-model-runtime-by-environment.md)**: **Ollama in development, hosted models in production, and the two are never the same thing.**

> **[C-410](../LANE_COORDINATION.md) is a deployment concern wearing an AI costume.** Every prompt is released for a local model; **production runs hosted ones**, and `require_model` refuses unmeasured pairs. **No prepared epic may assume an AI capability works in production until an evaluation exists for the production model.** [Epic G](404-epic-g-copilot.md) reaches this first and does not own it.

**Migrations:** a new module means a migration, and **[B-400](../BUGS.md) 🔴 is the live example of what goes wrong** — two lanes claimed `0031`, both merge cleanly, and Alembic cannot build the revision map. **Any package adding a table inherits that risk**; the mitigation is sequencing, not cleverness.

---

## 6 · Per-epic deltas

**Only what each epic must decide *because* §2–§5 exist. Every row names the decision the measurement serves.**

### [Epic C · People](400-epic-c-people.md)

| Concern | Delta | Decision it serves |
|---|---|---|
| **Redaction** 🔴 | **Extend the pattern to personal data before the first `Person` exists** (§2) | *Can a name reach a log aggregator?* — today, yes |
| **Erasure** 🔴 | **`ForgetPerson` must be observable.** A silent no-op is worse than no feature | *Did the erasure actually happen?* — a compliance answer, not a debugging one |
| **Metric** | Resolution states: `IDENTIFIED` / `AMBIGUOUS` / `DISPUTED` per run | *Is the identity model working, or quietly guessing?* |
| **Testing** | **Structural test: `Person` and `Member` are not joinable** · scoring-field refusal | Both are boundaries review alone will not hold |
| **Deployment** | New module → migration → **[B-400](../BUGS.md)'s risk** | Sequencing |

### [Epic E1 · CRM read](401-epic-e1-crm-read.md)

| Concern | Delta | Decision it serves |
|---|---|---|
| **Redaction** | **Verify `Credential.__repr__`'s refusal survives the logging path.** The type refuses to render itself; **confirm the JSON encoder honours it** | *Can an OAuth token reach a log?* — the §7 non-negotiable, currently prose |
| **Metric** 🟠 | **Connection state transitions**, especially → revoked/unusable | *A silently dead connection is worse than none* — E1 §10's own edge case, unmeasurable without this |
| **Reuse** | **Sync metrics already exist** via `provider_platform` | Add nothing |
| **Testing** | **Security Invariant: a session token cannot reach an `IntegrationGrant`** (§7) | ⚠️ Note [B-318](../BUGS.md)'s text-matching limitation |

### [Epic F · Workflow](402-epic-f-workflow.md)

| Concern | Delta | Decision it serves |
|---|---|---|
| **Reuse** | **Add nothing for delivery.** Outbox, dispatch, dead-letter metrics already cover the substrate | The whole point of reusing it |
| **Metric** | **Matched-but-undelivered count** | *"This rule matched 14 times; you are not being told about it yet"* — F §2's honesty claim **is** this metric |
| **Metric** | Evaluation latency per triggering event | *When does rule count become a scaling trigger?* |
| **Testing** 🔴 | **Structural: `workflow.rule_matched` is not a valid trigger** · `workflow` imports no other module's application layer | Loop safety and god-module prevention, **both in the type rather than a check** |

### [Epic D · Risk](403-epic-d-risk.md)

| Concern | Delta | Decision it serves |
|---|---|---|
| **Metric** | **`contested` rate across scored accounts** | *Is contradiction being surfaced, or has one posture quietly won?* — the property the whole ledger exists to protect |
| **Operations** | **What does the Playground show for a competitor entry?** (§4) | Avoid [B-319](../BUGS.md) a second time |
| **Testing** | Structural: the competitor declaration carries **no judgement field** | `commercial_profile` records and evaluates nobody |

### [Epic G · Copilot](404-epic-g-copilot.md)

| Concern | Delta | Decision it serves |
|---|---|---|
| **Metric** 🔴 | **Grounding failure rate** — `grounding.py` already calls it *"the one number this platform most needs about itself"* | **Named by the repository, and not yet emitted as a metric** |
| **Metric** | **Refusal rate**, and **cost per question** | *Is refusal working?* · **cost is unmodelled anywhere** — G §7 |
| **Deployment** 🔴 | **[C-410](../LANE_COORDINATION.md)** — no production-model evaluation exists | Blocks customer-facing inference, whichever epic arrives first |
| **Testing** | Refusal on unresolvable citation is **exercised**, not assumed | ADR-0031 cost three releases; *"it validates; it never repairs"* |

---

## 7 · What this backfill did not settle

1. **Whether personal-data redaction is a platform change or Epic C's.** `logging.py` is `signora_platform/`, which [C-010](../LANE_COORDINATION.md) records as **unassignable to any feature lane** — so the fix may not belong to whoever needs it. **Raised, not resolved.**
2. **Whether [B-318](../BUGS.md) weakens the Security Invariants three of these epics rely on.** It is 🟠 and Lane B's; **every package above assumes those invariants hold structurally, and B-318 says they match text.**
3. **Cost observability for AI features.** Nothing measures inference spend today. **Not urgent until [Epic G](404-epic-g-copilot.md) phase 3; genuinely absent now.**
