# ADR-0029 — Operational history must survive a rolled-back unit of work

> Status: **PROPOSED — 2026-07-30.** Awaiting ratification. **No code has been written against this ADR.**
> Deciders: Product Owner · Architecture Review Board
> Supersedes: nothing. Amends: nothing.
> Anchors: [28-ai-platform.md](../28-ai-platform.md) (T119, T121) · [06-events.md](../06-events.md) · [11-tenancy.md](../11-tenancy.md) · [16-architecture-risks.md](../16-architecture-risks.md) R-01, R-10 · CLAUDE.md §20a

## Context

`Infer.execute` writes an `ai_inference` row on **every** outcome — success, schema failure, ungrounded output, transient failure, permanent failure. That is AC-69, and it is the mechanism by which risk R-10 ("no AI evaluation methodology") stops being a risk and becomes a number: the ungrounded rate is read from that table and nowhere else.

The write goes through `SqlInferenceRecorder`, which uses the caller's session. Every unit of work in Signora is opened by `tenant_scoped_session`, which wraps `session.begin()`. So when a content failure propagates out of the unit of work — which is the correct thing for a caller to do, and what `Narrate` does — **the transaction rolls back and discards the failure record that was written moments earlier.**

Found while writing T121's demonstration, by asserting that an ungrounded output leaves an `ai_inference` row behind and discovering it does not.

### Why this is severe rather than untidy

**The rows that vanish are exactly the rows the metric is computed from.** A successful inference commits with its business transaction and is recorded. An ungrounded one raises, rolls back, and leaves nothing. The ungrounded rate therefore reads **0% forever**, and reads it *confidently*: the table is present, the column exists, the query returns a number, and the number is wrong in the reassuring direction.

That makes it worse than a missing feature. A missing table is visibly missing. This is a metric that looks operational and is systematically optimistic — the same failure shape as Decorative Logic, one layer out: an implementation that appears to record failures and does not.

It is also the third instance of one pattern in M8. T119 found that a provider failure recorded no vendor, and that a failed call recorded zero retries. Both were "the failure path is less observable than the success path." This is that pattern at the transaction boundary, and it is the one the previous two fixes could not reach.

### What is *not* wrong

- The domain is correct. `Infer` genuinely writes on every outcome; the tests proving it are not vacuous.
- `tenant_scoped_session` is correct. Rolling back a failed unit of work is exactly what it should do, and weakening that to preserve a log would be a serious tenancy and consistency regression.
- The outbox is correct. Business events *should* be atomic with the state change that caused them.

**The defect is a category error, not a bug in any one component.** `ai_inference` is operational history — a fact about what the platform did — and it has been given the transactional lifetime of business data, which is a fact about what a customer's workspace contains. Those two want opposite things from a rollback.

## Decision drivers

1. **A failed inference must never be less observable than a successful one** (CLAUDE.md §2, observability).
2. **Truth has exactly one authoritative representation.** Whatever is chosen must not produce two places the ungrounded rate could be read from.
3. **Tenancy is not negotiable.** Any new write path carries `workspace_id`, forced RLS, and the least-privileged runtime identity (§8). A recording mechanism that reached across workspaces would trade a metric for the tenancy model.
4. **The platform is frozen** (§20a). A change to `signora_platform/` needs a stated reason — this ADR is that reason if a platform change is chosen, and the option that avoids one is worth preferring.
5. **Ordering and atomicity must not be silently weakened elsewhere.** In particular, business events must remain atomic with their state change.
6. **M9 multiplies the volume.** Reasoning produces far more inferences than narration, so cost and connection pressure are real considerations, not hypothetical ones.

## Options

### Option A — a separate recording session

The recorder opens its own session from a factory, writes the row, commits, and closes. Independent of the caller's transaction, so a rollback cannot reach it.

**For.** Conceptually exact: operational history gets its own lifetime because it *has* its own lifetime. No platform change — the recorder is module infrastructure and a session factory is already how every entry point works. The row is durable the instant the call ends, which is what an incident investigation needs. Straightforward to test, including the property that matters (roll the caller back, assert the row survives).

