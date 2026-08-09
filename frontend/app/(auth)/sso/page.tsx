import { ShieldCheck } from 'lucide-react';

import { LockedField } from '@/components/ui';
import { ServiceStatus } from '@/components/auth/service-status';
import { loadAuthConfig, oauthMethods } from '@/lib/auth/config';

import { AuthLink, AuthShell } from '../auth-shell';
import { SsoMethods } from './sso-methods';

/**
 * **Single sign-on** — design `04`, *SSO — domain discovery*.
 *
 * **TASK-467 · Workflow 1, milestone 3.**
 *
 * ### 🔴 It also closes a dead link this lane shipped
 *
 * Milestone 2 put *"Use single sign-on"* on the sign-in card pointing at
 * `/sso`, **and no such route existed** — every enterprise buyer who followed
 * the one link addressed to them reached *"That address does not lead
 * anywhere."* **Found by building the next screen, not by a gate**, and it is
 * the exact defect class [`reachability`](../../../tests/components/reachability.test.tsx)
 * exists for one direction of: that check finds a route nothing leads to, and
 * this was a link leading to no route.
 *
 * ### ⛔ What this screen does not do, and will not pretend to
 *
 * The design resolves the address to a provider — *"`northwind.com` uses Okta.
 * You'll be redirected."* **Nothing in this platform maps an email domain to
 * an identity provider.** There is no such table, no such setting, no such
 * endpoint and no backlog row; `AuthConfig` holds Google and Microsoft
 * credentials and nothing else.
 *
 * ⚡ **So the field is rendered locked rather than filled.**
 * [`LockedField`](../../../components/ui/locked.tsx) exists for exactly this:
 * *"it renders no value when none is known … the field is named, the reason is
 * given, and nothing is invented to fill the gap"* (P-A). **Printing a
 * provider name would be inventing an identity-federation claim on the screen
 * a security team reads most carefully** — the most expensive place in the
 * product to invent one.
 *
 * ⛔ **And there is deliberately no email field.** The design's has one because
 * the answer depends on it; ours would return the same answer for every
 * address ever typed. **A control whose outcome cannot depend on its input is
 * the false affordance the shell already refuses** — *"a control that goes
 * nowhere costs more trust than an absent one."*
 *
 * ### It is not a dead end, which the design requires of every screen
 *
 * *"None is a dead end."* **The federated providers offered here are real** —
 * the same `socialProviders` the sign-in card offers, and Microsoft Entra ID is
 * how most enterprises federate — plus the route back to sign-in.
 */
export const dynamic = 'force-dynamic';

export default function SsoPage() {
  const config = loadAuthConfig();

  return (
    <AuthShell
      masthead={
        <div
          aria-hidden
          className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-subtle text-accent"
        >
          <ShieldCheck className="h-4 w-4" />
        </div>
      }
      title="Single sign-on"
      description="Continue with the identity provider your company federates through."
      footer={<AuthLink href="/signin">Back to sign in</AuthLink>}
      region={<ServiceStatus />}
    >
      <SsoMethods methods={oauthMethods(config)} />

      <LockedField
        label="Your company's identity provider"
        reason="Signora cannot yet look up a provider from your email domain, so it is not asked for. If your company federates through a provider that is not offered above, your administrator configures it."
      />
    </AuthShell>
  );
}
