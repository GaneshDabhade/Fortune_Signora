'use client';

import { createContext, useCallback, useContext, useMemo, useRef, useState } from 'react';

/**
 * 🔴 **State 08's second half** — 📁 `Fortune Signora Home.dc.html`:
 *
 * > *"Failed cards render their own error inside their own footprint with a
 * > correlation ID. The composition never collapses. **If EVERY card fails, the
 * > page states that and offers one retry for all.**"*
 * >
 * > **`AC-H07`** — *"Fail every card endpoint: the page states it and offers one
 * > retry. **No redirect occurs and the URL is unchanged.**"*
 *
 * ## ⚡ Why a registry, and why it is the smallest one that works
 *
 * ⛔ **Home cannot see the cards' queries.** Each card owns its own read — which
 * is 📁 §09's *"independence"* rule, *"one slow card holds its own skeleton; no
 * card waits for a sibling"* — so **the page has no way to know that all of them
 * failed** without something reporting it.
 *
 * ✅ **A card is failed exactly when it renders {@link CardFailure}**, so that is
 * where the report belongs. ⚡ **No card component changes**: the one component
 * every failure already goes through registers on mount and deregisters on
 * unmount, and Home counts.
 *
 * ⛔ **Not a second copy of each query in Home.** 📁 §2 — the card's query is the
 * authoritative representation of whether that card failed, and a parallel read
 * would eventually disagree with the card standing next to it.
 *
 * ## 🔴 *"One retry for all"* retries, it does not reload
 *
 * 📁 The System States grammar is explicit that a primary action *"does the most
 * likely useful thing rather than `reload`"*, and 📁 state 08's own rule is *"no
 * sibling is affected"*. ⚡ **Each failure registers its own `refetch`**, so the
 * page-level retry is every card's retry fired once — **not a navigation, which
 * is what `AC-H07`'s *"the URL is unchanged"* rules out.**
 */
export interface CardOutcomes {
  /** How many rendered cards are currently showing a failure. */
  readonly failed: number;
  /** Fire every failed card's own retry. */
  readonly retryAll: () => void;
  /** ⚡ Called by {@link CardFailure}. Returns nothing; the cleanup deregisters. */
  readonly report: (id: string, retry: () => void) => void;
  readonly forget: (id: string) => void;
}

const NOTHING: CardOutcomes = Object.freeze({
  failed: 0,
  retryAll: () => {},
  report: () => {},
  forget: () => {},
});

const Context = createContext<CardOutcomes>(NOTHING);

/**
 * ⚠️ **Absent by default, and that is deliberate.** ⛔ A card rendered outside
 * Home — in a component test, or on another surface later — must not throw for
 * want of a provider it has no reason to know about. **`NOTHING` makes the
 * registry optional without making it a lie**: with no provider the count stays
 * zero, and zero is what a page that is not Home would do with it anyway.
 */
export function useCardOutcomes(): CardOutcomes {
  return useContext(Context);
}

export function CardOutcomesProvider({ children }: { children: React.ReactNode }) {
  /**
   * ⚡ **A ref holds the retries and state holds only the COUNT.**
   *
   * ⛔ Putting the map in state would re-render every card each time one of them
   * failed. 📁 The count is the only thing Home renders on, so it is the only
   * thing that needs to be reactive.
   */
  const retries = useRef(new Map<string, () => void>());
  const [failed, setFailed] = useState(0);

  const report = useCallback((id: string, retry: () => void) => {
    // ⚡ **Re-registering the same id replaces its retry rather than counting
    // twice** — a card whose `refetch` identity changed between renders must not
    // inflate the count.
    const known = retries.current.has(id);
    retries.current.set(id, retry);
    if (!known) setFailed(retries.current.size);
  }, []);

  const forget = useCallback((id: string) => {
    if (!retries.current.delete(id)) return;
    setFailed(retries.current.size);
  }, []);

  const retryAll = useCallback(() => {
    // ⚡ **A copy, because a retry that succeeds deregisters during the loop.**
    for (const retry of [...retries.current.values()]) retry();
  }, []);

  const value = useMemo<CardOutcomes>(
    () => ({ failed, retryAll, report, forget }),
    [failed, retryAll, report, forget],
  );

  return <Context.Provider value={value}>{children}</Context.Provider>;
}
