# RESUME — Lane A, in-flight work

**Written 2026-08-20, before a machine restart. Delete this file once the work it describes is promoted.**

Branch `lane-a-product-surface` at `10c671d4`. **100 files modified, nothing committed.** `main`/`integration` are at `4f1e4449`.

---

## 0 · Read this first — the environment will NOT come back on its own

⛔ **A host restart leaves every lane stack down.** 📁 `infra/docker-compose.yml` declares **no `restart:` policy** for `postgres`, `redis` or `minio`, while the prod-local stack's services carry `restart: unless-stopped` and come back crash-looping against a database that is not there. **Measured on 2026-08-20: this is exactly what happened mid-session, and QE saw the identical signature on their lane.**

**Bring it back in this order:**

```bash
cd /home/ganesh/Projects/LaneA/signora-lane-a
set -a && . ./frontend/.env.local && set +a     # auth tier needs BETTER_AUTH_SECRET + SIGNORA_AUTH_DATABASE_URL
make demo-prepare                                # containers + migrations + demo users + seed
```

**Then the tiers that nothing starts for you:**

```bash
# API — port 8300
cd backend && nohup uv run uvicorn apps.api.main:create_app --factory --reload --port 8300 &

# Frontend — port 3300. ⛔ NOT `npm run dev`: it is bare `next dev` and binds 3000,
#    which is human review's slot. This is B-1046 and my half of it is fixed in the
#    Makefile's printed instructions, but the bare command still traps you.
cd frontend && nohup npx next dev -p 3300 &

# Background tier — relay + four arq pools. Nothing in infra/ starts these.
cd backend && SIGNORA_RELAY_DATABASE_URL="postgresql+asyncpg://signora_relay:signora_relay_local_dev@localhost:5732/signora" \
  nohup uv run python -m apps.worker.relay_main &
# ⛔ SEQUENTIALLY, with a pause. Four `uv run` at once race to sync the venv,
#    the first wins and the rest die with `Failed to spawn: arq`. Measured.
cd backend
nohup uv run arq apps.worker.main.WorkerSettings &                       # default pool
sleep 6
for p in ai_research intelligence read_model; do
  SIGNORA_WORKER_POOL=$p nohup uv run arq apps.worker.main.WorkerSettings &
  sleep 6
done
```

⚠️ **If the dev server has been up a long time and sign-in starts failing with `GET /signin?` and no `AUTH_TOKEN_ISSUED` in the log, the client bundle has gone stale.** ✅ **Restart `next dev`; it is not an auth defect.** This cost real time on 2026-08-20.

🔴 **AND CHECK THE BROWSER AFTER ADDING A HOOK TO `components/ui/`.** ⛔ **`skeleton.tsx` gained `useState`/`useEffect` with no `'use client'`, and every route returned 500** — ⚠️ **while all 4,000 unit tests passed**, because **Vitest renders everything as a client component and cannot see a missing directive.** ✅ **Sixteen route-level `loading.tsx` files are Server Components importing that module**, which turned one missing line into the whole product. ⚡ **`curl -s -o /dev/null -w "%{http_code}" localhost:3300/` is the two-second check.**

**Playwright needs both of these exported:**

```bash
export SIGNORA_APP_URL=http://localhost:3300
export LD_LIBRARY_PATH=$HOME/.cache/ms-playwright-deps/lib:$HOME/.cache/ms-playwright-deps/root/usr/lib/x86_64-linux-gnu
```

⛔ **Never run the integration suite against the lane database** — it truncates every table. **Spin a scratch DB:** `CREATE DATABASE scratch_x OWNER signora`, `SIGNORA_DATABASE_URL=…/scratch_x uv run alembic upgrade head`, then point `SIGNORA_TEST_APP_DATABASE_URL` / `SIGNORA_TEST_ADMIN_DATABASE_URL` at it. **Redis for the lane is port 6679** — do not derive it by analogy with Postgres's 5732, which I did and wasted a run on.

---

## 1 · The task in flight

**A strict element-by-element design-conformance pass on Opportunity Intelligence**, on the product owner's standing instruction:

