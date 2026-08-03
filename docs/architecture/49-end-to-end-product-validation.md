# 49 — End-to-End Product Validation

> **A record, dated 2026-08-03, by Lane B**, assigned *Customer Quality Engineer* and *End-to-End Product Validation* by the product owner.
>
> **It is not a plan.** Everything below was produced by driving the real application in a real browser against a real seeded organization, and every claim is either evidenced by a test that runs or is marked explicitly as unevidenced.

---

## 1 · The finding that reframes the assignment

**Signora had never rendered its own data in a browser.**

Not on a screen, not in a demo, not in any environment, at any point since M1.2 — eleven milestones. Every page drew its shell, its navigation, its headings and its empty state, and then rendered the empty state, because the request that would have filled it returned a 404 page of HTML.

```
signed in as the owner of a seeded organization with twelve accounts

  200 GET  /api/auth/get-session
  200 POST /api/token
  404 GET  /api/proxy/workspaces          ← Next's not-found handler
```

and on the screen: ***"You are not part of an organization yet."***

`lib/api/client.ts` chose `/api/proxy` as the browser's base URL in `ad52e66`, deliberately and correctly — the API is not internet-facing in the deployed topology. **The route it named was never built.** One reference in the repository, no implementation, no rewrite.

**Two more of the same kind were found in the first hour**, and together the three mean **no customer journey has ever been completable**:

| | What a customer experienced |
|---|---|
| [B-303](../BUGS.md) | No screen ever showed data |
| [B-304](../BUGS.md) | Every sign-in landed on *"That address does not lead anywhere"* |
| [B-305](../BUGS.md) | **Sign out** showed a page of vendor JSON and **left the person signed in** |

All three are fixed, each with a regression test that runs on every suite execution.

---

## 2 · Why nothing caught it, which is the more valuable half

**Every layer was proven. The composition between them was not.**

| Gate | What it proves | What it steps over |
|---|---|---|
| ~2000 backend tests | the endpoint is correct | they call the API directly |
| Vitest component tests | the component renders what it is given | they mock the hooks |
| `make smoke` | the cross-tier JWT contract holds live | it mints a real token and then calls **the API directly** |
| `frontend/tests/e2e/` | the sign-in *page* renders | **one file, and it had never signed in** |

The E2E suite's only authenticated test was `test.skip(!hasOAuth)`. No local install has OAuth credentials, so it had never run — and ADR-0033 added password sign-in without anybody noticing that the skip now hid a journey every install *could* exercise. Underneath the skip it waited for `/workspaces` and clicked a `workspace-item` test id, **neither of which has ever existed**: it would have failed on its first line if it had ever been reached.

> **This is the fourth instance of one pattern**, and the pattern is now the most reliable predictor of a customer-facing defect in this repository:
>
> | | |
> |---|---|
> | [B-024](../BUGS.md) | fakes accepted a row the real database refused |
> | [B-301](../BUGS.md) | Timeline shipped, and the deployed worker never registered its projection |
> | [B-302](../BUGS.md) | the Playground ran nine pipeline stages and never composed the tenth |
> | [B-303](../BUGS.md) | the browser's only route to the API was never built |
>
> **Every component proven; the composition never exercised.** [C-301](../LANE_COORDINATION.md) asks for the assertion at the worker boundary. [C-308](../LANE_COORDINATION.md) asks the same question at the browser boundary. They are probably one item, and QE is the only lane that can see both.

---

## 3 · Repository Reuse Audit

**Performed before a line was written, as required.** What follows is what was found, and what was done about it.

