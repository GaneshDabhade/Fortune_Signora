'use client';

import { useRouter } from 'next/navigation';
import { useMemo, useRef, useState } from 'react';

import { Button, PasswordField, PasswordStrength, evaluatePassword } from '@/components/ui';
import { MINIMUM_PASSWORD_LENGTH } from '@/lib/auth/password';
import { resetPassword } from '@/lib/auth/client';

/**
 * **Screen `09 · Set a new password`** — [TASK-488](../../../../docs/BACKLOG.md).
 *
 * ⚡ **Composed, not rebuilt.** `PasswordField` and `PasswordStrength` are the
 * library components Workflow 2 put into `components/ui` precisely because
 * this screen and screen `06` need the same controls — §20c's *add to the
 * library, never beside it*, paying off one workflow later.
 *
 * ### ⛔ The sentence this screen does not print
 *
 * **The design says: *"This signs you out of 4 other devices, including the
 * iPad last used 3 days ago."*** ⛔ **Both halves are unsupported and the
 * first is worse than unsupported — it is false.**
 *
 * * **Nothing is signed out.** `revokeSessionsOnPasswordReset` is a Better
 *   Auth option and `lib/auth/server.ts` does not set it, so the default
 *   applies and other sessions survive a reset. **Printing the sentence would
 *   tell somebody who has just been compromised that they are safe.**
 * * **And the count could not be produced anyway** — nothing lists sessions
 *   and nothing records a device, so *"4"* and *"the iPad"* have no source.
 *
 * ✅ **Raised as [C-244](../../../../docs/LANE_COORDINATION.md).** ⛔ **Enabling
 * revocation is `lib/auth/server.ts`, which this row states it does not
 * touch** — and it is a security *behaviour*, not a copy fix.
 */
export function ResetPasswordForm({ token, email }: { token: string; email: string | null }) {
  const router = useRouter();
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [fieldError, setFieldError] = useState<'password' | 'confirm' | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const passwordRef = useRef<HTMLInputElement>(null);
  const confirmRef = useRef<HTMLInputElement>(null);
  const rules = useMemo(() => evaluatePassword(password), [password]);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();

    // Only what the server enforces, for the reason `password.ts` records:
    // composition rules push people toward `Passw0rd!`, which is less entropy
    // in a longer costume. The strength list reports; it does not gate.
    if (password.length < MINIMUM_PASSWORD_LENGTH) {
      setFieldError('password');
      setMessage(`Your password needs at least ${MINIMUM_PASSWORD_LENGTH} characters.`);
      passwordRef.current?.focus();
      return;
    }
    // ⚡ **The confirm field is this screen's own rule, not the server's.** It
    // exists because a mistyped password on a screen with no *"forgot"* route
    // back is a lockout, and the person cannot see what they typed.
    if (confirm !== password) {
      setFieldError('confirm');
      setMessage('Both passwords need to match.');
      confirmRef.current?.focus();
      return;
    }

    setFieldError(null);
    setMessage(null);
    setPending(true);
    setError(null);

    const result = await resetPassword(token, password);
    if (result.ok) {
      router.push('/reset/done');
      return;
    }
    setError(result.error ?? null);
    setPending(false);
  };

  return (
    <form onSubmit={submit} noValidate className="flex flex-col gap-4">
      <p aria-live="polite" className="sr-only">
        {error ?? ''}
      </p>

      {email ? (
        <p className="text-sm leading-6 text-content-muted">
          for <span className="font-medium text-content">{email}</span>
        </p>
      ) : null}

      <div>
        <PasswordField
          ref={passwordRef}
          label="New password"
          autoComplete="new-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          {...(fieldError === 'password' && message ? { error: message } : {})}
        />
        <PasswordStrength rules={rules} />
      </div>

      <PasswordField
        ref={confirmRef}
        label="Confirm password"
        autoComplete="new-password"
        value={confirm}
        onChange={(event) => setConfirm(event.target.value)}
        {...(fieldError === 'confirm' && message ? { error: message } : {})}
      />

      {error ? (
        <p role="alert" className="text-sm text-danger">
          {error}
        </p>
      ) : null}

      <Button type="submit" className="w-full" disabled={pending}>
        {pending ? 'Updating…' : 'Update password'}
      </Button>
    </form>
  );
}