> **Final design documents are the source of truth. Existing implementation is not.**
> **Design-specified + producer available → implement.**
> **Design-specified + producer unavailable → honest absence, documented.**
> **Legacy/invented → remove.**
> **True product conflict → record the exact decision required.**
> ⛔ **Never fabricate business data, invent a producer, add a route, or weaken a gate.**

**The design lives in `Design Documents/*.html`** — bundled pages whose real markup is a JSON string on one long line. **Decode it:**

```python
import json, re
best = ''
for line in open(path, encoding='utf-8'):
    for m in re.finditer(r'"(?:[^"\\]|\\.)*"', line):
        if len(m.group(0)) > len(best): best = m.group(0)
markup = json.loads(best)
```

### The architectural finding that shapes everything

⛔ **Opportunity Intelligence must NOT get its own route.** 📁 [D38](docs/architecture/39-product-review-findings.md) removed *Opportunities* from navigation from first principles — *"adding one back is a claim that needs defending"* — and **[TASK-441](docs/BACKLOG.md) is `PROMOTED`**, having delivered it as a stage-grouped **view** with no route, warning in its own text that *"a route is how D38 gets reversed by accident."*

✅ **Measured: all 19 intelligence components render on `/accounts/[accountId]` and nowhere else.** **The cockpit's content is Account 360's**, so conformance work happens there. **[C-1537](docs/LANE_COORDINATION.md) carries the full reconciliation table and the ruling request.**

---

## 2 · Done this session — all green, none committed

| | |
|---|---|
| **B-293** | Playground seeded 61 memberships with **zero** names. Fixed `seed.py` (bind + scoped backfill). **Demonstrated: 60 of 61 named.** |
| **B-294** | `timeline_entry` has two unique indexes and `append` arbitrated on one. **Fixed** (bare `DO NOTHING`), **fire-tested** against the exact production error. |
| **B-295** | 14 workspace-scoped cascade roots with no FK to `workspace`; 49,015 orphaned entities. **`OPEN` — 🔴, not a lane's.** |
| **B-1046** | `npm run dev` binds 3000. **My half fixed** (Makefile now prints `--port $(SIGNORA_WEB)`). `package.json` is **correct** — Next honours `PORT` natively; measured. |
| **Signal Center** | Assign + Snooze built (the four exits the screen promised), keyboard `E`/`S`/`D`, refusal states. Demonstrated end to end. |
| **What moved it** | 📁 The OI design's waterfall — **existed nowhere.** Built from real `ScoreContribution` data. Desktop geometry **exact**: label 180px, track 6px, delta 36px, segments offset by running total. |
| **Rail ↔ section** | `#opportunities` rendered with **no rail entry** — the inverse of TASK-1483. **Fixed**, guarded **both directions**, fire-tested. |
| **Sources badge** | 📁 *"6 sources"* — `supporting_evidence.length`, rendering nowhere. **Implemented**, reusing `Badge tone="ai"`. |
| **Fact qualifier** | 📁 §08 pairs a value with a second term. `RecordFact` gained optional `delta`/`deltaTone`; **renewal countdown derived** from `renewal_date`. |

**Gates at handoff, 2026-08-21** — ⛔ **all on the FINAL code, not on an earlier pass:**

