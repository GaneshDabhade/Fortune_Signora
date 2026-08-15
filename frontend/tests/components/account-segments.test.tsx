/**
 * **The Companies table's Segment column** — [TASK-1479](../../../docs/BACKLOG.md)
 * slice ⓶b.
 *
 * 🔴 **The subject is the three states**, and specifically that **an unread
 * answer must not render as *No segment*** — 📁 [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md)'s
 * loading cousin, which [C-226](../../../docs/LANE_COORDINATION.md) found six
 * times on one screen and which the Owner column met one slice ago.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import {
  AccountSegments,
  UnsegmentedAccount,
  membershipFor,
} from '@/components/accounts/account-segments';
import type {
  AccountSegment,
  AccountSegmentMembership,
} from '@/lib/query/hooks/account-segments';

const BOARD: AccountSegment = {
  segment_id: 's1',
  name: 'Board reporting set',
  account_count: 212,
};
const WATCH: AccountSegment = {
  segment_id: 's2',
  name: 'Competitive watch',
  account_count: 26,
};
const IN_BOTH: AccountSegmentMembership = {
  account_id: 'a1',
  segment_ids: ['s1', 's2'],
};

describe('🔴 an unresolved read is not an empty result', () => {
  it('renders nothing at all while the answer has not arrived', () => {
    /**
     * ⛔ **Not *No segment*.** That is a claim about the company, and the
     * screen does not yet know it — **forty rows saying it during a load is
     * forty false statements.**
     */
    const { container } = render(
      <AccountSegments membership={undefined} segments={[BOARD]} />,
    );

    expect(container).toBeEmptyDOMElement();
  });

  it('✅ and a company genuinely in no grouping gets a designed answer', () => {
    render(<UnsegmentedAccount />);

    expect(screen.getByText('No segment')).toBeVisible();
  });

  it('🔴 says so when the read arrived and the company is in nothing', () => {
    /**
     * ⚠️ **The state between the two above, and it is the one that would be
     * lost.** ⛔ Rendering nothing here would be indistinguishable from
     * *unread*, **and the two are different facts about the same cell.**
     */
    render(
      <AccountSegments
        membership={{ account_id: 'a1', segment_ids: [] }}
        segments={[BOARD]}
      />,
    );

    expect(screen.getByText('No segment')).toBeVisible();
  });
});

describe('⚡ a company can be in more than one grouping, and the design says so', () => {
  it('renders every grouping it is in, not the first', () => {
    /**
     * 🔴 **The panel's counts overlap by construction** — 📁 five groupings
     * over one book of companies. ⛔ **Rendering only the first would be this
     * component choosing which of a customer's groupings matters**, which is
     * not a decision a cell gets to take.
     */
    render(<AccountSegments membership={IN_BOTH} segments={[BOARD, WATCH]} />);

    expect(screen.getByText('Board reporting set')).toBeVisible();
    expect(screen.getByText('Competitive watch')).toBeVisible();
  });

  it('⚡ orders them the way the directory does, not the way membership arrived', () => {
    /**
     * 📁 **The directory is name-ordered by the server**, so the same company
     * renders the same way on every visit. ⛔ *"Whatever order the ids came
     * back in"* is a hidden input (§2) — **a list a person scans that reorders
     * between two visits is the defect nobody reports and everybody
     * distrusts.**
     */
    render(
      <AccountSegments
        membership={{ account_id: 'a1', segment_ids: ['s2', 's1'] }}
        segments={[BOARD, WATCH]}
      />,
    );

    const rendered = screen.getAllByText(/Board reporting set|Competitive watch/);
    expect(rendered.map((node) => node.textContent)).toEqual([
      'Board reporting set',
      'Competitive watch',
    ]);
  });

  it('⛔ drops an id the directory does not know rather than rendering a broken chip', () => {
    /**
     * ⚡ **The two reads are separate requests**, so a grouping created between
     * them is a transient — **and the next directory fetch resolves it.** 📁
     * The same rule the Tags column already records.
     */
    render(
      <AccountSegments
        membership={{ account_id: 'a1', segment_ids: ['s1', 'created-since'] }}
        segments={[BOARD]}
      />,
    );

    expect(screen.getByText('Board reporting set')).toBeVisible();
    expect(screen.queryByText('created-since')).not.toBeInTheDocument();
  });
});

describe('⛔ picking one company’s groupings out of a page of answers', () => {
  it('finds the membership for the account asked about', () => {
    expect(membershipFor('a1', [IN_BOTH])?.segment_ids).toEqual(['s1', 's2']);
  });

  it('answers undefined for an account this page did not ask about', () => {
    expect(membershipFor('a2', [IN_BOTH])).toBeUndefined();
  });

  it('🔴 answers undefined while the page is unread, never a false absence', () => {
    /**
     * ⚡ **The guard that stops an unread page becoming forty *No segment*
     * cells.** `undefined` in, `undefined` out — the caller cannot flatten the
     * distinction by accident.
     */
    expect(membershipFor('a1', undefined)).toBeUndefined();
  });
});
