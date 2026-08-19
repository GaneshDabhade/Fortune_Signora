# Lane A — where the work stands, and what is next

**Written 2026-08-19 at `941f5832`.** ⚡ **`main` is `20fc5c2d`** — QE's cycle 251
promoted `8ceff5d6`, **so 25 of this lane's commits are on `main`.** **Two remain
local**, pushed to `origin/lane-a-product-surface-r2`.

> ⚠️ **First action next session: rebase.** `main` moved after the push, so
> `main` is no longer an ancestor of the branch. One rebase makes the next
> promotion a plain fast-forward again. **Then tell QE the tip.**

---

## 🔴 Correction to this file's own claim — B-1033, reported by QE

⚠️ **This handover said *"Home is done and on `main`"*. That is not quite true**,
and the correction is recorded rather than the sentence quietly edited.

**QE measured `card.recents` at 37px with 0px spacing against `2.5.8`.** ✅
**Confirmed here by reading the code rather than taken on report**: the row is a
`Link` with `py-2` around a 20px tile — **~37px** — and `border-b` with no gap,
so **0px between adjacent rows.**

### ⛔ Why `home-a11y` is 14/14 green and still missed it

**The Playground's `recently_viewed` is empty**, so no rows render, and the
`2.5.8` sweep measures **what happened to be on the page**. ⚡ **It is not a
vacuous guard** — it asserts `measured.length > 0` and did find controls — **it
is a coverage gap**: the offending controls only exist when there is data.
⛔ **Same shape as the rail-band finding one file over**: an assertion that
cannot distinguish *the rule holds* from *the case never arose*.

### ⚠️ And the fix is NOT a one-liner — it is B-286's class

📁 **The design declares `card.recents` as `1fr × 160px`, showing *"last five
records touched"*.** ⛔ **Five rows at 44px is 220px before padding and a
header**, against a declared **160px**. **The footprint and the criterion cannot
both hold.**

⚡ **Reading `2.5.8` precisely narrows what is actually broken today**, and this
lane established the two clauses earlier in the session:

| Clause | Recents row | |
|---|---|---|
| *"every action is at least 24 × 24px"* | 37px | ✅ clears it |
| *"with 8px separation"* | **0px** | ⛔ **the real desktop defect** |
| *"on mobile every **primary** action is 44px"* | 37px | ⛔ **if a recents row is primary** |

✅ **So the spacing is this lane's to fix.** ⛔ **The 160px-versus-five-rows
contradiction is the design's**, exactly as B-286 is — **and it must not be
resolved by quietly shrinking the row or dropping a record.**

> **First work on resume**, ahead of TASK-495 ⓑ's journey: fix the separation,
> make `home-a11y` measure a Home that HAS recents so the gap cannot reopen, and
> raise the footprint contradiction rather than deciding it.

---

## ✅ Landed on `main` this session

| | |
|---|---|
| **Home contract 5** | The activation registry moved from a frozen array in the browser bundle to **two endpoints, one per owning module**. ⛔ This is what made `AC-H09` and **state 12 reachable rather than unimplemented** — `home.tsx` had carried a branch keyed on a condition a client constant could never produce |
| **Home `2.5.8`** | Target size across the whole page. Found the criterion has **two clauses with different subjects** — *every* action clears 24×24, only a *primary* action is 44px |
| **Home `1.4.3`** | The contrast check the design asks for by name. Found **B-286** |
| **Home a11y × activation** | `1.3.1`, `2.4.3`, `4.1.3` and `2.5.8` measured against the composition that had **never** been measured — a new customer's first screen |
| **B-288** | 🔴 **Account search had crashed for every customer since 6 August.** `EntityKind.PERSON` was added to the backend and the frontend's mirrored union never was, so `KIND_LABEL['person'].toLowerCase()` threw and **took the search box with it** |
| **B-283** | Partly diagnosed. **The two screens do not share a cause**, which the row had assumed. Home's own half — the first-run overlay moving the `h1` down 95px — is fixed |
| **B-287** | An integration test hardcoded human review's Redis port. Filed to QE, who found it was **worse than the red line showed**: it also *deleted* a queue on the reviewer's server |
| **rail-band** | The band test **never left the rail anything**, so it could not have measured the override it is named for |

---

## 🔵 In flight — TASK-495 slice ⓑ, the notification bell

**Two commits, on the branch, not yet promoted.**

| | |
|---|---|
| ✅ **`c23a7720`** | **Backend.** The feed left-joins the read row and returns `FeedItem` — the notification and a `read_at`. **The panel could not be built without it**: the badge said how many were unread without anything saying which |
| ✅ **`941f5832`** | **UI.** The 32×32 bell, badge capped at 99+, the 400px popover, three tabs, day grouping with sticky heads, the 6px unread dot, and *opening an item* marking it read |