| Asset | Found | Decision |
|---|---|---|
| `frontend/playwright.config.ts` | 20 lines: `testDir`, timeout, trace | **Extended.** Projects, categories, video, screenshots, a serial policy and a documented reason for each |
| `frontend/tests/e2e/auth-journey.spec.ts` | 112 lines, one file | **Extended, never replaced.** Its twelve unauthenticated assertions are all kept; the dead authenticated block was rewritten around a sign-in that needs no external service |
| `infra/demo-users.json` | four personas, roles, one published password | **Reused as the suite's persona list.** A fourth copy of the same four people would disagree with the other three |
| `frontend/scripts/demo-users.ts` | creates accounts through Better Auth's own sign-up + verify routes | **Reused unchanged.** This is why the suite's sign-in is a real sign-in |
| `backend/tests/playground/seed.py` · `playground@2` | twelve accounts through the real pipeline | **Reused unchanged.** No simulator was built; none was needed |
| `signora_platform/simulation` | the M2.0 provider simulation framework | **Reused unchanged**, via the seeder |
| `frontend/tests/contract/mint-token.ts` | mints through the real issuance path | **Left alone.** It serves the backend's cross-tier test and the E2E suite needs no token of its own |
| `docs/RUNNING.md` § Running a lane | ports, database and Redis index per lane | **Followed exactly** — 3400/8400, `signora_lane_b`, Redis index 3 |
| `data-testid` anywhere in the product | **none** | **Not added.** `getByRole`/`getByLabel`/text is more stable and asserts what a customer perceives |

**Written new, and only where reuse genuinely failed:** the persona loader, the fixture (console capture, `signIn`, page objects), four page objects, the authentication setup project, and five spec files. **Nothing duplicates an existing capability.**

---

## 4 · What the suite is

```
frontend/tests/e2e/
  fixtures/personas.ts     reads infra/demo-users.json — the existing list
  fixtures/signora.ts      console evidence · real sign-in · page objects
  pages/                   attention · brief · settings · business
  auth.setup.ts            one real sign-in per persona; state reused
  auth-journey.spec.ts     the boundary, extended
  daily-usage.spec.ts      a seller's morning, end to end
  business-setup.spec.ts   declaring what the company sells
  permissions.member.spec.ts   the same product, administering nothing
  resilience.spec.ts       refresh · back · tabs · double-click · failure
  consistency.spec.ts      does the product agree with itself?
  accessibility.spec.ts    keyboard · focus · dialogs · labels · structure
```

**Four cadences, by tag:** `npm run test:e2e:smoke` · `:journey` · `:regression` · `:a11y`, and `npm run test:e2e` for all of it.

**Engineering choices, each with a reason rather than a convention:**

| | |
|---|---|
| **Serial, one worker** | The personas share one seeded organization. A workflow test that dismisses an account changes what a list test sees; parallelism would buy seconds and cost determinism |
| **Zero retries** | A retry turns a race into an intermittent pass, which is how a real defect becomes a flake nobody investigates. **An intermittent test is a defect in the test** (§11) |
| **`forbidOnly`** | A stray `.only` narrows the suite to one test and still reports green |
| **Roles and labels, never CSS** | The product ships no test ids; a suite keyed on Tailwind classes breaks on a spacing change and misses a broken workflow |
| **Storage state from a real sign-in** | One real sign-in instead of forty. Not a bypass — the setup project drives the form, and the sign-in itself is asserted where it belongs |
| **No `webServer`** | A lane already runs its own dev server on its own port; starting a second would bind a port belonging to somebody else |
| **Console captured on every test** | A 404 on a data request is invisible in the DOM. That is precisely how B-303 survived |

---

## 5 · Validation results

**Run against a live stack: Next 15 dev server on 3400, FastAPI on 8400, PostgreSQL `signora_lane_b` at migration head `0031`, seeded with `playground@2` — twelve accounts through the real pipeline, four personas enrolled through Better Auth.**

```
93 tests · 91 passed · 2 skipped · 0 failed  (92 regression + 1 demonstration)
6.9 minutes through `make e2e` — leased, re-seeded, serial, zero retries
```

Skipped, both deliberately and visibly: the **OAuth round trip** (no provider credentials) and one **workflow move** when the seeded book has no account left in that state.

Alongside it: **719 Vitest tests green**, `tsc --noEmit` clean, `eslint` clean, and the **production build succeeds** with `/api/proxy/[...path]` in the route manifest.

### What is proven to work, end to end

