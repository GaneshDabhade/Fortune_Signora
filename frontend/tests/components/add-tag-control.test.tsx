/**
 * **The bulk bar's *Add tag*** — [TASK-466](../../../docs/BACKLOG.md).
 *
 * 🔴 **The copy is the subject.** 📁 The row's Definition of Done: ***"the
 * confirm states the COUNT and the ACTION in the customer's words"*** — and
 * the second half of that promise is that **nothing is tagged yet.**
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { AddTagControl } from '@/components/accounts/add-tag-control';
import type { AccountTag } from '@/lib/api/types';

const RISK: AccountTag = { id: 't1', name: 'At risk', tone: 'risk' };

function open(props: Partial<Parameters<typeof AddTagControl>[0]> = {}) {
  render(
    <AddTagControl
      count={41}
      tags={[RISK]}
      onPropose={vi.fn()}
      onCreate={vi.fn()}
      pending={false}
      {...props}
    />,
  );
  fireEvent.click(screen.getByRole('button', { name: 'Add tag' }));
}

describe('🔴 the confirm names the count and the act, in the customer’s words', () => {
  it('says companies, never accounts', () => {
    /**
     * 📁 [ADR-0034](../../../docs/architecture/adr/0034-ubiquitous-language.md):
     * **a salesperson says *company* about the businesses they sell to**, and
     * `account` is the platform's word for the entity.
     */
    open();

    expect(screen.getByText(/Add a tag to 41 companies/)).toBeVisible();
    expect(screen.queryByText(/accounts/i)).not.toBeInTheDocument();
  });

  it('⚡ and one company is not "1 companies"', () => {
    open({ count: 1 });

    expect(screen.getByText(/Add a tag to 1 company$/)).toBeVisible();
  });
});

describe('🔴 it proposes, and the copy does not pretend otherwise', () => {
  it('says nothing changes until somebody approves it', () => {
    /**
     * 📁 [ADR-0405](../../../docs/architecture/adr/0405-an-action-is-approved-before-it-is-effective.md):
     * *an action is approved before it is effective.* ⛔ **A dialog that said
     * *"Tag 41 companies"* and closed would have told the customer the work
     * was done.**
     */
    open();

    expect(screen.getByText(/Nothing changes until somebody approves it/)).toBeVisible();
  });

  it('✅ and tells them the undo exists before they commit', () => {
    // ⚡ **Before, not after.** A reversal a customer only learns about in a
    // toast is one they cannot factor into the decision.
    open();

    expect(screen.getByText(/take it back for a\s+day/)).toBeVisible();
  });

  it('proposes the tag they picked', () => {
    const onPropose = vi.fn();
    open({ onPropose });

    fireEvent.click(screen.getByRole('button', { name: 'At risk' }));

    expect(onPropose).toHaveBeenCalledWith('t1');
  });
});

describe('⛔ an unread vocabulary is not an empty one', () => {
  it('renders no control at all while the read is in flight', () => {
    /**
     * 🔴 📁 [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md)'s shape: **an
     * unresolved read must never render as an empty result.** ⚡ Opening a
     * picker with an empty list would look like *"this organization has no
     * labels"* to somebody whose labels had simply not arrived.
     */
    const { container } = render(
      <AddTagControl
        count={41}
        tags={[]}
        onPropose={undefined}
        onCreate={vi.fn()}
        pending={false}
      />,
    );

    expect(container).toBeEmptyDOMElement();
  });

  it('✅ and a workspace that genuinely has none gets a designed empty state', () => {
    open({ tags: [] });

    expect(screen.getByText(/This organization has no tags yet/)).toBeVisible();
    // 📁 ADR-0034 again: the customer's word is *organization*.
    expect(screen.queryByText(/workspace/i)).not.toBeInTheDocument();
  });
});

describe('⚡ naming a new tag', () => {
  it('♿ the field is labelled', () => {
    open();

    expect(screen.getByLabelText('New tag name')).toBeVisible();
  });

  it('⛔ Create is refused while the name is blank', () => {
    open();

    expect(screen.getByRole('button', { name: 'Create' })).toBeDisabled();
  });

  it('⛔ and every control is refused while a proposal is in flight', () => {
    // ⚡ **A second press would propose a SECOND batch over the same
    // companies**, and the customer would have two approvals to make for one
    // decision.
    open({ pending: true });

    expect(screen.getByRole('button', { name: 'At risk' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Create' })).toBeDisabled();
  });
});
