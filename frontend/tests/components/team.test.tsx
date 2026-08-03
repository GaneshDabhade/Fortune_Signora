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

import type { Invitation, Membership } from '@/lib/api/types';

const workspaceContext = vi.hoisted(() => vi.fn());
const invitations = vi.hoisted(() => vi.fn());
const invite = vi.hoisted(() => vi.fn());
const revoke = vi.hoisted(() => vi.fn());
const resend = vi.hoisted(() => vi.fn());
const removeMember = vi.hoisted(() => vi.fn());
const members = vi.hoisted(() => vi.fn());
const viewerRole = vi.hoisted(() => vi.fn());
const session = vi.hoisted(() => vi.fn());

vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: workspaceContext,
}));

vi.mock('@/lib/query/hooks/team', () => ({
  useInvitations: invitations,
  useInviteMember: () => ({ mutate: invite, isPending: false }),
  useRevokeInvitation: () => ({ mutate: revoke, isPending: false }),
  useResendInvitation: () => ({ mutate: resend, isPending: false }),
  useRemoveMember: () => ({ mutate: removeMember, isPending: false }),
  useWorkspaceMembers: members,
  useViewerRole: viewerRole,
}));

vi.mock('@/lib/auth/client', () => ({ useSession: session }));

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

const ME = 'user-me';

function person(overrides: Partial<Membership> = {}): Membership {
  return {
    id: 'm1',
    workspace_id: WORKSPACE.id,
    user_id: ME,
    role: 'owner',
    created_at: '2026-08-01T09:00:00Z',
    member_email: 'ana@acme.com',
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
  session.mockReturnValue({ data: { user: { id: ME } } });
  viewerRole.mockReturnValue({ role: 'owner', resolved: true });
  members.mockReturnValue({ ...IDLE, data: { items: [person()] } });
});

describe('an organization with nobody in it says what to do about it', () => {
  it('offers the invitation rather than showing an empty table', () => {
    // A table of one row with column headings is the product showing its
    // schema. The one moment an administrator is guaranteed to be looking is
    // the moment to ask for a colleague.
    //
    // **Scoped to the Invited card**, because the roster above it legitimately
    // renders a table — the founder is always in it.
    render(draw());
    const invited = screen.getByRole('heading', { name: 'Invited' }).closest('div')!
      .parentElement!;

    expect(screen.getByText('Nobody has been invited yet')).toBeVisible();
    expect(within(invited).queryByRole('table')).toBeNull();
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
    // The same words in the roster and in the invited list, deliberately: a
    // role means one thing whether somebody holds it or has been offered it.
    invitations.mockReturnValue({ ...IDLE, data: [invitation({ role: 'owner' })] });

    render(draw());

    expect(screen.getAllByText('Can administer Signora')).toHaveLength(2);
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
    fireEvent.click(screen.getAllByRole('button', { name: 'Invite a colleague' })[0]!);

    expect(screen.getByText(/You can withdraw it any time before they accept/)).toBeVisible();
  });
});

describe('sending an invitation', () => {
  function openDialog() {
    render(draw());
    fireEvent.click(screen.getAllByRole('button', { name: 'Invite a colleague' })[0]!);
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

describe('the banner promised “send it again”, and now there is a control', () => {
  // **A defect in TM-03a, found by reading its own copy.** The forgotten-
  // invitation banner offered two actions and the table had one. A control
  // that goes nowhere costs more trust than an absent one — and here the
  // product was describing an action it could not perform.

  it('offers Send again on anything still waiting', () => {
    invitations.mockReturnValue({ ...IDLE, data: [invitation()] });

    render(draw());

    expect(screen.getByRole('button', { name: 'Send again' })).toBeVisible();
  });

  it('resends the invitation the button belongs to', () => {
    invitations.mockReturnValue({ ...IDLE, data: [invitation({ id: 'i7' })] });

    render(draw());
    fireEvent.click(screen.getByRole('button', { name: 'Send again' }));

    expect(resend).toHaveBeenCalledWith('i7', expect.anything());
  });

  it('does not offer it on a settled invitation', () => {
    // Re-sending a withdrawn invitation delivers a link that cannot be used,
    // which is worse than not sending one.
    invitations.mockReturnValue({ ...IDLE, data: [invitation({ state: 'expired' })] });

    render(draw());

    expect(screen.queryByRole('button', { name: 'Send again' })).toBeNull();
  });

  it('offers the recoverable action before the deliberate one', () => {
    invitations.mockReturnValue({ ...IDLE, data: [invitation()] });

    const { container } = render(draw());
    const text = container.textContent ?? '';

    expect(text.indexOf('Send again')).toBeLessThan(text.indexOf('Withdraw'));
  });
});

describe('the roster answers *who is in my organization?*', () => {
  it('names people by the address their membership was created with', () => {
    render(draw());

    expect(screen.getByText('ana@acme.com')).toBeVisible();
  });

  it('says *Somebody here* rather than an identifier when no address is known', () => {
    // **D23.** A membership added by identifier before invitations existed has
    // no address, and a UUID would be the same absence dressed as information.
    members.mockReturnValue({
      ...IDLE,
      data: { items: [person(), person({ id: 'm2', user_id: 'other', member_email: null })] },
    });

    const { container } = render(draw());

    expect(screen.getByText('Somebody here')).toBeVisible();
    expect(container.textContent).not.toContain('other');
  });

  it('marks which row is you', () => {
    render(draw());

    expect(screen.getByText('You')).toBeVisible();
  });

  it('says how many people, and how many can administer Signora', () => {
    // The second is what makes the last-owner refusal comprehensible before
    // anybody meets it.
    members.mockReturnValue({
      ...IDLE,
      data: {
        items: [person(), person({ id: 'm2', user_id: 'b', role: 'member', member_email: 'jo@acme.com' })],
      },
    });

    render(draw());

    expect(screen.getByText(/2 people · 1 can administer Signora/)).toBeVisible();
  });
});

describe('removing somebody is offered only where it is real', () => {
  it('is not offered to a member', () => {
    // Presentation, never enforcement — the server refuses it regardless, and
    // a control that goes nowhere costs more trust than an absent one.
    viewerRole.mockReturnValue({ role: 'member', resolved: true });
    members.mockReturnValue({
      ...IDLE,
      data: { items: [person(), person({ id: 'm2', user_id: 'b', member_email: 'jo@acme.com' })] },
    });

    render(draw());

    expect(screen.queryByRole('button', { name: 'Remove' })).toBeNull();
  });

  it('is never offered on your own row', () => {
    // Leaving is a different operation with a different invariant, and it is
    // blocked on C-207.
    render(draw());

    expect(screen.queryByRole('button', { name: 'Remove' })).toBeNull();
  });

  it('names the person and the consequence rather than asking *are you sure*', () => {
    members.mockReturnValue({
      ...IDLE,
      data: { items: [person(), person({ id: 'm2', user_id: 'b', member_email: 'jo@acme.com' })] },
    });

    render(draw());
    fireEvent.click(screen.getByRole('button', { name: 'Remove' }));

    expect(screen.getByText(/jo@acme.com will lose access/)).toBeVisible();
  });

  it('promises that what they decided stays on the record', () => {
    // D3: the membership is ended, never deleted, so decision history and the
    // timeline still say who acted.
    members.mockReturnValue({
      ...IDLE,
      data: { items: [person(), person({ id: 'm2', user_id: 'b', member_email: 'jo@acme.com' })] },
    });

    render(draw());
    fireEvent.click(screen.getByRole('button', { name: 'Remove' }));

    expect(screen.getByText(/already decided stays on the record/)).toBeVisible();
  });
});
