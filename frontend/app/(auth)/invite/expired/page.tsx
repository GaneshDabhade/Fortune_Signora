import Link from 'next/link';

import { AuthShell } from '../../auth-shell';

/**
 * **Screen `14 · Invitation expired`** — [TASK-489](../../../../../docs/BACKLOG.md),
 * against `docs/design-snapshot/screens/Fortune Signora Authentication.dc.html`
 * ([D-138](../../../../../docs/DECISION_REGISTER.md)), which routes it at
 * **`/invite/expired`**.
 *
 * ## ⚡ Why this exists now and could not before
 *
 * **The row recorded this screen as unbuildable, and it was right at the
 * time**: 📁 *"an expired invitation and one that never existed arrive as the
 * same `invitation_not_found`."* ⛔ **A screen that cannot be reached must not
 * be built** — [§2](../../../../../CLAUDE.md), and `reachability.py` refuses
 * it one layer down.
 *
 * ✅ **[B-214](../../../../../docs/BUGS.md) fixed exactly that** — the domain
 * already knew the invitation was expired and only the transport flattened it.
 * **`InvitationExpiredError` now yields `invitation_expired`**, so the accept
 * path can tell the two apart and send somebody here.
 *
 * ⚠️ **[TASK-489](../../../../../docs/BACKLOG.md) remains `BLOCKED` as a row,
 * and this is the half that is not.** Screen `13 Accept invitation` needs six
 * facts from inside a tenant the reader has not entered —
 * [C-245](../../../../../docs/LANE_COORDINATION.md), a disclosure ruling that
 * is the product owner's. ⛔ **Nothing here depends on that ruling**: an
 * expired invitation discloses nothing about the workspace, which is precisely
 * why it can ship while `13` cannot.
 *
 * ## ⛔ What this screen refuses to say
 *
 * **It does not name the organization.** 📁
 * [C-208](../../../../../docs/LANE_COORDINATION.md) settled it for `/join`:
 * *"the name lives inside the tenant the reader has not entered."* ⚡ **An
 * expired invitation is the weakest possible claim to membership**, so it
 * discloses less than the accept screen, not more.
 *
 * **And it does not offer to renew.** ⛔ **Nothing in the product lets an
 * invitee extend their own invitation**, and a button that cannot work is
 * worse than an instruction that can — so the screen tells them who *can*.
 */
export const metadata = { title: 'Invitation expired · Signora' };

export default function InvitationExpiredPage() {
  return (
    <AuthShell
      title="This invitation has expired"
      description="Invitations are time-limited, so an old link cannot be used to join."
    >
      <div className="flex flex-col gap-4 text-sm leading-6 text-content-muted">
        <p>
          {/* ⚡ **The recovery route is a person, not a control** — the only
              actor who can issue another invitation is somebody already in the
              organization. */}
          Ask whoever invited you to send a new one. They can do that from their
          organization&rsquo;s team settings, and the new link will work straight away.
        </p>
        <p>
          {/* ⛔ **Never back to the sign-in form as the primary action.** They
              did not fail to authenticate; the link aged out. Offering
              sign-in first would imply they got something wrong. */}
          Already have a Signora account?{' '}
          <Link
            href="/signin"
            className="rounded font-medium text-accent underline decoration-border underline-offset-4 transition-colors hover:decoration-accent "
          >
            Sign in
          </Link>
          .
        </p>
      </div>
    </AuthShell>
  );
}
