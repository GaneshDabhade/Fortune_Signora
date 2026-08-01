/**
 * Moving through the list rather than back to it.
 *
 * The morning was twenty-four navigations for twelve accounts, because the
 * brief's only exit pointed backwards and every return scrolled the list to
 * the top (R10-01). These assert the rules that keep the replacement honest.
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { AccountSequence } from '@/components/intelligence/sequence';
import type { AccountAttention, AccountIdentity } from '@/lib/api/types';

const push = vi.hoisted(() => vi.fn());
vi.mock('next/navigation', () => ({ useRouter: () => ({ push }) }));

function account(id: string): AccountAttention {
  return {
    id: `opp-${id}`,
    account_id: id,
    score: 50,
    trend: 'rising',
    score_change: 5,
    signal_type: 'active_evaluation',
    posture: 'neutral' as const,
    contested: false,
    evidence: 'current',
    stage: 'tracking',
    owner_id: null,
    opened_at: '2026-07-01T00:00:00Z',
  };
}

const RANKED = [account('a'), account('b'), account('c')];

const NAMES = new Map<string, AccountIdentity>(
  [
    ['a', 'NVIDIA Corporation'],
    ['b', 'Databricks, Inc.'],
    ['c', 'Snowflake Inc.'],
  ].map(([id, name]) => [
    id!,
    {
      account_id: id!,
      name: name!,
      agreement: 'agreed',
      source_count: 2,
      source: 'coresignal',
      observed_at: '2026-07-01T00:00:00Z',
    },
  ]),
);

beforeEach(() => push.mockReset());

describe('the brief offers where to go next', () => {
  it('names the next account rather than pointing at it', () => {
    // "Next: Snowflake Inc." tells a reader where they are going; "Next →"
    // asks them to find out by arriving.
    render(<AccountSequence accountId="b" accounts={RANKED} identities={NAMES} />);

    expect(screen.getByRole('link', { name: /Snowflake Inc\./ })).toHaveAttribute(
      'href',
      '/accounts/c',
    );
    expect(screen.getByRole('link', { name: /NVIDIA Corporation/ })).toHaveAttribute(
      'href',
      '/accounts/a',
    );
  });

  it('says where you are in the sequence', () => {
    render(<AccountSequence accountId="b" accounts={RANKED} identities={NAMES} />);

    expect(screen.getByText('2 of 3')).toBeInTheDocument();
  });

  it('draws no dead control at either end', () => {
    // A disabled control teaches a reader that controls here can be dead.
    render(<AccountSequence accountId="a" accounts={RANKED} identities={NAMES} />);

    expect(screen.queryByRole('link', { name: /NVIDIA/ })).not.toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Databricks/ })).toBeInTheDocument();
  });

  it('says an account has left the list rather than inventing a place', () => {
    // Dismiss an account and it is no longer open work, so it leaves the list
    // — but its brief survives (D27).
    render(<AccountSequence accountId="gone" accounts={RANKED} identities={NAMES} />);

    expect(screen.getByText(/No longer on your list/)).toBeInTheDocument();
  });

  it('renders nothing at all before the list arrives', () => {
    const { container } = render(
      <AccountSequence accountId="b" accounts={[]} identities={undefined} />,
    );

    expect(container).toBeEmptyDOMElement();
  });

  it('follows the ranking, so next means next most pressing', () => {
    // The order is the attention list's, not alphabetical and not by id.
    render(<AccountSequence accountId="a" accounts={RANKED} identities={NAMES} />);

    expect(screen.getByRole('link', { name: /Databricks/ })).toHaveAttribute(
      'href',
      '/accounts/b',
    );
  });
});

describe('the keyboard path', () => {
  it('moves forward on j and back on k', async () => {
    const user = userEvent.setup();
    render(<AccountSequence accountId="b" accounts={RANKED} identities={NAMES} />);

    await user.keyboard('j');
    expect(push).toHaveBeenCalledWith('/accounts/c');

    await user.keyboard('k');
    expect(push).toHaveBeenCalledWith('/accounts/a');
  });

  it('does nothing at the end of the sequence', async () => {
    const user = userEvent.setup();
    render(<AccountSequence accountId="c" accounts={RANKED} identities={NAMES} />);

    await user.keyboard('j');

    expect(push).not.toHaveBeenCalled();
  });

  it('never fires while somebody is typing', async () => {
    // **A reason field containing `jkjk` instead of a sentence would be the
    // product eating the customer's words**, and the workflow reason is the
    // one piece of text in Signora nothing can reproduce if it is lost.
    const user = userEvent.setup();
    render(
      <>
        <input aria-label="Why are you taking this on?" />
        <AccountSequence accountId="b" accounts={RANKED} identities={NAMES} />
      </>,
    );

    await user.click(screen.getByLabelText('Why are you taking this on?'));
    await user.keyboard('jk');

    expect(push).not.toHaveBeenCalled();
    expect(screen.getByLabelText('Why are you taking this on?')).toHaveValue('jk');
  });

  it('never fires while a dialog is open', async () => {
    // The decision dialog is a native <dialog>; while one is open the reader
    // is answering a question, not navigating.
    const user = userEvent.setup();
    render(
      <>
        <dialog open>Recording a decision</dialog>
        <AccountSequence accountId="b" accounts={RANKED} identities={NAMES} />
      </>,
    );

    await user.keyboard('j');

    expect(push).not.toHaveBeenCalled();
  });

  it('leaves browser and OS shortcuts alone', async () => {
    const user = userEvent.setup();
    render(<AccountSequence accountId="b" accounts={RANKED} identities={NAMES} />);

    await user.keyboard('{Meta>}j{/Meta}');

    expect(push).not.toHaveBeenCalled();
  });
});
