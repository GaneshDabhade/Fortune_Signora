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

---

## 8 · The second table of this class — `notification_read`, 2026-08-16

**[TASK-480](../BACKLOG.md), ruled by [D-239](../DECISION_REGISTER.md).** ⚡ **`person_preferences` was the first; this is the second, and it is recorded here because the CLASS is what this document owns.**

✅ **The shape is followed exactly rather than adapted**: **`workspace_id` non-nullable · forced RLS · `user_id = current_setting('app.user_id')` in every policy · and the repository filters by both again**, which is 📁 [§8](../../CLAUDE.md)'s defence-in-depth earned by the person predicate for the same reason the tenant one earns it.

### 🔴 What the second instance taught that the first did not

⚠️ **§8 requires policies covering `SELECT`/`INSERT`/`UPDATE` separately.** ⛔ **`notification_read` has no `UPDATE` grant and no `UPDATE` policy, and the Security Invariant caught it.**

⚡ **Two wrong repairs were available** — **add a grant nothing needs, or weaken the test.** ✅ **`IMMUTABLE_TENANT_TABLES` is how this repository had already resolved the tension**, and its own comment is the argument: 📁 ***"requiring one would mean weakening immutability to satisfy a test, which is exactly backwards."***

> 🔴 **So a person-scoped table may ALSO be immutable, and the two classifications compose.** ⚡ **`person_preferences` is mutable — a preference is a current answer.** ⛔ **A read is a record of something that happened, and the time it happened is not a field that can be corrected.**

### ⚡ The modelling rule this instance contributes

⛔ **A read is a FACT; an unread is the ABSENCE of one.**

⚠️ **The obvious alternative is a `read: bool` per person per notification, and it fails on volume before it fails on principle**: **it requires a row to exist BEFORE anybody does anything**, so a workspace of 200 people receiving 50 notifications holds **10,000 rows describing inaction.**

✅ **And the derived count follows from it** — 📁 [§2](../../CLAUDE.md), *truth has exactly one authoritative representation*. ⛔ **A stored counter is a second copy of what the rows already say, and the two disagree the first time a delivery fails half-way.**

### ⚠️ What a person-scoped table still cannot do, restated because it was tested

📁 **§5 of this document already says the person predicate does not survive a background worker.** ⚡ **`notification_read` inherits that unchanged**: **every read of it happens inside a request that has set `app.user_id`**, and **a worker computing unread counts would see none of them.**

⛔ **Not a limitation this row hit** — the badge is rendered in a request — ⚠️ **but the first row that wants a digest email will, and it should find this sentence rather than the surprise.**

## 9 · The third table of this class — `notification`, 2026-08-16

📁 **[TASK-495](../BACKLOG.md)**, migration `0059`, on
[ADR-0017](adr/0017-notifications.md) and [D-239](../DECISION_REGISTER.md).

⚡ **`notification_read` (§8) records what a person has read.** ⛔ **It could not
name what they had read** — nothing published one. ✅ **This is the other half.**

### 🔴 The first table of this class whose policies are ASYMMETRIC

⚠️ **`person_preferences` (`0044`) and `notification_read` (`0058`) both carry
`workspace_id AND user_id` on every policy**, because in both cases **a person
acts on their own row.**

⛔ **A notification does not work that way.** ⚡ **It is written FOR somebody
else** — a mention is one colleague addressing another, and the research agent
addresses whoever asked. **An INSERT policy requiring
`recipient_id = current_setting('app.user_id')` would make it impossible to
notify anybody but yourself**, which is every case a notification exists for.

| Verb | Predicate | Why |
|---|---|---|
| `SELECT` | `workspace_id AND recipient_id` | 🔴 **The guarantee.** One person's notifications are not another's |
| `INSERT` | `workspace_id` | ⚡ **A colleague may write one.** A recipient predicate here permits notifying nobody but yourself |
| `DELETE` | `workspace_id` | ✅ **Retention, never *dismiss*.** A recipient predicate would leave a departing colleague's rows erasable by nobody |
| `UPDATE` | — | ⛔ **No grant and no policy.** §2 — correcting the summary of a nudge somebody already read changes what they were told after they were told it |

> 🔴 **So the narrowing 492 §0 describes lands entirely on the READ side here,
> and that is the finding this table contributes to the pattern.** ⚡ **The
> class is not *"every policy gains the person predicate"*; it is *"the person
> predicate goes wherever the person's privacy is at stake"*** — **and for a
> table written by one person and read by another, that is `SELECT` alone.**

### ⚠️ It first shipped with no `DELETE`, and the Security Invariant refused it

📁 **`test_tenancy_policy.py`, on every immutable tenant table**: *"Erasability
is a property of the TENANCY model, not of what a row means: a workspace that
cannot be deleted is a retention problem on every table it owns, immutable or
not."*

⛔ **The reasoning that withheld the grant conflated two questions.** ⚡
***Dismissing* a notification is a read** — recorded in `notification_read`,
which is why the two tables are separate — **and that is a product decision.**
✅ **Erasing a workspace is a tenancy obligation, and it is not negotiable per
table.**

> ⚡ **The general form, worth carrying to the fourth table of this class:
> immutability is a claim about `UPDATE`. It is never a claim about `DELETE`.**

### ⛔ And still no display name

📁 **[C-203](../LANE_COORDINATION.md) is `DEFERRED` with a concrete trigger** —
📁 [D-116](../DECISION_REGISTER.md), *M-E, when a provider supplies a person
identifier* ([TASK-429](../BACKLOG.md)) — **and its impact line names
notifications.** ⚡ **Deferred-with-a-trigger is precisely the state you build
AROUND rather than through**: ⛔ a field added here would resolve it silently
and the trigger would never fire. ⚡ **`actor_person_id` carries identity; there is deliberately
no `actor_name` column**, because one here would have answered C-203 by
accident for Timeline, comments, audit history, AI attribution and mentions at
the same time.

✅ **`actor_agent_name` is carried**, because an agent has no Better Auth
identity to resolve: the platform authored the name.
