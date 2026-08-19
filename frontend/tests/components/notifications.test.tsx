/**
 * **The top bar's notification panel** — [TASK-495](../../../docs/BACKLOG.md)
 * slice ⓑ, against 📁 `Fortune Signora App Shell.dc.html` §10.
 */
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { AppNotification } from '@/lib/api/types';

const unread = vi.hoisted(() => vi.fn());
const feed = vi.hoisted(() => vi.fn());
const markRead = vi.hoisted(() => vi.fn());

vi.mock('@/lib/query/hooks/notifications', () => ({
  useUnreadNotifications: unread,
  useNotifications: feed,
  useMarkNotificationsRead: () => ({ mutate: markRead, isPending: false }),
}));
vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: () => ({ activeWorkspace: { id: 'w1', name: 'Northwind' } }),
}));

const { Notifications, groupByDay } = await import('@/components/shell/notifications');

function item(over: Partial<AppNotification> = {}): AppNotification {
  return {
    id: over.id ?? 'n1',
    category: 'needs_you',
    actor_kind: 'agent',
    actor_person_id: null,
    actor_agent_name: 'Renewal risk sweep',
    subject_kind: 'account',
    subject_id: 'a1',
    summary: 'finished researching Vantage Logistics',
    expectation: 'Review what it found',
    occurred_at: new Date().toISOString(),
    read_at: null,
    ...over,
  };
}

beforeEach(() => {
  unread.mockReturnValue({ data: { unread: 0, capped: false, cap: 99 } });
  feed.mockReturnValue({ data: { notifications: [] }, isPending: false, isError: false });
  markRead.mockReset();
});

describe('📁 "count badge caps at 99+"', () => {
  it('says the count in the control name, not only in a dot', () => {
    unread.mockReturnValue({ data: { unread: 3, capped: false, cap: 99 } });

    render(<Notifications />);

    // ♿ ⛔ **A control labelled *Notifications* tells a screen-reader user
    // nothing about whether opening it is worth their time.**
    expect(screen.getByRole('button', { name: 'Notifications, 3 unread' })).toBeVisible();
  });

  it('🔴 caps at 99+, which is the shell law the slot was written for', () => {
    unread.mockReturnValue({ data: { unread: 412, capped: true, cap: 99 } });

    render(<Notifications />);

    expect(screen.getByTestId('notification-badge')).toHaveTextContent('99+');
  });

  it('⛔ and draws no badge at all at zero', () => {
    render(<Notifications />);

    expect(screen.queryByTestId('notification-badge')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^Notifications/ })).toBeVisible();
  });
});

describe('📁 "opens a 400px panel, not a page"', () => {
  it('⛔ reads nothing until it is opened', () => {
    render(<Notifications />);

    // ⚡ **The bell is on every screen and the panel is opened rarely** — the
    // feed's `enabled` is the open state, so a bell nobody clicks costs a count.
    expect(feed).toHaveBeenCalledWith('w1', false);
  });

  it('opens on click and asks for the feed then', async () => {
    render(<Notifications />);

    await userEvent.click(screen.getByRole('button', { name: /^Notifications/ }));

    expect(screen.getByTestId('notification-panel')).toBeVisible();
    expect(feed).toHaveBeenLastCalledWith('w1', true);
  });

  /**
   * 📁 §*Multi-workspace* — *"when a user has more than one workspace, search,
   * notifications and the assistant all carry the workspace name in their
   * header. **Ambiguity here is what causes the wrong customer to be
   * discussed**."*
   */
  it('🔴 names the workspace, because the wrong one is the expensive mistake', async () => {
    render(<Notifications />);

    await userEvent.click(screen.getByRole('button', { name: /^Notifications/ }));

    expect(screen.getByRole('dialog', { name: 'Notifications — Northwind' })).toBeVisible();
  });
});

