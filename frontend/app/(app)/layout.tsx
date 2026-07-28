import { headers } from 'next/headers';
import { redirect } from 'next/navigation';

import { auth } from '@/lib/auth/server';

import { AuthenticatedShell } from './authenticated-shell';

/**
 * Every route under `(app)` requires a session.
 *
 * Checked on the **server**, before any page renders. A client-side
 * redirect would ship the page to the browser first and then navigate
 * away, which briefly exposes whatever the page rendered.
 */
export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const session = await auth().api.getSession({ headers: await headers() });
  if (!session?.user) redirect('/sign-in');

  return <AuthenticatedShell email={session.user.email}>{children}</AuthenticatedShell>;
}