- **A person signs in with an address and a password and reaches their morning.** Asserted on every run, in every project.
- **Twelve accounts render, ranked, and the ranking is monotonically decreasing** — the header's promise (*"most pressing first"*) is now a test rather than a sentence.
- **Every listed account opens**, and none 404s.
- **The score on the row is the score on the brief** — checked across three accounts, because one can agree by accident.
- **A citation opens the evidence behind it**, and the drawer contains readings rather than a shell.
- **The brief carries a history** — B-302's fix, verified through the browser rather than through the database.
- **Back, forward, reload and deep links all preserve the account.**
- **A member sees their morning, is not offered Settings, is redirected if they type the address, and is refused `403` by the server if they try the write anyway** — the courtesy and the enforcement, asserted separately.
- **A caller naming an organization they do not belong to gets `404`, never `403`** — the anti-enumeration property, exercised through the real token path.
- **Signing out ends the session** — in the tab that clicked, and in a second tab.
- **A product declared on the business page survives a reload**, and a double-click creates one product rather than two.

### What the failures taught

**Twelve failures across five runs, and after the four product defects, *every remaining one was a defect in the test*.** Recording them because the brief said an intermittent test is a defect in the test, and because each was a lesson about asserting against a real product rather than a mocked one.

| Symptom | Underneath it |
|---|---|
| four unrelated screens went blank mid-suite | **the sign-out test was revoking the shared session** — correct product behaviour, wrong test design. It now holds its own session and destroys only that |
| a member's write returned `422`, not `403` | **my payload was wrong**, not the API. Recorded because it nearly became a false finding: the API's schema is public at `/openapi.json`, so nothing is disclosed and there is no defect |
| `/workspaces is not reachable without a session` failed | **the assertion had always been wrong** — a 404 is not a redirect. Replaced with the property it meant to assert, over the four routes that actually exist |
| five consistency tests re-asserted the attention list against itself | **rows were read before their links existed.** A row renders as soon as its score arrives; the name, and therefore the anchor, comes from a second request the list deliberately does not block on. `href` was `''`, and `page.goto('')` resolves to the base URL — so the test navigated nowhere and failed on a brief that never opened. **The product behaviour it tripped over is deliberate and good** |
| a product's name matched four elements | **it is on the page four times, correctly** — the catalog, and the three declarations that let a customer say which product they mean. Located by its edit control instead |
| the double-click test timed out | Playwright waits for actionability, and the first save removes the button — so an unbounded second click waits out the test rather than doing what a hurried person's second click does, which is nothing |
| *who you sell to* counted zero of everything | the section loads independently of the catalog above it (B-006), so its heading is on screen while its own answer is in flight |

---

## 6 · Observations, ranked by customer impact

**Recorded, not fixed.** Each names what a customer experiences.

### 🟠 Worth doing next

| | Observation | Evidence |
|---|---|---|
| **O-1** | **A fresh access token is minted for every single API request.** Opening the attention list issues **eight** `POST /api/token` round trips, each an RS256 signature, before any data arrives. Nothing caches a token that is valid for minutes | network capture, `/` |
| **O-2** | **The empty state a brand-new customer sees first is `You are not part of an organization yet`** — which is true, and is also the only thing the product says to somebody who has just successfully signed up. The path from there to a working organization is one button and no explanation of what happens next | observed on a fresh account |
| **O-3** | **Scripts under `frontend/scripts/` do not read `.env.local`.** `loadAuthConfig()` supplies a working *default* for every value, so `make demo-users` silently seeds whatever the fallback names rather than what the developer configured. **A hidden input** (§2) — it cost this lane a wrong-database seed before it was noticed | reproduced |
| **O-4** | **`make demo` and the seeder both print `http://localhost:3000`** regardless of which lane ran them, and `RUNNING.md`'s lane section does not mention either | reproduced |

### 🟡 Real, smaller

| | Observation |
|---|---|
| **O-5** | `RUNNING.md`'s troubleshooting table attributes *"signed in, but every screen is empty"* to a missing signing key. **From M1.2 the true cause was B-303**, and the entry would have sent every reader to the wrong place |
| **O-6** | The attention list is unpaginated. Twelve rows is fine; the first workspace watching thousands is the trigger, and the platform cursor is datetime-keyed |
| **O-7** | Playwright's browsers were never installed in this clone, and `npm run test:e2e` therefore reported a launch failure rather than a test result. **A suite that cannot run is not a gate** |

