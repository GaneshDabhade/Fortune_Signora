/**
 * The screen that lets an organization grow.
 *
 * **Until this shipped, a workspace was permanently whoever created it** —
 * `POST /members` takes a `user_id`, and nothing resolved an address to one.
 *
 * These assert the product rules rather than the rendering: that a forgotten
 * invitation is raised rather than waited for, that settled invitations stay
 * visible because an expired one is the signal to act on, and that the words a
 * customer reads are theirs rather than the enum's.
 */
import { fireEvent, render, screen, within } from '@testing-library/react';
import type { ReactElement } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { Invitation } from '@/lib/api/types';

const workspaceContext = vi.hoisted(() => vi.fn());
const invitations = vi.hoisted(() => vi.fn());
const invite = vi.hoisted(() => vi.fn());
const revoke = vi.hoisted(() => vi.fn());

vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: workspaceContext,
}));

vi.mock('@/lib/query/hooks/team', () => ({
  useInvitations: invitations,
  useInviteMember: () => ({ mutate: invite, isPending: false }),
  useRevokeInvitation: () => ({ mutate: revoke, isPending: false }),
}));

vi.mock('@/components/feedback/toast', () => ({ useToast: () => ({ toast: vi.fn() }) }));

import TeamPage from '@/app/(app)/settings/team/page';

const WORKSPACE = { id: 'aaaaaaaa-1111-4111-8111-111111111111', name: 'Acme Revenue' };
const IDLE = { data: undefined, isLoading: false, isError: false };

function invitation(overrides: Partial<Invitation> = {}): Invitation {
  return {
    id: 'i1',
    workspace_id: WORKSPACE.id,
    invited_email: 'sam@acme.com',
    role: 'member',
    state: 'pending',
    expires_at: new Date(Date.now() + 6 * 864e5).toISOString(),
    created_at: new Date().toISOString(),
    invited_by: 'u1',
    ...overrides,
  };
}

function draw(): ReactElement {
  return <TeamPage />;
}

beforeEach(() => {
  vi.clearAllMocks();
  workspaceContext.mockReturnValue({ activeWorkspace: WORKSPACE, isLoading: false });
  invitations.mockReturnValue({ ...IDLE, data: [] });
});

describe('an organization with nobody in it says what to do about it', () => {
  it('offers the invitation rather than showing an empty table', () => {
    // A table of one row with column headings is the product showing its
    // schema. The one moment an administrator is guaranteed to be looking is
    // the moment to ask for a colleague.
    render(draw());

    expect(screen.getByText('Nobody has been invited yet')).toBeVisible();
    expect(screen.queryByRole('table')).toBeNull();
  });
});

describe('the list answers *did anybody not come?*', () => {
  it('keeps settled invitations, because an expired one is the signal', () => {
    invitations.mockReturnValue({
      ...IDLE,
      data: [invitation({ id: 'i2', invited_email: 'kit@acme.com', state: 'expired' })],
    });

    render(draw());

    expect(screen.getByText('kit@acme.com')).toBeVisible();
    expect(screen.getByText('Expired')).toBeVisible();
  });

  it('puts everyone still waiting above everyone settled', () => {
    invitations.mockReturnValue({
      ...IDLE,
      data: [
        invitation({ id: 'a', invited_email: 'settled@acme.com', state: 'revoked' }),
        invitation({ id: 'b', invited_email: 'waiting@acme.com', state: 'pending' }),
      ],
    });

    const { container } = render(draw());
    const text = container.textContent ?? '';

    expect(text.indexOf('waiting@acme.com')).toBeLessThan(text.indexOf('settled@acme.com'));
  });

  it('offers to withdraw only what can still be withdrawn', () => {
    // Withdrawing an accepted invitation would claim an act that changes
    // nothing — the colleague is already in the organization, and removing
    // them is a different operation with a different blast radius.
    invitations.mockReturnValue({
      ...IDLE,
      data: [invitation({ state: 'accepted', invited_email: 'joined@acme.com' })],
    });

    render(draw());

    expect(screen.queryByRole('button', { name: 'Withdraw' })).toBeNull();
  });

  it('withdraws the invitation the button belongs to', () => {
    invitations.mockReturnValue({ ...IDLE, data: [invitation({ id: 'i9' })] });

    render(draw());
    fireEvent.click(screen.getByRole('button', { name: 'Withdraw' }));

    expect(revoke).toHaveBeenCalledWith('i9');
  });
});

