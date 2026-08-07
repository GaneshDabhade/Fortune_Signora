/**
 * How the attention list is arranged — flat, or grouped by where each pursuit
 * stands.
 *
 * **TASK-441, and it is [C-229](../../../docs/LANE_COORDINATION.md)'s answer B
 * rather than a new screen.** The recommendation is exact: *"a stage-grouped
 * **view** of the attention list, travelling in the URL beside `owner`, which
 * delivers* where does everything stand *with no fourth sidebar entry and no
 * second copy of the list."*
 *
 * ### Why this is not a screen
 *
 * ⛔ **Every one of TASK-441's deliverables already renders.**
 * `ContributionList`, `ScoreArithmetic`, `OpportunityMomentum`,
 * `AccountHistory` and `CompetitorContext` are on Account 360, and
 * score-with-expiry is on this page. **A screen repeating them would be a
 * second copy of the same reads** — and [D38](../../../docs/architecture/39-product-review-findings.md)
 * removed *Opportunities* from navigation from first principles, saying
 * *"adding one back is a claim that needs defending."*
 *
 * ⚡ **What genuinely has no answer is a third question**: not *this account*
 * and not *who do I call today*, but **where does everything stand.** Grouping
 * the list a seller is already looking at answers it **with no new read** —
 * `AccountAttention` has carried `stage` since the list existed.
 *
 * ### In the URL, for the three reasons `owner` is
 *
 * A refresh, a browser back, and a second tab as a different view — the same
 * argument `owner-scope.ts` makes, and the reason neither is `useState`.
 */

import type { OwnerScope } from '@/lib/state/owner-scope';

/** `flat` is the list as it has always been; `stage` groups it by pursuit. */
export type Standing = 'flat' | 'stage';

const STANDINGS: readonly Standing[] = ['flat', 'stage'];

/** What a customer calls each arrangement. **Neither word is a noun for a
 * place** — they name how one list is arranged, which is what keeps this a
 * view rather than a second screen. */
export const STANDING_WORDS: Record<Standing, string> = {
  flat: 'By urgency',
  stage: 'By stage',
};

/**
 * The arrangement a URL is asking for.
 *
 * **An unknown value reads as `flat`**, on `scopeFrom`'s reasoning exactly: a
 * hand-edited or stale link should show a seller their list, not an error.
 * There is nothing here to protect.
 */
export function standingFrom(value: string | null | undefined): Standing {
  return STANDINGS.includes(value as Standing) ? (value as Standing) : 'flat';
}

/**
 * A link that keeps both the scope and the arrangement.
 *
 * **Defaults are left out.** `owner=all` and `by=flat` are what the bare path
 * already means, and a clean URL is the one a seller copies into a message.
 */
export function withStanding(path: string, scope: OwnerScope, standing: Standing): string {
  const query = [
    scope === 'all' ? null : `owner=${scope}`,
    standing === 'flat' ? null : `by=${standing}`,
  ].filter((part): part is string => part !== null);

  return query.length === 0 ? path : `${path}?${query.join('&')}`;
}
