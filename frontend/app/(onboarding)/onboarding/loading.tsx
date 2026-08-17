import { OnboardingSkeleton } from './company-form';

/**
 * **The loading state for every onboarding route** — [§19](../../../CLAUDE.md)'s
 * *loading*, and the one most often skipped.
 *
 * ⚡ **It arrived when `connect-form.tsx` gave this directory its first read
 * from `lib/query/hooks`**, and `route-states.test.tsx` said so immediately:
 * 📁 *"a route that reads owes a loading state."* ⛔ **The guard was right and
 * the gap was real** — `/onboarding` has always read the session.
 *
 * ⛔ **A skeleton, never an empty state.** 📁 [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md)
 * in its worst form is a screen asserting emptiness before the read returns.
 * **This claims nothing.**
 *
 * ⚡ **Next.js applies a parent `loading.tsx` to every nested segment**, so
 * `/onboarding/company`, `/you`, `/goals`, `/connect` and `/introduction` are
 * all covered by this one file rather than by five copies of it ([§2](../../../CLAUDE.md)).
 */
export default function OnboardingLoading() {
  return <OnboardingSkeleton />;
}
