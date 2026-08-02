# ADR-0040: Notifications — *what changed since I last looked*

**Status:** **Proposed, not accepted.** Written by Lane B on 2026-08-02, assigned M14a, **before implementation** — the same order [ADR-0038](0038-timeline.md) followed for Timeline.

**Ratification requires one 🔴 change this ADR cannot make: a fifteenth entry in [04-modules.md](../04-modules.md).** Draft text is in §10, ready to paste.

---

## Context

M14a arrived with a ratified purchase and no architecture. [ADR-0017](0017-notifications.md) chose **Novu** for cross-channel delivery; [Principle 15](../02-principles.md) classes notifications as commodity; [15-project-structure.md](../15-project-structure.md):39 places the adapter in `platform/bought_infra_adapters/`. **[04-modules.md](../04-modules.md) defines fourteen modules and Notifications is not among them**, and the word does not appear in that file.

`grep -ri notification` across `backend/` returns two hits and neither is a notification: a comment about PostgreSQL `LISTEN/NOTIFY` in the outbox relay, and `aria-label="Dismiss notification"` on the frontend toast.

**The discovery finding, recorded in [C-027](../../LANE_COORDINATION.md):**

> **ADR-0017 bought *delivery*. It did not decide *notification*, and they are different concerns.**

Everything ADR-0017 selected — templating, channel fallback, preference management, delivery tracking — is *how a message reaches a person*. None of it answers whether a notification should exist, who should be told, how severe it is, or whether somebody has dealt with it. **Buying a courier is not deciding what to send.**

---

## Decision

### 1 · Notifications is a bounded context. Delivery stays bought.

```
  what happened            →  Timeline           entity-addressed · immutable · built
  what currently needs
  attention                →  Revenue Intel.     derived · never stored · not started
  what to do about it      →  Recommendation     content · not started
  what changed since I
  last looked, and have
  I dealt with it          →  Notifications      person-addressed · mutable   ← this ADR
  how it reaches them      →  Novu               bought · ADR-0017 · unused on Day One
```

**Not folded into Timeline**, the strongest rival. Timeline is *immutable by design* — no `UPDATE` grant, a correction is a new entry — and **a notification is mutable by definition**: read, dismissed, snoozed. They are genuinely projections of the same events, but to **different addressees with different lifecycles**, and sharing the projection would couple the one property Timeline exists to guarantee to a table that must be updated a hundred times a day.

**Not folded into Recommendation Engine**, which ADR-0017 names as the producer. A recommendation is *content*; a notification is *that somebody should be told about it*. Recommendation Engine is also not started.

**The adapter does not go in a platform package.** `platform/bought_infra_adapters/` has never been built, `signora_platform/` is frozen (§20a), and `CLAUDE.md` §6 records this exact placement failing twice already — the Provider Port and the AI Provider Port were both put in platform packages by 15-project-structure.md and landed in their owning modules both times. **This would be the third.**

### 2 · Attention and Notifications are different products, permanently

**Ratified by the product owner, 2026-08-02**, and it settles a boundary an implementing lane must not draw:

| | The question it answers |
|---|---|
| **Attention** — Revenue Intelligence Platform | ***"What currently requires my attention?"*** |
| **Notifications** — this module | ***"What changed since I last looked?"*** |

**They must never converge**, and the architecture makes convergence expensive rather than merely discouraged:

| | Attention | Notification |
|---|---|---|
| Derived from | current state | **an event that occurred** |
| Stored? | **Never** — a stored copy is stale the moment the world moves | Always — nothing reproduces whether a person looked at something |
| Data category | derived intelligence, rebuildable | **workflow state, unreproducible** |
| Goes away when | the underlying condition resolves | **the person deals with it** |

The two rules that follow are the load-bearing part of this ADR:

> **A notification is generated from an event, never from a state.**
>
> Generating one by scanning state produces it again tomorrow, and again the day after. **The need for "duplicate suppression" is the symptom of having modelled it from state**, not a requirement to design for. Genuine redelivery is handled by identity (§4).

> **A notification records a fact in the past tense and references its subject live.**
>
> *"Your HubSpot connection expired"* is true forever and never needs correcting. *"Reconnect it"* is an affordance that exists only while the connection does. Storing a snapshot of the subject makes the notification a lie the moment the subject moves; storing nothing makes a notification about a deleted object unreadable. **Store the fact, resolve the subject.**

