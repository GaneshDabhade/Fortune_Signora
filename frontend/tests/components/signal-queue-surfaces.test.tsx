/**
 * **The Signal Center's three queue-local surfaces** —
 * [TASK-1468](../../../docs/BACKLOG.md) ② ③ ⑦.
 *
 * ⚡ **The properties worth protecting are all about restraint**, which is what
 * the existing [`signal-queue.test.tsx`](signal-queue.test.tsx) already says
 * about this screen: **it must not print a field the platform does not
 * publish, and it must not narrow something the server derives.**
 */
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { QueueEntry, SignalTypeName } from '@/lib/api/types';

const triage = vi.hoisted(() => vi.fn());
const resolveMutate = vi.hoisted(() => vi.fn());
const catalog = vi.hoisted(() => vi.fn());
const identities = vi.hoisted(() => vi.fn());

vi.mock('@/lib/query/hooks/triage', () => ({
  useWorkspaceTriage: triage,
  useResolveSignal: () => ({ mutate: resolveMutate, isPending: false }),
}));
vi.mock('@/lib/query/hooks', () => ({
  useSignalCatalog: catalog,
  useAccountIdentities: identities,
}));
vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: () => ({ activeWorkspace: { id: 'ws-1' } }),
}));

import { SignalQueue } from '@/app/(app)/signals/signal-queue';

function entry(id: string, type: string): QueueEntry {
  return {
    signal_id: id,
    signal_type: type,
    entity_id: 'acc-1',
    rationale: 'Two buyers raised list price on the renewal thread.',
    state: 'open',
    resolution: null,
  };
}

const TYPES: SignalTypeName[] = [
  { key: 'pricing_objection', title: 'Pricing objection', why_it_matters: 'x' },
  { key: 'champion_left', title: 'Champion left', why_it_matters: 'y' },
];

/** ⚡ Three of one type and one of another, so a filter has something to do. */
const PAGE = [
  entry('s1', 'pricing_objection'),
  entry('s2', 'pricing_objection'),
  entry('s3', 'pricing_objection'),
  entry('s4', 'champion_left'),
];

beforeEach(() => {
  resolveMutate.mockClear();
  catalog.mockReturnValue({
    data: new Map(TYPES.map((t) => [t.key, t])),
    isError: false,
    isPending: false,
  });
  identities.mockReturnValue({ data: new Map([['acc-1', { account_id: 'acc-1', name: 'Vantage' }]]) });
  triage.mockReturnValue({ data: { items: PAGE }, isPending: false, isError: false });
});

describe('⑦ the counts header says the one thing it can support', () => {
  it('✅ it counts what needs review', () => {
    render(<SignalQueue />);

    expect(screen.getByTestId('queue-counts')).toHaveTextContent('4 need review');
  });

  /**
   * 🔴 **The assertion that keeps a later change from filling the design's
   * shape with invention.**
   *
   * 📁 The design draws *"14 need review · **6 assigned to you** · **41 this
   * week**"*. ⛔ **`QueueEntry` has no assignee and no timestamp** — so both
   * would be numbers this screen made up, and 📁 [§20c](../../../CLAUDE.md)
   * forbids exactly that.
   */
  it('⛔ and never the two the contract cannot support', () => {
    render(<SignalQueue />);

    const counts = screen.getByTestId('queue-counts');
    expect(counts).not.toHaveTextContent(/assigned to you/i);
    expect(counts).not.toHaveTextContent(/this week/i);
  });
});

