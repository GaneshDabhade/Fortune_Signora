/**
 * Accounts you have decided about, as a customer experiences them — `R4-04`.
 *
 * The tests that matter are about **safety and restraint**: whether dismissing
 * something is undoable, whether the section stays out of the way of a reader
 * who never dismisses, and whether it gives back the customer's own words
 * rather than a category the product invented for them.
 */
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import { DecidedAccounts } from '@/components/intelligence/decided';
import type { AccountIdentity, DecidedAccount } from '@/lib/api/types';

const VIEWER = '00000000-0000-4000-8000-000000000001';

function decided(overrides: Partial<DecidedAccount> = {}): DecidedAccount {
  return {
    account_id: '11111111-1111-4111-8111-111111111111',
    opportunity_id: '22222222-2222-4222-8222-222222222222',
    stage: 'dismissed',
    reason: 'They standardised on a competitor last quarter.',
    owner_id: VIEWER,
    decided_at: '2026-07-30T09:00:00Z',
    ...overrides,
  };
}

const IDENTITIES = new Map<string, AccountIdentity>([
  [
    '11111111-1111-4111-8111-111111111111',
    {
      account_id: '11111111-1111-4111-8111-111111111111',
      name: 'Databricks, Inc.',
      source: 'apollo',
      source_count: 1,
      agreement: 'agreed',
      observed_at: '2026-07-01T00:00:00Z',
      last_observed_at: '2026-07-28T00:00:00Z',
    },
  ],
]);

function section(accounts: DecidedAccount[], identities = IDENTITIES) {
  return render(
    <DecidedAccounts accounts={accounts} identities={identities} viewerId={VIEWER} />,
  );
}

describe('a reader who has decided nothing', () => {
  it('sees nothing at all — not an empty state', () => {
    const { container } = section([]);

    // **Absent, not empty.** D6 rejected a filter because a control that
    // always shows the same thing teaches people to ignore controls. A reader
    // who never dismisses should never learn this exists.
    expect(container).toBeEmptyDOMElement();
  });
});

describe('the section stays out of the way', () => {
  it('is closed until asked', () => {
    section([decided()]);

    expect(screen.getByRole('button', { expanded: false })).toBeVisible();
    expect(screen.queryByText(/Databricks/)).toBeNull();
  });

  it('says how many there are before it is opened', () => {
    section([decided(), decided({ opportunity_id: 'b', account_id: 'b' })]);

    expect(
      screen.getByRole('button', { name: /2 accounts you have decided about/i }),
    ).toBeVisible();
  });

  it('counts one account in the singular', () => {
    section([decided()]);

    expect(
      screen.getByRole('button', { name: /^1 account you have decided about$/i }),
    ).toBeVisible();
  });

  it('opens on click and announces that it did', async () => {
    section([decided()]);

    await userEvent.click(screen.getByRole('button'));

    expect(screen.getByRole('button', { expanded: true })).toBeVisible();
    expect(screen.getByText('Databricks, Inc.')).toBeVisible();
  });
});

describe('what a row says', () => {
  it('gives back the words the person typed', async () => {
    section([decided()]);
    await userEvent.click(screen.getByRole('button'));

    // The only place in the product that shows a customer their own judgement
    // back. A summary of it would be the product editing them.
    expect(
      screen.getByText('They standardised on a competitor last quarter.'),
    ).toBeVisible();
  });

  it('leads back to the account, by name', async () => {
    section([decided()]);
    await userEvent.click(screen.getByRole('button'));

    const link = screen.getByRole('link', { name: /Databricks/ });
    expect(link).toHaveAttribute(
      'href',
      '/accounts/11111111-1111-4111-8111-111111111111',
    );
  });

  it('reaches an account no source has named', async () => {
    section([decided()], new Map());
    await userEvent.click(screen.getByRole('button'));

    // An account nobody has named is exactly the one a reader most wants to
    // open, and withholding the link because the label is poor would hide the
    // page that explains why.
    expect(screen.getByRole('link')).toHaveAttribute(
      'href',
      '/accounts/11111111-1111-4111-8111-111111111111',
    );
  });

  it('marks a dismissal as feedback about Signora, not as a loss', async () => {
    section([decided()]);
    await userEvent.click(screen.getByRole('button'));

    expect(screen.getByText('Not worth showing')).toBeVisible();
    expect(screen.queryByText('Lost')).toBeNull();
  });

  it('keeps a lost deal distinct from a dismissal', async () => {
    section([decided({ stage: 'closed_lost', reason: 'Went with the incumbent.' })]);
    await userEvent.click(screen.getByRole('button'));

    // Merging them would destroy the only signal the platform gets about its
    // own qualification quality.
    expect(screen.getByText('Lost')).toBeVisible();
    expect(screen.queryByText('Not worth showing')).toBeNull();
  });

  it('says when, in words rather than a timestamp', async () => {
    section([decided()]);
    await userEvent.click(screen.getByRole('button'));

    expect(screen.queryByText(/2026-07-30T/)).toBeNull();
  });

  it('marks a row the reader holds', async () => {
    section([decided()]);
    await userEvent.click(screen.getByRole('button'));

    expect(screen.getByText(/yours/)).toBeVisible();
  });

  it('claims nothing about a row somebody else holds', async () => {
    section([decided({ owner_id: 'someone-else' })]);
    await userEvent.click(screen.getByRole('button'));

    // **D23.** The tier verifies tokens without learning who anybody is, so
    // it can never say a name — and saying the wrong one would be worse.
    expect(screen.queryByText(/yours/)).toBeNull();
  });
});

describe('what it deliberately does not offer', () => {
  it('has no undo', async () => {
    section([decided()]);
    await userEvent.click(screen.getByRole('button'));

    // A dismissal is a recorded decision with a reason. Reopening is a
    // *transition*, with its own reason and actor, and it lives on the
    // account's brief — a one-click undo would edit history.
    expect(screen.queryByRole('button', { name: /undo|restore|reopen/i })).toBeNull();
  });

  it('shows no score beside a settled judgement', async () => {
    const { container } = section([decided()]);
    await userEvent.click(screen.getByRole('button'));

    // Re-litigating a decision against a number that moved after it was made
    // is a different activity, and the brief is one click away for it.
    expect(container.textContent).not.toMatch(/\bscore\b/i);
  });

  it('never shows a workflow stage key', async () => {
    const { container } = section([
      decided(),
      decided({ opportunity_id: 'b', account_id: 'b', stage: 'closed_lost' }),
    ]);
    await userEvent.click(screen.getByRole('button'));

    // `dismissed` and `closed_lost` are the platform's words (ADR-0034).
    expect(container.textContent).not.toContain('dismissed');
    expect(container.textContent).not.toContain('closed_lost');
  });
});

describe('the rows are a list', () => {
  it('renders one list item per decision', async () => {
    section([
      decided(),
      decided({ opportunity_id: 'b', account_id: 'b', reason: 'Too small.' }),
    ]);
    await userEvent.click(screen.getByRole('button'));

    const list = screen.getByRole('list');
    expect(within(list).getAllByRole('listitem')).toHaveLength(2);
  });
});