### 3 · Severity is carried. Priority is not.

**Severity is a property of the event** — a failure is more severe than an informational change, and that is true for everybody.

**Priority is a property of the recipient's situation** — whether this account is in their focus, how it ranks against eleven others. That is Attention's, and it is derived.

**Notifications therefore carry severity and no ranking of any kind.** This is the same discipline that keeps the Signal Engine from producing a number: a module permitted to rank becomes a second scoring engine, and the two will disagree.

### 4 · Identity, and what it makes impossible

```
notification.id = uuid5(NOTIFICATION_NAMESPACE, f"{event_id}:{recipient_id}")
```

Derived, exactly as `TimelineEntry.project()` derives from `event_id`. Written with `ON CONFLICT DO NOTHING`.

**What this buys, stated as the scenarios it answers:**

- **Replayed events** — a dead letter replayed months later derives the same id and writes nothing. No ledger required, which is why [C-012](../../LANE_COORDINATION.md) constrains the handler's shape rather than blocking it.
- **Redelivery under concurrency** — two workers handling one redelivery both insert, and the database refuses the second. Read-then-write would let both through.
- **Two genuinely distinct events that mean similar things** — two rows, and **that is correct.** Superseding is already modelled upstream (`observation.superseded`, `business_event.superseded`, `signal.superseded`), so a notification whose subject was superseded reads as superseded through §2's live reference. Semantic deduplication here would be this module second-guessing a decision another module already made and published.

### 5 · One row per recipient

Not one row plus *N* read-states. Preferences and channels differ per person, and a shared row with a read-state table is the same thing with worse queries and a harder tenancy story. A workspace event across fifty members is fifty rows.

**Recipients are resolved at generation time** through a `RecipientPolicy` port — Day One implementation: every member of the workspace. **A member added afterwards does not receive it retroactively**, because they could not have acted on it and a joining teammate should not inherit a year of somebody else's alerts.

### 6 · Two rules that keep a backfill from paging everyone

**The scenario that breaks a naive design**: an import, a replay, or a provider backfill produces thousands of events with historic `occurred_at`, and every member is notified about a year of history at once.

> **Nothing is notified about a moment the recipient could not have acted on.** An event whose `occurred_at` precedes the recipient's membership generates no notification, and neither does one older than a stated horizon.

Derived at generation time from facts the module already holds. **No new event contract, no flag for producers to remember to set** — a producer-set flag is a hidden input, and the module that forgets it is the one doing the backfill.

### 7 · What is workflow state, and the `UPDATE` grant it needs

This module's table is **the repository's first deliberate exception** to *immutability is the default for anything that records a fact*, and the exception is exactly the one Opportunity Engine already established: **workflow state is a third data category, neither derived intelligence nor operational history, and it is unreproducible precisely because a human moved it.**

`read_at`, `dismissed_at` and `snoozed_until` are updatable. **Nothing else is** — the fact, its subject, its severity and its provenance are written once. The migration grants `UPDATE` on those columns and no others, so the exception is enforced by the database rather than by intent.

**Bulk acknowledgement** is therefore one statement — `WHERE recipient_id = … AND read_at IS NULL` — rather than *N*, and it is idempotent by construction.

**Snoozing needs no scheduler.** `snoozed_until` is evaluated at read time, and the notification center is pull-based. This falls out of choosing in-app first and is one of the reasons to.

### 8 · Provenance is recorded, and AI-authored content is marked

Every notification names its `producer_module` and the `event_id` that caused it — which is what makes *"why did I get this?"* answerable without reconstruction.

**Day One generates notifications only from events**, so every one is system-generated. **User-generated notifications** (a mention, an assignment) are deferred because **no module publishes such an event today**, and **AI-authored notification text is deferred** because a notification carrying model prose is a different trust object from one carrying a derived fact, and it would need the citation discipline of [ADR-0031](0031-evidence-citation-protocol.md) rather than a field.

---

## Day One — the scope, and what it deliberately excludes

**Set by the product owner, 2026-08-02.**

| In | Out |
|---|---|
| **In-app only** · unread/read · acknowledge/dismiss · event-driven generation · idempotent by identity · workspace- and user-scoped · history · preferences **only where immediately required** | **email · SMS · push · Slack · Teams** · digests · batching · quiet hours · escalation · reminders · reassignment · role-based routing |

> **Build an excellent notification center before introducing delivery channels. Channels plug into a mature notification domain rather than define it.**

