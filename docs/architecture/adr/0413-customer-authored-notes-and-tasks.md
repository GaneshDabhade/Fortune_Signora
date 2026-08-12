# ADR-0413 — Signora owns customer-authored Notes and Tasks

| | |
|---|---|
| **Status** | ✅ **RATIFIED — product owner, 2026-08-12, as [C-210](../../LANE_COORDINATION.md) option A** |
| **Decision** | ✅ ***"Signora should own customer-authored NOTES and TASKS."*** |
| **Scope** | ⛔ **Two record types. ⛔ NOT files · NOT emails · NOT meetings · NOT arbitrary custom fields** |

## 1 · What changes, and it is a category rather than two tables

📁 **Measured by Lane A before the ruling: thirty-five write endpoints across every module, and not one accepts customer-authored record content.** **Every write today is configuration, membership, or a workflow decision.**

> ⚡ **So this is the first time Signora becomes the **system of record** for something a customer creates.**

⛔ **That is why retention, export, permissions and audit follow from it** — **not as scope creep, but because a system of record owes them and a read-only platform did not.**

## 2 · Why exactly these two

📁 **The ruling: *"Notes and Tasks are first-class customer-authored records that Signora can reason over and that participate in the existing timeline/product experience."***

| | |
|---|---|
| ✅ **Notes · Tasks** | ⚡ **Already the shape of things the platform reasons over, and both feed the timeline it has** |
| ⛔ **Emails · Meetings** | **A *read* of the customer's own system.** 📁 **`integrations` already owns that boundary and `Capability.CRM_RECORDS` is built** — ⚡ **making Signora author them would duplicate a boundary that exists** |
| ⛔ **Files** | **A storage and retention problem, not a reasoning one** |
| ⛔ **Custom fields** | **A schema-authoring capability, and a different question entirely** |

## 3 · One canonical model

📁 **The ruling: *"Use one canonical model; do not create screen-specific note/task representations."***

⚠️ **Account 360 draws notes and tasks; other approved surfaces will.** ⛔ **A per-screen model is how two surfaces disagree about what a task's completion means within one release.**

## 4 · What a Note and a Task are

| | |
|---|---|
| **Both** | **Workspace-owned · authored by a member · attached to an account · appear in the timeline** |
| **Note** | ⚡ **An observation.** ⛔ **Immutable, or versioned — never silently edited** ([§2](../../../CLAUDE.md), *immutability is the default for anything that records a fact*). ⚠️ **A note somebody relied on must remain readable as it was** |
| **Task** | ⚡ **A commitment with a state.** **It has an assignee, and it completes** |

⚠️ **The mutability difference is the one genuine modelling decision here and it is stated rather than left to a lane:** ⛔ **a Task's state MUST change — that is what a task is** — **while a Note records what somebody thought at a moment.** ✅ **Both belong in the timeline; only one is a fact about the past.**

## 5 · Tenancy and authorization

🔴 **Workspace-owned, without exception:** **non-nullable `workspace_id` · RLS enabled *and* forced · registered in `tenancy_policy.py` in the same change that creates the table** ([§8](../../../CLAUDE.md)).

⚠️ **Authorization is [ADR-0410](0410-authorization-capability-layer.md)'s**, and ⛔ **field-level permissions are explicitly NOT approved by this ruling** — 📁 *"that is a separate authorization capability question."*

## 6 · What this releases

✅ **The Notes and Tasks portions of Account 360**, excluded from [TASK-1476](../../BACKLOG.md) under [C-210](../../LANE_COORDINATION.md).
⛔ **The remaining C-210 sections stay excluded** — files, custom fields, and anything depending on them.

## 7 · What this ADR deliberately does not decide

⛔ **Schema · API shape · the migration · whether a note is versioned or append-only · task state vocabulary · reminders or due dates unless the approved design draws them · retention periods · export format · any UI.**

✅ **All of it is Lane A's.** ⛔ **And the boundary that matters most: do not grow this into files, emails, meetings or custom fields because the model would accommodate them.** ⚡ **The ruling named four exclusions deliberately.**
