# Repository Source of Truth

> **One question, one document.** This file answers *"where does X live?"* and nothing else.
>
> **It duplicates no content.** Every row is a pointer. If a sentence would be true both here and in the document it names, **it belongs there and this file links to it.**

## The map

| Question | Authority | Owner | Class |
|---|---|---|---|
| **What are the rules?** | [`CLAUDE.md`](CLAUDE.md) | Product owner | Constitutional |
| **How must an implementation be built?** | [`ENGINEERING_LAWS.md`](ENGINEERING_LAWS.md) | Product owner | Constitutional |
| **What is the architecture?** | [`docs/architecture/`](docs/architecture/) `01`–`21` · module designs `22`–`29`, `33` | Product owner | Constitutional |
| **Why is it that way?** | [`docs/architecture/adr/`](docs/architecture/adr/) · index in [`adr/README.md`](docs/architecture/adr/README.md) | Product owner | Constitutional |
| **What has been decided?** | **[`docs/DECISION_REGISTER.md`](docs/DECISION_REGISTER.md)** | Lane C records · product owner rules | Durable |
| **What is being decided?** | **[`docs/DECISION_QUEUE.md`](docs/DECISION_QUEUE.md)** — **checked by `infra/decision-queue.py --check`** | Lane C stages · the named owner rules | Operational |
| **Where are we?** | [`PROJECT_STATUS.md`](PROJECT_STATUS.md) | **QE**, measured from the promoted commit | Measured |
| **What is built, module by module?** | **[`IMPLEMENTATION_STATUS.md`](IMPLEMENTATION_STATUS.md)** — **generated** | `infra/implementation-status.py` | Generated |
| **What happened, and when?** | **[`PROJECT_HISTORY.md`](PROJECT_HISTORY.md)** — **generated** | `infra/project-history.py` | Generated |
| **What should the next session know?** | [`docs/SESSION_HANDOFF.md`](docs/SESSION_HANDOFF.md) | QE, at Closeout | Measured |
| **What may I claim?** | [`docs/BACKLOG.md`](docs/BACKLOG.md) — **order is priority** | Product owner | Operational |
| **Who is doing what?** | [`docs/ACTIVE_ASSIGNMENTS.md`](docs/ACTIVE_ASSIGNMENTS.md) | The claiming lane | Operational |
| **What is broken?** | [`docs/BUGS.md`](docs/BUGS.md) | Any lane opens · **QE verifies** | Operational |
| **What is one lane waiting on?** | [`docs/LANE_COORDINATION.md`](docs/LANE_COORDINATION.md) | Any lane opens · the named owner answers | Operational |
| **What must the product look like?** | **[`410`](docs/architecture/410-approved-ui-specification.md)** → the DesignSync project | Product owner | Constitutional |
| **What is planned, and in what order?** | [`IMPLEMENTATION_ROADMAP.md`](IMPLEMENTATION_ROADMAP.md) · [`PRODUCT_ROADMAP.md`](PRODUCT_ROADMAP.md) · [`AI_MATURITY_ROADMAP.md`](AI_MATURITY_ROADMAP.md) | Scope: product owner · progress: QE | Durable |
| **Which screens are implemented?** | [`412`](docs/architecture/412-backend-capability-matrix.md) · [`413`](docs/architecture/413-migration-inventory.md), and Lane C's UI Implementation Dashboard | Lane C | Durable |
| **How does Lane C work?** | [`docs/PRODUCT_OFFICE.md`](docs/PRODUCT_OFFICE.md) | Lane C | Durable |
| **How does QE work?** | [`docs/QUALITY_ENGINEERING.md`](docs/QUALITY_ENGINEERING.md) · [`docs/REPOSITORY_RELEASE_CHECKLIST.md`](docs/REPOSITORY_RELEASE_CHECKLIST.md) | QE | Durable |
| **How do I run it?** | [`docs/RUNNING.md`](docs/RUNNING.md) — **the port and database allocation is authoritative** | QE | Operational |
| **Where do I start?** | [`README.md`](README.md) § *Read these first* | — | — |

## The coordination subsystem — how a lane learns what to build

> **Added 2026-08-09, [D-203](docs/DECISION_REGISTER.md) §2.** ⛔ **The map above described every register and none of the machinery a lane actually polls.** ⚡ **The operating model was the one thing the source-of-truth document did not describe** — so an artifact could contradict it and this file had nothing to say.

**The whole subsystem is `docs/coordination/`, plus one orphan git ref.** [D-144](docs/DECISION_REGISTER.md) · [479](docs/architecture/479-coordination-architecture.md).

| Question | Authority | Owner | Class |
|---|---|---|---|
| **What does my lane poll?** | **`git show origin/coordination:coordination.toml`** — an **orphan ref carrying exactly two files** | `infra/coordination.py --publish` | Generated |
| **What may my lane claim?** | **[`queues/lane-a.toml`](docs/coordination/queues/lane-a.toml)** · [`lane-c.toml`](docs/coordination/queues/lane-c.toml) — **one `backlog`, every row claimable** | Lane C writes · the lane chooses within it | Operational |
| **What is Product Office telling my lane?** | [`notices.toml`](docs/coordination/notices.toml) — **reasoning only; a state word is refused** ([B-216](docs/BUGS.md)) | Lane C | Operational |
| **Which customer journey is where?** | **[`workflows.toml`](docs/coordination/workflows.toml)** — 29 workflows, one state each | Lane C | Operational |
| **Who owns this module?** | **[`modules.toml`](docs/coordination/modules.toml)** — **the only place a lane's name is an answer** ([C-412](docs/LANE_COORDINATION.md)) | Lane C | Operational |
| **What do our words mean?** | [`vocabulary.toml`](docs/coordination/vocabulary.toml) — `infra/vocabulary-check.py` | Lane C | Operational |
| **Is the pipeline deep enough?** | `infra/pipeline-dashboard.py` — **generated into every status report** | Lane C | Generated |

