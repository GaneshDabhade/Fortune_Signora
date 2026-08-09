/**
 * **Screen `14 · Invitation expired`** — [TASK-489](../../../docs/BACKLOG.md),
 * the half of that row [B-214](../../../docs/BUGS.md) unblocked.
 *
 * ⚡ **The interesting assertions are all about what this screen does NOT
 * say.** An expired invitation is the weakest possible claim to membership, so
 * the disclosure question that blocks screen `13` is settled here by saying
 * less rather than by a ruling.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import InvitationExpiredPage from '@/app/(auth)/invite/expired/page';

describe('what the screen tells somebody whose link aged out', () => {
  it('says the invitation expired, and why the link no longer works', () => {
    render(<InvitationExpiredPage />);
    expect(
      screen.getByRole('heading', { name: /This invitation has expired/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/time-limited/i)).toBeInTheDocument();
  });

  it('⚡ names a person as the recovery route, not a control that cannot work', () => {
    /**
     * ⛔ **Nothing in the product lets an invitee extend their own
     * invitation.** A *"Request a new one"* button would be a control with no
     * capability behind it — [§2](../../../CLAUDE.md)'s class — so the screen
     * tells them who actually can.
     */
    render(<InvitationExpiredPage />);
    expect(screen.getByText(/Ask whoever invited you/i)).toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: /resend|request|renew|new invitation/i }),
    ).not.toBeInTheDocument();
  });
});

describe('🔴 what it refuses to disclose', () => {
  it('⛔ never names the organization', () => {
    /**
     * 📁 **[C-208](../../../docs/LANE_COORDINATION.md) settled this for
     * `/join`**: *"the name lives inside the tenant the reader has not
     * entered."* ⚡ **An expired invitation is a weaker claim than a live one**,
     * so this screen discloses less than the accept screen, never more — and
     * **that is why it can ship while screen `13` waits on
     * [C-245](../../../docs/LANE_COORDINATION.md).**
     */
    const { container } = render(<InvitationExpiredPage />);
    const text = container.textContent ?? '';
    // Nothing that could only come from inside the tenant.
    expect(text).not.toMatch(/workspace name|members?\b.*\d|invited by|your role/i);
    // And no interpolation hole where a name was meant to go.
    expect(text).not.toMatch(/\{\{|\bundefined\b|\bnull\b/);
  });

  it('⛔ does not send them back to the form as the primary action', () => {
    // They did not fail to authenticate — the link aged out. Leading with
    // sign-in would imply they got something wrong.
    render(<InvitationExpiredPage />);
    const links = screen.getAllByRole('link');
    expect(links[0]).not.toHaveAttribute('href', '/sign-in');
    // It is still offered, second, for somebody who already has an account.
    expect(screen.getByRole('link', { name: /^Sign in$/ })).toHaveAttribute('href', '/sign-in');
  });
});
