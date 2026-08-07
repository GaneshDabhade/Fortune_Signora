import { TriangleAlert } from 'lucide-react';
import { Suspense } from 'react';

import { ServiceStatus } from '@/components/auth/service-status';
import { SkeletonText } from '@/components/ui';

import { AuthLink, AuthShell } from '../auth-shell';
import { ErrorDetail } from './error-detail';

/**
 * **Authentication error** — design `16`.
 *
 * **TASK-467 · Workflow 1, milestone 4.**
 *
 * ### 🔴 It replaces the vendor's own error page
 *
 * **Better Auth serves a complete `<!DOCTYPE html>` document from
 * `/api/auth/error`** — its own font stack, its own colours, its own heading —
 * and until this route existed **that is where every failed federated sign-in
 * landed.** ⛔ **An enterprise buyer whose identity provider refused them was
 * taken out of Signora entirely, into a page that does not look like the
 * product and offers no way back.**
 *
 * ⚡ **Found by reading `node_modules`, not by hitting it** — `dist/api/routes/error.mjs`
 * is the page, and `dist/oauth2/state.mjs` is the default that points at it
 * ([D-137](../../../docs/DECISION_REGISTER.md): *accessible is a claim to be
 * tested, never assumed in either direction*).
 *
 * ⚡ **The fix is one option on the sign-in request** — `errorCallbackURL`,
 * which Better Auth already accepts — **so the Authentication Authority is
 * untouched.** [D-159](../../../docs/DECISION_REGISTER.md): only the
 * customer-visible presentation layer is replaced.
 *
 * ### Two routes out, because the design allows no dead ends
 *
 * *"Email your IT team"* is the design's primary, and **it is not built**: it
 * needs an address for a customer's IT team, and Signora holds no such field.
 * ⛔ **A `mailto:` to nobody is worse than no button.** What is offered is what
 * works — **try another method**, and **back to sign in** — which is the design's
 * own second and the route every person needs regardless.
 */
export const dynamic = 'force-dynamic';

export default function AuthenticationErrorPage() {
  return (
    <AuthShell
      masthead={
        <div
          aria-hidden
          className="flex h-9 w-9 items-center justify-center rounded-lg border border-danger bg-danger-subtle text-danger"
        >
          <TriangleAlert className="h-4 w-4" />
        </div>
      }
      title="Sign-in was rejected"
      footer={
        <>
          <AuthLink href="/sign-in">Try another way to sign in</AuthLink>
        </>
      }
      region={<ServiceStatus />}
    >
      {/* `useSearchParams` suspends, and the shell around it is static — so
          the boundary is here rather than at the page, and the card's frame
          renders immediately instead of the whole screen waiting. */}
      <Suspense fallback={<SkeletonText lines={2} />}>
        <ErrorDetail />
      </Suspense>
    </AuthShell>
  );
}