`tsc` 0 · `eslint` 0 · **4,000 vitest / 206 files** · **29 accessibility+design Playwright** · `mypy` clean · **4,982 pytest + 1 skip, and the skip was then run and passed** (it needs `SIGNORA_REDIS_URL`; the lane's Redis is **6679**, and the scratch DB was dropped afterwards).

⚠️ **183 files uncommitted.** ⛔ **Nothing is pushed.** 📁 **Three of QE's ten rows were re-reports of work already sitting here unseen** — commit and rebase onto `origin/main` before the next audit, or it happens again.

---

## 3 · Rulings established — apply these, do not re-derive them

**① 🔴 OVERTURNED 2026-08-21 — by measuring all 35 documents instead of one.**

⛔ **This ruling said the colour table has nine tokens and that `--ink-4`, `--ai-line` and `--ai-ink` are "mock chrome".** ⚠️ **It was drawn from the Design System document's SUMMARY table.** ✅ **The real token layer is the `tokens()` block every screen document carries**, and a script comparing all 35 finds **37 roles and ZERO disagreements** — including `--ink-4` (`#a39a91` / `#65737c`, and our `--color-border-strong` already implements it exactly), `--ai-ink`, `--ai-line`, and the `-line` roles in 18 of 35.

✅ **What survives, and is the part that mattered**: a value appearing in ONE mock is still illustrative — `--brand-soft` is in 1 of 35 — so *count the documents before believing a token*. ⛔ **What does not survive**: treating a role carried identically by all 35 as chrome. 📁 **`design-foundation.test.tsx` now reads every document, asserts they agree, and checks BOTH themes** — which is how the two remaining defects (`--color-accent-hover` and `--color-accent-soft`, correct in light and wrong in dark) were finally visible.

**② Nearest scale step, not arbitrary pixels.** A mock's `9px` gap, `1.5px` rail or `3px` ring maps to the nearest scale step. ⛔ `gap-[9px]` also trips the design-token guard.

**③ Anchor ids are implementation detail.** 5 of 12 diverge (`#opps`, `#org`, `#graph`, `#tech`, `#compete`). **Verified: the rail is their only consumer.** A customer sees the label, never the id. ⛔ **Renaming them is churn D-220 §10 forbids.**

**④ Do not paste a mock's raw CSS into a docstring.** `design-tokens.test.tsx` scans component source for `text-…`; a quoted `text-transform:` reads as a type-scale utility no token declares. **Describe the declaration in a table instead.** The guard is right.

---

## 3b · QE's ten rows — done 2026-08-21, and three corrections to them

📁 **B-1050…B-1059 on `origin/main` @ `98793262`.** ⛔ **My `docs/BUGS.md` predates them** (the branch is behind), **so their `Status` cells are NOT updated — do that at the rebase.**

| Row | What happened |
|---|---|
| **B-1046** | ✅ **Makefile half was already fixed here and invisible to QE** — uncommitted. **Found a THIRD site QE did not reach**: `docs/RUNNING.md:217` printed bare `npm run dev` beside a hardcoded `:3000`. Fixed. |
| **B-1050** | ✅ **Already fixed here**, independently, same diagnosis — uncommitted. **Verified: no two of canvas/surface/raised/sunken collide in either theme.** |
| **B-1051** | ✅ Added `--color-ai-ink · ai-line · accent-ink · accent-line · success-line · warning-line · danger-line`, both themes, at the design's values. 🔴 **QE's `--color-accent-soft` claim was half right**: ours implements `--brand-soft` (1/35), and it is the DARK value that is wrong. ⚡ **Found two more of the same shape** — `--color-accent-hover` held `--brand-ink` in dark. **Consumers moved off invented `/30` alphas.** |
| **B-1052** | 🔴 **CORRECTED — the row asks for the opposite of the design.** ⛔ **Measured: of 180 badge-like tinted elements, 166 carry NO border and 14 do.** ✅ **What the same measurement DOES find is the foreground**: `--brand-tint → --brand-ink` (55/55) and `--ai-tint → --ai-ink` (47/48), where ours used `--brand`/`--ai`. **Fixed that; added no borders.** |
| **B-1053** | ✅ **Fixed, and the cause was one layer deeper than the row.** 🔴 **`/account-identities` returned a ZERO-FILLED row for any id** — contradicting its own docstring and ADR-0409 §5 — **so the screen was faithfully rendering what the platform told it.** **Backend + frontend fixed; browser-verified end to end.** |
| **B-1054** | ✅ `AccountSectionShell` renders no count when the read failed. **The successful-and-empty `0` is asserted separately so the fix cannot soften it.** |
| **B-1055** | ✅ One id grammar (`tabId`/`tabPanelId`/`TabPanel`) across **all three** tablists — 📁 **QE's third, the notifications popover, verified live rather than assumed.** **Collapsed utility rail no longer claims `role="tab"`** — it is a disclosure that OPENS the panel, which it previously did not do at all. ⚡ **Roving `tabindex` needed ARROW KEYS with it**: an index without them puts two of three tabs out of the keyboard's reach — a regression wearing the fix's clothes. ✅ **Guarded product-wide in the browser** (every `role=tab` resolved against every panel, popover and panel opened in the test) **and fire-tested by removing `aria-controls`.** |
| **B-1056** | ✅ Seven in-shell headings moved to the `Title` role; **the list is now an executable guard** (`page-heading-role.test.tsx`) with named KEEP verdicts including `/workspaces`. ⛔ **`PageHeader` COMPOSITION is deliberately not done** — 📁 TASK-1446: *"each migration is a ROW, not work smuggled into this one."* |
| **B-1057** | ✅ `LoadingRegion` + an announcement inside `SkeletonText`, which **16 of 17 route fallbacks already render**. **Browser, read held open: `aria-busy` 1, live region *"Loading the signal queue…"*.** |
| **B-1058** | 🔴 **CORRECTED — the design's indicator is TWO parts.** ⛔ **All 21 `box-shadow:0 0 0 3px var(--brand-tint)` also carry `border:1px solid var(--brand)`.** ⚡ **A bare tint ring is ~1.06:1 on the page and would fail `1.4.11`.** ✅ **One rule, 460 per-component utilities removed. Browser, 28 Tab stops: 1 distinct treatment, down from QE's 4.** |
| **B-1059** | ✅ `rounded-md` → `rounded-lg`. |

✅ **Instrument: 📁 [`frontend/tests/support/design-snapshot.ts`](frontend/tests/support/design-snapshot.ts)** — the 35-document token reader, shared with QE's own extraction and now agreeing on every figure. ⛔ **It was first written into `infra/`, which 📁 [D-022](docs/DECISION_REGISTER.md) reserves to Lane C** — **QE flagged it, verified directly, moved.** ✅ **Offered to Lane C as [C-1541](docs/LANE_COORDINATION.md).** ⚡ **The move removed a SECOND copy inside this repository**: `design-foundation.test.tsx` had its own extraction, so the guard now imports the module.

⚠️ **Two things a browser caught that no test could**: the missing `'use client'`, and **`box-shadow` silently deleting the focus halo on every element with a `shadow-*` class** — the halo now composes through Tailwind's ring slot.

---

## 4 · Next — the remaining micro-audit

**Method, unchanged: extract the design's markup → screenshot → measure → compare → fix or record.**

**Not yet compared:**

1. **Status chips beside the title** — 📁 `inline-flex;gap:6px;font-size:11.5px;font-weight:600;padding:3px 9px;border-radius:6px` with a **6px dot** on the risk chip, and a second chip with no dot.
2. **Deal ↔ company cross-link** — 📁 `Vantage Logistics A/S ↗`, `12.5px`, `--brand-ink`, `600`.
3. **AI Summary Strip** — placement, tint, source count, confidence, generated timestamp, reasoning affordance.
4. **Evidence section** — 📁 *"Basis for the actions"*: number chip `19×19`, `radius 6px`, `--ai-tint`/`--ai-ink`, `10px/700`; title `12.5px/600`; meta `11px --ink-3`; rows `padding:12px 16px` with a `--line-soft` divider.
5. **Competitors** · **What you sell** · **Before you act** · **Sequence navigation**.
6. **Every absence state** — the design draws these and they are as auditable as populated ones.
7. **Reasoning card populated state** — ⛔ **blocked**: the live Playground holds **zero** decision packages, so it renders its absence branch. ✅ **Structure already verified** (dot 8px, `--ai`, `--ai-tint` ring, `<ol>`). **Do not seed fake data to photograph it.**

---

## 5 · Producer-unavailable — leave absent, do not invent

**Amount · Close date · Forecast · `healthRows` ×5 · `forecastRows` ×5 · committee · calls · emails · tasks · Files · reasoning `weight` · Emails/Notes/Custom fields/History rail entries.**

⚠️ **`useBuyingCommittee` is the WORKSPACE's declaration of which roles form a committee — not who is on this deal.** Rendering it as stakeholders is a category error.

⚠️ **Evidence citations cannot be made clickable.** Kinds produced are `buying_score:`, `opportunity:`, `signal_contribution:`, `business_event:`; **`EvidenceDrawer` resolves only `business_event`**, and **0 of 170 such citations resolve to an existing row.**

---

## 6 · Open, needing a ruling — do not resolve in code

- **[C-1537](docs/LANE_COORDINATION.md)** — does Opportunity Intelligence become its own screen, reversing D38, and if so **what publishes a deal's amount, close date and forecast?** The two halves are one question.
- **Account 360 section vocabulary** — *In plain language · Before you act · What contributed · What changed, and who says so · What you sell*. **The rail's labels are part of this same conflict**, which is why the `pageNav` 18-vs-15 split and `Score & health` being split in two were recorded rather than changed.
- **Seven-tab conflict** (Experience Map says six, Account 360 draws seven).
- **[B-295](docs/BUGS.md)** — the cascade root. 🔴, touches frozen `signora_platform/`.

---

## 6b · 🔴 What this audit CANNOT tell you, and it is the more dangerous direction

⛔ **Every figure in §3b counts what was found. Nothing counts what was looked at and missed.**

⚡ **QE's framing, and it is the sharpest thing either lane produced on 2026-08-21**: ***"a false positive costs you an argument; a false negative ships."*** ✅ **Everything this lane optimised for that day catches false positives** — checking QE's reproductions before implementing, fire-testing every new guard, refusing to claim a suite number until it landed. ⛔ **None of it catches a miss.**

🔴 **The micro-audit's own record is the evidence.** ⚠️ **Two of QE's ten sat inside areas this lane had already reported as compared** — the Signal Center's tabs and the account page's failed-read count. ⛔ **So *"compared, clean"* in §4 means *I looked and did not see*, and never *there is nothing there*.**

⚠️ **And the harder version, which no tally catches at all.** 📁 **QE's own log for the utility panel reads `tabFound=1 after={"w":28,"tabpanels":0}`** — **a complete and correct record of the defect, reasoned past** because `⌘.` docked the panel and a working alternative excused a broken control. ⛔ **The instrument was right and the conclusion was not.** ⚡ **This lane did not find it by being more careful**: [B-1055](docs/BUGS.md) required reading `onTab` to add a roving `tabindex`, and the call site was two lines away.

✅ **Treat a clean comparison as a statement about attention, not about the surface.**

### ⚡ The one practice that helps, and its exact limit

📁 **QE's move, and it is the useful half of the finding**: ***"if the evidence was captured correctly, then the evidence can be re-read with the conclusions removed."***

✅ **Run on this lane's own token measurements** — asking *for EVERY colour role the design publishes, is its value carried by some implementation token in BOTH themes?*, which is a question none of the rows needed:

```
33 colour roles across 35 documents
every role's value is carried by some token, both themes
```

⛔ **No new finding, reported as such rather than hunted past.** ⚠️ **And the first version of that check produced eight confident orphans that were all lookup collisions** — a reverse value→token map, several tokens sharing a value, last write winning. **The re-read is not safer than the original reading; it is only differently biased.**

🔴 **What it DID explain.** 📁 **`--brand-strong` is declared by 2 of 35 documents and used ZERO times in the corpus** — and it is the role `--color-accent-hover` was carrying wrongly in dark. ⛔ **No screenshot could ever have shown that**, because nothing in the design draws with it. ✅ **A value-against-design check in both themes is not belt-and-braces for that role; it is the only instrument that reaches it.**

⚠️ **The limit, stated so the practice is not oversold**: **it catches the subset where the record survives and the reasoning was wrong.** ⛔ **It cannot catch the case where the instrument was never pointed.**

---

## 7 · Recurring failure mode — worth reading before you start

**Truncation that reads as a result.** Three instances in one day: a probe hardcoded to `/accounts` that silently measured the wrong page and reported clean; a `head -6` on a grep reported as a total; a `\d person_preferences` cut at 14 lines that appeared to show a missing column and nearly caused shipped work to be rebuilt.

⚡ **And its sibling: `count()` does not auto-wait in Playwright.** A count taken straight after navigation reports zero on a section that has not rendered, and the skip that follows **hides a feature that works.** This shipped once on the Signal Center and was nearly repeated on the waterfall.
