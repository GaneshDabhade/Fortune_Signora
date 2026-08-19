/**
 * **The top bar's notification panel** — [TASK-495](../../../docs/BACKLOG.md)
 * slice ⓑ, against 📁 `Fortune Signora App Shell.dc.html` §10.
 */
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { AppNotification } from '@/lib/api/types';

const feed = vi.hoisted(() => vi.fn());
const markRead = vi.hoisted(() => vi.fn());
/** ⚡ **What the identity surface answers**, keyed by subject id. */
const names = vi.hoisted(() => new Map<string, string>());

vi.mock('@/lib/query/hooks/notifications', () => ({
  useNotifications: feed,
  useMarkNotificationsRead: () => ({ mutate: markRead, isPending: false }),
  /**
   * ⚡ **The real one, not a stub** — 📁 it is four lines of pure arithmetic over
   * the feed, and **a mocked count would let the badge and the panel disagree**,
   * which is exactly the defect deriving it from one read removed.
   */
  unreadCount: (data: { notifications: AppNotification[] } | undefined) =>
    (data?.notifications ?? []).filter((one) => one.read_at === null).length,
}));
vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: () => ({ activeWorkspace: { id: 'w1', name: 'Northwind' } }),
}));
/**
 * ⚡ **The identity surface, which names the record.** ⛔ Mocked at the hook and
 * not at `apiRequest`: 📁 the panel's claim is *"it states which record"*, and
 * where the name came from is `useAccountIdentities`'s own test's question.
 */
