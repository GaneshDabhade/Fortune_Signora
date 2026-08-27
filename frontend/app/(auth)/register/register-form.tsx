'use client';

import { useRouter } from 'next/navigation';
import { useMemo, useRef, useState } from 'react';

import { Button, Input, PasswordField, PasswordStrength, evaluatePassword } from '@/components/ui';
import { MINIMUM_PASSWORD_LENGTH } from '@/lib/auth/password';
import { signUpWithPassword } from '@/lib/auth/client';

/**
 * **Screen `06 · Create account`**, rebuilt from
 * `docs/design-snapshot/screens/Fortune Signora Authentication.dc.html`.
 *
 * ⛔ **Rebuilt, not refined.** [D-154](../../../../docs/DECISION_REGISTER.md)
 * forbids iterating from the legacy screen in terms, and this one differed in
 * every measurement the design states: three fields against the design's
 * three but named differently, no strength meter, no legal line, a hint
 * sentence in place of the rule list, and a submit labelled *Create account*
 * where the design says **Continue** — because it is step 1 of 2 and the
 * account is not finished when it is pressed.
 *
 * ⚠️ **What the design draws that this does not build, and why.**
 *
 * * **The fourth password rule, *Not found in a breach corpus*** — real, and
 *   out of this row's budget. See `components/ui/password-strength.tsx`.
 * * **The domain-already-has-a-workspace branch** — *"a work email on a
 *   domain that already has a workspace is offered a request to join instead
 *   of a second workspace."* **Nothing behind it exists**, verified rather
 *   than assumed: `Workspace` carries no domain, none of `workspace_tenancy`'s
 *   twenty routes is a request-to-join, and the same absence already stopped
 *   the request-access route on `/join` (`tests/components/join.test.tsx`).
 *   ⚡ **And the lookup would have to answer an unauthenticated caller**,
 *   which makes *"does this company use Signora?"* answerable by anyone with
 *   the sign-up form — a disclosure worth a ruling rather than a lane's
 *   judgement.
 */
export function SignUpForm() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const nameRef = useRef<HTMLInputElement>(null);
  const emailRef = useRef<HTMLInputElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);
  const [fieldError, setFieldError] = useState<'name' | 'email' | 'password' | null>(null);
  const [fieldMessage, setFieldMessage] = useState<string | null>(null);

  const rules = useMemo(() => evaluatePassword(password), [password]);

  /**
   * **The design's 2.4.3 — focus lands on the first invalid field**, not on a
   * summary the person then has to hunt the field from. Only the rules the
   * server actually enforces are checked here: a form that refused a password
   * for lacking a capital letter would be enforcing a rule the platform
   * deliberately does not have.
   */
  const firstProblem = ():
    | { field: 'name' | 'email' | 'password'; message: string }
    | null => {
    if (!name.trim()) return { field: 'name', message: 'Enter your full name.' };
    if (!email.trim())
      return { field: 'email', message: 'Enter the work email address you use for Signora.' };
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))
      return { field: 'email', message: 'Enter a work email address.' };
    if (password.length < MINIMUM_PASSWORD_LENGTH)
      return {
        field: 'password',
        message: `Your password needs at least ${MINIMUM_PASSWORD_LENGTH} characters.`,
      };
    return null;
  };

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();

    const problem = firstProblem();
    if (problem) {
      setFieldError(problem.field);
      setFieldMessage(problem.message);
      const target =
        problem.field === 'name' ? nameRef : problem.field === 'email' ? emailRef : passwordRef;
      target.current?.focus();
      return;
    }

    setFieldError(null);
    setFieldMessage(null);
    setPending(true);
    setError(null);

    const result = await signUpWithPassword(name, email, password);
    if (result.ok) {
      router.push(`/verify?email=${encodeURIComponent(email)}`);
      return;
    }
    setError(result.error ?? null);
    setPending(false);
  };

  return (
    <form onSubmit={submit} noValidate className="flex flex-col gap-4">
      {/**
        * 🔴 **The same error was announced TWICE, and one of them was
        * assertive** — 📁 [C-1571](../../../../docs/LANE_COORDINATION.md).
        *
        * ⛔ **This `sr-only` polite region announced it, and a separate
        * `role="alert"` below announced it again** — so a screen-reader user
        * heard the sentence twice, **the second time as an interruption.**
        *
        * ⚠️ **The comment that stood here already said why that is wrong** —
        * *"`role="alert"` would interrupt somebody mid-field"* — **while the
        * file did it thirty-five lines later.** 📁 §17 `3.3.1` (*"announced
        * politely"*) and `System States` `4.1.3` (*"only a state that ends the
        * session announces assertively"*), and a failed registration ends
        * nothing.
        *
        * ✅ **One element, which is `signin-form.tsx`'s shape** — the sibling
        * screen that got this right: **`sr-only` when there is nothing to say,
        * and the visible error itself when there is.** ⚡ **One node, one
        * announcement, and the visible text and the announced text cannot
        * drift apart because they are the same node.**
        */}
      <p
        aria-live="polite"
        className={
          error === null ? 'sr-only' : 'text-sm text-danger'
        }
      >
        {error ?? ''}
      </p>

      <Input
        ref={nameRef}
        label="Full name"
        autoComplete="name"
        value={name}
        onChange={(event) => setName(event.target.value)}
        {...(fieldError === 'name' && fieldMessage ? { error: fieldMessage } : {})}
      />

      <Input
        ref={emailRef}
        label="Work email"
        type="email"
        autoComplete="email"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        {...(fieldError === 'email' && fieldMessage ? { error: fieldMessage } : {})}
      />

      <div>
        <PasswordField
          ref={passwordRef}
          autoComplete="new-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          {...(fieldError === 'password' && fieldMessage ? { error: fieldMessage } : {})}
        />
        <PasswordStrength rules={rules} />
      </div>

      {/* ⚡ **`w-full` is the design's *width fixed*, not a layout preference.**
          The button's Loading spec is *"label kept, width fixed"* — and this
          label grows from **Continue** to **Creating your account…**, so an
          intrinsically-sized button would jump the moment it is pressed. **The
          card must not reflow while somebody waits.** */}
      <Button type="submit" className="w-full" disabled={pending}>
        {pending ? 'Creating your account…' : 'Continue'}
      </Button>
    </form>
  );
}