describe('📁 the three tabs, and two are the domain’s own categories', () => {
  it('filters to the category the tab names', async () => {
    feed.mockReturnValue({
      data: {
        notifications: [
          item({ id: 'a', category: 'needs_you', summary: 'needs approval' }),
          item({ id: 'b', category: 'mention', summary: 'mentioned you' }),
        ],
      },
      isPending: false,
      isError: false,
    });

    render(<Notifications />);
    await userEvent.click(screen.getByRole('button', { name: /^Notifications/ }));

    // The first tab is the design's first, and it is selected on open.
    expect(screen.getByText(/needs approval/)).toBeVisible();
    expect(screen.queryByText(/mentioned you/)).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole('tab', { name: 'Mentions' }));
    expect(screen.getByText(/mentioned you/)).toBeVisible();
    expect(screen.queryByText(/needs approval/)).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole('tab', { name: 'All' }));
    expect(screen.getByText(/needs approval/)).toBeVisible();
    expect(screen.getByText(/mentioned you/)).toBeVisible();
  });
});

describe('📁 the first tab carries its count, and only the first', () => {
  it('reads "Needs you · 2" when two are blocking and unread', async () => {
    feed.mockReturnValue({
      data: {
        notifications: [
          item({ id: 'a', category: 'needs_you', read_at: null }),
          item({ id: 'b', category: 'needs_you', read_at: null }),
          // ⛔ Read, so it is not blocking anybody any more.
          item({ id: 'c', category: 'needs_you', read_at: new Date().toISOString() }),
          // ⛔ A mention is not this tab's.
          item({ id: 'd', category: 'mention', read_at: null }),
        ],
      },
      isPending: false,
      isError: false,
    });

    render(<Notifications />);
    await userEvent.click(screen.getByRole('button', { name: /^Notifications/ }));

    expect(screen.getByRole('tab', { name: 'Needs you · 2' })).toBeVisible();
    // ⚡ **A count on *All* would be the length of a list already visible.**
    expect(screen.getByRole('tab', { name: 'All' })).toBeVisible();
    expect(screen.getByRole('tab', { name: 'Mentions' })).toBeVisible();
  });

  it('⛔ and drops the count entirely at zero, rather than showing "· 0"', async () => {
    feed.mockReturnValue({
      data: { notifications: [item({ category: 'mention' })] },
      isPending: false,
      isError: false,
    });

    render(<Notifications />);
    await userEvent.click(screen.getByRole('button', { name: /^Notifications/ }));

    expect(screen.getByRole('tab', { name: 'Needs you' })).toBeVisible();
  });
});

describe('🔴 "opening the panel does not mark items read; opening an item does"', () => {
  it('⛔ marks nothing when the panel opens', async () => {
    feed.mockReturnValue({
      data: { notifications: [item()] },
      isPending: false,
      isError: false,
    });

    render(<Notifications />);
    await userEvent.click(screen.getByRole('button', { name: /^Notifications/ }));

    // ⚡ **A panel that marked everything read on open would destroy the only
    // signal the badge carries**, and the design forbids it in the same
    // sentence that describes the behaviour.
    expect(markRead).not.toHaveBeenCalled();
  });

  it('✅ marks exactly the item that was opened, and no others', async () => {
    feed.mockReturnValue({
      data: { notifications: [item({ id: 'a' }), item({ id: 'b', summary: 'second thing' })] },
      isPending: false,
      isError: false,
    });

    render(<Notifications />);
    await userEvent.click(screen.getByRole('button', { name: /^Notifications/ }));
    await userEvent.click(screen.getByText(/second thing/));

    await waitFor(() => expect(markRead).toHaveBeenCalledWith(['b']));
    expect(markRead).toHaveBeenCalledTimes(1);
  });
});

