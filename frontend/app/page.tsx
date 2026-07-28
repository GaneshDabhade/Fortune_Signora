import { redirect } from 'next/navigation';
import { headers } from 'next/headers';

import { auth } from '@/lib/auth/server';

export default async function Home() {
  const session = await auth().api.getSession({ headers: await headers() });
  redirect(session?.user ? '/workspaces' : '/sign-in');
}
