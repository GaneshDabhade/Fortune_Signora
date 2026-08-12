/**
 * **§03 · Second factors and enrolment** — [TASK-1414](../../../docs/BACKLOG.md).
 *
 * 🔴 **The row's Playwright coverage says *"the backup codes are shown exactly
 * once"*.** ⚡ **Exactly once is not a rendering fact and cannot be asserted by
 * looking at one screen** — **it is asserted here by the absence of any call
 * that could ask for them again.**
 */
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const enable = vi.hoisted(() => vi.fn());
const verifyTotp = vi.hoisted(() => vi.fn());
const disable = vi.hoisted(() => vi.fn());

vi.mock('@/lib/auth/client', () => ({
  authClient: { twoFactor: { enable, verifyTotp, disable } },
}));

import { FactorsPanel } from '@/app/(app)/profile/security/factors-panel';
import { groupInFours, manualKeyFrom } from '@/app/(app)/profile/security/enrolment';

const TOTP_URI = 'otpauth://totp/Signora:a@b.com?secret=JBSWY3DPEHPK3PXP&issuer=Signora';

beforeEach(() => {
  vi.clearAllMocks();
  enable.mockResolvedValue({
    error: null,
    data: { totpURI: TOTP_URI, backupCodes: ['4H8K-92QX', '7TPM-3F1A', 'QW5R-88LZ'] },
  });
  verifyTotp.mockResolvedValue({ error: null });
  disable.mockResolvedValue({ error: null });
});

describe('⛔ what is drawn is what can be enrolled', () => {
  /**
   * 📁 **The design lists five methods.** ⛔ **Three of them — passkey, push and
   * SMS — do not exist in this product**, and drawing them greyed out is the
   * false-affordance class.
   */
  it('🔴 the three unbuildable methods are absent, not disabled', () => {
    render(<FactorsPanel twoFactorEnabled hasPassword />);

    const rows = within(screen.getByTestId('factor-list')).getAllByRole('listitem');

    // ⚠️ **Asserted against the ROWS, not against the words.** ⛔ *"weaker than
    // a passkey"* appears in the design's own explanation of TOTP, so a
    // document-wide search for `passkey` would fail on prose that is correct.
    expect(rows.map((row) => row.querySelector('span')?.textContent)).toEqual([
      'Authenticator app',
      'Backup codes',
    ]);
  });

  it('✅ each method states its resistance class beside it, rather than by position', () => {
    render(<FactorsPanel twoFactorEnabled hasPassword />);

    const rows = within(screen.getByTestId('factor-list')).getAllByRole('listitem');
    expect(rows[0]).toHaveTextContent('Codes');
    expect(rows[1]).toHaveTextContent('Last resort');
  });

  /**
   * ⚡ **An account with no second factor is not an empty list.** ⛔ **On this
   * page the absence IS the finding**, and *"no methods"* reads as a neutral
   * fact about a screen rather than a fact about the reader's exposure.
   */
  it('🔴 no second factor reads as exposure, never as an empty list', () => {
    render(<FactorsPanel twoFactorEnabled={false} hasPassword />);

    expect(screen.getByTestId('no-factors')).toHaveTextContent('only thing standing between');
  });
});

