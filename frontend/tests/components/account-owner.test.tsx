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

const PRIYA = {
  id: 'm1',
  workspace_id: 'w1',
  user_id: 'u1',
  role: 'member' as const,
  created_at: '2026-08-01T00:00:00Z',
  member_email: 'priya.nair@northwind.example',
};
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
  it('shows the address, because the platform has no name to give', () => {
    /**
     * ⛔ **Better Auth owns user identity and runs in the Next.js tier, so the
     * Python API has no name** — 📁 [C-024](../../../docs/LANE_COORDINATION.md),
     * ADR-0026. ⚡ **`member_email` is what a person recognises, and it is
     * what Team Management already shows.**
     */
    render(<AccountOwner assignment={OWNED} members={[PRIYA]} />);

    expect(screen.getByText('priya.nair@northwind.example')).toBeVisible();
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


describe('⚡ the wording for an absent address is the one that already exists', () => {
  it('says “Somebody here” rather than an identifier dressed as information', () => {
    /**
     * 📁 **D23's wording, reused rather than reinvented.** Team Management
     * already answers this exact absence, and ⛔ **a second answer for one
     * question is the duplicated vocabulary [§4](../../../CLAUDE.md) forbids.**
     */
    render(
      <AccountOwner assignment={OWNED} members={[{ ...PRIYA, member_email: null }]} />,
    );

    expect(screen.getByText('Somebody here')).toBeVisible();
  });
});
