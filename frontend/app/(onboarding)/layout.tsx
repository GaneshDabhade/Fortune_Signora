import { headers } from 'next/headers';
import { redirect } from 'next/navigation';

import { auth } from '@/lib/auth/server';
import { WorkspaceProvider } from '@/lib/state/workspace-provider';

/**
 * **Onboarding runs after authentication and before the App Shell** —
 * [TASK-469](../../../docs/BACKLOG.md), Workflow 8.
 *
 * ### ⛔ Authenticated, and deliberately not inside `(app)`
 *
 * **The session check is the same one `(app)/layout.tsx` performs**, for the
 * same reason and on the server for the same reason: a client-side redirect
 * ships the page to the browser first and then navigates away.
 *
 * ⚠️ **What is different is the chrome.** `(app)` wraps everything in the
 * `AuthenticatedShell` — navigation, the workspace selector, search. **A
 * person part-way through setup has nowhere to navigate to yet**, and the
 * design draws this flow with a rail and nothing else. Nesting under `(app)`
 * would have meant either showing a shell full of destinations that do not
 * work, or bending the shell for one caller ([§20c](../../../CLAUDE.md)).
 *
 * ### The same `force-dynamic`, for the same reason as `(app)`
 *
 * Every route here reads a session, and reading a session opens the auth
 * database. **Prerendering would resolve configuration at build time into an
 * artifact that must read it at boot** — [B-104](../../../docs/BUGS.md), and
 * §20b's environment-based-configuration rule inverted.
 */
export const dynamic = 'force-dynamic';

export default async function OnboardingLayout({ children }: { children: React.ReactNode }) {
  const session = await auth().api.getSession({ headers: await headers() });
  if (!session?.user) redirect('/signin');

  // `QueryProvider` is already mounted in the root layout, so only the
  // workspace context is added here — wrapping a second query client would
  // give the two trees separate caches of the same data.
  return <WorkspaceProvider>{children}</WorkspaceProvider>;
}
