/**
 * **Bulk revocation** — [TASK-470](../../../docs/BACKLOG.md) milestone 3.
 *
 * 🔴 **Two approved designs draw this and neither half of the repository had
 * it.** 📁 The Security Center's §05 renders ***"Revoke 2 selected"*** and
 * ***"Sign out everywhere"*** side by side; the User Profile's `05` renders the
 * second. ⛔ **The panel shipped with per-session revocation only.**
 *
 * ⚠️ **The L-1 reuse audit narrowed this row before a line was written**: the
 * sessions list, the read, the re-read rule and the *this device* exclusion all
 * already shipped in [TASK-1414](../../../docs/BACKLOG.md). **A second sessions
 * panel would have been the duplicate this repository keeps filing.**
 *
 * 🔴 **The distinction every test here turns on**: 📁 *"Sign out everywhere
 * leaves this one alive by default. Choosing to include it is possible, and
 * warns that you will land on the sign-in screen."* ⚡ **Two different endpoints
 * — `/revoke-other-sessions` and `/revoke-sessions` — and calling the wrong one
 * signs somebody out of the screen they are reading.**
 */
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const listSessions = vi.hoisted(() => vi.fn());
const revokeSession = vi.hoisted(() => vi.fn());
const revokeSessions = vi.hoisted(() => vi.fn());
const revokeOtherSessions = vi.hoisted(() => vi.fn());

vi.mock('@/lib/auth/client', () => ({
  authClient: { listSessions, revokeSession, revokeSessions, revokeOtherSessions },
}));

import { AccountSecurity } from '@/app/(app)/profile/security/account-security';

const HERE = 'token-here';

function session(token: string, userAgent: string) {
  return {
    token,
    userAgent,
    ipAddress: '10.4.1.9',
    createdAt: '2026-08-10T08:02:00.000Z',
    updatedAt: '2026-08-12T06:00:00.000Z',
  };
}

const THREE = [
  session(HERE, 'Mozilla/5.0 Chrome/138'),
  session('token-edge', 'Mozilla/5.0 Edge/138'),
  session('token-fox', 'Mozilla/5.0 Firefox/131'),
];

beforeEach(() => {
  vi.clearAllMocks();
  listSessions.mockResolvedValue({ error: null, data: THREE });
  revokeSession.mockResolvedValue({ error: null });
  revokeSessions.mockResolvedValue({ error: null });
  revokeOtherSessions.mockResolvedValue({ error: null });
});

async function panel() {
  render(<AccountSecurity currentToken={HERE} factors={2} />);
  return await screen.findByTestId('sessions-bulk-bar');
}

describe('🔴 Sign out everywhere leaves this one alive', () => {
  /**
   * 🔴 **The assertion that separates the two endpoints**, and the one a test
   * checking *"a request was made"* would pass while the product signed the
   * reader out.
   */
  it('🔴 calls revoke-OTHER-sessions, never revoke-sessions', async () => {
    const bar = await panel();

    await userEvent.click(within(bar).getByRole('button', { name: 'Sign out everywhere' }));

    expect(revokeOtherSessions).toHaveBeenCalledTimes(1);
    expect(revokeSessions).not.toHaveBeenCalled();
  });

  /**
   * ⚡ **The list is re-read afterwards**, on the panel's existing rule — 📁
   * *"session rows never render optimistically."*
   */
  it('✅ re-reads the list rather than trusting the response', async () => {
    const bar = await panel();
    expect(listSessions).toHaveBeenCalledTimes(1);

    await userEvent.click(within(bar).getByRole('button', { name: 'Sign out everywhere' }));

    expect(listSessions).toHaveBeenCalledTimes(2);
  });

  /**
   * ⛔ **Nothing to sign out of means the control refuses rather than
   * disappears.** ⚡ **It is part of the design's anatomy**, and an absent
   * control reads as a missing capability rather than an empty one.
   */
  it('⛔ is disabled when this is the only session', async () => {
    listSessions.mockResolvedValue({ error: null, data: [THREE[0]] });
    const bar = await panel();

    expect(within(bar).getByRole('button', { name: 'Sign out everywhere' })).toBeDisabled();
  });
});

