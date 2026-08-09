/**
 * **Confirm it is you** — [TASK-1410](../../../docs/BACKLOG.md).
 *
 * 🔴 **The row names its own risk: *"building this as a UI dialog… it is an
 * authorization boundary that happens to have a dialog."*** ⚡ **So the case
 * that earns this file is that the dialog AUTHORISES NOTHING** — the server
 * does, via `freshAge` — **and that the prompt names what it is about to do**,
 * because 📁 *"'confirm your identity' with no object is how people approve
 * things they did not intend."*
 */
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { StepUpDialog } from '@/components/auth/step-up-dialog';

const ACTION = 'Revoke 3 sessions and 2 connected apps';

function open(overrides: Partial<React.ComponentProps<typeof StepUpDialog>> = {}) {
  const onConfirm = vi.fn().mockResolvedValue(true);
  const onDismiss = vi.fn();
  const utils = render(
    <StepUpDialog
      open
      action={ACTION}
      expiresInSeconds={292}
      onConfirm={onConfirm}
      onDismiss={onDismiss}
      {...overrides}
    />,
  );
  return { onConfirm, onDismiss, ...utils };
}

describe('🔴 the prompt states what it is about to authorise', () => {
  it('⛔ names the action, because "confirm your identity" with no object is the defect', () => {
    open();
    expect(screen.getByText(/You are about to/)).toBeInTheDocument();
    expect(screen.getByText(ACTION)).toBeInTheDocument();
  });

  // ⛔ **There is deliberately no runtime test that `action` cannot be
  // omitted.** 📁 The prop is required and `tsc` refuses the call; a runtime
  // assertion for a compile-time guarantee is Decorative Logic ([§2](../../../CLAUDE.md))
  // — it cannot fail for the reason it claims to exist. **The first draft of
  // this file had one, and it rendered a second dialog into the DOM to prove
  // something the type system had already prevented.**
});

describe('📁 the code, and its expiry is visible', () => {
  it('shows six boxes, which is otpLength and the design’s number', () => {
    open();
    expect(screen.getAllByRole('textbox')).toHaveLength(6);
  });

  it('⚡ counts down, because a silent expiry fails as a wrong code', () => {
    open({ expiresInSeconds: 292 });
    expect(screen.getByText('Expires in 4:52')).toBeInTheDocument();
  });

  it('⛔ an expired code says so and refuses Confirm', () => {
    open({ expiresInSeconds: 0 });
    expect(screen.getByText(/expired — ask for another/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Confirm' })).toBeDisabled();
  });
});

describe('🔴 a wrong code does not consume the challenge', () => {
  it('⛔ keeps the digits and stays open', async () => {
    // 📁 TASK-486's rule carried over: retyping six characters to fix one is
    // the complaint the design names. And the dialog does not close — a
    // challenge that vanishes on a typo has consumed itself.
    const user = userEvent.setup();
    const onConfirm = vi.fn().mockResolvedValue(false);
    open({ onConfirm });

    await user.click(screen.getAllByRole('textbox')[0] as HTMLElement);
    await user.paste('123456');
    await user.click(screen.getByRole('button', { name: 'Confirm' }));

    await waitFor(() => expect(screen.getByText(/did not match/)).toBeInTheDocument());
    expect(
      screen.getAllByRole('textbox').map((b) => (b as HTMLInputElement).value).join(''),
    ).toBe('123456');
  });

  it('⚡ and typing again clears the error rather than leaving it stale', async () => {
    const user = userEvent.setup();
    open({ onConfirm: vi.fn().mockResolvedValue(false) });

    await user.click(screen.getAllByRole('textbox')[0] as HTMLElement);
    await user.paste('123456');
    await user.click(screen.getByRole('button', { name: 'Confirm' }));
    await waitFor(() => expect(screen.getByText(/did not match/)).toBeInTheDocument());

    await user.click(screen.getAllByRole('textbox')[5] as HTMLElement);
    await user.keyboard('{Backspace}');
    expect(screen.queryByText(/did not match/)).not.toBeInTheDocument();
  });
});

describe('🔴 the action does not execute when the dialog is dismissed', () => {
  it('⛔ dismissing calls back and never confirms', async () => {
    // The row's Playwright line, asserted at the component level too: a
    // dismissed challenge must not authorise anything.
    // ⚠️ **Dispatched rather than typed, and the reason is the environment.**
    // `Dialog` is the native `<dialog>`, which bridges Escape to `onClose`
    // through the `cancel` event — and **jsdom does not implement
    // `showModal`**, so `{Escape}` fires nothing here. **Dispatching `cancel`
    // is what the browser does**, so this asserts the bridge that actually
    // carries the dismissal rather than jsdom's missing keyboard path.
    const { onConfirm, onDismiss, container } = open();

    const dialog = container.querySelector('dialog');
    dialog?.dispatchEvent(new Event('cancel', { cancelable: true }));

    await waitFor(() => expect(onDismiss).toHaveBeenCalled());
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it('⛔ Confirm is refused until the code is complete', async () => {
    const user = userEvent.setup();
    const { onConfirm } = open();

    await user.click(screen.getAllByRole('textbox')[0] as HTMLElement);
    await user.keyboard('123');
    expect(screen.getByRole('button', { name: 'Confirm' })).toBeDisabled();
    expect(onConfirm).not.toHaveBeenCalled();
  });
});

describe('📁 the backup path, and the time-box the person is told about', () => {
  it('offers a backup code when the caller supports one', async () => {
    const user = userEvent.setup();
    const onUseBackupCode = vi.fn();
    open({ onUseBackupCode });

    await user.click(screen.getByRole('button', { name: 'Use a backup code' }));
    expect(onUseBackupCode).toHaveBeenCalledTimes(1);
  });

  it('⛔ and offers nothing when it does not — never a control that does nothing', () => {
    open({ onUseBackupCode: undefined });
    expect(screen.queryByRole('button', { name: 'Use a backup code' })).not.toBeInTheDocument();
  });

  it('⚡ says the grant is time-boxed, because a silent one surprises people', () => {
    // 📁 "Step-up lasts 10 minutes… short enough that an unlocked laptop is
    // not a standing authorisation." The server enforces it via freshAge: 600;
    // this tells the person.
    open();
    expect(screen.getByText(/lasts 10 minutes/)).toBeInTheDocument();
  });
});
