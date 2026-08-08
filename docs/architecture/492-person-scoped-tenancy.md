# 492 · Person-scoped tenancy — the third class, and it is already half-built

**Lane C · Product Office · 2026-08-08.** **[D-172](../DECISION_REGISTER.md) §1: *"define a tenancy model that will naturally support every future user-specific capability across the platform… Design this once as part of the domain foundation rather than allowing each workflow to introduce its own user-scoped storage."***

> ⚡ **The finding that shortens this document: the platform already sets `app.user_id` on every transaction, `membership` already carries `(workspace_id, user_id)`, and `11-tenancy.md` already names a *user-scoped session shape*.** ⛔ **What is missing is not a mechanism. It is a *classification* and one policy predicate.**

---

## 0 · The recommendation

> ## ✅ **A third tenancy class — `PERSON_OWNED_TABLES` — which is a *narrowing* of tenant-owned, never a parallel to it.**
>
> **`workspace_id` stays non-nullable and every existing guarantee still applies. One predicate is added: `user_id = current_setting('app.user_id')::uuid`.**

⛔ **This introduces no parallel identity concept**, which is [D-172](../DECISION_REGISTER.md) §1's stated preference — **the identity is the one Better Auth already issues and `membership` already stores.**

---

## 1 · ⚡ What already exists — measured

| | Evidence |
|---|---|
| ✅ **`app.user_id` is set on every transaction** | **`signora_platform/db/session.py:31` — `set_config('app.user_id', :user_id, true)`.** **Seven references across the platform** |
| ✅ **A user-scoped session shape is already designed** | **`api/context.py`: *"`UserContext` — authenticated, no workspace selected. Only `app.user_id`…"*** **and `11-tenancy.md` requires both shapes be tested** |
| ✅ **`membership` is already the `(workspace, person)` tuple** | **`workspace_tenancy/infrastructure/models.py:57` — `workspace_id` and `user_id`, both non-nullable, both indexed** |
| ✅ **RLS already reads `app.user_id`** | **Migrations `0001` and `0003` — `workspace` is readable because *"its RLS policy is membership-based on `app.user_id`"*** |
| ⛔ **What does not exist** | **A table whose *rows* are filtered by `app.user_id`.** **The setting exists, the policy pattern exists on one table, and no module has person-owned data yet** |

> ## ⚡ **So the platform has been carrying the mechanism for a person-scoped row since migration 0001, and nothing has ever needed one. `User Profile` is simply the first.**

---

## 2 · ⚠️ The question the classification must answer first

**Is a person's preference scoped to the *person*, or to the *person within a workspace*?**

⛔ **The repository has already answered it, in [418 §](418-platform-foundation-assessment.md):**

> **"Person-scoped configuration and workspace-scoped configuration are different aggregates. A profile preference, a notification matrix and a session belong to a **person within a workspace**… Both are workspace-tenanted and only one is workspace-*owned*."**

✅ **And the product argument agrees with the architectural one.** **A seller in two workspaces wants different notification settings in each** — **a per-person-global setting would silently make one workspace's noise the other's.** ⚠️ **The exceptions are few and are display-level: theme and accessibility are plausibly per-person-global, and are cheap to promote later; the reverse is not.**

> ## ✅ **So: `(workspace_id, user_id)`. Workspace-tenanted, person-owned.** ⛔ **Never `user_id` alone.**

⚡ **This is what makes the class a *narrowing*.** **A table without `workspace_id` would need a different policy mechanism entirely — and `11-tenancy.md` names the one existing exception, Business Event Engine's taxonomy, with an explicit warning: *"do not use this as precedent for any other table without an explicit design review."***

---

## 3 · The design — two shapes, not fourteen tables

**[D-172](../DECISION_REGISTER.md) §1 lists fourteen capabilities. They are not one kind of thing, and treating them as one would produce either fourteen tables or one shapeless key-value store.**

### ✅ Shape A — `person_setting`: one table for *settings*

**For Theme · Accessibility · Notification Preferences · Session Preferences · Personal Preferences.**

| | |
|---|---|
| **Key** | **`(workspace_id, user_id, namespace, key)`** |
| **Value** | **`jsonb`** |
| **Why one table** | ⚡ **These are small, sparse, read together and never queried across people.** **Fourteen tables of two columns each is the schema equivalent of the page-local component §20c forbids** |
| ⛔ **Why it is not a generic store** | **Each namespace publishes a *typed façade* in its owning module's `public/`** — `NotificationPreferences`, `ThemePreference` — **so no module reads a raw key, and an invalid key is unconstructable** ([§2](../../CLAUDE.md), *types make incorrect architecture impossible*) |

### ✅ Shape B — person-owned *entities*, in their owning modules

