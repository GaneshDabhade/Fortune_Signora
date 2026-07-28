import { headers } from 'next/headers';
import { redirect } from 'next/navigation';

import { auth } from '@/lib/auth/server';

import { WorkspaceList } from './workspace-list';

export default async function WorkspacesPage() {
  const session = await auth().api.getSession({ headers: await headers() });
  if (!session?.user) redirect('/sign-in');

  return (
    <main className="mx-auto max-w-3xl space-y-6 p-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Workspaces</h1>
          <p className="text-sm text-slate-500">{session.user.email}</p>
        </div>
        <SignOutButton />
      </header>
      <WorkspaceList />
    </main>
  );
}

function SignOutButton() {
  return (
    <form action="/api/auth/sign-out" method="post">
      <button
        type="submit"
        className="rounded-md border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50"
      >
        Sign out
      </button>
    </form>
  );
}