vi.mock('@/lib/query/hooks', () => ({
  useAccountIdentities: (_workspaceId: string | null, ids: string[]) => ({
    data: new Map(ids.map((id) => [id, { account_id: id, name: names.get(id) ?? null }])),
  }),
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

/** ⚡ **`n` unread items**, because the badge is now counted from the feed. */
function unreadItems(count: number): AppNotification[] {
  return Array.from({ length: count }, (_, index) => item({ id: `u${index}`, read_at: null }));
}

function loaded(notifications: AppNotification[]) {
  return { data: { notifications }, isPending: false, isError: false };
}

beforeEach(() => {
  feed.mockReturnValue(loaded([]));
  markRead.mockReset();
  names.clear();
});

describe('📁 "count badge caps at 99+"', () => {
  it('says the count in the control name, not only in a dot', () => {
    feed.mockReturnValue(loaded(unreadItems(3)));

    render(<Notifications />);

    // ♿ ⛔ **A control labelled *Notifications* tells a screen-reader user
    // nothing about whether opening it is worth their time.**
    expect(screen.getByRole('button', { name: 'Notifications, 3 unread' })).toBeVisible();
  });

  it('🔴 caps at 99+, which is the shell law the slot was written for', () => {
    feed.mockReturnValue(loaded(unreadItems(412)));

    render(<Notifications />);

    expect(screen.getByTestId('notification-badge')).toHaveTextContent('99+');
  });

  it('⛔ and draws no badge at all at zero', () => {
    // ⚡ **Items, but every one of them read** — ⛔ *no notifications* and *none
    // unread* are different facts, and the badge answers the second.
    feed.mockReturnValue(loaded([item({ read_at: new Date().toISOString() })]));

    render(<Notifications />);

    expect(screen.queryByTestId('notification-badge')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^Notifications/ })).toBeVisible();
  });
});

describe('📁 "opens a 400px panel, not a page"', () => {
  /**
   * 🔴 **This asserted the opposite until the journey was written.** ⚠️ It read
   * *"reads nothing until it is opened"* and checked `feed('w1', false)` — ⛔
   * **the badge was a second read, and that read issued a `GET` to a `POST`
   * route and took a `405` on every authenticated screen.**
   *
   * ✅ **One read now serves both**, 📁 because slice ⓐ put `read_at` in the
   * feed. ⚡ **So the assertion is that opening the panel asks for nothing
   * new** — the panel renders what the bell already counted.
   */
  it('⛔ opening the panel issues no second read — the bell already has it', async () => {
    feed.mockReturnValue(loaded([item()]));

    render(<Notifications />);
    expect(feed).toHaveBeenCalledWith('w1');
    const before = feed.mock.calls.length;

    await userEvent.click(screen.getByRole('button', { name: /^Notifications/ }));

    expect(screen.getByTestId('notification-panel')).toBeVisible();
    // ⚡ **Re-rendered, so called again — with the same argument.** ⛔ There is
    // no open flag, which is what makes a second request impossible.
    expect(feed.mock.calls.length).toBeGreaterThan(before);
    for (const call of feed.mock.calls) expect(call).toEqual(['w1']);
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

describe('📁 "agent and AI notifications are marked with the intelligence hue"', () => {
  /**
   * 🔴 **The design's reason is in the same sentence** — *"so a generated nudge
   * never reads as a colleague's request"* — ⛔ and without a mark the two are
   * the same object.
   */
  it('marks an agent, and leaves a colleague unmarked', async () => {
    feed.mockReturnValue(
      loaded([
        item({ id: 'a', actor_kind: 'agent', actor_agent_name: 'Research' }),
        item({
          id: 'b',
          actor_kind: 'person',
          actor_agent_name: null,
          actor_person_id: 'p1',
          summary: 'asked you to look at this',
        }),
      ]),
    );

    render(<Notifications />);
    await userEvent.click(screen.getByRole('button', { name: /^Notifications/ }));

    // ⛔ **One mark for two items** — ⚡ a mark on both would say nothing, which
    // is the failure the criterion names.
    expect(screen.getAllByTestId('agent-mark')).toHaveLength(1);
  });
});

describe('📁 "states who or what acted, on which record, and what is expected"', () => {
  /**
   * 🔴 **The middle clause is the one that was missing.** ⛔ The row said what
   * acted and what was expected and **never named the record** — 📁 the
   * notification carries subject *identity* (*events carry identity; ports carry
   * payload*), so the shell resolves the name the way every other surface does.
   */
  it('names the record beside the expectation', async () => {
    names.set('a1', 'Vantage Logistics');
    feed.mockReturnValue(loaded([item({ subject_kind: 'account', subject_id: 'a1' })]));

    render(<Notifications />);
    await userEvent.click(screen.getByRole('button', { name: /^Notifications/ }));

    expect(screen.getByTestId('notification-record')).toHaveTextContent('Vantage Logistics');
    expect(screen.getByText(/Review what it found/)).toBeVisible();
  });

  /**
   * ⛔ **Dropped, never guessed.** ⚡ *"Unnamed account · Review what it found"*
   * tells a reader less than the expectation on its own, and 📁 the Playground
   * holds accounts no source has named.
   */
  it('⛔ says nothing about the record when nothing can name it', async () => {
    feed.mockReturnValue(loaded([item({ subject_kind: 'account', subject_id: 'a1' })]));

    render(<Notifications />);
    await userEvent.click(screen.getByRole('button', { name: /^Notifications/ }));

    expect(screen.queryByTestId('notification-record')).not.toBeInTheDocument();
    expect(screen.getByText(/Review what it found/)).toBeVisible();
  });

  /**
   * 🔴 📁 **`navigate-to-context`** — [TASK-480](../../../docs/BACKLOG.md)'s own
   * list of what this capability is, and the one item of it the panel had not
   * built.
   */
  it('✅ opening an item goes to the record, and closes the panel behind it', async () => {
    names.set('a1', 'Vantage Logistics');
    feed.mockReturnValue(loaded([item({ subject_kind: 'account', subject_id: 'a1' })]));

    render(<Notifications />);
    await userEvent.click(screen.getByRole('button', { name: /^Notifications/ }));

    // ⛔ **A link, not a `router.push`** — ⚡ so it opens in a new tab and needs
    // no router for the shell to render, which is what the first draft cost.
    const row = screen.getByRole('link');
    expect(row).toHaveAttribute('href', '/accounts/a1');

    await userEvent.click(row);
    await waitFor(() => expect(markRead).toHaveBeenCalled());
    // ⚡ 📁 *"A popover keeps the user in place"* — ⛔ and a popover left open
    // over the page it just took somebody to is not keeping them anywhere.
    expect(screen.queryByTestId('notification-panel')).not.toBeInTheDocument();
  });

  /**
   * ⛔ **A subject with no route marks read and stays put.** ⚡ **A control that
   * navigates for one row and not the next is worse than one that never
   * navigates**, so the row says which it is by whether it names a record.
   */
  it('⛔ a subject the shell cannot open is a button, not a link', async () => {
    feed.mockReturnValue(loaded([item({ subject_kind: 'opportunity', subject_id: 'o1' })]));

    render(<Notifications />);
    await userEvent.click(screen.getByRole('button', { name: /^Notifications/ }));

    expect(screen.queryByRole('link')).not.toBeInTheDocument();
    await userEvent.click(screen.getByText(/Review what it found/));
    await waitFor(() => expect(markRead).toHaveBeenCalledWith([expect.any(String)]));
  });
});

describe('📁 the panel\'s own head — "Notifications", the count, and "Mark all read"', () => {
  /**
   * 🔴 **Not the same act as opening an item.** 📁 *"Opening the panel does not
   * mark items read; opening an item does"* governs what happens **by itself**
   * — ⚡ this is somebody deciding, which is why it is a control.
   */
  it('marks every unread item, across tabs, in one call', async () => {
    feed.mockReturnValue(
      loaded([
        item({ id: 'a', category: 'needs_you', read_at: null }),
        item({ id: 'b', category: 'mention', read_at: null }),
        item({ id: 'c', category: 'needs_you', read_at: new Date().toISOString() }),
      ]),
    );

    render(<Notifications />);
    await userEvent.click(screen.getByRole('button', { name: /^Notifications/ }));
    await userEvent.click(screen.getByRole('button', { name: 'Mark all read' }));

    // ⛔ **`a` and `b`, and never `c`** — ⚡ the *Needs you* tab is showing, and
    // a control in the panel's head is not the tab's.
    expect(markRead).toHaveBeenCalledWith(['a', 'b']);
  });

  it('⛔ and is disabled when there is nothing to mark', async () => {
    feed.mockReturnValue(loaded([item({ read_at: new Date().toISOString() })]));

    render(<Notifications />);
    await userEvent.click(screen.getByRole('button', { name: /^Notifications/ }));

    expect(screen.getByRole('button', { name: 'Mark all read' })).toBeDisabled();
  });

  /**
   * ⚠️ 📁 **The design draws a *"Notification settings"* footer and it is
   * deliberately absent.** ⛔ It opens the *Notification Center*, **Workflow
   * 17's screen, which does not exist** — and a link to an unbuilt screen is
   * the false-affordance class this slice has refused twice already.
   */
  it('⛔ offers no link to a screen that does not exist', async () => {
    render(<Notifications />);
    await userEvent.click(screen.getByRole('button', { name: /^Notifications/ }));

    expect(screen.queryByText(/Notification settings/i)).not.toBeInTheDocument();
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
