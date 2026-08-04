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
| **What is being decided?** | [`docs/DECISION_PACKS.md`](docs/DECISION_PACKS.md) — **staging, not a record** | Lane C | Operational |
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

## Archive strategy — defined, not yet created

**`docs/archive/` will be created when there is content to move, and not before.** *An archive created early is a second place to look.*

| | |
|---|---|
| **Archive** | Superseded planning and preparation whose epic has shipped · a proposal that has been ruled and would otherwise read as a plan |
| **Never archive** | Any ADR · dated records `30`+ *(already marked historical, and cited by later documents)* · anything constitutional |
| **Delete instead** | **Operational duplicates.** A dead copy of a live register should disappear, not accumulate — as the root `ACTIVE_ASSIGNMENTS.md` did |
| **Rule on entry** | **Nothing is edited on the way in.** Archiving moves a file out of the reading path; it never alters what it says |
