'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';

import { Button, Input } from '@/components/ui';
import { signInWithPassword, signOut, useSession } from '@/lib/auth/client';

/**
 * **Your session expired** — design `18`, *over the current view*.
 *
 * **TASK-467 · Workflow 1, milestone 3.**
 *
 * ### ⚡ The design states the reason, and it is a defect claim
 *
 * *"Re-authentication happens over the page, not instead of it. The route,
 * scroll position, filters and draft state survive; the underlying content is
 * dimmed and inert but still visible, so people can see what they were doing.
 * **A full redirect is used only when the session is revoked rather than
 * expired.**"*
 *
 * ⛔ **So a redirect on expiry is not a styling choice — losing a half-written
 * filter set to a login bounce is data loss**, and the product does it today:
 * every route under `(app)` redirects to `/sign-in` the moment the server
 * cannot see a session.
 *
 * ### Expired and revoked are told apart, because the design says they behave differently
 *
 * | | | |
 * |---|---|---|
 * | **Expired** | `session.expiresAt` has passed | **This overlay.** Nothing navigates, so the route, the scroll position and every unsubmitted control survive by construction |
 * | **Revoked** | the session is gone *before* `expiresAt` | **Full sign-out.** An administrator ended it, or the password was reset from screen `09` — *"this signs you out of 4 other devices"* — and offering to unlock in place would be offering to undo a security action |
 *
 * ⚡ **Both facts come from Better Auth**: `expiresAt` is on the session it
 * already returns, so the moment is known in advance and a timer fires on it
 * exactly rather than polling and noticing late.
 *
 * ### Native `<dialog>`, and deliberately with no way out
 *
 * `showModal()` gives focus trapping, top-layer stacking and background
 * inertness from the platform ([`Dialog`](../ui/dialog.tsx) is built on the
 * same reasoning). ⛔ **`Dialog` itself is not reused, because every route out
 * of it is wrong here**: Escape, the backdrop and the close control all mean
 * *dismiss*, and a lock a person can dismiss leaves them looking at a screen
 * whose every action will 401. **`cancel` is prevented and never closes.**
 *
 * ⚠️ **The page behind is scroll-locked too** — `showModal()` leaves the root
 * scroller live ([B-307](../../../docs/BUGS.md), found by driving it), and the
 * design's *"dimmed and inert"* is not satisfied by a page that still scrolls
 * under the lock.
 */
export function SessionLock({ email }: { email: string }) {
  const router = useRouter();
  const { data } = useSession();
  const dialog = useRef<HTMLDialogElement>(null);
  const hadSession = useRef(false);

  const [expired, setExpired] = useState(false);
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const expiresAt = data?.session.expiresAt;

  // **Expiry: fire on the moment, do not poll for it.**
  useEffect(() => {
    if (expiresAt === undefined) return;
    const remaining = new Date(expiresAt).getTime() - Date.now();
    if (remaining <= 0) {
      setExpired(true);
      return;
    }
    // `setTimeout` clamps above ~24.8 days; a session lasts seven, so the
    // clamp is unreachable here and is not worked around with a chained
    // timer that would only ever be dead code.
    const timer = setTimeout(() => setExpired(true), remaining);
    return () => clearTimeout(timer);
  }, [expiresAt]);

  // **Revocation: the session went away while it was still valid.**
  useEffect(() => {
    if (data) {
      hadSession.current = true;
      return;
    }
    // ⚠️ **`data` is null before the first fetch resolves as well as after a
    // revocation**, and those are opposite facts. The flag is what separates
    // them: only a session that was once seen can have been taken away.
    if (hadSession.current && !expired) {
      void signOut();
    }
  }, [data, expired]);

  useEffect(() => {
    const element = dialog.current;
    if (!element) return;
    if (expired && !element.open) element.showModal();
    if (!expired && element.open) element.close();
  }, [expired]);

  useEffect(() => {
    const element = dialog.current;
    if (!element) return;
    // Escape must not dismiss a lock. Prevented rather than ignored: the
    // default would close the dialog in the DOM while React still believes
    // it is open, leaving the page inert with nothing over it.
    const refuse = (event: Event) => event.preventDefault();
    element.addEventListener('cancel', refuse);
    return () => element.removeEventListener('cancel', refuse);
  }, []);

  useEffect(() => {
    if (!expired) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = previous;
    };
  }, [expired]);

  const unlock = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!password) {
      setError('Enter your password to continue.');
      return;
    }

    setPending(true);
    setError(null);
    const result = await signInWithPassword(email, password);
    setPending(false);

    if (result.ok) {
      setPassword('');
      setExpired(false);
      // The tree above this overlay was rendered against a session the server
      // no longer recognised; refresh it in place. **Nothing is pushed** —
      // navigating is the behaviour this component exists to avoid.
      router.refresh();
      return;
    }
    if (result.throttled) {
      setError(
        result.retryAfterSeconds === undefined
          ? 'Too many attempts. Sign-in is paused for this device; try again shortly.'
          : `Too many attempts. Sign-in is paused for this device for ${result.retryAfterSeconds} seconds.`,
      );
      return;
    }
    setError(result.error ?? "That password doesn't match.");
  };

  return (
    <dialog
      ref={dialog}
      aria-labelledby="session-lock-title"
      // `shadow-xl` is the design's `--e4`, and this is the surface it exists
      // for: a card over content that is still visible underneath it. It read
      // `shadow-lg` — the elevation of something sitting *on* the page —
      // until TASK-491 gave the fourth step a token.
      className="w-[calc(100vw-2.5rem)] max-w-card rounded-xl border border-border bg-surface p-6 text-content shadow-xl backdrop:bg-backdrop/40"
    >
      <form onSubmit={unlock} className="flex flex-col gap-4">
        <div className="flex flex-col gap-2">
          <h2
            id="session-lock-title"
            className="text-lg font-semibold tracking-tight text-content"
          >
            Your session expired
          </h2>
          {/* ⚠️ **The design names the record whose edits survive** — *"your
              unsaved edits to Vantage Logistics are kept in this tab."*
              Nothing tracks draft state, so naming one would be a promise
              about recovery this product cannot keep. **What is claimed is
              only what the implementation guarantees**: no navigation
              happened, so the page is untouched. */}
          <p className="text-sm leading-6 text-content-muted">
            Sign in again to continue. Nothing has navigated away — this page is
            exactly as you left it.
          </p>
        </div>

        {error ? (
          <p
            aria-live="polite"
            className="rounded-md border border-danger bg-danger-subtle px-3 py-2 text-sm text-content"
          >
            {error}
          </p>
        ) : null}

        <Input
          label={`Password for ${email}`}
          type="password"
          autoComplete="current-password"
          autoFocus
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />

        <div className="flex flex-col gap-2">
          <Button type="submit" className="w-full" loading={pending}>
            Unlock
          </Button>
          {/* The one way out, and it is the honest one: leaving deliberately
              rather than dismissing the lock and finding every action fails. */}
          <Button
            type="button"
            variant="ghost"
            className="w-full"
            disabled={pending}
            onClick={() => void signOut()}
          >
            Sign out
          </Button>
        </div>
      </form>
    </dialog>
  );
}
