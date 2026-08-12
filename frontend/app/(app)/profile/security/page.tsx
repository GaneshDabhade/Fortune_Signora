import { headers } from 'next/headers';

import { auth } from '@/lib/auth/server';

import { AccountSecurity } from './account-security';
import { FactorsPanel } from './factors-panel';
import { PasswordPanel } from './password-panel';
import { RecoveryPanel } from './recovery-panel';

/**
 * **`/profile/security` — the Security Center** —
 * [TASK-1414](../../../../../docs/BACKLOG.md), Workflow 23, against 📁
 * [`Fortune Signora Security Center.dc.html`](../../../../../docs/design-snapshot/screens/)
 * ([D-138](../../../../../docs/DECISION_REGISTER.md)).
 *
 * ## 📁 The design's own statement of what this page is for
 *
 * > ***"A security page has one job on the day it matters: let someone who
 * > thinks they have been compromised understand what happened and stop it, in
 * > under a minute, while frightened. Everything here is arranged for that
 * > reading — the unrecognised device is at the top, every destructive control
 * > states its blast radius before it fires, and no screen claims an outcome
 * > the system cannot guarantee."***
 *
 * ⚡ **The last clause is why this page states four absences out loud** rather
 * than rendering a tidier screen that implies more than the product can do.
 *
 * ## 🔴 Under `/profile`, because the design says whose page this is
 *
 * 📁 ***"Posture is computed from your account only. Workspace-wide controls
 * live in Settings and are shown here as context, never as something you can
 * change."*** ⛔ **So it is not a Settings screen** — Settings is the
 * organization's, and this is one person's.
 *
 * ⚡ **Panels composed into a route**, which is the shape
 * [TASK-470](../../../../../docs/BACKLOG.md) established for `/profile` and the
 * reason this page is a heading and four children.
 *
 * ## ⛔ What is NOT here, and why each one is absent
 *
 * | Design | Why it is absent |
 * |---|---|
 * | **§06 sign-in history** | 📁 `workspace_tenancy`'s security event stream is **write-only by its own design** — *"no reader is published; the Security Center screens that READ this stream are Workflow 23"*. **Publishing one is a `backend/modules/` change and this row's Change Budget is the frontend** |
 * | **§07 connected applications** | ⛔ **No module publishes a per-person authorisation** — the connections that exist are the workspace's, in Settings, and the design puts those behind an admin role anyway |
 * | **§01's unrecognised-device banner** | ⚡ **It is the sign-in history, rendered as an alert.** Same absent reader |
 * | **Passkeys, push and SMS** | ⛔ **`better-auth@^1.1.0` ships no passkey plugin**, and nothing sends a push or an SMS |
 *
 * ⚠️ **Each is stated on the screen where the reader would look for it**, never
 * left as a gap that reads like a clean bill of health.
 */
export const dynamic = 'force-dynamic';

export default async function SecurityPage() {
  const requestHeaders = await headers();
  const session = await auth().api.getSession({ headers: requestHeaders });

  /**
   * 🔴 **Which provider holds the password is a READ, never a guess.**
   *
   * ⛔ **The tempting shortcut is *"no password field means SSO"***, which is
   * the same conflation [B-253](../../../../../docs/BUGS.md) is open for one
   * component along: **an unresolved read rendered as a fact.** ⚡ **Better
   * Auth publishes the account list, so the question has an answer.**
   */
  const accounts = await auth().api.listUserAccounts({ headers: requestHeaders });
  const credential = accounts?.find((account) => account.providerId === 'credential');
  const ssoProvider = credential === undefined ? (accounts?.[0]?.providerId ?? null) : null;

  /**
   * ⚡ **Two, not one**: the authenticator app and the backup codes that come
   * with it are separate methods in the design's list, and Better Auth enables
   * them together. ⛔ **Nothing counts them by rendering the list and measuring
   * it** — that would make a number depend on markup.
   */
  const factors = session?.user.twoFactorEnabled === true ? 2 : 0;

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-xl font-semibold tracking-tight text-content">Security</h1>
        <p className="mt-1 max-w-[80ch] text-sm leading-6 text-content-muted">
          Everything on this page is about your own account. If you think somebody else has
          got into it, the sessions below are what you end first.
        </p>
      </div>

      <AccountSecurity currentToken={session?.session.token ?? ''} factors={factors} />
      <PasswordPanel ssoProvider={ssoProvider} />
      <FactorsPanel
        twoFactorEnabled={session?.user.twoFactorEnabled === true}
        hasPassword={credential !== undefined}
      />
      <RecoveryPanel />
    </div>
  );
}
