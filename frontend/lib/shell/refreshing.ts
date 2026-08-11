/**
 * **§16 tier three — is data on screen being replaced right now?** —
 * [TASK-1463](../../../docs/BACKLOG.md), against
 * `docs/design-snapshot/screens/Fortune Signora App Shell.dc.html`
 * ([D-138](../../../docs/DECISION_REGISTER.md)).
 *
 * > 📁 ***"Three tiers, chosen by what is actually unknown… In-place refreshes
 * > show a 2px bar under the top bar and dim stale figures to 60%; they never
 * > cover data that is already readable."***
 * >
 * > 📁 **The third case, in the design's own table**: *"In-place refresh ·
 * > Filter change, sync, retry · 2px bar under the top bar; existing figures
 * > stay readable at 60% until replaced. **No overlay, no spinner, no layout
 * > shift.**"*
 *
 * ## 🔴 The tier is defined by what is already readable, not by what is loading
 *
 * ⚡ **This is the whole distinction between tier three and the two above it**,
 * and it is why a plain *"something is fetching"* boolean is the wrong signal:
 * 📁 **cold boot and route change SKELETON the content region**, because there
 * is nothing to read yet. **An in-place refresh must not**, because there is —
 * and replacing readable figures with a skeleton is the [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md)
 * mistake in the other direction: **a screen that had the answer and chose to
 * stop showing it.**
 *
 * ## ⚡ Derived from the query cache, never tracked
 *
 * 📁 [§2](../../../CLAUDE.md), *the least powerful author capable of producing
 * a field correctly*. **The cache already knows which queries are in flight and
 * which of those have data**; a `refreshing` flag lifted into React state would
 * be a second representation of that, kept in step by hand, and **wrong in
 * exactly the moments that matter** — a fetch that errors, a query that unmounts
 * mid-flight, two regions refreshing at once.
 */
import { useIsFetching } from '@tanstack/react-query';

/**
 * True while **every** in-flight fetch is replacing data the reader can
 * already see.
 *
 * ⛔ **A single first-load fetch turns this off**, even alongside ten
 * refreshes. ⚡ **That is deliberate and it is the tier boundary**: if anything
 * on screen is still unknown, the screen is in tier one or two and the region
 * that owns it is already skeletoning — **dimming the rest would say *stale*
 * about content that is simply new.**
 */
export function useIsRefreshing(): boolean {
  const refreshing = useIsFetching({
    predicate: (query) => query.state.data !== undefined,
  });
  const firstLoads = useIsFetching({
    predicate: (query) => query.state.data === undefined,
  });

  return refreshing > 0 && firstLoads === 0;
}
