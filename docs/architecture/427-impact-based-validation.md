# 427 — Repository Impact–Based Validation: the framework

> **Lane C — Product Office, 2026-08-04.** Prepared, not implemented. Supersedes the narrower [426](426-change-aware-validation.md), which evaluated one rule; **this is the framework the product owner directed.**
>
> **The objective is not to run fewer tests.** It is that the repository — not a person — computes which validations a change requires.

## 1 · The crux, found in the certification record

**`REQUIRED_GATES` is a `frozenset` of six**, and the record already enforces the property this framework must not lose:

```python
REQUIRED_GATES: Final = frozenset(
    {"pytest", "mypy", "tsc", "import-linter", "security-invariants", "smoke"}
)

@property
def missing_gates(self) -> frozenset[str]:
    """Required gates this run never executed. **Absence is not a pass.**"""
```

**Its own comment says why:** *"A run recording no gates at all would otherwise satisfy 'every gate passed' vacuously — **the same defect [36-empty-array-checks.md](36-empty-array-checks.md) found in nine shipped CHECK constraints**, where `array_length(x, 1) >= 1` cannot reject the empty array."*

> **So the framework reduces to one change, and one danger.**
>
> **The change:** `REQUIRED_GATES` stops being a constant and becomes **computed from the diff**, recorded in the run.
>
> **The danger:** the vacuity defect returns, one level up. **Today a gate cannot be absent. Under a computed set, a gate can be legitimately absent — and a mis-classification is then indistinguishable from a pass.** The repository has already been bitten by this exact shape nine times.

**Everything else in this document exists to make that one change safe.**

## 2 · Repository Impact Model

**Impact is derived from paths, because paths are the only signal that cannot be misremembered** — the same reason `certification-guard.py --audit-main` checks paths and never commit messages.

| Impact | Triggered by |
|---|---|
| **Platform** | `backend/signora_platform/**` · `infra/docker-compose*.yml` · `infra/postgres-init/**` · **any worker or relay composition** |
| **Persistence** | `backend/migrations/**` · any `__tablename__` change · `tenancy_policy.py` |
| **Module** | `backend/modules/<m>/**` — **and the impact names the module** |
| **Public contract** | `backend/modules/*/public/**` · `apps/api/composition/**` · `pyproject.toml` import contracts |
| **Event** | `domain/events.py` · `06-events.md` |
| **Security · tenancy** | `signora_platform/auth/**` · `policy.csv` · `tenancy_policy.py` · anything under `security_invariants/` |
| **Frontend** | `frontend/**` |
| **Prompt** | `modules/*/prompts/**` · `evaluation/**` |
| **Gate** | ⚠️ **`infra/**` · `Makefile` · `backend/tests/certification/**`** |
| **Documentation** | `docs/**` · `*.md` |

> **Two rules make the model safe rather than clever.**
>
> **① Unknown paths escalate to full.** A path the model does not recognise is **Platform impact by default**, never *none*. **A new directory must not silently reduce validation** — that is how the matrix goes wrong without anybody editing it.
>
> **② A change touching `infra/`, the `Makefile` or the certification package computes the full profile, always.** *"Changing one changes what certification means"* — **the classifier cannot be trusted to classify changes to itself.**

## 3 · Validation Capability Inventory

**Everything that already exists. The framework selects among these; it builds none of them.**

| Capability | Command | What it proves |
|---|---|---|
| **pytest + coverage** | `make test` · floor **95%** | Backend behaviour |
| **Security Invariants** | in `pytest` | Tenancy, auth, RLS, event durability — **permanent, never skippable** |
| **mypy strict** | `mypy --strict` | Backend typing |
| **tsc** · **eslint** | `tsc --noEmit` | Frontend typing |
| **import-linter** | `lint-imports` | **35 contracts** — module boundaries |
| **frontend suite** | vitest · Playwright | Components, e2e, accessibility, consistency |
| **smoke** | `make smoke` | Twelve-factor, health, readiness, structured logging |
| **migration reversibility** | to base and back | Schema |
| **`make dr`** | full stack restart | **Platform resilience — 360 invariants re-run after each restart** |
| **runtime-composition** | `runtime-composition.py` | The deployed worker consumes what a module projects |
| **reachability** | `reachability.py` | A customer can reach the screen |
| **state-check** | `state-check.py` | Documents agree with the repository |
| **doc-drift** | `doc-drift.py` | Documentation matches code |
| **event-catalog** | `event-catalog.py` | Declared events have publishers |
| **coverage-debt** | `coverage-debt.py` | No file at 0% |
| **prompt evaluation** | `make eval*` | `(model, dataset)` pairings |
| **certification** | `make certify` | The record itself |

## 4 · Change → Validation Matrix

**🔒 = always, whatever changed. ● = required for this impact.**

| | Docs | Frontend | Prompt | Module | Contract | Event | Persistence | Security | Platform · Gate |
|---|---|---|---|---|---|---|---|---|---|
| **state-check · doc-drift** | ● | 🔒 | 🔒 | 🔒 | 🔒 | 🔒 | 🔒 | 🔒 | 🔒 |
| **tsc · eslint · frontend suite** | | ● | | | | | | ● | ● |
| **accessibility · consistency** | | ● | | | | | | | ● |
| **pytest + coverage floor** | | | ● | ● | ● | ● | ● | ● | ● |
| **Security Invariants** | | | 🔒 | 🔒 | 🔒 | 🔒 | 🔒 | 🔒 | 🔒 |
| **mypy strict** | | | ● | ● | ● | ● | ● | ● | ● |
| **import-linter** | | | | ● | ● | ● | | ● | ● |
| **event-catalog** | | | | | | ● | | | ● |
| **reachability** | | ● | | ● | ● | | | | ● |
| **runtime-composition** | | | | ● | ● | ● | | | ● |
| **migration reversibility** | | | | | | | ● | | ● |
| **smoke** | | | | | ● | | ● | ● | ● |
| **`make dr`** | | | | | | | ● | ● | ● |
| **prompt evaluation** | | | ● | | | | | | ● |