describe('a forgotten invitation is raised, not waited for', () => {
  it('says so when one has been unanswered for over a week', () => {
    // Nobody goes looking for a forgotten invitation — that is what forgotten
    // means — so the page has to raise it.
    invitations.mockReturnValue({
      ...IDLE,
      data: [invitation({ created_at: new Date(Date.now() - 9 * 864e5).toISOString() })],
    });

    render(draw());

    expect(screen.getByText(/sent over a week ago/)).toBeVisible();
  });

  it('stays quiet about a recent one', () => {
    invitations.mockReturnValue({ ...IDLE, data: [invitation()] });

    render(draw());

    expect(screen.queryByText(/sent over a week ago/)).toBeNull();
  });

  it('never counts a settled invitation as forgotten', () => {
    // An invitation withdrawn a month ago is not waiting for anybody.
    invitations.mockReturnValue({
      ...IDLE,
      data: [
        invitation({
          state: 'revoked',
          created_at: new Date(Date.now() - 30 * 864e5).toISOString(),
        }),
      ],
    });

    render(draw());

    expect(screen.queryByText(/sent over a week ago/)).toBeNull();
  });
});

describe('the words are the customer’s', () => {
  it('describes a role by what it lets somebody do', () => {
    invitations.mockReturnValue({ ...IDLE, data: [invitation({ role: 'owner' })] });

    render(draw());

    expect(screen.getByText('Can administer Signora')).toBeVisible();
  });

  it('says *Withdrawn* rather than *Revoked*', () => {
    // A salesperson withdraws an offer; a system revokes a credential.
    invitations.mockReturnValue({ ...IDLE, data: [invitation({ state: 'revoked' })] });

    render(draw());

    expect(screen.getByText('Withdrawn')).toBeVisible();
    expect(screen.queryByText('Revoked')).toBeNull();
  });

  it('tells the administrator what sending one does, and that it is reversible', () => {
    render(draw());
    fireEvent.click(screen.getAllByRole('button', { name: 'Invite a colleague' })[0]);

    expect(screen.getByText(/You can withdraw it any time before they accept/)).toBeVisible();
  });
});

describe('sending an invitation', () => {
  function openDialog() {
    render(draw());
    fireEvent.click(screen.getAllByRole('button', { name: 'Invite a colleague' })[0]);
    return screen.getByRole('dialog');
  }

  it('cannot be sent without an address', () => {
    const dialog = openDialog();

    expect(within(dialog).getByRole('button', { name: 'Send invitation' })).toBeDisabled();
  });

  it('sends the address and the role together', () => {
    const dialog = openDialog();

    fireEvent.change(within(dialog).getByLabelText('Their email address'), {
      target: { value: ' Sam@Acme.com ' },
    });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Send invitation' }));

    expect(invite).toHaveBeenCalledWith(
      { email: 'Sam@Acme.com', role: 'member' },
      expect.anything(),
    );
  });

  it('defaults to the role that cannot administer anything', () => {
    // The safe default. Making somebody an administrator is a deliberate act.
    const dialog = openDialog();

    expect(within(dialog).getByLabelText('What they can do')).toHaveValue('member');
  });
});

describe('it says when it could not load, rather than disappearing', () => {
  it('reports the failure and reassures about the data', () => {
    invitations.mockReturnValue({ ...IDLE, isError: true });

    render(draw());

    expect(screen.getByText(/could not be loaded/)).toBeVisible();
    expect(screen.getByRole('heading', { name: 'Invited' })).toBeVisible();
  });
});