### Unevidenced, and deliberately not claimed

**The visual half of a premium review cannot be taken from a browser I cannot see.** Micro-interactions, spacing rhythm, hover and focus *aesthetics*, dark-mode fidelity, responsive breakpoints, animation timing and "does this feel like Linear" are **not asserted anywhere in this document**. What the suite does cover mechanically — focus visibility, focus return, labelling, heading structure, decorative icons — is in `accessibility.spec.ts`. **The rest needs a human at `make demo`**, and with B-303 fixed that session is now worth having for the first time.

---

## 6a · Customer confidence

**Asked and answered in the product owner's words: *if I were a paying customer today, how confident would I feel using this part of Signora?***

| Area | Confidence | Why |
|---|---|---|
| **Signing in and out** | **High** | It works, it is refused correctly when it should be, it does not leak which half of a credential was wrong, and signing out actually ends the session — all four asserted on every run. All four were broken this morning |
| **The morning list** | **High** | Ranked, honest about what it does not know, and every row leads somewhere. The one thing a seller reads first is now proven to be a real ordering rather than an arrangement |
| **The account brief** | **Medium-high** | The argument holds together and every citation opens real evidence. What holds it back is R1-01: *"why now"* says the same thing on eleven of twelve rows, so the column a seller reads second stops earning attention by the fourth account |
| **Declaring your business** | **Medium-high** | Five declarations, versioned, recoverable, and the concurrent-edit case does not lose anybody's work. The gap is that **nothing downstream consumes an ICP yet** — a customer describes who buys from them and the product does not visibly change |
| **Deciding on an account** | **High** | The one place a human decision is recorded, and it is required to carry a reason, attributed, dated, permanent, and survives a reload. It also offers somewhere to go next rather than leaving a person on a page they have finished with |
| **Connections** | **Medium**, and correctly so | The product refuses to offer what it cannot complete — *"Connecting this is not available yet"* rather than a button that fails at the callback. **That is the confidence-building answer**; the low ceiling is the missing capability, not a missing statement about it |
| **Coming back later** | **High** | Refresh, back, forward, deep links, bookmarks and a second tab all behave. This was the single largest cluster of defects and is now the most heavily asserted area |
| **When something fails** | **Medium-high** | A failed list says *nothing has changed about your accounts*, which is what a seller actually fears. A failed brief does not masquerade as an empty one. What is missing is any indication that background work is still in progress |

**The biggest confidence-building change of this cycle** is not any single fix — it is that **the product now shows a customer their own data**, and everything above is a statement about a product somebody can actually use.

**The biggest remaining gap is not a defect.** It is that a customer can do all of the above and still not know **what to do first**. There is no guided first run ([C-007](../LANE_COORDINATION.md)), and a brand-new organization's only sentence is *"You are not part of an organization yet."*

---

## 6b · Product experience scorecard

**Reasoned, not scored out of ten** — the point is the argument, and a number would invite comparison between things that are not comparable.

