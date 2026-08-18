'use client';

import { Compass } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

import { StatedAbsence } from '@/components/feedback/stated-absence';
import { useEntryDecision } from '@/lib/entry/use-entry';

/**
 * **`/` is entry resolution and nothing else** —
 * 📁 `docs/design-snapshot/screens/Fortune Signora Authenticated Entry.dc.html`
 * ([D-138](../../../docs/DECISION_REGISTER.md)).
 *
 * > 📁 ***"Every authenticated person lands on `/w/:workspace/home`."***
 * > 📁 ***"Entry resolution belongs to the shell, exclusively, and a module that
 * > wants to influence it registers a rule rather than performing a redirect."***
 *
 * ## 🔴 The engine was built, tested, and had one caller
 *
 * ⚠️ **[`lib/entry`](../../../lib/entry) implements all twenty-four rules with a
 * fixture each**, and 📁 its own header said *"it is also not wired to anything
 * yet, deliberately… [TASK-1401](../../../docs/BACKLOG.md) is the row that
 * replaces the five hardcoded redirects."* ⛔ **The only production caller was
 * onboarding's exit**, so **`/` rendered the Attention screen** — a product
 * surface where the design puts the resolver.
 *
 * ⚡ **The cost was not cosmetic.** Rules 11–14 decide which workspace a person
 * with several memberships enters and whether they see the chooser at all;
 * **none of them ran for anybody arriving at `/`**, which is the most travelled
 * path in the product.
 *
 * ✅ **The Attention screen keeps working at [`/attention`](./attention/page.tsx).**
 * ⛔ **It is moved rather than deleted** — no design document names it, and
 * retiring a shipped surface is a product decision
 * ([C-1532](../../../docs/LANE_COORDINATION.md)).
 *
 * ## ⛔ `replace`, never `push`
 *
 * 📁 ***"Entry resolution replaces history rather than pushing to it. Pressing
 * back from Home after login exits to the sign-in page, not into a loop through
 * the resolver."*** ⚡ **A `push` here would put the resolver in history**, and
 * *back* would land on it again and resolve forward — the loop the design names
 * by name.
 *
 * ## 🔴 A read that failed must not route
 *
 * 📁 **[P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md)**, and 📁
 * [`use-entry.ts`](../../../lib/entry/use-entry.ts) states the stake: on this
 * decision **the empty result is a redirect.** ⛔ **A failed membership read
 * treated as *no memberships* fires rule 10 and tells somebody with five
 * organizations that they belong to nothing** — and they lose the page they
 * were on to be told it.
 *
 * ✅ **So `unresolved` renders a stated failure and stays put.** ⚡ The engine is
 * not asked; it is not a fallback destination.
 *
 * ## ⚡ This route renders no product UI, and that is the specification
 *
 * 📁 *"No confirmation, no picker, no interstitial"* for the sole-workspace
 * case. ⛔ **So there is no greeting, no card and no spinner with a message** —
 * the shell is already painted around this, and a person who arrives here is
 * gone again in one frame.
 */
export default function EntryPage() {
  const router = useRouter();
  const state = useEntryDecision();
  const route = state.status === 'resolved' ? state.decision.route : null;

  useEffect(() => {
    // ⛔ **In an effect, not during render.** Navigating while rendering is a
    // side effect in the render phase, and React may run it twice.
    if (route !== null) router.replace(route);
  }, [router, route]);

  if (state.status === 'unresolved') {
    return <StatedAbsence as="page" icon={Compass} subject="your organizations" />;
  }

  /**
   * ⚡ **A live region and no visible chrome.** ⛔ A spinner here would flash on
   * every sign-in for the time it takes one cached query to answer, and 📁 the
   * design's budget is *"shell painted under 400ms from resolution"* — **the
   * shell is already painted.** ♿ **A screen-reader user still hears that
   * something is happening**, which a bare empty `<main>` would not give them.
   */
  return (
    <main aria-busy="true" className="sr-only" data-testid="entry-resolver">
      <p role="status">Opening your organization.</p>
    </main>
  );
}