### ⛔ What is NOT done, and it is required

> **A Playwright journey and a headed review.** 📁 [§19](../CLAUDE.md) makes both
> part of the Definition of Done for a customer-visible slice — *"a UI slice is
> not complete until its scenario is written and passing"*, and the headed run is
> **continuous product review**, not verification.

**Neither exists. The slice is not ready for QE until both do.**

### ⚠️ Two things worth knowing before continuing it

**The design draws rows that have no producer.** A *system* row (*"Export
finished — 8,412 rows"* with a `Download`) and an *ai* row distinct from an
agent's. ⛔ `ActorKind` is `person | agent` and **nothing exports or scores into
this feed** — they are absent rather than mocked, and a `Download` that downloads
nothing would be worse than no row.

**Two contract absences are carried through deliberately.** A person's actor has
**no name** (`C-203`, and Better Auth is the sole Authentication Authority), so a
row shows an agent's name or none — ⛔ **never an invented *"Someone"***. And
`subject_id` carries **no title**, because a cached account name renders one that
changed last week.

---

## ⛔ Open, and none of it this lane's to decide

| | |
|---|---|
| **C-1533** | Home state 14's entry condition and its copy describe different cards. **Product owner** |
| **C-1534** | Six Home cards name a dependency no approved document assigns a producer. **Product owner** |
| **B-286** | The design's own light warn tag is **4.078:1** against the 4.5:1 it states. ⛔ **Not an implementation defect** — the token is byte-faithful, so the palette is the design's. Encoded `it.fails`, so it **reddens the day somebody fixes it** |
| **B-283**, the rest | Home's remaining ~0.11 is the shell's flex row changing width at ≈4s; Companies' 0.29 is an auto-layout table settling its columns. ⚠️ **Likely in `components/shell/`** — the frozen foundation, where a change touches every screen, **so it is its own slice with its own verification** |

---

## 📁 The backlog, measured rather than assumed

**Queue order is `TASK-421 · 1416 · 1424 · 1478 · 1484`.**

- ⛔ **TASK-421** needs **ADR-C**, which does not exist. Verified: no masking ADR
  in `docs/architecture/adr/`. **An architectural blocker, not this lane's to
  invent.**
- ⛔ **TASK-1416** — re-measured a **fifth** time: `app/(app)/reports/` still
  holds two files and **zero** `useQuery`/`apiRequest`. **Drill-down has no
  figure to drill into.** The row frees itself the moment a report renders one
  real figure.
- ⚠️ **TASK-1424** reads `READY` with its work already on `main` — state
  contested, and **closing it is not this lane's to do by guessing.**
- ⚠️ **TASK-1478** is a standing programme, **not a task**.
- ✅ **TASK-1484** is buildable — the palette ships four groups where the design
  names seven. ⛔ **Deliberately not claimed**: this lane already holds four
  claims, one `IN PROGRESS`, and **claiming a fifth while holding unstarted ones
  is hoarding.**

**So the next work is finishing TASK-495 ⓑ**, not claiming anything new.

---

## ⚡ Two operational facts that cost time to rediscover

⛔ **The backend integration suite truncates every table** ([B-282](BUGS.md)).
Run it against a disposable database — create, `alembic upgrade head`, run, drop.

⛔ **The lane API on 8300 does not auto-reload.** A new route 404s until
`uv run uvicorn apps.api.main:create_app --factory --port 8300` is restarted, and
the symptom looks exactly like a frontend bug.

⚠️ **`demo:users` refuses `SIGNORA_ENVIRONMENT=lane-a`** — 📁 that is **ruled**
([C-298](LANE_COORDINATION.md) / [ADR-0412](architecture/adr/0412-environment-and-secret-safe-logging.md)),
the allow-list must **not** be widened, and `RUNNING.md` now carries the working
sequence: **name `SIGNORA_AUTH_DATABASE_URL` directly and leave
`SIGNORA_ENVIRONMENT` alone.**

---

## 🔴 The one lesson worth carrying forward

**A mutation has to be verified as applied before its result means anything.**

Two fire-tests this session reported *"passed"* and **neither had tested
anything**: a 12-space `.outerjoin(` is a substring of a 16-space one 550 lines
earlier, so the mutation landed on an unrelated query and nearly proved a real
guard decorative. ⚡ **Once targeted properly, one guard was load-bearing and the
other was not** — and the second is now documented as defence in depth rather
than claimed as the guarantee.
