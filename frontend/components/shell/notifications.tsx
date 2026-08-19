'use client';

import { Bell } from 'lucide-react';
import { useCallback, useId, useMemo, useRef, useState } from 'react';

import { StatedAbsence } from '@/components/feedback/stated-absence';
import { Tabs } from '@/components/ui/tabs';
import { cn } from '@/lib/design/cn';
import type { AppNotification } from '@/lib/api/types';
import {
  useMarkNotificationsRead,
  useNotifications,
  useUnreadNotifications,
} from '@/lib/query/hooks/notifications';
import { useDismissable } from '@/lib/shell/dismissable';
import { SLOT_SPEC, badgeLabel } from '@/lib/shell/top-bar';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';

/**
 * **The top bar's notification slot** — [TASK-495](../../../docs/BACKLOG.md)
 * slice ⓑ, against 📁 `Fortune Signora App Shell.dc.html` §10.
 *
 * > 📁 *"32 × 32. Count badge caps at 99+. **Opens a 400px panel, not a page.**"*
 * > 📁 *"400px popover at `--e4`, anchored to the bell, 12px from the top bar.
 * > **Grouped by day with sticky day heads.** Unread is a 6px dot on the right,
 * > **never a coloured row**."*
 *
 * ## 🔴 Why this slot was empty until now, and what changed
 *
 * ⛔ **It was left empty deliberately** — 📁 [C-275](../../../docs/LANE_COORDINATION.md),
 * and the comment that stood here said *"a bell that opens an empty 400px panel
 * is the defect [TASK-1433](../../../docs/BACKLOG.md) was parked for."* ⚡ **That
 * was true and is no longer**: slice ⓐ shipped the feed, the badge and the read
 * state, and `ai_research_engine` publishes into it when a research run finishes.
 * **The panel has something to show before it has a bell.**
 *
 * ## ⛔ Three tabs, and two of them are the server's own categories
 *
 * 📁 *"Needs you: approvals, mentions, assignments — anything blocking a person.
 * Mentions: comments and @-references only. All: everything."* ⚡ `Category` is
 * `needs_you | mention`, **so the taxonomy is the domain's rather than a
 * presentation invention**, and *All* is the absence of a filter.
 *
 * ## ⚠️ What the design draws that has no producer, and is therefore absent
 *
 * 📁 The reference panel shows a **system** row (*"Export finished — 8,412
 * rows"*) with a `Download` action, and an **ai** row distinct from an agent's.
 * ⛔ **`ActorKind` is `person | agent`**, and nothing exports or scores into this
 * feed. ⚡ **Absent rather than mocked** — 📁 [§20c](../../../CLAUDE.md), *"never
 * introduce mock business data"*, and a Download link that downloads nothing is
 * worse than no row.
 */

type Tab = 'needs_you' | 'mention' | 'all';

/**
 * 📁 **The design's order, and its first tab carries a count** — the reference
 * panel's tabs read *"Needs you · 3"*, *"Mentions"*, *"All"*.
 *
 * ⛔ **Only the first**, and that is the design's own asymmetry rather than an
 * omission: ⚡ *"Needs you"* is *"anything blocking a person"*, so its size is
 * the thing somebody is deciding whether to act on. **A count on *All* would be
 * the length of a list they can already see.**
 */
function tabsFor(items: readonly AppNotification[]): readonly { value: Tab; label: string }[] {
  // ⚡ **Unread only.** ⛔ A count of everything ever sent would never fall, and
  // a number that only rises is one people stop reading.
  const blocking = items.filter(
    (item) => item.category === 'needs_you' && item.read_at === null,
  ).length;
  return [
    { value: 'needs_you', label: blocking === 0 ? 'Needs you' : `Needs you · ${blocking}` },
    { value: 'mention', label: 'Mentions' },
    { value: 'all', label: 'All' },
  ];
}

/**
 * 📁 *"Grouped by day with sticky day heads."*
 *
 * ⚡ **Grouped in arrival order rather than sorted** — the feed is already newest
 * first, and 📁 *"the panel never reorders while open"* is a rule a second sort
 * could only break.
 */