| Dimension | Assessment |
|---|---|
| **Functional completeness** | **Strong for the daily loop, thin at the edges.** Triage → brief → evidence → decide is complete and proven. Absent: search, filter, sort, bulk actions, saved views, and any way to find an account that is not on today's list |
| **Workflow clarity** | **Strong.** Two navigation entries, one ordered list, one question per screen. The restraint is the achievement: this product had six menu items for four modules and is better for having five fewer |
| **Explainability** | **The product's best quality.** A score decomposes into an arithmetic, the arithmetic into contributions, a contribution into provider readings, and every one of those is a real record. Nothing on the daily surface was written by a model, deliberately. **Held back only by R1-01** |
| **Recoverability** | **Good, with one asymmetry.** Cancel, escape and reload all preserve state; a watched company can be un-watched. But **a recorded decision is permanent by design and the dialog says so** — correct for an audit trail, and it means a mis-click on *Not a real opportunity* has no undo. Worth a confirmation step, not a change of model |
| **Trustworthiness** | **High, and structurally so.** Every number is derived and citable; the list and the brief are asserted to agree; the product refuses to offer a connection it cannot complete. **The one thing that would damage it most is a screen that quietly shows nothing** — which is precisely the class of defect this cycle removed |
| **Visual polish** | **Not assessable from here, and not claimed.** Structure, focus, labelling and heading hierarchy pass; spacing, motion, dark mode and "premium feel" need a human at a browser |
| **Performance perception** | **The weakest dimension.** Opening one page mints **eight** access tokens, each an RS256 signature. Nothing tells a customer that background work is in progress, and research is the one action that costs real time |
| **Discoverability** | **Adequate for a seller, poor for an administrator.** The daily surface needs no discovery. But the five declarations that make the product work are three clicks deep behind *Settings*, and nothing on the attention list points at them when it is empty for want of them |
| **Enterprise readiness** | **Two roles where reviewers asked for five** (R8-05). No audit surface for permission changes, no ownership transfer, no way to leave an organization. **These are absences, not defects** — and each is the kind of thing an enterprise buyer asks about in the first meeting |
| **Overall customer confidence** | **A product a seller could use tomorrow and an administrator could not yet run.** The daily loop is real, explainable and trustworthy. What surrounds it — first run, team management, connections, search — is where the next confidence lives |

---

## 6c · The environment question, answered from the repository's own work

**The product owner asked nine questions about environment isolation and instructed me to read the existing work first. Every one of them had already been answered, and the answers are not mine.**

