/**
 * **Screen `08 · Reset your password`** — Workflow 4, [TASK-487](../../../docs/BACKLOG.md).
 *
 * ⚡ **Almost every test here is the same property stated a different way:
 * the screen must not tell anybody whether an account exists.** It is the one
 * page nobody has to authenticate to reach, so a form that distinguished a
 * known address from an unknown one would be an enumeration oracle open to
 * the internet.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const requestPasswordReset = vi.hoisted(() => vi.fn());
vi.mock('@/lib/auth/client', () => ({
  requestPasswordReset: (...args: unknown[]) => requestPasswordReset(...args),
}));

import { ForgotPasswordForm } from '@/app/(auth)/forgot-password/forgot-password-form';

const KNOWN = 'm.reinhardt@northwind.com';
const UNKNOWN = 'nobody.at.all@northwind.example';

beforeEach(() => {
  vi.clearAllMocks();
  requestPasswordReset.mockResolvedValue({ ok: true });
});

async function request(address: string) {
  const user = userEvent.setup();
  await user.type(screen.getByLabelText('Work email'), address);
  await user.click(screen.getByRole('button', { name: 'Send reset link' }));
}

describe('🔴 the screen never reveals whether an account exists', () => {
  it('answers a known address and an unknown one with the same words', async () => {
    /**
     * **The single most important assertion in this workflow**, and the row
     * names it: *"the response must be identical for a known and an unknown
     * address — that is an account-enumeration property."*
     */
    render(<ForgotPasswordForm />);
    await request(KNOWN);
    const known = (await screen.findByRole('status')).textContent;

    requestPasswordReset.mockResolvedValue({
      ok: false,
      error: 'There is no account for that address.',
    });
    render(<ForgotPasswordForm />);
    await request(UNKNOWN);
    const unknown = screen.getAllByRole('status').at(-1)?.textContent;

    expect(unknown).toEqual(known);
  });

  it('⛔ never renders what the server said about the address', async () => {
    // Even a truthful refusal is an oracle here. It is withheld deliberately.
    requestPasswordReset.mockResolvedValue({
      ok: false,
      error: 'There is no account for that address.',
    });
    render(<ForgotPasswordForm />);

    await request(UNKNOWN);

    expect(screen.queryByText(/no account/i)).not.toBeInTheDocument();
  });

  it('states the condition rather than implying a send', async () => {
    // *"If an account exists…"* — true either way, which is the point.
    render(<ForgotPasswordForm />);
    await request(KNOWN);

    expect(await screen.findByRole('status')).toHaveTextContent(/if an account exists/i);
  });
});

describe('the screen the design draws', () => {
  it('asks for a work email and sends a reset link', () => {
    render(<ForgotPasswordForm />);

    expect(screen.getByLabelText('Work email')).toBeVisible();
    expect(screen.getByRole('button', { name: 'Send reset link' })).toBeVisible();
  });

  it('a malformed address never reaches the network', async () => {
    render(<ForgotPasswordForm />);
    await request('not-an-address');

    expect(requestPasswordReset).not.toHaveBeenCalled();
    expect(screen.getByText('Enter a work email address.')).toBeVisible();
    expect(screen.getByLabelText('Work email')).toHaveFocus();
  });

  it('holds the button width while sending', async () => {
    // The design's Loading spec — *"label kept, width fixed"*.
    let release: (v: { ok: true }) => void = () => {};
    requestPasswordReset.mockReturnValue(new Promise<{ ok: true }>((r) => (release = r)));
    render(<ForgotPasswordForm />);

    await request(KNOWN);
    const sending = await screen.findByRole('button', { name: 'Sending…' });
    expect(sending).toBeDisabled();
    expect(sending).toHaveClass('w-full');

    release({ ok: true });
  });
});

describe('⚠️ the expiry it prints is the expiry the platform has', () => {
  it('🔴 prints the number `lib/auth/server.ts` actually configures', async () => {
    /**
     * ⚡ **This asserts the *pairing*, not the number** — [C-243](../../../docs/LANE_COORDINATION.md),
     * ruled [D-185](../../../docs/DECISION_REGISTER.md) §1.
     *
     * ⛔ **Either half alone is a defect, and they are in different files.**
     * The configuration without the copy leaves a screen understating a
     * credential's life; the copy without the configuration restores exactly
     * the lie this screen refused to print for four workflows. ⚡ **So the
     * expected sentence is *derived* from the configured seconds rather than
     * typed beside them** — changing one number alone fails here, which is
     * the only way a pairing survives the person who did not read the ruling.
     *
     * ⚠️ **This screen printed *an hour* until 2026-08-08 and this test
     * asserted it.** That was correct then: nothing configured the value and
     * `better-auth` defaults to `3600`. **The ruling moved the platform, so
     * the test moved with it** — it was never asserting sixty minutes, it was
     * asserting truthfulness.
     */
    const server = readFileSync(join(process.cwd(), 'lib/auth/server.ts'), 'utf8');
    const seconds = Number(/resetPasswordTokenExpiresIn:\s*(\d+)/.exec(server)?.[1]);
    expect(seconds).toBe(1800);

    render(<ForgotPasswordForm />);
    await request(KNOWN);

    const confirmation = await screen.findByRole('status');
    expect(confirmation).toHaveTextContent(
      new RegExp(`expires in ${seconds / 60} minutes`, 'i'),
    );
    expect(confirmation).not.toHaveTextContent(/an hour/i);
  });

  it('says the link works once', async () => {
    render(<ForgotPasswordForm />);
    await request(KNOWN);

    expect(await screen.findByRole('status')).toHaveTextContent(/works once/i);
  });
});
