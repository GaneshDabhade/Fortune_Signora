# 426 — Change-Aware Validation Profiles: evaluation

> **Lane C — Product Office, 2026-08-04.** A governance proposal, evaluated. **Accepted in principle, narrowed in scope, and deferred on the repository's own performance rule.**

## 1 · What `make dr` actually does

**It restarts every component of the running production stack — Postgres, Redis, API, workers — and asserts nothing was lost.** It waits up to 90 seconds for API readiness and **re-runs 360 Security Invariants after each restart.** Its header states the reason: *"none of it is inferred from the design, because **the design being correct is exactly the claim under test**."*

**It runs under `environment-lease.py`**, so it also serialises against `certify`, `smoke` and `up`.

## 2 · The proposal is already half-built, and the repository drew the line more conservatively

> **A mechanical, path-based classifier already exists and is already trusted with a certification decision.**

| Existing mechanism | What it decides, mechanically |
|---|---|
| **`make certified ARGS="--next-cycle"`** | *"Does anything here change what the software does?"* — **whether a certification cycle is warranted at all** |
| **`certification-guard.py --audit-main`** | Whether a commit is a Closeout — **by checking paths, never commit messages** |

**And the repository already states the motivation the proposal gives:**

> *"Certifying them alone spends a full gate run proving a markdown table is still true, **which is how a team learns to skip cycles** — and the habit of skipping is the one thing this model cannot survive."*

**So the documentation-only case is solved.** A docs commit does not open a cycle, so it never reaches `dr`.

> ⚠️ **And the existing classifier is deliberately more conservative than the proposal would be.** **`infra/` is excluded from the harmless set by name**: *"`smoke.sh`, `disaster-recovery.sh`, `state-check.py` and the compose files decide whether a gate passes, so **changing one changes what certification means**."* **That exclusion was learned from a defect — [B-014](../BUGS.md).** Any profile rule must inherit it rather than re-derive it.

## 3 · What is genuinely new, and it is narrower than the proposal

**With docs already handled, one case remains: an executable change that cannot touch platform resilience.**

**A frontend-only slice is the clear example.** `dr` asserts that Postgres, Redis, the API and the workers survive a restart with nothing lost. **A change to `frontend/` cannot make that claim false**, so running `dr` against it proves nothing about the change — it re-proves the platform.

| Change touches | `dr` |
|---|---|
| `backend/**` · `migrations/**` · **`infra/**`** · compose · `signora_platform/**` | **Always.** *(`infra/` by name — §2)* |
| `frontend/**` only | **The one defensible skip** |
| `docs/**` only | **Never reaches certification** — `--next-cycle` already refuses the cycle |
| **A release candidate, whatever it touches** | **Always** |

> **That is one rule, not a profile system.** A framework of profiles for a single boundary is the speculative abstraction §6 forbids.

## 4 · Why it is deferred, and the trigger is stated

**`CLAUDE.md` §14:** *"Do not add caching, batching, or other performance mechanisms speculatively. **Performance work is justified by the evidence-based triggers in [12-scalability.md](12-scalability.md), not by intuition about what 'might get slow.'**"*

> **No such trigger has fired.** **Nothing in the repository records `dr` as slow, costly or a bottleneck** — its only mentions describe what it proves. **There is no measurement of its duration anywhere.**

**And the current bottleneck is measured and is somewhere else entirely.** As of `797f01f`: **`integration` has not moved in eleven polls**, QE reports `READY FOR NEW WORK: YES` with nothing to validate, and Lane A is idle on three artifacts that never reached `integration`. **Certification duration is not the constraint; certification not being asked for is.**

> **Optimising a stage that is not the constraint moves nothing** — and it spends governance, which is the resource this repository is actually short of.

**The trigger, stated so it is checkable rather than argued:**

> **A measured certification wall-clock that demonstrably delays a promotion, recorded at least twice.** Not *"`dr` feels long"* — **a cycle where the gate run, not the queue, was the reason work waited.**

## 5 · The constraint that must survive whenever it is built

**`make certify` has no options, and that must remain true.**

> *"`make certify` has no options, **deliberately**: a mode that skipped a gate would produce a run that cannot certify, and **a command whose convenient path yields worthless evidence teaches people to use it.**"*

**The proposal is compatible with this and only just.** The distinction is exact:

| | |
|---|---|
| ✅ **Computed** | The suite is derived from the diff, by the same code that already decides whether a cycle is warranted. **No flag, no argument, no human input** |
| ⛔ **Passed** | Any form of `make certify --skip-dr`, or a profile a person selects. **That is the option the constitution refuses** |

**And the certification record must state which profile ran and why.** A record that does not say what it skipped **is not evidence** — it is a claim, and `CLAUDE.md` §2's whole discipline is that the repository must be able to tell the truth about itself. **A certification asserting more than it ran would be the most expensive falsehood this repository could hold.**

## 6 · Recommendation

| | |
|---|---|
| **The principle** | ✅ **Accept.** *"Validation should become smarter, not lighter"* is right, and mechanical-not-discretionary is the correct shape |
| **The scope** | ⚠️ **Narrow to one rule** — `frontend/**`-only skips `dr`; everything else runs it; release candidates always |
| **The implementation** | 🔁 **Reuse `--next-cycle`'s classifier.** **Do not build a second path classifier** — two would eventually disagree, and the one nobody maintains would be the one deciding what to skip |
| **The timing** | ⏸️ **Defer.** §14 — no trigger has fired, and the measured bottleneck is elsewhere |
| **Backlog** | **`SEQUENCED`**, with the trigger named — the pattern [D-042](../DECISION_REGISTER.md) established |

> **The honest summary: the proposal is correct, the repository already implements most of it, and the part that remains has no evidence behind it yet.** **Recording the trigger costs nothing and means the day it fires, nobody has to argue about whether it did.**
