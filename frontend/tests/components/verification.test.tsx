/**
 * **Screen `07 · Verify email`** — Workflow 3, [TASK-486](../../../docs/BACKLOG.md).
 *
 * ⚡ **The tests are about the resend, because that is what this screen can
 * honestly do.** The design draws six digit boxes; `lib/auth/server.ts` sends
 * a link and no endpoint would accept a typed code — [C-241](../../../docs/LANE_COORDINATION.md).
 * **So the boxes are not drawn, and one test asserts their absence** for the
 * same reason `join.test.tsx` asserts *Request access* is never offered.
 */
import { act, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const resendVerification = vi.hoisted(() => vi.fn());
vi.mock('@/lib/auth/client', () => ({
  resendVerification: (...args: unknown[]) => resendVerification(...args),
}));

import { ResendVerification } from '@/app/(auth)/verify-email/resend';

const ADDRESS = 'm.reinhardt@northwind.com';

beforeEach(() => {
  vi.clearAllMocks();
  resendVerification.mockResolvedValue({ ok: true });
});

afterEach(() => vi.useRealTimers());

/** Send once and let the countdown start. */
async function resendOnce(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole('button', { name: 'Resend' }));
  expect(await screen.findByRole('button', { name: /Resend in/ })).toBeInTheDocument();
}

describe('the timer the design specifies', () => {
  it('starts at 45 seconds and prints the time remaining', async () => {
    // *"The resend timer starts at 45s and doubles."* And the design's own
    // accessibility note asks for the remaining time to be shown rather than
    // the control merely being disabled.
    const user = userEvent.setup();
    render(<ResendVerification email={ADDRESS} />);

    await resendOnce(user);

    expect(screen.getByRole('button', { name: 'Resend in 0:45' })).toBeDisabled();
  });

  it('counts down in real seconds', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    render(<ResendVerification email={ADDRESS} />);

    await resendOnce(user);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(3000);
    });

    expect(screen.getByRole('button', { name: 'Resend in 0:42' })).toBeInTheDocument();
  });

  it('doubles on the second send', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    render(<ResendVerification email={ADDRESS} />);

    await resendOnce(user);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(45_000);
    });
    await resendOnce(user);

    // 45 → 90. `1:30`, printed as the design prints it.
    expect(screen.getByRole('button', { name: 'Resend in 1:30' })).toBeInTheDocument();
  });

  it('⛔ does not start the wait when the send failed', async () => {
    /**
     * **A failure that began a 45-second countdown would punish somebody for
     * the product's own error**, and leave them no way to retry.
     */
    resendVerification.mockResolvedValue({ ok: false, error: 'Could not be reached.' });
    const user = userEvent.setup();
    render(<ResendVerification email={ADDRESS} />);

    await user.click(screen.getByRole('button', { name: 'Resend' }));

    expect(await screen.findByRole('button', { name: 'Resend' })).toBeEnabled();
    expect(screen.getByText('Could not be reached.')).toBeVisible();
  });

  it('suggests spam and the corporate filter on the third send', async () => {
    // The design's own escalation: by the third attempt the likely cause is
    // not a slow queue, and saying so is more use than sending again.
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    render(<ResendVerification email={ADDRESS} />);

    for (const wait of [45_000, 90_000]) {
      await resendOnce(user);
      await act(async () => {
        await vi.advanceTimersByTimeAsync(wait);
      });
    }
    await resendOnce(user);

    expect(screen.getByText(/spam folder and ask whether your corporate filter/i)).toBeVisible();
  });

  it('says nothing about filters before then', async () => {
    const user = userEvent.setup();
    render(<ResendVerification email={ADDRESS} />);

    await resendOnce(user);

    expect(screen.queryByText(/corporate filter/i)).not.toBeInTheDocument();
    expect(screen.getByText(/check the address above/i)).toBeVisible();
  });
});

describe('what the screen does not claim', () => {
  it('⛔ never draws six code boxes, because nothing would verify them', () => {
    /**
     * **C-241.** `better-auth/plugins/email-otp` is installed and
     * unregistered; the server sends `{ user, url }`. **A control whose
     * outcome cannot depend on its input is a false affordance** — the rule
     * this lane already applied to `/join`'s *Request access* and `/sso`'s
     * domain field. **Six digits typed into a screen that cannot check them
     * is the strongest version of it: it looks like it worked until it does
     * not.**
     */
    render(<ResendVerification email={ADDRESS} />);

    expect(screen.queryByLabelText(/digit|code/i)).not.toBeInTheDocument();
    expect(screen.queryAllByRole('textbox')).toHaveLength(1);
  });

  it('keeps the address prefilled and editable', () => {
    // The most likely reader is somebody who mistyped it one screen ago.
    render(<ResendVerification email={ADDRESS} />);

    expect(screen.getByLabelText('Work email')).toHaveValue(ADDRESS);
  });

  it('announces the wait politely, never as an alert', async () => {
    // It changes every second; an interruption per second is not feedback.
    const user = userEvent.setup();
    render(<ResendVerification email={ADDRESS} />);

    await resendOnce(user);

    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(document.querySelector('[aria-live="polite"]')).toHaveTextContent(/send again in/i);
  });
});
