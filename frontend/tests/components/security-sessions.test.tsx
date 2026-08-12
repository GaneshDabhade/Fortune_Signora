/**
 * **§01 posture and §05 sessions, which are one read** —
 * [TASK-1414](../../../docs/BACKLOG.md).
 *
 * 🔴 **The row's Playwright coverage says *"revoking a session actually ends
 * it — asserted from the revoked session, not from the list."*** ⚡ **A browser
 * is where that half is proven.** ⛔ **What is proven HERE is the half a browser
 * cannot show**: that the list is re-read rather than spliced, so the screen
 * never claims a revocation on the strength of a `200` nobody re-checked.
 */
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const listSessions = vi.hoisted(() => vi.fn());
const revokeSession = vi.hoisted(() => vi.fn());

vi.mock('@/lib/auth/client', () => ({ authClient: { listSessions, revokeSession } }));

import { AccountSecurity } from '@/app/(app)/profile/security/account-security';
import { clientOf } from '@/app/(app)/profile/security/sessions-panel';

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

const TWO = [
  session(HERE, 'Mozilla/5.0 Chrome/138'),
  session('token-there', 'Mozilla/5.0 Edge/138'),
];

beforeEach(() => {
  vi.clearAllMocks();
  listSessions.mockResolvedValue({ error: null, data: TWO });
  revokeSession.mockResolvedValue({ error: null });
});

describe('🔴 one read, two surfaces', () => {
  /**
   * ⛔ **The posture cell and the table are the same question.** ⚡ **Two reads
   * would be two answers** ([§2](../../../CLAUDE.md)) — **and they would
   * disagree at the one moment the number matters.**
   */
  it('🔴 the sessions are fetched ONCE for both panels', async () => {
    render(<AccountSecurity currentToken={HERE} factors={2} />);

    await screen.findByText('2 sessions');
    expect(listSessions).toHaveBeenCalledTimes(1);
  });

  it('✅ and the posture cell agrees with the table it is beside', async () => {
    render(<AccountSecurity currentToken={HERE} factors={2} />);

    expect(await screen.findByText('2 sessions')).toBeInTheDocument();
    expect(within(screen.getByRole('table')).getAllByRole('row')).toHaveLength(3);
  });
});

describe('🔴 revocation', () => {
  it('⛔ this device is never offered for revocation', async () => {
    render(<AccountSecurity currentToken={HERE} factors={2} />);

    const rows = within(await screen.findByRole('table')).getAllByRole('row');
    // ⚡ **No control at all rather than a disabled one** — there is nothing to
    // refuse, so there is nothing to offer.
    expect(within(rows[1] as HTMLElement).queryByRole('button')).not.toBeInTheDocument();
    expect(rows[1]).toHaveTextContent('This device');
    expect(within(rows[2] as HTMLElement).getByRole('button', { name: 'Revoke' })).toBeInTheDocument();
  });

  /**
   * 🔴 **The assertion an optimistic implementation fails.**
   *
   * 📁 ***"Session rows never render optimistically. A stale list here is worse
   * than a slow one."*** ⛔ **Splicing the row out of local state would pass
   * every *the row is gone* assertion** — **so this asserts the RE-READ.**
   */
  it('🔴 a successful revoke re-reads the list rather than removing the row locally', async () => {
    render(<AccountSecurity currentToken={HERE} factors={2} />);
    const table = await screen.findByRole('table');

    listSessions.mockResolvedValue({ error: null, data: [TWO[0]] });
    await userEvent.click(within(table).getByRole('button', { name: 'Revoke' }));

    expect(revokeSession).toHaveBeenCalledWith({ token: 'token-there' });
    expect(listSessions).toHaveBeenCalledTimes(2);
    expect(await screen.findByText('1 session')).toBeInTheDocument();
  });

  it('⛔ a failed revoke says so instead of showing a list nobody re-checked', async () => {
    revokeSession.mockResolvedValue({ error: { message: 'no' } });
    render(<AccountSecurity currentToken={HERE} factors={2} />);
    const table = await screen.findByRole('table');

    await userEvent.click(within(table).getByRole('button', { name: 'Revoke' }));

    expect(await screen.findByText(/could not load where you are signed in/i)).toBeInTheDocument();
  });
});

describe('🔴 a failed read is never an empty screen', () => {
  /**
   * 📁 [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md), and on this page the
   * empty result reads as ***you are signed in nowhere*** — ⛔ **which would
   * tell somebody under attack that the attacker's session is gone.**
   */
  it('⛔ says the read failed, and shows no table at all', async () => {
    listSessions.mockResolvedValue({ error: { message: 'down' }, data: null });
    render(<AccountSecurity currentToken={HERE} factors={2} />);

    expect(await screen.findByText(/could not load where you are signed in/i)).toBeInTheDocument();
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
  });

  /**
   * 🔴 **And the posture cell must not turn the failure into a number.**
   * ⛔ **`0 sessions` beside a failed read is the same lie in a smaller font.**
   */
  it('🔴 the posture cell says Not known rather than a count', async () => {
    listSessions.mockResolvedValue({ error: { message: 'down' }, data: null });
    render(<AccountSecurity currentToken={HERE} factors={2} />);

    const cell = (await screen.findAllByTestId('posture-cell')).find(
      (candidate) => candidate.dataset.label === 'Active sessions',
    );
    expect(cell).toHaveTextContent('Not known');
    expect(cell).not.toHaveTextContent(/\d+ sessions?/);
  });
});

describe('⛔ a client is not a device', () => {
  it('✅ names the browser and never guesses the hardware', () => {
    expect(clientOf('Mozilla/5.0 (Macintosh) Chrome/138 Safari/537')).toBe('Chrome');
    expect(clientOf('Mozilla/5.0 (Macintosh) Version/18 Safari/605')).toBe('Safari');
  });

  it('⛔ an absent user agent is Unknown client, never blank', () => {
    expect(clientOf(null)).toBe('Unknown client');
    expect(clientOf('')).toBe('Unknown client');
  });
});

describe('🔴 §01 · the three cells that cannot answer', () => {
  /**
   * ⛔ **The most dangerous sentence this product could print is
   * `Open alerts: none`**, and it is the one a tidier screen would print.
   */
  it('⛔ open alerts says Not known, on screen, in words', async () => {
    render(<AccountSecurity currentToken={HERE} factors={2} />);

    const cell = (await screen.findAllByTestId('posture-cell')).find(
      (candidate) => candidate.dataset.label === 'Open alerts',
    );
    expect(cell).toHaveTextContent('Not known');
    expect(cell).toHaveTextContent('nothing reads them back yet');
  });

  it('✅ all five cells are on the page, including the three that cannot answer', async () => {
    render(<AccountSecurity currentToken={HERE} factors={2} />);

    expect(await screen.findAllByTestId('posture-cell')).toHaveLength(5);
  });
});
