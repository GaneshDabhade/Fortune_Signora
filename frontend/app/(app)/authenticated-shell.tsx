'use client';

import { usePathname } from 'next/navigation';
import { useState, type ReactNode } from 'react';

import { SessionLock } from '@/components/auth/session-lock';
import { AppShell } from '@/components/shell/app-shell';
import { RouteGuard } from '@/components/shell/route-guard';
import { Button, SkeletonText } from '@/components/ui';
import Link from 'next/link';

import { signOut, useSession } from '@/lib/auth/client';
import { useViewerRole } from '@/lib/query/hooks/team';
import { ResumeOnboarding } from '@/components/workspace/resume-onboarding';
import { WorkspaceProvider, useWorkspaceContext } from '@/lib/state/workspace-provider';

/**
 * The client half of the authenticated layout.
 *
 * Split from `layout.tsx` because the session check must run on the server
 * while the shell needs client-side hooks. Passing only the email across
 * the boundary keeps the session object itself server-side.
 *
 * ### It used to tell everybody they were an owner
 *
 * A `TODO(M2.1)` sat here for four milestones: *"resolving it here needs a
 * `GET /workspaces/{id}/me` that does not exist yet — adding one is an API
 * change, not a frontend decision."* Until then it hardcoded `owner` **for
 * everybody**.
 *
 * **The premise was wrong.** `Membership` already carries `user_id` and `role`,
 * the members endpoint already returns them, and the session already carries
 * the signed-in user's id. No new endpoint was ever needed — and the TODO had
 * outlived the belief that produced it.
 *
 * ### Presentation, never enforcement
 *
 * Casbin on the server is the authorization decision (§20c, ADR-0010) and
 * nothing here changes that. What changes is that a member is no longer offered
 * controls the server will refuse — **a control that goes nowhere costs more
 * trust than an absent one**, which is the rule this surface already applies to
 * citations and to workflow actions.
 */
export function AuthenticatedShell({
  email,
  children,
}: {
  email: string;
  children: ReactNode;
}) {
  return (
    <WorkspaceProvider>
      {/* **Inside the provider, deliberately.** A role is a fact about a person
          *in a workspace*, so it cannot be resolved above the thing that knows
          which workspace is active. */}
      <ShellForViewer email={email}>{children}</ShellForViewer>
    </WorkspaceProvider>
  );
}

function ShellForViewer({ email, children }: { email: string; children: ReactNode }) {
  const pathname = usePathname();
  const {
    workspaces,
    activeWorkspace,
    isLoading: workspacesLoading,
  } = useWorkspaceContext();
  const { data: session } = useSession();

  const viewer = useViewerRole(activeWorkspace?.id ?? null, session?.user.id ?? null);

  // **Nothing is guarded until the role is known.** `RouteGuard` fails closed
  // and *redirects*, which is right once the answer is in and wrong before it:
  // an owner opening Settings directly would be bounced to the front page in
  // the moment before their own membership arrived, and would not be sent
  // back. The frame renders throughout; only its contents wait.
  //
  // ### And that is exactly what happened, through the other input
  //
  // `useViewerRole` answers `{ role: null, resolved: true }` when there is no
  // workspace — correctly, because *"no workspace means nothing to have a role
  // in"*. **On a fresh page load there is no workspace yet**: the list is still
  // in flight, `activeWorkspace` is legitimately `null`, and the hook reported
  // a resolved *"not a member"* for it.
  //
  // So `RouteGuard` fired on the first render and redirected. **An owner could
  // open Settings by clicking the sidebar and was thrown out of it by pressing
  // F5** — and with it the whole administrative surface: products, the ideal
  // customer, the buying committee, connections. Not reachable by URL, not
  // bookmarkable, not shareable.
  //
  // The two questions are separate and both must be answered before anything is
  // guarded: *which organization is this* and *what is this person in it*.
  // `resolved` alone conflates a workspace that is absent with one that has not
  // arrived, which is the same distinction the hook already draws so carefully
  // one level down (B-306).
  //
  // **`!isLoading` is not sufficient, and that is the subtle half.** The
  // provider chooses the active workspace in an effect that runs *after* the
  // list arrives, so there is a render in which loading is finished and
  // `activeWorkspace` is still `null`. The question is answered when there is
  // an active organization, or when the list came back and there are none —
  // and it is genuinely open in between.
  const workspaceKnown =
    !workspacesLoading && (activeWorkspace !== null || workspaces.length === 0);
  const resolved = viewer.resolved && workspaceKnown;
  const role = viewer.role;

  return (
    <AppShell
      role={resolved ? role : null}
      userId={session?.user.id ?? null}
      signOut={<SignOutButton email={email} />}
    >
      {/* ⚡ **Onboarding's only entrance** — TASK-469. It renders nothing
          unless this person has a run that is unfinished, and a dismissal
          sticks: *"no second ask, no guilt copy."* */}
      <ResumeOnboarding />
      {resolved ? (
        <RouteGuard pathname={pathname} role={role}>
          {children}
        </RouteGuard>
      ) : (
        <SkeletonText lines={3} />
      )}
      {/* **Mounted once, over everything** — design `18` requires
          re-authentication to happen *over* the current view rather than
          instead of it, so it lives at the shell and not on a page. It renders
          nothing until the session it is watching actually expires. */}
      <SessionLock email={email} />
    </AppShell>
  );
}

/**
 * Sign out.
 *
 * ### It used to leave people signed in, and show them a vendor error
 *
 * This was a native `<form method="post">` to `/api/auth/sign-out`. A browser
 * submits a form as `application/x-www-form-urlencoded`; Better Auth accepts
 * `application/json` only. **Every sign-out therefore navigated the customer
 * to a page of raw JSON** — `UNSUPPORTED_MEDIA_TYPE` — **and left the session
 * intact.**
 *
 * That is a security defect before it is a UX one: on a shared machine, a
 * person who signed out was still signed in, and the product had told them
 * otherwise by navigating away from itself.
 *
 * `signOut()` in `lib/auth/client.ts` has always done this correctly — it
 * calls the vendor's own client, which sends JSON, and then goes to
 * `/signin`. The control simply never used it. Nothing new is written here;
 * one duplicate of a behaviour is removed in favour of the one that works.
 */
function SignOutButton({ email }: { email: string }) {
  const [pending, setPending] = useState(false);

  return (
    <div className="flex items-center gap-3">
      {/* ⚡ **The profile's entrance, and the smallest one that is honest** —
          TASK-470. The design puts it in the App Shell's utility rail, which
          is Workflow 13 and not built; ⛔ **this row may not build that shell**,
          so the link goes where the identity already is. The email was already
          printed here and was not a link, which is exactly the "route with no
          entrance" `infra/reachability.py` refused. */}
      <Link
        href="/profile"
        className="hidden rounded text-sm text-content-muted underline decoration-border underline-offset-4 transition-colors hover:text-content hover:decoration-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent sm:inline"
      >
        {email}
      </Link>
      <span className="text-sm text-content-muted sm:hidden">{email}</span>
      <Button
        type="button"
        variant="secondary"
        size="sm"
        loading={pending}
        onClick={() => {
          // Latched rather than reset: the call ends in a navigation away from
          // this page, so there is no state to restore — and a second click
          // during the round trip would sign out twice.
          setPending(true);
          void signOut();
        }}
      >
        Sign out
      </Button>
    </div>
  );
}
