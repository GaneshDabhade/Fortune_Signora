'use client';

import { UserCog } from 'lucide-react';
import { useState } from 'react';

import { cn } from '@/lib/design/cn';
import type { WorkspaceEntry } from '@/lib/api/types';

/**
 * 📁 **Authenticated Entry rule 21**, hosted by Home:
 *
 * > *"**Role changed since last session** — Home, with a notice naming **what
 * > changed and by whom**. The composition may differ from yesterday and **that
 * > must not be silent**."*
 * >
 * > 📁 **Home's entry-point table**: *"Adds a notice; **the composition itself
 * > does not change mid-session**."*
 *
 * ## ⛔ It says what changed, never *"your permissions were updated"*
 *
 * ⚡ **The design's whole reason is that a silently different Home is
 * disorienting** — somebody who was an owner yesterday and sees fewer controls
 * today must be told, and told *by whom*, because that is the person they will
 * ask.
 *
 * ## ⚡ The wording is the repository's, not this component's
 *
 * 📁 [`components/team/history.tsx`](../team/history.tsx) already publishes the
 * ratified sentences for a role change — *"made {them} able to administer
 * Signora"* and *"moved {them} to working accounts"* — and 📁 D23's *"Somebody"*
 * for an actor with no known address. ⛔ **Inventing a second phrasing for the
 * same event is the vocabulary drift [ADR-0034](../../../docs/architecture/adr/0034-ubiquitous-language.md)
 * exists to prevent**, and it would leave the team log and Home describing one
 * change in two ways.
 *
 * ⚠️ **Second person, because Home is talking to the subject.** The history log
 * narrates about somebody; this notice is addressed to them.
 *
 * ## ⛔ The composition does not change while they are here
 *
 * 📁 The entry table says so by name. ⚡ **This component renders and nothing
 * else** — it triggers no refetch and resolves no composition, so a role change
 * takes effect on the next entry rather than under somebody's cursor.
 */
export interface RoleChangeNoticeProps {
  readonly change: WorkspaceEntry['role_change'];
}

export function RoleChangeNotice({ change }: RoleChangeNoticeProps) {
  const [dismissed, setDismissed] = useState(false);

  if (change === null || change === undefined || dismissed) return null;

  /**
   * 📁 The ratified sentences, in the second person.
   *
   * ⛔ **`previous_role` is deliberately unused in the sentence.** ⚡ The
   * repository's own wording names the destination — *"able to administer
   * Signora"* — and a *"from member to owner"* construction is the engineering
   * vocabulary ADR-0034 keeps off a screen. **The field is on the contract
   * because the log records it**, not because a reader needs it.
   */
  const who = change.changed_by_email ?? 'Somebody';
  const what =
    change.new_role === 'owner'
      ? `${who} made you able to administer Signora.`
      : `${who} moved you to working accounts.`;

  return (
    /**
     * ♿ **`role="status"`** — 📁 4.1.3, and the greeting owns the one entry
     * announcement. ⛔ **Not `alert`**: a role change is a fact about where
     * somebody stands, not an emergency.
     *
     * ⚡ **Warn rather than danger.** 📁 System States: *"neutral for absence,
     * **warn for permission** and interruption, risk for genuine failure"* — and
     * a red strip would read as something having gone wrong.
     */
    <div
      role="status"
      data-testid="role-change"
      className={cn(
        'flex flex-wrap items-center gap-x-3 gap-y-2 rounded-lg px-4 py-3',
        'border border-warning-line bg-warning-subtle',
      )}
    >
      <span
        aria-hidden
        className="grid h-5 w-5 flex-none place-items-center rounded-sm bg-surface text-warning"
      >
        <UserCog className="h-3 w-3" />
      </span>
      <p className="text-label leading-[1.5] text-content">
        {what}{' '}
        <span className="text-content-muted">
          What you can see here may have changed.
        </span>
      </p>
      {/* 📁 **Dismissible.** ⚡ It is a notice about something already done — there
          is nothing to act on, and a strip with no dismiss on a page somebody
          opens every morning becomes furniture. ⛔ Per-mount rather than stored:
          the notice only appears on the entry that follows the change. */}
      <button
        type="button"
        onClick={() => setDismissed(true)}
        className="ml-auto inline-flex h-control-sm items-center rounded-md px-2 text-2xs font-semibold text-content-subtle transition-colors hover:text-content "
      >
        Dismiss
      </button>
    </div>
  );
}
