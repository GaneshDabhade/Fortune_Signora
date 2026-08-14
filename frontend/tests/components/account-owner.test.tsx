/**
 * **The Companies table's Owner column** — [TASK-1479](../../../docs/BACKLOG.md) slice ⓶.
 *
 * 🔴 **The subject is the three states**, and specifically that **an unread
 * answer must not render as *Unassigned*** — 📁 [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md)'s
 * loading cousin, which [C-226](../../../docs/LANE_COORDINATION.md) found six
 * times on one screen.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import {
  AccountOwner,
  UnassignedOwner,
  ownerFor,
} from '@/components/accounts/account-owner';
import type { AccountAssignment } from '@/lib/query/hooks/account-assignments';

const PRIYA = { user_id: 'u1', name: 'Priya Raghunathan' };
const OWNED: AccountAssignment = {
  account_id: 'a1',
  role: 'owner',
  member_user_id: 'u1',
};

describe('🔴 an unresolved read is not an empty result', () => {
  it('renders nothing at all while the answer has not arrived', () => {
    /**
     * ⛔ **Not *Unassigned*.** That is a claim about the account, and the
     * screen does not yet know it — **forty rows saying *Unassigned* during a
     * load is forty false statements.**
     */
    const { container } = render(<AccountOwner assignment={undefined} members={[PRIYA]} />);

    expect(container).toBeEmptyDOMElement();
  });

  it('✅ and a genuinely unassigned account gets a designed answer', () => {
    render(<UnassignedOwner />);

    expect(screen.getByText('Unassigned')).toBeVisible();
  });
});

describe('⚡ the id becomes a person here, and nowhere else', () => {
  it('resolves the member against the list the screen already holds', () => {
    /**
     * 📁 ADR-0411 stores a reference *so that a name is never duplicated* —
     * ⛔ **a name on the wire would be stale the day somebody changed theirs.**
     */
    render(<AccountOwner assignment={OWNED} members={[PRIYA]} />);

    expect(screen.getByText('Priya Raghunathan')).toBeVisible();
  });

  it('🔴 says so when the holder is no longer a member', () => {
    /**
     * ⚡ **The case the reference model makes visible** — 📁 and exactly what
     * [C-1510](../../../docs/LANE_COORDINATION.md) asks the product owner
     * about.
     *
     * ⛔ **Never the raw id**: a customer shown a `UUID` learns nothing.
     * ⛔ **And never nothing**: that would hide that the account is held.
     */
    render(<AccountOwner assignment={OWNED} members={[]} />);

    expect(screen.getByText('No longer a member')).toBeVisible();
    expect(screen.queryByText('u1')).not.toBeInTheDocument();
  });
});

describe('⛔ picking one account’s owner out of a page of answers', () => {
  it('finds the owner and not the CSM', () => {
    const assignments: AccountAssignment[] = [
      { account_id: 'a1', role: 'csm', member_user_id: 'u2' },
      OWNED,
    ];

    expect(ownerFor('a1', assignments)?.member_user_id).toBe('u1');
  });

  it('answers undefined for an account this page did not ask about', () => {
    expect(ownerFor('a2', [OWNED])).toBeUndefined();
  });

  it('🔴 answers undefined while the page is unread, never a false absence', () => {
    /**
     * ⚡ **The guard that stops an unread page becoming forty *Unassigned*
     * cells.** `undefined` in, `undefined` out — the caller cannot flatten the
     * distinction by accident.
     */
    expect(ownerFor('a1', undefined)).toBeUndefined();
  });
});