describe('🔴 Revoke N selected', () => {
  it('✅ revokes exactly the selected tokens, and not this one', async () => {
    await panel();

    await userEvent.click(screen.getByRole('checkbox', { name: 'Select Edge session' }));
    await userEvent.click(
      screen.getByRole('button', { name: 'Revoke 1 selected' }),
    );

    expect(revokeSession).toHaveBeenCalledTimes(1);
    expect(revokeSession).toHaveBeenCalledWith({ token: 'token-edge' });
  });

  /**
   * 🔴 **The count in the bar is the count that will be revoked.** ⛔ **A
   * *select all* that silently skipped this session would make the number a
   * guess**, so the current session is not selectable at all.
   */
  it('🔴 select-all takes every OTHER session, and the count says so', async () => {
    await panel();

    await userEvent.click(screen.getByRole('checkbox', { name: 'Select every other session' }));

    expect(screen.getByRole('button', { name: 'Revoke 2 selected' })).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: 'Revoke 2 selected' }));

    expect(revokeSession).toHaveBeenCalledTimes(2);
    expect(revokeSession).not.toHaveBeenCalledWith({ token: HERE });
  });

  /**
   * ⛔ **This session has no checkbox at all** — 📁 *"your own session is never
   * revoked silently"*, and **a checkbox that cannot be ticked is worse than
   * none** ([§2](../../../CLAUDE.md)).
   */
  it('⛔ this session offers no selection control', async () => {
    await panel();

    expect(
      screen.queryByRole('checkbox', { name: 'Select Chrome session' }),
    ).not.toBeInTheDocument();
  });

  /**
   * 🔴 **A selection is cleared by the re-read**, because every token in it may
   * already be gone. ⚡ **The rule [`signal-queue.tsx`](../../app/\(app\)/signals/signal-queue.tsx)
   * already keeps** — *a selection that survives is a selection whose action
   * bar lies about what it will act on.*
   */
  it('🔴 the selection does not survive the re-read', async () => {
    await panel();

    await userEvent.click(screen.getByRole('checkbox', { name: 'Select Edge session' }));
    await userEvent.click(screen.getByRole('button', { name: 'Revoke 1 selected' }));

    expect(screen.queryByRole('button', { name: /Revoke .* selected/ })).not.toBeInTheDocument();
  });

  /**
   * ⛔ **A failure stops the loop.** ⚡ **The ones that succeeded really are
   * revoked** — carrying on would report a partial result as a whole one, and
   * the panel states the failure rather than the count.
   */
  it('⛔ stops at the first failure rather than pressing on', async () => {
    revokeSession.mockResolvedValueOnce({ error: { message: 'nope' } });
    await panel();

    await userEvent.click(screen.getByRole('checkbox', { name: 'Select every other session' }));
    await userEvent.click(screen.getByRole('button', { name: 'Revoke 2 selected' }));

    expect(revokeSession).toHaveBeenCalledTimes(1);
  });
});

describe('🔴 including this one is possible, and it warns first', () => {
  /**
   * 🔴 **The design's exact requirement**: *"Choosing to include it is
   * possible, and warns that you will land on the sign-in screen."* ⛔ **One
   * click must not end the session reading the page.**
   */
  it('🔴 warns before ending the session reading the page', async () => {
    await panel();

    await userEvent.click(screen.getByRole('button', { name: 'Sign out of this one too' }));

    expect(screen.getByText(/land on the sign-in screen/i)).toBeInTheDocument();
    // ⛔ **Nothing has happened yet.**
    expect(revokeSessions).not.toHaveBeenCalled();
  });

  /**
   * ⚠️ **This test found a real ambiguity rather than needing a better
   * selector.** ⛔ **The confirm was also called *"Sign out everywhere"***, so
   * the page held two buttons with one accessible name doing different things
   * — **and the one inside the dialog ends the session reading it.** ✅ **The
   * product was renamed, not the query.**
   */
  it('✅ and confirming calls revoke-sessions, the one that includes this one', async () => {
    await panel();

    await userEvent.click(screen.getByRole('button', { name: 'Sign out of this one too' }));
    await userEvent.click(
      screen.getByRole('button', { name: 'Sign out, including here', hidden: true }),
    );

    expect(revokeSessions).toHaveBeenCalledTimes(1);
    expect(revokeOtherSessions).not.toHaveBeenCalled();
  });

  /**
   * ⛔ **The honest sentence the design writes, and it ships as content.** 📁
   * *"Your identity provider may still hold a session — we say so rather than
   * implying we control it."*
   */
  it('✅ says what it cannot end', async () => {
    await panel();

    await userEvent.click(screen.getByRole('button', { name: 'Sign out of this one too' }));

    expect(screen.getByText(/identity provider may still hold a session/i)).toBeInTheDocument();
  });
});