**The three instruments a Product Office cycle runs, all advisory, all must exit 0:**

| | |
|---|---|
| `python3 infra/state-check.py` | **Every register, every identifier, every projection.** The promotion gate lives here |
| `python3 infra/decision-queue.py --check` | **An open item with no queue row is an item nobody is routed to** |
| `python3 infra/coordination.py --check` | **The published ref matches what the generator emits today** |

> ⛔ **`coordination.toml` is a PROJECTION and never an authority.** **[`BACKLOG.md`](docs/BACKLOG.md), [`modules.toml`](docs/coordination/modules.toml) and [`LANE_COORDINATION.md`](docs/LANE_COORDINATION.md) stay authoritative** — editing the projection by hand makes it wrong rather than making it true. ⚡ **[C-425](docs/LANE_COORDINATION.md): *the ref does not get to be ahead; it gets to be fast.***

## Archived — read as history, never as instruction

> **[D-203](docs/DECISION_REGISTER.md) §2, 2026-08-09.** **Each carries a banner at its own head**; none was deleted, and **none was moved**. ⛔ **Moving them would have required editing 34 inbound links, ~20 of them inside `architecture/30`+ records this file's own archive strategy says are never edited.** ⚡ **The banner puts the warning where a reader arrives; a relocation only changes where they arrive from.**

| Document | Status | Why |
|---|---|---|
| [`docs/DECISION_PACKS.md`](docs/DECISION_PACKS.md) | ⛔ **SUPERSEDED** | **Duplicate source of truth** — 37 ids dated 08-04 against [`DECISION_QUEUE.md`](docs/DECISION_QUEUE.md)'s 70 dated 08-08, **24 ids in both** |
| [`docs/REPOSITORY_ARCHITECTURE_PROPOSAL.md`](docs/REPOSITORY_ARCHITECTURE_PROPOSAL.md) | ⛔ **NEVER ADOPTED** | Its own first line: *"PROPOSED — awaiting approval. Nothing implemented."* **No ruling ever adopted it** |
| [`docs/PRODUCT_EXPERIENCE.md`](docs/PRODUCT_EXPERIENCE.md) | ⚠️ **OWNER CHANGED** | Owned by **Lane B**, closed by [D-165](docs/DECISION_REGISTER.md). **Reassigned to Lane C as a discovery register** |
| [`docs/PRODUCT_QUALITY.md`](docs/PRODUCT_QUALITY.md) | 🟠 **AWAITING QE** | **Referenced by nothing.** [C-1400](docs/LANE_COORDINATION.md) — ⛔ **a reference count is evidence of disuse, never of supersession**, and this one is QE's to rule |

## The five classes, and why the class matters

**A class answers the question a cold reader actually has: *can I trust this today?***

| Class | Changes | Trust it |
|---|---|---|
| **Constitutional** | Only by product-owner ruling | **Always.** Reality is changed to match it, never the reverse |
| **Measured** | Regenerated every cycle from the promoted commit | **Yes — it was re-measured, never transcribed** |
| **Generated** | Rebuilt from the repository by a script | **Yes, and never edit it by hand** |
| **Operational** | Continuously, by the row's owner | **Yes for *now*; it is not history** |
| **Durable** | Rarely, by addition | **Yes, and corrections are dated in place** |
| **Historical** — `docs/architecture/30`+ | **Never** | **Only about its date.** Read as history, never as instruction |

## Two rules this file exists to enforce

> **One authoritative source per category.** If two documents would answer the same question, one is authoritative and the other links to it. **A duplicated fact eventually becomes a contradictory one** (`CLAUDE.md` §2).

> **Generated documents are never edited by hand.** A generated file carrying manual edits drifts *and* nobody trusts the regeneration — **the worst of both.** `IMPLEMENTATION_STATUS.md` and `PROJECT_HISTORY.md` carry a header saying so.

## Archive strategy — exercised 2026-08-09, and amended by what it cost

**`docs/archive/` was to be created when there was content to move.** ⚡ **Content arrived, and moving it turned out to be the wrong instrument** — recorded here rather than left as a rule nobody could follow.

| | |
|---|---|
| **Archive** | Superseded planning and preparation whose epic has shipped · a proposal that has been ruled and would otherwise read as a plan |
| **Never archive** | Any ADR · dated records `30`+ *(already marked historical, and cited by later documents)* · anything constitutional |
| **Delete instead** | **Operational duplicates.** A dead copy of a live register should disappear, not accumulate — as the root `ACTIVE_ASSIGNMENTS.md` did |
| **Rule on entry** | **Nothing is edited on the way in.** Archiving never alters what a document says |
| ⚡ **How, amended** | **Banner in place — do not relocate.** ⛔ **A move rewrites every inbound link, and the citations come overwhelmingly from `architecture/30`+ records the row above forbids editing.** ✅ **`docs/archive/` is still not created, and now for a measured reason rather than a deferred one: the three documents archived under [D-203](docs/DECISION_REGISTER.md) §2 carry 34 inbound links between them, and relocating them would have meant editing ~20 historical records to preserve a tidier tree.** ⚠️ **A banner reaches the reader at the moment they open the file; a folder only reaches the reader who was browsing.** ✅ **The [Archived](#archived--read-as-history-never-as-instruction) table above is the index** |