**In-app is the only channel that needs nothing bought.** It is our database, our API and our UI — no Novu instance, no SMTP, no deliverability, no vendor account, and no cloud infrastructure, which matters because [ADR-0027](0027-local-first-development.md) makes the local run the only run and M14.5 is three milestones away. Every other channel needs infrastructure that does not exist, and building against it would repeat the position M13 has just paused in.

**Reminders are excluded on principle, not on effort.** *"You still haven't dealt with this"* is generated from a state, which §2 forbids. If reminders are wanted later they must come from an event — a scheduler publishing `reminder.due` — never from a scan. **The thing a reminder is reaching for is the Attention surface**, which is RIP's and answers it correctly by construction.

**Reassignment and ownership are excluded** because assigning a notification to somebody else is a work-assignment concept, and no module owns one. A notification is **addressed**, not owned.

**ADR-0017 is not reversed.** Novu remains the ratified choice for delivery and is simply unused until a delivered channel ships. **`NotificationChannel` is not built as an empty port either** — §20c's rule against speculative abstraction applies, and the in-app center is not a channel implementation, it is the module's own read surface.

### 9 · Three more scenarios, and each one changed something

Run against the second scenario list before N-01. Most were already answered by §2–§8; **three were not, and each produced a rule.**

**Reconnecting an integration — a resolved subject stays unread.** A customer's HubSpot credential expires, they are notified, they reconnect. Should the notification disappear?

> **No. The fact stays, the affordance goes, and it remains unread until somebody looks at it.**

*"Your HubSpot connection expired"* did happen and is still true. But **unread is about seeing, not about the world** — auto-clearing it would mean *"what changed since I last looked"* silently omits changes that resolved themselves, which is exactly the week-away case in JN5. The row reads as resolved and offers no *Reconnect*, because §2's live subject resolution already says so. **This is the sharpest test of the Attention boundary:** Attention *should* drop it the moment it resolves, and Notifications *must not*.

**Provider retries and delayed delivery — do not notify on a transient failure.** A sync that fails and succeeds on retry must produce nothing. Notifying on the first failure produces an alert the customer cannot act on and that is false by the time they read it.

> **A notification is worth generating only for a state a person must act on, not for every event that occurs.**

This is why the Day One consumed-event set is deliberately small and grows on evidence. **The pressure will always be to subscribe to more**, and the discipline is that each addition names the action a customer would take.

**Multiple workspaces — the unread count is per workspace, and tenancy decides it.** A user belonging to three organizations cannot have one global count: `notification` is workspace-owned with forced RLS, and a cross-workspace aggregate would require reading outside the active workspace context. **The tenancy model settles a product question that would otherwise have been argued on taste**, and it settles it the right way — a count mixing three customers' organizations is a number nobody can act on.

**Everything else was already covered**, and is listed so a reviewer can see it was asked: *first notification* and *workspace with no notifications* (the empty state, designed first) · *unread accumulation* and *bulk read* (§7, one statement) · *notification ageing* (a sort key, never a stored expiry) · *dismissed notifications* (§7) · *simultaneous* and *duplicate* and *replayed events* (§4) · *imported history* (§6) · *deleted source objects* (§2) · *multiple users* (§5).

---

## The customer journey

Written in the customer's words ([ADR-0034](0034-ubiquitous-language.md)). A salesperson says *notification*, *unread*, *dismiss* and *snooze* unprompted; they never say *envelope*, *projection*, *idempotent* or *recipient policy*.

| | The customer's question | What the product does |
|---|---|---|
| **JN1** | *"What changed since I last looked?"* | A count they can see without opening anything, and a list newest-first when they do |
| **JN2** | *"Is anything actually wrong?"* | The severe ones read as severe and are not buried under the informational ones |
| **JN3** | *"I've dealt with that."* | One action, and it stays dealt with |
| **JN4** | *"Not now."* | It goes away and comes back, without being lost |
| **JN5** | *"What did I miss while I was away?"* | A week's absence reads as a readable list, not four hundred rows |
| **JN6** | *"Why am I being told this?"* | Every notification says what happened and takes them to the thing it happened to |

**JN5 and JN6 are the two that decide whether the feature is used**, and both are design problems rather than storage problems. JN5 is why grouping is a read-time concern (§ below). JN6 is why provenance is stored (§8).

---

## The slices — backend and UI together, never sequentially

