import { headers } from 'next/headers';
import { redirect } from 'next/navigation';

import { auth } from '@/lib/auth/server';
import { WorkspaceProvider } from '@/lib/state/workspace-provider';

/**
 * **Signed in, and not yet inside an organization** —
 * [TASK-1421](../../../docs/BACKLOG.md).
 *
 * ## 🔴 The chooser needs the list and cannot have the shell
 *
 * ⛔ **`WorkspaceProvider` is mounted in `(app)`'s shell and `(onboarding)`'s
 * layout, and `/workspaces` is in neither.** ⚡ **Without this the page threw**
 * — `useWorkspaceContext` raises outside its provider, and the customer got
 * *"Something went wrong"* on the one screen whose job is to let them in.
 *
 * ⚠️ **Found by the journey, and it could not have been found by a component
 * test**: those mock the context, so the page renders perfectly against a
 * provider that is not in the tree. 📁 **The same class the ⓶a journey found
 * — built, tested, and unreachable — arriving through composition rather than
 * through routing.**
 *
 * ## ⛔ The shell is still not wrapped around it, and that is the design
 *
 * 📁 `Fortune Signora Workspace Chooser.dc.html` §03: **WS-B's precondition is
 * *"no shell exists yet"***. ⚡ **The app shell needs an organization to render
 * a rail for**, and this is the screen for somebody who has not chosen one.
 * ✅ **So the provider is mounted alone** — the data, without the chrome.
 *
 * ## ⚡ The same session check, on the server, for the same reason
 *
 * 📁 `(onboarding)/layout.tsx`'s reasoning applies unchanged: **a client-side
 * redirect ships the page to the browser first and then navigates away.**
 * ⚠️ **And `force-dynamic` for the same reason as both other layouts** —
 * reading a session opens the auth database, and prerendering would resolve
 * configuration at build time into an artifact that must read it at boot
 * ([B-104](../../../docs/BUGS.md)).
 */
export const dynamic = 'force-dynamic';

export default async function WorkspacesLayout({ children }: { children: React.ReactNode }) {
  const session = await auth().api.getSession({ headers: await headers() });
  if (!session?.user) redirect('/signin');

  // `QueryProvider` is already mounted in the root layout, so only the
  // workspace context is added here — a second query client would give the
  // two trees separate caches of the same data.
  return <WorkspaceProvider>{children}</WorkspaceProvider>;
}