| Question | Answer | Where it was already decided |
|---|---|---|
| Should Playwright own a dedicated **compose project**? | **No.** | **RE-05 was deprioritised on 2026-08-03** — *"the lease serialises what this would parallelise… its remaining value is parallel certification, a Stage 4 concern, not a now one"* ([RELEASE_ENGINEERING.md](../RELEASE_ENGINEERING.md) §7) |
| A dedicated **auth database**? | **It has one.** | `signora_lane_b` — [RUNNING.md § Running a lane](../RUNNING.md#running-a-lane) |
| A dedicated **application database**? | **The same one.** | ditto |
| Dedicated **Redis**? | **Logical index 3.** | ditto |
| Dedicated **ports**? | **3400 / 8400.** | ditto, and *"no lane invents ports"* |
| Reuse **provider simulation**? | **Already does**, via the Playground seeder | §3 above |
| **Regenerate seed data** before every run? | **Yes, per suite — and that is the one genuinely new decision.** `make e2e` re-seeds; `make e2e-quick` does not | New. Reasoning below |
| **Preserve state** or be **disposable**? | **Disposable per run, durable between runs** | Below |
| Can **two Playwright runs collide**? | **They could, and now they cannot** | `environment-lease.py`, reused unchanged |

> **Nothing new was built for isolation.** A lane's environment already *is* the isolation the question asks for, and the repository has twice declined — on evidence — to add a second environment model. Building one for Playwright would have been the parallel system I was told not to build.

### The one hazard that was real, and it was mine

**`playwright.config.ts` defaulted `SIGNORA_APP_URL` to `http://localhost:3000` — Human Review's stack, which belongs to the product owner and to no lane.**

That was survivable while the suite only read. **It stopped being survivable the moment the suite started writing** — and this milestone made it write: products, watched companies, and **permanent, attributed decisions**. `npm run test:e2e` with no environment variable would have put decisions signed *Dana Reyes* into the environment the product owner reviews the product in.

**This is the cycle-25 class exactly**: one operation quietly mutating an environment another operation owns. The repository's own conclusion from that incident is the fix — *prevention, not detection* — so the suite now **refuses to start** with no URL, and **refuses to drive ports 3000 or 8000** at all:

```
  REFUSING to drive http://localhost:3000.
  Ports 3000 and 8000 are Human Review on `main` (docs/RUNNING.md).
  This suite writes to whatever it is pointed at …
```

There is a documented override for the one legitimate case — demonstrating the product on the review stack deliberately — and it is a variable nobody sets in a script.

### Re-seeding, and why it is per suite rather than per test

**The evidence is in this milestone.** `workflow.spec.ts` records real decisions, which changes what the attention list contains, so **two consecutive runs are not identical**. Three options were weighed:

| | |
|---|---|
| **Per test** | Correct and unaffordable — the seeder is seconds, and 92 tests would add an hour |
| **Never** | What we had. A suite whose result depends on how many times it has been run |
| **Per suite** | **Chosen.** `make e2e` seeds then runs; `make e2e-quick` skips it for iterating on one spec |

This is RE-03's reasoning — *"a certification that creates and drops its own database cannot measure the wrong one"* — applied one level up, and **without building RE-03**: a re-seed of an owned database achieves the reproducibility without the disposable-database machinery that item is about.

### Two runs at once, and why nothing new locks anything

`make e2e`, `make e2e-quick` and `make product-demo` all run inside **`infra/environment-lease.py`, unchanged**. Two Playwright runs in one clone would truncate each other's database mid-suite — the same failure, one layer out, as the one that made cycle 25 record *"134 passed"* against a suite of 2589. The lease already prevents it, is re-entrant, and reclaims a dead holder. **Reused rather than reimplemented.**

---

## 6d · Browsers

| Engine | State | Evidence |
|---|---|---|
| **Chromium, headless** | The suite's default | 92 tests |
| **Chromium, headed** | **Works** — WSLg provides a display, so the demonstration is watchable | `make product-demo` |
| **Firefox** | **Works. 16/16 on the daily journey, no differences** | `E2E_BROWSERS=all --project=firefox` |
| **WebKit** | **Blocked by the host**, not by the product | 40 missing system libraries — `libgtk-4`, `libgraphene`, `libevent`, GStreamer. One command fixes it: **`sudo npx playwright install-deps webkit`**, which needs a password this lane does not have |

**Firefox and WebKit are absent from a normal run by design.** A listed project runs by default, and three engines over every journey would triple a six-minute suite to answer a compatibility question nobody has asked. `E2E_BROWSERS=all` adds them, over the daily journey only — *does the product work in another engine*, not *does every assertion hold three times*.

---

## 6e · The Product Demonstration Suite

```bash
make product-demo          # watch it, headed, at a human pace
make product-demo-record   # headless, keeps the video and the trace
```

**A different product from the regression suite, and separated because the goals conflict.**

| | Regression | Demonstration |
|---|---|---|
| **Wants** | fast, headless, independent | to be **watched** |
| **Shape** | many small isolated cases | **one continuous story** |
| **On failure** | a precise assertion | *"the demonstration stopped here"* |
| **Artifact** | a pass | a **video somebody can replay** |

Nine steps, narrated as they happen, every one against real pipeline output. It **does not assert its way through the product**: a demonstration that failed on a changed sentence would be re-baselined until it demonstrated nothing — the same failure mode as a re-baselined screenshot — so it asserts only what would make the demonstration meaningless if absent.

What it printed on its last run, unedited:

```
1 · "Which accounts should I work on today?"
     12 accounts, most pressing first
     · NVIDIA Corporation  · Databricks, Inc.  · Snowflake Inc.  · Stripe, Inc.

4 · The score decomposes into an arithmetic
     90 of 120 points

5 · "Prove it."
     Grew open roles 60% over 32 days · Only coresignal has reported this
     · Jul 26, 2026 · open roles 300→480 · coresignal · Jul 26, 2026

9 · What Signora refuses to claim
     No developer application is configured here, so no button is offered.
```

**5.5 MB of artifacts per run** — video, trace, screenshots — in `frontend/test-results/`, git-ignored. That is the living documentation the brief asked for, and it is replayable by somebody who was not in the room.

---

## 7 · Visual regression strategy — challenged first, as asked

**The recommendation is: do not add screenshot snapshots yet, and the reason is not effort.**

| Screen | Stable? | Verdict |
|---|---|---|
| Sign-in, forgot-password, verify-email | **Yes** — no customer data | **Snapshot-worthy.** The only genuinely static screens in the product |
| The 404 page | Yes | Snapshot-worthy |
| Attention list | **No** — twelve rows whose scores, trends and evidence states are computed from dates relative to *today* | **Never.** The Playground is deliberately anchored to the current day so evidence ages realistically; a snapshot would fail daily and be re-baselined until it asserted nothing |
| Account brief | **No** — same, plus optional AI narration | **Never** |
| Business page | Partly | **Structure, not pixels** |

> **A snapshot that is re-baselined on every failure is worse than no snapshot**: it costs maintenance continuously and detects nothing, and it teaches a team that a red visual test means "accept it".

**What replaces it, and is already written:** structural assertions — one `<h1>` per screen, every input labelled, `aria-current` on exactly one nav entry, no unlabelled `<svg>` in `main`, the dialog labelled and focus-trapped. These fail on a real regression and survive a spacing change.

**When to revisit:** the moment a design-token change ships. A token edit is exactly the change a two-screen snapshot suite would catch and a structural suite would not.

---

## 8 · Future pressure

| Pressure | What breaks first | Trigger to watch |
|---|---|---|
| **10,000 accounts** | the unpaginated attention list, then the eight-token page load | the first workspace above a few hundred watched companies |
| **Many users** | `POST /api/token` per request becomes per-user-per-request; every one is an RS256 signature on the Next tier | measured token issuance rate |
| **Real-time updates** | nothing in the suite or the product distinguishes *stale* from *loading*; a live-updating list needs both | the first push-based surface |
| **Multiple organizations per person** | the workspace selector is `workspaces.length <= 1 → render nothing`. Correct today; the first customer with two subsidiaries makes it the primary control | a second organization on one account |
| **The suite itself** | serial and one worker: 72 tests take minutes. Sharding needs **per-worker seeded organizations**, which the seeder does not offer | when the suite passes ~10 minutes |
| **AI on the daily surface** | every assertion here is on deterministic text. A generated sentence on a row would make exact-text assertions non-deterministic | the first model-authored field on `/` |

---

## 9 · Prioritized roadmap

| # | Work | Why it is here | Owner |
|---|---|---|---|
| **1** | **Ratify B-303's fix** — a new route in the frontend foundation, taken as a production defect | It is the largest change a lane has made outside its budget, and it should be a decision rather than a fait accompli | **Product owner + QE** |
| **2** | **Decide whether `test:e2e:smoke` becomes a gate** ([C-308](../LANE_COORDINATION.md)) | Eight tests, ~40s, and it would have failed on all three 🔴 | **QE** |
| **3** | **Human product review at `make demo`** | Nineteen of the assignment's deliverables need eyes on rendered screens, and the environment is worth reviewing for the first time | **Product owner** |
| **4** | **O-1 — cache the access token for its lifetime** | Eight signatures per page load, on every page load, for every user | frontend foundation |
| **5** | **O-3 — make `loadAuthConfig()` fail rather than default** | A hidden input that silently targets the wrong database | frontend foundation |
| **6** | **Extend the suite to the connection centre and the ICP surface** | Both are built and neither is driven yet | Lane B |
| **7** | **O-2 — the first five minutes** | Already [C-007](../LANE_COORDINATION.md), and now measured rather than predicted | product owner |

---

## 10 · Resume conditions

**Anybody continuing this work needs four things and nothing else:**

1. **A stack on your lane's row of [`RUNNING.md`](../RUNNING.md#running-a-lane)** — database migrated, `auth:migrate`, `demo:users` **with `SIGNORA_AUTH_DATABASE_URL` set explicitly** (O-3), then the seeder.
2. **`npx playwright install chromium`.** On a system without `libnss3`/`libnspr4`/`libasound2`, the browser needs them; where `sudo` is unavailable they can be unpacked into a user cache and reached with `LD_LIBRARY_PATH`.
3. **`SIGNORA_APP_URL=http://localhost:<your web port>`** — otherwise the suite drives whatever is on 3000, which belongs to human review.
4. **This document, and §3 before writing anything.**
