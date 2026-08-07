'use client';

import { useRouter } from 'next/navigation';
import { useCallback, useId, useRef, useState } from 'react';

import { Button, Input } from '@/components/ui';
import { signIn, signInWithPassword } from '@/lib/auth/client';

import { AuthLink } from '../auth-shell';
import { Authenticating, type AuthStage } from './authenticating';
import { Throttled } from './throttled';

const OAUTH_LABELS: Record<string, string> = {
  google: 'Continue with Google',
  microsoft: 'Continue with Microsoft',
};

/**
 * Sign in — **Workflow 1, milestone 2**, against
 * `docs/design-snapshot/screens/Fortune Signora Authentication.dc.html` §02–03.
 *
 * ### ⛔ Presentation replaced; everything behind it reused
 *
 * **[D-159](../../../../docs/DECISION_REGISTER.md): *"only the customer-visible
 * presentation layer is being replaced."*** So `signInWithPassword`, `signIn`,
 * the `router.refresh()`-then-`push` ordering and its hard-won comment, and
 * the configuration-driven method list are all untouched. **Better Auth
 * remains the sole Authentication Authority** ([§13](../../../../CLAUDE.md)).
 *
 * ### What changed, and it is the order
 *
 * ⚡ **The design puts providers first, then a divider, then the fields.** The
 * previous screen led with the password form on the reasoning that *"the
 * password method is the one that always works"* — sound, and not what the
 * finalized design says. **D-159 is explicit that an existing implementation
 * which does not conform is replaced rather than argued with.**
 *
 * ### The states this screen owns
 *
 * | | |
 * |---|---|
 * | **Inline validation** | Before the network is touched — an empty or malformed address is this screen's to answer |
 * | **Authentication failure** | The design's own words: *"That email and password don't match."* ⛔ **Never *"no such account"*** — *"never confirm an account exists"* is the design's second rationale and removes enumeration entirely |
 * | **Loading** | ⚡ **The label is kept and the width fixed** — the design's button spec is `label kept, width fixed`, so the card does not reflow while a person waits |
 * | **Focus** | `2.4.3` — **focus lands on the first invalid field after a failed submit** |
 * | **Announcement** | `3.3.1` — the summary is `aria-live="polite"` and announced **once, not per keystroke** |
 * | **Autocomplete** | `1.3.5` — `username` and `current-password`, so a manager fills the whole form |
 */
