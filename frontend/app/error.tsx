'use client';

import { TriangleAlert } from 'lucide-react';
import { useEffect } from 'react';

import { SystemState } from '@/components/ui/system-state';
import { ApiError } from '@/lib/api/client';

/**
 * The outermost net — what a customer sees when a render fails somewhere
 * nothing else is catching.
 *
 * ### It does not duplicate `ErrorBoundary`, and the scopes are the point
 *
 * `components/feedback/error-boundary.tsx` wraps three regions **inside** the
 * authenticated shell, and it is the better experience wherever it applies: a
 * failed sidebar degrades the sidebar and the rest of the page keeps working.
 *
 * **It cannot apply outside the shell.** The `(auth)` group renders with no
 * boundary at all, so a render error on **sign-in — the first screen every
 * customer sees** — blanked the application entirely. So does an error in the
 * shell itself, or in the root providers.
 *
 * This file is Next's route-level boundary: the same nesting rule React
 * boundaries already follow, applied one level further out. **Nearest wins**,
 * so nothing inside the shell reaches here, and behaviour still exists once.
 *
 * ### The correlation id is the whole reason this is not a generic message
 *
 * When the failure carries one, it is shown. It is the single piece of
 * information that turns *"it broke"* into a request an engineer can find in
 * seconds (`16-logging`, `19-api-conventions`), and the same choice the
 * in-shell boundary and the toast both already make.
 *
 * ### It renders through the ladder — [TASK-1429](../docs/BACKLOG.md)
 *
 * ⛔ **This file wrote its own 500 and `app-shell`'s boundary wrote another,
 * with different colours, a different shape and a different retry.** 📁 The
 * ladder puts this one at **app scope**, which is what makes it announce
 * assertively — `4.1.3`: *"only a state that ends the session announces
 * assertively, once"* — ⚡ **and that politeness is now DERIVED from the
 * scope rather than chosen here.**
 *
 * 🔴 **The reference became copyable, and that is a behaviour change rather
 * than a refactor.** ⛔ **It was plain text: an identifier a customer had to
 * read down a phone.**
 *
 * ### Retry before reload
 *
 * `reset()` re-renders the segment without discarding the router, the query
 * cache or the customer's place. **A transient failure costs a click rather
 * than a full page load**, and where it does not help, the reload advice is
 * there in plain words.
 */
export default function AppError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Structured, and to stdout by way of the browser console — the only
    // channel this tier has. Never the raw error object: it is logged for a
    // human reading a support call, not for a stack trace nobody will read.
    console.error('signora.render_failed', {
      message: error.message,
      digest: error.digest,
      correlation_id: error instanceof ApiError ? error.correlationId : undefined,
    });
  }, [error]);

  const reference = error instanceof ApiError ? error.correlationId : error.digest;

  return (
    <main className="flex min-h-screen items-center justify-center bg-canvas px-6">
      <div className="w-full max-w-md">
        <SystemState
          scope="app"
          state="global-error-boundary"
          glyph={TriangleAlert}
          // 📁 `1.3.1` — *"an h1 that names what happened, not 'Error'."*
          // ⚡ The copy is unchanged; the ladder is now what renders it.
          title="Something went wrong"
          description="This screen could not be shown. Nothing about your accounts, your evidence or your decisions has changed — the failure is in displaying them."
          primaryAction={
            <button
              type="button"
              onClick={reset}
              className="rounded text-sm font-medium text-accent underline decoration-border underline-offset-4 transition-colors hover:decoration-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            >
              Try again
            </button>
          }
          secondaryAction={
            <span className="text-sm text-content-subtle">
              or reload the page if it keeps happening
            </span>
          }
          // 🔴 **This is the substantive change and not a refactor.** It was
          // `Reference: {reference}` as plain text — ⛔ **an identifier a
          // customer had to read aloud down a phone.** 📁 The grammar's rule
          // ③: *"identifiers are copyable — the single thing that makes a
          // support conversation short."*
          {...(reference === undefined ? {} : { correlationId: reference })}
        />
      </div>
    </main>
  );
}
