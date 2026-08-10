'use client';

import { useMemo, useState } from 'react';

import { Badge, Button, Card, Dialog, EmptyState, ErrorState, Input, Skeleton, Tabs } from '@/components/ui';
import type { QueueEntry, QueueState, ResolveOutcome } from '@/lib/api/types';
import { useSignalCatalog } from '@/lib/query/hooks';
import { useAccountIdentities } from '@/lib/query/hooks';
import { useResolveSignal, useWorkspaceTriage } from '@/lib/query/hooks/triage';
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

  const queue = useWorkspaceTriage(workspaceId, state);
  const catalog = useSignalCatalog(workspaceId);
  const resolve = useResolveSignal(workspaceId);

  const entries = useMemo(() => queue.data?.items ?? [], [queue.data]);

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

  const decide = (entry: QueueEntry, outcome: ResolveOutcome) => {
    resolve.mutate({ signalId: entry.signal_id, outcome });
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
                        <div className="flex min-w-0 flex-col gap-1">
                          <span className="text-sm font-medium text-content">
                            {titleFor(entry.signal_type)}
                          </span>
                          {/* ⚠️ **Nullable by design** — *"`name` is null when
                              nobody has named the account"*. ⛔ The id is not
                              printed as a fallback: an id is not a name, and a
                              seller cannot act on one. */}
                          <span className="text-sm text-content-muted">
                            {identity?.name ?? 'Unnamed account'}
                          </span>
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