**Against.** A second connection per inference. Under M9's volume that is real pool pressure, and it arrives at the worst moment — a provider outage means every call fails, every failure opens a connection, and the recording path is busiest exactly when the database is least happy. Also: the row commits *before* the caller's transaction resolves, so a successful inference inside a business transaction that later fails for an unrelated reason leaves a record of work whose effects were discarded. That is arguably correct (the call did happen, and tokens were spent) but it is a semantic a reader must be told about.

### Option B — an autonomous transaction on the same connection

A savepoint or a `dblink`/`pg_background`-style autonomous write that commits independently while reusing the caller's connection.

**For.** No second connection.

**Against.** PostgreSQL has no true autonomous transaction. A savepoint does not survive an outer rollback — it is *inside* it — so this does not actually solve the problem, and believing it does would produce exactly the reassuring-but-wrong behaviour we are trying to remove. The extension-based variants introduce a new dependency, run outside RLS unless carefully bound, and put a connection-opening function inside the database. **Recommended for rejection**, and recorded so nobody proposes it again believing savepoints are enough.

### Option C — record through the outbox

`Infer` publishes an `ai.inference_recorded` event in the caller's transaction; a relay consumer projects it into `ai_inference`.

**For.** Reuses the transactional outbox the platform already has, no new connection in the request path, and the relay is already the durable-delivery mechanism.

**Against.** **It does not solve the problem either.** The outbox insert is in the same transaction, so a rollback discards the event exactly as it discards the row. The only way this works is if the event is published *outside* the failing transaction, which reduces to Option A with more moving parts. It also splits the ungrounded rate's source of truth into "the table" and "whatever the relay has processed so far", creating a window where the metric is wrong for a different reason — and duplicate truth is the thing we most consistently remove.

### Option D — record after the unit of work, at the composition boundary

`Infer` returns the record instead of writing it; the caller's entry point writes it after the transaction resolves, either way.

**For.** No second connection during the call. Explicit.

**Against.** It makes recording the *caller's* responsibility, so a caller that forgets simply produces no history — and "every outcome is recorded" stops being a guarantee `Infer` can make and becomes a convention thirteen modules must remember. That is precisely the shape of guarantee this codebase converts *into* enforcement rather than out of it. **Recommended for rejection.**

## Recommendation

**Option A**, with two qualifications drawn from the objections above:

1. **The recorder owns a session factory, not a session**, injected at the composition root — so the AI Platform's infrastructure decides when to open a connection and no caller is involved.
2. **The commit semantics are stated in the record, not left to a reader.** A row means *"this call was made and this is how it ended"*, which is deliberately independent of whether the business transaction that requested it survived. That is the honest meaning: tokens were spent and a vendor was called, and those facts do not un-happen because a later step failed.

Option B and Option D are recommended for **explicit rejection** — B because savepoints cannot do what it claims, D because it converts a guarantee into a convention. Option C is recommended for rejection on the same ground as B, plus duplicate truth.

## Consequences if ratified

**Positive.** AC-69 becomes true in production, not only in the domain. R-10's metric becomes trustworthy. The `ai_inference` table finally has the lifetime its category implies, and `ai_narration` — which *should* roll back with its business transaction, because a narration nobody committed was never shown to anyone — keeps the lifetime *its* category implies. The distinction between the two becomes visible in the code rather than accidental.

**Negative, and accepted.** One additional short-lived connection per inference, worst at the worst time; and a documented asymmetry where a recorded inference may describe work whose business effects were discarded.

**Required alongside the implementation.** A Security Invariant proving the row survives a rolled-back caller — because this is a guarantee that was believed and untrue for a day, and the only defence against that recurring is a test that fails when it stops holding. The recording identity remains `signora_app`, with `workspace_id`, forced RLS, and the existing grants unchanged: **this ADR changes when the row is committed, never who may write or read it.**

**Not in scope.** `ai_narration` keeps the caller's transaction. Business events keep the outbox. Nothing about tenancy, ordering, or the platform freeze changes.

## Status of this document

**Proposed, not decided.** No code has been written against it, and none should be until it is ratified — the finding was raised deliberately rather than fixed inside the milestone that found it, and this ADR exists so the decision is explicit rather than emerging from an implementation. The behaviour as it stands today is asserted by an integration test in `tests/ai_platform/test_narration.py`, with the desired behaviour written into its failure message, so the day this is implemented is the day that test notices.
