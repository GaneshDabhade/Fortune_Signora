/**
 * **Screens `09 · Set a new password` and `10 · Password updated`** —
 * [TASK-488](../../../docs/BACKLOG.md).
 *
 * ⚡ **The load-bearing test is the absence of a sentence.** The design says a
 * reset *"signs you out of 4 other devices"*; `revokeSessionsOnPasswordReset`
 * is unset, so nothing is signed out — [C-244](../../../docs/LANE_COORDINATION.md).
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const push = vi.hoisted(() => vi.fn());
vi.mock('next/navigation', () => ({ useRouter: () => ({ push, refresh: vi.fn() }) }));

const resetPassword = vi.hoisted(() => vi.fn());
vi.mock('@/lib/auth/client', () => ({
  resetPassword: (...a: unknown[]) => resetPassword(...a),
}));

import { ResetPasswordForm } from '@/app/(auth)/reset/[token]/reset-password-form';

const STRONG = 'Correct-Horse-9';

beforeEach(() => {
  vi.clearAllMocks();
  resetPassword.mockResolvedValue({ ok: true });
});

describe('🔴 what this screen must not claim', () => {
  it('never says a reset signs other devices out, because it does not', () => {
    /**
     * ⛔ **Worse than unsupported — false.** `lib/auth/server.ts` does not set
     * `revokeSessionsOnPasswordReset`, so other sessions survive. **Printing
     * it would tell somebody who has just been compromised that they are
     * safe**, which is the most expensive place in the product to be wrong.
     */
    render(<ResetPasswordForm token="t" email="m.reinhardt@northwind.com" />);

    expect(screen.queryByText(/signs you out|other devices|iPad/i)).not.toBeInTheDocument();
  });

  it('never prints a device count it cannot produce', () => {
    // Nothing lists sessions and nothing records a device.
    render(<ResetPasswordForm token="t" email={null} />);

    expect(screen.queryByText(/\d+ other/i)).not.toBeInTheDocument();
  });
});

describe('the screen the design draws', () => {
  it('names the address the link was for', () => {
    render(<ResetPasswordForm token="t" email="m.reinhardt@northwind.com" />);

    expect(screen.getByText('m.reinhardt@northwind.com')).toBeVisible();
  });

  it('asks twice and refuses a mismatch before the network', async () => {
    // ⚡ **This screen's own rule, not the server's.** A mistyped password on
    // a screen with no way back is a lockout, and it cannot be seen.
    const user = userEvent.setup();
    render(<ResetPasswordForm token="t" email={null} />);

    await user.type(screen.getByLabelText('New password'), STRONG);
    await user.type(screen.getByLabelText('Confirm password'), 'Correct-Horse-8');
    await user.click(screen.getByRole('button', { name: 'Update password' }));

    expect(resetPassword).not.toHaveBeenCalled();
    expect(screen.getByText('Both passwords need to match.')).toBeVisible();
    expect(screen.getByLabelText('Confirm password')).toHaveFocus();
  });

  it('sends a matching pair and lands on the success screen', async () => {
    const user = userEvent.setup();
    render(<ResetPasswordForm token="a-real-token" email={null} />);

    await user.type(screen.getByLabelText('New password'), STRONG);
    await user.type(screen.getByLabelText('Confirm password'), STRONG);
    await user.click(screen.getByRole('button', { name: 'Update password' }));

    expect(resetPassword).toHaveBeenCalledWith('a-real-token', STRONG);
    expect(push).toHaveBeenCalledWith('/reset/done');
  });

  it('reports the strength of what is typed, and still does not gate on it', async () => {
    // The same judgement as screen 06: the list reports, it never refuses.
    const user = userEvent.setup();
    render(<ResetPasswordForm token="t" email={null} />);

    await user.type(screen.getByLabelText('New password'), 'anappleadayxx');
    await user.type(screen.getByLabelText('Confirm password'), 'anappleadayxx');
    expect(screen.getByRole('meter', { name: 'Password strength' })).toHaveAttribute(
      'aria-valuenow',
      '1',
    );

    await user.click(screen.getByRole('button', { name: 'Update password' }));
    expect(resetPassword).toHaveBeenCalledOnce();
  });
});
