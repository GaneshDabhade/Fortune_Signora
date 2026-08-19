'use client';

/**
 * **Is Signora degraded** — [TASK-1484](../../../../docs/BACKLOG.md) ⓑ,
 * against 📁 `Fortune Signora App Shell.dc.html` **§07**.
 *
 * > 📁 ***"System status is a persistent pill in the top bar rather than a
 * > banner — degradation is a fact about the product, not an interruption, and
 * > it expands into detail on click."***
 *
 * ## 🔴 The slot answered a narrower question than the design asks
 *
 * ✅ **`components/ui/offline-status.tsx` is correct and stays** — ⚡ it cites
 * §07 to justify its placement and the citation is right. ⛔ **But it answers
 * *is this browser online*, and §07 asks *is Signora degraded*.** ⚠️ **Two
 * different facts in one slot, and the shipped one is the narrower.**
 *
 * ## ⚡ The source exists and is not new work
 *
 * 📁 `apps/api/main.py` — **`GET /ready` publishes `status` with a row per
 * dependency**, and it has since the platform shipped. ⛔ **This row adds no
 * endpoint, no field and no backend change**, which its own budget requires.
 *
 * ## ⚠️ Why this does not go through `apiRequest`
 *
 * 🔴 **`/ready` answers `503` when it is degraded, deliberately** — 📁 its own
 * docstring: *"not ready is a 503, not a 200 with bad news in the body… every
 * orchestrator routes on the status code and never reads the body."*
 *
 * ⛔ **`apiRequest` throws on a non-2xx and parses the body as the API's error
 * envelope**, so the degraded answer — **the one this pill exists to show** —
 * would arrive as `unknown_error` with the per-service rows discarded. ⚡ **This
 * is the one read in the product whose failure status IS its payload.**
 *
 * ✅ **The hop is unchanged**: `/api/proxy` forwards the response untouched and
 * still requires a session, so nothing here is a second authorization surface.
 */

import { useQuery } from '@tanstack/react-query';

/** 📁 The shape `apps/api/main.py` publishes. Mirrored, not invented. */
export interface Readiness {
  status: 'ready' | 'degraded';
  database: 'ok' | 'unavailable';
  authentication: 'ok' | 'degraded' | 'unavailable';
  authentication_detail: string | null;
}

/** One dependency, as the pill's expanded panel lists it. */
export interface ServiceState {
  readonly name: string;
  readonly state: Readiness['database'] | Readiness['authentication'];
  readonly detail: string | null;
}

/**
 * 📁 **The design's per-service rows.** ⛔ **Derived from the payload rather
 * than declared**, so a service the API stops reporting stops being listed
 * instead of rendering a stale row — and 📁 TASK-1484's own bound is *"do not
 * invent a service the `/ready` payload does not report."*
 */
export function servicesOf(readiness: Readiness | undefined): readonly ServiceState[] {
  if (readiness === undefined) return [];
  return [
    { name: 'Database', state: readiness.database, detail: null },
    {
      name: 'Authentication',
      state: readiness.authentication,
      detail: readiness.authentication_detail,
    },
  ];
}

/**
 * ⚡ **Every 30 seconds**, the client's own `staleTime` — 📁 `lib/query/client.tsx`.
 * ⛔ **A pill that reported the state at page load would say *degraded* through
 * a recovery and *ready* through an outage**, which is worse than no pill.
 */
export const READINESS_INTERVAL_MS = 30_000;

export function useReadiness() {
  return useQuery({
    queryKey: ['readiness'],
    refetchInterval: READINESS_INTERVAL_MS,
    /**
     * ⛔ **No retry.** ⚡ A `503` here is **the answer**, not a transient
     * failure to paper over — and three retries would delay the one state the
     * pill exists to show by the length of the backoff.
     */
    retry: false,
    queryFn: async (): Promise<Readiness> => {
      const response = await fetch('/api/proxy/ready');
      /**
       * 🔴 **`503` carries the body.** ⛔ Anything else does not: a `502` from
       * the hop, a `401` from an expired session, HTML from a misrouted path.
       * ⚡ **So the reachable-but-degraded case is read and every other failure
       * is thrown**, which is what keeps *"we asked and it is degraded"*
       * distinguishable from *"we could not ask"*.
       */
      if (response.ok || response.status === 503) {
        return (await response.json()) as Readiness;
      }
      throw new Error(`readiness unavailable (${response.status})`);
    },
  });
}
