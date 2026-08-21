import { ShieldCheck } from 'lucide-react';
import Link from 'next/link';

import { loadAuthConfig, oauthMethods } from '@/lib/auth/config';
import { ServiceStatus } from '@/components/auth/service-status';

import { AuthShell } from '../auth-shell';

/**
 * **Welcome** — design `01`, the front door.
 *
 * **TASK-467 · Workflow 1, milestone 3**, against
 * `docs/design-snapshot/screens/Fortune Signora Authentication.dc.html`.
 *
 * ### ⚠️ The design puts this at `/` and it is at `/welcome`
 *
 * **`/` is the attention list** — a signed-in seller's morning, and the single
 * most-used screen in the product. **[D-159](../../../../docs/DECISION_REGISTER.md)
 * is explicit that routing is reused** and that only the customer-visible
 * presentation layer is replaced, so the address was not taken from the screen
 * that has held it since M1.
 *
 * ⛔ **What is *not* decided here: where an anonymous visitor lands.** Today
 * `app/(app)/layout.tsx` sends them to `/signin`, and the design's journey 1
 * begins on this screen instead. **That is a product decision about the front
 * door, not a presentation change**, so it is raised for the product owner
 * rather than made by this lane in passing.
 *
 * ### The three actions, and the third one is the enterprise one
 *
 * | | |
 * |---|---|
 * | **Sign in** | Primary |
 * | **Create a workspace** | Secondary — *organization*, never *workspace*, is the customer's word ([ADR-0034](../../../../docs/architecture/adr/0034-workspace-vocabulary.md)) |
 * | **Sign in with SSO** | Under an `Enterprise` divider, on the sunken surface |
 *
 * ⚡ **The `Enterprise` divider is the point.** The design separates it from
 * the two ordinary actions because *"the first screen an enterprise buyer sees
 * … their security team reads most carefully"* — an SSO route offered
 * *alongside* password sign-in reads as an afterthought.
 */
export const dynamic = 'force-dynamic';

export default function WelcomePage() {
  const config = loadAuthConfig();
  const canCreateAccount = config.passwordEnabled || oauthMethods(config).length > 0;

  return (
    <AuthShell
      // The shell's small mark is suppressed: this screen carries the brand
      // itself, at 36px over the heading, and printing it twice on the first
      // screen a buyer sees is worse than printing it nowhere.
      mark={false}
      masthead={
        <div
          aria-hidden
          className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent text-sm font-bold tracking-tight text-accent-contrast"
        >
          FS
        </div>
      }
      title="Fortune Signora"
      description="Revenue intelligence for enterprise teams. Sign in to your organization, or create one for your company."
      region={<ServiceStatus />}
    >
      <div className="flex flex-col gap-2.5">
        <Link
          href="/signin"
          className="flex h-control-md items-center justify-center rounded-md bg-accent text-sm font-semibold text-accent-contrast shadow-sm transition-colors hover:bg-accent-hover "
        >
          Sign in
        </Link>
        {/* ⛔ **Offered only when an account can actually be created.** With
            every sign-in method switched off this button leads to a form that
            cannot submit — the *"control that goes nowhere"* the shell already
            refuses for authorization, applied one screen earlier. */}
        {canCreateAccount ? (
          <Link
            href="/register"
            className="flex h-control-md items-center justify-center rounded-md border border-border-strong bg-surface text-sm font-semibold text-content transition-colors hover:bg-surface-sunken "
          >
            Create an organization
          </Link>
        ) : null}
      </div>

      {/* The divider and the action it introduces are one block, so the
          shell's rhythm separates *Enterprise* from the two ordinary actions
          rather than separating the label from its own button. */}
      <div className="flex flex-col gap-3.5">
        <div className="flex items-center gap-2.5">
          <span aria-hidden className="h-px flex-1 bg-border" />
          <span className="text-xs text-content-subtle">Enterprise</span>
          <span aria-hidden className="h-px flex-1 bg-border" />
        </div>

        <Link
          href="/sso"
          className="flex h-control-md items-center justify-center gap-2 rounded-md bg-surface-sunken text-sm font-semibold text-content-muted transition-colors hover:text-content "
        >
          <ShieldCheck aria-hidden className="h-3.5 w-3.5" />
          Sign in with SSO
        </Link>
      </div>
    </AuthShell>
  );
}
