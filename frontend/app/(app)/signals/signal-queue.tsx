'use client';

import { useEffect, useMemo, useState } from 'react';

import { Badge, Button, Card, Dialog, EmptyState, ErrorState, Input, Skeleton, Tabs } from '@/components/ui';
import type { QueueEntry, QueueState, ResolveOutcome } from '@/lib/api/types';
import { useSignalCatalog } from '@/lib/query/hooks';
import { AccountName } from '@/components/intelligence/account-name';
import { useAccountIdentities } from '@/lib/query/hooks';
import { useResolveSignal, useWorkspaceTriage } from '@/lib/query/hooks/triage';
import { cn } from '@/lib/design/cn';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';

/**
 * **The Signal Center** — [TASK-439](../../../../docs/BACKLOG.md), against
 * `docs/design-snapshot/screens/Fortune Signora Signal Center.dc.html`
 * ([D-138](../../../../docs/DECISION_REGISTER.md)).
 *
 * > 📁 ***"A triage queue, not a notification list · every signal ends in a
 * > decision."***
 *
 * ## ⛔ What this slice is, and what it deliberately is not
 *
 * **The row's `Delivers` is the boundary, not the design's page count**:
 * *"the queue, grouped and counted · the four ways a signal ends · a dismissal
 * reason · snoozed signals returning at their stated time."*
 *
 * ⚠️ **The design also draws signal analytics, a rules engine with automatic
 * retuning, per-signal evidence, reasoning and a timeline.** ⛔ **None of that
 * is built here.** **No row covers them and none of their reads exist** —
 * building them would be inventing scope ([§21](../../../../CLAUDE.md)), and
 * the row already bounded itself for exactly this reason.
 *
 * ## 🔴 Two fields the design draws are absent, and that is reported
 *
 * **The design's rows carry `title · type · summary · account · pips`.**
 * ✅ **Three resolve against what is published**: the catalog supplies the
 * title (*"the key travels and `useSignalCatalog` supplies the words"*),
 * `signal_type` is on the entry, and `AccountIdentity` supplies the name.
 *
 * ⛔ **`summary` and `confidence` have no source at all** —
 * [C-251](../../../../docs/LANE_COORDINATION.md). **They are ABSENT rather
 * than drawn empty or drawn locked**, which is
 * [C-248](../../../../docs/LANE_COORDINATION.md)'s precedent.
 *
 * ⚠️ **The tempting wrong move, named so nobody makes it later**: the catalog
 * carries `why_it_matters`, and rendering it as the row summary would look
 * right and be wrong on every row — **it is a fact about the *type*, identical
 * under every signal of that type**, printed where the design puts a
 * per-instance finding.
 */

/** 📁 The design's three tabs: *Needs review* · *Snoozed* · *Closed*. */
const STATES: readonly { value: QueueState; label: string }[] = [
  { value: 'open', label: 'Needs review' },
  { value: 'snoozed', label: 'Snoozed' },
  { value: 'closed', label: 'Closed' },
];

/**
 * ⛔ **A dismissal requires a reason and the type already says so** —
 * `ResolveOutcome` is a discriminated union where *"a dismissal without a
 * reason is unconstructable rather than merely rejected"*. **This screen keeps
 * that true at the edge**: the control cannot submit an empty one.
 *
 * 📁 **And the design says why it matters, which is not politeness**:
 * *"Dismissal reasons feed rule precision."* **A reason is an input to
 * retuning, so an empty one is a lost measurement rather than a rude click.**
 */
const MIN_REASON = 1;

