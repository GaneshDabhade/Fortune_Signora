'use client';

import { useRouter, useParams } from 'next/navigation';

import { Button, Card, CardBody } from '@/components/ui';
import { ApiError } from '@/lib/api/client';
import { useAcceptInvitation } from '@/lib/query/hooks/team';

/**
 * Joining an organization you were invited to.
 *
 * **The only screen in Signora shown to somebody who is not a member of the
 * workspace it is about.** The `(app)` layout still requires a session — being
 * signed in is exactly what makes acceptance possible, because the offer is
 * matched against the verified email claim on the caller's own token.
 *
 * ### It cannot name the organization, and that is a consequence rather than
 * an oversight
 *
 * A workspace's name is inside the tenant. The person reading this is not in
 * it yet, so nothing here can read it — that is
 * [C-208](../../../../../docs/LANE_COORDINATION.md)'s trade-off, taken
 * knowingly: acceptance never reads across tenants, and the alternative was a
 * policy change or a role that bypasses row-level security.
 *
 * **The invitation email carries the name**, which is where the customer
 * already saw it. This screen says what it can prove and does not guess.
 *
 * ### It asks rather than acts
 *
 * Landing on a URL does not join an organization. A page that accepted on load
 * would put a side effect behind a link somebody could be sent, previewed by a
 * mail client, or opened twice — and joining a customer's workspace is not
 * something to do because a browser followed a redirect.
 */
export default function JoinPage() {
  const params = useParams<{ workspaceId: string }>();
  const workspaceId = params?.workspaceId ?? null;
  const router = useRouter();
  const accept = useAcceptInvitation(workspaceId);

  /**
   * **Every refusal the endpoint can give, in the words it gave them.**
   *
   * The messages are written to be read: *"There is no invitation to this
   * organization for your address"*, *"Verify your email address before
   * accepting"*. Re-writing them here would put the same sentence in two
   * places and the copy nobody maintains is this one.
   *
   * A non-`ApiError` is a network failure and says so — it is the one case
   * where retrying is the right advice.
   */
  const refusal =
    accept.error === null
      ? null
      : accept.error instanceof ApiError
        ? accept.error.message
        : 'Signora could not be reached. Check your connection and try again.';

  if (accept.isSuccess) {
    return (
      <Card>
        <CardBody className="flex flex-col items-start gap-4">
          <div>
            <h1 className="text-base font-semibold text-content">You have joined</h1>
            <p className="mt-1 text-sm text-content-muted">
              {/* **Now it can name what it could not a moment ago.** The
                  membership is what makes the workspace readable, so this
                  sentence is only true after the fact — and it is deliberately
                  the first thing that changes. */}
              You are a {accept.data.role} of this organization. Its accounts and
              intelligence are yours to read.
            </p>
          </div>
          {/* **`/` and not `/accounts`.** There is no accounts index — the
              attention list is the product's home, and `/accounts/[id]` is the
              only route under that segment. A guard caught the difference
              before a customer did. */}
          <Button onClick={() => router.push('/')}>Go to your accounts</Button>
        </CardBody>
      </Card>
    );
  }

  return (
    <Card>
      <CardBody className="flex flex-col items-start gap-4">
        <div>
          <h1 className="text-base font-semibold text-content">Join this organization</h1>
          <p className="mt-1 text-sm text-content-muted">
            You were invited to a Signora organization. Accepting adds you to it, using
            the email address you signed in with.
          </p>
        </div>

        {refusal !== null && (
          <p role="alert" className="text-sm leading-6 text-content-muted">
            {refusal}
          </p>
        )}

        <Button
          onClick={() => accept.mutate()}
          disabled={accept.isPending || workspaceId === null}
        >
          {accept.isPending ? 'Joining…' : 'Accept invitation'}
        </Button>
      </CardBody>
    </Card>
  );
}
