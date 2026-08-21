'use client';

import type { HistoryEntry } from '@/lib/api/types';

/**
 * What has happened to this organization.
 *
 * ### Why this is not the account timeline, having checked
 *
 * `components/timeline/feed.tsx` groups by day, renders newest first, and
 * translates a `kind` through a reviewed catalog — **the same shape this
 * needs**, which made reuse the obvious move.
 *
 * **It is the wrong abstraction, and one difference decides it.** The account
 * timeline answers *what happened to this account* and **names nobody**. This
 * answers ***who did what to whom***, so an actor and a subject are structural
 * rather than fields inside `detail`. Bending the feed to carry two people
 * would make every account entry pay for a pair it never has.
 *
 * **And extracting a shared framework now would be generalising from two
 * instances** — the same *two is a coincidence, three is a pattern* rule that
 * refused a generic pending-relationship aggregate
 * ([46-team-management.md](../../../docs/architecture/46-team-management.md) §11).
 * **The trigger is stated: a third history surface.**
 *
 * ### The sentences are here, not on the wire
 *
 * The API sends `kind`, two people and the roles. **A rendered sentence would
 * make improving the wording a migration**, and would stop an export phrasing
 * the same entry differently (ADR-0034).
 */
export function OrganizationHistory({
  entries,
  isLoading,
  isError,
}: {
  entries: readonly HistoryEntry[];
  isLoading: boolean;
  isError: boolean;
}) {
  if (isLoading) return <p className="text-sm text-content-muted">Loading history…</p>;
  if (isError) {
    // Rendered rather than absent: a section that vanishes on failure reads as
    // a feature the customer does not have (B-006).
    return (
      <p className="text-sm text-content-muted">
        This organization&rsquo;s history could not be loaded. Try again in a moment.
      </p>
    );
  }
  /**
   * 🔴 **[B-420](../../../docs/BUGS.md) — this guard HID the crash rather than
   * catching it.**
   *
   * ⛔ **When the hook handed over the `CursorPage` envelope instead of an
   * array, `entries.length` was `undefined`** — and `undefined === 0` is
   * `false`, **so the envelope passed straight through this guard to the
   * `for…of` below it.** ⚡ **A guard standing directly in front of the defect
   * and waving it past is worse than no guard**: it is where a reader looks
   * first and finds nothing wrong.
   *
   * ✅ **`Array.isArray` asks the question the `for…of` actually needs
   * answered.** ⛔ **It is not defensive noise** — the hook's type is a claim
   * about the wire, and this is the one place that claim meets reality before
   * something iterates it.
   */
  if (!Array.isArray(entries) || entries.length === 0) {
    return (
      <p className="text-sm text-content-muted">
        Nothing has happened here yet. Inviting somebody, changing what they can do,
        or removing them will all appear here.
      </p>
    );
  }

  const days = groupByDay(entries);

  return (
    <div className="flex flex-col gap-5">
      {days.map(([day, ofThatDay]) => (
        <section key={day} className="flex flex-col gap-2">
          <h3 className="text-xs font-medium uppercase tracking-wide text-content-subtle">
            {day}
          </h3>
          <ol className="flex flex-col gap-2">
            {ofThatDay.map((entry, index) => (
              <li
                key={`${entry.occurred_at}:${index}`}
                className="flex items-baseline justify-between gap-4 border-l-2 border-border pl-3"
              >
                {/* 🔴 **`min-w-0 break-words`, and both halves are load-bearing.**
                    ⛔ **An audit sentence names a person by EMAIL, and an email
                    is one unbreakable word** — so this paragraph's min-content
                    was the whole address, the row could not shrink to its
                    container, and the DOCUMENT scrolled sideways at 390px.
                    ⚡ **Measured on `/settings`: the column reached 494px
                    against a 375px viewport.** ⚠️ **`min-w-0` alone only lets
                    the box shrink; without `break-words` the text still
                    overflows it.** 📁 **A flex child defaults to
                    `min-width:auto`, which is why this needs saying at all.** */}
                <p className="min-w-0 break-words text-md leading-6 text-content">
                  {sentence(entry)}
                </p>
                <time
                  className="shrink-0 text-xs text-content-subtle"
                  dateTime={entry.occurred_at}
                >
                  {timeOf(entry.occurred_at)}
                </time>
              </li>
            ))}
          </ol>
        </section>
      ))}
    </div>
  );
}

/**
 * One entry, as a person would say it.
 *
 * **An auditor, a support engineer and a new owner must all understand it
 * without knowing how Signora is built** — so no entry names a table, a role
 * enum value, an identifier, or an operation.
 *
 * **`Somebody` where no actor was recorded**, which is the D23 convention and
 * is honest: an invitation withdrawn today records no actor, and attributing
 * it to the inviter would be a guess about a different person.
 */
function sentence(entry: HistoryEntry): string {
  const who = entry.actor_email ?? 'Somebody';
  const them = entry.subject_email ?? 'somebody';

  switch (entry.kind) {
    case 'joined':
      return entry.new_role === 'owner'
        ? `${them} created this organization`
        : `${them} joined`;
    case 'invited':
      return `${who} invited ${them} as ${roleWords(entry.new_role)}`;
    case 'invitation_withdrawn':
      return `${who} withdrew the invitation to ${them}`;
    case 'invitation_accepted':
      return `${them} accepted their invitation`;
    case 'role_changed':
      return entry.new_role === 'owner'
        ? `${who} made ${them} able to administer Signora`
        : `${who} moved ${them} to working accounts`;
    case 'removed':
      return entry.reason
        ? `${who} removed ${them} — ${entry.reason}`
        : `${who} removed ${them} from this organization`;
    default:
      return `${who} changed something`;
  }
}

/** The catalog's words, never the enum's (ADR-0034). */
function roleWords(role: string | null): string {
  return role === 'owner' ? 'somebody who can administer Signora' : 'somebody who works accounts';
}

function groupByDay(entries: readonly HistoryEntry[]): [string, HistoryEntry[]][] {
  const days = new Map<string, HistoryEntry[]>();
  for (const entry of entries) {
    const day = new Date(entry.occurred_at).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
    days.set(day, [...(days.get(day) ?? []), entry]);
  }
  return [...days.entries()];
}

function timeOf(iso: string): string {
  return new Date(iso).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
}
