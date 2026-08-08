import { headers } from 'next/headers';

import { auth } from '@/lib/auth/server';

import { LocalePanel } from './locale-panel';
import { ProfilePanel } from './profile-panel';

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
    <div className="flex flex-col gap-10">
      <h1 className="text-xl font-semibold tracking-tight text-content">Your profile</h1>
      <ProfilePanel name={user?.name ?? null} email={user?.email ?? ''} />
      <LocalePanel />
    </div>
  );
}
