/**
 * *"What happened?"*, answered for somebody who does not know how Signora is
 * built.
 *
 * **The test the product owner set:** would an auditor, a support engineer and
 * a new owner all understand it? So these assert that no entry names a table,
 * an enum value, an identifier or an operation — and that every question a
 * customer would reasonably ask has an answer.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { OrganizationHistory } from '@/components/team/history';
import type { HistoryEntry } from '@/lib/api/types';

function entry(overrides: Partial<HistoryEntry> = {}): HistoryEntry {
  return {
    occurred_at: '2026-08-01T09:00:00Z',
    kind: 'invited',
    actor_id: 'u1',
    actor_email: 'ana@acme.com',
    subject_email: 'sam@acme.com',
    subject_membership_id: null,
    previous_role: null,
    new_role: 'member',
    reason: null,
    ...overrides,
  };
}

function draw(entries: HistoryEntry[]) {
  return render(
    <OrganizationHistory entries={entries} isLoading={false} isError={false} />,
  );
}

describe('every question a customer would ask has an answer', () => {
  it('who invited this person', () => {
    draw([entry()]);

    expect(screen.getByText(/ana@acme.com invited sam@acme.com/)).toBeVisible();
  });

  it('who removed them, and why', () => {
    draw([
      entry({
        kind: 'removed',
        actor_email: 'ana@acme.com',
        subject_email: 'jo@acme.com',
        reason: 'Left the company',
      }),
    ]);

    expect(
      screen.getByText('ana@acme.com removed jo@acme.com — Left the company'),
    ).toBeVisible();
  });

  it('says who removed them even when nobody gave a reason', () => {
    // A removal without a reason is ordinary. The entry must still be complete.
    draw([entry({ kind: 'removed', subject_email: 'jo@acme.com' })]);

    expect(
      screen.getByText('ana@acme.com removed jo@acme.com from this organization'),
    ).toBeVisible();
  });

  it('who promoted them, and to what', () => {
    draw([
      entry({
        kind: 'role_changed',
        subject_email: 'jo@acme.com',
        previous_role: 'member',
        new_role: 'owner',
      }),
    ]);

    expect(
      screen.getByText(/made jo@acme.com able to administer Signora/),
    ).toBeVisible();
  });

  it('who stepped back, said as a move rather than a demotion', () => {
    // *Demoted* is a judgement. Somebody handing over has not been demoted.
    draw([
      entry({
        kind: 'role_changed',
        subject_email: 'ana@acme.com',
        previous_role: 'owner',
        new_role: 'member',
      }),
    ]);

    expect(screen.getByText(/moved ana@acme.com to working accounts/)).toBeVisible();
    expect(screen.queryByText(/demot/i)).toBeNull();
  });

  it('who created the organization', () => {
    draw([entry({ kind: 'joined', actor_email: null, new_role: 'owner' })]);

    expect(screen.getByText('sam@acme.com created this organization')).toBeVisible();
  });

  it('when, to the minute', () => {
    const { container } = draw([entry()]);

    expect(container.querySelector('time')).toHaveAttribute(
      'dateTime',
      '2026-08-01T09:00:00Z',
    );
  });
});

describe('it is honest about what it does not know', () => {
  it('says *Somebody* rather than guessing an actor', () => {
    // An invitation withdrawn today records no actor. Attributing it to the
    // inviter would be a guess about a different person.
    draw([
      entry({ kind: 'invitation_withdrawn', actor_id: null, actor_email: null }),
    ]);

    expect(screen.getByText('Somebody withdrew the invitation to sam@acme.com')).toBeVisible();
  });

  it('never prints an identifier', () => {
    const { container } = draw([entry({ actor_email: null, subject_email: null })]);

    expect(container.textContent).not.toContain('u1');
  });
});

describe('a reader who does not know how Signora is built', () => {
  it('meets no table, enum, identifier or operation', () => {
    const { container } = draw([
      entry(),
      entry({ kind: 'removed', reason: 'Contract ended' }),
      entry({ kind: 'role_changed', previous_role: 'member', new_role: 'owner' }),
      entry({ kind: 'joined', new_role: 'owner' }),
      entry({ kind: 'invitation_withdrawn' }),
      entry({ kind: 'invitation_accepted' }),
    ]);
    const text = (container.textContent ?? '').toLowerCase();

    for (const forbidden of [
      'membership',
      'workspace',
      'role_changed',
      'invitation_withdrawn',
      'owner"',
      'null',
      'undefined',
      'endpoint',
      'record',
    ]) {
      expect(text).not.toContain(forbidden);
    }
  });

  it('never says *member* or *owner* as bare words', () => {
    // They are the policy's words. A customer reads what somebody can do.
    const { container } = draw([
      entry({ new_role: 'owner' }),
      entry({ kind: 'role_changed', previous_role: 'owner', new_role: 'member' }),
    ]);
    const text = container.textContent ?? '';

    expect(text).toContain('administer Signora');
    expect(text).toContain('working accounts');
  });
});

describe('the states around it', () => {
  it('says a new organization has no history rather than showing nothing', () => {
    draw([]);

    expect(screen.getByText(/Nothing has happened here yet/)).toBeVisible();
  });

  it('reports a failure rather than disappearing', () => {
    render(<OrganizationHistory entries={[]} isLoading={false} isError />);

    expect(screen.getByText(/could not be loaded/)).toBeVisible();
  });

  it('groups by day, newest first', () => {
    const { container } = draw([
      entry({ occurred_at: '2026-08-02T09:00:00Z', subject_email: 'newer@acme.com' }),
      entry({ occurred_at: '2026-08-01T09:00:00Z', subject_email: 'older@acme.com' }),
    ]);
    const text = container.textContent ?? '';

    expect(text.indexOf('newer@acme.com')).toBeLessThan(text.indexOf('older@acme.com'));
    expect(container.querySelectorAll('section')).toHaveLength(2);
  });
});
