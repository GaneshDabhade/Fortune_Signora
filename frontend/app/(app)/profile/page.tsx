import Link from 'next/link';
import { headers } from 'next/headers';

import { auth } from '@/lib/auth/server';

import { ProfileShell } from './profile-shell';

/**
 * **`/profile`** — [TASK-470](../../../../docs/BACKLOG.md), Workflow 9,
 * milestone 1.
 *
 * ### ⛔ Panels composed into a route, never a shell
 *
 * The row is explicit: *"Renders inside the Application Shell — Workflow 13,
 * which is NOT built. This row therefore delivers the panels, composed into a
 * route that stands alone, and the shell adopts them when it lands. It must
 * not build a shell; that is Workflow 13's and building it here is the §20d
 * defect."*
 *
 * ⚡ **So this page is a heading and two panels.** The design's nine-item
 * settings rail belongs to the shell, and drawing one here would be the
 * borrowed code §20d warns about — unreviewed against its own acceptance
 * criteria and owned by nobody.
 */
export const dynamic = 'force-dynamic';

export default async function ProfilePage() {
  const session = await auth().api.getSession({ headers: await headers() });
  const user = session?.user;

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-title text-content">Your profile</h1>

      {/* 🔴 **The design's `ProfileShell` — a rail and one section beside it.**

          ⛔ **This replaces a single scrolling column of every panel.** ⚡ **That
          was not a smaller version of this design, it was a different
          information architecture**: the design's sections are destinations
          behind a 212px rail, and stacking them scrolled every one of them past
          a reader who wanted one.

          ⚠️ **The stack is gone rather than wrapped.** */}
      <ProfileShell name={user?.name ?? null} email={user?.email ?? ''} />

      {/**
       * 🔴 **The Security Center's entrance** —
       * [TASK-1414](../../../../docs/BACKLOG.md).
       *
       * ⚡ **Kept outside the shell deliberately**: it is a route rather than a
       * section of this screen, and `make reachability` reports *No entrance at
       * all* for a route no screen links to.
       */}
      <Link
        className="rounded-lg border border-border bg-surface p-5 hover:bg-surface-sunken "
        href="/profile/security"
      >
        <span className="block text-base font-semibold text-content">Security</span>
        <span className="mt-1 block text-sm text-content-muted">
          Your password, your second factors, and every session signed in as you —
          including the ones you can end.
        </span>
      </Link>
    </div>
  );
}
