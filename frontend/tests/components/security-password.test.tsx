/**
 * **§02 · Password, and the SSO state the row warns about** —
 * [TASK-1414](../../../docs/BACKLOG.md).
 *
 * ⚠️ **The row names the risk in terms**: *"Rendering the SSO-managed password
 * state as a disabled field. The design sends the person to their provider with
 * a working link; a disabled field is the false affordance class again."*
 * 🔴 **So the link is asserted, and so is its absence when there is nowhere
 * honest to send somebody.**
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const changePassword = vi.hoisted(() => vi.fn());
vi.mock('@/lib/auth/client', () => ({ authClient: { changePassword } }));

import { PasswordPanel } from '@/app/(app)/profile/security/password-panel';

beforeEach(() => {
  vi.clearAllMocks();
  changePassword.mockResolvedValue({ error: null });
});

describe('🔴 when the password lives with an identity provider', () => {
  it('✅ shows the form disabled AND says where the password actually lives', () => {
    render(<PasswordPanel ssoProvider="google" />);

    expect(screen.getByText(/never receives, stores or verifies your password/)).toBeInTheDocument();
    const link = screen.getByRole('link', { name: 'Change password at Google' });
    expect(link).toHaveAttribute('href', 'https://myaccount.google.com/security');
  });

  /**
   * ⛔ **A form with no way out is the whole defect the row names.** ⚡ **This
   * is the assertion that fails if somebody deletes the link and keeps the
   * disabled fields**, which is the version that looks finished.
   */
  it('🔴 the disabled fields are never the only thing on the panel', () => {
    render(<PasswordPanel ssoProvider="microsoft" />);

    expect(screen.getByRole('link', { name: /Change password at Microsoft/ })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Change password' })).not.toBeInTheDocument();
  });

  /**
   * ⛔ **An unknown provider gets NO link, and says why.** ⚡ **A button that
   * goes to a guessed address is worse than a sentence** — 📁 a dead link on a
   * security page teaches somebody the product does not know its own shape.
   */
  it('⛔ never invents an address for a provider it does not know', () => {
    render(<PasswordPanel ssoProvider="okta" />);

    expect(screen.queryByRole('link')).not.toBeInTheDocument();
    expect(screen.getByTestId('password-no-link')).toHaveTextContent('does not know that address');
  });
});

describe('🔴 when the account holds its own password', () => {
  it('✅ the strength meter reports and never gates', async () => {
    render(<PasswordPanel ssoProvider={null} />);

    await userEvent.type(screen.getByLabelText('New password'), 'a');

    // ⛔ **Weak, and the submit is still live** — 📁 [TASK-485](../../../docs/BACKLOG.md)
    // decided this and the row forbids re-deciding it here.
    expect(screen.getByRole('button', { name: 'Change password' })).toBeEnabled();
  });

  /**
   * 🔴 **The choice is a real parameter, and this is the assertion that proves
   * it.**
   *
   * 📁 ***"You choose whether that happens — keeping them is legitimate when you
   * are simply rotating a credential, and dangerous when you suspect
   * compromise, so we ask rather than assume."*** ⛔ **A radio the screen reads
   * and then ignores would pass every rendering test.**
   */
  it('🔴 the sign-out choice reaches the server, and both answers do', async () => {
    render(<PasswordPanel ssoProvider={null} />);

    await userEvent.type(screen.getByLabelText('Current password'), 'old-one');
    await userEvent.type(screen.getByLabelText('New password'), 'Correct-Horse-9');
    await userEvent.click(screen.getByRole('button', { name: 'Change password' }));

    // ✅ **The safe default, because the design names it as the default.**
    expect(changePassword).toHaveBeenCalledWith(
      expect.objectContaining({ revokeOtherSessions: true }),
    );

    // ⚡ **The fields are re-typed because a successful change clears them** —
    // ⛔ **holding a password in a field after it has been used is the state a
    // shared screen leaks**, and `required` refuses the empty form besides.
    await userEvent.click(screen.getByLabelText(/Keep my other sessions/));
    await userEvent.type(screen.getByLabelText('Current password'), 'Correct-Horse-9');
    await userEvent.type(screen.getByLabelText('New password'), 'Correct-Horse-10');
    await userEvent.click(screen.getByRole('button', { name: 'Change password' }));

    expect(changePassword).toHaveBeenLastCalledWith(
      expect.objectContaining({ revokeOtherSessions: false }),
    );
  });

  it("⛔ reports the server's own sentence rather than a paraphrase", async () => {
    changePassword.mockResolvedValue({ error: { message: 'Password is too short' } });
    render(<PasswordPanel ssoProvider={null} />);

    await userEvent.type(screen.getByLabelText('Current password'), 'old-one');
    await userEvent.type(screen.getByLabelText('New password'), 'short');
    await userEvent.click(screen.getByRole('button', { name: 'Change password' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Password is too short');
  });

  /**
   * ⚡ **The confirmation says which of the two happened.** ⛔ *"Your password
   * has been changed"* alone leaves somebody who suspects compromise unsure
   * whether the attacker is still signed in.
   */
  it('✅ says what became of the other sessions, not merely that it worked', async () => {
    render(<PasswordPanel ssoProvider={null} />);

    await userEvent.type(screen.getByLabelText('Current password'), 'old-one');
    await userEvent.type(screen.getByLabelText('New password'), 'Correct-Horse-9');
    await userEvent.click(screen.getByRole('button', { name: 'Change password' }));

    expect(await screen.findByRole('status')).toHaveTextContent('other sessions have ended');
  });
});