> **The Security Invariants are 🔒 on every executable profile and are never computed away.** `CLAUDE.md` §11: *"Claude must never delete, skip, or weaken one of these tests… a failure there means a guarantee the architecture depends on has stopped holding."* **A framework that could reason its way out of them would have inverted their purpose.**

**A release candidate runs every row. No computation, no exceptions.**

## 5 · Profiles

**Six, and they are the matrix's columns collapsed — not a separate vocabulary to maintain.**

`documentation` · `frontend` · `prompt` · `module` · `persistence` · `platform` — **plus `release-candidate`, which is *everything* and is not computed.**

**Profiles compose.** A slice touching `frontend/**` and `modules/signal_engine/**` gets the **union**, never the smaller. **Union, never intersection** — stated because the opposite is the single easiest bug to write here.

## 6 · Automation strategy

**Reuse, and there is a lot to reuse.**

| | |
|---|---|
| **Classifier** | **Extend `make certified ARGS="--next-cycle"`**, which already answers *"does anything here change what the software does?"* from paths. **Do not write a second classifier** — two would eventually disagree, and the unmaintained one would be the one deciding what to skip |
| **Record** | **`REQUIRED_GATES` becomes computed and is written into the run.** `missing_gates` then checks against **the computed set**, so *"absence is not a pass"* survives verbatim |
| **Command** | **`make certify` keeps no options.** The profile is computed from the diff; **no flag, no argument, no human input** |
| **Report** | The certification record states **the profile, the impacts detected, and every gate not run with the reason.** **A record that does not say what it skipped is a claim, not evidence** |

## 7 · Risk analysis — the honest part

| | Risk | Mitigation |
|---|---|---|
| **1** | ⚠️ **A mis-classification is indistinguishable from a pass.** The `36-empty-array-checks.md` defect, one level up | **Unknown paths escalate to Platform** · **`infra/`, `Makefile` and the certification package always compute full** · **the profile is recorded, so a wrong one is findable afterwards** |
| **2** | **The matrix becomes stale as the repository grows.** A new module, a new gate, a new directory | **The release candidate runs everything, and it is the matrix's audit** — if a full run catches something the profile would not have, the matrix was wrong and the evidence is in the same cycle. **No scheduled job is needed**, which matters under §20c-2 |
| **3** | **`REQUIRED_GATES` could compute to empty** | **A floor: `state-check`, `doc-drift` and — on any executable change — the Security Invariants are 🔒.** **An empty computed set is a hard failure, never a pass** |
| **4** | **It becomes a lever.** Someone shapes a commit to land in a cheaper profile | **Paths are the input and paths are the change.** A commit that avoids `backend/**` did not change the backend. **The lever and the honest signal are the same thing** |
| **5** | **QE loses independence** — the repository decides what QE runs | **QE still runs the gates and still judges the result.** What moves is *which* gates, and it moves from nobody's decision to a recorded computation. **Today QE cannot skip either; the difference is that the reason becomes inspectable** |

> **The framework's danger is not weaker gates. It is a wrong matrix that nobody notices** — and the release candidate is the only mechanism that can catch that, which is why it must stay unreduced.

## 8 · Migration plan

**Five steps, each independently valuable, none requiring the next.**

| | Step | Value on its own |
|---|---|---|
| **1** | **Emit the impact analysis at every certification, and change nothing else.** The profile is *reported*, and every gate still runs | **Weeks of evidence that the classifier is right, at zero risk** |
| **2** | **Record the computed profile in the certification record**, still running everything | The record starts carrying the data an audit needs |
| **3** | **Apply the profile to `documentation` only** — the case `--next-cycle` already handles | **Smallest possible first cut** |
| **4** | **Apply to `frontend`** — the case [426](426-change-aware-validation.md) argued | |
| **5** | **Apply to the remaining profiles** | |

> **Step 1 is the whole design decision.** **If the classifier disagrees with reality even once during step 1, the framework is not ready** — and finding that out costs nothing, because everything still ran.

## 9 · Governance updates required

**When implemented, not now:**

**`CLAUDE.md` §20e** — *"`make certify` has no options"* stands and gains one sentence: **the required gate set is computed from repository impact and recorded; it is never passed, selected or overridden.** **ADR-0032** is amended for the computed `REQUIRED_GATES` and the profile field. **`QUALITY_ENGINEERING.md`** gains the matrix as the authority for which gates a cycle runs.

**An ADR is required** — this changes what a certification *asserts*, which is the repository's central release guarantee.

## 10 · Recommendation

| | |
|---|---|
| **The framework** | ✅ **Accept.** The design is sound and the reuse is high — **no new capability is built, only selection** |
| **Step 1** | ✅ **Do it when a lane is free.** Reporting impact while running everything is **pure evidence at zero risk**, and it is the only way to earn the rest |
| **Steps 3–5** | ⏸️ **Gated on step 1's evidence**, not on a date |
| **The trigger for steps 3–5** | **The classifier agreeing with the full run across a stated number of consecutive cycles.** Not *"it looks right"* |

> **The proposal's own framing is the right one and worth keeping: validation should become smarter, not lighter.** **Step 1 makes it smarter and not one test lighter** — and it is the step that tells us whether the rest is safe.
