# Session Handoff

> ## Cycle 260 — promoted `47244e79`, 2026-08-22 · **the Settings rebuild, and a divergence that was not one**
>
> **`main` = `47244e79` = the certified commit.** `pytest` **5452** · coverage **95.03%** · **679 Security Invariants** · `mypy` **956** · `import-linter` **37/37** · `tsc` · `frontend-suite` **4023/209** · `eslint` · `smoke` 24/577s · **DR passed** · **reversible in 6s** · head **`0066`**. **13 commits — 11 QE documentation carried from `integration`, plus Lane A's Settings work. FIRST attempt.**
>
> ✅ **Browser 450/458 — 5 failed, 3 skipped. All five also failed on the previous `main`, which had six.** ⚡ **Zero regressions and one fewer failure**: `golden-journey:53` fixed by renaming the tenth invented heading (*"What has happened"* → the design's *"Recent activity"*).
>
> ⚡ **A newer SHA (`8d0ab949`) arrived 21 minutes into the run and was deliberately NOT taken.** 📁 **[ADR-0032](architecture/adr/0032-release-certification.md) binds certification to an immutable commit**, so `integration` moving never invalidates a run in flight. **Verified the delta first — 2 files, zero backend — so nothing recorded against `47244e79` was affected.** ⛔ **Restarting would have discarded 21 minutes AND let a lane extend a run indefinitely by pushing into it.** ✅ **`8d0ab949` is the next cycle's input.**
>
> 🔴 **[C-1547](LANE_COORDINATION.md) — a screen document can contradict the design system, and the screen is not automatically right.** **Settings draws section cards at 16px; `Card` renders 12px; §05 assigns 12px to Card and 16px to the table plane, and §09 says *"12px radius"* in words.** ⚡ **Three signals against one — the primitive is right.** 📁 **Same question as D13-A; rule them together.**
>
> ⚠️ **Still NOT VERIFIED and still [C-1544](LANE_COORDINATION.md)**: the POPULATED state of account narration, AI research and evidence citations. **Their ABSENT states are exercised.** **[B-296](BUGS.md)** is filed and not fixed — the Companies grid applies no `kind` filter, so technology entities render as unnamed companies.

> ## Cycle 259 — promoted `68da093e`, 2026-08-21 · **Lane A's UI conformance work, after four candidates**
>
> **`main` = `68da093e` = the certified commit.** `pytest` **5452** · coverage **95.03%** · **679 Security Invariants** · `mypy` **956** · `import-linter` **37/37** · `tsc` · `frontend-suite` **4010/208** · `eslint` · `smoke` 24/270s · **DR passed** · **reversible in 7s** · head **`0066`**. **5 commits, Lane A.**
>
> ✅ **Browser gate 442/451 — 6 failed, 3 skipped — and all six also fail on the previous `main`, which had ten.** ⛔ **Zero regressions.** ⚠️ **Two apparent regressions were investigated and were CONTAMINATION FROM QE'S OWN REPEATED RUNS** — three suites on one seed left 30 entities and 5 workspaces where a clean seed gives 15 and 1 ([B-1017](BUGS.md)'s mechanism). **17/17 green after a rebuild and reseed. Not filed; QE's fault, recorded rather than charged to the lane.**
>
> 🔴 **[B-1063](BUGS.md) is this cycle's most transferable finding: a certification gate that could not fail on the machine that certifies.** ⛔ **`page-heading-role.test.tsx` read the product owner's uncommitted `Design Documents/` behind `if (!existsSync(path)) return` — reported as a PASS, with `0 skipped`.** ⚡ **Fixed by reading `docs/design-snapshot/` instead, so the hidden input DISAPPEARS rather than becoming visible; QE fire-tested the repair by breaking the string on a machine without the corpus.**
>
> ⚠️ **NOT VERIFIED, and it is [C-1544](LANE_COORDINATION.md), not a defect**: the POPULATED state of **account narration** *(measured — `narrate.py` 0 of 7, "points — Field required")*, **AI research** *(structural, not separately measured)* and **evidence citations** *(unreachable without narration)*. ✅ **Their ABSENT states are fully exercised and covered.** ⛔ **Account validation is NOT affected** — it reads domain-expert catalog prose, not model output.
>
> ⚡ **Four candidates, three refusals, and every refusal was correct.** 📁 **Production stayed byte-identical through two of them, so a refusal cost one browser pass rather than a cycle.**

> ## Cycle 258 — promoted `438447ba`, 2026-08-21 · **the cycle the planner said was not needed**
>
> **`main` = `438447ba` = the certified commit.** `pytest` **5448** · coverage **95.03%** · **679 Security Invariants** · `mypy` **956** · `import-linter` **37/37** · `tsc` · `frontend-suite` **3525/204** · `eslint` · `smoke` 24/203s · **DR passed** · **reversible head→base→head in 5s** · head **`0066`**. **14 commits, QE. ONE attempt.**
>
> 🔴 **`make certified ARGS="--next-cycle"` reported *"No cycle needed"* and the cycle ran anyway, on the product owner's explicit instruction.** ⛔ **All 14 commits are documentation — proven by path, not by commit message: `git diff --name-only main..integration` returned three files, all under `docs/`.** ⚡ **It ran because `main` did not carry the ten defect rows Review 13 produced, and [§20e](../CLAUDE.md) requires `main` to represent the authoritative state.** ⚠️ **Recorded here rather than glossed: the planner and the instruction disagreed, and the instruction is the product owner's to give.**
>
> ⚡ **What reached `main`: Review 13, the full UI conformance audit** — **39 routes · 91 page renders · 13 widths · both themes · 35 design documents parsed · 37 tokens × 2 themes compared by value.** **[B-1050](BUGS.md)–[B-1059](BUGS.md) for Lane A, [B-1046](BUGS.md) reopened, [C-113](LANE_COORDINATION.md) for Lane C, D13-A/B/C for the product owner.**
>
> ⚠️ **The browser gate was NOT re-run and that is deliberate.** **The Validation Planner classified the diff `documentation` and the tree is byte-identical to the previous `main` outside `docs/`** — ⛔ **a Playwright suite cannot observe a change to a markdown file.** ✅ **All eight `REQUIRED_GATES` ran in full; the two the planner named as planned-and-not-recorded are `doc-drift` and `state-check`, both reported by the record itself (B-131).**
>
> 🔴 **The number worth carrying: the audit examined TWENTY candidates, confirmed TEN, and TEN died on re-measurement** — **every one an instrument fault, and one of them was [B-1050](BUGS.md), a row QE had filed and then corrected against itself.**
>
> ⛔ **The board was not reconciled because there was nothing to reconcile** — `--audit-claims` confirms `integration` carried no unpromoted claim commit, so no lane's claim closed in this cycle.

> ## Cycle 257 — promoted `07f22c04`, 2026-08-21 · **a week of instrument work reaches `main`**
>
> **`main` = `07f22c04` = the certified commit.** `pytest` **5448** · coverage **95.03%** · **679 Security Invariants** · `mypy` **956** · `import-linter` **37/37** · `tsc` · `frontend-suite` **3525/204** · `eslint` · `smoke` 24/165s · **DR passed** · **reversible in 5s beside the browser gate** · head **`0066`**. **15 commits, QE. ONE attempt.**
>
> ⛔ **Five things the next session must not misread.**
>
> ⓐ 🔴 **[B-1048](BUGS.md): `&` returns success for LAUNCHING, never for RUNNING.** ⛔ **QE reported *"browser gate started"* when the script did not exist** — a host reboot had cleared `/tmp` — **and polled a 0-byte log for twelve minutes reading *empty* as *still building*.** ✅ **After launching ANYTHING in the background, read its first output before reporting a start.** ⚠️ **Third instance this week of [B-142](BUGS.md)'s family.**
>
> ⓑ ⚠️ **The browser-gate procedure has no home outside `/tmp`.** ✅ **Reconstructible from [`RUNNING.md`](RUNNING.md) in a minute** — ⛔ **but nothing tells you it is missing.** 📁 **Same reboot as [C-112](LANE_COORDINATION.md).**
>
> ⓒ ⚡ **[B-1036](BUGS.md) has four cycles of evidence and the PATTERN is the finding.** **Six specs, and no two runs share the same set** — `connections:32`, `search-journey:18`, `top-bar-search:26`, `confidence:158`, `shell-values:48`, `business-setup:62`. ⛔ **A defect in one spec would recur in that spec.** ✅ **Diagnose with the 7-second re-seed** ([B-1044](BUGS.md)), ⛔ **never by manufacturing load.**
>
> ⓓ ⛔ **`migration-reversibility` and `dr` are STILL not in the certification record.** 📁 **[B-131](BUGS.md)'s field now names them on every run** — 8 gates this cycle, 9 last, `accessibility` correctly dropping with the diff. **Run both by hand every cycle; the record will not remind you, only record their absence.**
>
> ⓔ ⚠️ **[`QUALITY_ENGINEERING.md` §0f](QUALITY_ENGINEERING.md) is the standing rule now** — **classify a certification-speed change BEFORE implementing it.** 🔴 **Class ⑤, contract/semantic, means STOP and escalate**, and [B-1034](BUGS.md) and [C-111](LANE_COORDINATION.md) are the worked examples.
>
> **Open and mine:** [C-111](LANE_COORDINATION.md) · [C-112](LANE_COORDINATION.md) · [B-1039](BUGS.md) · [B-1040](BUGS.md) · [B-1036](BUGS.md) · [B-1042](BUGS.md) · [B-1043](BUGS.md) · [B-131](BUGS.md).
>
> **Open and NOT mine:** [B-295](BUGS.md) *(🔴 schema — `entity` has no FK to `workspace` while ten tables cascade from it; two designs already dismissed work on that cascade)* · [B-1045](BUGS.md) · [B-1035](BUGS.md) · [B-1033](BUGS.md) · [B-289](BUGS.md).
>
> **Next candidate:** ⛔ **none. `integration` == `main` and `lane-qe` is level.**

> ## Cycle 256 — promoted `fa3c78ab`, 2026-08-20 · **the gate measurement that found nothing is being consumed**
>
> **`main` = `fa3c78ab` = the certified commit.** `pytest` **5444** · coverage **95.03%** · **679 Security Invariants** · `mypy` **956** · `import-linter` **37/37** · `tsc` · `frontend-suite` **3525/204** · `eslint` · `smoke` 24/201s · **DR passed, 15 checks** · **reversible in 7s beside the browser gate** · head **`0066`**. **3 commits, QE. ONE attempt.**
>
> ⛔ **Four things the next session must not misread.**
>
> ⓐ 🔴 **[C-111](LANE_COORDINATION.md): 808 events published, 808 relayed, `processed_event` = 0.** ⛔ **`claim()` writes that table before every handler runs, so ZERO means not one event was consumed by any consumer.** **Queues: `read_model` 139 · `intelligence` 29 · `ai_research` 1 · `default` — the key does not exist.** ✅ **The worker is healthy on `default` with 8 subscriptions and zero errors; nothing was ever routed to it.** ⚠️ **`smoke` and `dr` both reported success.** ⛔ **Do NOT correct either gate alone — the right assertion FAILS on today's stack, so gate and environment are ONE change and it needs a ruling.**
>
> ⓑ ✅ **[B-131](BUGS.md)'s field is computed, not stamped — confirmed on a SECOND candidate.** **255 named nine planned-but-unrun gates; 256 names eight, because `accessibility` correctly dropped for a candidate with no frontend change.** ⚠️ **`migration-reversibility` and `dr` are named on BOTH. Run them by hand every cycle; the record will not remind you, only record their absence.**
>
> ⓒ ⚠️ **[B-1037](BUGS.md) was CORRECTED, not closed.** ⛔ **Its original mechanism is DISPROVEN and struck through in the register — do not cite it.** ✅ **The real defect was an empty audit reading as a clean one, and the fix is bounded to `--audit-claims`, the only audit whose printed population differs from its judged one.**
>
> ⓓ ⚡ **Re-run a browser failure ALONE before reporting it.** **This cycle: `confidence:158` and `shell-values:48` passed in isolation ([B-1036](BUGS.md)); `shell-values:214` failed alone too and is real ([B-1045](BUGS.md)).** ⛔ **The decisive test separates a defect from starvation and nothing else does.**
>
> **Open and mine:** [C-111](LANE_COORDINATION.md) *(awaiting a ruling)* · [B-1039](BUGS.md) · [B-1040](BUGS.md) · [B-1043](BUGS.md) · [B-1044](BUGS.md) · [B-1034](BUGS.md) · [B-1036](BUGS.md) · [B-1038](BUGS.md) · [B-1042](BUGS.md) · [B-131](BUGS.md).
>
> **Open and NOT mine:** [B-1045](BUGS.md) *(new — the breadcrumb)* · [B-1035](BUGS.md) · [B-1033](BUGS.md) · [B-289](BUGS.md) · [B-283](BUGS.md)'s remainder.
>
> **Next candidate:** ⚡ **`lane-qe` at `c415ac27`** — C-111's measurement, documentation only, so it **accumulates** rather than warranting a cycle ([§20e](../CLAUDE.md)). ✅ **Lane A holds nothing awaiting certification.**

