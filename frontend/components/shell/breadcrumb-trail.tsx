'use client';

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

import type { Crumb } from '@/lib/shell/breadcrumb';

/**
 * **The trail a screen publishes into the shell's top bar** — against 📁
 * `Fortune Signora App Shell.dc.html` **§04** and **§05**
 * ([D-138](../../../docs/DECISION_REGISTER.md)).
 *
 * > 📁 **§04 — *"56px, surface-coloured, sticky, one hairline at the bottom.
 * > **Left: breadcrumb only.**"***
 * >
 * > 📁 **§05 — *"Mandatory below the first level, because most sessions start
 * > from a deep link in Slack or email."***
 *
 * ## 🔴 The slot existed, the trail existed, and nothing joined them
 *
 * ⚠️ **Measured on `/accounts` at 1440×900 before this file existed:**
 *
 * | | |
 * |---|---|
 * | The top bar's `[data-slot="breadcrumb"]` | ⛔ **`617 × 0` — zero height, zero children** |
 * | `nav[aria-label="Breadcrumb"]` | 🔴 **`@281,107` — *inside* `main > content-container > header`** |
 *
 * ⛔ **So the design's one breadcrumb was drawn in the one place the design
 * does not put it**, and the slot it does put it in rendered nothing on every
 * screen. ⚡ **`AppShell` already took a `breadcrumb` prop and `TopBar` already
 * rendered it**; the page had no way to reach either, because a page is
 * `children` and children do not pass props upward.
 *
 * ## ⚡ Published, not derived — and that was already the rule
 *
 * 📁 `app-shell.tsx`'s own note: ***"supplied by the page, never derived here.
 * A `/accounts/[id]` segment is an account's NAME, and only the module holding
 * that record knows it; deriving it would put routing in the shell"***
 * ([D-193](../../../docs/DECISION_REGISTER.md)). ✅ **This preserves that
 * exactly** — the shell still learns the trail from the screen; it just has a
 * channel now.
 *
 * ⛔ **This is NOT a module adding to the top bar**, which 📁 shell rule 2
 * forbids. **The slot is the shell's, its markup is the shell's, and a screen
 * supplies only the labels** — the same shape
 * [`utility-panel.tsx`](utility-panel.tsx) already uses for `publish`.
 */
interface TrailContract {
  readonly trail: readonly Crumb[];
  readonly publish: (key: string, trail: readonly Crumb[]) => void;
  /**
   * 🔴 **A screen withdraws only what it still owns** — ⛔ **and this is a
   * defect that was measured, not anticipated.**
   *
   * ⚠️ **Clicking a row on `/accounts` left the slot EMPTY**, while loading the
   * same URL directly filled it correctly. **During a client-side transition
   * React mounts the incoming tree before unmounting the outgoing one**, so the
   * order was `publish(new)` → `withdraw()` → nothing. ⚡ **The key makes the
   * cleanup a no-op once somebody newer has published**, which is the ordinary
   * last-writer-wins guard and the only shape that does not depend on React's
   * commit order staying what it is today.
   */
  readonly withdraw: (key: string) => void;
}

const EMPTY: readonly Crumb[] = [];

const TrailContext = createContext<TrailContract>({
  trail: EMPTY,
  publish: () => {},
  withdraw: () => {},
});

export function BreadcrumbTrailProvider({ children }: { children: ReactNode }) {
  const [published, setPublished] = useState<{ key: string; trail: readonly Crumb[] }>({
    key: '',
    trail: EMPTY,
  });
  const trail = published.trail;

  const publish = useCallback(
    (key: string, next: readonly Crumb[]) => setPublished({ key, trail: next }),
    [],
  );
  const withdraw = useCallback(
    (key: string) => setPublished((was) => (was.key === key ? { key: '', trail: EMPTY } : was)),
    [],
  );

  const contract = useMemo<TrailContract>(
    () => ({ trail, publish, withdraw }),
    [trail, publish, withdraw],
  );

  return <TrailContext.Provider value={contract}>{children}</TrailContext.Provider>;
}

/** ⚡ **What the top bar renders.** */
export function useBreadcrumbTrail(): readonly Crumb[] {
  return useContext(TrailContext).trail;
}

/**
 * **A screen states where it sits, and the shell draws it.**
 *
 * ⛔ **Withdrawn on unmount**, so a trail never outlives the screen that owns
 * it — ⚠️ **a stale crumb is worse than none**: it tells somebody they are
 * somewhere they have left.
 *
 * ⚡ **The dependency is the serialised trail rather than the array**, because
 * a page that builds its crumbs inline creates a new array on every render and
 * an identity-compared effect would publish forever.
 */
export function usePublishBreadcrumb(trail: readonly Crumb[]): void {
  const { publish, withdraw } = useContext(TrailContext);
  const key = JSON.stringify(trail);

  useEffect(() => {
    publish(key, JSON.parse(key) as readonly Crumb[]);
    return () => withdraw(key);
  }, [key, publish, withdraw]);
}