**For Saved Searches · Saved Filters · Dashboard Layouts · Recently Viewed · Bookmarks · Draft AI Sessions · Personal Copilot Context · Recent Activity.**

⛔ **These are not settings.** **They have their own lifecycle, their own queries, their own ordering and their own retention** — ⚡ **`SavedView` already exists this way, with `SavedViewReader`, `SavedViewWriter` and its own table.** ✅ **Each lives in the module that owns its language** (§6, *a port belongs to the module that owns the language it represents*), **carrying `(workspace_id, user_id)` and the person-owned policy.**

> ## ⚡ **The classification test, in one line: *does anything ever query this across people?*** **No → Shape A. Yes, or it has a lifecycle → Shape B.**

---

## 4 · The platform capability every future workflow inherits

⛔ **[D-172](../DECISION_REGISTER.md) §5: *"design it once and allow every workflow to inherit it."*** **What is designed once is three things, and none is a screen:**

| | |
|---|---|
| **① `PERSON_OWNED_TABLES`** | **A third list in `tenancy_policy.py`, beside `TENANT_OWNED_TABLES` and `PLATFORM_INFRASTRUCTURE_TABLES`.** ⚡ **A table in none of the three still fails the build — the existing rule is unchanged and gains a case** |
| **② The policy shape** | **Everything tenant-owned requires — non-nullable `workspace_id`, `ENABLE` + `FORCE` RLS, separate `SELECT`/`INSERT`/`UPDATE` policies, no `BYPASSRLS` — *plus* `user_id = current_setting('app.user_id')::uuid` in each** |
| **③ A Security Invariant** | ⚡ **The one that makes it real: a person-owned table must return *nothing* for a second person in the same workspace.** ⛔ **`11-tenancy.md` already requires a `WHERE`-less query per tenant table; this adds a second person to the same assertion** |

✅ **A future workflow then inherits person-scoping by adding its table to one list** — **not by designing a policy.**

---

## 5 · ⚠️ What this costs, and the one thing it does not solve

| | |
|---|---|
| ⚠️ **`app.user_id` must be set on every path that touches a person-owned table** | ✅ **It already is** — the platform sets it in `session.py` for both context shapes. ⛔ **But the event bus sets it for a system actor, and a background handler writing person-owned data would write as that actor.** **Named now rather than discovered: person-owned tables are written from request context only, and a handler that needs one is a design review** |
| ⚠️ **Deletion and retention** | **A person leaving a workspace should take their person-owned rows with them.** ⛔ **`TASK-426` already exists for retention and this is a case it must cover, not a new row** |
| ⛔ **What it does not solve** | **Cross-workspace identity — *"the same human in two workspaces"*.** ⚡ **Deliberately: nothing in the fourteen capabilities needs it, and [§6](../../CLAUDE.md) forbids building for a need that does not exist.** **If `Personal Bookmarks` must one day span workspaces, that is a promotion of one namespace, not a redesign** |

---

## 6 · ⚡ An unasked recommendation — [D-172](../DECISION_REGISTER.md) §6

**Three capabilities on §1's list are not person-scoped storage at all, and putting them there would be a mistake:**

| | |
|---|---|
| ⛔ **Recent Activity · Recently Viewed** | **These are *derivable* from the audit and timeline streams the platform already produces.** ⚡ **[§2](../../CLAUDE.md): *truth has exactly one authoritative representation; everything else derives from it* — and a stored copy of "what this person opened" is a second representation of what the audit log already knows.** ✅ **Recommend: a read projection, never a table** |
| ⚠️ **Draft AI Sessions · Personal Copilot Context** | **These carry model output, and [§2](../../CLAUDE.md) classifies materialized AI artifacts as *historical facts, not current truth* — immutable, attributable, never edited.** ⛔ **Storing them as mutable person settings would break a guarantee the AI platform already makes.** ✅ **Recommend: they belong to `ai_platform`'s existing artifact model with a person dimension, not to `person_setting`** |

> ## ⚡ **So of the fourteen capabilities, roughly five are settings, six are person-owned entities, two are derivations that should store nothing, and one belongs to an existing aggregate.** ⛔ **Designing one storage mechanism for all fourteen would have been the error the ruling was written to prevent, one level down.**

---

## 7 · What unblocks now

✅ **Workflow 9 — User Profile — is no longer blocked on an unanswered architectural question.** ⛔ **What remains is ordinary implementation work: one migration, one list entry, one Security Invariant, and the typed façades each consuming module publishes.**

⚠️ **[C-307](../LANE_COORDINATION.md) is answered rather than closed by this office** — **it was raised by another lane, and [§20e](../../CLAUDE.md) gives the close to the requesting lane.**