describe('📁 "unread is a 6px dot on the right, never a coloured row"', () => {
  it('draws the dot from the item’s own read time, not from the badge', async () => {
    feed.mockReturnValue({
      data: {
        notifications: [
          item({ id: 'a', read_at: null }),
          item({ id: 'b', read_at: new Date().toISOString(), summary: 'already read' }),
        ],
      },
      isPending: false,
      isError: false,
    });

    render(<Notifications />);
    await userEvent.click(screen.getByRole('button', { name: /^Notifications/ }));

    // ⛔ **One dot, not two** — the badge count says how many without saying
    // which, and a panel that read the count would mark every row unread.
    expect(screen.getAllByTestId('unread-dot')).toHaveLength(1);
    // ♿ The dot is decorative; the state is said.
    expect(screen.getAllByText('Unread')).toHaveLength(1);
    expect(screen.getAllByText('Read')).toHaveLength(1);
  });
});

describe('⛔ a failed read is never an empty result', () => {
  it('🔴 says the read failed rather than "you are all caught up"', async () => {
    feed.mockReturnValue({ data: undefined, isPending: false, isError: true });

    render(<Notifications />);
    await userEvent.click(screen.getByRole('button', { name: /^Notifications/ }));

    // 📁 `P-A`. ⚡ And through `StatedAbsence`, so the wording is the ninth
    // call site's rather than this surface's tenth invention.
    expect(screen.getByText(/could not load your notifications/i)).toBeVisible();
    expect(screen.queryByTestId('notifications-empty')).not.toBeInTheDocument();
  });

  it('✅ and an empty feed says so in its own words', async () => {
    render(<Notifications />);
    await userEvent.click(screen.getByRole('button', { name: /^Notifications/ }));
    await userEvent.click(screen.getByRole('tab', { name: 'All' }));

    expect(screen.getByTestId('notifications-empty')).toBeVisible();
  });
});

describe('📁 "grouped by day with sticky day heads"', () => {
  const TODAY = new Date('2026-08-19T12:00:00Z');

  it('names today and yesterday rather than dating them', () => {
    const groups = groupByDay(
      [
        item({ id: 'a', occurred_at: '2026-08-19T09:12:00Z' }),
        item({ id: 'b', occurred_at: '2026-08-18T17:40:00Z' }),
        item({ id: 'c', occurred_at: '2026-08-11T08:00:00Z' }),
      ],
      TODAY,
    );

    // ⚡ **A date beside a time a person can still remember reads as older
    // than it is.**
    expect(groups.map((group) => group.day)).toEqual(['Today', 'Yesterday', expect.any(String)]);
    expect(groups[2]!.day).not.toBe('Today');
  });

  it('⛔ never reorders — the groups follow the feed, which is newest first', () => {
    // 📁 *"the panel never reorders while open"*, and a second sort here is
    // the only thing that could break it.
    const groups = groupByDay(
      [
        item({ id: 'a', occurred_at: '2026-08-18T09:00:00Z' }),
        item({ id: 'b', occurred_at: '2026-08-19T09:00:00Z' }),
      ],
      TODAY,
    );

    expect(groups.map((group) => group.day)).toEqual(['Yesterday', 'Today']);
  });

  it('keeps consecutive items of one day in one group', async () => {
    feed.mockReturnValue({
      data: {
        notifications: [
          item({ id: 'a' }),
          item({ id: 'b', summary: 'second thing' }),
        ],
      },
      isPending: false,
      isError: false,
    });

    render(<Notifications />);
    await userEvent.click(screen.getByRole('button', { name: /^Notifications/ }));

    const today = screen.getByRole('region', { name: 'Today' });
    expect(within(today).getAllByRole('listitem')).toHaveLength(2);
  });
});

describe('♿ Escape closes it and returns focus to the bell', () => {
  it('🔴 the return is the half that gets dropped', async () => {
    render(<Notifications />);
    const bell = screen.getByRole('button', { name: /^Notifications/ });
    await userEvent.click(bell);
    expect(screen.getByTestId('notification-panel')).toBeVisible();

    await userEvent.keyboard('{Escape}');

    expect(screen.queryByTestId('notification-panel')).not.toBeInTheDocument();
    // ⛔ **Without this a keyboard user who closes the panel is returned to the
    // top of the document** — they lose their place as the price of dismissing.
    expect(bell).toHaveFocus();
  });
});