describe('② the filter narrows by type, and only by type', () => {
  it('✅ a chip per type, counted from the unfiltered page', () => {
    render(<SignalQueue />);

    const filters = screen.getByTestId('signal-filters');
    expect(within(filters).getByRole('button', { name: /Pricing objection/ })).toHaveTextContent('3');
    expect(within(filters).getByRole('button', { name: /Champion left/ })).toHaveTextContent('1');
  });

  it('✅ choosing one narrows the list and says how far', async () => {
    render(<SignalQueue />);

    await userEvent.click(screen.getByRole('button', { name: /Champion left/ }));

    // 📁 The design's *"14 of 22 shown"*, and ⚡ **both numbers are counted.**
    expect(screen.getByText('1 of 4 shown')).toBeInTheDocument();
  });

  /**
   * ⛔ **The chip that narrows must not delete the way back.**
   *
   * ⚠️ **Building the chips from the FILTERED list is the obvious mistake**:
   * choosing one type removes every other chip, and the control that narrows
   * becomes the control that traps.
   */
  it('🔴 every chip survives a narrowing, so the reader can change their mind', async () => {
    render(<SignalQueue />);

    await userEvent.click(screen.getByRole('button', { name: /Champion left/ }));

    const filters = screen.getByTestId('signal-filters');
    expect(within(filters).getByRole('button', { name: /Pricing objection/ })).toBeInTheDocument();
  });

  it('♿ a chosen chip is pressed, not merely coloured', async () => {
    render(<SignalQueue />);
    const chip = screen.getByRole('button', { name: /Champion left/ });

    expect(chip).toHaveAttribute('aria-pressed', 'false');
    await userEvent.click(chip);
    expect(chip).toHaveAttribute('aria-pressed', 'true');
  });

  it('✅ Clear restores the whole page in one action', async () => {
    render(<SignalQueue />);
    await userEvent.click(screen.getByRole('button', { name: /Champion left/ }));

    await userEvent.click(screen.getByRole('button', { name: 'Clear' }));

    expect(screen.queryByText(/of 4 shown/)).not.toBeInTheDocument();
  });

  /**
   * 🔴 **An empty selection is *not narrowed*, never *nothing*.**
   *
   * 📁 The same rule [`working-list.ts`](../../lib/views/working-list.ts)
   * applies to `all`: **the absence of a narrowing is not a narrowing to
   * zero.** ⛔ **Getting this backwards empties the screen on first paint.**
   */
  it('⛔ no chip chosen shows everything', () => {
    render(<SignalQueue />);

    expect(screen.getAllByRole('checkbox')).toHaveLength(PAGE.length);
  });
});

describe('③ bulk selection acts on what the reader can see', () => {
  it('✅ selecting shows the bar and the count', async () => {
    render(<SignalQueue />);

    await userEvent.click(screen.getAllByRole('checkbox')[0]!);

    expect(screen.getByTestId('bulk-bar')).toHaveTextContent('1 selected');
  });

  it('♿ the row control names the signal, never "select"', () => {
    render(<SignalQueue />);

    // ⚡ **Somebody hearing the row hears what they are about to act on.**
    expect(screen.getByRole('checkbox', { name: 'Select Champion left' })).toBeInTheDocument();
  });

  it('✅ one decision is recorded per selected signal', async () => {
    render(<SignalQueue />);
    await userEvent.click(screen.getAllByRole('checkbox')[0]!);
    await userEvent.click(screen.getAllByRole('checkbox')[1]!);

    await userEvent.click(screen.getByRole('button', { name: 'Mark actioned' }));

    expect(resolveMutate).toHaveBeenCalledTimes(2);
    expect(resolveMutate).toHaveBeenCalledWith({ signalId: 's1', outcome: { kind: 'actioned' } });
  });

  /**
   * 🔴 **The defect this clears exists to prevent.**
   *
   * ⚠️ **A selection that survives a filter says *"3 selected"* while two of
   * them are off screen** — and the person presses the button believing it
   * means the three in front of them.
   */
  it('🔴 narrowing the list clears the selection rather than acting off screen', async () => {
    render(<SignalQueue />);
    await userEvent.click(screen.getAllByRole('checkbox')[0]!);
    expect(screen.getByTestId('bulk-bar')).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: /Champion left/ }));

    expect(screen.queryByTestId('bulk-bar')).not.toBeInTheDocument();
  });

  /**
   * ⛔ **Only the outcome the union lets a bulk control construct honestly.**
   *
   * 📁 `ResolveOutcome` makes `dismissed` carry a reason and `snoozed` carry an
   * `until`; `assigned` carries a person. ⚡ **A bulk control for any of the
   * three would have to invent the thing that makes it citable.**
   */
  it('⛔ no bulk dismiss, snooze or assign', async () => {
    render(<SignalQueue />);
    await userEvent.click(screen.getAllByRole('checkbox')[0]!);

    const bar = screen.getByTestId('bulk-bar');
    expect(within(bar).queryByRole('button', { name: /dismiss/i })).not.toBeInTheDocument();
    expect(within(bar).queryByRole('button', { name: /snooze/i })).not.toBeInTheDocument();
    expect(within(bar).queryByRole('button', { name: /assign/i })).not.toBeInTheDocument();
  });
});