**Each is independently demonstrable to a non-engineer without naming a module** (§2 of `CLAUDE.md`), and each ships its own screen.

| # | Slice | The demonstration, in a customer's words |
|---|---|---|
| **N-01** | A notification exists and can be seen | *"My CRM connection expired, and Signora told me."* |
| **N-02** | Read and unread | *"I can see there are three new things, and after I look they stop being new."* |
| **N-03** | Acknowledge and dismiss | *"I've dealt with that, and it stops asking."* |
| **N-04** | Snooze | *"Not today — remind me Monday."* |
| **N-05** | History, grouping and scale | *"I was away a week; here's what I missed, and it's readable."* |
| **N-06** | Preferences, only what N-01–N-05 proved necessary | *"Stop telling me about this kind of thing."* |

**N-06 is deliberately last and deliberately conditional.** Preferences designed before there is anything to prefer produce a settings screen nobody can answer.

### Test data enters through the pipeline, never through this module

**Product owner, 2026-08-02.** Notifications needed for implementation or testing are **generated by the pipeline that will generate them in production**:

```
provider ingestion → normalization → observation → business event
                                                  → projection → notification
```

**No row is inserted into `notification` directly, and no domain rule is bypassed to produce one.** If a scenario is hard to produce, the fix is to extend provider simulation, demo ingestion, a replay dataset or event generation — **never to weaken the product to make the data easy** (`CLAUDE.md` §20e). Data arriving by a private door proves the door.

**Two of those doors are not Lane B's**, and that is a coordination matter rather than an exception: `signora_platform/simulation` is frozen platform (🔴) and the Playground is QE's. **The scenarios N-01–N-05 need will be requested through the register, not built around.**

### What the UI must answer at both ends of the range

**Zero notifications is the common state and must be designed first**, not last. An empty notification center says *"Nothing new since you last looked"* — a statement about the product working, never an apology for having no data.

**Hundreds is the state that decides whether it is used.** Grouping happens **at read time and never at write time**: collapsing at write would destroy the ability to mark one thing read. Group by subject and kind, newest first, severe first within a group.

**Mobile is not built and is not designed away.** The center is a list with one primary action per row, which is the shape that survives a narrow viewport. Nothing in this design depends on hover, a wide table, or a second column.

---

## Consequences

**Accepted.** A fifteenth bounded context, and one table carrying a justified `UPDATE` grant on three named columns.

**Given up.** Any delivered channel until Novu is provisioned; digests, quiet hours and escalation with it. **The product will say nothing about email until email actually sends** — the same rule the Connection Center already follows with `connectable: false`.

**Deferred with the reason recorded, so it is not rediscovered:** reminders (§Day One) · reassignment (§Day One) · role-based routing (`RecipientPolicy` is the extension point and is not extended) · AI-authored text (§8) · user-generated notifications (§8).

**The risk worth naming.** Notifications and Attention will look similar on a screen and be built by different lanes at different times. §2 is what stops them converging, and the first review to find a stored `needs_attention` column in this module, or an `acknowledged` flag in Revenue Intelligence Platform, has found the convergence beginning.

---

## §10 · The `04-modules.md` entry this ADR needs, ready to ratify

```markdown
### Notifications

**Owns:** What each person in a workspace has been told, and whether they have
dealt with it. Notification, Recipient, Severity, Acknowledgement, Snooze.

**Does Not Own:** **Any judgement about what matters.** Not what currently
requires attention (Revenue Intelligence Platform), not what happened to an
account (Timeline), not what to do about it (Recommendation Engine), not
severity of a business condition — it carries the severity the producing event
states and never derives one. Also not delivery: channels, templating,
scheduling and retries are Novu's (ADR-0017).

**Core Concepts:** Notification, Recipient, Severity, Read State, Dismissal,
Snooze, Recipient Policy.

**Key Published Events:** none. Notifications is a pure read-side consumer.

**Key Consumed Events:** any workspace-scoped event whose occurrence a person
should know about. Day One: a deliberately small set, extended by evidence.

> **The permanent principle (proposed 2026-08-02):** ***Attention answers
> "what currently requires my attention?"; Notifications answers "what changed
> since I last looked?"*** The first is derived and never stored; the second is
> workflow state and cannot be derived. They are different products and must
> never converge. See ADR-0040.
```

**And one row in the README module registry**, which this ADR does not write because ratification is what makes it true.