describe('🔴 enrolment', () => {
  /**
   * ⛔ **An account whose password lives elsewhere cannot enrol here**, and it
   * is TOLD so — ⚡ **rather than shown a password field that will always be
   * refused.**
   */
  it('⛔ an SSO account is told why, and is given no form to fail at', async () => {
    render(<FactorsPanel twoFactorEnabled={false} hasPassword={false} />);

    await userEvent.click(screen.getByRole('button', { name: 'Add a method' }));

    expect(screen.getByRole('note')).toHaveTextContent('cannot add an authenticator app');
    expect(screen.queryByLabelText('Your password')).not.toBeInTheDocument();
  });

  it('✅ the password is the first step, because the framework requires it', async () => {
    render(<FactorsPanel twoFactorEnabled={false} hasPassword />);

    await userEvent.click(screen.getByRole('button', { name: 'Add a method' }));
    await userEvent.type(screen.getByLabelText('Your password'), 'hunter-two');
    await userEvent.click(screen.getByRole('button', { name: 'Continue' }));

    expect(enable).toHaveBeenCalledWith({ password: 'hunter-two' });
  });

  /**
   * ♿ 🔴 **The manual key is present on the scan step, at every width.**
   *
   * 📁 The row: *"the QR code and its manual key are both offered at every
   * width — the design's 'Cannot scan?' is not a mobile fallback, it is always
   * present"* (WCAG 2.1.1). ⚡ **Here it is the ONLY way in**, since nothing
   * renders a QR image, and that is stated in the component rather than hidden.
   */
  it('🔴 the manual key is shown, grouped in fours', async () => {
    render(<FactorsPanel twoFactorEnabled={false} hasPassword />);

    await userEvent.click(screen.getByRole('button', { name: 'Add a method' }));
    await userEvent.type(screen.getByLabelText('Your password'), 'hunter-two');
    await userEvent.click(screen.getByRole('button', { name: 'Continue' }));

    expect(await screen.findByTestId('manual-key')).toHaveTextContent('JBSW Y3DP EHPK 3PXP');
  });

  it('✅ a wrong code says the codes rotate, and does not clear what was typed', async () => {
    verifyTotp.mockResolvedValue({ error: { message: 'invalid' } });
    render(<FactorsPanel twoFactorEnabled={false} hasPassword />);

    await userEvent.click(screen.getByRole('button', { name: 'Add a method' }));
    await userEvent.type(screen.getByLabelText('Your password'), 'hunter-two');
    await userEvent.click(screen.getByRole('button', { name: 'Continue' }));
    await userEvent.click(await screen.findByRole('button', { name: 'I have added it' }));
    await userEvent.type(screen.getByLabelText('Verification code, character 1 of 6'), '000000');
    await userEvent.click(screen.getByRole('button', { name: 'Verify and continue' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('rotate every 30 seconds');
  });

  /**
   * 🔴 **Shown once, and this is the assertion for it.**
   *
   * ⚡ **The codes arrive in the `enable` response and are never asked for
   * again**: the whole flow calls `enable` exactly once, and no other call in
   * this component can return them. ⛔ **A future *"show my codes"* button would
   * turn this red**, which is the point.
   */
  it('🔴 the backup codes come from ONE call and nothing can ask for them again', async () => {
    render(<FactorsPanel twoFactorEnabled={false} hasPassword />);

    await userEvent.click(screen.getByRole('button', { name: 'Add a method' }));
    await userEvent.type(screen.getByLabelText('Your password'), 'hunter-two');
    await userEvent.click(screen.getByRole('button', { name: 'Continue' }));
    await userEvent.click(await screen.findByRole('button', { name: 'I have added it' }));
    await userEvent.type(screen.getByLabelText('Verification code, character 1 of 6'), '123456');
    await userEvent.click(screen.getByRole('button', { name: 'Verify and continue' }));

    const codes = await screen.findByTestId('backup-codes');
    expect(within(codes).getAllByRole('listitem')).toHaveLength(3);
    expect(enable).toHaveBeenCalledTimes(1);

    // ⛔ **And they are gone the moment the flow ends.**
    await userEvent.click(screen.getByRole('button', { name: 'I have saved them' }));
    await userEvent.click(screen.getByRole('button', { name: 'Done' }));

    expect(screen.queryByTestId('backup-codes')).not.toBeInTheDocument();
  });

  it('♿ the codes are text a person can select and download, never an image', async () => {
    render(<FactorsPanel twoFactorEnabled={false} hasPassword />);

    await userEvent.click(screen.getByRole('button', { name: 'Add a method' }));
    await userEvent.type(screen.getByLabelText('Your password'), 'hunter-two');
    await userEvent.click(screen.getByRole('button', { name: 'Continue' }));
    await userEvent.click(await screen.findByRole('button', { name: 'I have added it' }));
    await userEvent.type(screen.getByLabelText('Verification code, character 1 of 6'), '123456');
    await userEvent.click(screen.getByRole('button', { name: 'Verify and continue' }));

    expect(await screen.findByText('4H8K-92QX')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Download .txt' })).toHaveAttribute(
      'download',
      'signora-backup-codes.txt',
    );
    expect(screen.queryByRole('img')).not.toBeInTheDocument();
  });
});

describe('🔴 removal states its blast radius and the server holds the gate', () => {
  it('⛔ the consequence is on screen BEFORE the control that fires it', async () => {
    render(<FactorsPanel twoFactorEnabled hasPassword />);

    await userEvent.click(screen.getByRole('button', { name: 'Remove' }));

    const confirm = screen.getByTestId('remove-factor');
    expect(confirm).toHaveTextContent('leaves Backup codes');
    expect(within(confirm).getByRole('button', { name: 'Remove it' })).toBeInTheDocument();
  });

  it('✅ the password reaches the framework, which is where the challenge is enforced', async () => {
    render(<FactorsPanel twoFactorEnabled hasPassword />);

    await userEvent.click(screen.getByRole('button', { name: 'Remove' }));
    await userEvent.type(screen.getByLabelText('Your password'), 'hunter-two');
    await userEvent.click(screen.getByRole('button', { name: 'Remove it' }));

    expect(disable).toHaveBeenCalledWith({ password: 'hunter-two' });
  });

  it('⛔ a refused password keeps the factor and says so', async () => {
    disable.mockResolvedValue({ error: { message: 'Invalid password' } });
    render(<FactorsPanel twoFactorEnabled hasPassword />);

    await userEvent.click(screen.getByRole('button', { name: 'Remove' }));
    await userEvent.type(screen.getByLabelText('Your password'), 'wrong');
    await userEvent.click(screen.getByRole('button', { name: 'Remove it' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Invalid password');
    expect(screen.getByTestId('factor-list')).toBeInTheDocument();
  });
});

describe('⚡ the secret is read out of the URI rather than stored twice', () => {
  it('✅ pulls the secret from an otpauth URI', () => {
    expect(manualKeyFrom(TOTP_URI)).toBe('JBSWY3DPEHPK3PXP');
  });

  it('✅ groups in fours for the ear as well as the eye', () => {
    expect(groupInFours('JBSWY3DPEHPK3PXP')).toBe('JBSW Y3DP EHPK 3PXP');
  });
});
