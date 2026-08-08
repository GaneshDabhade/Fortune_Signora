import { headers } from 'next/headers';

import { auth } from '@/lib/auth/server';

import { OnboardingWelcome } from './welcome';

/**
 * **`/onboarding`** — screens `01 Welcome` and `02 Product introduction`,
 * [TASK-469](../../../../docs/BACKLOG.md).
 */
export const dynamic = 'force-dynamic';

export default async function OnboardingPage() {
  const session = await auth().api.getSession({ headers: await headers() });

  // *"Nothing already known is asked again"* (WCAG 3.3.7). The name is read
  // from the account and greeted; **the screen never asks for it**, and when
  // the account has none the greeting is impersonal rather than blank.
  const name = session?.user?.name ?? null;
  const firstName = name === null || name.trim() === '' ? null : name.trim().split(/\s+/)[0]!;

  return <OnboardingWelcome firstName={firstName} />;
}
