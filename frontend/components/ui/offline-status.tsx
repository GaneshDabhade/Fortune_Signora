'use client';

import { useEffect, useState } from 'react';

import { cn } from '@/lib/design/cn';
import { useQueuedEdits } from '@/lib/query/offline';

/**
 * **You are offline, and here is what is waiting** —
 * [TASK-1435](../../../docs/BACKLOG.md).
 *
 * > 📁 **System States §04**: ***"Signora keeps working on what it already
 * > has. The table you were reading is still here, filters still apply, and
 * > two edits are queued. They are sent in order when the connection returns —
 * > the queue is visible, not implied."***
 *
 * ## ⚡ A status pill, and the design says which surface rather than leaving it
 *
 * ⚠️ **§04 says *"Banner, not takeover"*, and reading only that sentence sends
 * you to the shell's banner region** — where the constitution admits exactly
 * two kinds, `environment` and `commercial`, and offline is neither.
 * 📁 **The App Shell design answers it: §07 — *"System status is a persistent
 * pill in the top bar rather than a banner — degradation is a fact about the
 * product, not an interruption."*** ✅ **And the offline entry is
 * `scope: 'In shell'`**, which is the same answer from the other document.
 *
 * ⛔ **So no third banner kind is invented and shell rule 14 is not touched.**
 * ⚡ **`system-status` is already a declared slot** in
 * [`lib/shell/top-bar.ts`](../../lib/shell/top-bar.ts), placed by
 * [TASK-1408](../../../docs/BACKLOG.md) before anything needed it.
 *
 * ## 🔴 *Visible, not implied* is the acceptance criterion, so the count is the point
 *
 * ⛔ **A pill reading *"Offline"* and nothing else is the *implied* version the
 * design refuses.** ⚡ **The number of waiting edits is what turns it from a
 * status into a promise a person can check**, which is why the count is in the
 * label rather than behind the disclosure.
 *
 * ## ⚠️ It renders nothing when there is nothing to say
 *
 * ⛔ **Online with an empty queue renders `null`** — not a green *"Online"*
 * pill. 📁 §07's green state hides its own label below 1280px, and a pill
 * whose only content is *"everything is fine"* is chrome that costs a slot
 * every screen inherits.
 */

/** 📁 The design's own line, and it names both facts. */
const OFFLINE_TITLE = 'You are offline';

export function OfflineStatus({ className }: { className?: string }) {
  const queued = useQueuedEdits();
  const [open, setOpen] = useState(false);
  // ⛔ **Not read during render.** The server has no `navigator`, so reading it
  // in the render body disagrees with the markup Next produced and loses the
  // tree — the same hydration rule `use-rail-collapse.ts` documents.
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    const sync = () => setOffline(!navigator.onLine);
    sync();
    window.addEventListener('online', sync);
    window.addEventListener('offline', sync);
    return () => {
      window.removeEventListener('online', sync);
      window.removeEventListener('offline', sync);
    };
  }, []);

  // ⚡ **Still shown while the queue drains after reconnect**: the sentence
  // *"they are sent when the connection returns"* is only true if somebody can
  // watch it happen.
  if (!offline && queued.length === 0) return null;

  const label = offline
    ? OFFLINE_TITLE
    : `Sending ${queued.length} ${queued.length === 1 ? 'edit' : 'edits'}`;

  return (
    <div className={cn('relative', className)}>
      <button
        type="button"
        onClick={() => setOpen((was) => !was)}
        aria-expanded={open}
        // ♿ The pill is two or three words; the accessible name carries the
        // consequence, which is what a person actually needs to hear.
        aria-label={
          queued.length === 0
            ? OFFLINE_TITLE
            : `${label}. ${queued.length} waiting to send, in order.`
        }
        data-offline={offline}
        className={cn(
          'flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium',
          'transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent',
          offline
            ? 'border-warning/30 bg-warning-subtle text-warning'
            : 'border-border bg-surface-sunken text-content-muted',
        )}
      >
        <span aria-hidden>⇎</span>
        <span>{label}</span>
        {/* 🔴 *visible, not implied* — the number is in the label, never only
            behind the disclosure. */}
        {queued.length > 0 && offline ? (
          <span className="rounded-full bg-warning/15 px-1.5">{queued.length}</span>
        ) : null}
      </button>

      {/* 📁 §07 — *"it expands into detail on click."* The list is the design's
          `{{ q.t }} {{ q.meta }} {{ q.state }}`, in send order. */}
      {open && queued.length > 0 ? (
        <div
          role="status"
          className="absolute right-0 z-20 mt-2 w-72 rounded-lg border border-border bg-surface p-3 shadow-lg"
        >
          <p className="mb-2 text-2xs font-semibold uppercase tracking-wide text-content-subtle">
            Waiting to send, in order
          </p>
          <ol className="flex flex-col gap-2">
            {queued.map((edit) => (
              <li key={edit.id} className="flex items-baseline justify-between gap-3">
                <span className="min-w-0 flex-1 truncate text-sm text-content">{edit.title}</span>
                {edit.meta === undefined ? null : (
                  <span className="shrink-0 text-2xs text-content-subtle">{edit.meta}</span>
                )}
              </li>
            ))}
          </ol>
          {/* ⛔ **No *Send now*.** The library sends on reconnect and there is
              nothing a button could do while the connection is gone — §2's
              control that does nothing, and the worse kind: one a person
              presses during an outage and believes. */}
          <p className="mt-3 text-2xs text-content-subtle">
            Signora sends these in order as soon as the connection returns.
          </p>
        </div>
      ) : null}
    </div>
  );
}