export function groupByDay(
  items: readonly AppNotification[],
  today: Date,
): readonly { day: string; items: readonly AppNotification[] }[] {
  const groups: { day: string; items: AppNotification[] }[] = [];
  for (const item of items) {
    const day = dayLabel(new Date(item.occurred_at), today);
    const last = groups[groups.length - 1];
    if (last?.day === day) last.items.push(item);
    else groups.push({ day, items: [item] });
  }
  return groups;
}

/**
 * ⚡ **Today and Yesterday by name**, because a date beside a time a person can
 * still remember reads as older than it is.
 */
function dayLabel(at: Date, today: Date): string {
  const days = Math.round(
    (startOfDay(today).getTime() - startOfDay(at).getTime()) / 86_400_000,
  );
  if (days <= 0) return 'Today';
  if (days === 1) return 'Yesterday';
  return at.toLocaleDateString(undefined, { day: 'numeric', month: 'long' });
}

function startOfDay(at: Date): Date {
  return new Date(at.getFullYear(), at.getMonth(), at.getDate());
}

export function Notifications() {
  const { activeWorkspace } = useWorkspaceContext();
  const workspaceId = activeWorkspace?.id ?? null;
  const [open, setOpen] = useState(false);
  const [tab, setTab] = useState<Tab>('needs_you');
  const container = useRef<HTMLDivElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const panelId = useId();

  const badge = useUnreadNotifications(workspaceId);
  const feed = useNotifications(workspaceId, open);
  const markRead = useMarkNotificationsRead(workspaceId);

  const dismiss = useCallback(() => setOpen(false), []);
  useDismissable({ open, container, trigger, onDismiss: dismiss });

  const items = feed.data?.notifications ?? [];
  const shown = useMemo(
    () => (tab === 'all' ? items : items.filter((item) => item.category === tab)),
    [items, tab],
  );
  const groups = useMemo(() => groupByDay(shown, new Date()), [shown]);

  const label = badgeLabel(badge.data?.unread ?? 0);

  return (
    <div ref={container} className="relative shrink-0" data-slot="notifications">
      <button
        ref={trigger}
        type="button"
        onClick={() => setOpen((was) => !was)}
        aria-expanded={open}
        aria-haspopup="dialog"
        aria-controls={open ? panelId : undefined}
        /* ♿ **The count is in the name, not only in the dot.** ⛔ A control
           labelled *Notifications* tells a screen-reader user nothing about
           whether opening it is worth their time. */
        aria-label={
          label === null ? 'Notifications' : `Notifications, ${label} unread`
        }
        style={{ width: SLOT_SPEC.notifications.width, height: SLOT_SPEC.notifications.height }}
        className={cn(
          'relative flex items-center justify-center rounded-md text-content-muted',
          'transition-colors hover:text-content',
          'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2',
          'focus-visible:outline-accent',
        )}
      >
        <Bell className="h-[18px] w-[18px]" aria-hidden />
        {label === null ? null : (
          /* 📁 *"Count badge caps at 99+"* — ⚡ the cap is `badgeLabel`'s, and
             it was written for this slot before the slot existed. */
          <span
            aria-hidden
            data-testid="notification-badge"
            className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-danger px-1 text-2xs font-semibold leading-none text-accent-contrast"
          >
            {label}
          </span>
        )}
      </button>

      {open ? (
        <div
          id={panelId}
          /* ♿ **`dialog`, and the design calls it a popover** — ⛔ it is not a
             `menu`: its rows are content with their own controls rather than a
             list of commands, which is the distinction `SystemState` draws for
             the same reason. */
          role="dialog"
          aria-label={
            /* 📁 §*Multi-workspace* — *"when a user has more than one workspace,
               search, notifications and the assistant all carry the workspace
               name in their header. Ambiguity here is what causes the wrong
               customer to be discussed."* */
            activeWorkspace ? `Notifications — ${activeWorkspace.name}` : 'Notifications'
          }
          data-testid="notification-panel"
          /* 📁 *"400px popover… 12px from the top bar."* */
          className="absolute right-0 top-[calc(100%+12px)] z-20 w-[400px] rounded-lg border border-border-soft bg-surface shadow-lg"
        >
          <div className="border-b border-border-soft p-2">
            <Tabs label="Notifications" items={tabsFor(items)} value={tab} onChange={setTab} />
          </div>

          {/* 📁 *"4 items visible before scroll."* ⚡ A row is ~76px, so the
              height is stated in rows rather than guessed in pixels. */}
          <div className="max-h-[304px] overflow-y-auto overscroll-contain">
            {feed.isPending ? (
              <p className="px-4 py-6 text-center text-xs text-content-subtle">
                Loading your notifications…
              </p>
            ) : feed.isError ? (
              /* ⛔ 📁 `P-A` — **a failed read must never render as an empty
                 result.** A panel that said *"you are all caught up"* when it
                 could not ask would be the worst sentence in this component.
                 ⚡ **`StatedAbsence`, not a sentence of this surface's own** —
                 📁 nine call sites say it the same way, and a tenth wording
                 would be the drift that component exists to stop. */
              <div className="p-3">
                <StatedAbsence subject="your notifications" as="inline" />
              </div>
            ) : groups.length === 0 ? (
              <p
                data-testid="notifications-empty"
                className="px-4 py-6 text-center text-xs text-content-muted"
              >
                {tab === 'all'
                  ? 'Nothing yet. Signora tells you here when something needs you.'
                  : 'Nothing in this group.'}
              </p>
            ) : (
              groups.map((group) => (
                <section key={group.day} aria-label={group.day}>
                  {/* 📁 *"sticky day heads"* */}
                  <h3 className="sticky top-0 z-10 bg-surface-sunken px-4 py-1.5 text-2xs font-semibold uppercase tracking-wide text-content-subtle">
                    {group.day}
                  </h3>
                  <ul>
                    {group.items.map((item) => (
                      <NotificationRow
                        key={item.id}
                        item={item}
                        onOpen={() => markRead.mutate([item.id])}
                      />
                    ))}
                  </ul>
                </section>
              ))
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}

/**
 * 📁 *"Opening the panel does not mark items read; **opening an item does**."*
 *
 * ⛔ **So the row's control is what marks it**, never the panel's mount. ⚡ A
 * panel that marked everything read on open would destroy the only signal the
 * badge carries, and the design forbids it in the same sentence that describes
 * the behaviour.
 */
function NotificationRow({
  item,
  onOpen,
}: {
  readonly item: AppNotification;
  readonly onOpen: () => void;
}) {
  const unread = item.read_at === null;
  return (
    <li className="border-b border-border-soft last:border-b-0">
      <button
        type="button"
        onClick={onOpen}
        className={cn(
          'flex w-full items-start gap-3 px-4 py-3 text-left transition-colors',
          'hover:bg-surface-sunken',
          'focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-2',
          'focus-visible:outline-accent',
        )}
      >
        <span className="min-w-0 flex-1">
          <span className="block text-sm text-content">
            {/* ⛔ **An agent's name, or nothing** — 📁 `C-203`: a person's name
                is not resolvable in this tier, and inventing *"Someone"* would
                be copy the design never wrote. */}
            {item.actor_agent_name === null ? null : (
              <span className="font-semibold">{item.actor_agent_name} </span>
            )}
            {item.summary}
          </span>
          <span className="mt-0.5 block text-2xs text-content-subtle">
            {item.expectation}
          </span>
        </span>
        {/* 📁 *"Unread is a 6px dot on the right, never a coloured row."* */}
        {unread ? (
          <span
            aria-hidden
            data-testid="unread-dot"
            className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent"
          />
        ) : null}
        {/* ♿ The dot is decorative; the state is said. */}
        <span className="sr-only">{unread ? 'Unread' : 'Read'}</span>
      </button>
    </li>
  );
}
