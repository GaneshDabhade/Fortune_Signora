/**
 * **Screen `06 · Create account`** — Workflow 2, [TASK-485](../../../docs/BACKLOG.md).
 *
 * ⚡ **The tests are mostly about the password block**, because that is where
 * the design and the platform disagree and where a screen most easily starts
 * lying. The design draws four rules; `lib/auth/password.ts` records a
 * reviewed decision that **length is the only *requirement***; and the backlog
 * row calls the block a *"password **strength** list"*. **So the list reports
 * and does not gate**, and these assert both halves of that — the reporting is
 * live and true, and the gate is absent.
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { MINIMUM_PASSWORD_LENGTH } from '@/lib/auth/password';

const push = vi.hoisted(() => vi.fn());
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push, refresh: vi.fn(), prefetch: vi.fn() }),
}));

const signUpWithPassword = vi.hoisted(() => vi.fn());
vi.mock('@/lib/auth/client', () => ({
  signUpWithPassword: (...args: unknown[]) => signUpWithPassword(...args),
}));

import { SignUpForm } from '@/app/(auth)/sign-up/sign-up-form';

/** Satisfies every rule the meter can evaluate **and** the enforced minimum. */
const STRONG = 'Correct-Horse-9';

beforeEach(() => {
  vi.clearAllMocks();
  signUpWithPassword.mockResolvedValue({ ok: true });
});

describe('the strength list reports what is true of the typed string', () => {
  it('starts with nothing met, because nothing has been typed', () => {
    render(<SignUpForm />);

    expect(screen.getByRole('meter', { name: 'Password strength' })).toHaveAttribute(
      'aria-valuenow',
      '0',
    );
  });

  it('counts the length rule the moment the password is long enough', async () => {
    render(<SignUpForm />);
    const meter = screen.getByRole('meter', { name: 'Password strength' });

    await userEvent.type(screen.getByLabelText('Password'), 'a'.repeat(MINIMUM_PASSWORD_LENGTH - 1));
    expect(meter).toHaveAttribute('aria-valuenow', '0');

    await userEvent.type(screen.getByLabelText('Password'), 'a');
    expect(meter).toHaveAttribute('aria-valuenow', '1');
  });

  it('evaluates case and symbol independently of length', async () => {
    // Three rules, and each has to be its own answer — a meter that moved in
    // lockstep would be a length bar wearing three labels.
    render(<SignUpForm />);
    const meter = screen.getByRole('meter', { name: 'Password strength' });

    await userEvent.type(screen.getByLabelText('Password'), 'aB');
    expect(meter).toHaveAttribute('aria-valuenow', '1'); // case only

    await userEvent.type(screen.getByLabelText('Password'), '9');
    expect(meter).toHaveAttribute('aria-valuenow', '2'); // case + symbol
  });

  it('names each rule in the design\'s own words', () => {
    render(<SignUpForm />);

    expect(screen.getByText(`At least ${MINIMUM_PASSWORD_LENGTH} characters`)).toBeVisible();
    expect(screen.getByText('Upper and lower case')).toBeVisible();
    expect(screen.getByText('A number or symbol')).toBeVisible();
  });

  it('announces politely, never as an alert', () => {
    // It changes on every keystroke. `role="alert"` would interrupt a
    // screen-reader user mid-word, which is 3.3.1's whole point.
    render(<SignUpForm />);

    const list = screen.getByText('Upper and lower case').closest('ul');
    expect(list).toHaveAttribute('aria-live', 'polite');
  });
});

describe('what the list does not claim', () => {
  it('⛔ never draws the breach rule, because nothing checks it', () => {
    /**
     * **The design's fourth rule — *Not found in a breach corpus*.** Better
     * Auth 1.6.25 ships `haveIBeenPwned` and it is genuinely implementable,
     * but the plugin hooks `password.hash` **on the server** and TASK-485 says
     * in terms that nothing in this row touches `lib/auth/server.ts`.
     *
     * ⛔ **So it is raised, not drawn.** A row a client could only guess at
     * would be a rule the product does not check painted as one it does —
     * [D-156](../../../docs/DECISION_REGISTER.md) ④.
     */
    render(<SignUpForm />);

    expect(screen.queryByText(/breach/i)).not.toBeInTheDocument();
  });

  it('⛔ does not gate the form on a rule the platform does not enforce', async () => {
    /**
     * **The single most important assertion on this screen.** `password.ts`
     * records the position — *"composition rules push people toward
     * `Passw0rd!`, which is less entropy in a longer costume"* — so refusing
     * a long lowercase password would be **this lane inventing a security
     * rule the product never adopted.**
     */
    render(<SignUpForm />);

    await userEvent.type(screen.getByLabelText('Full name'), 'Marta Reinhardt');
    await userEvent.type(screen.getByLabelText('Work email'), 'm.reinhardt@northwind.com');
    // Long enough, and it satisfies neither composition rule.
    await userEvent.type(screen.getByLabelText('Password'), 'anappleadayxx');
    await userEvent.click(screen.getByRole('button', { name: 'Continue' }));

    expect(screen.getByRole('meter', { name: 'Password strength' })).toHaveAttribute(
      'aria-valuenow',
      '1',
    );
    expect(signUpWithPassword).toHaveBeenCalledOnce();
  });

  it('does enforce the one rule the server enforces, before the network', async () => {
    render(<SignUpForm />);

    await userEvent.type(screen.getByLabelText('Full name'), 'Marta Reinhardt');
    await userEvent.type(screen.getByLabelText('Work email'), 'm.reinhardt@northwind.com');
    await userEvent.type(screen.getByLabelText('Password'), 'Short-9');
    await userEvent.click(screen.getByRole('button', { name: 'Continue' }));

    expect(signUpWithPassword).not.toHaveBeenCalled();
    expect(
      screen.getByText(`Your password needs at least ${MINIMUM_PASSWORD_LENGTH} characters.`),
    ).toBeVisible();
    expect(screen.getByLabelText('Password')).toHaveFocus();
  });
});

