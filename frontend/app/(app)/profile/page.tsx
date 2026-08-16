import Link from 'next/link';
import { headers } from 'next/headers';

import { auth } from '@/lib/auth/server';

import { AccessibilityPanel } from './accessibility-panel';
import { AiPanel } from './ai-panel';
import { AppearancePanel } from './appearance-panel';
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
      <AppearancePanel />
      {/* 📁 **The design's `04 · Accessibility`.** ⚡ **In the design's own
          order** — it sits directly after Appearance, before AI preferences. */}
      <AccessibilityPanel />
      <AiPanel />

      {/* ⛔ **Keyboard shortcuts is deliberately NOT here.**

          📁 The design gives User Profile a *Keyboard shortcuts* section, and
          **`SHORTCUT_GROUPS` is already rendered by the shell's Shortcuts
          overlay** ([`shortcuts-reference.tsx`](../../../components/shell/shortcuts-reference.tsx)).
          ⚡ **The registry is the single source and the overlay is its
          canonical surface** — a second reference here would be two lists of
          one truth, disagreeing the first time a chord changes.

          ⚠️ **The design's section is a REFERENCE, not a customiser**: its
          items carry a label and keys and nothing editable, so there is no
          behaviour here that the overlay does not already provide. */}

      {/**
       * 🔴 **The Security Center's entrance** —
       * [TASK-1414](../../../../docs/BACKLOG.md).
       *
       * ⛔ **`make reachability` reports *No entrance at all* for a route no
       * screen links to**, and it is the gate [C-229](../../../../docs/LANE_COORDINATION.md)
       * failed on. ✅ **So the door ships with the room.**
       *
       * ⚡ **Here rather than in the account menu**: 📁 the design fixes that
       * menu at six items and *Security* is not one of them, and
       * [`account-menu.tsx`](../../../components/shell/account-menu.tsx)
       * already renders three of the six as absent rather than inventing
       * destinations. **This page is the one that is already about your own
       * account.**
       */}
      <Link
        className="rounded-lg border border-border bg-surface p-5 hover:bg-surface-sunken focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
        href="/profile/security"
      >
        <span className="block text-base font-semibold text-content">Security</span>
        <span className="mt-1 block text-sm text-content-muted">
          Your password, your second factors, and every session signed in as you — including
          the ones you can end.
        </span>
      </Link>
    </div>
  );
}