export function SignInForm({
  passwordEnabled,
  oauthMethods,
}: {
  passwordEnabled: boolean;
  oauthMethods: string[];
}) {
  const router = useRouter();
  const summaryId = useId();
  const emailRef = useRef<HTMLInputElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [reveal, setReveal] = useState(false);
  const [remember, setRemember] = useState(false);
  const [fieldError, setFieldError] = useState<'email' | 'password' | null>(null);
  // **The field says what to do; the summary says what happened.** The design
  // wants both (3.3.1 — *adjacent to the field* **and** a summary) and they
  // must not be the same sentence: one string in two live regions is one
  // message announced twice.
  const [fieldMessage, setFieldMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState<string | null>(null);
  // **Throttled is a state of this screen, not a route.** The design lists
  // `/throttled`, and the remaining window is a fact only the sign-in response
  // carries — a route reached by navigation would have to be *told* the
  // number by whoever sent it there, and a number a screen is told rather than
  // reads is the fabricated-data trap in its politest form.
  const [throttled, setThrottled] = useState<{ retryAfterSeconds?: number } | null>(null);
  // Design 15. `null` while the form is on screen; a stage while it is not.
  const [stage, setStage] = useState<AuthStage | null>(null);
  const attempt = useRef<AbortController | null>(null);

  // Stable, because `Throttled` holds it in a `useEffect` dependency list —
  // a fresh closure each render would restart the countdown every second.
  const resume = useCallback(() => {
    setThrottled(null);
    setError(null);
    setPending(null);
  }, []);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();

    // Inline validation first: this screen can answer an empty or malformed
    // address without a round trip, and 2.4.3 wants focus on the offending
    // field rather than on a summary the person then has to hunt from.
    if (!email.trim() || !email.includes('@')) {
      setFieldError('email');
      setFieldMessage('Enter a work email address.');
      setError('Enter the work email address you use for Signora.');
      emailRef.current?.focus();
      return;
    }
    if (!password) {
      setFieldError('password');
      setFieldMessage('Enter your password.');
      setError('Your password is needed to sign in.');
      passwordRef.current?.focus();
      return;
    }

    setFieldError(null);
    setFieldMessage(null);
    setPending('password');
    setStage('credentials');
    setError(null);

    const controller = new AbortController();
    attempt.current = controller;

    let result;
    try {
      result = await signInWithPassword(email, password, controller.signal);
    } catch {
      // **The abort lands here, and so does a dropped connection.** Both mean
      // the same thing to the person: nothing happened and the form should
      // come back. `cancel()` has already restored it in the first case, so
      // this only has to avoid leaving the card stuck on a stage.
      setStage(null);
      setPending(null);
      return;
    }

    if (result.ok) {
      // ⚡ **The second step of design 15, and it is a real one.** The refresh
      // and the navigation below are what *preparing your organization*
      // names — the server tree is rebuilt against the new session before the
      // person is moved onto it.
      setStage('organization');
      // `router.refresh()` first: the session cookie was just set, and a
      // client-side navigation alone would render the destination against a
      // server component tree that still believes nobody is signed in.
      router.refresh();
      // **`/workspaces` for three slices, and no such route has ever
      // existed** — a password sign-in landed on the not-found page. Better
      // Auth navigates to its own `callbackURL` and beats this push, so it
      // was fixed at its source in `lib/auth/client.ts`; kept here because it
      // is still the right destination when the vendor does not navigate.
      router.push('/');
      return;
    }
    // **The throttle is answered before the credential is**, because the
    // server refused the request before it evaluated anything: reporting a
    // rate limit as a credential failure tells somebody whose password is
    // correct that it is wrong, and the retry it invites extends the block.
    if (result.throttled) {
      setThrottled({ retryAfterSeconds: result.retryAfterSeconds });
      setStage(null);
      setPending(null);
      return;
    }
    setStage(null);
    // **Never *"no such account"*.** The design's second rationale: *"this
    // costs a little clarity and removes account enumeration entirely."*
    setError(result.error ?? "That email and password don't match.");
    setFieldMessage('Check this and try again.');
    setFieldError('password');
    setPending(null);
    passwordRef.current?.focus();
  };

  // ⛔ **It replaces the card rather than sitting above it.** Leaving the form
  // in place under a pause notice offers a control the server will refuse for
  // the next several seconds — and every use of it makes the wait longer.
  if (throttled) {
    return <Throttled retryAfterSeconds={throttled.retryAfterSeconds} onExpire={resume} />;
  }

  // Design 15. It renders nothing for the first 800ms, so a fast sign-in never
  // sees it and the card does not flash.
  if (stage !== null) {
    return (
      <Authenticating
        stage={stage}
        onCancel={() => {
          attempt.current?.abort();
          setStage(null);
          setPending(null);
        }}
      />
    );
  }

  if (!passwordEnabled && oauthMethods.length === 0) {
    return (
      <p className="rounded border border-warning bg-surface-raised p-3 text-sm text-content">
        No sign-in method is configured, so nobody can sign in. Enable password sign-in or
        add a provider.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-5">
      {oauthMethods.length > 0 ? (
        <div className="flex flex-col gap-2">
          {oauthMethods.map((method) => (
            <Button
              key={method}
              type="button"
              variant="secondary"
              className="w-full"
              disabled={pending !== null}
              onClick={() => {
                setPending(method);
                void signIn(method);
              }}
            >
              {OAUTH_LABELS[method] ?? `Continue with ${method}`}
            </Button>
          ))}
        </div>
      ) : null}

      {oauthMethods.length > 0 && passwordEnabled ? (
        // The divider is decorative; the word is not read out twice because
        // the fields below are labelled in their own right.
        <div aria-hidden className="flex items-center gap-3">
          <span className="h-px flex-1 bg-border" />
          <span className="text-xs text-content-subtle">or</span>
          <span className="h-px flex-1 bg-border" />
        </div>
      ) : null}

      {passwordEnabled ? (
        <form onSubmit={submit} noValidate className="flex flex-col gap-4">
          {/* 3.3.1 — announced once, politely, rather than on every keystroke.
              `role="alert"` would interrupt mid-typing. */}
          <p
            id={summaryId}
            aria-live="polite"
            className={
              error
                ? 'rounded-md border border-danger bg-danger-subtle px-3 py-2 text-sm text-content'
                : 'sr-only'
            }
          >
            {error ?? ''}
          </p>

          <Input
            ref={emailRef}
            label="Work email"
            type="email"
            autoComplete="username"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            aria-describedby={error ? summaryId : undefined}
            {...(fieldError === 'email' && fieldMessage ? { error: fieldMessage } : {})}
          />

          <div className="flex flex-col gap-1">
            <div className="relative">
              <Input
                ref={passwordRef}
                label="Password"
                type={reveal ? 'text' : 'password'}
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                aria-describedby={error ? summaryId : undefined}
                className="pr-16"
                {...(fieldError === 'password' && fieldMessage ? { error: fieldMessage } : {})}
              />
              {/* 2.1.1 — a real button, reachable and operable by keyboard.
                  3.3.8 — paste stays permitted; nothing here blocks it. */}
              <button
                type="button"
                onClick={() => setReveal((shown) => !shown)}
                aria-pressed={reveal}
                className="absolute right-2 top-8 rounded px-2 py-1 text-xs font-medium text-content-muted transition-colors hover:text-content focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2"
              >
                {reveal ? 'Hide' : 'Show'}
              </button>
            </div>
            {/* ⚠️ **The design places this beside the *label*; it is placed
                beside the *field* instead.** `Input` renders its own label and
                §20c forbids reshaping a shared component for one page's
                benefit, so the choice was between a library change and one
                line of vertical distance. **Recovery stays adjacent to the
                password**, which is the behaviour the placement exists for —
                somebody who cannot remember looks here rather than below a
                button they have already failed to use. */}
            <p className="text-right text-sm">
              <AuthLink href="/forgot-password">Forgot password?</AuthLink>
            </p>
          </div>

          <label className="flex items-center gap-2 text-sm text-content-muted">
            <input
              type="checkbox"
              checked={remember}
              onChange={(event) => setRemember(event.target.checked)}
              className="h-4 w-4 rounded border-border-strong text-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2"
            />
            Keep me signed in for 30 days
          </label>

          {/* The design's loading spec is `label kept, width fixed` — so the
              button says what it is doing without the card reflowing under
              somebody's cursor. */}
          <Button type="submit" className="w-full" disabled={pending !== null}>
            {pending === 'password' ? 'Signing in…' : 'Sign in'}
          </Button>
        </form>
      ) : null}

      <p className="text-center text-sm text-content-muted">
        Your company uses SSO? <AuthLink href="/sso">Use single sign-on</AuthLink>
      </p>
    </div>
  );
}