> ## Cycle 255 — promoted `8524cf0d`, 2026-08-20 · **the record stops being silent, and the suite loses 2.7 minutes without losing a test**
>
> **`main` = `8524cf0d` = the certified commit.** `pytest` **5442** · coverage **95.03%** · **679 Security Invariants** · `mypy` **956** · `import-linter` **37/37** · `tsc` · `frontend-suite` **3525/204** · `eslint` · `smoke` 24/232s · **DR passed, 15 checks** · **reversible in 6s beside the browser gate** · head **`0066`**. **2 commits, QE. ONE attempt.**
>
> ⛔ **Four things the next session must not misread.**
>
> ⓐ ✅ **[B-131](BUGS.md): the certification record now names the gates it did NOT run.** ⚡ **Read it from `manifest.json`, not the log** — `planned_not_recorded`, verified on this very run as the nine `platform`-profile gates including `dr` and `migration-reversibility`. ⛔ **Recorded, never applied**: `satisfied` does not read it, `REQUIRED_GATES` is unchanged, and widening what certification REQUIRES is an [ADR-0032](architecture/adr/0032-release-certification.md) decision. ⚠️ **The deeper fix is UNTAKEN — two mandatory gates still execute outside certification, by hand. Run them by hand every cycle; the record will not remind you, it will only record that they were absent.**
>
> ⓑ ⚡ **Measure, then check the measurement.** 📁 **A 2.7-minute saving came from ONE unbounded wait** — `demo/golden-journey` step 6 called `scrollIntoViewIfNeeded` with no timeout and inherited 180s, while every sibling used 20s. **180.0s → 35.1s.** ✅ **Passing-test time moved FOUR SECONDS (776s → 772s)** — **the whole saving came out of a failing test's patience.** ⛔ **The failure set is unchanged at seven, identical specs.**
>
> ⓒ 🔴 **A near-miss, kept because it is the class this repository keeps finding.** **QE queried `workspace`/`workspace_member`, got `0` and *"relation does not exist"*, and was one step from filing a 🔴 against `make dr` for destroying data while reporting *"Nothing lost"*.** ⛔ **The table is `membership` and `make dr` truncates nothing.** ⚡ **A wrong table name produces evidence indistinguishable from a serious defect** — 📁 and see [B-1044](BUGS.md): re-running one browser spec costs a ~4-minute rebuild, which is why isolation runs are expensive.
>
> ⓓ ⚠️ **Two branches are PRESERVED by product-owner ruling** — **`qe-validate`** ([B-1022](BUGS.md)) and **`qe-candidate`** ([B-1042](BUGS.md)) — **and the three retired Lane C remotes hold 75 commits that exist nowhere else** ([C-110](LANE_COORDINATION.md)). ⛔ **Branch cleanup is evidence preservation first, deletion second.**
>
> **Open and mine:** [B-1039](BUGS.md) *(one worker on the `default` pool — and `notification-arrival`'s 162s is its timeout, the largest remaining item in the browser gate)* · [B-1040](BUGS.md) · [B-1043](BUGS.md) · [B-1044](BUGS.md) · [B-1034](BUGS.md) · [B-1036](BUGS.md) · [B-1037](BUGS.md) · [B-1038](BUGS.md) · [B-1042](BUGS.md) · [B-131](BUGS.md).
>
> **Open and NOT mine:** [B-1035](BUGS.md) · [B-1033](BUGS.md) · [B-289](BUGS.md) · [B-283](BUGS.md)'s remainder.
>
> **Next candidate:** ⛔ **none. `integration` == `main` and `lane-qe` is level.** ✅ **Lane A holds nothing awaiting certification** — its 11 commits are pre-rebase copies, verified.

> ## Cycle 254 — promoted `7a0f21c9`, 2026-08-20 · **the instruments, and the measured proof that fixing tests is the fastest certification**
>
> **`main` = `7a0f21c9` = the certified commit.** `pytest` **5434** · coverage **95.03%** · **679 Security Invariants** · `mypy` **956** · `import-linter` **37/37** · `tsc` · `frontend-suite` **3525/204** · `eslint` · `smoke` 24/167s · **DR passed, 15 checks** · **reversible `head → base → head`** · head **`0066`**. **22 commits, QE. ONE attempt.**
>
> ⛔ **Five things the next session must not misread.**
>
> ⓐ 🔴 **Measure before optimising, and then check the measurement.** ⚡ **QE computed 7.4 minutes of browser-suite overhead and was wrong by TEN TIMES** — the parser mangled multi-minute durations. ✅ **Real figure: 41s, 3%, median test 1.40s.** ⛔ **What costs time is FAILING tests waiting out timeouts — 509s = 42% of cycle 253's suite.** ⚡ **So the largest speed optimisation available is making the suite green, and it weakens nothing.** ✅ **Proven in the same cycle: 509s → 373s, 20.7m → 19.8m, no gate changed.**
>
> ⓑ ⚡ **Browser failures 14 → 7.** [C-109](LANE_COORDINATION.md) cleared three rate-limit journeys, [B-1032](BUGS.md) cleared both `rail-band` tests, and `search-journey`/`top-bar-search` cleared with the load ([B-1036](BUGS.md)). ⛔ **`demo/golden-journey` 180s and `notification-arrival` 162s are now 30% of the suite in TWO tests**, and the second is [B-1039](BUGS.md).
>
> ⓒ ✅ **Migration reversibility is off the critical path and this is NOT a gate change.** **Disposable database on the LANE server (5632); the browser gate is on prod-local (5433).** ⛔ **Different server, different database, no shared state.** ⚡ **12s, measured beside a live browser suite.** 📁 **The runbook block also could not be run as written until this cycle** — it omitted `SIGNORA_TEST_ADMIN_DATABASE_URL` ([B-1041](BUGS.md), fixed on `lane-qe` at `eef5d74b`, **not in this promotion**).
>
> ⓓ ⛔ **The certification record does NOT contain `migration-reversibility` or `dr`.** 📁 The planner reported **nine** gates not recorded for the `platform` profile — *reported only, nothing skipped, nothing refused* ([B-131](BUGS.md)). **Both were run by hand and both passed. Run them by hand every cycle; the record will not remind you.**
>
> ⓔ ⚠️ **Two branches are PRESERVED by product-owner ruling and must not be deleted**: **`qe-validate`** holds an unmerged fix for [B-1022](BUGS.md), and **`qe-candidate`** holds certification records for two runs `main` has no account of ([B-1042](BUGS.md)). ⛔ **The three retired Lane C remotes hold 75 commits that exist nowhere else** ([C-110](LANE_COORDINATION.md)). 📁 **Branch cleanup is evidence preservation first, deletion second** — the ruling's six questions are on each row.
>
> **Open and mine:** [B-1039](BUGS.md) · [B-1040](BUGS.md) *(two gates say "workers consuming" and neither measures a worker)* · [B-1034](BUGS.md) · [B-1036](BUGS.md) · [B-1037](BUGS.md) · [B-1038](BUGS.md) · [B-1042](BUGS.md) · [B-1015](BUGS.md) · [B-1027](BUGS.md).
>
> **Open and NOT mine:** [B-1035](BUGS.md) — ⚡ **and it is a certification-speed item as well as a correctness one**: `client.ts` mints a token per request, so a navigation is ~24 HTTP requests where 12 would do, across ~430 navigations. ⛔ **Communicated to Lane A as information; prioritising it is the product owner's, not QE's** · [B-1033](BUGS.md) · [B-289](BUGS.md) · [B-283](BUGS.md)'s remainder.
>
> **Next candidate:** ⚡ **`lane-qe` at `eef5d74b`, 1 commit.** ✅ **Lane A holds nothing awaiting certification** — its branch carries 11 pre-rebase copies of already-promoted work and rebases at its next Startup.

> ## Cycle 253 — promoted `8a8116d5`, 2026-08-19 · **the top bar against the design, and three failures that were not defects**
>
> **`main` = `8a8116d5` = the certified commit.** `pytest` **5435** · coverage **95.03%** · **679 Security Invariants** · `mypy` **956** · `import-linter` **37/37** · `tsc` · `frontend-suite` **3518/202** · `eslint` · `smoke` 24/228s · **DR passed, 15 checks** · **reversible `head → base → head`** · head **`0066`**. **10 commits, Lane A. ONE attempt.**
>
> ⛔ **Five things the next session must not misread.**
>
> ⓐ ⚠️ **[B-1036](BUGS.md): three specs failed the full run and passed in isolation** — `connections:32`, `search-journey:18`, `top-bar-search:26`, **`13 passed (19.3s)` alone.** ⚡ **`20s · 1.0m · 16.0s` under load against `899ms · 1.9s · 1.4s` alone — a 10–40× slowdown on identical code.** ⛔ **Do not name a mechanism.** **QE reported all three to Lane A as possible defects, including asking whether TASK-1484's own acceptance spec was a complete slice. It was.** ✅ **Re-run a browser failure in isolation BEFORE reporting it.**
>
> ⓑ 🔴 **[B-1040](BUGS.md): `smoke.sh` AND `disaster-recovery.sh` both assert *workers consuming*, and neither measures a worker.** `smoke` tests only *without error*; **`dr` checks `outbox_event WHERE relayed_at IS NULL == 0`, which is the RELAY.** ⛔ **Stages 14b–14k do NOT cover the gap — every one runs `uv run pytest tests/…` straight against the database and never enqueues.** ⚡ **The async dispatch path is asserted end to end by nothing**, which is how [B-1039](BUGS.md) survived 227 runs.
>
> ⓒ ⛔ **[B-1041](BUGS.md): the release checklist's reversibility snippet cannot be run as written** — it omits `SIGNORA_TEST_ADMIN_DATABASE_URL`, which only ever existed inside a `make` target. ✅ **Supply it from `infra/environments.py --exports`, never a hardcoded port** ([B-1003](BUGS.md), [B-1028](BUGS.md)).
>
> ⓓ ✅ **Name the certification working branch `lane-qe-cycleNNN`.** ⚡ **`environments.py` matches `lane-qe-`, so it derives port 5632 with NO `SIGNORA_ENVIRONMENT` override.** ⛔ **`qe-cycleNNN` matches nothing and falls back to 5432 — human review's** ([B-1034](BUGS.md)). ⚠️ **And do NOT set `SIGNORA_ENVIRONMENT` to work around it: `frontend/lib/auth/config.ts` reads the same variable to mean *which deployment is this*, and setting it fails nine frontend tests.**
>
> ⓔ 🔴 **Six QE instrument defects are held on one reasoning** — [B-1034](BUGS.md) · [B-1037](BUGS.md) · [B-1038](BUGS.md) · [B-1039](BUGS.md) · [B-1040](BUGS.md) · [B-1041](BUGS.md), all *"not while a candidate is mid-cycle"*. ⚡ **Correct once; an excuse when it repeats.** ✅ **`lane-qe` is 18 commits ahead and is QE's stated candidate for cycle 254.**
>
> **Open and NOT mine:** [B-1035](BUGS.md) — ⚡ **the mechanism is measured now: `frontend/lib/api/client.ts` calls `fetchAccessToken()` on EVERY request, and that is itself a `POST /api/token`. No cache, no expiry check. One data read is two HTTP requests** · [B-1033](BUGS.md) · [B-289](BUGS.md) · [B-283](BUGS.md)'s remainder.
>
> **Next candidate:** ⚡ **`lane-qe` at `e0c98ec8`+, unless the product owner directs otherwise.** ✅ **Lane A is level with `main` and holds nothing outstanding.**

> ## Cycle 252 — promoted `7fae6e18`, 2026-08-19 · **the notification bell reaches a customer, and the browser gate finds what eight gates cannot**
>
> **`main` = `7fae6e18` = the certified commit.** `pytest` **5435** · coverage **95.03%** · **679 Security Invariants** · `mypy` **956** · `import-linter` **37/37** · `tsc` · `frontend-suite` **3467/199** · `eslint` · `smoke` 24/192s · **DR passed, 679 invariants** · head **`0066`**. **8 commits, Lane A. ONE attempt.**
>
> ⛔ **Five things the next session must not misread.**
>
> ⓐ 🔴 **[B-1035](BUGS.md): 13 access tokens for one page against a deliberate ceiling of 12.** ⚡ **One access token is minted PER DATA REQUEST** — an RS256 signature each, for a token valid for minutes — **and `TASK-495`'s notification `useQuery` (`refetchInterval: 30_000`) is on every authenticated screen.** ⛔ **The ceiling was NOT raised.** 📁 The test states its own purpose: *"set to catch a regression rather than to bless the current number."* ⚠️ **Promoted anyway, and the reasoning is published**: the eight REQUIRED gates are the promotion decision, all eight passed, and `main` already carried five red browser tests. **Holding this candidate to a standard the repository does not apply to itself would have been QE inventing a gate.**
>
> ⓑ ⚠️ **Twelve browser failures, and `12` is right where `13` looks right.** **The output carries 13 `✘` markers; `home-a11y:432` carries `test.fail()`** — Lane A's deliberate [B-289](BUGS.md) holder, **passing by failing.** ⛔ **QE counted markers first and was corrected by the summary line.** **Count what the reporter totalled, not what it printed.**
>
> ⓒ 🔴 **[B-1034](BUGS.md): certification on a `qe-cycleNNN` branch derives NO environment, and `_exports()` then falls back to port 5432 — human review's.** ⚡ **This is [B-1028](BUGS.md) surviving its own fix**: that row removed the literal `5432` from `database.py`; **the derivation replacing it resolves to `5432` on exactly the branches certification runs from.** ✅ **Workaround: `SIGNORA_ENVIRONMENT=lane-qe`** — ⛔ **which `frontend/lib/auth/config.ts` also reads, where it means *"which deployment is this"*, and setting it failed nine frontend tests. One variable, two meanings.**
>
> ⓓ ⛔ **[B-1038](BUGS.md): a failed certification poisons the next attempt and blames the operator.** `append(run)` runs unconditionally, so a failed run dirties `certification/manifest.json`, and attempt two reports *"the working tree was dirty"*. ⚡ **The code comment already calls the required `git checkout -- certification/` a step; [`REPOSITORY_RELEASE_CHECKLIST.md`](REPOSITORY_RELEASE_CHECKLIST.md) does not mention it.** **Run it between attempts.**
>
> ⓔ ⚠️ **[B-1037](BUGS.md): `--audit-claims` reads LOCAL refs** and reported *"0 claim(s) awaiting promotion"* while one plainly was. ✅ **`--audit-main` gets it right in the same run and prints the note.** **`git fetch` before believing either.**
>
> **Open and mine:** [B-1034](BUGS.md) · [B-1037](BUGS.md) · [B-1038](BUGS.md) · [B-1036](BUGS.md) *(observed flake, no mechanism named — deliberately)* · [B-1032](BUGS.md) · [B-1031](BUGS.md) · [B-1030](BUGS.md) *(**cause established: rate limiting**, which that row had recorded as disconfirmed)* · [B-1027](BUGS.md) · [B-1015](BUGS.md). ⚡ **Six of these are FIXED on `lane-qe` and not yet certified** — **15 commits, and five of this cycle's twelve browser failures are already fixed there.**
>
> **Open and NOT mine:** [B-1035](BUGS.md) `frontend/lib/api` · [B-1033](BUGS.md) · [B-289](BUGS.md) · **[B-283](BUGS.md)'s remaining half — FROZEN frontend foundation (§20c), and who does it is not QE's to decide.**
>
> **Awaiting the product owner, blocking nothing:** [C-1535](LANE_COORDINATION.md) *(the background tier — relay + arq — is not started by anything in `infra/`, and `notification-journey.spec.ts` is the only spec that needs it)* · [C-1533](LANE_COORDINATION.md) · [C-1534](LANE_COORDINATION.md). ⚠️ **And `C-109` — raised by QE, on `lane-qe`, NOT yet on `main`**: the suite now waits out the product's rate limiter rather than being refused by it, and **whether the product should exempt a test origin instead is the product owner's.** ⛔ **Deliberately not linked: the anchor does not exist in this file's `main` copy, and a link to a row nobody can open is worse than a sentence.**
>
> **Next candidate:** ⚡ **`lane-a-product-surface-r2` at `10c671d4` — 11 commits, [TASK-1484](BACKLOG.md) `IN VALIDATION`.** ⚠️ **It arrived while this cycle was closing and was NOT chased** — a branch moving during certification is the normal case.

> ## Cycle 251 — promoted `8ceff5d6`, 2026-08-19 · **Home, and a thirteen-day customer crash the browser gate is why anybody knows about**
>
> **`main` = `8ceff5d6` = the certified commit.** `pytest` **5432** · coverage **95.03%** · **676 Security Invariants** · `mypy` **955** · `import-linter` **37/37** · `tsc` · `frontend-suite` **3430/198** · `eslint` · `smoke` 24/166s · **DR passed** · head **`0066`**. **25 commits, Lane A. Two attempts.**
>
> ⛔ **Five things the next session must not misread.**
>
> ⓐ 🔴 **[B-288](BUGS.md): account search crashed for every customer, in every workspace, from 2026-08-06 — thirteen days.** `KIND_LABEL: Record<SearchResultType, string>` is the shape §2 recommends and **the union it was total over had gone stale.** ⚡ **A map total over the wrong set is total and wrong: totality guarantees nothing unless the type it ranges over is DERIVED.** ⛔ **And the journey pointing at it searched for a company the Playground does not have, so it could never have passed** — **a test that cannot pass is not coverage and looks exactly like it.**
>
> ⓑ ⚡ **Migration reversibility ran against DATA and was REFUSED first.** `person_preferences` was empty — the exact table `0065`/`0066` touch — so QE ran the browser suite first to populate it through the product's own doors, then measured: **4 rows, reversible, rows survived.** **Query the table the migration touches, not the database.**
>
> ⓒ ⚠️ **[B-1032](BUGS.md) is QE's own**: `rail-band` returned `232 · 109 · 85 · 61` against `56` — **five frames of a 150ms width transition.** ⛔ **QE reported the `232` to Lane A as possibly a defect; *"reproducible 3/3"* was three samples of one race.**
>
> ⓓ ⚠️ **[B-1033](BUGS.md) is Lane A's**: `home-a11y` is `14/14` green on an empty `recently_viewed` and fails on three real rows — **37px touch target, 0px spacing.** **A test that cannot fail in the case it exists for.**
>
> ⓔ ⛔ **Two refusals, both correct, both the operator's fault.** [B-1031](BUGS.md): the frontend reporter crashed on a post-teardown `window is not defined` and the gate said *"did not report a total"* — **honest; the tests passed.** And **promotion refused because the certification record was in a STASH rather than the tree.**
>
> **Open and mine:** [B-1032](BUGS.md) · [B-1031](BUGS.md) · [B-1030](BUGS.md) four auth journeys, **rate limiting disconfirmed by measurement, no cause named** · [B-1027](BUGS.md) the silent `mode: 'serial'` cap · [B-1015](BUGS.md).
>
> **Open and NOT mine:** [B-1033](BUGS.md) `product_surface` · **[B-283](BUGS.md)'s remaining half — `components/shell/` and the Companies table, FROZEN frontend foundation.** §20c admits it on two of its four exceptions and **who does it is not QE's to decide.**
>
> **Next candidate:** none. `integration == main`. **Lane A returns to the startable backlog.**

> ## Cycle 250 — promoted `7b02364c`, 2026-08-19 · **the browser gate becomes worth running, and the worst defect was in the gate**
>
> **`main` = `7b02364c` = the certified commit.** `pytest` **5378** · coverage **95.03%** · **676 Security Invariants** · `mypy` **949** · `import-linter` **37/37** · `tsc` · `frontend-suite` **3324/192** · `eslint` · `smoke` 24/181s · **DR passed** · head **`0064`**. **7 commits, QE. Eight gates, first attempt.**
>
> ⛔ **Five things the next session must not misread.**
>
> ⓐ 🔴 **[B-1028](BUGS.md): every certification this repository has ever performed created and dropped its database on `localhost:5432` — slot 0, human review's.** `disposable()` runs `CREATE DATABASE` and `DROP DATABASE … WITH (FORCE)`. **Nothing was lost only because the names are always `signora_certify_<sha>`. That is luck.** ⚠️ **THREE instances** — `database.py:71`, `:79`, `release-preflight.py:215` — **and the third was found only because fixing the first was not enough.** 📁 **[B-270](BUGS.md) → [B-287](BUGS.md) → B-1028: one shape, a suite reaching for slot 0 because slot 0 is what a literal spells.**
>
> ⓑ ✅ **The browser suite is now `373 / 16 / 4` from `348 / 36 / 8`, and `373+16+4 = 393` enumerated with ZERO unrun.** **The arithmetic is part of the result** — see ⓒ.
>
> ⓒ ⚠️ **[B-1027](BUGS.md) is OPEN and it is a silent coverage cap.** A `mode: 'serial'` block abandons its tail and counts it as **neither failed nor skipped**; one run reported **385 of 393** and said nothing. ⛔ **Always add the three numbers.**
>
> ⓓ ⚡ **Migration reversibility was run against DATA for the first time** — `head → base → head` on 796 outbox events, 193 claims, 93 observations. ⛔ **`action_batch_transition` held zero rows, so [B-1016](BUGS.md)'s class was NOT exercised**, and the first attempt ran against an empty database and would have been reported as a used one. **Query the row counts.**
>
> ⓔ 🔴 **QE corrected its own row.** B-1016 was filed without reading `0048`'s `downgrade` docstring, which argues the refusal is correct. **Lane A read it independently, determined NOT A DEFECT, and deliberately did not close it.** ✅ **Closed by QE.**
>
> **Open and mine:** [B-1027](BUGS.md) the silent cap · [B-1013](BUGS.md) · [B-1014](BUGS.md) · [B-1025](BUGS.md) · [B-1026](BUGS.md) · [B-1028](BUGS.md) all `FIXED` awaiting independent verification · [B-1015](BUGS.md) the prod restart asymmetry · **four unattributed auth-flow browser failures, claimed as nothing.**
>
> **Open and NOT mine:** [B-1029](BUGS.md) — `rail-band`, `search-journey`, `signal-center` fail alone on a clean environment, `product_surface`. ⛔ **A stale spec and a regressed product produce identical evidence; which it is belongs to the assignee.**
>
> **Next candidate:** **`a9d1d7ea` on `origin/lane-a-product-surface-r2` — 23 commits, rebased and gated by Lane A, `main` an ancestor.** They will rebase once more onto `7b02364c`. **Contract 5 needs an exploratory pass on an untouched workspace; `0065`/`0066` need the used-database run, which is QE's.**

> ## Cycle 249 — promoted `19317ea3`, 2026-08-19 · **the `/attention` guard lands, and a certification record that named a commit the run never began on**
>
> **`main` = `19317ea3` = the certified commit.** `pytest` **5378** · coverage **95.02%** · **676 Security Invariants** · `mypy` **949** · `import-linter` **37/37** · `tsc` · `frontend-suite` **3324/192** · `eslint` · `smoke` 24/158s · **DR passed, 676 invariants against the restarted stack** · head **`0064`**. **4 commits, QE.**
>
> ✅ **The product owner's seventh certification condition now holds.** `frontend/tests/e2e/attention-route-absence.spec.ts` — three `@regression` assertions, all passing, fire-tested by repointing them at a surface that DOES exist.
>
> ⛔ **Four things the next session must not misread.**
>
> ⓐ **Two certification attempts, and the first was DISCARDED BY QE rather than failed by a gate.** [B-1025](BUGS.md): `make certify` on `12c21acb` passed all eight gates and recorded `CERTIFIED 0d61c30a107a` — a commit QE made *while it was running*. **`tree_is_clean()` could not catch it**, and its own docstring says why: *"whether the tree certified was actually stored."* A commit mid-run leaves the tree clean. **Fixed by `refuse_if_head_moved()`, which refuses before the record is written.** ⚡ **It cost nothing that time — 0 non-docs paths differed — and that was luck, not a property.**
>
> ⓑ **The candidate advanced from the SHA the product owner named.** They named `12c21acb`; `19317ea3` was promoted, and **contains it entirely.** The fix for the defect that certifying `12c21acb` exposed is executable, so it had to be inside the certified tree.
>
> ⓒ **[B-1017](BUGS.md) is 🔴 `OPEN` on `main`, promoted over on the product owner's explicit override.** ⛔ **Not a resolution, and the severity was not lowered — not by QE and not by the ruling.** **QE wrote that row, set it 🔴, and 🔴 was the only thing holding the candidate out, so the reclassification was RAISED and not taken.** ⚡ **It is QE's next slice.**
>
> ⓓ **The full browser suite ran for the first time in the repository's history — 392 tests, 24.2m, 348 passing.** **All 36 failures are B-1017 and none is a regression.** ✅ **Decisive test: environment destroyed and rebuilt, the three worst-hit specs alone → 67 passed, 0 failed, one workspace row afterwards.** ⛔ **Ten of those failed in the full run.**
>
> ⚡ **Per-cycle environment isolation is now mandatory and paid for itself immediately.** `down -v` → `up` → `auth:migrate` → `demo:users` → `playground.seed` gave **4 members** against the **57** the shared stack has accumulated. 📁 **[B-282](BUGS.md), the phantom `e2e-recents` connection and [B-284](BUGS.md) all read as product defects and none of them was.**
>
> **Open and mine:** [B-1017](BUGS.md) the browser fixture strategy — **next slice** · [B-1013](BUGS.md) `FIXED` awaiting independent verification · [B-1014](BUGS.md) same · [B-1025](BUGS.md) same · [B-1015](BUGS.md) the prod stack's restart asymmetry · [B-1016](BUGS.md) `0048`'s downgrade, **pre-existing and Lane A's by module**.
>
> **Next candidate:** Lane A reported **nine commits on `943ba3ed`, unpushed** — Home states 01/03/04/05/08/09/13, all six viewports, loading floor and ceiling, customisation, **migrations `0065` and `0066`**. **They belong to the next cycle and were not chased.**

> ## Cycle 248 — promoted `3a18bd96`, 2026-08-18 · **Home implemented, the standalone Attention surface retired, and a gate that had been passing on nothing**
>
> **`main` = `3a18bd96` = the certified commit.** `pytest` **5376** · coverage **95.02%** · **676 Security Invariants** · `mypy` **948** · `import-linter` **37/37** · `tsc` · `frontend-suite` **3324/192** · `eslint` · `smoke` 24/216s · **DR passed** · **reversible** · head **`0064`**. **29 commits, Lane A.**
>
> ⛔ **Two things the next session must not misread.** ⓐ **The first certification attempt was REFUSED** on a failing `smoke` — [B-1024](BUGS.md), a required `slug` whose caller was never updated — **and the refused record is committed rather than discarded.** ⓑ **[B-285](BUGS.md): four `disaster-recovery.sh` assertions were vacuous**, discarding the response with `-o /dev/null`, so a refused create produced a zero outbox count and the gate reported that the relay had resumed. **This cycle is the first run of `make dr` whose assertions were load-bearing.**
>
> ⚠️ **The `/attention` absence guard is on `lane-qe`, NOT in the promoted commit.** **Six of the product owner's seven conditions are satisfied on `main`; the seventh arrives when the guard is promoted.**
>
> ### Previously — cycle 247, promoted `6eba78bf` · **QE's own seven commits, and the standard now exceeds what the gates measure**
>
> **`main` = `6eba78bf` = the certified commit.** `pytest` **5287** · coverage **95.08%** · **668 Security Invariants** · `mypy` **940** files · `import-linter` **37/37** · `tsc` clean · `frontend-suite` **3405/192** · `eslint` clean · `smoke` 24/207s · **DR passed** · **reversible on a clean database** · head **`0060`**. **7 commits, one lane.**
>
> ⛔ **Two things the next session must not misread.** ⓐ **This cycle certified QE's own work and no independent review existed** — the two-lane model leaves QE the only author and the only certifier of certification infrastructure. ⓑ **The certification standard ratified 2026-08-18 names fourteen conditions and the gates measure seven.** **Playwright, browser verification, design conformance and regression-vs-baseline have no gate at all** ([B-131](BUGS.md)).
>
> **Open and mine:** [B-1013](BUGS.md) `FIXED` awaiting independent verification · [B-1014](BUGS.md) same · [B-1015](BUGS.md) the prod stack's restart asymmetry · [B-1016](BUGS.md) `0048`'s downgrade, **pre-existing and Lane A's by module**.
>
> ### Previously — cycles 244–246, promoted `0281e08b`, 2026-08-17 · **three attempts, two correct refusals, and a lane's measurement that overruled QE's**
>
> **`main` = `0281e08b` = the certified commit.** `pytest` **5280** · coverage **95.08%** · **668 Security Invariants** · `mypy` **939** files · `frontend-suite` **3405/192** · `smoke` 24/162s · **DR passed** · **reversible** · head **`0060`**. **41 commits, three lanes.**
>
> 🔴 **Cycle 244 refused: coverage 94.98%.** ⚡ **Predicted in `PROJECT_STATUS.md` five cycles earlier, both halves** — *"the fourth or fifth cycle crosses, and the lane that crosses it will not be the lane that caused it."*
>
> ⛔ **Cycle 245 passed all eight gates and refused to RECORD** — *"the working tree was dirty, so the tree certified was never stored."* ⚡ **The dirty files were cycle 244's own uncommitted outputs; the preflight said so on line 4 and QE read `READY` on line 2.** ✅ **The guard refusing to attest to a tree it cannot store is correct.**
>
> ⚠️ **QE began a SPLIT candidate to promote around the failure** — the product owner asked for whatever could be promoted, and it was cleanly separable. ✅ **Abandoned the moment Lane A's fix landed.**
>
> 🔴 **QE overruled a lane's defect report and the lane was right.** **`make coverage-debt` — QE ran it, it worked, QE told Lane A their report was stale.** ⛔ **QE's `.coverage` was from a run above the floor.** ⚡ **Lane C found the mechanism: `round(total, precision) < fail_under` with `precision` unset, so `round(94.98, 0) = 95.0` and cycle 244 never triggered it.** 📁 **Three parties measured three regions and each named their own as the rule; Lane A's was the only one taken in the condition under discussion.**
>
> ⚠️ **And QE's evidence sent Lane A to the wrong file** — `handlers.py` at 90% (30 missing) rather than `claims.py` at 78% (8 missing). ⛔ **`coverage-debt` ranks by missing lines and never said so**: *which file moves the total* and *which file is least understood* are different questions with one output.
>
> ⚡ **Two rules now name the whole of [B-1000](BUGS.md)'s family, both Lane C's, both applied against Lane C's own work within the hour:**
> ⛔ ***A "cannot reproduce" is a claim about the reproduction attempt, not about the defect.***
> ⛔ ***A failure is a claim about the RUN, not about the code, until you check the conditions the run needed.***
>
> ✅ **The false `infra/` claim QE published at cycle 243 is corrected in `PROJECT_STATUS.md`** — `review.py` alone has 64 test files. ⚡ **Lane C retracted it to one reader; QE had published it to every future one, *because the false version was the more alarming one*.**

> ## Cycle 243 — promoted `cbc71c12`, 2026-08-17 · **two `infra/` defects only the type gate could see**
>
> **`main` = `cbc71c12` = the certified commit.** `pytest` **5225** · coverage **95.04%** · **668 Security Invariants** · `mypy` **935** files · `frontend-suite` **3330/189** · `smoke` 24 stages in **191s** · **DR passed** · **reversible** · head **`0059`**. ✅ **Eight gates, first attempt.**
>
> ⛔ **`decision-queue.py` used `sys.stderr` with no `import sys`, in the file-not-found branch** — **the module loads, every happy path works, and the `NameError` waits for the one run that needed the diagnostic.** ⚡ **`state-check.py` bound one name to two things seventy lines apart.** 🔴 **Both found by `mypy` because **mypy was reading NONE of these files** ([B-435](BUGS.md)) — ⛔ **CORRECTED 2026-08-17: this said the type gate was the WHOLE net and that `infra/` had no suite. Both false — `review.py` alone has 64 test files.****
>
> 🔴 **[B-1000](BUGS.md) took three more instances, and all three were caught by somebody other than QE.** **QE called a lane's branches *"idle"* when they held 22 unpushed commits, and another lane's *"clean"* when its tree held two uncommitted files** — ⚡ ***"'idle' is the word that would have justified an operation that COULD destroy them."*** ✅ **The checks stay; the claims change to *no pushed work*.**
>
> ⚠️ **And the thirteenth is this row's own original failure: cycle 242's Closeout skipped activity 9, the release summary.** ⛔ **Written late and marked as late.** ⚡ **Caught by an `assert count == 1` on an anchored replacement — nothing checks that a cycle published its summary.**
>
> ✅ **[B-1010](BUGS.md) filed**: `reachability` walks route → screen, `runtime-composition` walks projection → worker, **and nothing walks endpoint → frontend consumer.** ⛔ **Recorded, not built** — the freeze wants an observed pattern and this is one observation.

> ## Cycle 242 — promoted `1aaf9678`, 2026-08-16 · **a cycle deferred to protect a lane's session, and the deferral found their stall**
>
> **`main` = `1aaf9678` = the certified commit.** `pytest` **5225** · coverage **95.04%** · **668 Security Invariants** · `mypy` **935** files · `import-linter` **37/37** · **`frontend-suite` 3330 in 189 files** · `eslint` clean · `smoke` 24 stages in **290s** · **DR passed** · **reversible on a clean database** · head **`0059`**. ✅ **Eight gates, first attempt.**
>
> ✅ **[B-436](BUGS.md)'s `None`/`[]` split made behavioural** — the Decorative Logic QE found and the lane repaired rather than deleted.
>
> 🔴 **QE ABORTED its own certification rather than compete for memory with a lane's session.** **199 MB free, swap 4.0/4.0 GB, and a `next-server` at 5.94 GB belonging to an active lane.** ⛔ **The OOM killer would have taken QE's pytest or their session, and buying a green run with somebody else's work is not a trade** — **including indirectly.** ✅ **Nothing was lost: a gate re-runs for free, a session does not.**
>
> ⚡ **The deferral found a defect neither lane was looking for.** 📁 **The lane restarted, recovered 6.8 GB, and discovered a Playwright run that had sat at ZERO BYTES for twenty minutes was thrashing, not slow — the same specs then finished in 46 seconds.** ⛔ ***A run producing no bytes is indistinguishable from one producing them slowly.***
>
> ✅ **A protocol came out of it rather than a sacrifice**: **whoever notices the pressure first says so, and neither side guesses.** **The lane offered the symmetry unprompted.**
>
> 🔴 **A TENTH instrument failure, and it nearly produced a false abort.** **QE's waiter watched the wrong PID** — `ps … | grep "[m]ake certify" | head -1` captured the nohup wrapper, not `make certify`. ⛔ **When the wrapper exited, the log held only the preflight and QE was one step from reporting *certification aborted*.** ⚡ **It had not aborted; it was 85 seconds into pytest.** 📁 **What caught it was instruction 6 — read the error before reporting a verdict — and there was NO error to read. The absence is what exposed the wrong operand.**
>
> ✅ **Three environment hazards recorded in [`RUNNING.md`](RUNNING.md) under one rule — *realign before trusting a red***: a **stamped database above the tree** · a **stale E2E workspace pointer**, where four journeys failed against a screen that was correct · and **exhausted swap**, where a suite that looks slow is not the problem.

> ## Cycle 241 — promoted `d5c84340`, 2026-08-16 · **the lease stops treating a dead pid as proof the machine is free**
>
> **`main` = `d5c84340` = the certified commit.** `pytest` **5225** · coverage **95.05%** · **668 Security Invariants** · `mypy` **935** files · `import-linter` **37/37** · **`frontend-suite` 3330 in 189 files** · `eslint` clean · `smoke` 24 stages in **206s** · scenario **198 assertions** · **DR passed with 668** · **reversible on a clean database** · head **`0059`**. ✅ **Eight gates, first attempt.**
>
> ⛔ **The [C-108](LANE_COORDINATION.md) hold was RESHAPED, not lifted.** **Three TASK-1481 commits touching `signora_platform/` stay held — but they sat at the BOTTOM of the lane's branch, so the hold was also catching [B-436](BUGS.md) and a coordination republish.** 📁 **Product owner: *"don't let it unnecessarily block unrelated implementation."*** ✅ **The lane reordered and named a boundary SHA; QE verified it rather than accepting it.**
>
> 🔴 **A Decorative Logic finding, and an instrument finding worth more.** **`test_none_and_empty_are_not_collapsed` asserted against SOURCE, and the distinction it guarded had no behaviour — `[]` and `None` both reclaimed.** ⚡ **The lane fixed it behaviourally: `[]` reclaims silently, `None` reclaims AND states the bound.**
>
> ⛔ **QE announced a mutation that would have been blind: collapsing `None` into `[]` inside `_running_containers`, which those tests `monkeypatch.setattr` away.** ⚡ **It reports `6 passed` and would have "confirmed" the split was load-bearing.** 🔴 ***A mutation applied to a function the test replaces proves nothing — and it fails GREEN, which is the direction that misleads.*** 📁 **Recorded as [B-1000](BUGS.md)'s eighth instance, and the only one caught before it ran.**
>
> ⚠️ **Certified under a memory-pressure warning and nothing was killed to speed it up** — a 2.1 GB dev server on port 3300 belonged to an active lane. **19 minutes against 8–13 for the previous four.**

> ## Cycle 240 — promoted `6619c162`, 2026-08-16 · **Account 360's Research summary, and the guard repair that stops false cycle warrants**
>
> **`main` = `6619c162` = the certified commit.** `pytest` **5218** · coverage **95.05%** · **668 Security Invariants** · `mypy` strict over **934** files · `import-linter` **37/37** · **`frontend-suite` 3330 in 189 files** · `eslint` clean · `smoke` 24 stages in **250s** · scenario **198 assertions** · **DR passed with 668** · **reversible base→head→base→head on a clean database** · head **`0059`**. ✅ **Eight gates, first attempt.**
>
> ⚡ **Account 360's Research summary is rebuilt to the finalized design with Collapsed and Expanded states, and its journey PASSES HEADED** — [D-134](DECISION_REGISTER.md) performed rather than asserted.
>
> ✅ **[B-1005](BUGS.md)'s repair shipped, path-based as [D-240](DECISION_REGISTER.md) §1 ruled.** **Before: `--next-cycle` called 7 of 8 commits executable, every path markdown or `.toml` under `docs/`. After: *"No cycle needed."*** ⛔ **`docs/coordination/modules.toml` is deliberately excluded — `_audit_claims` reads it, so it is an operand of a gate**, and a suffix widening would have made an ownership change Closeout-legal. 📁 **[B-014](BUGS.md), one directory over.**
>
> ⚠️ **Allowlist rather than denylist, deliberately**: a missed projection costs one unnecessary certification, **a missed gate operand would be absorbed as documentation with nobody deciding it.** ✅ **Fire-tested four ways, each red.** ⚡ **`--audit-main` byte-identical before and after — the repair changes what happens next and rewrites no verdict about the past.**
>
> ⚡ **QE's branch absorbed the rebase this cycle and the lane's was taken untouched.** ⛔ **Cycle 239 did the opposite and moved seven of a lane's commits for a documentation-only branch.** 📁 **The rule QE had argued to Product Office two cycles earlier, finally applied to its own convenience.**
>
> ✅ **The three-cycle coverage fall broke: 95.06 → 95.05 → 95.04 → 95.05.** ⚡ **Reported as a trajectory while falling and as broken now it is not** — **a trend row quietly deleted the moment it stops being alarming teaches a reader that trends are only mentioned when they are bad.**
>
> 🔴 **[B-1000](BUGS.md) was RESCOPED after Lane C produced the seventh instance — `>/dev/null 2>&1` on the one command that reports a silent failure.** ⛔ **Seven instances, two lanes, filed under `Module: QE process` where no other lane would read it.** ⚡ **A repository-wide class scoped to one lane is invisible to the lanes committing it — this row's own defect, applied to itself.**

> ## Cycle 239 — promoted `1dc2c39e`, 2026-08-16 · **a customer is told when Signora finishes researching an account**
>
> **`main` = `1dc2c39e` = the certified commit.** `pytest` **5199** · coverage **95.04%** · **668 Security Invariants** · `mypy` strict over **933** files · `import-linter` **37/37** · **`frontend-suite` 3324 in 189 files** · `eslint` clean · `smoke` 24 stages in **229s** · scenario **198 assertions** · **DR passed with 668 invariants** · **reversible base→head→base→head on a clean database** · head **`0059`**. ✅ **Eight gates, first attempt.**
>
> 🔴 **`notification` is the first person-scoped table whose policies are deliberately ASYMMETRIC, and QE read them from `pg_policies` rather than from the migration.** **`SELECT` narrows by `recipient_id`; `INSERT` and `DELETE` do not** — ⚡ **a notification is written FOR somebody else, so a recipient predicate on the write would permit notifying nobody but yourself.** ✅ **RLS enabled and forced; registered in both `TENANT_OWNED_TABLES` and `IMMUTABLE_TENANT_TABLES`.**
>
> ✅ **The Security Invariant suite refused the migration's first form** — no `DELETE` grant, argued from immutability. ⛔ **The lane fixed the MIGRATION, not the test**, and recorded the rule: ⚡ ***immutability is a claim about `UPDATE`; it is never a claim about `DELETE`.*** 📁 **Erasability is a property of the tenancy model, not of what a row means.**
>
> 🔴 **Coverage fell a THIRD consecutive cycle: 95.06 → 95.05 → 95.04 against a floor of 95.0.** ⛔ **Four basis points.** ⚡ **Each fall is unremarkable and three monotonic falls is not** — **reported as a trajectory, because the lane that crosses the floor will not be the lane that caused it.** ⚠️ **And `make coverage-debt`, the instrument that would name which files are responsible, is unavailable — its reader exits 2 on `coverage json`.**
>
> ⛔ **QE moved a lane's commits through an ungated shell fallback**: `git merge --ff-only … || git rebase -q …` — the `--ff-only` correctly failed and the `||` rebased `integration`, sitting at the lane's tip, onto `lane-qe`. ✅ **Verified: all seven present, `git cherry` 0 duplicates, prior `integration` still an ancestor.** ⚠️ **[B-1000](BUGS.md)'s SIXTH instance, twenty minutes after the fifth** — **and worse, because the fallback changed what happened next and QE pushed before checking what it had done.**
>
> 🔴 **The deeper error: QE put its own documentation-only branch into a cycle carrying a lane's four slices, when the lane's branch was fast-forwardable alone.** 📁 **The same reasoning QE had given Product Office two cycles earlier — do not make a lane rebase for a batch that blocks nobody — applied to their branch and not to its own.**
>
> ✅ **`git cherry` replaced the hand-rolled patch-id comparison and earned it in one measurement**: the lane's branch read **7 ahead** under `rev-list --count` and **all seven `-`** under `git cherry`. ⚡ **The same false signal that produced [B-1009](BUGS.md), answered in 43ms by a command with no window to get wrong.**
>
> ⚡ **The batch test decided two planning syncs in opposite directions in one session, correctly both times.** ⛔ **Cycle 238's blocked nobody and went second; cycle 239's blocked Lane A's entire remaining sequence and went first, by direct ref push during the gate run.** 📁 **Same rule, opposite outcome — *the test is on the BATCH, never on the class*.**

> ## Cycle 238 — promoted `18036f09`, 2026-08-16 · **per-person notification state reaches `main`, unreachable and saying so**
>
> **`main` = `18036f09` = the certified commit.** ⚡ **Verified against the SHA the guard named, NOT against `integration`** — which had moved to `9023b187` before the promotion, for the second cycle running. `pytest` **5143** · coverage **95.05%** · **651 Security Invariants** · `mypy` strict over **924** files · `import-linter` **37/37** · **`frontend-suite` 3324 in 189 files** · `eslint` clean · `smoke` 24 stages in **219s** · **DR passed with 651 invariants against the restarted stack** · **reversible base→head→base→head on a clean database** · head **`0058`**. ✅ **Eight gates, first attempt.**
>
> 🔴 **The slice's whole guarantee is the PERSON predicate, and QE verified it in PostgreSQL rather than in the migration.** ⛔ **Two colleagues in one workspace are legitimately the same tenant — workspace isolation cannot separate them.** ✅ **From `pg_policies` on a freshly migrated database: `SELECT`, `INSERT` and `DELETE` all carry `workspace_id` AND `user_id`; `relrowsecurity` and `relforcerowsecurity` both `t`; no `UPDATE` policy, and the table is in BOTH `TENANT_OWNED_TABLES` and `IMMUTABLE_TENANT_TABLES`.**
>
> ⚡ **QE asked the lane *before* the branch was offered whether the colleague case was in its 13, and the answer was NO.** ✅ **The lane added it rather than defending the suite** — three assertions, of which ② reads as the second person **with no `user_id` predicate in the SQL**, so it tests the policy rather than the repository's `where` clause. ⛔ **Run as the owner all three pass against a table with no policies at all, and the lane fire-tested that.**
>
> ⚠️ **Coverage fell 95.06% → 95.05% against a floor of 95.0 — five basis points.** ⛔ **Not a finding**: the slice added 359 test lines and 19 invariants *and* domain, repository and contract code. ⚡ **Recorded so the slice that crosses the floor is not a surprise.**
>
> ⛔ **`make certify`'s preflight REFUSED on port 3100 — a container QE left running after cycle 237's DR.** ✅ **The guard refused rather than reclaiming the port.** ⚠️ **`make up` and `make dr` without `make down` is the gap, and a lane needing those ports would have hit QE's leftover rather than their own.**
>
> ⚡ **Both lanes' branches were fast-forwardable and only one could stay that way.** **QE took the feature branch over D-136's stated ordering**, because the alternative forced a five-commit executable rebase on a lane that had rebased fifteen minutes earlier at QE's request. ✅ **Raised with Product Office rather than left to be inferred; their reading is better — D-136's priority exists so no lane works from stale planning, so where none can be, it protects nothing.** ⛔ **With the guard: *the test is on the BATCH, never on the class* — *"planning is usually not urgent"* would recreate [C-422](LANE_COORDINATION.md).**
>
> ⚡ **The rebase changed the measurement**: `5140 + 3` before, **`5143 passed, 1 skipped`** after. **Right by luck, then right by measurement** — the lane's own words, and the clearest case this session for step 4.

> ## Cycle 237 — promoted `2e7f5da6`, 2026-08-16 · **a cycle whose warrant QE believes is a defect, run anyway, and it discharged the release claim**
>
> **`main` = `2e7f5da6` = the certified commit.** ⚡ **Verified against the SHA the guard named, NOT against `integration`** — **which had already moved to `e4e64885` before the promotion ran.** `pytest` **5124** · coverage **95.06%** · **632 Security Invariants** · `mypy` strict over **920** files · `import-linter` **37/37** · **`frontend-suite` 3324 in 189 files** · `eslint` clean · `smoke` 24 stages in **165s** · **DR passed with 632 invariants against the restarted stack** · **reversible base→head→base→head on a clean database** · head **`0057`**. ✅ **Eight gates, first attempt.**
>
> 🔴 **QE certified a cycle it believed was warranted by a defect, and said so rather than skipping it.** ⛔ **`--next-cycle` called `da7d3d7f` executable; it is four planning files, and the classification comes from `.toml` falling through to `platform` ([B-1005](BUGS.md)).** ✅ **Run anyway for two reasons that are not *the tool said so*: defaulting broader is the rule when impact is uncertain, and the promotion discharges [B-1007](BUGS.md).**
>
> ✅ **And it did.** **`--audit-main` refused 3 commits before this cycle and refuses `0` after it** — **1996 commits, 214 certified, 1782 in-snapshot.** ⚡ **The three became ancestors of a certified commit and were reclassified without anybody touching them**, which is why B-1007 was filed rather than left to heal: **a violation that heals silently is one nobody learns from.**
>
> 🔴 **[D-240](DECISION_REGISTER.md) ruled [B-1005](BUGS.md) PATH-based, on QE's counter-example.** ⛔ **The obvious fix — add `.toml` to `CLOSEOUT_SUFFIXES` — is the unsafe one**: `docs/coordination/modules.toml` is read by `certification-guard.py:840` inside `--audit-claims`, **so it is an operand of a gate**, and a suffix widening would let an ownership change reach `main` outside a snapshot. 📁 **[B-014](BUGS.md), one directory over.** ⚠️ **Lane C had framed those files as projections read only by `coordination.py`; the row is corrected.**
>
> ⚡ **A `Planning-Sync` correction reached every lane DURING the certification, without disturbing it.** **`git push origin e4e64885:refs/heads/integration` moves the ref and never the working tree** — so the gates went on measuring `2e7f5da6` while lanes polled `e4e64885`. ⛔ **The pin stayed an ancestor, so `promoted == certified` held.** 📁 **This is what makes D-136's priority class satisfiable at all; [C-422](LANE_COORDINATION.md) cost two days for want of it.**
>
> 🔴 **[B-1008](BUGS.md): the dashboard published cycle 235's Security Invariant count during cycle 236's Closeout** — `458+` where the record it was reading said `632`. ⚠️ **The `+` is the worst part: a hedge makes a stale figure unfalsifiable rather than accurate.** ⛔ **A recurrence — the footnote warning against exactly this was written four cycles earlier, in the same file.** ✅ **Found by re-deriving every figure instead of re-reading any of them, which also caught `443`, `3254/184`, head `0054` and `217s`.**
>
> ⚠️ **Two more were MISLABELLED rather than stale, and no re-measurement would have caught them**: *"60 ADRs"* counted `README.md`, *"148 numbered architecture documents"* counted two unnumbered files. ✅ **59 and 146.** ⚡ **The numbers matched the commands that produced them; the words above them asked for something else.**
>
> 🔴 **CORRECTED — Lane B's BRANCH is stranded; its WORK is on `main`, and this entry said otherwise.** ⛔ **Asserted *"276 test lines never offered to QE"*; the blob on `main` and the blob on `lane-b` are byte-identical (`7fab4469`), and `fd0f55cd`'s patch-id `057beed982b2` is already on `main` as `ba904596`.** ✅ **Only `2e3d33e0`, a claim commit, is genuinely unpromoted.** ⚡ **So there is nothing to adopt because nothing is missing** — the D-240 relevance check is answered without being run. 🔴 **The mechanism ([B-1009](BUGS.md)): `git rev-list --count` is a fact about a REF and QE turned it into a claim about CONTENT, skipping the standing instruction to resolve every *ahead* count by patch-id.** ⚠️ **The mirror of the same cycle's orphaned board SHAs — there the citation resolved and the ref did not; here the ref was stale and the content was promoted. One root: the ref and the content are different operands.** 📁 **Found by Lane A, verified independently by Lane C; QE had told BOTH of them the false version.**
>
> ⚡ **The week's dominant defect family got a fifth and sixth instance, one of them from a lane:** **`assert hasattr(repository, "unread")` passes for the wrong signature, the wrong argument names and the wrong return type** — the three ways a port actually drifts — and **`--audit-claims` checks a ceiling and no floor**, so Lane A's TASK-480 claim was guard-clean and invisible on the board at once. ⛔ **The shape: an instrument answering a checkable question adjacent to the one asked, written by somebody who believed they were checking the real one.**
>
> ⚡ **[TASK-1401](BACKLOG.md): somebody finishing setup lands in their own workspace rather than a placeholder.** 📁 **QE verified the load-bearing claim from the file rather than the summary** — `integration:.../onboarding/exit.ts` line 49 read *"⛔ Not a product decision. It is today's behaviour, held in one place"* above `return '/'`. ✅ **And the journey assertion got STRONGER: `/$|\/business/` passes for a person routed nowhere; `/\/w\/[^/]+\/home$/` says they were routed into their own workspace.**
>
> ✅ **`machine_credentials` is a new bounded context** ([ADR-0414](architecture/adr/0414-machine-credentials-bounded-context.md)). ⚡ **QE checked the 🔴 `04-modules.md` edit against §4 specifically: the section cites the ADR for every boundary including the exclusions, and `05-module-dependencies.md` is UNTOUCHED** — **a module recorded in `04` describes a ratified context; a new dependency EDGE would be a fresh claim and outside the delegation.**
>
> 🔴 **Lane A shipped Decorative Logic into the one slice whose subject is guards, and the fire test caught it.** **A dry-run refusal in `dispatched_on` — removed it, every test stayed GREEN, because a dry run can never be `APPROVED` and the method already refuses anything unapproved.** ✅ **Deleted rather than kept**, and ⚡ **the completeness test deliberately does NOT demand a per-method message, because one would push the next person to re-add the branch just removed** — **a test that recreates the defect it was written after.**
>
> ⚡ ***Two guards with the same message are one guard as far as a test can tell*** — Lane A, after their test matched the CONSTRUCTOR's message and reported it as the METHOD's.
>
> ✅ **QE fire-tested the guarantee the slice rests on.** `__post_init__` holds: `replace()` re-runs construction; `deepcopy`/`pickle` rebuild a state that was already valid and cannot manufacture a forbidden one; `object.__new__` bypasses everything and **is available on every Python object ever written.** ⛔ **No `B-` row.** ⚠️ **But the test answered a narrower question than asked — the risk is the day a repository reconstructs through anything but the constructor, and slice ⓑ inherits it undischarged.**
>
> ⚡ **A lane idle for want of a ruling was unblocked WITHOUT a gate run**: `integration` is a ref, and a direct `git push origin <sha>:refs/heads/integration` moves it without touching the working tree of the machine running the gates. ⛔ **Cycle 235's distinction used correctly rather than broken.**
>
> 🔴 **A blocker was released on doc-comments.** **`TASK-1432`'s release said two files *"both read"* `lib/shell/scope.ts`; neither imports it — one is a markdown link, the other prose.** ⚡ **Lane A caught it and their own first `grep` made the identical mistake one command earlier.** ✅ ***Search what the compiler reads, not what a human wrote.***
>
> ## Cycle 235 — promoted `251f7183`, 2026-08-16 · **a second hosted vendor, and four attempts**
>
> **`main` = `251f7183` = the certified commit**, verified from `ls-remote` after the push. `pytest` **4950** · coverage **95.03%** · **458** Security Invariants · `mypy` strict over **911** files · **`frontend-suite` 3303 in 187 files** · `smoke` 24 stages in 147s · **DR passed** · **reversible base→head→base→head on a clean database** · head **`0057`**. ✅ **Eight gates.**
>
> ⚡ **[TASK-420](BACKLOG.md): a second hosted AI vendor reaches production and NOTHING ABOVE THE PORT MOVED.** **One `if key: register(...)` in the composition, a third contract subclass passing UNMODIFIED, and three vendors getting structured output three genuinely different ways** — a JSON-mode string, a forced tool call, a native `response_format`. ⛔ **`Demo:` UNCONFIGURED rather than unreachable, and the lane drew that distinction itself.**
>
> 🔴 **FOUR attempts. Only attempt 1 is a statement about the commit, and half of it is QE's.** ⛔ **QE pinned `b0048fea`, started `make certify`, and merged another lane's commit into `integration` twenty seconds later** — `make certify` runs in place, so the gates measured `d3cbfa6e` and the run recorded itself there. ⚡ ***A cycle cannot be half-measured at one commit and half at another*** — **the sentence QE had written to Lane C an hour earlier.** **Attempt 2: session ended. Attempt 3: databases down. Attempt 4: a tree that did not move.**
>
> ⚠️ **[B-273](BUGS.md) — the flake attempt 1 found — is diagnosed better by Lane A than by QE's report of it.** **`shouldAdvanceTime: true` was holding `findBy*` up BY making the countdown tick — one option doing two jobs.** ⛔ **Two repairs that looked right and were not are recorded**, including `vi.useFakeTimers()` bare turning nine failures into nine TIMEOUTS — *"a worse signal than the flake"*. ✅ **Fixed with `toFake: ['setInterval','clearInterval']` and a fire test that inserts a real 2-second stall and reproduces the exact message.** ⚡ ***A test that asserts an exact time must own every millisecond that reaches the assertion.***
>
> 🔴 **[B-1006](BUGS.md) filed from the promotion**: `--audit-main` audits a REF using the manifest from the WORKING TREE, and the bounded exception guarantees they disagree at exactly the moment of promotion. **It refused with three real commits named as *"reached `main` without a gate"*; the same audit on the same `main` reads *guarantee holds* from a tree holding the record.** ⛔ **A false refusal and the most alarming sentence the tool can print.**
>
> ⚠️ **Held deliberately out of this cycle: `c42de09e` ([TASK-1401](BACKLOG.md)), because the lane asked for time to watch it headed.** **The request was honoured.**
>
> ## Cycle 234 — promoted `723a0bf2`, 2026-08-15 · **the workspace chooser, and a handoff caught in time**
>
> **`main` = `723a0bf2` = the certified commit**, verified from `ls-remote` after the push. **19 commits, two lanes, one gate run.** `pytest` **4915** · coverage **95.01%** · **458** Security Invariants · `mypy` strict over **910** files · **`frontend-suite` 3303 in 187 files** · `smoke` 24 stages in 222s · **DR passed with 458 invariants** · **reversible base→head→base→head on a clean database** · head **`0057`**. ✅ **Eight gates, first attempt.**
>
> ⚡ **[TASK-1421](BACKLOG.md): a person in two organizations can choose which to work in** — `/workspaces`, **a route four entry rules already dead-ended into.** **[TASK-1473](BACKLOG.md): the rail collapses at 1024–1279 and keeps the choice at 1280+**, fire-tested BOTH ways — *"a one-sided guard would have passed against a rail that is collapsed everywhere."*
>
> 🔴 **Both were returned once, for a missing `Slice-Handoff` rather than a failure.** 📁 **The baseline can only be held and a promoted message is immutable** — **amending while the branch was still the lane's cost one rebase; after promotion it would have cost the baseline permanently.** ✅ **Tree byte-identical; only the messages changed.**
>
> ⚠️ **[TASK-430](BACKLOG.md) built and withdrawn** — an endpoint with eight passing tests and no surface to land on, because an earlier lane had already recorded that the surface should not exist. ⚡ **The reusable half is the ORDERING: the artefacts that say *where this goes* are the same artefacts that say *whether this belongs*, and consulting them last means the work is already built when the answer arrives.**
>
> 🔴 **An authorization suite that would have passed with the authorization deleted.** **Removing `context.authorize` left SEVEN of eight tests green, because `policy.csv` grants `person, read` to BOTH membership roles** — ⛔ **nothing in the file distinguished a checked route from an unchecked one.** ⚡ ***An authorization test proves nothing if every subject in the file holds the grant.*** ✅ **What makes it fixable is the capability layer supplying a subject that holds no grants by construction** ([ADR-0410](architecture/adr/0410-capability-layer.md) §5) — **so any route in this repository can now be tested that way, which was not true before cycle 233.**
>
> ⚠️ **[B-436](BUGS.md): `holder()` silently reclaims a lease whose pid is dead.** **Found by planting a dead-pid record and getting NO output — the absence was the finding.** ⛔ **QE's worked example of the damage was WRONG and is corrected in the row**: `make dr` restarts the *production* stack and a lane's e2e runs against its *own*, so demonstrated cost is zero. ⚡ **What survives is sharper — the lease guards five targets correctly and three vestigially, so the ruling is *guard what is actually shared* rather than *a third behaviour that does not exist yet*.**
>
> ## Cycle 233 — promoted `044fbf30`, 2026-08-15 · **the capability layer, and B-270 closed**
>
> **`main` = `044fbf30` = the certified commit**, `promoted == certified` verified from `ls-remote` after the push. **25 commits from three lanes.** `pytest` **4915** · coverage **95.01%** ⚠️ *(one basis point)* · **458** Security Invariants · `mypy` strict over **910** files · **`frontend-suite` 3284 in 186 files** · `smoke` 24 stages in 213s · **DR passed with 458 invariants against the restarted stack** · **migrations reversible base→head→base→head on a clean database** · migration head **`0057`**. ✅ **Eight gates, first attempt.**
>
> ⚡ **Lane A: ADR-0410's capability layer** (named roles, an effective-permissions preview both ways, `0057`) **and `TASK-1477 ⓐ`'s commercial vocabulary.** **Lane C: B-271** — `environments.py` returned `signora_lane_<name>` for every non-zero slot and **no such database has ever existed**; it now returns `signora` everywhere and **the PORT is the separator.** **QE: B-270, B-1002, B-1003.**
>
> 🔴 **[B-270](BUGS.md) is closed on both halves and its row is the model working.** **Lane A raised the severity to 🔴 on their branch; QE set the status to `FIXED` on theirs; git merged the two lines cleanly** — 📁 `registers.py`: *"🔴 **and** unresolved. A fixed 🔴 is a record, not a blocker."* ⚡ **§2 satisfied in both directions with no trade between the truer row and the shippable one, and QE never had to choose.**
>
> ⛔ **The third destructive path was named by no lane for a full day: `tests/playground/seed.py` imports `DEFAULT_APP_DATABASE_URL` from `conftest` and has no `Makefile` in front of it when run directly** — **which is the exact mechanism in B-270's own title.**
>
> ⚠️ **QE moved off slot 0's cluster.** **`backend/.env` read `localhost:5432/signora_lane_qe`** — QE was one of the four `signora_lane_*` databases it had cited as evidence for `RUNNING.md:324` being their producer. **Now `5632`, migrated to `0057`, Redis off human review's `6379`, 458 invariants passing against its own cluster.**
>
> 🔴 **[B-1005](BUGS.md) filed: two independent classifiers are both blind to `.toml`.** `_is_closeout` passes the prefix and fails the suffix; `IMPACT_RULES` matches no rule and falls through to `platform`. ⛔ **157 of 932 commits in a week — 17% — were planning that the classifier treated as executable**, and it collides with [D-144](DECISION_REGISTER.md)'s *"a planning change that is not published has not been made"* for exactly one lane. ⚡ **The fix is not obviously *add `.toml`*: `_is_closeout` guards what may reach `main` outside a certified snapshot. Same route as B-122 — evidence to the product owner.**
>
> ⚠️ **QE held DR rather than forcing a stale lease.** **The recorded holder's pid was dead and `release --force` was authorised by the tool's own diagnostic; a LIVE e2e run existed that the record knew nothing about.** ⛔ ***A dead pid is evidence about a record, not about the machine.***
>
> ⚡ **The day's practice, from three lanes: a number needs its REF, its PREDICATE and its MAPPING** — and 2026-08-15 produced one failure of each. **Plus Lane A's *grep for an existing MEMBER, never for the type*, and *a wrong count announces itself when something disagrees; a right count answering the wrong question agrees with everything.***
>
> 🟠 **Open for the product owner: who verifies a defect in QE's own test infrastructure, when §20e says the lane that fixed it may not?** **QE fixed half of B-270 and will not stamp it.**
>
> ## Cycle 232 — promoted `9a01139c`, 2026-08-15 · **the promotion gate now refuses a record that skipped a gate**
>
> **`main` = `9a01139c` = the certified commit.** 14 commits — **13 Lane C, 1 QE.** `pytest` **4811** · coverage **95.12%** · **446** Security Invariants · `mypy` strict over **900** files · **`frontend-suite` 3263 in 185 files** · **`eslint` clean** · `smoke` **24 stages in 153s** · **DR passed, 446 invariants against the restarted stack** · reversibility base-and-back at `0056`. ✅ **Eight gates, all recorded.**
>
> ⚠️ **Three runs, and the first two were ABORTS rather than failures** — QE's own `SIGTERM` (`Error 143`) and `release-preflight` `Error 3` *(nothing listening on 5432; containers went down with a session)*. 📁 ***A failure is a statement about the commit; an abort is a statement about the run*** — the tree was byte-identical across all three.
>
> 🔴 **[B-1002](BUGS.md) — the promotion guard's `CERTIFIED` and the certification package's had drifted apart.** `_satisfied()` was a **second implementation** whose docstring claimed parity it did not have. It checked four of five conditions; **the missing one was whether every member of `REQUIRED_GATES` actually ran** — the condition the product owner changed the same morning — and `for gate in run.get("gates") or []` meant **a record with no gates read as satisfied.** ⚡ **That is [B-122](BUGS.md)'s own scenario: `frontend-suite` absent from 228 runs, absence never a failure, every one of them promotable.**
>
> ✅ **Fixed as two NAMED predicates, because there were always two questions.** `_satisfied` — *did this run's recorded gates pass?*, about the past, no required-gate check, deliberately. `_promotable` — *may this be promoted now?*, about today, full check. **Constants imported from `record.py`, never restated.** **Verified: `ac622c24ad30`, a six-gate record, is now REFUSED naming `eslint` and `frontend-suite`.**
>
> ⛔ **QE's stated reason for the split was WRONG and the fire test found it.** QE wrote that making `_satisfied` strict would make `--audit-main` refuse 209 commits on `main`. **It does not** — the audit accepts *an ancestor of a certified commit on `main`*, and a certified tip vouches for everything behind it. ⚡ **The 209 was a real measurement of a quantity the audit never consumes.** **The design survives on the argument the fire test found instead: `certified_all` is EMPTY in the window between a widening and its first passing run, and with nothing to be an ancestor of, every non-Closeout commit becomes a violation at once.** **A historical audit whose verdict depends on a gate added this morning is not a historical audit.**
>
> 🔴 **TWO 🔴 DEFECTS ARE OPEN AND NEITHER IS FIXED ON `main`.** ⛔ **[B-270](BUGS.md): `make test` in a fresh shell truncates human review's database.** `conftest.py` resolves from `os.environ`, not `backend/.env`, and the target passes the destructive-consent flag with **no database variable** — **new shell → documented gate → slot 0 emptied, no mistake required.** ⛔ **[B-271](BUGS.md): `environments.py` derives `signora_lane_<name>` while `docker-compose.yml` hardcodes `POSTGRES_DB: signora`** — **the port from one model, the database from another, so the pair describes no environment that exists.** **Both fixes are prepared on `lane-c-sync`; they land in cycle 233.**
>
> ⚠️ **[B-272](BUGS.md): the coverage instrument under-reports async SQLAlchemy code.** `coverage.py` defaults to `concurrency = thread`; SQLAlchemy runs every database `await` through greenlet. **Lane A measured one file at 64% → 100% on a single config line, same 20 tests, no code changed.** ✅ **So 95.12% is a FLOOR, not a ceiling** — ⛔ **but `coverage-debt`'s worst-offender list is naming async files that are already exercised, and §19 tells every lane to run it before handover.** **QE's, cycle 233, and `fail_under` must be re-cut from the new measurement.**
>
> ⚡ **Nine instances of one defect family were recorded across three lanes this cycle**, and the best statements of it are not QE's: **Lane C — *read around the match rather than counting it*** · **Lane C — *a SHA in a message is a promise not to move the ref*** · **QE — *a parent process that does not need a variable is not evidence that its child lacks one*** · **Lane A's, the cleanest — four diagnostic rounds on a seeder before checking whether the row was there, because their own suite was truncating between its commit and its next read.** ⛔ **Every reading correct; none of them the operand.**
>
> ## Cycle 231 — promoted `136f112b`, 2026-08-15 · **ADR-0411 is complete**
>
> **`main` = `136f112b` = the certified commit.** **Lane A's TASK-1479 ⓶b — Segments — completes ADR-0411**: Tags at TASK-466, Owner/CSM at ⓶a, Segments here. **9 commits, migrations `0055`/`0056`.** `pytest` **4796** · coverage **95.12%** *(up from 95.02 — the first slice this week to raise the floor rather than defend it)* · **446** Security Invariants · `mypy` **899** files · **`frontend-suite` 3263 in 185 files** · **`eslint` clean** · **DR passed** · reversibility clean at head `0056`. ✅ **First attempt, eight gates.**
>
> ⚡ **Lane C's 14 commits replayed to nothing — verified by patch-id, 0 of 14 not already on `main`.** **So the coverage figure is attributable to these nine commits alone.**
>
> 🔴 **A Security Invariant failed once on Lane A's machine and did not reproduce — `test_an_invalid_audience_is_rejected`.** It has now passed in isolation, across the invariant suite in order, in two of their full runs, **and in QE's certification (446 invariants).** ⛔ **Not filed as a defect and not dismissed as a flake.**
>
> **The diagnosis is by mechanism rather than by log, because the log was discarded.** `JwtVerifier.verify` catches `jwt.ExpiredSignatureError` **first** and maps it to `ExpiredTokenError`, which is **deliberately not** an `InvalidTokenError`; PyJWT validates `exp` before `aud`. **Lane A tested it: expired + wrong audience → `ExpiredTokenError`.** ⚡ **So a clock step produces exactly this failure, and `DID NOT RAISE` — the audience check actually weakening — would be deterministic and could not be intermittent.** **One non-reproducing failure is evidence *for* the clock and *against* the guarantee having lapsed.** ⚠️ **Sufficient is not demonstrated, and it stays an open observation.**
>
> ⚠️ **The reusable lesson is Lane A's own and it is about process:** they tailed a gate run to four lines and discarded the diagnostic **on a Security Invariant failure** — *"the one output you cannot regenerate, because the next run is a different run."* **Full output captured for gate runs from now.**
>
> 🔴 **The `Security Invariants: N` figure means less than its name, and this is the first cycle to say so on the dashboard.** **It counts test ids, and only `IMMUTABLE_TENANT_TABLES` is parametrized** — so **registering a tenant-owned table adds assertions and no ids.** **Cycle 231's `+3` was one table entering the immutable set, times three parametrized tests; its three tenant-owned registrations moved it by zero.** ⛔ **A lane citing the count as evidence its registration is not decorative is citing the one figure insensitive to that.** **Measured by Lane C, verified independently.**
>
> ## Cycle 230 — promoted `84cd6ad4`, 2026-08-15 · **what CERTIFIED means changed**
>
> ⚡ **`REQUIRED_GATES` is eight, not six.** **`frontend-suite` and `eslint` are members**, on the product owner's ruling of [B-122](BUGS.md), **and the runner executes them** — the pairing that matters, since adding to the set without running them would fail every future certification on *"required gate did not run"*.
>
> ✅ **Proven by the run, not asserted: `84cd6ad42242` records EIGHT gates** — `frontend-suite` **3254 passed in 184 files**, `eslint` **clean** — **the first time either appears in 229 runs.** The planner's shortfall fell from **11 to 8**.
>
> 📁 **The evidence the ruling rested on**: `385970bf`, cycle 228's certified and promoted commit, **fails `auth-mode.test.ts` deterministically** — reproduced in a clean worktree with `SIGNORA_ENVIRONMENT` unset and no `.env`. **`tsc` passed throughout and could not have caught it: a type-checker sees a wrong type, and this was a wrong assertion.**
>
> ⚠️ **The historical effect is accepted, in the product owner's words: *"the records remain historical records under the gate set that existed at the time; the current derived state may correctly show that they do not satisfy today's expanded gate set."*** **`satisfied` is derived and never stored, and `tsc`'s own addition at `4e43da17` is the worked precedent — it did this to 41 earlier runs without anybody rewriting a record.** ⛔ **No prior certification is withdrawn or re-read.**
>
> ⚡ **QE is allocated `B-1000`–`B-1099`**, recorded in [`CLAUDE.md`](../CLAUDE.md) §20e. **`100`–`199` is exhausted at 98 of 100, and both apparent gaps are live references** — `B-102` with 12 mentions, `B-182` with 2. ⛔ **A gap that is referenced is not free.** **This is the first edit QE has made to `CLAUDE.md` and it was directed rather than drafted.**
>
> ⚠️ **A follow-up, recorded and deliberately not made a blocker on the product owner's instruction:** `--audit-main` reads certification records by commit rather than `satisfied`, and QE has not measured whether widening changes any of its verdicts.
>
> ## Cycle 229 — promoted `ac622c24`, 2026-08-15
>
> **`main` = `ac622c24` = the certified commit.** **26 commits, three lanes** — Lane A's TASK-1479 ⓶a (bulk owner change, migrations `0053`/`0054`), Lane C's coordination and register work, QE's own gate repair. `pytest` **4704** · coverage **95.02%** · **443** Security Invariants · migration head **`0054`** · **DR passed** with 443 against the restarted stack · reversibility clean.
>
> ⚠️ **Second attempt. The first was `NOT CERTIFIED` — coverage 94.78% against the 95.0 floor, with all six gates passing.** ⛔ **The gates were not what failed; the condition was.**
>
> 🔴 **QE's first attribution of that failure was wrong, and the correction is the reusable half.** `coverage json`'s statement arithmetic gives **95.84%** where the gate reports **94.78%**, because **the gate counts branches.** ⛔ **Attributing a branch-coverage failure with a line-coverage sum names the wrong files.** ✅ **Recomputed over `num_statements + num_branches`, which reproduces the gate exactly: the three files the slice added missed 55 where 49 had to close.** **Lane A closed them to 100% and measured 95.02% — the predicted landing to the decimal** — and **held slice ⓶b back themselves** because its files sat at 27–42%.
>
> ⚡ **The reversal guard was fire-tested and it is load-bearing.** Removing both `member_user_id == assigned_to` conditions turns **exactly three red of 29**: *does not overwrite an assignment made since* · *reversing twice does not re-assert a stale holder* · *an absence is only restored if the batch still holds it*. ⛔ **QE selected the wrong test files three times before finding them** — a grep for `restore_previous|ReverseAssignment` never matched `tests/integration/`, where they live. **The claim held; the instrument that checked it did not, three times.**
>
> 🔴 **[B-122](BUGS.md) is the finding that outlives this cycle.** **`frontend-suite` and `eslint` have run in 0 of 227 certification runs**, and **a red frontend suite reached `main` under a CERTIFIED stamp** — `auth-mode.test.ts`, failing since `3eb51f0d`. `tsc` passed throughout and could not have caught it. ⚠️ **QE's own cheap gates had the same hole**; `vitest` now runs before every pin. ⛔ **Adding either to `REQUIRED_GATES` is the product owner's** — and **the objection QE first gave against it does not hold**: `satisfied` is derived and never stored, so widening re-judges history visibly rather than falsifying it, and **`tsc`'s own addition on 2026-08-04 is the worked precedent** *(41 five-gate runs before it, zero after — a four-minute boundary)*.
>
> ⚠️ **QE allocated two identifiers from Lane A's block and its own check caught it.** `B-200`/`B-201` collided with existing rows; renumbered to **`B-122`**. **The cause was the week's pattern in the search that chose the number** — grepping `^### B-1[0-9]{2}`, seeing `B-199`, and taking `200`. 🔴 **And QE's block is exhausted: 97 of 100 used, two of the three gaps live references, zero free. Raised for a ruling; QE will not grant itself a range.**
>
> ## Cycle 228 — promoted `385970bf`, 2026-08-14
>
> **`main` = `385970bf` = the certified commit.** **14 commits, two lanes** — Lane A's ADR-0412 ⓵b and C-298, Lane C's C-1433 and the B-433 reconciliation. `pytest` **4641** · coverage **95.03%** · **443** Security Invariants *(up 21)* · migration head **`0052`**. **DR passed** — 443 against the restarted stack. **Reversibility clean.** ✅ **First attempt, no aborts.**
>
> ⚡ **ADR-0412 is implemented and verified by running it, not by reading it.** `SIGNORA_ENVIRONMENT` is a closed `SignoraEnvironment` enum on a required field. **Six inputs checked**: `lane-a` and `development` and `""` each raise a `ValidationError` naming the vocabulary · **genuinely missing raises `Field required [type=missing]`**, which is §2's *"a missing value FAILS, it does not default"* · `local` is accepted · **`production-local` is accepted by the vocabulary and then refused by the registry**, which is the correct layering — the value is legal, the mock may not serve there.
>
> ✅ **Lane A's claim that `production-local` needs no gate change is verified both ways** — `smoke` (24 stages, inside certification) and `dr` both pass untouched.
>
> 🔴 **QE returned the slice twice before pinning, and both were worth the round trip.**
>
> **① The new Security Invariant tested a copy of the registry.** `test_no_stack_name_is_a_member_of_the_deployment_vocabulary` hand-listed **six** stack names where `BY_NAME ∪ UNSLOTTED` holds **nine**. **Fire-tested: a future `lane-d` or `lane-e` collision would have passed SILENTLY.** ⛔ **The same defect as [B-199](BUGS.md) and [B-434](BUGS.md) — a hand-maintained copy of a registry — but in a Security Invariant, where a guard that tests a copy still looks like a guard.** ✅ **Now derived; `lane-f` is covered without anybody remembering.**
>
> **② `mypy --strict` failed at the certification scope.** ⚠️ **The lane's gate checked 571 files; certification checks 882** — the 311-file gap is `tests/` and `apps/`, **and the change broke a test.** ⛔ **`strict = true` is already project-wide, so naming paths was pure narrowing with no compensating benefit.** ⚡ **Fixed without widening the `type: ignore`** — assigning a typed member keeps `[assignment]` live rather than switching a whole error class off on that line.
>
> ⛔ **Neither was excluded.** §20e says a failing gate excludes a slice; **a live lane with a one-line fix is a faster path to the same correctness, and excluding would have held Lane C's nine commits behind a defect that was not theirs.**
>
> ⚠️ **A QE sequencing error, corrected mid-cycle:** the first candidate was pinned *before* the gates ran on the assembled tree, so it was discarded when `mypy` failed. **Gates first, then pin.**
>
> ⚡ **The recurring defect of this cycle and the last, named nine times: an instrument answering a narrower question than the one asked.** A password check on whole literals · a redaction probe blind to a sink that renders no fields · a degeneracy predicate asking *empty* instead of *collides* (7 of 8, not 6) · a disjointness measurement against an inferred vocabulary · **a commit count whose two sides were read backwards** · a removal predicate matching state commits · a Security Invariant's hardcoded list · a lane's type gate scoped below the deciding one · **and a missing-value test where `.env` supplied the operand I had removed.** **Every one found by somebody other than its author, which is now the argument for the pairing rather than an observation about it.**
>
> ## Cycle 227 — promoted `da7d5e3e`, 2026-08-14
>
> **`main` = `da7d5e3e` = the certified commit.** **14 commits from three lanes** — Lane A's `TASK-429` and `B-267`, Lane C's D-236 follow-ups, QE's `B-434`. `pytest` **4603** · coverage **95.03%** · **422** Security Invariants *(up 16)* · migration head **`0052`**. **DR passed** — 422 invariants against the restarted stack. **Reversibility head→base→head clean.**
>
> ⚠️ **Second attempt. The first ABORTED on the environment lease and that is a statement about the run, not the commit.** Lane A held it for a test run; the pid was gone but *"may be stale"* is not *"is dead"*, so it was **not** force-released. **The lease cleared itself.** 📁 Its own message names the precedent: *cycle 25 recorded `pytest 134 passed` against a suite of 2589 because another run truncated its database mid-suite.*
>
> ⛔ **KNOWN LIMITATION, promoted deliberately and named rather than buried.** **[B-267](BUGS.md) closes the credential-in-a-log-message leak but not the malformed case**: `postgres://user:p@ss@host` matched to the *first* `@`, so `ss` survived. ✅ **Strictly better than the previous `main`**, where the whole password reached the JSON sink and everything reached the plain sink. ✅ **Unreachable today, checked rather than assumed** — `database_url` and `redis_url` are Pydantic `PostgresDsn`/`RedisDsn`, so a literal `@` in userinfo fails validation before it exists, and `grep` finds **no code path that logs a URL at all**. **Lane A's fix is on `3e3bd774` and lands next cycle.**
>
> ⚡ **B-267 validated by attack, not by reading.** Ten routes redact — message, `%s` arg, structured field, **and both exception/traceback paths through both formatters**. Neutering the pattern *while keeping the capture group* turns **10 of 15 assertions red**; the five survivors each test a **different** mechanism (bearer, key-based, credential-free URL, and the plain sink's own property). **No decorative assertion survives.**
>
> 🔴 **`TASK-429`'s central claim survives direct attack.** A promotion **and** a rename both re-report as `apollo:1` — **2 distinct keys for 3 records**, exactly as declared. ⚠️ **But 7 of 8 occurrence attributes collide when the identifying field is absent**: `HEADCOUNT_CHANGE` is the only survivor, because it puts the whole value in the key. **The guard was at one producer and not at the seam that collapses**; Lane A moved it to the seam as `UnkeyableOccurrenceError`, distinct from `UnclassifiedAttributeError` so an engineer is routed to a payload rather than to `ATTRIBUTE_KINDS`.
>
> ⛔ **QE certified its own gate change this cycle, and that is stated rather than hidden.** [B-434](BUGS.md) — the coordination owner check demanded a literal lane name where [C-213](LANE_COORDINATION.md) forbids one, so **satisfying it required committing the violation it protects against.** Fixed by joining through [`modules.toml`](coordination/modules.toml). **Fire-testing it found a second, older defect: the `Lane B` branch had never once been reachable** (`actor` is `Lane [ACD]`), **proven dead against the promoted file rather than assumed**, and reordered rather than deleted because the property is real. **12 regression tests, five of which must fire.** ⚠️ **`infra/state-check.py` is a QE gate and no other lane can validate it; the independent evidence is the deterministic gate plus a suite whose failing cases were proven able to fail.**
>
> ⚠️ **A gate QE skipped rather than one that failed:** the new suite broke `mypy --strict` because I type-checked `infra/` and not `backend/`. Caught by running the cheap gates before `certify`, fixed in the same cycle.
>
> 📁 **[C-1433](LANE_COORDINATION.md) — `SIGNORA_ENVIRONMENT` names two concepts.** Stack (`infra/environments.py`: `demo · lane-a…lane-e · lane-qe · review`) and deployment class (ADR-0412: `local · test · demo · production-local · staging · production`). **Intersection is `{demo}`, and it is deliberate.** ⚠️ **QE first reported it as EMPTY, measured against an *inferred* vocabulary containing `development` — the member ADR-0412 explicitly removed. Lane C caught it before it reached a ruling.** ⚡ **ADR-0412 §6 may already decide the item** — *"a second reader of it elsewhere is the second taxonomy this ruling forbids"* — with §7's exclusion list checked and not covering it. **Lane C declined to close it on their own drafted clause.**
>
> ## Cycle 226 — promoted `3d7e2d9e`, 2026-08-13
>
> **`main` = `3d7e2d9e` = the certified commit.** **Lane C's five commits — D-236's three rulings, the queue regeneration, the snapshot manifest.** `pytest` **4547** · coverage **95.06%** · **406** Security Invariants · migration head **`0052`**. **DR passed** — 406 invariants against the restarted stack. **Reversibility head→base→head clean on a disposable database.** ✅ **First attempt, no aborts.**
>
> ⚡ **The cycle was warranted by the path classifier, not by judgement.** Three of the five commits touch `docs/coordination/*.toml` — neither `.md` nor `.json` — so `_is_closeout` calls them executable and `IMPACT_RULES` calls them `platform`. **Documentation alone would have accumulated.**
>
> 🔴 **Four "ahead" counts were three illusions, and resolving them is why nothing was re-certified.** Lane A showed 2 ahead of `integration` and Lane B 2 ahead. **Patch-id and blob-hash put all four already on `main`** — Lane B's `affiliation_reader.py` and its 276-line test file are byte-identical to `main`'s. **A count is never the answer; the mapping is.**
>
> ⚠️ **Lane A's `TASK-429` was NOT bundled, deliberately.** Three of its commits were *authored* at 17:34, before the 17:42:30 pin, but reached `origin` at 17:48. §20e would have permitted a re-pin — it costs a restart, not correctness — but **bundling makes one lane's gate hold another lane's work.** It is cycle 227.
>
> ⚡ **`integration` moved mid-cycle and that was legal.** Lane A pushed `fc14b5c5`, a claim for `TASK-1479` touching only `ACTIVE_ASSIGNMENTS.md` and `BACKLOG.md`; `--audit-claims` passes. **Promotion still went to the certified SHA and no other**, and Closeout step 10 replayed the claim on top.
>
> 🔴 **B-265's hypothesis was about a QE operation and is disproven.** Lane A wondered whether a `dr` restore moved a schema behind a lane's tests. **`dr`, `smoke`, `up` and `down` all target the `signora-prod` compose project — its own postgres on 5433 — and `certify` builds a disposable per-commit database.** No QE operation can reach a lane's. ⚡ **The gap Lane A actually named stands regardless**: `conftest.py` guards destructive consent and RLS binding and **nothing asserts the schema is at head**, so a stale database is discovered as N application failures rather than one sentence — **and N grows with every migration.**
>
> ⚡ **B-433 was misdiagnosed and the disproof was inside the file that reported it.** Lane C isolated a withheld queue row to a two-module `Module` cell from a sample of two. **Across all 10 of Lane A's `READY` rows, `on_integration` is a perfect discriminator, 10/10** — and the emitted source carries **no `module` field at all**. The generator was enforcing §20e; the array was right and the summary counted a row it withholds. **Lane C reached the same conclusion independently and left the wrong diagnosis standing rather than rewriting it** (§2).
>
> 📁 **[B-199](BUGS.md) filed 🟢** — the commit titled *"the snapshot manifest went stale again"* corrected the row into three denominators (37 files, but `2,769,237` is exactly the 35 `.html` files), and **two per-file byte figures were never true of their files**, both of which have one commit and never changed size. **All 36 hashes verified individually and every one is correct.** Fix authored at `e39988aa`, not yet on `integration`.
>
> ## Cycle 225 — promoted `0c79753f`, 2026-08-13
>
> **`main` = `0c79753f` = the certified commit.** Two commits, Lane A · `pytest` **4547** · coverage **95.06%** · **406** Security Invariants · migration head **`0052`**. **DR passed.** ✅ **First attempt, no aborts.**
>
> ### ✅ `TASK-1480` — the demonstration cast is invented
>
> **The old one asserted things about real businesses.** 📁 `playground@3` seeds **12 accounts · 7 qualified opportunities · 0 normalization rejections**. **Mechanism untouched** — `20-provider-simulation.md` governs it unchanged, and a new dataset is a new version with its own `content_hash`.
>
> ⚡ **The row flagged one of its own *Done when* items as historically broken** — *"the Playground reseed produces a working owner persona; [B-262](BUGS.md) says it does not today"* — **and proved it rather than asserting it**: reseed, then run the Companies journey. **6 of 6 green, headless and headed.**
>
> ### 🔴 A false alarm whose shape is worth keeping
>
> **The first attempt failed 4 of 6 with *"You are not part of an organization yet"*** — ⚡ **which is exactly what [B-262](BUGS.md) looks like.** ⛔ **The cause was the lane's own: `pytest` had run between seeding and testing, and that suite TRUNCATES every table after each test**, so the database had no workspaces at all.
>
> ✅ **Reading the database rather than the screenshot is what separated them.** ⚠️ **Same family as the 654 connection errors and the count that would not move: a symptom that matches a known defect exactly, and a measurement that says otherwise.**
>
> ### ⛔ Lane C excluded, and §5d used by somebody else for the first time
>
> **The conflict was in `docs/coordination/coordination.toml` and `queues/lane-a.toml` — both generated by `coordination.py`.** ✅ **QE aborted rather than resolved**, which is Lane C's own §5d correction: **taking either side of a generated file is the mistake that note names.** **They rebased and re-derived.**
>
> ### ⚠️ Waiting for the next cycle
>
> **[D-236](DECISION_REGISTER.md)** — three product-owner rulings closing `C-1505`, `C-1506` and `C-1507`. ⚡ **Lane A is already building against them and will close its own rows once they are an ancestor of `integration`**, the same discipline it held for D-235. **Not idle, and not a synchronization condition.**

> ## Cycle 224 — promoted `7cd62c57`, 2026-08-13
>
> **`main` = `7cd62c57` = the certified commit.** Eleven commits, **all three lanes**, 28 executable paths · `pytest` **4547** · coverage **95.06%** · **406** Security Invariants · migration head **`0052`**. **DR passed.** ✅ **First attempt, no aborts.**
>
> ### 🔴 A defect record of QE's own was lost and recovered
>
> **[B-196](BUGS.md) was gone from every ref.** ⛔ **Filed on `lane-qe`, pushed, and discarded by QE's own Closeout `reset --keep` before any candidate picked it up.** 📁 **`reset --keep` refuses to discard UNCOMMITTED changes and discards COMMITTED ones without comment.**
>
> ✅ **Audited on `main`: B-190 through B-195 all survived; B-196 did not.** ⚡ **The difference is not care — it is whether a cycle ran in between.**
>
> ⚠️ **Found only because an anchored insert asserted `count == 1` and threw.** ⛔ **A broad replacement would have written the next row and reported success, leaving B-196 lost with nothing to notice.** 📁 **The product owner's standing instruction to prefer anchored replacements is what surfaced it.**
>
> ✅ **Recovered by extracting the section from `bca167b7` in the reflog** — **not by cherry-picking**, which conflicted in `certification/manifest.json`, **a generated file QE does not hand-resolve.** ⚡ **And this candidate was built by cherry-picking `lane-qe` rather than resetting it**, which is [B-198](BUGS.md) applied rather than restated.
>
> ### ⛔ Two rows filed with it
>
> **[B-197](BUGS.md)** — **`_promote` reads `docs/BACKLOG.md` on both refs and nothing else**, and `verified_regressions` checks the four QE-written states of a **task** row. **So a `FIXED` → `OPEN` regression is invisible, and so is a `VERIFIED` regression in `BUGS.md`** — ⚡ **the second is worse, because §20e says *only QE sets `VERIFIED`* on a bug.** ✅ **Worth building: `registers.py` already parses the rows and `verified_regressions` already implements the ordering.**
>
> **[B-198](BUGS.md)** — the practice that lost B-196. ⛔ **It states the decision rather than taking it**: either rows stop being filed on `lane-qe`, or the Closeout stops resetting it. **Both have costs and neither is obviously right.**

> ## Cycle 223 — promoted `fde954be`, 2026-08-13
>
> **`main` = `fde954be` = the certified commit.** Four commits, both lanes · `pytest` **4527** · coverage **95.09%** · **406** Security Invariants · mypy strict over **878** files · migration head **`0052`**, unchanged. **DR passed.** ✅ **First attempt, no aborts.**
>
> ### ✅ [D-235](DECISION_REGISTER.md) is on `main` — three rulings that were stranded
>
> **Verified absent from `integration` before the cycle opened.** ⚡ **Lane A had measured that and correctly declined to act on them.** 📁 **One gates the `propose` write port — the last thing between `TASK-466` and a customer pressing the control.** The other two release `TASK-466`'s *Segment* portion and unblock everything in `TASK-1423` except WL-08.
>
> ### ⚡ Why both lanes are in one cycle rather than Lane A alone
>
> **Lane C reported the gating fact with no ask attached**, and explicitly noted **no lane was idle** so the synchronization rule did not apply. ⛔ **Without it QE would have run a one-commit cycle and their twelve would have accumulated a fourth time.**
>
> ⚡ **A fact reported without an escalation attached was more useful than the escalation would have been** — recorded because it is the cheaper mechanism and the one that keeps working.
>
> ### ⚠️ Lane C's §5d correction — the diagnosis was the symptom
>
> **The queue array is not hand-maintained: `coordination.py` writes it.** ⛔ **So after a rebase the committed value is whatever the replayed commits left — stale until the generator runs.** ✅ ***"Re-derive"* was right for a reason they had not measured; *"restore my version"* never was.**
>
> ### ⛔ Still owed by QE
>
> **`--promote` inspects `VERIFIED` and not `FIXED`.** A `FIXED` → `OPEN` regression was caught in cycle 221 **only because QE read two refs by hand after a conflict recurred.** ⚠️ **Raised by Lane A; the row is QE's to file.**

> ## Cycle 222 — promoted `12625ab9`, 2026-08-13
>
> **`main` = `12625ab9` = the certified commit.** Two commits, Lane A · migration head **`0052`** · `pytest` **4505** · coverage **95.10%** · **406** Security Invariants · mypy strict over **875** files. **DR passed. Reversibility proven base ↔ `0052`.** ✅ **First attempt, no aborts.**
>
> ### 🔴 The invariant count, and a correction that landed on QE's own sentence
>
> **Lane A retracted their own claim** that cycle 221's 403 → 406 meant *three tables being checked*. ✅ **QE verified the retraction rather than accepting it**, and **cycle 222 demonstrates it: a third table was added and the count stayed at 406.**
>
> ⛔ **QE's cycle 221 handoff said *"QE verified that rather than taking it"* — and the verification covered the REGISTRATION only.** ⚠️ **One check was presented as covering two claims.** **Corrected in place, dated, above.**
>
> ⚡ **The transferable part is Lane A's tell: the count not moving when it should have.** **Same instrument as the 654 errors that were all connection failures — a number behaving in a way the story cannot explain.**
>
> ### ✅ Three design decisions fire-tested by the lane, each to an exact count
>
> **`200` on create, not `201`** — typing an existing name **selects** that tag, so a `201` would be a lie on the second press. **`AccountTagError`'s own error-map row** — without it a duplicate label reported `catalog_refused`, **a document the caller was not editing**; **exactly two red.** **`changed` nullable with the null load-bearing** — `None` is *not applied yet*, `[]` is *applied and everyone already had it*; ⛔ **a caller reading *nothing to reverse* as *never applied* would offer undo on a finished batch**; **exactly three red.**
>
> ### ⛔ [C-1504](LANE_COORDINATION.md) — a premise that expired
>
> `action_batch/public/` publishes **read-only** and says why: *"a port that could write before the domain exists would let a consumer commit to a lifecycle nobody has built."* ⚡ **That reasoning was right and its premise has expired** — slices 4 and 5 shipped, `TASK-465` is `PROMOTED`. **The docstring still reads *"nothing implements this yet."*** ✅ **Recorded rather than edited, and raised rather than taken — by the lane that owns BOTH modules and could have taken the edge quietly.**

> ## Cycle 221 — promoted `a5b3b8b1`, 2026-08-13
>
> **`main` = `a5b3b8b1` = the certified commit.** Thirteen commits, both lanes · migration head **`0051`** · coverage **95.08%** · **406** Security Invariants · mypy strict over 872 files. **DR passed. Reversibility proven base ↔ `0051` on a disposable database.** ✅ **First attempt, no aborts.**
>
> ### ✅ Coverage headroom is positive again
>
> **95.08% against a floor of 95.0** — **eight basis points, the first positive headroom in four cycles**, after [B-196](BUGS.md) took it to 94.96. ⚡ **Lane A measured 100% on both new files BEFORE pushing rather than at certification**, which is what §19 asks for and what the previous cycle cost.
>
> ### ✅ Security Invariants 403 → 406
>
> **Both registered in `tenancy_policy.py` in the same change that creates them** (§8). ✅ **QE verified THAT — it grepped both names.**
>
> ⚠️ **CORRECTED 2026-08-13, cycle 222, by Lane A retracting their own claim.** ⛔ **The sentence above originally read *"the three new ones are these tables being CHECKED rather than merely listed"*, and the arithmetic was wrong.** 📁 **Measured**: all three tables are in `TENANT_OWNED_TABLES`, and **only `account_tag_assignment` is in `IMMUTABLE_TENANT_TABLES`** — the parametrized one — **with an explicit comment that `account_tag` is deliberately not there.** ⚡ **The +3 is one table entering one list.**
>
> ⛔ **And QE's *"verified that rather than taking it"* covered the registration only, not the arithmetic.** **One check was presented as covering two claims.** ✅ **Demonstrated in cycle 222: a third table was added and the count stayed at 406.** **The substance holds** — removing `account_tag_batch` from `TENANT_OWNED_TABLES` fails `test_every_table_is_classified`.
>
> ### 🔴 Two findings from Lane A that a green run would have hidden
>
> **① A 98% coverage run named one uncovered line whose docstring claimed the method was idempotent while the code raised.** ⛔ **The comment was wrong, not the code** — **coverage catching a false claim rather than a missing test.**
>
> **② An attribution test stayed green because the FAKE was doing the protecting.** ⛔ `setdefault` preserved the first writer, **so the test was checking the double rather than the code.** ✅ **The fake now raises the duplicate-key violation Postgres would** — `(tag_id, account_id)` is a primary key — **and the same fire test turns five red instead of one.** ⚡ **[B-191](BUGS.md)'s lesson in the fixture layer.**
>
> ### ⚠️ An environment failure, and the tell that identifies one
>
> **Lane A hit 654 `ConnectionRefusedError`s. It was QE's stack** — `make dr` and `make down` bring it down as part of the cycle. **They restarted it and said so.** ⚡ **Their tell is better than a retry: errors and passes matched EXACTLY.** **An environment failure takes every test; a regression takes some.**
>
> ### ⛔ Open against QE's own guard
>
> **`--promote` inspects `VERIFIED` and not `FIXED`.** 📁 A `FIXED` → `OPEN` regression was caught this cycle **only because QE read two refs by hand after a conflict recurred.** ⚠️ **Raised by Lane A, and it should not stay something noticed twice by accident.**

> ## Cycle 220 — promoted `72c53947`, 2026-08-13
>
> **`main` = `72c53947` = the certified commit.** Fourteen commits, all Lane A · migration head **`0050`** · coverage **95.03%** · 403 Security Invariants · mypy strict over 868 files. **DR passed. Reversibility proven base ↔ `0050`.**
>
> ### 🔴 [B-196](BUGS.md) — the first attempt passed all six gates and failed the CONDITION
>
> **`coverage 94.96% is below 95.0%`.** ⚡ **Two facts, and the row states both because either alone misreports it:**
>
> **①** `preferences.py` had **10 uncovered statements** — the `if updated is not current:` **idempotence guard**, designed and stated in its own comment, asserted nowhere.
> **②** **The repository had already spent its headroom**: 95.03 → 95.0 → 94.96. **Any slice adding ~9 uncovered units would have failed.**
>
> ⛔ **Reporting ① alone reads as a lane shipping untested code; ② alone excuses ten uncovered statements in a new file.**
>
> ⚠️ **QE nearly misattributed it in the lane's favour**: the first measurement was **module-only** and showed `router.py` and `composition.py` at **0%**, because their coverage comes from integration tests. **The full suite produced the two line ranges.**
>
> ✅ **Lane A's fix is the shape that matters.** ⛔ **Asserting the value is unchanged does not test that guard** — the domain already refuses to move, **so a use case calling `save()` anyway would pass every value assertion and still write a row per click.** ✅ **The fake counts writes; the assertion is on the count.** **Removing both guards turns exactly the two idempotence assertions red and leaves the other eight green.**
>
> ### ⚠️ Reversibility needs a disposable database, and the first attempt showed why
>
> **Run against `signora`, the downgrade FAILED** re-adding `ck_action_batch_transition_only_application_is_unattributed` — **violated by existing rows**, demo data using a relaxation a later migration introduced. ⛔ **That is a data condition, not a non-reversible migration.** ✅ **base ↔ `0050` on a fresh database: clean.**
>
> ### ⛔ Lane C excluded twice, and the second time was worth recording
>
> **Two lanes asserted different states for [B-253](BUGS.md)** — Lane C `OPEN — RELEASED TO LANE A`, Lane A `FIXED` — **both dated today, both honest from where written.** ⚡ **A QE that picks between two lanes' assertions about a row is writing a register it does not own**, so it went back to them.
>
> ✅ **Lane C resolved it by removing their own redundant line rather than negotiating**, and stated the general form: ***a release note and a fix state are different facts, and only one of them is the `Status` cell.*** **Releasing a row is Lane C's; recording it fixed is the lane's; `VERIFIED` is QE's alone.**

> ## Cycle 219 — promoted `47fce828`, 2026-08-13
>
> **`main` = `47fce828` = the certified commit.** Thirteen commits · migration head **`0049`** · `pytest 4424` · **coverage `95.0`** · 403 Security Invariants · mypy strict over 868 files. **Migration reversibility proven base ↔ `0049`.**
>
> ⚠️ **Cycle 218 has no block here, and that absence IS [B-195](BUGS.md)'s finding**: its Closeout touched `docs/BACKLOG.md` and nothing else. **Left as a dated gap rather than backfilled** — a record of what was missed is worth more than a tidy sequence.
>
> ### 🔴 Three certifications, and both failures were QE's
>
> **① `0ccc72de` passed every gate and could not be promoted.** ⛔ QE's own [B-195](BUGS.md) filing had gone to `main` and `integration` was never rebased onto it, **so the certified commit was not a descendant.** 📁 **§20e predicts it exactly** — *rebase `integration` onto `main`, always; Closeout commits land on `main` and never on `integration`, so every cycle diverges the two by construction.* **The rule was not missing. It was read and not performed.**
>
> **② The second attempt was one push from destroying eleven commits** — seven of `TASK-1424`, [B-264](BUGS.md), and migration `0049`. ⚡ **QE rebased the candidate onto `main`, then ran the patch-id survival check its own procedure requires — against a STALE `origin/integration`, before fetching.** It reported everything surviving: **true of the ref compared against, false of the repository.** ✅ **`--force-with-lease` refused with `stale info`, and that is the only thing that caught it.**
>
> > ⛔ **A verification against a stale operand is not a weaker verification. It is a confident wrong answer guarding a destructive operation.**
>
> **The recovery was the skipped step** — rebase `integration` onto `main`, which **replays** everything rather than discarding it. ✅ Verified against the **fetched** ref: nothing missing by patch-id, migration present.
>
> ⛔ **Not instrumented, deliberately.** **Both errors were caught by gates that already existed** — `--ff-only` refused, then `--force-with-lease` refused — **and neither would have been caught by anything QE was about to build.** ⚡ **The guarantee held twice while the sequence failed twice.**
>
> ### ⚠️ Coverage headroom is gone
>
> **`95.0` against a floor of `95`.** It passed. **4 basis points three cycles ago, 3 last cycle, 0 now.** ⛔ **The next slice that adds an uncovered line fails the gate**, and it will present as that slice being rejected for something the repository had already spent. 📁 `make coverage-debt ARGS="<module>"` sees it before QE does.
>
> ### ✅ What shipped
>
> **`TASK-1424`** — the first-run overlay, its dismissal stored where *forever* means it, and activation's two blocking steps. **[B-264](BUGS.md)** — changing any preference silently forgot which workspace you were in. **[B-195](BUGS.md)** — the board-header check now asks whether the record is *current*, after three wrong predicates.

> ## Cycle 217 — promoted `e158dd04`, 2026-08-12
>
> **`main` = `e158dd04` = the certified commit.** Ten commits. **First attempt, no aborts.**
>
> ### ✅ `TASK-1476` — Account 360, validated on its DECLARED scope
>
> ⚠️ **The four journeys are recorded as written-and-not-passing and [B-261](BUGS.md)/[B-262](BUGS.md) as declared limitations** — **neither promoted to a defect QE discovered nor absorbed into compliance.** 📁 The `PROMOTED` row says so.
>
> **Two invariants fire-tested rather than read**, both from the scope the lane declared:
>
> | Mutation | Result |
> |---|---|
> | `worstSeverity` inverted, so a collapsed section reports its **best** member | ⛔ **4 red — including at the rendered header**, so the guard reaches the screen, not only the helper (B-191's lesson) |
> | `collapseKey` keyed by the **record** instead of the account type | ⛔ **Does not compile.** The signature takes `userId, kind, sectionId` — **the forbidden implementation is unrepresentable**, which is stronger than a test |
>
> ### ⚡ The stranded synchronization work landed with it
>
> **`ADR-0409` `RATIFIED`, the `C-210` and `C-1430` rulings that read `OPEN` on `integration`, the five commissioned designs with hashes, and four rows released.**
>
> ### 🔴 The route finding, and it is Lane A's own row
>
> **Ten executable `TASK-1476` commits reached `integration` without QE** — [B-238](BUGS.md)'s second instance, recorded by Lane A against itself. ⛔ **`--audit-claims` reported *0 claims awaiting promotion* the whole time and was not wrong**: it audits subjects beginning `Claim `. ✅ **`--audit-main` was clean throughout — the `main` guarantee never depended on the route.**
>
> ⚡ **Lane C's framing is the one to keep: this was a state contradiction with an owner, not a route defect** — *"a check cannot resolve a contradiction between two people's claims; it can only make the repository look like it has."* **No guard was added.**
>
> ### ⚠️ Open and not QE's
>
> **[B-263](BUGS.md)** — `C-210` names two questions, and the one without a heading is invisible to a heading-based scan. **Lane A has stopped allocating coordination ids: `C-200`–`C-299` are exhausted and [BUGS.md](BUGS.md)'s own table says Lane A's block is the product owner's to allocate.** ⛔ **That is a ruling, not a QE fix.**

> ## Cycle 216 — promoted `c3964e6c`, 2026-08-12
>
> **`main` = `c3964e6c` = the certified commit.** Fourteen commits, all registers and coordination. **First attempt, no aborts.** ⛔ **No customer-visible change.**
>
> ### ⚡ A synchronization cycle, and the second time the rule has been invoked
>
> **[`TASK-1476`](BACKLOG.md) and [`TASK-1477`](BACKLOG.md) were `READY` on `lane-c-sync` and absent from `integration`** while Lane A was idle and correctly refusing to claim from a Product Office branch. ✅ **Verified by SET, not count** — a count of Status cells containing `READY` reads every row that merely narrates having been READY. **The candidate was docs-only, so accumulation would have held it; §20e says which rule wins.**
>
> ### ⚠️ What is deliberately NOT in this promotion
>
> **`TASK-1478`, `D-229` and `ADR-0409` arrived on `lane-c-sync` after the snapshot was pinned.** ⛔ **They belong to the next cycle by construction** — re-pinning would have meant re-measuring against a different tree. **Nothing is lost.**
>
> ### 🔴 Open against QE
>
> **[B-194](BUGS.md)** — Closeout ran `state-check` piped into a grep for one expected line, and **a duplicate `C-300` was promoted while the tool was reporting it.** ✅ **Correction held since: the findings are read in full, and greps come afterwards to confirm.**

> ## Cycle 215 — promoted `0f9c7f90`, 2026-08-12
>
> **`main` = `0f9c7f90` = the certified commit.** Three commits, all Lane A. **First attempt, no aborts.**
>
> ### ✅ The idle ended and the product moved in the same cycle
>
> **A seller can work their whole book from one screen** — table or cards, chosen columns, narrowing by name, source, kind or recency, paging, and export ([`TASK-1475`](BACKLOG.md)). ⚡ **Claimed the hour it reached `integration`, implemented, handed over.** **That is what four idle cycles were costing, stated as one data point rather than as prose.**
>
> ### ⚡ QE's validation, and the lane asked for it by name
>
> **The screen carries two absences that must never collapse** — *the book is empty* and *the narrowing excluded everything*. ✅ **Fire-tested, not read**: collapsing the filtered title turns **1 red** (and the test's name is the property), removing the `isError` branch turns **3 red**. 📁 **[P-A](DOMAIN_DISCOVERY_REGISTER.md) is guarded rather than asserted**, with the branch order error → loading → empty book → narrowed.
>
> ### ✅ The coverage line's first live test
>
> **50 of 121 when it shipped; 50 of 124 after this promotion.** ⛔ **The numerator held while the denominator rose** — a slice that ships with its link does not move it. **[B-258](BUGS.md) closes with the slice**, as its row said.
>
> ### ⛔ What the next session should know is absent, and why
>
> **A column exists only where a field does.** `ColumnSpec.read` takes a `ListedAccount`, **so five of the design's columns, board view, grouping, sorting, smart filters and the AI rows are all absent** — each groups or ranks by a field whose source is undecided. ✅ **Nothing invented meanwhile.**
>
> ⚡ **[C-300](LANE_COORDINATION.md) is the widest open decision**: one ruling spanning this table, `TASK-1469` and [C-297](LANE_COORDINATION.md). **With [C-298](LANE_COORDINATION.md), [C-299](LANE_COORDINATION.md), [C-1424](LANE_COORDINATION.md) and [C-106](LANE_COORDINATION.md), decisions — not capacity — bound the next screen.**

> ## Cycle 214 — promoted `98b9055b`, 2026-08-12
>
> **`main` = `98b9055b` = the certified commit.** Nine commits, all Lane C. **First attempt, no aborts.**
>
> ### ✅ A four-cycle idle ended, and that is the whole cycle
>
> 📁 **[`TASK-1475`](BACKLOG.md) is on `integration` and claimable.** ⛔ **It had been `READY` on `lane-c-sync` and absent from `integration` while Lane A sat idle for four consecutive cycles**, correctly refusing to claim from a Product Office branch.
>
> ### ⚡ The rule that made it happen, and it had never been invoked before
>
> **`lane-c-sync` is docs-only, so the accumulation rule would have parked it a fourth time.** 📁 **§20e: *"whenever an implementation lane has been idle for more than one reporting cycle because `READY` work exists only outside `integration`, synchronizing that work becomes the highest repository priority — above further preparation, above new initiatives, above every planning activity."*** ✅ **Applied as the rule, not as an exception.**
>
> ⛔ **QE could not see the condition: it reads `integration` and nothing else.** ⚡ **Lane A verified the absence and Lane C reported it against its own queue** — **neither waited to be asked, and that turned a fifth idle cycle into one exchange.**
>
> ### ⚠️ One judgement worth knowing about
>
> **Lane C rebased once on request; then QE's own Closeout moved `integration` two commits and stranded them again.** ✅ **QE performed the second rebase itself rather than handing back drift it had created.** **Nine commits, no conflicts — so no judgement about another lane's register was made**, which is what the rule protects. ⛔ **Had it conflicted it would have gone back.**
>
> ### What the next session should expect
>
> ⚡ **Lane A claiming `TASK-1475`.** **Nothing is queued ahead of it and nothing waits on QE.** ⛔ **The five product-owner decisions are unchanged and remain the only other constraint** — [C-106](LANE_COORDINATION.md), [C-297](LANE_COORDINATION.md), [C-298](LANE_COORDINATION.md), [C-299](LANE_COORDINATION.md), [C-1424](LANE_COORDINATION.md).

> ## Cycle 213 — promoted `77daace8`, 2026-08-12
>
> **`main` = `77daace8` = the certified commit.** Five commits, Lane A ×3 and QE ×2. ⚠️ **Second attempt, and QE stopped the first itself** — 39 seconds in, rather than promote an instrument whose number nobody could act on.
>
> ### 🔴 Read this first: a lane is idle on work that already exists
>
> 📁 **[`TASK-1475`](BACKLOG.md) is `READY` on `lane-c-sync` and absent from `integration`** — measured both ways. ⛔ **Lane A is on its fourth consecutive idle cycle and refuses to claim from a Product Office branch, correctly.**
>
> ⚡ **§20e names this condition and calls synchronizing it the highest repository priority, above further preparation and every planning activity.** ✅ **Applied as the rule rather than as an exception**, and **cycle 214 takes `lane-c-sync` first.**
>
> ⚠️ **It was invisible to QE, because QE reads only `integration`.** ✅ **Both lanes reported it without being asked** — which is the only reason it surfaced at all.
>
> ### ⛔ QE was wrong twice this cycle, and both are corrected in place
>
> **[B-193](BUGS.md)** concluded no structured task→commit link existed and that inventing one would change how work is recorded. ⚡ **Lane A corrected it: §20e mandates a `Slice-Handoff` whose `Milestone` field names the `TASK-nnn`, and 325 commits on `main` carry one.** **An error of fact.** ✅ **The real reason the held-row check stays unbuilt is now measured: 48 of 121 promoted tasks have no handoff, including the one that produced the finding** — a check keyed on it would be silent exactly where it is needed.
>
> **And QE reported `people` and `integrations` as empty `public/` contracts.** ⛔ **They publish 3 and 17 names.** ⚠️ **QE counted sibling files rather than reading `__init__.py`, which is where `__all__` lives.** ✅ **`timeline` is the single instance** — and 📁 **`ai_research_engine` is the model for its repair**: an equally empty contract whose file is a docstring saying *"deliberately empty until something outside this module needs it."* **Lane A plans that docstring; the wording already exists.**
>
> ### ✅ What is new in the instrument
>
> **A handoff-coverage line in [`state-check.py`](../infra/state-check.py)**, fire-tested four ways — including that **it reports everything if its own scan breaks, rather than going quiet.** ⚡ **It is a BASELINE, not a target**: a promoted commit message is immutable, so **the count can only be held, and a rise is a slice that shipped without its link.**
>
> ### The decision queue is unchanged, and it is still the whole constraint
>
> ⛔ **[C-106](LANE_COORDINATION.md) · [C-297](LANE_COORDINATION.md) · [C-298](LANE_COORDINATION.md) · [C-299](LANE_COORDINATION.md) · [C-1424](LANE_COORDINATION.md).**

> ## Cycle 212 — promoted `02775de5`, 2026-08-12
>
> **`main` = `02775de5` = the certified commit.** Four commits, Lane A ×3 and QE ×1. ⚠️ **Second attempt — the first certification was killed and wrote no record**, which is how it was told apart from a verdict: the manifest still named `96f2343475fa` afterwards. **The manifest is the durable record; a log is not.**
>
> ### 🔴 Three setup failures, one appearance, and one undecided root
>
> **[B-257](BUGS.md).** 📁 `config.ts:140/151/157` default `SIGNORA_APP_URL` and `SIGNORA_JWT_ISSUER` to `localhost:3000` and `SIGNORA_API_URL` to `8000`, and 📁 [`RUNNING.md:311`](RUNNING.md) reserves those ***"to no lane."*** ⛔ **An unset variable does not aim a lane at a wrong port — it aims its auth tier at the product owner's demo stack.**
>
> **The comment defending them claimed *"a URL pointing at the wrong port fails loudly and immediately."*** ⛔ **QE's own measurement disproves it**: `Invalid origin` → `403`, a sign-in that submits and never navigates — **identical to a missing Better Auth schema and to missing demo accounts.** ⚡ **Three causes, one appearance, and QE hit all three in one session assembling a lane environment.**
>
> ✅ **The values were left deliberately.** `environmentName()` returns `local` for every lane, so **the auth tier cannot tell a first clone from a lane** — 📁 **[C-298](LANE_COORDINATION.md)**, and QE checked that rather than taking it on trust.
>
> ### ✅ [B-191](BUGS.md) is closed, both instances, both directions
>
> The journey **passes with the fix and fails with `name={null}`** — *Expected substring: `"Dana Reyes"`*. ⚡ **Last cycle the same revert left 3062 tests green.**
>
> ### 🔴 The repository's binding constraint is now a decision queue, not capacity
>
> ⛔ **Lane A has had nothing startable for three cycles**, and **the defect supply that carried the first two is spent.** ⚡ **Its own words: *"Startup step 4 is exhausted rather than thin… I would rather say that plainly than keep widening what counts as work."***
>
> **Every open defect in its modules is terminal** — fixed and with QE, routed and awaiting a ruling, blocked on an unruled governance amendment ([C-101](LANE_COORDINATION.md)), or parked by ruling.
>
> ⚡ **The unblock order is the lane's own, smallest first: [C-298](LANE_COORDINATION.md) → [C-299](LANE_COORDINATION.md) → [C-1424](LANE_COORDINATION.md).** **C-298 buys [B-223](BUGS.md) and [B-257](BUGS.md) together; C-299's recommendation wires `last_used_workspace`, which already exists.** ⛔ **None is large, and all are decisions rather than implementations.**
>
> ### ⚠️ Two measurements that are not gates
>
> **`ruff check modules/` → 85 errors**, and `ruff` is not a certification gate ([B-211](BUGS.md)). ✅ **Re-measured rather than carried; the row's figure was 238.** ⛔ **A green certification must not be read as *the backend is lint-clean*.**
>
> **[B-192](BUGS.md) is open and blocked on [B-105](BUGS.md)**, both QE's: a setup prerequisite added today would refuse when a lane ran it.

> ## Cycle 211 — promoted `96f23434`, 2026-08-12
>
> **`main` = `96f23434` = the certified commit.** Two commits, Lane A ×1 and QE ×1. **First attempt, no aborts.** ⛔ **No customer-visible change, and that is the point** — the whole cycle is [B-191](BUGS.md)'s repair.
>
> ### ✅ Verified by measurement, and ⛔ one half that was not
>
> **[B-256](BUGS.md): verified.** The identical revert QE ran in cycle 210 — the two component lines, `reachable` untouched — **left 3062 tests green then and turns three red now.**
>
> **[B-429](BUGS.md): NOT executed.** ✅ The journey asserts the right seam — the account menu read through `layout.tsx`, a real session and the whole shell chain. ⛔ **QE verified its shape, not its behaviour**, and **reading a guard is not testing it, which is B-191's own point.** ⚠️ **Both halves are recorded because a partial verification reported as a whole one is exactly the defect B-191 is about.**
>
> ### 🔴 [B-192](BUGS.md) — QE's own runbook is missing the step that would have let it finish
>
> [`RUNNING.md`](RUNNING.md)'s *Running a lane* documents compose, three exported URLs, `alembic upgrade head`, `uvicorn` and `npm run dev`. ⛔ **It documents nothing that creates the Better Auth schema.** 📁 **Alembic manages the Python tier only; Better Auth owns `user`, `session`, `account` and `verification` and creates them itself** ([ADR-0026](architecture/adr/0026-jwt-boundary-architecture.md)).
>
> ⚠️ **Measured on a freshly-migrated lane database: 59 tables, and not one of the four.** **Sign-in submits and never navigates** — so **the first thing that breaks names the wrong subsystem**, which is [B-219](BUGS.md)'s three-day lesson repeating in a different place.
>
> ⛔ **Filed rather than fixed.** `npx @better-auth/cli migrate --config lib/auth/server.ts` answers *"No configuration file found"*, **so the correct command is not obvious and guessing at it would be inventing a documented step rather than recording one.**
>
> ### ⚠️ The constraint has not moved
>
> **Queue depth, not implementation capacity.** ⚡ **Lane A put it plainly: *"the supply of my own past mistakes is not infinite and is a poor substitute for scheduled work."*** **Three product-owner decisions remain open and unchanged — [C-106](LANE_COORDINATION.md), [C-1424](LANE_COORDINATION.md), [C-297](LANE_COORDINATION.md).**

> ## Cycle 210 — promoted `b4c99250`, 2026-08-12
>
> **`main` = `b4c99250` = the certified commit.** Seven commits: Lane A ×3, Lane C ×3, QE ×1. **First attempt, no aborts.** `integration` = the certification record, which promotes next cycle.
>
> ### 🔴 The product was promising a capability two modules refuse in writing
>
> **[B-256](BUGS.md).** Onboarding told whoever picked the **first** goal on the screen — *Forecast accurately* — that ***"Signora will open on Forecast, the Executive Dashboard."*** ⛔ **Neither has a route on any branch**, and `forecast` is refused as **domain law**: 📁 `buying_score_engine/domain/events.py` states *"No probability, no likelihood, no prediction… it does not forecast a purchase"*, and `opportunity_engine`'s router says it again independently. ✅ **QE verified both halves rather than accepting them** — the domain text at source, and the five absent routes by looking for their pages.
>
> ⚡ **The transferable part is the shape.** The map was a `Record<string, string>` — it answered *what is this called* and **could not express *named and unreachable***, so an absent screen was indistinguishable from a shipped one. ⛔ **And the file's own honest guard — *"an unknown identifier is titled rather than dropped"* — made the promise stronger.**
>
> ### ⛔ A fix can be right and its proof still worthless
>
> **[B-191](BUGS.md), and it is the cycle's other lesson.** B-256's guard imports `reachable` and calls it directly; **nothing in `frontend/tests` renders `GoalsForm`.** ⚡ **Measured, not reasoned**: QE reverted the two component lines, left the helper intact, ran the suite — **169 files, 3062 tests, all green**, with the screen promising Forecast again. Tree restored.
>
> **[B-252](BUGS.md)'s class one file along, and the same lane named it this week**: *a proof that cannot fail when the thing it protects is removed*. ✅ **Filed 🟡 against `product_surface` — nothing is wrong today; what is missing is the proof it stays right.**
>
> ### ⚠️ Queue depth is now the binding constraint, and it is not implementation capacity
>
> **Lane A is level with `main` and has had nothing startable for two consecutive cycles.** Both times it produced real value anyway — eight defects, then B-256 and a measurement — **which is Startup step 4 working twice and is not a queue.** `state-check`: **3 claimable rows against a floor of 10, 17 prepared against 20.** **Lane C has recorded it as its next bounded objective.**
>
> ⛔ **And [`TASK-1469`](BACKLOG.md)'s parallelisable step names the wrong lane** — it says the `opportunity_engine` measurement is *"what Lane B can do NOW"*, and `opportunity_engine` is **Lane A's**. **A task addressed to a lane that does not own the module is a task nobody starts.**
>
> ### Three decisions, all the product owner's
>
> ⛔ **[C-106](LANE_COORDINATION.md)** — [B-428](BUGS.md)-B's severity, unruled since cycle 205; every promotion since carries it as a standing override with the severity untouched. ⛔ **[C-1424](LANE_COORDINATION.md)** — [B-253](BUGS.md). ⚡ **[C-297](LANE_COORDINATION.md)** — new, and the sharpest: **honest is not the same as good.** A customer who picks *Forecast accurately* now sees their selection register and **nothing else, having just told Signora what they came for.**

> ## Cycle 209 — promoted `9c7e052e`, 2026-08-12
>
> **`main` = `9c7e052e` = the certified commit.** Seventeen commits: Lane A ×8, Lane C ×7, QE ×2. **`main` has moved five times today.**
>
> ⛔ **Every promotion since cycle 205 carries [B-428](BUGS.md) 🔴 `OPEN` on the product owner's standing override.** **Not a resolution**; severity untouched. **[C-106](LANE_COORDINATION.md) is still unruled and is now the only place the question lives** — ✅ **[C-107](LANE_COORDINATION.md) is `RESOLVED`** (Lane C, on measurement: `_promote()` runs two gates and never opens `BUGS.md`, so there is no executable 🔴 block and the rule is prose QE applies). ⚡ **That resolution *sharpens* C-106 rather than reducing it: there is now no code to defer to.**
>
> ⚠️ **[B-253](BUGS.md) and [C-1424](LANE_COORDINATION.md) are unchanged and still the one open item with a live customer cost** — an owner shown their own destinations locked on every cold boot, and a one-line repair waiting on a ruling about which wrong state is less harmful.
>
> ### 🔴 The finding worth carrying forward: a green suite can go red on a date
>
> **[B-189](BUGS.md). The repository certified at 09:34 and 10:44 and could not at 12:17, on a backend tree `git diff` reports as identical.** A test declared `NOW = 2026-08-05 12:00 UTC`, built a fixture expiring seven days later, and its fake compared that against `datetime.now(UTC)`. **At noon the window closed.**
>
> ⚡ **Lane A's repair went a layer deeper than QE's diagnosis.** The fake was applying an expiry filter `SqlInvitationRepository.find_live` does not apply, so an expired offer was answered *"there is no invitation"* instead of *"this invitation has expired"* — **the sentence reserved for a revoked or never-issued offer, given to somebody who only needed a new link.** ✅ **QE found a test that broke on a date; Lane A found a customer being told the wrong thing.**
>
> ✅ **A module guard now refuses any file in `workspace_tenancy` that declares a fixed moment and then reads the real clock.** ⚠️ **The repository-wide sweep found one instance and is a grep** — it cannot see a fixture whose expiry is computed rather than written.
>
> ### ⛔ Third instance in two days of a guard that reads source as text
>
> **[B-254](BUGS.md), QE's own, raised by Lane A.** `test_no_production_package_imports_certification` checked `if "certification" in path.read_text()`. **The name was a false claim about what the code did**, so prose failed a clean tree and Lane A had to spell the package name in two halves to describe the defect. ✅ **It parses now.** ⚡ **After [B-162](BUGS.md) (narrowed until it stopped firing) and [B-252](BUGS.md) (an identifier in a comment counted as a caller), the pattern is established: a text scan over source will eventually be satisfied by prose or defeated by it.**
>
> ### ✅ The `distDir` interaction QE flagged is disproven at runtime
>
> **[B-219](BUGS.md) moved the build output, so the production image's static-asset paths moved with it.** QE warned that copying to `.next/static` would produce **an image that starts and serves no CSS** — silent, and worse than a build failure. **Measured on the built image: `200`, 40 589 bytes.** ⛔ **A prediction is not a finding until it is measured either way.**
>
> ⚠️ **A DR failure that was QE's own procedure, recorded because the wrong diagnosis was plausible.** `make dr` reported *"API did not become ready within 90s"*; **`dr` requires the production stack already up and QE had not run `make up`.** Memory was genuinely tight at the time — a `next-server` holding 6.9 GB — **and that fact was true and irrelevant.**
>
> ⚠️ **Migration reversibility truncated the shared `signora` database**, which is the Human Review stack's. **Reseeded at Closeout; noted because it is [B-250](BUGS.md)'s neighbourhood** — the default target of the test configuration is the environment every lane and the review stack share.

> ## Cycle 208 — promoted `0ffe15f3`, 2026-08-12
>
> **`main` = `0ffe15f3` = the certified commit.** Cycles 206–208 all promoted; **`main` has moved four times today.**
>
> ⛔ **Every promotion since cycle 205 carries [B-428](BUGS.md) 🔴 `OPEN` on the product owner's standing override.** **Not a resolution**; severity untouched. **[C-106](LANE_COORDINATION.md) and [C-107](LANE_COORDINATION.md) are still unruled.**
>
> ⚠️ **[B-253](BUGS.md) fails three journeys on `main` right now** — `rail-assistant.spec.ts`, *"Settings — restricted"*, against an **owner**. **[C-1424](LANE_COORDINATION.md) holds a one-line repair and needs a product ruling** on which wrong state is less harmful. **This is the one open item with a live customer cost.**
>
> **QE gate defects fixed today, all found by running QE's own instruments:** [B-184](BUGS.md) the claim audit could never pass · [B-187](BUGS.md) `state-check` could not see an 8-character SHA · [B-188](BUGS.md) `smoke` discarded the evidence for its own verdict. ⚡ **All three were correct about a fact and wrong about what the fact meant.**
>
> ⚠️ **The WSL Docker environment does not keep the dev stack alive between runs.** Three certifications aborted at `release-preflight` on a dead database. ⛔ **A workstation condition, not a repository defect** ([B-011](BUGS.md)). **Certify is now launched chained** — `up -d --wait` → preflight → `make certify`, each gated on the previous exit code.

> ## Cycle 205 — promoted `0dfc07f4`, 2026-08-12
>
> **`main` = `0dfc07f4` = the certified commit.** `integration` = `f860ec1f` (the certification record, which promotes next cycle).
>
> ⛔ **Promoted with [B-428](BUGS.md) 🔴 `OPEN`, on the product owner's explicit override.** **Not a resolution.** Criterion B is a *capability* defect and blocks under both readings of [C-107](LANE_COORDINATION.md); **QE did not touch the severity.**
>
> ✅ **[B-183](BUGS.md) is `CLOSED`** — its own condition, *"closes when the fix is promoted"*, met literally. ⚠️ **[C-107](LANE_COORDINATION.md) stays OPEN anyway**: it closed because a promotion happened, and **the next 🔴 written the same way will self-block identically. A promotion is not a ruling.**
>
> **Two decisions still with the product owner:** [C-106](LANE_COORDINATION.md) — B-428-B's severity. [C-107](LANE_COORDINATION.md) — does the 🔴 block read the candidate tree or the row's status.
>
> **QE gate defects fixed this cycle, all found against QE's own instruments:** [B-184](BUGS.md) — the claim audit refused on immutable history, so it could never pass; **the same range bug also made the skips report name 131 of 166 claims (now 5)**, and **`_claim_stowaways` measured from `main` while its docstring said `integration`** — ⚡ **so the promotion block was manufacturing false positives in the check that guards promotion, and the rate grew with the block.** Now measured from `_validated_floor()`.
>
> **Open and NOT QE's:** [B-185](BUGS.md) `--dry-run` writes the generated coordination source *(Lane C)* · [B-186](BUGS.md) the republish is not the last commit of its batch *(Lane C)* · [B-253](BUGS.md) 🟠 cold boot shows an owner their own destinations locked, raised as [C-1424](LANE_COORDINATION.md).
>
> ⚠️ **Two aborts preceded this certification and neither was a property of the commit** — a run killed with its process leaving no marker, and `release-preflight` refusing on a dead database. **The manifest is the durable record; a log is not.** QE reported a run as in flight that had already died, and only caught it by reading `certification/manifest.json`.


> **This file answers one question: *"what should the next session know?"*** Current repository state · current certification state · active lanes · open blockers · pending work · repository recommendations.
>
> **[PROJECT_STATUS.md](../PROJECT_STATUS.md) answers a different one — *"where are we?"*** Milestone progress, completion percentage, repository health and every measured figure live there and are **not repeated here** (`CLAUDE.md` §20e). Where this file needs a number, it links.
>
> **Authoritative continuation point.** Written by **QE at Repository Closeout**, after every promotion — a feature lane never edits it.
> **As of:** 2026-08-15 · **`main` at `136f112b`** · ✅ **CERTIFIED under eight gates, and commit-bound**
>
> Read this first. Then **[21-intelligence-pipeline.md](architecture/21-intelligence-pipeline.md)** — the flagship reference for how information moves through Signora — then [PROJECT_STATUS.md](../PROJECT_STATUS.md) for the dashboard, and [IMPLEMENTATION_ROADMAP.md §5b](../IMPLEMENTATION_ROADMAP.md#5b-execution-sequence) for the execution order. Everything else is reference.

---

## 1 · Current project position

| | |
|---|---|
| **Last completed** | **M12.5 Commercial Profile** — all five slices promoted 2026-08-02. *A customer declares what they sell, who buys it, who agrees, what they are pushing, and which companies they are going after.* **The pipeline finally has an input** |
| **Also shipped** | **M12.4 research on demand**, verified against a real model |
| **Inserted, and open** | **M9.5 Evidence Citation Protocol** (ADR-0031). Steps A–D landed; **Step F is incomplete** |
| **Current** | **M12.3 evidence and actions** (D20 remains) · **M7 Timeline — backend proven live this cycle, mount point still open** ([C-024](LANE_COORDINATION.md)) |
| **✅ Workflows 1–4 on `main`; ten rows claimable** | ⛔ **Read [B-150](BUGS.md) and [B-411](BUGS.md) before resolving any register conflict** — never chain `git add` after a resolver with `&&`, and run `state-check` before every Closeout commit.: QE deleted a `BACKLOG.md` line in cycle 122 by inferring intent from absence, and restored it in cycle 123. **The rule it produced: when a conflict is a pure deletion, ask whether any commit on the branch performs it.** ⚡ **Screen `08` prints the *true* link expiry — 60 minutes, not the design's 30.** ⛔ **Read [B-148](BUGS.md) before reading `queues/lane-a.toml`.** | **Rulings are outstanding, all the product owner's** — and **Lane C now exists to prepare them.** Its four pushes this cycle are decision packages, not implementation. [PROJECT_STATUS.md §1c](../PROJECT_STATUS.md) has the list and the single action each needs |
| **Head at handoff** | **`a792be6`** — the certification record, one commit past the certified `5a9743a`. ✅ **Plain fast-forwards; no lease** |
| **Latest certification** | ✅ [`5a9743a73b21`](../certification/reports/5a9743a73b21.md) — **CERTIFIED 2026-08-11**, bound to commit `5a9743a`, migration head `0048`, protocol v2, profile `platform`, **first attempt** |
| **Phase** | **Product implementation.** Ten pipeline stages built and frozen behind them; the surface is being exposed |
| **Overall completion** | **~85%** by engineering effort — see [PROJECT_STATUS.md](../PROJECT_STATUS.md), which is authoritative |
| **Branch** | `main` at `a792be6`, certified at `5a9743a`. ⚡ **The product is now measured at `390×844` — a real handset, which no viewport in this repository had ever exercised**, because `phone: 640px` is a min-width. ⚡ **The matrix asserts both axes**: nothing inside a `fixed` region may sit below the fold. ⚠️ **The new check is proven against a forced overflow and NOT against [B-241](BUGS.md)**, which could not be reproduced. ⏳ **Neither lane is ff-able**: Lane A 19 ahead / 21 behind, Lane C 5 / 23 — both need a rebase onto `main`. |

**🔴 Read this before anything else:** **`reasoning@1` has no released model.** M9.5 moved the rendering protocol to v2, which withdrew every protocol-1 release by derivation. `explanation_narration@1`, `research_planning@2` and `research_synthesis@2` re-earned theirs; `reasoning@1` did not — `granite3.3:2b` refuses under protocol 2 and `llama3.1:8b` is UNMEASURABLE on this hardware. **The Decision Package stage would refuse in production.** Do not tune the prompt, the delimiter, the schema or the timeout to make it pass.

**🟢 D37 was ruled on and became D38: the information architecture, reviewed from first principles.** Six navigation entries became two — `Attention` at `/` and `Settings`. Companies, Signals and Timeline were four of thirteen pipeline modules with a menu item each, and none of them is one of the six customer journeys. Overview is retired; the brief moved to `/accounts/[accountId]`. **D1 is settled with it** after two deferrals.

**🟢 `make demo` is now the whole setup.** Stack, schema, Better Auth's tables, **four sign-in accounts**, twelve seeded accounts. Credentials and troubleshooting live in [RUNNING.md](RUNNING.md), which is the single source of truth. The accounts are created through `auth.api.signUpEmail` and `auth.api.verifyEmail` — **the same handlers a browser reaches**, so nothing about the pipeline differs; they simply already exist.

**🟢 Sign-in works now, and did not before.** Better Auth's tables had never been created by anything in the repository, and the `after` hook broke every completed auth request — two defects each hiding the other, invisible because no authentication request had ever finished. Run **`cd frontend && npm run auth:migrate`** once on any clone, then register at `/sign-up`; the verification link is written to the dev server's stdout. **A third defect sat behind those two**: Better Auth's default id is a nanoid and the Python verifier requires a UUID, so every API call from a real signed-in user would have 401'd. Fixed with Better Auth's own `generateId` hook — the *function* form, because `'uuid'` resolves to a column default that inserts null on tables created before it. See [ADR-0033](architecture/adr/0033-authentication-methods.md) and `docs/RUNNING.md`.

**Recent commits:** `0ea5ef5` ⚡ **B-221 — three instances on three consecutive publishes, so it is systematic** · `0325456` 🔴 **Lane A's blockers recorded where they are visible — the board said "Nothing"** · `53052e5` **Closeout — a checklist that failed itself first** · `bb898e5` ⚡ **B-160 strengthened — the coordination check drifts on the wall clock, not on lane activity** · `a68134d` ⚡ **D-213 — the production readiness checklist, and it caught a false pass of its own** · `a68f2d9` **Closeout — the shell's first red edit** · `6c9275a` **Lane A notice — the C-252 ruling, within the cap** · `456bde7` **C-252 answered, C-254 prepared** · `6a3aa1c` 🔴 **B-221 — the coordination notice names a row its own backlog array omits** · `a165ed1` **TASK-1408 — the banner and breadcrumb slots placed** · `a15f2f4` **C-257 — TASK-1408 cannot reach its DoD** · `f4fb959` ⚡ **TASK-1408 — the collapse wired into the frame, and the first shell edit** · `d60a4a1` **Closeout — a locked door you can see** · `a9f7890` ⚡ **TASK-1408 — rail collapse, remembered per user and per device class** · `de6a954` **TASK-1408 — the breadcrumb rendered, and the trail stays a prop** · `d1ddbf6` **C-256 — the banner region has no caller, and the gate found two of three were sequencing** · `80696f9` ⚡ **TASK-1408 — global scope, and the widening a module must not be able to do** · `0af5da0` ⚡ **TASK-1408 — the rail, where a restricted destination stays on screen** · `e353cb9` **Closeout — a blocking gate honoured against QE's interest** · `3b3e891` **Certification record for 5853f391 — certified and deliberately NOT promoted** · `4acb69d` ⚡ **TASK-1408 — the top bar, enforced by absence, and a guard that read its own prose** · `0facb0c` **C-255 — §04 needs three capabilities no row owns** · `dbcca11` **TASK-1408 — the breadcrumb, where the collapse is arithmetic** · `9be235d` ✅ **B-220 superseded by QE's B-161, and its severity lowered by measurement** · `73d5338` **TASK-1408 — the banner region** · `409183b` ⚡ **TASK-1408 — the shell's constitution, as code rather than as a comment** · `7c5c604` **Closeout — the repair branch is one commit stale** · `f954477` ⚡ **C-252, C-253, C-254 — three questions TASK-1409 cannot answer for itself** · `6636e6c` ✅ **TASK-1409 — the scope ladder, and a collision two primitives were always going to have** · `0e0684c` **Closeout — B-159 closed, B-160 filed** · `97a13ce` ⚡ **D-212 — sustained implementation mode, and a gate on myself before the next clarification** · `dcc4e6c` ✅ **D-210 — the shell audit is clean, and both apparent gaps were my vocabulary** · `2afe285` **Claim TASK-1409 — Workflow 28 · System States** · `90eed8b` **Closeout — a flag named --dry-run that writes** · `7bc4b53` ⚡ **D-209 — yes, Lane A can build; and C-251's answer was smaller than the question** · `483ad46` **Closeout — the exclusion that ended by itself** · `6ccea5f` ⚡ **D-208 — three of the four frozen rows should never have been frozen** *(D-198…D-208, eleven rulings)* · `fb4b2e9` 🔴 **B-216 — Lane C built a channel to route past QE, then used it to assert a state** · `14abd98` **Closeout — TASK-1400 VERIFIED, B-155 refined** · `14b3985` ⚡ **C-245 — the other two invitation screens, and one of them must not be built** · `e2e19e8` ✅ **TASK-489 screen 14 — Invitation expired, the half B-214 unblocked** · `68fc188` ⛔ **Closeout — a journey run that measured nothing (B-156, B-157)** · `a540f5e` ⚡ **TASK-439 — the Signal Center queue, and a door that only existed when the list was full** · `2bf7450` ⚡ **TASK-469 milestone 2 — screen 08's skip confirmation, no second ask** · `070bef1` ✅ **B-413's row folded — the duplicate check caught it and QE read the list** · `1b92d07` **Workflow 9 read `planned` while two of its three milestones were on main** · `5bc7ef5` 🔴 **B-413 — the promotion gate reported zero blocking 🔴 for six days** · `461365c` ✅ **B-209 FIXED — eleven journeys, one word** · `a1af45d` ⚡ **TASK-1400 — The Authenticated Entry Engine** · `f94c06a` ⛔ **B-154 — QE promoted a conflict marker into the one register its check does not read** · `901935d` ⛔ **B-153 — QE ran the check that caught a duplicate identifier and grepped past the finding** · `3373af7` ✅ **B-152 VERIFIED — Lane C repaired the ruling, not the file** · `86ad2c6` ⚡ **QE was right about the second projection — and my fix for it was wrong once** *(`TASK-1400` released)* · `9378e82` **TASK-470 — milestones 1 and 2 delivered, milestone 3 blocked with both reasons** · `e85e5d4` ⚡ **screen 04 — AI preferences, and the two rows that are policies** *(migration 0045)* · `ffe4fef` ✅ **B-215 — it was a lost keystroke, not a lost request** · `2ecfe98` ⚡ **TASK-470 milestone 2 — appearance belongs to the account, not the browser** · `2016ac0` ✅ **B-215 — the hypothesis was wrong, and the register says so** · `2fe9843` ⚡ **TASK-470 milestone 1 — a person's profile, and the fields the product cannot honestly show** *(`Resource.PREFERENCES`)* · `a85d852` **D-196 — six epics, eight rows** · `a3b835c` ⚡ **TASK-470 — the preference store** *(migration 0044, `person_preferences`)* · `8fd06c7` ⚡ **TASK-469 — onboarding stops choosing where a person lands** *(D-193 received, verified not yet actionable)* · `90450cc` **B-214 — an expired invitation and a withdrawn one stop arriving identical** · `089a119` ⚡ **TASK-469 milestone 1 — a person is guided into Signora** *(migration 0043)* · `f5d9be5` **Routine cycle — C-244 queued, the floor restored** · `50df5db` 🔴 **D-192 — three shipped journeys end nowhere, and the design said so all along** · `3697e54` ⚡ **D-191 — the premise does not hold, and I recommend against both options** · `dcb8f0f` ⚡ **TASK-498 milestone 5 — the reset link lives thirty minutes, and three screens say so** · `b082413` **The notice channel, re-applied — the rebase dropped it and kept its data** · `aa22cc1` 🔴 **C-245 — screen 13 shows a reader six facts they are not permitted to see** · `4590094` **B-214 — the domain knows an invitation expired and the API cannot say so** · `9b43575` **D-187 — one claimable, twenty prepared behind it** · `d6ba6f7` 🔴 **TASK-488 — Workflow 5 · Password Reset, and the sentence it refuses to print** · `19afc49` ⚡ **TASK-474 — the mailbox is an experience now** · `2a35ac1` 🔴 **B-151 — the dashboard said "Blocking Quality Defects: None" while two were open** · `64373a8` ⚡ **TASK-474 milestone 1 — the mailbox's store, its transport and its refusal** · `c6e9278` ⚡ **TASK-498 — three ruled controls registered, in the one file every row forbade** · `7a802d1` **TASK-483 — the shell was already correct, so the deliverable is the guard** · `82084ed` 🔴 **B-150 — the conflict marker QE promoted, repaired, and the check QE skipped** · `adce341` ⛔ **B-411 — restoring the line QE deleted, because QE deleted it** · `16d6084` **D-185 — both decisions applied** · `80c21b1` ⚡ **TASK-484 — the two journeys, one delivered and one carried as far as it goes** · `3ed76cf` **D-184 — the floor is ten** · `c1caeab` **D-183 — five claimable rows, in an order** · `37292b5` ⚡ **C-242 update — the synchronization dependency has grown from four rows to six** · `5e06adc` **Lane A's map is correct, its parser beat mine** · `2259cc2` ⚡ **TASK-487 — screen 08 · Reset your password, and the expiry it prints is true** · `2f858a3` ⚡ **Workflow 4 released, and C-241 was answered two screens above where I looked** · `eac9a9c` **Routine check — the release trigger fired for ten rows** · `67d662e` **D-182 — Workflow 8 decomposed, because it was the cliff** · `4b7f1b9` ⚡ **TASK-486 milestone 1 — screen 07 · Verify email, and the six boxes are not built** · `891e2c4` **D-181 — the ref is recovered, and the hand-rolled push is gone** · `6f88ece` **C-240 is RULED** · `85ef84d` ⚡ **TASK-494 — email leaves the process through Resend, behind the existing port** · `063908a` **D-180 — execution mode accepted** · `dd9e836` **B-149 FIXED — the journey addresses its own password field, verified headed** · `ea79500` **C-240 — renumbered into Lane A's own block** · `50e8113` **D-179 — adoption becomes state** · `6394ff6` **Lane A delivered Workflow 2 and went to zero claimable** · `fee72e2` ⚡ **TASK-485 milestone 1 — screen 06 · Create account, to the approved design** · `e60e5e3` **C-435 is allocated twice, and the block model failed for the first time** · `6f91974` **D-173 — the coupling is a ruling already made and half-implemented** · `d989172` **C-435 — the synchronization deadlock** · `11ef155` **Lane A cannot claim TASK-485 yet** *(⛔ [B-148](BUGS.md) — it could, and did)* · `c584e8e` **B-409 — the starvation check counted finished work** · `018195f` **Claim TASK-485** · `f6f9c85` **Workflow 1 is on main at 12 of 12 design elements, and Workflow 2 releases itself** · `1e09e25` **D-171 — the operating model, critiqued as it asked** · `9aae52b` **Workflow 1 milestone 4 — the workflow is complete** · `16ba152` **427 step 2 — a run records the profile the planner computed** · `f6df17e` **Workflow 1 milestone 3 — the front door, the enterprise route, and the two states between signed in and signed out** · `18fa051` **D-165 — Lane B is gone from the active model** · `5391744` **D-163 — the queue advances itself, and a check now says so every run** · `d8f5ab1` **D-162 — the foundation gates everything** · `ab1ba57` **D-161 — Lane A built the right screen against the wrong palette, and that is my defect** · `8295fdb` **Workflow 1 milestone 1 — the authentication shell, rebuilt from the design** · `ba0520a` **TASK-458 — a decision-maker signal can say which seat, and for how long** · `67fe1a8` **Lane A is unblocked, and the thing that would have blocked it next is fixed too** · `a4de1c3` **D-156 — Workflow 1 is four screens, not three** · `ecc2cc3` **Two decision-queue entries retired — both were answered and both still asked** · `c2aecd3` **Poll — D-152, D-153 and D-154 are all on main, and the queue stops saying otherwise** · `6555968` **D-154 — one file asserts a visual value, and one test is why** · `7bf7380` **B-145 — the coordination source goes stale by the clock** · `ba90459` **M-I · who has held a role at a company, and who left** · `2894c40` **C-430 holds two lanes, not one — Lane A found the far end of its own chain** · `d437932` **C-238 — the port is typed, and nothing implements it** · `6fdb6cc` **B-407 answered — the guarantee holds, and the finding is a transient-window artifact** · `e932b87` **TASK-428 — a role change becomes an affiliation, and C-237's reader** · `02fe658` **TASK-444 — the catalog learns which rules misfire** · `dae6417` **B-140 — a failing gate reported its verdict and discarded its evidence** · `eb07eb0` **B-138 — the Coordination subsystem lands, and a lane's poll becomes one fetch and one read** · `d66e223` **B-137 — state-check read the last certification attempt and called it the last certification** · `9ba145f` **TASK-202 — reasoning@2, and why the credential was never sufficient** · `8cff168` **TASK-901 slice 3 — buying_score_engine consumes what it declares** · `af6ddd2` closeout `b5cff6f` · `b5cff6f` **TASK-440 carried two states, and the first was Lane C's own** · `f20a53a` **TASK-901 slice 1 — a declaration asks for a provider read, C-021 answered** · `258aa94` closeout `c160921` · `c160921` **D-137/138 — the design lives in the repository** · `aef01d4` **TASK-472 — a workspace can list its accounts** · `e588dac` **TASK-406 — an ICP criterion is scored against outcomes** · `c4754b5` closeout `0869861` · `0869861` **TASK-460 — Global Search renders the groups it has been sent all along** · `8664e51` **TASK-456 — the catalog explains itself in one field rather than four** · `7c68039` closeout `766fd4c` · `766fd4c` **B-133 filed — an unused import the image build refused** · `8d14f07` **B-132 — the fake implements for_workspace** · `4dbcab4` **TASK-443 — a workspace's history is queryable** · `519e845` closeout `92b5d87` · `92b5d87` **TASK-446 — an account's observed attributes have a publisher** · `004ec06` **TASK-201 — a committee seat can be cited** · `849fdb7` closeout `5743a90` · `5743a90` **C-230 — Lane A's assignable work is exhausted** · `1dae9ed` **B-131 — certification reports what the plan required and it did not run** · `49bf2b5` closeout `3eec247` · `3eec247` **Lane C's batch — the Validation Planner (D-115), execution state as a check (D-123)** · `d243c32` closeout `78705c2` · `78705c2` **TASK-427 — a person, and an affiliation that closes rather than being overwritten** · `5c31293` closeout `a7c9839` · `a7c9839` **TASK-432 — a triaged signal says so, and the pipeline hears it** · `bcea8ba` closeout `e636018` · `e636018` **D-105 — three approved screens decomposed** · `3ff0b2a` **TASK-400 — a seller can see whether Signora is still watching a company** · `b0ed594` closeout `b562226` · `b562226` **QE's escalation — one row was Lane C's to release** · `c8c9ab9` **C-104 answered, and QE reasoned from a false positive** · `bf4aa65` closeout `f1eddf4` · `f1eddf4` **D-100 — every coordination item declares an owner and a state** · `35c22a5` closeout `ef3e51f` · `ef3e51f` **D-099 — B-327 was FIXED and was not, and the duplicate id is what hid it** · `b6ec848` **465 — across 70 certifications, no gate has caught a product defect** · `397f62d` **B-328 — the gate says 54 READY, this lane said zero, and there are two** · `c3f8c0a` closeout `6e7bcdb` · `6e7bcdb` **D-097 — check ⑧, and the queue validator caught two of its author's own** · `a1dfa84` **C-420 — matching.py becomes evaluation.py while that is still free** · `a6eee5d` closeout `ff3ac8f` · `ff3ac8f` **D-093 — the discovery phase closes** · `ff01301` **TASK-438 — the pipeline says how it is doing** · `ac65c73` **B-123 — stage 1 runs the frontend suite** · `7606e0f` closeout `ce1a658` · `ce1a658` **B-126 — the duplicate was a second design doc** · `8eb2fb5` **B-127 — an ended membership grants nothing, and the guarantee outlives the feature** · `79bbf8b` closeout `f14db51` · `f14db51` **TASK-437 — a member can leave, and removal starts actually revoking access (B-206)** · `be9c65f` closeout `4dd2f21` · `4dd2f21` **B-205's mechanical half — a check for a document warning it is not on `integration` while it is** · `a4efd54` closeout `6b7b04e` · `6b7b04e` **M14 — a person can be permitted to leave, and nobody gains the power to eject** · `fec8b5b` **TASK-434 — an account can be asked whether it matches a criterion** · `cebbba7` closeout `772eebe` · `772eebe` **TASK-408 — a search that finds nothing of a kind says so** · `c8c4511` **B-205 — three documents disagree about a bounded context** · `2a5fb75` **TASK-436 — `provider_platform` builds its own registry** · `69a7f11` **three Lane A slices, and a returned test fixed by declaring the route** · `839e8b0` **TASK-904 — an invitation becomes a membership** · `3e4a924` **D-073 — `signora_platform` has an owner, and the generators are tested** · `f7a0d1d` **the register audits itself, and B-120 files the untested generators** · `3c12b5d` **TASK-417 — wave 1 complete, and the audit is the half worth reporting** · `8ea9db8` **TASK-415 — every AI path runs without downloading a model** · `5bc5c79` **one compose project per environment — B-118's root cause removed** · `9ff285d` **TASK-405 — the queue reads by state, and a snooze returns** · `b871f18` **execution isolation — the workstation lease, and the end of phantom failures** · `acb774b` **TASK-405 — a signal's resolution, as a record rather than a field** · `56b9c53` **TASK-414 impact analysis, published queues, and the gate Lane C did not run on its own test** · `914f1dc` **A-ii — a seller can ask who to talk to at an account** · `9ce7b77` **Lane A resumes, `make doctor` ships, `demo` enters the model** · `1e55191` **the lane consolidation — module assignment becomes authoritative** · `3ab3111` **Lane C's Platform Foundation batch — `infra/` gets an owner, C-010 closes** · `c60bb39` **the lifecycle terminology, applied to work that was correctly begun** · `ea35fbe` **Epic E1's Integrations half — the port a customer's CRM will arrive through** · `dd91c62` **TASK-407 — a connection says whether it actually works** · `7a95403` **A-i — Signora's conclusion about an account can finally be read** · `85845c6` **TASK-301 — a search result says what kind of thing it is** · `f7439ca` **[B-112](BUGS.md) — the gatekeeper stops answering from a stale clone** · `9af6144` Lane B reports AVAILABLE · `d392ed5` **Lane B — register closures and the C-103 union** · `b332aea` **B-111 — tsc becomes a gate, and main type-checks again** · `a955016` **Lane A — Sales Engagement, Sales Workspace, Team Management** · `9a112ae` **Lane B — ICP segments, CRM acquisition, refresh revocation** · `ba46132` **make workstation, and a backlog item closed by measuring it** · `630fc79` **RE-03 — certification provisions its own database** · `08226e5` **the event catalog drift check** · `b0d10b3` **Lane C — the repository gets a Product Office** · `47cdfd0` **Lane C readiness — the infrastructure is ready and the decision queue is not** · `65c8b2c` **the production stack leaves the review ports** · `bdc159f` **RS-1 — `make unsaved`, and a measurement corrected by 4x** · `f034364` **`make review` — a product review is one command, and it leaves a record** · `909374a` **the branch guard and L-17** · `190e340` **machine resources are a fifth isolation layer** · `68ac56e` **smoke reports its slowest stage** · `9484228` **Redis isolation — a shared queue executes** · `514de85` **[B-104](BUGS.md) — the auth tier had one database for every environment** · `9ef2f25` **[ADR-0100](architecture/adr/0100-delegated-dependency-rulings.md) — ten delegated rulings** · `fd2d942` **PQ-02 — a route nothing leads to is a finding** · `ebcf690` **the environment lease — one operation owns the stack** · `5c47a0d` **RE-01 — certification attempts become countable** · `34d8acb` **the preflight names the container** · `77a37fa` **Dependency Health Review — 32 items become 5 decisions** · `d39b136` **[ENGINEERING_LAWS.md](../ENGINEERING_LAWS.md) — the Repository Engineering Standard, thirteen laws** · `fec1424` **[B-101](BUGS.md) — the KPI block counted nine rows twice** · `1e269f5` **[B-100](BUGS.md) — a rebase moved the board back seven cycles, and no gate could see it** · `cb5cd33` Lane A's Team Management discovery (documentation only) · `4ebe68c` closeout `2262bb5` · `2262bb5` **[B-301](BUGS.md) — Timeline consumes what it projects** · `e5a266d` **35 commits — Lane A's product surface and provider platform batch** · `b9278c6` closeout `bd57c7c` · `bd57c7c` **M13-S09 — the credential store gets tested** · `3ef367d` M13-S02 the connections a customer can see · `e08c7cb` **M13-S01 — a customer's connection to their own systems** · `056a53a` **M7-S04a — the history a seller can read** · `c3435a0` ADR-0039 accepted as direction · `1bbee30` **certification binds to a commit** · `3f4e988` **M12.5 — the pipeline finally has an input**

**Where everything now lives.** Five registers, one responsibility each, and a session should read all five before its first slice: [BACKLOG.md](BACKLOG.md) *what is available to claim* · [BUGS.md](BUGS.md) *what is wrong* · [LANE_COORDINATION.md](LANE_COORDINATION.md) *what one lane needs from another* · [ACTIVE_ASSIGNMENTS.md](ACTIVE_ASSIGNMENTS.md) *who is doing what* · [RUNNING.md](RUNNING.md) *which ports and database are yours*. The rules governing all of them are `CLAUDE.md` §20e; how QE operates them is [QUALITY_ENGINEERING.md](QUALITY_ENGINEERING.md), and the cycle itself is [REPOSITORY_RELEASE_CHECKLIST.md](REPOSITORY_RELEASE_CHECKLIST.md).

### What a session needs operationally

**Every measured figure — test counts, coverage, invariants, contracts, migrations — is in [PROJECT_STATUS.md §4](../PROJECT_STATUS.md).** It is deliberately not duplicated here: two copies of one measurement eventually disagree, and the copy nobody re-measures is the one somebody reads.

| | |
|---|---|
| **Certification** | ✅ **CERTIFIED** — [`f954477e9e42`](../certification/reports/f954477e9e42.md), bound to **commit `f954477`** and migration head `0045`. ⛔ **START HERE: `origin/integration` is DIVERGED from `main` at `227a074f`** — [B-161](BUGS.md). ✅ **`main` carries ALL FOUR of its commits, proved by `git patch-id --stable` — nothing would be lost.** ⛔ **The one repair is `git push --force-with-lease=integration:227a074f origin main:integration`, and this environment has refused it SIX times.** ⚠️ **The gap is now 33 commits.** ✅ **Lane A rebased and fast-forwarded.** ⛔ **A second consequence: `--next-cycle` compares `integration` against the certified SHA, so while `integration` is diverged it reports CERTIFICATION CYCLE AVAILABLE permanently — do not read that as a signal.** ⛔ **§20e Startup step 1 and Claim Protocol steps 1 and 7 all tell a lane to begin from `integration` — so a lane following the protocol literally starts 27 commits stale. Build every candidate by rebasing the lane branch onto `main`.** ⚡ **The repository still functions: build every candidate by rebasing the lane branch onto `main`, never onto `origin/integration`.** ✅ **[B-159](BUGS.md) closed — `coordination.toml` now reports `claimable_now = 22`, matching `BACKLOG.md`.** ⛔ **But [B-160](BUGS.md): `coordination.py --check` still exits 1 on two volatile metrics, so *do not read a `--check` failure as staleness* — diff `_content` and look at what actually differs.** ⚠️ **[B-158](BUGS.md) — `--dry-run` writes; never run it to inspect.** ✅ **The seven-cycle Lane C exclusion is over — fifteen commits rebased clean, [B-155](BUGS.md) answered by the branch rather than by QE.** ⚡ **`state-check` fell 5 → 2 findings.** ⚡ **[C-245](LANE_COORDINATION.md) is with the product owner and is a *disclosure* ruling, not a scheduling one — screen 13 cannot be built without weakening `InvitationNotFoundError`'s deliberate flattening.** ⛔ **Read [B-156](BUGS.md) first if you are about to run journeys: `make e2e` off a lane branch builds `http://localhost` with no port, passes both of the suite's URL guards, and reports 157 failures that measured nothing.** ⚠️ **Lane C is 12 ahead / 2 behind — diverged, sixth exclusion, now [B-155](BUGS.md); nobody blocked, planning throughput the cost.** 🔴 **Read [B-413](BUGS.md) first: the promotion gate returned `False` for every bug row for six days, and 70 Closeouts were made under it. Repaired and proved able to fail.** ⚡ **[D-200](DECISION_REGISTER.md) ruled — see [PROJECT_STATUS.md §1f](../PROJECT_STATUS.md).** ⛔ **`state-check`'s corruption check now reads six registers, not four** ([B-154](BUGS.md)). It expires by derivation the moment a migration, a prompt release, the rendering protocol or the scenario set changes. **`make certified ARGS="--audit-main"` proves the guarantee across the whole branch** |
| **Lane C** | **Product Office & Architecture Office**, created 2026-08-03, **operational 2026-08-04.** Producing decision packages — *"five blocking items reduced to four decisions, three of them signatures"*. Its branch is documentation-only and 153 behind `integration`, which is correct: **it owns no module and needs no runtime**, so nothing it writes needs certifying |
| **Active lanes** | [ACTIVE_ASSIGNMENTS.md](ACTIVE_ASSIGNMENTS.md) — the execution board. **Both feature lanes are `AVAILABLE`**: Lane A finished R2-01 and Lane B finished M12.5. **Both are building**: Lane A holds TASK-002, Lane B holds TASK-001. **A claim is pushed to `integration`**, which is the ref every lane pulls — pushing it only to a lane branch is how the protocol failed to arbitrate on its first day |
| **Open blockers** | [C-010](LANE_COORDINATION.md) — no lane is assignable to `apps/`, `signora_platform/` or repository process. **Three defects landed in that gap this cycle** ([B-007](BUGS.md), [B-012](BUGS.md), [B-013](BUGS.md)); the last was fixed only because the product owner directed QE to touch it. [C-012](LANE_COORDINATION.md)/[C-013](LANE_COORDINATION.md) wait on RFCs queued since M3A |
| **Open defects** | [BUGS.md](BUGS.md) — **0 open 🔴.** Seven rows are `FIXED` awaiting verification, and **[B-009](BUGS.md), [B-013](BUGS.md) and [B-014](BUGS.md) may not be closed by QE**, which fixed them |
| **Pending work** | **[BACKLOG.md](BACKLOG.md) is the queue** — `TASK-001`…`TASK-016`: 5 `READY`, 8 `WAITING`, 3 `BLOCKED`. **Start at TASK-001.** M12.3 list hierarchy (D20) · **M9.5 Step F** · [B-010](BUGS.md) — nothing narrates in the Playground, so M12.3's headline feature cannot be demonstrated · `reasoning@1` still has no released model (below) |
| **A second ruling QE cannot make** | **[C-104](LANE_COORDINATION.md)** — `POST /connections/{id}/check` calls HubSpot **inside the request handler**, and §7 names provider calls among what must not be synchronous. **No gate fails**, the call is bounded, the abstraction holds, and the lane argued the case in the route's docstring. **The concern is precedent** — the next lane wanting a synchronous vendor call will cite this endpoint |
| **One ruling QE cannot make** | **[B-113](BUGS.md)** — `certification-guard.py --audit-claims` has a **permanent** known failure: a claim commit from 2026-08-02 that also touched the coordination register, 235 commits back on `main`. Rewriting history is ⚫, baselining past it narrows a gate to stop it failing, and declaring a historic exception is a governance act. **A check with a permanent failure stops being read**, which is the actual cost |
| **Recommendations** | **For the product owner, in [BACKLOG.md](BACKLOG.md) order:** rule [C-010](LANE_COORDINATION.md) — four defects have now landed in code no lane may touch — then choose an option for [C-008](LANE_COORDINATION.md), whose proposal is accepted and waiting. **The lanes need nothing from anybody**: both are `AVAILABLE` and the queue has claimable work at the top |
| **QE's next action** | ⚠️ **[B-123](BUGS.md) — run `vitest` by hand until the gate exists.** `certify` and `validate` both omit it, so **1255 frontend tests are run by nobody**, and a slice whose tests are entirely frontend passes `make validate` completely. It caught a real failure on its first hand-run. **Lane B is validated and needs one rebase** |
| **The constraint** | **Supply, not process.** Lane B is idle having found nothing eligible; [C-020](LANE_COORDINATION.md) leaves M7 without a scope. Product-owner work, and QE is not compensating for it |
| **Governance** | **Stable, and evolving reactively from now on** (`CLAUDE.md` §20e). Build product · observe execution · change governance only when execution reveals a bottleneck. **Do not refine it because you can** |
| **Lane A, first thing** | **Your claim on TASK-002 exists only on `lane-a-product-surface`.** Under the corrected protocol it belongs on `integration`, where other lanes can see it — push it there before continuing, or the queue keeps reading TASK-002 as free |
| **Before your first slice** | **Rebase onto `integration`.** It was rewritten on 2026-08-02 to reconcile a merge commit on `main` ([B-012](BUGS.md)); a lane branch created before that will not fast-forward |
| **Tooling** | `make` was absent from this workstation and was installed 2026-08-02 ([B-011](BUGS.md), [RUNNING.md](RUNNING.md)). **A missing prerequisite is installed, not worked around** (`CLAUDE.md` §20e). **Do *not* export lane database variables for `make certify` or `make validate`** — since [B-106](BUGS.md)/RE-03 both **create and drop their own database**, and an exported variable is the hidden input those changes removed |

**Local prerequisites:** Docker · `uv` on `PATH` (`~/.local/bin`) · Postgres and Redis via `infra/docker-compose.yml`. Tests need all three lane database variables plus `SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1` ([RUNNING.md § Running a lane](RUNNING.md#running-a-lane)) — the suite truncates, and the flag is a deliberate guard. **`make` is required and is now installed.**

---

## 1b · Blockers and dependencies — nothing here is discoverable from the code

> **Written 2026-08-11 by QE.** ⚡ **Every row names who owns the next move**, because the failure this section exists to prevent is a blocker that looks answered. ⛔ **A stale assignee is worse than a missing one** ([C-213](LANE_COORDINATION.md)).

### Waiting on the product owner

| | Blocks | Owner |
|---|---|---|
| **`lane-qe` remote push** — `origin/lane-qe` is at `37e095c6`, the guard commit **before** it was amended with the real-git regressions. Local is `main`. **Needs `--force-with-lease=lane-qe:37e095c6`** | Nothing executable. `lane-qe`'s content is on `main` and certified | **Product owner** — deliberately held; both remote-ref operations were scoped as one controlled pair |

### Waiting on a lane

| | Blocks | Owner |
|---|---|---|
| **Lane A rebase onto `integration`** (`ab519d82`). Its branch is 9 ahead of `main` but does **not** fast-forward from `integration` | ⛔ **The whole certification cycle.** `--next-cycle` says a cycle is available and the candidate cannot be assembled without it | **Lane A** |
| **[B-179](BUGS.md)** — the Team screen never settles at 1024/1280 | Nothing yet; it will block any measurement of that screen | **Lane A** (`product_surface`) |
| **Lane B is 641 commits behind** with 2 uncertified commits on its branch | Its own work only | **Lane B** |

### QE's own, and none of them block another lane

| | State |
|---|---|
| **[B-181](BUGS.md)** — `production-readiness.py` greps `backend/` for a limiter that lives in `frontend/lib/auth/`. **Green twice for two different wrong reasons** | `OPEN`. ⛔ **Do not fix by widening the glob** — the discriminating property is `storage`, not `enabled` |
| **[B-177](BUGS.md)** — `mypy --strict` passes over 564 files and fails over 866; nothing tells a lane which scope the gate uses | **Lane's half FIXED, QE's half `OPEN`.** The next lane pays it again |
| **[B-173](BUGS.md)** — `--promote` reads the certification record from the working tree while the merge needs it clean | `OPEN`, **five occurrences**. Worked around by ordering every cycle |
| **[B-156](BUGS.md)** — a journey run with no port passes both URL guards | ⚠️ **Environment half SOLVED 2026-08-11** *(see the row — `auth.user` was missing from `signora_lane_qe`)*. **The guard half is untouched** |
| **[B-161](BUGS.md) · [B-220](BUGS.md) · [B-238](BUGS.md)** — one defect, three rows | **Repair shipped and certified** (`_claim_stowaways`). ⛔ **Consolidate before closing**: discovery · diagnosis · repair · protecting test, in that order |
| **[B-180](BUGS.md)** — QE's layout invariant could not fail | **FIXED**, fire-tested both directions. QE does not close its own row |
| **The responsive matrix is uncertified** | 26 checks across four breakpoints, running against the real product on `lane-qe`. ⛔ **Not counted as coverage until it goes through a cycle** |

### Dependencies that are decisions, not work

| | Owner |
|---|---|
| **C-1405 — Workspace Chooser** | **Product owner.** The only outstanding design decision |
| **C-287 — inbound rate limiting** | **Deferred** until Better Auth 1.1.0 is verified. [TASK-1430](BACKLOG.md) stays `BLOCKED` either way |
| **C-285 · C-286** — three designs publish shortcut tables with colliding chords; the design's card is three columns and the shared `Dialog` is 448px and 🔴 | **Product owner** |

### The environment fact that cost the most, so it is written down once

> ⛔ **`frontend/.env.local` points `SIGNORA_AUTH_DATABASE_URL` at `signora` — the Playground.** **Every QE auth/seed command must override it**, and **the dev server must be started with the override too**, or the app authenticates against a database the personas are not in. ✅ **QE verified `signora` was untouched afterwards, and that verification should be repeated every time.**

---

## 2 · Architecture state

Permanent contracts. Each is enforced by automated test, not convention. **Changing any of these requires an RFC.**

### Foundations

| Contract | Established | What it guarantees |
|---|---|---|
| **Platform Runtime** | M1.1 | Transactional outbox, relay, dispatch, platform-owned idempotency, retry, dead-lettering, worker pools. Consumers are idempotent on `event_id`; nothing assumes exactly-once or cross-entity ordering. |
| **Authentication Boundary** | M1.2 | Better Auth in Next.js is the sole authentication authority. The Python tier **only verifies** RS256 JWTs and is cryptographically incapable of minting one. Algorithms pinned to exactly `["RS256"]`. |
| **Deployment Foundation** | M1.3A | Production images, per-tier database identities, concurrency-safe migration runner, restart-safe stack. `/ready` returns **503** when not ready — orchestrators route on the code, not the body. |
| **Platform Smoke Test** | M1.4 | One command verifies the whole platform. Required before every milestone and release. |
| **Local-First verification** | 2026-07-29 | Every gate runs locally ([ADR-0027](architecture/adr/0027-local-first-development.md), CLAUDE.md §20c-2). GitHub is version control, backup, and future collaboration only; Actions are disabled and the three workflows are retained at `workflow_dispatch`. **A `git push` stores the repository and triggers nothing.** CI returns only when the architecture, Intelligence Pipeline, Workflow Pipeline and AI Platform have all stabilised **and** it is explicitly requested. |
| **Platform Freeze** | M1.3A | `signora_platform/` changes only for a security fix, production defect, or approved change. **One change since:** the relay's transient-failure handling. |
| **Frontend Foundation** | M1.5 | Design system, components, shell, routing, query layer — consumed, not modified. Exceptions: production defect, **accessibility issue**, security issue, approved change. |

### Tenancy and data

| Contract | What it guarantees |
|---|---|
| **Tenant Isolation Policy** | Every table declared tenant-owned or platform infrastructure — **classification is never inferred**. Tenant tables carry a non-null identifier, RLS enabled **and forced**, and policies covering SELECT/INSERT/UPDATE separately. A table in neither list fails the build. |
| **Migration / runtime credential separation** | Runtime services never execute under migration or owner credentials. Each tier holds its own least-privileged role: `signora_app` (API, workers), `signora_auth` (frontend), `signora_relay` (outbox), owner (migrations only). |
| **Platform Infrastructure Policy** | `outbox_event`, `processed_event`, `dead_letter_event`, `alembic_version` are owned by platform services. The application **publishes and cannot read**; only the relay consumes. Isolation is by grant, since these tables span workspaces and have no RLS. |
| **Immutable tenant tables** | `claim`, `resolution_decision`, `observation`, `business_event`, `signal`, `signal_profile`, `buying_score`, `workspace_scoring_model`, `opportunity`, `opportunity_state`, and `workspace_opportunity_policy` are immutable. **Workflow required no exception** — M6 added three tables and none of them needed the grant. `signora_app` holds **no `UPDATE` grant** on any of them — an attempted overwrite fails with a permission error. `DELETE` remains, because all are derived and regeneration is the rollback for a broken mapper or rule. |
| **Shared vocabulary** | `provider_normalization/public` — the canonical attributes, their value types, and the frozen claim views — is a **platform-wide contract** every downstream pipeline module may depend on (ratified 2026-07-29). A vocabulary dependency, not a data-access one: claim *data* still travels through read ports. Extending it still requires an RFC. |
| **Module boundaries, enforced** | Since M3A, import-linter carries a contract per module pair: no module may import another's `domain/`, `application/`, `infrastructure/`, or `interface/`, and upstream modules cannot import downstream ones. Data crosses via a **read port on `public/`** — a Protocol plus frozen views, never an ORM instance. |

### Provider layer

| Contract | What it guarantees |
|---|---|
| **Provider neutrality** | The Provider Platform never knows which provider — or whether it is simulated. It knows only that it holds a Provider Port implementation. |
| **Pipeline neutrality (AC-21)** | **Behavioural, not informational.** Metadata may exist (`ProviderResponse.simulated`, `ProviderDescriptor.simulated`, `ProviderName`) provided no business behaviour changes, no branching occurs, and no simulation-specific execution path exists. Asserted directly: nothing branches on simulation state or provider identity. |
| **Provider Independence (AC-20)** | Each generator and mapper is independently removable. Scenarios compose providers; **providers never depend on each other**. |
| **Identical adapter contract** | Simulated and production adapters satisfy the same Port, verified by **one shared contract suite run against both**. This is the keystone test — the only mechanism catching drift between the two paths. |
| **Payload provenance** | A simulated payload's shape must come from official documentation, a vendor sandbox, a recorded test account, or a sanitized production response. **Never invented.** All five providers are currently `Conditional` with clearly-marked development fixtures. |

### Evidence

| Contract | What it guarantees |
|---|---|
| **Evidence-first architecture** | **Normalization preserves evidence; it does not determine truth.** No identity resolution, no reconciliation, no ranking, no confidence. Truth belongs downstream. |
| **The Claim model** | The unit of evidence: *this provider asserted this attribute had this value, as of this time, and here is the raw record.* Disagreement survives — two providers reporting different headcounts produce two claims. |
| **No confidence at normalization** | Normalization has no authority to estimate it. A number invented there would propagate into buying scores as though it meant something. |
| **Canonical vocabulary** | 15 attributes, closed and explicitly typed. **Adding one requires an RFC**; adding a mapper is routine. That asymmetry lets integrations evolve while the platform's language stays stable. |
| **Evidence chain** | Every claim carries provider, raw record id, `observed_at`, mapper version, and payload provenance. Zero orphans, asserted by join. **The chain begins at normalization and must never be weakened.** |
| **Fail loudly** | Unknown, missing, and unparseable are distinct rejection reasons, each naming its field path. A vendor shape change surfaces as a rising rejection rate, diagnosable without reading source. |

### Knowledge

| Contract | What it guarantees |
|---|---|
| **Identity, never truth** | **The Knowledge Graph resolves identity. The Knowledge Graph does not resolve truth.** `entity` has **no attribute columns** — asserted structurally. `ClaimSet` returns every contributing claim rather than a chosen value. Ratified 2026-07-28; changing it requires an RFC. |
| **Deterministic resolution** | Three rules in precedence order — provider's own key, exact domain, legal name plus country. No fuzzy matching, no similarity thresholds, no probabilistic scoring. The same claims in any order produce the same graph. |
| **`MatchStrength` is never a number** | A semantic category describing the *rule*, never a score. It must never participate in a weighted calculation or underpin heuristic resolution. **The type itself refuses** numeric conversion and ordering — `int()`, `float()`, `<`, `>` all raise. Ratified 2026-07-29. |
| **Ambiguity merges nothing** | Two matching candidates produce an `AMBIGUOUS` decision naming both and **merge nothing** — enforced by a database CHECK constraint, not by the code path that writes the row. An under-merge is a visible duplicate; an over-merge silently mixes two customers' intelligence. |
| **Decisions explain themselves** | Every binding traces to a decision naming its rule **and the value that matched**. Corrections supersede rather than mutate; on an immutable table the pointer necessarily points **backwards** (`supersedes`), because a forward one would require an `UPDATE` grant. |

### Change

| Contract | What it guarantees |
|---|---|
| **The layering principle** | *Claims preserve evidence · the Knowledge Graph resolves identity · the Observation Engine detects change · the Business Event Engine determines business meaning · the Signal Engine determines commercial meaning.* **Each stage answers one question and refuses the next one.** Ratified 2026-07-29. |
| **Change, never significance** | No threshold exists in the Observation Engine. A Security Invariant reads its derivation and use case as **syntax trees** and fails if magnitude is ever compared against a constant — so the prose explaining that there is no threshold cannot be mistaken for one. |
| **Per-provider series only** | Change is computed **within one provider's series**. Two providers reporting different values is *disagreement*, not movement; merging would manufacture growth that never happened. `derive` takes a single `provider`, so the bug is not expressible. |
| **Restraint** | **Re-assertion is never an observation** — the dominant case in a polling pipeline. The **first value establishes a baseline** and produces nothing: Signora merely learned, and `entity.created` already says that once per company. |
| **Derived identity** | An observation's id is a UUIDv5 over the observed facts — never allocated, and deliberately **not keyed on claim ids**, which are minted when a mapper runs. Deduplication is a primary-key conflict, and regenerating claims cannot duplicate the table. |
| **Refinement, not rewriting** | A late-arriving claim makes an earlier observation *less precise*, not false. The finer observations name the coarser one; it stays readable as what was believed then. |

### Business meaning

| Contract | What it guarantees |
|---|---|
| **Business relevance, never commercial judgement** | The Business Event Engine answers *"why is this business-relevant?"* and never *"should we engage this account?"*. No priority, score, urgency, or rank on `business_event` — enforced by a column-name invariant. Ratified 2026-07-29. |
| **Taxonomy is data; rules are code** | The taxonomy — types, meanings, and **every materiality threshold** — is a versioned repository artifact reviewed like code. Correlation logic is Python. Meaning evolves slowly; derivation may evolve fast, and a better rule must not change what a hiring surge *is*. |
| **No threshold in code** | Rule modules are parsed as **syntax trees**; any numeric literal in a comparison other than `0` or `1` fails the build. Declared parameters and read parameters are reconciled in both directions, and every type has exactly one rule, validated at engine construction. |
| **Agreement is evidence, not truth** | Each provider's series is evaluated alone, so no rule combines two providers' values. Two providers reaching one conclusion produce **one** event recording both — a set, never a coefficient. This is the pipeline's only cross-provider reasoning, and it is deliberately narrow. |
| **The taxonomy is a product asset** | Every type passes the CRO test: *would they immediately understand what this means?* No provider, implementation, or engineering terminology — asserted by invariant, including that business domains never name a data-model term. |
| **Two versions, never conflated** | `taxonomy_version` is meaning; `payload_version` is wire shape. Conflating them means tuning a threshold breaks a consumer contract, so nobody ever tunes a threshold. |

### Commercial meaning

| Contract | What it guarantees |
|---|---|
| **The global/subjective boundary** | *Business events describe objective business phenomena; signals describe customer-specific commercial hypotheses.* Signals are the **first subjective layer**. Everything above the Signal Engine is globally true; everything below stays traceable back to globally true information. Ratified 2026-07-29. |
| **Ownership decides where configuration lives** | Not technology. Signora's language — the business event taxonomy and the signal catalog — ships as versioned repository artifacts. The customer's commercial position — the signal profile — lives in versioned, immutable, attributed rows. Apply this criterion whenever a similar question arises. |
| **The signal vocabulary stays global** | A workspace configures *relevance* and **can never invent a type** — structurally unrepresentable, since `ProfileEntry.signal_type` is typed as `SignalType`. This is what makes AI prompting, benchmarking, analytics, documentation, and support work across customers. |
| **No commercial verdict in the Signal Engine** | No score, priority, likelihood, or rank. Relevance is a category with no numeric meaning; the module contains no numbers beyond windows and counts. |
| **Contradiction is preserved** | Opposing hypotheses coexist for one account and are never reconciled — the claim-disagreement principle one layer up. |
| **Composites enrich, never replace** | Constituent signals are generated and stored independently; the composite **names** them and adds context on top of history rather than collapsing it. |
| **Hypotheses are phrased as possibilities** | *may*, *might*, *suggests* — asserted by invariant. A type stating its hypothesis as fact has drifted into the Business Event Engine's territory. |
| **Two replay modes, never conflated** | Historical (reproduce what we told them) and current (what would we say now). Both first-class. |
| **Customer-authored data is different** | `signal_profile` cannot be regenerated from anything. Signals are derived and rebuildable; profiles need the operational rigour of customer-owned data. |
| **Downstream references business events directly** | Signals, Buying Scores, Opportunities, and AI explanations reference **business event types**, not re-derived meaning from observations. A module that reconstructs *"this looks like a hiring surge"* from raw observations has forked the vocabulary, and two definitions of one concept diverge within a year. Ratified 2026-07-29. |

### Commercial attention

| Contract | What it guarantees |
|---|---|
| **Prioritization, never resolution** | *Buying scores prioritize commercial attention. They do not predict purchasing behaviour, estimate probability, or resolve contradiction. They summarize **explainable** commercial attention.* Deciding which contradictory hypothesis is true needs evidence this module lacks and judgement belonging to AI Reasoning and to humans. Ratified 2026-07-29. |
| **Opposing readings never net** | Attention is **unsigned for every posture** — a negative contribution is unrepresentable, not merely discouraged. Netting would score a fought-over account like an inert one (4 versus 45 under the shipped model), and those are the two most different accounts in the book. Contradiction is marked `contested`, with the outweighed reading's signals **named**. |
| **A score is a projection, never a replacement** | No account attributes on `buying_score`, no account representation on `BuyingScoreQueries` — both asserted by invariant. An account's truth lives in claims, the Knowledge Graph, observations, and business events. |
| **The ledger is the score** | Read the dependency as **ledger → score**. `BuyingScore.projected_from` is the only constructor and takes the ledger first; a score whose value disagrees with its ledger is refused at construction as a *corrupt explanation*. Reproduction uses **no clock and no configuration**, in integer arithmetic end to end. |
| **The business event is the unit of contribution** | Not the signal. An event is attributed to the highest-weighted signal citing it; the others stay in the ledger with a zero contribution and a stated reason. Double counting is structurally impossible, and **nothing is silently dropped** — a zero with a reason is information; an absent row is a mystery. |
| **Step decay, because a stored score must be honest** | A score is exactly correct between `computed_at` and `valid_until`. Any decay changing continuously with wall-clock time breaks that promise the instant after the score is written. Bands are **fractions of each type's own relevance window**, reusing the catalog's judgement rather than inventing a second one. The decisive argument was **semantic consistency, not accuracy**. |
| **Staleness is evidence-derived** | Shelf-life expiry is the one input arriving without an event. The sweep reads `valid_until` — a boundary each score derived from its own evidence — rather than polling an interval somebody guessed. It is **workspace-scoped**: a cross-tenant sweep cannot be served under forced RLS without a role that bypasses it, and no such role may exist. |
| **Three layers of configuration ownership** | Signal catalog (Signora — *what hypotheses mean*) · signal profile (customer — *which we care about*) · **scoring model** (customer — *how much attention each earns*). Separate rows, deliberately: folding weights into the profile would mean tuning a score churns the explanation of every historical signal. |
| **Posture is Signora's; weights are the customer's** | A workspace tunes weights, multipliers, bands, and the ceiling. It may never invert what a signal type *means* — there is no `posture` field in the overrides and no column in the table. |
| **No signals, no score** | An account nothing has been observed about gets **no reading**, not a zero. A zero is a statement, and Signora has not made one. |

### Commercial commitment

| Contract | What it guarantees |
|---|---|
| **Intelligence suggests; humans commit** | A buying score may **create** an opportunity; **only a human may progress one beyond the machine-authored boundary.** `TRACKING` is the sole machine-authored stage, enforced **three ways** — the type system (`next_state` demands an `actor_id` with no default), the domain, and a database CHECK. Ratified 2026-07-29. |
| **Three categories of platform data** | **Derived intelligence** (rebuildable, machine-authored) · **customer configuration** (declarative, irreplaceable) · **workflow state** (accumulated, irreplaceable). They must never blur. |
| **A rebuild regenerates intelligence only** | Until M6 *"rebuild the pipeline"* was universally safe. It is now safe **for derived intelligence**; `opportunity`, `opportunity_state`, `workspace_opportunity_policy`, `signal_profile`, and `workspace_scoring_model` are never rebuilt. Asserted by test, not remembered. |
| **Opportunities outlive their score** | The score is why it was *opened*, never why it stays open. Nothing happening at a company is not evidence a deal is dead. Cooling evidence is **surfaced, never acted upon** — creation is automatic, closure never is. |
| **Workflow stores no derived intelligence** | No current score, no signals, no recomputed judgement. An opportunity cites the score that caused it and reads everything else live; `evidence_state` is derived at read time and never stored. |
| **History is never rewritten** | Append-only state, each row the *complete* workflow state rather than a delta — so the status **is** the audit log and the two cannot disagree. No `UPDATE` grant, and no `delete` on the repository either: derived tables offer deletion because regeneration is their rollback, and workflow has none. |
| **The citation cannot be orphaned** | `ON DELETE RESTRICT` on the originating score. Immutability governs *updates* and says nothing about deletes — and because every upstream id is derived from evidence, a rebuild reproduces identical score ids, so regeneration does not sever it either. |
| **Every state names its actor and reason** | *"Someone changed it"* is not an explanation. Workflow explains itself as thoroughly as intelligence does. |
| **Dismissal is distinct from a lost deal** | One is feedback about Signora's judgement, the other a sales outcome. Collapsing them would destroy the only signal the platform gets about its own qualification quality. |
| **Four ownership layers** | Signal catalog (Signora) · signal profile · scoring model · **opportunity policy** (all customer). Each module owns its own customer-authored policy, versioned alongside its output — which is also what keeps any of them extractable. |

---

## 3 · Product Pipeline state

```
Raw Provider Record   ✅ M2.1   Provider Platform — syncs, watermarks, raw storage
        ↓
Claim                 ✅ M2.2   Provider Normalization — canonical evidence
        ↓
Knowledge Graph       ✅ M3A    identity resolution, relationships, claim sets
        ↓
Observation           ✅ M3B    what changed, according to whom
        ↓
Business Event        ✅ M4     what it means, in language a CRO recognises
        ↓  ─────────── the global / customer-specific boundary ───────────
Signal                ✅ M5A    why it might matter to *this* customer
        ↓  ───────────── the first intentional reduction ─────────────
Buying Score          ✅ M5B    how much attention it deserves, explainably
        ↓  ────── intelligence suggests · humans commit ──────
Opportunity           ✅ M6     ★ what Sales actively tracks — first sellable moment
        ↓
Timeline              ⏳ M7     the account narrative
        ↓
AI Reasoning          ⏳ M9     why, with evidence
        ↓
Recommendation        ⏳ M11    what to do next
```

**Eight links exist and are verified against the live stack** (smoke stages 14b–14h). A simulated provider payload enters through the Provider Port, is stored raw, becomes canonical claims, is resolved to an entity whose decision explains itself, any change in what a provider asserts becomes an observation attributed to that provider, and a material change becomes a typed business event a CRO could read — *"Started using CloudERP"*, *"Raised 24M USD in a series b round"* — and, for a workspace that says it cares, that event becomes a commercial hypothesis with its own two-part explanation — which becomes one number per account whose every point can be traced back through the ledger to the vendor payload that started it — and, finally, an account a seller commits to tracking, whose commitment survives the number that suggested it. No simulation-specific logic exists anywhere in that path.

Everything from M8 onward is unbuilt. See **[21-intelligence-pipeline.md](architecture/21-intelligence-pipeline.md)** for what each remaining stage adds and what it is forbidden from doing.

---

## 4 · Design philosophy for the remaining pipeline

The principles that got the project here, in the order they matter:

1. **Preserve evidence.** Information discarded during processing can never be recovered. When preserving evidence and simplifying downstream code conflict, preserve evidence.
2. **Delay interpretation.** Each module should do its own job and no downstream module's. Interpretation performed early is interpretation that cannot be revised.
3. **Prefer explainability.** Every conclusion must trace to the evidence that produced it. That chain is the product — any system can produce a score.
4. **Every module must increase business understanding.** Nothing exists merely to move data. If a stage only reshapes, question whether it should exist.
5. **AI reasons over structured evidence.** It never invents facts. It explains conclusions using observations earlier modules already proved.
6. **Prefer deterministic behaviour over hidden heuristics.** A magic number nobody can justify will be trusted by four modules within a year.
7. **Prefer explicit domain concepts over generic data processing.** `TECHNOLOGY_REMOVED` beats `is_live: false`.
8. **Architecture before implementation.** Think about the domain, challenge the first design, consider alternatives, then pick the simplest model that fully covers the problem.
9. **Raise architectural questions before coding, never implement around uncertainty.** This has happened repeatedly and has been right every time.

**Process discipline that must continue:** every guard proven to fail when its guarantee is removed · documentation updated in the same change · Security Invariants extended per milestone · `make smoke` green before closing · PROJECT_STATUS updated before the next milestone begins.

---

## 5 · M8 starting context

### What M8 inherits

**Input:** tracked accounts a human has committed to. Through `modules.opportunity_engine.public`:

- `OpportunityQueries.tracked(workspace_id, entity_id)` — the open opportunity, its current state, the live score, and a derived `evidence_state`
- `OpportunityQueries.explanation(...)` — the opportunity, its complete state history, and the `BuyingScoreExplanation` for the originating score, which already carries the ledger and one `SignalExplanation` per contributing signal
- `OpportunityQueries.history(...)` · `.for_entity(...)` · `.policy(...)` · `.artifact()`

Subscribe to `opportunity.created` and `opportunity.stage_changed`.

**The whole chain is walkable from one call:** opportunity → buying score → contribution ledger → signals → business events → observations → knowledge → claims → raw provider records. Nothing downstream needs to re-derive any of it.

**Already exists and should be assumed:** event bus with platform-owned idempotency · forced RLS · `make smoke`, extensible with a stage (14b–14i) · the Tenant Isolation Policy — **register every new table in `tenancy_policy.py` or the build fails**.

### The central challenge

**M8 is a substrate milestone, not a pipeline stage.** It builds the AI Provider Abstraction Layer, the Internal Prompt Registry, and an evaluation harness — the things M9 (Reasoning) and M10 (Research) are built on. Nothing about it answers a business question, and it should not try to.

Two contracts already ratified constrain it:

1. **All vendor access goes through the abstraction layer** (`14-ai-architecture.md`, ADR-0012). No domain or application code ever touches a model SDK.
2. **AI output is untrusted until validated** against an expected Pydantic v2 structure, and must never trigger a privileged or irreversible action without validation and, where the architecture calls for it, human confirmation. **After M6 that has a sharper meaning:** the only irreversible thing in the platform is workflow, and *intelligence suggests, humans commit* now governs AI exactly as it governs scoring.

### The four open questions, now answered

All four were settled inside the proposal. Recorded here so they are not re-opened.

1. **Where do prompt versions live?** Repository artifacts beside the taxonomy, scoring model and policy — the ownership criterion's fifth application. **Immutable once released**, enforced by content hash: editing a shipped version fails the build, because it would silently invalidate every result claiming that version.
2. **What can the harness assert?** Two different things that were being conflated. **Deterministic correctness** — schema, grounding, citation, quantities, workspace — verified on every call against recorded fixtures, mutation-proven, **never calling a model**. **Probabilistic quality** — golden sets, `make eval`, outside the test gate. A Security Invariant needing a GPU is not a guarantee.
3. **Module or platform concern?** Split by whether it contains judgement: the **container** is infrastructure that *refuses* a mixed-workspace set, the **contents** are the caller's domain choice. Generalises — when a concern is part tenancy and part domain, the tenancy half is a type that refuses and the domain half is a caller that chooses.
4. **Cost and latency?** Usage yes, money no. Tokens, latency, retries are facts about what happened; a price is true for a week. Pricing is applied outside the port at reporting time.

### Two platform findings, open — RFCs queued

Both concern `signora_platform/`, which is frozen (CLAUDE.md §20a). **Neither is to be worked around inside a product milestone.**

| Finding | Effect | Resolution path |
|---|---|---|
| **`EventHandler` receives no session.** A handler must work in the *same transaction* as the dispatcher's idempotency claim, but the registry's signature is `(envelope) -> None`. | **No module handler is registered in the live registry.** The pipeline is exercised end to end through its real handlers in the integration suite and `make smoke`, but the deployed worker consumes nothing. Also leaves M5B's staleness sweep unscheduled. | RFC: **EventHandler transaction participation.** |
| **`PublishableEvent` cannot be satisfied by a frozen dataclass.** | Eight modules now carry a `# type: ignore` at their publish site. | RFC: **PublishableEvent immutability compatibility.** |

### Known limits — and which are debt

A **known limitation** is a deliberate scope boundary that behaves correctly; **architectural debt** is something that will have to be undone.

| Item | Kind | Note |
|---|---|---|
| No worker registration; no sweep scheduler | **Debt** — platform, RFC queued | The deployed worker consumes nothing. Product milestones must not route around it. |
| Eight `# type: ignore` at publish sites | **Debt** — platform, RFC queued | Small, contained, identical in every module. |
| One-open-opportunity-per-account is application-enforced | **Known limitation** | "Open" means *the latest state row is not terminal*, which no index can express. A derived `generation` plus a unique index converts the concurrent case into a conflict; the residual is checked in the transaction. Denormalising openness would restore the `UPDATE` grant to buy a constraint. |
| Signal relevance is denormalized at generation | **Known limitation** | A workspace downgrading a type from primary to supporting sees the change in newly generated signals, not existing ones. *Ignoring* a type takes effect immediately. Deliberate in M5A. |
| Demonstrations use a workspace-authored threshold and historical replay | **Known limitation** | The scenario's evidence is thin and short-lived; rather than tune product defaults to make demos pass, the demonstrations configure a workspace and ask as of a moment derived from the evidence. Fixed by the scheduled M2.0 simulation work, not by code. |
| Provider fixtures are `Conditional` | **Known limitation** | Clearly marked; payload provenance contract holds. |
| AC-40 (M4) partial | **Known limitation** | Re-evaluation on `observation.superseded` wired at contract level. |

### Carried forward

- **Scheduled simulation work (M2.0), four items.** A scenario with genuine multi-week movement · fixture enrichment so Crunchbase and CoreSignal carry a domain · an intent trajectory sustaining above the elevated threshold for enough weeks · **evidence recent and rich enough that several hypotheses are concurrently live and buying scores clear the shipped qualification threshold**, so the contested scoring path and out-of-box qualification are both exercised at wall-clock now.

### Deferred, and to stay deferred

- **Account fit / ICP** — deferred out of M5A, M5B **and M6**. It needs resolved entity attribute values, which the Knowledge Graph deliberately does not provide, so it needs a **resolution policy** — a first-class architectural decision deserving its own milestone. *Do not solve it opportunistically inside a milestone about something else.*

  > **2026-08-01, Vision & Roadmap Consistency Review.** This deferral was correct three times and has now become the thing it was protecting against. **ICP appears in five documents and no plan** — it has never been given a milestone number, so every milestone defers it and none owns it. *A deferral without an owner is a deletion with a paper trail.* The instruction above still stands — do not smuggle it into a milestone about something else — but it now needs a **number**, which is a category-3 change and the product owner's to approve. See [PRODUCT_ROADMAP.md](../PRODUCT_ROADMAP.md), recommendation 2.

- **Target account selection** — *which companies does Signora watch.* **Raised 2026-08-01, and the honest position is that no module owns it.** `RunProviderSync` takes a `subject` and nothing supplies one; there is no scheduler; the deployed worker registers one function. It was written into M2.1's *demo scenario* (*"Add a target account list"*) and never into its scope. **Do not assign it opportunistically** — it is a bounded-context question, and guessing an owner is how the next boundary violation starts.
- **Automatic closure of anything a human is working on** — no argument survives the creation/closure asymmetry.
- **Prediction anywhere** — a buying score is not a probability; no column, field, or event payload may imply otherwise. Guarded by invariant.
- **Commercial verdicts upstream of M5B** · **thresholds in rule, strategy, scoring, or qualification code** — guarded by syntax-tree invariants in M4, M5A, M5B and M6.
- **Per-workspace vocabulary types, postures, or stages** — configuration is relevance, weights and thresholds; the vocabularies and their meanings stay global. Per-workspace stages are a CRM concern, trigger M13.
- **Opportunity value, forecast, close date, notes, tasks, activities** — CRM features. M13 integrates with the system that owns them rather than rebuilding it.
- **Multiple concurrent opportunities per account** — real multi-product selling has them; the trigger is M13, where the external system's model becomes the constraint.
- **Cross-account ranking** · **learned weights or thresholds** · **score-derived alerting** · **inferred relevance** · **runtime-editable artifacts** (trigger: a non-engineer must tune without a release, realistically M12) · **fuzzy identity matching** · **person entities** · **manual merge UI (M12)** · **authentic provider payloads** · **cloud infrastructure (M14.5)** · **business UI (M12)**.

---

## 6 · Key documents

| Document | What it is for |
|---|---|
| **[21-intelligence-pipeline.md](architecture/21-intelligence-pipeline.md)** | **Read first.** The flagship reference: how a fact travels from raw provider payload to recommendation, what each stage adds, and what each stage is forbidden from doing. Written for engineers, architects, future hires, customers, and investors. Authored at the M3A boundary, as planned — after three stages existed, so it documents working software rather than projections. |
| [22-knowledge-graph.md](architecture/22-knowledge-graph.md) | The M3A design, marked **as built**, including four departures from the approved proposal and why each was forced. |
| [23-observation-engine.md](architecture/23-observation-engine.md) | The M3B design, marked **as built**. Contains the four evaluated architectures and why cross-provider observation series were rejected — the single most important rejection in the module. |
| [24-business-event-engine.md](architecture/24-business-event-engine.md) | The M4 design, marked **as built**. Contains the taxonomy/rules reasoning and what the CRO test changed before implementation. |
| [25-signal-engine.md](architecture/25-signal-engine.md) | The M5A design, marked **as built**. Contains the global-vs-workspace analysis and the ownership criterion for where configuration lives — the reasoning to reuse whenever a similar question arises. |
| [26-buying-score-engine.md](architecture/26-buying-score-engine.md) | The M5B design, marked **as built**. Contains the reduction analysis (*what is reduced · what stays recoverable · what must never be discarded*), the four-way decay evaluation and the reversal it produced, and three recorded departures. **Read the decay section before proposing any time-dependent artifact** — it generalises. |
| [27-opportunity-engine.md](architecture/27-opportunity-engine.md) | The M6 design, marked **as built**. Contains the intelligence-versus-workflow analysis, the three evaluated state models and why supersession was rejected, and the explicit answer to whether workflow outlives the intelligence that created it. **Read it before adding anything a human authors.** |
| [06-events.md](architecture/06-events.md) | The event catalog. `claim.recorded` and the five Knowledge Graph events are current as of M3A. |
| [05-module-dependencies.md](architecture/05-module-dependencies.md) | The dependency graph, and the read-port pattern for reading another module's data. |
| [04-modules.md](architecture/04-modules.md) | Module ownership and vocabulary. Provider Normalization and Knowledge Graph entries reflect what was actually built, not the v2 placeholders. |

---

## 7 · Lane starting points

> **Rewritten 2026-08-01.** This section described M12.1.5 — three milestones behind — as *the* next starting point, which is what a cold session would have read first. **There is no single next session now.** Three lanes run concurrently (`CLAUDE.md` §20e); each has its own.

**Every lane, before its first slice:** read [`README.md`](../README.md) → `CLAUDE.md` §20e → your module's manifest in [04-modules.md](architecture/04-modules.md). Then set up your database and ports per [RUNNING.md § Running a lane](RUNNING.md#running-a-lane), and **verify the isolation** before writing code.

### Lane A — Product Surface · `lane-a-product-surface`

**Open item awaiting the product owner: R9-03** — a contraction risk reads like a small opportunity, and posture on the row changes what a CRO scans for. **Do not implement it without the ruling.**

Then **M12.4 — research on demand**: `Research.run()` exists and nothing invokes it outside a test. It needs an ARQ job and an endpoint that accepts and returns immediately (§7 forbids a handler blocking on ~54 s of pipeline work).

**Also owned, and outstanding:** `reasoning@1` has no released model, so the Decision Package would refuse at runtime — the product's loudest broken thing, recorded in §1 of `PROJECT_STATUS.md`. And **B-001** in [BUGS.md](BUGS.md), in `signal_engine`.

### Lane B — Commercial Profile · `lane-b-commercial-profile`

**Slice 1 (product catalog) shipped at `1ae600d`.** Read [ADR-0035](architecture/adr/0035-commercial-profile.md) — it is the module's design record, and the manifest in `04-modules.md` is its contract.

**Next: slice 2 — the ICP declaration.** An ICP is *"the kind of company that buys **this product**"*, so it references a product id and inherits the catalog's discipline: versioned, immutable, superseded, its own aggregate.

**The boundary is the whole job:** it records what a customer declares. **It computes nothing, resolves nothing, matches nothing, and calls no provider.** Fit *matching* is not this module's — it needs resolved attribute values, which is a Knowledge Graph slice (Lane A) and deliberately separate. Two import-linter contracts enforce the boundary; if one fails, the slice has drifted.

Slices 3–5 follow: buying-committee role templates, business priorities, and the target account list. **Slice 5 is the one that matters most to the rest of the system** — it publishes `commercial_profile.target_accounts_changed` and finally gives Provider Platform the `subject` it has taken since M2.1. That edge is Customer–Supplier: **tell Lane A before building it.**

### Lane QE · `lane-qe`

**Builds no production feature.** First tasks, in order:

1. **Verify the lane isolation actually holds** — run a suite in each lane's database and confirm the others are untouched. Everything else depends on this.
2. **Use the product.** Every defect that has mattered here was found that way; 2046 tests found none of them. Sign in as each of the four demo personas and work a morning.
3. **Validate the Playground against `playground@2`** — `make demo-narrate` has not been re-run since the dataset changed, so the narrations are one bland sentence each (**R11-07**) and the M12.3 citation slice cannot be shown at its best.
4. **Own [BUGS.md](BUGS.md)** — two rows are already open.


## Change log

| Date | Change |
|---|---|
| 2026-08-01 | v25 — **QE becomes Quality Engineering and Integration**, and this file passes to it. Repository state is now written at **Repository Closeout**, after every promotion, **measured from `main`** rather than assembled from lane reports. Two registers added — [ACTIVE_ASSIGNMENTS.md](ACTIVE_ASSIGNMENTS.md) (who is executing what) and [LANE_COORDINATION.md](LANE_COORDINATION.md) (what one lane needs from another) — and *lane* was separated from *module*: **a module is a permanent architectural boundary, a lane is a temporary execution resource**, so this file and every other now say *current assignee* rather than *owner*. **§1 had been seven commits stale**, missing M12.5's entire module, ADR-0034 and ADR-0035; the figures above are re-measured. **The repository is uncertified by derivation** — the record is bound to migration head `0018` and `main` is at `0019`, which nothing had noticed because the dashboard stopped before M12.5 landed. |
| 2026-08-01 | v24 — **The repository is parallel-development ready.** Four blockers fixed, no architecture changed. **(1)** `CLAUDE.md`'s preamble defined the architecture as documents `01`–`17`; there are **39 numbered documents and 36 ADRs**, so a cold session could not see every module design or the entire product-surface design — harmless with one session holding the tree in context, a correctness defect with two. Corrected, with the three document groups named. **(2)** `tests/conftest.py` resolved the target database from **plain constants**, and the `SIGNORA_TEST_APP_DATABASE_URL` override reached only two fixtures — every API integration test constructed `Settings(database_url=DEFAULT_APP_DATABASE_URL)` directly and went to the shared database regardless. Two lanes running `pytest` would have truncated each other's rows mid-run. Now resolved once, from the environment, so all twelve call sites inherit isolation; **proven by running 33 tests against `signora_lane_b` and confirming `signora` was untouched.** **(3)** `CLAUDE.md` **§20e** added — lanes, Change Budget (🟢🟠🔴⚫), shared-file ownership, git and merge protocol, and migration ownership. **(4)** `README.md` was **17 bytes**; it is now the entry point, with the read-first ordering and the **module registry** that answers *who owns this module right now* in one second. Two documents contradicted two lanes and were amended as Category 1 sequencing changes: `IMPLEMENTATION_ROADMAP.md §1` (*sequential single-stream execution*) and `CLAUDE.md §20d`, whose milestone rule now binds **per lane**. **Deliberately not done:** merging `SESSION_HANDOFF` into `PROJECT_STATUS` and splitting `38`/`39` — assigning them a single owner achieves the same conflict reduction for none of the churn. |
| 2026-08-01 | v23 — **M12.5 slice 1: `commercial_profile`, the head of the pipeline.** [ADR-0035](architecture/adr/0035-commercial-profile.md) ratified and the fourteenth module built — **the first with no upstream dependency**, and the answer to a gap that has existed since M2.1: `RunProviderSync` takes a `subject` and nothing has ever supplied one. Signora had thirteen modules that process companies and no bounded context saying *which*. Four ownerless capabilities (products, ICP, buying committee, target accounts) turned out to be facets of one question the roadmap treated as four gaps. **The boundary is one line — it records; it computes nothing, resolves nothing, calls no provider** — and two import-linter contracts enforce it rather than documenting it. Slice 1 is the **product catalog**: versioned, immutable, superseded, with a product identity that outlives the catalog containing it, saved whole with `expected_version` so a concurrent save is a 409 rather than a silent overwrite. **Two findings from building it.** `signal_profile` reads `WHERE supersedes IS NULL` for "current", which on an immutable table is the **first** version permanently — latent only because nothing has ever written a second profile, and reachable the moment the profile gets a write API (slice 2/4). And the **Security Invariants refused the first migration** for withholding `DELETE`: erasability is a tenancy property, not a statement about what a row means, and immutability belongs in the application. **ICP is smaller than five documents claim** — the product owner's provider ruling decided the ownership half of the resolution policy, and `select_name` already ships the mechanism, so what remains is a Knowledge Graph slice rather than a milestone. |
| 2026-08-01 | v22 — **ADR-0034: the product's ubiquitous language, and the audit that forced it.** *Workspace* is Signora's word for a tenant and had become **the word the product said to a customer**, because nothing had ever written down that it should not — *"Organization" appears nowhere in the repository*, so an engineer reaching for the right word found the only one available. Every new account read *"You are not in a workspace yet"*; the new-organization dialog **explained Row-Level Security to a salesperson**; the header's accessible name said *workspace*, making a screen-reader user the only customer told the internal term. **And a password sign-in redirected to `/workspaces`, a route that has never existed** — every password sign-in for three slices landed on the not-found page, missed by 2312 tests because nothing asserted where a successful sign-in goes. **The leak and the dead route were the same defect**: the code was reasoning about tenancy while the product needed a destination. **Enforced rather than documented** — `vocabulary.test.tsx` scans user-visible strings, forbids a route path named after an internal concept, asserts every `router.push` resolves to a real page, and **found a leak the manual audit had missed on its first run** (*"every business event should cite what produced it"*, in an error message). **Nothing renamed inward**: `workspace_id`, RLS, API paths, the JWT claim, modules and architecture documents all keep the internal name. **CLAUDE.md §4 extended** — it governed the language between engineers and was silent on the language between the product and its customer. **Second consistency pass** found three more capabilities entering through a Demo Scenario rather than a Scope entry: deprioritization intelligence (a governing differentiator in zero milestones) and **the RevOps surface** (Job 7 — the economic buyer has no screen in the product surface design, whose six journeys are all a seller's). **Four confirmed instances**, now the dominant way capability leaves this roadmap. |
| 2026-08-01 | v21 — **Vision & Roadmap Consistency Review, and D42.** The review reconstructed the customer lifecycle and checked all twenty stages against the repository: **nine implemented, five built and unreachable, four never named.** ICP confirmed forgotten — deferred out of M5A, M5B and M6 with correct reasons each time, named in five documents, and **never given a milestone number**, so every milestone defers it and none owns it. **Target account selection is the worse instance**: written into M2.1's *demo scenario* and never into its scope, and recorded as missing for the first time. **The pattern named:** three capabilities entered the roadmap through a Demo Checklist rather than a Scope entry, which is the mechanism by which something can be simultaneously "in the roadmap" and unscheduled. Two documents making **provider configuration a customer responsibility** corrected under the product owner's ruling — `04-modules.md` (*"which providers are enabled per workspace/plan"*) and, more seriously, `37-product-surface.md`, which classified provider precedence as *"a customer policy, the same category as the scoring model."* **The review did not redirect the slice**, deliberately: every gap it found is an architectural decision or a milestone of its own, and building into them would be §20d's anti-pattern. **D42 shipped instead** — narration citations now open, resolving to *what the model was given* rather than to three new endpoints returning three records, because all three cited kinds are things Signora wrote and a citation may not end at another of its own summaries. The facts are **re-derived through the pure assembler**, never stored, and `ai_narration.evidence_digest` — stored since M8, read by nothing — is what makes re-derivation honest: without the comparison the screen would present today's facts as the ones the model saw. Verified end to end against three real Playground accounts: every citation resolved. |
| 2026-07-31 | v20 — **M10 T138: the research lifecycle closes.** retrieve → plan → execute → synthesise → store → publish, with `ai_research.completed` cataloged (closing **F-4**: `artifact_ref` and `model_provenance` were categories of field, not fields) and **smoke stage 14k**. **The synthesis is grounded against findings, not facts** — the narrator's evidence set holds one entry per finding, so it *cannot* reach past a finding to reinterpret the business event beneath, because that event is not in the set it was given. **Nothing is stored until everything succeeded**, proven by test: an unreleased synthesis prompt leaves no task row and no findings, rather than a run that found things and said nothing. **`research_synthesis@1` is REFUSED and stays unreleased** — one grounding failure, identical across three runs, where the model stripped the `research_finding:` prefix on one case and not the other. Not tuned around; it is ADR-0031's clearest instance yet. **R-09 is answered by measurement**: two model calls, 32.8 s + 20.8 s ≈ **54 s steady-state, ~70 s cold**, 0 retries in nine calls — and the shape matters more than the number, because the plan cannot name a derivation twice so the cost is two calls rather than *N*. Six mutations survived, all real: both synthesis validators were untested, the codec's `datetime` branch was unreachable from any current derivation, and nothing exercised re-saving a finding an earlier run had already established. |
| 2026-07-31 | v19 — **M10 T137: the first model call, and `research_planning@1` RELEASED** for `llama3.1:8b` after **eight consecutive passing runs** — 2 cases, 0 grounding failures, 0 schema failures, coverage 1.000. **M10 owns its own golden dataset** for a mechanical reason: the derivation catalog consumes `business_event` and `dissenting_signal`, M8's set holds neither, and every step a planner produced against it would be refused by its own schema. **R-09 is now half-measured and the half is recorded**: one planning call is **32.8 s median steady-state, 48.3 s cold**, ~890 in / ~200 out tokens, 0 retries — against a 60 s policy timeout, so the cold-start margin is real. A task timeout still cannot be set until synthesis exists. **`granite3.3:2b` was measured and REFUSED** on this prompt — 2 schema failures in each of three runs — which is a capability finding and the reason planning's certified model is not the reasoner's. **F-1 escalated to High**: three released prompts, two models, one registry slot, and at T137 it blocked a measurement rather than a request. The **plan-ordering question was settled from repository evidence** (A — preserve model output): `ai_reasoning.stated_reasoning` and `ai_narration.statements` both round-trip unordered, a materialized AI artifact is a historical fact, and canonicalisation buys nothing because a finding's identity sorts its citations. Two mutations survived and both were real: the request path could call `Infer.measure` and skip the release rule — the guarding invariant scanned only `modules/ai_platform`, now widened repository-wide — and my own T132 network-client invariant fired on the composition root, whose stated justification T137 disproved; narrowed to *a client may exist only in a file that hands it to the provider registry*, which still refuses a fetch client inside `evaluation/`. |
| 2026-07-31 | v18 — **M10 T136: the orchestrator, and three derivations that introduce no authority.** `CORROBORATION`, `DISSENT` and `RECENCY` are pure functions of the facts they are given — no clock, no database, no model, and **no threshold**: counting is a measurement, sufficiency is a judgement, and a judgement compiled into a comparison is a business rule nobody reviewed. Dissent reports the *set* of relevances present rather than a strongest one, because ordering a category is how a category becomes a score. **Type↔rule pairing is asserted at import**, both directions, the Business Event Engine's check applied here. **R-09 is deliberately still open**: a full plan over 35 facts runs in microseconds, measured — but the term that dominates a research task is the model call, no prompt exists until T137, and wrapping microseconds in a timeout would make the risk *look* addressed while the part that takes minutes stayed unmeasured. There is likewise **no step counter**: the plan reaching the orchestrator is already bounded by the catalog. Nine mutations; four survived and three of those were real — recency read *first fact* rather than *earliest* because every fixture was ascending, the orchestrator's use of a rule's version was invisible while every rule sits at version 1, and the import-time pairing call was untested because the tests invoked it directly. |
| 2026-07-31 | v17 — **M10 T135: the planner, and the module becomes agentic.** It answers one question — *which comparison is worth performing next?* — and **has nowhere to put an answer**: no field for a conclusion, `extra="forbid"`, so a model that answers rather than selects has its output refused. `DerivationType` is closed, and each member exists because retrieval already exposes what it needs. **Closure is not reimplemented**: a plan is a `GroundedOutput`, its targets *are* its reason's citations, and M8's `check()` already refuses a target the model was never shown — including an invented figure in the justification, which would otherwise sit in the audit trail as the reason work was done. **Two limits, neither a tuned number**: one step per derivation (so plan length is bounded by the catalog, not a constant), and **an empty plan is legal** — stopping is a planning answer, and an agent that cannot stop does not terminate. A draft called a plan INFERRED; corrected — a plan asserts nothing about the customer's world, so it is model-authored **operational history** like `ResearchTask`, and classifying machinery would make the epistemic ladder mean less. Seven mutations, all fatal. |
| 2026-07-31 | v16 — **M10 T134: internal retrieval.** `ResearchFactSource` in `domain/`, `OpportunityFactSource` over `opportunity_engine.public` — the module's only pipeline edge, and enough. **It defines no fact type of its own**: the AI Platform already publishes `EvidenceFact`, and a second shape for one idea would mean two canonical forms and eventually two digests. It emits only what M8's assembler omits — **business events**, which carry `corroborating_providers`, the one place provider agreement is visible and which nothing in the product surfaces; and **dissent**, which the buying score preserves through six stages and the assembler correctly drops. **Disjointness by kind is a Security Invariant**, because two modules emitting one kind would make a citation resolve to two different sentences. Per-fact helpers were written and discarded — annotating them required naming types that arrive *inside* another module's contract, so keeping the types flowing removed eight `type: ignore`s. **A contract hole was closed:** T131 omitted `modules.ai_platform.infrastructure` from M10's forbidden list, which M9 forbids; retrieval nearly reused M8's `assemble` through it. Six mutations, five fatal, one equivalent mutant identified and one control correctly surviving. |
| 2026-07-31 | v15 — **M10 T133: migration `0018`.** Three tables, **because there are three data categories** rather than three types — `research_task` is operational history, `research_finding` derived intelligence, `research_synthesis` a materialized AI artifact — and a pipeline rebuild treats each differently. No foreign key points anywhere, and the inward reason was not obvious: a finding's identity excludes its task, so `task_id` records the run that *first* derived it, and a CASCADE would erase facts a later run also produced. **Found while writing the test meant to prove a constraint fires: `array_length('{}', 1)` returns NULL, so `array_length(x, 1) >= 1` cannot reject an empty array.** Proven end to end — a `signal` citing no business events inserts successfully. Nine shipped constraints across five tables and six milestones carry the broken form; only `0018`'s two were repaired, with `cardinality()`. See [36-empty-array-checks.md](architecture/36-empty-array-checks.md). Five mutations run, all fatal after one was retried when its edit silently failed to apply. |
| 2026-07-31 | v14 — **M10 scope ruled: Internal Research**, and T131–T132 delivered. Two roadmap assumptions were tested against the repository and both failed — pgvector has no corpus to retrieve over, and every tool the architecture names is internal. The milestone shrank from ~12–16 ew to ~6–9, *as a consequence of correction rather than of cutting*, and **neither open product question blocks it**. T132 installed the three-way origin/identity split the Knowledge Contract's Rule 1 requires: a task mints (an act), a finding derives `uuid5` from content (a computation), a synthesis mints (a model call). **A finding has no free-text field** — because DERIVED describes how content was produced and promotion does not exist, the model plans which comparison to run and deterministic code computes the answer. **Rule 12 is enforced by absence:** a synthesis has no address, so no consumer can cite model-authored prose even deliberately. Eleven mutations run; two survived and both were real — a self-referential assertion that could not see its own constant change, and the same gap found still open in the Signal Engine. |
| 2026-07-31 | v13 — **M9 COMPLETE.** `reasoning@1` **released** against `granite3.3:2b` — 2 cases, 0 grounding failures, 0 schema failures, coverage 0.833, recorded after eight consecutive passing runs with **no change to the benchmark, dataset, rubric, schema, timeout or release criteria**. The assumption that M9 required a hosted model was **disproved by measurement**: the constraint was 4 GiB of VRAM, not reasoning capability — `llama3.1:8b` ran 58% on CPU and timed out, while a 1.9 GB model at 100% GPU passed eight times. On this hardware *stronger* means *larger* means *slower*. **[ADR-0031](architecture/adr/0031-evidence-citation-protocol.md) written and deliberately not implemented:** the renderer emits `[token]` while the parser accepts `token`, so three models were REFUSED for following *"cite by their exact reference strings"* literally — an **M8** defect that has been passing on one model's formatting habit since M8. `granite3.3:2b` is recorded as *currently certified*, not permanent. Full [M9 retrospective](architecture/30-m9-retrospective.md) written: nine stated assumptions proved false, five unreachable guards removed, eleven mutations run with six exposing real gaps. |
| 2026-07-30 | v12 — **M9 T130 complete; M9 implementation finished.** The Decision Package is now produced, stored and announced end to end: `AIReasoningModel`, `SqlDecisionPackageRepository`, the `PipelineReasoningContext` adapter, `build_reason`, `ai_reasoning.completed` cataloged, and **smoke stage 14j** (109 tests, no model call). **T128's architectural half closed:** both evaluation entry points route through `build_provider_registry`, and the Ollama-specific `/api/tags` probe was **removed** — it gated a hosted release run on a local runtime and was never what prevented a fake (composition is). A new Security Invariant enforces that the evaluation framework names no vendor in executable code, with prose exempt and a positive control. `reasoning@1` was run against `claude-sonnet-4-5` and returned **UNMEASURABLE — no adapter serves that model**, because no credential is configured; **no release was manufactured**, and a test now fails if one ever appears unearned. Four T130 findings, all from the repository refusing something: `public/` cannot publish a filesystem prompt loader (layering), `SignalQueries` already owned the catalog (parameter removed), `signora_app` cannot read `outbox_event` (relay identity used), and a redundant deduplication was deleted after a mutation showed it protected nothing. Eleven mutations run; six exposed real gaps and became permanent tests. 1563 tests, coverage 95.75%, 295 invariants, 25 contracts, smoke green over 22 stages. |
| 2026-07-30 | v11 — **M9 T122–T129 complete; T130 is the last task.** Records the three evaluation states (READY / REFUSED / UNMEASURABLE), `reasoning@1` authored and unreleased after an UNMEASURABLE local run, the ruling that release is earned against the hosted production model, and the T129 finding that **provider-neutral evaluation already exists** — `build_provider_registry` registers both vendors and `for_model` resolves without naming one, so only the eval entry points' hand-rolled registration needs routing through it. §7 rewritten for T130 with the full remaining work and the settled decisions that must not be re-opened. |
| 2026-07-30 | v10 — **ADR-0029 ratified and implemented; M8 architecturally closed with no findings outstanding.** Operational history commits on its own transaction — AC-69 now holds in production, not only in the domain. `ai_narration` keeps the caller's transaction, deliberately. A failed operational write is observable rather than silent. §7 now points at M9. |
| 2026-07-30 | v9 — **M8 complete.** T121 composes the validated platform: migration `0016` (`ai_narration`), the narration use case, `ai.narration_completed`, the composition root, and smoke stage 14i. Records the **fifth data category** — the materialized AI artifact — and the ruling that it is a historical fact rather than current truth, therefore immutable. §1 and §7 rewritten for M9. Superseded by v10. |
| 2026-07-30 | v8 — **M8 T111–T120 built; the evaluation harness run against a real model.** `explanation_narration@1` passed against `llama3.1:8b` (2 cases, 0 grounding failures, 0 schema failures, coverage 1.000) and is released for that model and refused for every other — the first objective AI-quality signal in the project. Records the rootless Ollama install this workstation needs, the two open harness gaps (retries not surfaced in the report; two structurally identical golden cases), and the observed cost (29.4 s cold load, 43–52 s per case, first call retried at the 60 s policy timeout). §1 and §7 rewritten: this file had been telling the next session to begin at T111, ten tasks after implementation actually started. |
| 2026-07-30 | v7.2 — **Pre-flight synchronization before T111.** Records **statelessness** as the AI Platform's second permanent principle — ratified in review but, until now, present only in conversation. Promotes [28-ai-platform.md](architecture/28-ai-platform.md) to **RATIFIED** and folds the confirmed decisions (module location, dependency direction, freeze-after-M10, Claude-only production adapter, one event, the binding stop condition) into its approval record. §1, §5 and §7 corrected: this file previously told the next session to *write* a proposal that already existed. `make smoke` and `make dr` now invoke through `bash` rather than the executable bit, which commit `0309193` had dropped. Coverage is quoted as **~95.3%** — the earlier "correction" to 95.25% was chasing ±0.02pp run-to-run noise, not fixing an error. |
| 2026-07-29 | v7.1 — **Local-First Development** adopted before M8 implementation ([ADR-0027](architecture/adr/0027-local-first-development.md), CLAUDE.md §20c-2 and the new *repository tells the truth* principle in §2). Actions disabled; three workflows retained at `workflow_dispatch`. The cross-tier JWT contract test moved into `make smoke` (stage 15b) and now **fails when skipped**. Corrected two pre-existing drifts: smoke has **21 stages, not 23**, and coverage measures **95.25%**. |
| 2026-07-29 | v7 — updated at the M6 boundary. Adds the **Commercial commitment** contract block (intelligence suggests, humans commit · three data categories · a rebuild regenerates intelligence only · opportunities outlive their score · workflow stores no intelligence · history never rewritten · the citation cannot be orphaned · every state names its actor and reason · dismissal distinct from a lost deal · four ownership layers). Rewrites §5 for M8, records the eighth `# type: ignore` and the application-enforced open-per-account rule, and notes that CLAUDE.md §19 now binds a **Milestone Definition of Done** ending in a pushed, clean tree. |
| 2026-07-29 | v6 — updated at the M5B boundary. Adds the **Commercial attention** contract block (prioritization never resolution · opposing readings never net · a score is a projection · the ledger is the score · the business event is the unit of contribution · step decay · evidence-derived staleness · three ownership layers · posture is Signora's · no signals, no score). Adds a **known limits** table distinguishing *limitation* from *debt*. Rewrites §5 for M6, records the sweep-scheduler consequence of the `EventHandler` finding, and keeps both platform findings as **queued RFCs**. |
| 2026-07-29 | v5 — updated at the M5A boundary. Adds the **Commercial meaning** contract block (the global/subjective boundary · ownership decides where configuration lives · the vocabulary stays global · no commercial verdict · contradiction preserved · composites enrich · hypotheses phrased as possibilities · two replay modes · customer-authored data is different). Rewrites §5 for M5B, keeps the two platform findings as **queued RFCs**, and records a fourth item of scheduled M2.0 simulation work. |
| 2026-07-29 | v4 — updated at the M4 boundary. Adds the **Business meaning** contract block (business relevance never commercial judgement · taxonomy is data, rules are code · no threshold in code · agreement is evidence · the taxonomy as a product asset · two versions never conflated). Rewrites §5 for M5A, keeps the two platform findings as **queued RFCs**, and records three items of scheduled M2.0 simulation work. |
| 2026-07-29 | v3 — updated at the M3B boundary. Adds the **Change** contract block (the layering principle, change-never-significance, per-provider series only, restraint, derived identity, refinement) and the shared-vocabulary contract. Rewrites §5 for M4, records the two platform findings as **queued RFCs** rather than obstacles, and lists the scheduled M2.0 simulation work. |
| 2026-07-29 | v2 — updated at the M3A boundary. Adds the **Knowledge** contract block (identity-never-truth, deterministic resolution, `MatchStrength` is never a number, ambiguity merges nothing, decisions explain themselves) and the module-boundary enforcement contract. Rewrites §5 for M3B, records **two open platform findings** and one scheduled fixture follow-up, and points §6 at [21-intelligence-pipeline.md](architecture/21-intelligence-pipeline.md) as the document to read first. |
| 2026-07-28 | v1 — created at the M2.2 boundary. Establishes the handoff document as the authoritative continuation point. |