export function SignalQueue() {
  const { activeWorkspace } = useWorkspaceContext();
  const workspaceId = activeWorkspace?.id ?? null;

  const [state, setState] = useState<QueueState>('open');
  const [dismissing, setDismissing] = useState<QueueEntry | null>(null);
  const [reason, setReason] = useState('');

  /**
   * 📁 **Surface ② — the design's filter chips** ([TASK-1468](../../../../docs/BACKLOG.md)).
   *
   * ⛔ **By `signal_type`, and NOT by the design's own example.** 📁 It draws
   * *"Confidence ≥ 3"* — 🔴 **`QueueEntry` publishes six fields and confidence
   * is not one of them**, so a confidence chip would be filtering on a number
   * this screen invented. **The gap is stated to the reader instead**
   * ([§20c](../../../../CLAUDE.md)).
   *
   * 🔴 **And the filter is CLIENT-side while the state tabs are SERVER-side —
   * the two are not the same decision.** 📁 [`triage.ts`](../../../lib/query/hooks/triage.ts)
   * says why: *"queue state is derived on the server from the decision in force
   * and the clock; a browser re-filtering a cached page would be re-deriving it
   * from stale inputs, and a snooze that had elapsed would keep looking
   * snoozed."* ⚡ **`signal_type` carries no clock** — it is a fact about the
   * signal, fixed when it was raised — **so narrowing on it locally cannot go
   * stale.** ⛔ **Nothing here may narrow `state`.**
   */
  const [types, setTypes] = useState<ReadonlySet<string>>(() => new Set());

  /**
   * 📁 **Surface ③ — bulk selection.** ⚡ **Held as `signal_id`s rather than as
   * entries**, so a selection survives a refetch that replaced the objects: 📁
   * `useResolveSignal` invalidates every triage view on each decision, **and a
   * selection of stale objects would act on rows that had already moved.**
   */
  const [selected, setSelected] = useState<ReadonlySet<string>>(() => new Set());

  const queue = useWorkspaceTriage(workspaceId, state);
  /**
   * 📁 **Surface ⑦ — the counts header.** ⚡ **A second read of the OPEN queue**,
   * so *"needs review"* is true on every tab rather than only on the one that
   * happens to be showing. ⛔ **react-query de-duplicates it against the tab's
   * own request when `state` is `open`**, so this is one request, not two.
   */
  const open = useWorkspaceTriage(workspaceId, 'open');
  const catalog = useSignalCatalog(workspaceId);
  const resolve = useResolveSignal(workspaceId);

  const all = useMemo(() => queue.data?.items ?? [], [queue.data]);

  /**
   * ⚡ **What the list shows** — `all` narrowed by the chosen types. ⛔ **An
   * empty selection is *not narrowed*, never *nothing*** — the same rule
   * [`working-list.ts`](../../../lib/views/working-list.ts) applies to `all`:
   * **the absence of a narrowing is not a narrowing to zero.**
   */
  const entries = useMemo(
    () => (types.size === 0 ? all : all.filter((entry) => types.has(entry.signal_type))),
    [all, types],
  );

  // ⚡ **One request for every name on the page**, not one per row — the hook
  // de-duplicates and sorts the ids so the key is stable.
  const identities = useAccountIdentities(
    workspaceId,
    entries.map((entry) => entry.entity_id),
  );

  /** The catalog's words for a key. ⛔ **Never a table in this file** — that
   * would be the second vocabulary the architecture forbids. */
  const titleFor = (key: string): string => catalog.data?.get(key)?.title ?? key;

  /**
   * 📁 *"Grouped and counted."* **Grouped by signal type**, which is the only
   * grouping the published contract can support — ⛔ severity, the design's
   * other axis, is not a field the entry carries.
   */
  const groups = useMemo(() => {
    const byType = new Map<string, QueueEntry[]>();
    for (const entry of entries) {
      const bucket = byType.get(entry.signal_type);
      if (bucket === undefined) byType.set(entry.signal_type, [entry]);
      else bucket.push(entry);
    }
    return [...byType.entries()].sort((a, b) => b[1].length - a[1].length);
  }, [entries]);

  /**
   * ⛔ **The chips are built from the UNFILTERED page, never from `entries`.**
   * ⚡ **Otherwise choosing a type removes every other chip** — the control
   * that narrows the list would delete the way back, which is the
   * control-that-traps-you shape rather than a filter.
   */
  const availableTypes = useMemo(() => {
    const counts = new Map<string, number>();
    for (const entry of all) counts.set(entry.signal_type, (counts.get(entry.signal_type) ?? 0) + 1);
    return [...counts.entries()].sort((a, b) => b[1] - a[1]);
  }, [all]);

  const toggleType = (type: string) =>
    setTypes((was) => {
      const next = new Set(was);
      if (next.has(type)) next.delete(type);
      else next.add(type);
      return next;
    });

  /**
   * ⛔ **Selection is cleared whenever the visible set changes.** ⚠️ **A
   * selection that survives a filter is a selection whose action bar says
   * *"3 selected"* while two of them are off screen** — and the person presses
   * it believing it means the three they can see.
   */
  const visibleIds = entries.map((entry) => entry.signal_id).join(',');
  useEffect(() => setSelected(new Set()), [visibleIds]);

  const toggleSelected = (signalId: string) =>
    setSelected((was) => {
      const next = new Set(was);
      if (next.has(signalId)) next.delete(signalId);
      else next.add(signalId);
      return next;
    });

  const decide = (entry: QueueEntry, outcome: ResolveOutcome) => {
    resolve.mutate({ signalId: entry.signal_id, outcome });
  };

  /**
   * 📁 **Surface ③'s action bar.** ⛔ **Only the outcomes that need no further
   * input.** ⚠️ **Dismissal is deliberately NOT here**: 📁 the queue's own rule
   * is that a dismissal carries a reason — *"a dismissal without a reason is
   * unconstructable rather than merely rejected"* — **and one reason typed once
   * for eleven different signals is the reason nobody can cite later.**
   */
  const decideMany = (outcome: ResolveOutcome) => {
    for (const signalId of selected) resolve.mutate({ signalId, outcome });
    setSelected(new Set());
  };

  if (queue.isError || catalog.isError) {
    // ⛔ **[P-A](../../../../docs/DOMAIN_DISCOVERY_REGISTER.md): a page must say
    // when it could not find out.** An empty queue and an unreachable one are
    // different facts and must never render the same.
    return (
      <ErrorState
        title="The queue could not be loaded"
        description="Signora could not reach the signal service. Nothing has been lost — every signal is still waiting."
      />
    );
  }

  return (
    <section className="flex flex-col gap-6" aria-labelledby="signals-heading">
      <header className="flex flex-col gap-2">
        <h1 id="signals-heading" className="text-xl font-semibold tracking-tight text-content">
          Signals
        </h1>
        <p className="text-sm leading-6 text-content-muted">
          Detected events arrive continuously. Every one leaves the queue by being actioned,
          assigned, snoozed or dismissed with a reason.
        </p>
      </header>

      {/* 📁 The design's three states, and the count is on the tab.
          ⛔ **This block WAS a local `role="tab"` implementation** — 📁 the only
          workflow-local reimplementation
          [498](../../../../docs/architecture/498-common-platform-audit.md)
          found. ⚡ **[TASK-1448](../../../../docs/BACKLOG.md) makes it the
          shared `Tabs`**, and the migration is not cosmetic: **the local one
          had `role="tab"` and `aria-selected` and no arrow-key navigation**,
          so it announced itself as tabs and behaved like a row of buttons. */}
      {/* 📁 **Surface ⑦ — the counts header.** The design draws *"14 need review
          · 6 assigned to you · 41 this week"*.
          🔴 **ONE of those three is publishable and the other two are absent
          rather than approximated.** ⛔ **`QueueEntry` has no assignee** — so
          *"assigned to you"* would be a number this screen invented — **and no
          timestamp**, so *"this week"* has no clock to count against.
          ⚡ **[§20c](../../../../CLAUDE.md): screens without a shipped module
          behind them state the absence.** **The gap is
          [C-292](../../../../docs/LANE_COORDINATION.md).** */}
      {open.isPending ? null : (
        <p className="text-sm text-content-muted" data-testid="queue-counts">
          <span className="font-medium text-content tabular-nums">
            {open.data?.items.length ?? 0}
          </span>{' '}
          need review
          {/* ⛔ **Never a second number here to fill the design's shape.** */}
        </p>
      )}

      <Tabs
        label="Queue state"
        items={STATES.map((tab) => ({
          value: tab.value,
          label: tab.label,
          // ⛔ **The count only when it is known.** A count rendered while the
          // read is pending would be a number the screen cannot support.
          badge:
            state === tab.value && !queue.isPending ? entries.length : undefined,
        }))}
        value={state}
        onChange={setState}
      />

      {/* 📁 **Surface ② — the filter chips and *"14 of 22 shown"*.**
          ⛔ **Rendered only when there is more than one type to choose
          between**: a single chip that cannot narrow anything is a control
          that does nothing ([§2](../../../../CLAUDE.md)). */}
      {availableTypes.length > 1 ? (
        <div className="flex flex-wrap items-center gap-2" data-testid="signal-filters">
          <span className="text-2xs uppercase tracking-wide text-content-subtle">Filter</span>
          {availableTypes.map(([type, count]) => {
            const on = types.has(type);
            return (
              <button
                key={type}
                type="button"
                onClick={() => toggleType(type)}
                // ♿ **`aria-pressed`, not a styled `div`.** A chip that only
                // looks selected is unselected to a screen reader.
                aria-pressed={on}
                className={cn(
                  'flex h-7 items-center gap-1.5 rounded-full border px-3 text-2xs transition-colors',
                  'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent',
                  on
                    ? 'border-accent bg-accent-subtle font-semibold text-accent'
                    : 'border-border text-content-muted hover:bg-surface-sunken hover:text-content',
                )}
              >
                {titleFor(type)}
                <span className="tabular-nums">{count}</span>
              </button>
            );
          })}
          {types.size > 0 ? (
            <>
              {/* 📁 The design's *"14 of 22 shown"*, and ⚡ **both numbers are
                  counted rather than claimed.** */}
              <span className="tabular-nums text-2xs text-content-subtle">
                {entries.length} of {all.length} shown
              </span>
              {/* ⛔ **The way back is always offered.** ⚠️ A narrowing a reader
                  cannot undo in one action is how an empty list gets reported
                  as missing data. */}
              <button
                type="button"
                onClick={() => setTypes(new Set())}
                className="rounded text-2xs text-accent underline decoration-border underline-offset-4 transition-colors hover:decoration-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
              >
                Clear
              </button>
            </>
          ) : null}
        </div>
      ) : null}

      {/* 📁 **Surface ③'s action bar** — the design's *"✓ 3 selected"*.
          ⛔ **Present only when something is selected**, and ♿ **`role="status"`**
          so a screen-reader user learns the count changed without being
          interrupted mid-row. */}
      {selected.size > 0 ? (
        <div
          role="status"
          data-testid="bulk-bar"
          className="flex flex-wrap items-center gap-3 rounded-lg border border-accent bg-accent-subtle px-4 py-2.5"
        >
          <span className="text-sm font-medium text-accent tabular-nums">
            {selected.size} selected
          </span>
          <Button variant="secondary" onClick={() => decideMany({ kind: 'actioned' })}>
            Mark actioned
          </Button>
          {/* 🔴 **One action, and the other three are absent for reasons the
              contract states rather than for lack of room.**
              ⛔ **No bulk dismissal** — 📁 `ResolveOutcome` makes a dismissal
              without a reason *unconstructable rather than merely rejected*,
              and **one reason typed once for eleven signals is the reason
              nobody can cite later.**
              ⛔ **No bulk snooze** — **`snoozed` requires an `until`**, this
              screen has no per-row snooze to borrow a duration from, and ⚡
              **inventing one would decide on a customer's behalf when a signal
              comes back.**
              ⛔ **No bulk assign** — `assigned` requires a person, which is a
              choice per signal rather than per selection.
              ✅ **`actioned` is the only outcome the union lets a bulk control
              construct honestly.** */}
          <button
            type="button"
            onClick={() => setSelected(new Set())}
            className="ml-auto rounded text-2xs text-accent underline decoration-border underline-offset-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          >
            Clear selection
          </button>
        </div>
      ) : null}

      {queue.isPending ? (
        <div className="flex flex-col gap-3" aria-hidden>
          <Skeleton className="h-16" />
          <Skeleton className="h-16" />
          <Skeleton className="h-16" />
        </div>
      ) : entries.length === 0 ? (
        /* ⚡ **A quiet queue is a success state and must read as one** — the
           design's own rule on the neighbouring screen. */
        <EmptyState
          title={state === 'open' ? 'Nothing needs review' : 'Nothing here'}
          description={
            state === 'open'
              ? 'Every signal Signora raised has been actioned, assigned, snoozed or dismissed.'
              : 'No signals are in this state.'
          }
        />
      ) : (
        <div className="flex flex-col gap-6">
          {groups.map(([type, rows]) => (
            <div key={type} className="flex flex-col gap-2">
              <h2 className="flex items-center gap-2 text-sm font-medium text-content">
                {titleFor(type)}
                <span className="tabular-nums text-content-subtle">{rows.length}</span>
              </h2>

              <ul className="flex flex-col gap-2">
                {rows.map((entry) => {
                  const identity = identities.data?.get(entry.entity_id) ?? null;
                  return (
                    <li key={entry.signal_id}>
                      <Card className="flex flex-wrap items-start justify-between gap-3 p-4">
                        {/* 📁 **Surface ③'s per-row control.**
                            ♿ **A real `<input type="checkbox">`**, not a styled
                            button: ⛔ **it is what gives a screen reader the
                            checked state, the group semantics and the shift-
                            click behaviour a reader already knows** — and
                            reimplementing those is the workflow-local
                            reimplementation [498](../../../../docs/architecture/498-common-platform-audit.md)
                            found once already on this very screen's tabs.
                            ⚡ **The label names the SIGNAL, never *"select"***,
                            so somebody hearing the row hears what they are
                            about to act on. */}
                        <input
                          type="checkbox"
                          checked={selected.has(entry.signal_id)}
                          onChange={() => toggleSelected(entry.signal_id)}
                          aria-label={`Select ${titleFor(entry.signal_type)}`}
                          className="mt-1 h-4 w-4 shrink-0 accent-accent focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
                        />
                        <div className="flex min-w-0 flex-col gap-1">
                          <span className="text-sm font-medium text-content">
                            {titleFor(entry.signal_type)}
                          </span>
                          {/* ⚠️ **Nullable by design** — *"`name` is null when
                              nobody has named the account"*. ⛔ The id is not
                              printed as a fallback: an id is not a name, and a
                              seller cannot act on one. */}
                          {/* 🔴 **B-290** — ⛔ the identity read settles after
                              the queue does, so this rendered its fallback as an
                              answer and then replaced it. */}
                          <AccountName
                            name={identity?.name ?? null}
                            pending={identities.isPending}
                            absent="Unnamed account"
                            className="text-sm text-content-muted"
                          />
                          {/* 🔴 **Per signal, never per type.** The catalog's
                              `why_it_matters` describes the TYPE and would read
                              as right under all fifty rows; `rationale` is
                              authored where the reasoning happened.
                              ⛔ **Not recomposed here** — the interpretation a
                              customer reads and the evidence an auditor checks
                              must not diverge, so this renders the sentence and
                              composes nothing.
                              📱 **Clamped to two lines and complete in the DOM**:
                              the full text stays readable to assistive tech and
                              on hover, because a truncated reason that reads as
                              the whole reason is worse than none. */}
                          <p
                            className="line-clamp-2 text-sm leading-6 text-content-muted"
                            title={entry.rationale}
                          >
                            {entry.rationale}
                          </p>
                        </div>

                        {entry.state === 'open' ? (
                          <div className="flex flex-wrap items-center gap-2">
                            <Button
                              size="sm"
                              onClick={() => decide(entry, { kind: 'actioned' })}
                              disabled={resolve.isPending}
                            >
                              Actioned
                            </Button>
                            <Button
                              size="sm"
                              variant="secondary"
                              onClick={() => setDismissing(entry)}
                              disabled={resolve.isPending}
                            >
                              Dismiss
                            </Button>
                          </div>
                        ) : (
                          <Badge>{entry.resolution?.outcome ?? entry.state}</Badge>
                        )}
                      </Card>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </div>
      )}

      <Dialog
        open={dismissing !== null}
        onClose={() => {
          setDismissing(null);
          setReason('');
        }}
        title="Why is this not worth acting on?"
        description="Dismissal reasons feed rule precision — a rule dismissed often enough is proposed for retuning."
        footer={
          <div className="flex flex-wrap items-center gap-3">
            <Button
              // ⛔ **Cannot submit an empty reason.** The type makes a
              // reasonless dismissal unconstructable; this keeps that true at
              // the edge rather than relying on the server to refuse it.
              disabled={reason.trim().length < MIN_REASON || resolve.isPending}
              onClick={() => {
                if (dismissing === null) return;
                decide(dismissing, { kind: 'dismissed', reason: reason.trim() });
                setDismissing(null);
                setReason('');
              }}
            >
              Dismiss signal
            </Button>
            <Button
              variant="secondary"
              onClick={() => {
                setDismissing(null);
                setReason('');
              }}
            >
              Cancel
            </Button>
          </div>
        }
      >
        <Input
          label="Reason"
          value={reason}
          onChange={(event) => setReason(event.target.value)}
          placeholder="Already handled on the call"
        />
      </Dialog>
    </section>
  );
}
