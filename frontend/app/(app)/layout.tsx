import { headers } from 'next/headers';
import { redirect } from 'next/navigation';

import { auth } from '@/lib/auth/server';

import { AuthenticatedShell } from './authenticated-shell';

/**
 * **Nothing under `(app)` may be prerendered.** Declared on the segment, so it
 * covers every page beneath it rather than relying on five files each
 * remembering.
 *
 * Every route here reads a session, and reading a session opens the auth
 * database. **All five pages were being statically prerendered**, so the build
 * itself connected to a database to render signed-in screens — and, because
 * `loadAuthConfig()` had fallbacks, it connected to the *shared* one
 * ([B-104](../../../docs/BUGS.md)). That is the Infrastructure Contract's
 * environment-based-configuration rule inverted (§20b): configuration was being
 * resolved at build time, into an artifact that must read it at boot.
 *
 * It was invisible because it worked. Removing the fallbacks turned it into a
 * failed build, which is the only reason anybody looked.
 */
export const dynamic = 'force-dynamic';

/**
 * Every route under `(app)` requires a session.
 *
 * Checked on the **server**, before any page renders. A client-side
 * redirect would ship the page to the browser first and then navigate
 * away, which briefly exposes whatever the page rendered.
 */
export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const session = await auth().api.getSession({ headers: await headers() });
  if (!session?.user) redirect('/signin');

  /**
   * **B-429.** `session.user.name` was in scope on this line and was not
   * passed, and the menu three files away then explained its own absence as a
   * platform limitation. Registration requires a full name, so the platform
   * does publish one — the shell's composition was dropping it.
   */
  return (
    <AuthenticatedShell email={session.user.email} name={session.user.name ?? null}>
      {children}
    </AuthenticatedShell>
  );
}