describe('the form the design draws', () => {
  it('asks for the three fields the design names, and no others', () => {
    render(<SignUpForm />);

    expect(screen.getByLabelText('Full name')).toBeVisible();
    expect(screen.getByLabelText('Work email')).toBeVisible();
    expect(screen.getByLabelText('Password')).toBeVisible();
  });

  it('submits with Continue, because the account is not finished here', () => {
    // *"Step 1 of 2"* — the design's own label. **Create account** would
    // promise the journey ends at this button; verification follows it.
    render(<SignUpForm />);

    expect(screen.getByRole('button', { name: 'Continue' })).toBeVisible();
    expect(screen.queryByRole('button', { name: 'Create account' })).not.toBeInTheDocument();
  });

  it('autocompletes so a password manager fills the whole form', () => {
    // The design's 1.3.5. `new-password` is what makes a manager *offer* to
    // generate one rather than suggest the password being reused.
    render(<SignUpForm />);

    expect(screen.getByLabelText('Full name')).toHaveAttribute('autocomplete', 'name');
    expect(screen.getByLabelText('Work email')).toHaveAttribute('autocomplete', 'email');
    expect(screen.getByLabelText('Password')).toHaveAttribute('autocomplete', 'new-password');
  });

  it('takes focus to the first field that is wrong, in order', async () => {
    // 2.4.3 — and *in order*: an empty form has three problems and the person
    // is sent to the first, not to whichever check happened to run last.
    render(<SignUpForm />);

    await userEvent.click(screen.getByRole('button', { name: 'Continue' }));
    expect(screen.getByLabelText('Full name')).toHaveFocus();

    await userEvent.type(screen.getByLabelText('Full name'), 'Marta Reinhardt');
    await userEvent.click(screen.getByRole('button', { name: 'Continue' }));
    expect(screen.getByLabelText('Work email')).toHaveFocus();
  });

  it('a malformed address never reaches the network', async () => {
    render(<SignUpForm />);

    await userEvent.type(screen.getByLabelText('Full name'), 'Marta Reinhardt');
    await userEvent.type(screen.getByLabelText('Work email'), 'not-an-address');
    await userEvent.click(screen.getByRole('button', { name: 'Continue' }));

    expect(signUpWithPassword).not.toHaveBeenCalled();
    expect(screen.getByText('Enter a work email address.')).toBeVisible();
  });

  it('the password can be revealed and hidden by keyboard', async () => {
    // The shared `PasswordField`, reached through the screen that now uses it.
    render(<SignUpForm />);
    const password = screen.getByLabelText('Password');

    expect(password).toHaveAttribute('type', 'password');
    await userEvent.click(screen.getByRole('button', { name: 'Show' }));
    expect(password).toHaveAttribute('type', 'text');
    expect(screen.getByRole('button', { name: 'Hide' })).toHaveAttribute('aria-pressed', 'true');
  });

  it('sends a new account to verification, carrying the address', async () => {
    render(<SignUpForm />);

    await userEvent.type(screen.getByLabelText('Full name'), 'Marta Reinhardt');
    await userEvent.type(screen.getByLabelText('Work email'), 'm.reinhardt@northwind.com');
    await userEvent.type(screen.getByLabelText('Password'), STRONG);
    await userEvent.click(screen.getByRole('button', { name: 'Continue' }));

    expect(signUpWithPassword).toHaveBeenCalledWith(
      'Marta Reinhardt',
      'm.reinhardt@northwind.com',
      STRONG,
    );
    expect(push).toHaveBeenCalledWith('/verify-email?email=m.reinhardt%40northwind.com');
  });

  it('repeats the server\'s refusal rather than rewriting it', async () => {
    signUpWithPassword.mockResolvedValue({ ok: false, error: 'An account with that email exists.' });
    render(<SignUpForm />);

    await userEvent.type(screen.getByLabelText('Full name'), 'Marta Reinhardt');
    await userEvent.type(screen.getByLabelText('Work email'), 'm.reinhardt@northwind.com');
    await userEvent.type(screen.getByLabelText('Password'), STRONG);
    await userEvent.click(screen.getByRole('button', { name: 'Continue' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('An account with that email exists.');
    expect(push).not.toHaveBeenCalled();
  });
});
