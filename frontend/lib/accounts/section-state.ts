/**
 * **The six states every Account 360 section is in, and the rules the design
 * states about them** — [TASK-1476](../../../docs/BACKLOG.md), against 📁
 * `Fortune Signora Account 360.dc.html` §*States*.
 *
 * ## ⚡ Why a law file rather than six `if`s in a page
 *
 * 📁 **The design writes eighteen rules across six groups, and fourteen of them
 * are about what must STAY TRUE while a section changes state** — *"collapsing
 * cannot hide a risk"*, *"the rest of the record stays live"*, *"the page
 * height is stable"*. ⛔ **A rule of that shape cannot be asserted against a
 * rendered section**, because the thing it forbids is a section rendering
 * *plausibly* while lying. ✅ **Encoded as functions, each one has a test that
 * can fail.**
 *
 * ## ⛔ What this file deliberately does NOT define
 *
 * 🔴 **The error state.** 📁 The design says *"always scoped to the smallest
 * failing section; the rest of the record stays live"* — ✅ **and that is
 * [`lib/system-states/ladder.ts`](../system-states/ladder.ts), already built
 * and already refusing.** `region` scope legalises `region-error` and
 * **`isLegal('region', '500')` is false**, which is the design's sentence
 * enforced one layer down. ⛔ **A second error vocabulary here would be the
 * two-representations defect [§2](../../../CLAUDE.md) names by name.**
 *
 * 🔴 **The empty state's rendering.** [`EmptyState`](../../components/ui/empty-state.tsx)
 * owns it, and [`SystemState`](../../components/ui/system-state.tsx)'s own
 * docstring records why the two must never merge.
 */

import { ApiError } from '@/lib/api/client';
import type { AccountSection } from './sections';

/**
 * 📁 **The design's six groups.** ⚠️ *Across all states* is deliberately one of
 * them rather than a preamble — **its three rules are invariants that hold
 * WHILE a section is in any of the other five**, and a name makes that
 * testable.
 */
export const SECTION_STATES = [
  'loading',
  'error',
  'empty',
  'collapsed',
  'expanded',
  'always',
] as const;

export type SectionState = (typeof SECTION_STATES)[number];

/**
 * ⚡ **How bad the worst thing in a section is.**
 *
 * ⛔ **Ordered, and the order is the whole point** — 📁 *"the header keeps the
 * count and the worst status, so collapsing cannot hide a risk."* **Folding a
 * list to its worst member needs a comparison**, and a set with no order
 * cannot provide one.
 *
 * ⚠️ **`none` is a real member, not an absence.** A section that has no notion
 * of status reports `none` and the header shows a count alone — **which is
 * different from a section whose items are all fine**, and the two must not
 * collapse into each other.
 */
export const SEVERITY_ORDER = ['none', 'good', 'watch', 'risk'] as const;

export type SectionSeverity = (typeof SEVERITY_ORDER)[number];

/**
 * 🔴 **The rule that makes collapsing safe.**
 *
 * 📁 ***"Header keeps the count and the worst status, so collapsing cannot
 * hide a risk."***
 *
 * ⛔ **Not `items.length` and not the first item's severity.** ⚡ A section
 * collapsed to *"4 signals"* while one of them is a risk is the design's
 * failure case stated exactly — **so the fold takes the maximum and never an
 * average, a first, or a most-common.**
 */
export function worstSeverity(items: readonly SectionSeverity[]): SectionSeverity {
  return items.reduce<SectionSeverity>(
    (worst, item) =>
      SEVERITY_ORDER.indexOf(item) > SEVERITY_ORDER.indexOf(worst) ? item : worst,
    'none',
  );
}

/**
 * 📁 **What a collapsed header says** — *"14 detected · 1 competitor present"*,
 * *"4 · 1 regulatory, acts on renewal"*.
 *
 * ⚡ **The count is always stated, including when it is zero**, because 📁 *"a
 * positive empty is good news, not a gap"* and a header that omitted the
 * number would make *nothing here* and *not loaded* look identical when
 * collapsed.
 *
 * ## 🔴 The count is its own measurement — [B-299](../../../docs/BUGS.md)
 *
 * ⛔ **This took `items.length` as the count, so *how many* and *how bad* came
 * out of one array.** ⚡ **`worstSeverity`'s own note two functions up already
 * said why that cannot hold** — *"a section that has no notion of status
 * reports `none` and the header shows a COUNT ALONE"* — **and there was no
 * parameter through which a count alone could arrive.**
 *
 * 🔴 **So a section declining to judge its items had to report having none.**
 * 📁 *Open opportunities* and *Recent activity* both pass no severities on
 * purpose — an opportunity's stage is not a verdict on the account, and a
 * recorded event is not a judgement — **and both rendered `0` beside a body
 * holding content.** ⚠️ **Collapse either one and the header reads *"Recent
 * activity 0"* over a hidden timeline**, which is 📁 *"collapsing cannot hide a
 * risk"* failing in the one place the rule was written for.
 *
 * ⚠️ **`null` is *nobody counted*, and it is a third answer** — 📁
 * [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md), and the same distinction
 * [B-1054](../../../docs/BUGS.md) drew for a failed read. ✅ **A read that
 * SUCCEEDED and found nothing still says `0`.**
 */
export interface CollapsedHeader {
  /** ⛔ **`null` means no measurement was obtained**, never *zero items*. */
  readonly count: number | null;
  readonly worst: SectionSeverity;
}

export function collapsedHeader(
  count: number | null,
  severities: readonly SectionSeverity[],
): CollapsedHeader {
  return { count, worst: worstSeverity(severities) };
}

/**
 * 🔴 **Where a collapse preference is remembered, and it is the rule most
 * likely to be got wrong.**
 *
 * 📁 ***"State persists per user and per account TYPE, not per record."***
 *
 * ⚠️ **Read that twice.** ⛔ **Keying it by `accountId` is the obvious
 * implementation and it is the one the design forbids** — a rep who collapses
 * *Technology stack* has decided they do not care about technology stacks on
 * companies, **not that they do not care about it on Acme.** ⚡ Keyed per
 * record, the preference is re-made on every account a rep opens, which is the
 * same as having no preference at all.
 *
 * ⚡ **`kind` is the account type the platform actually publishes** —
 * `ListedAccount.kind`, `'company' | 'person'` — **and not an invented
 * segment**: [C-1425](../../../docs/LANE_COORDINATION.md) covers the concepts
 * that do not exist, and this is not one of them.
 */
export function collapseKey(userId: string, kind: string, sectionId: string): string {
  return `signora:a360:collapse:${userId}:${kind}:${sectionId}`;
}

/**
 * ⛔ **Proof that the key cannot carry a record.** ⚡ Exported so the rule is
 * checkable by something other than reading `collapseKey` — 📁 the guard
 * belongs at the seam ([B-191](../../../docs/BUGS.md)), and the seam is the key
 * itself rather than the component that reads it.
 */
export function keyMentions(key: string, value: string): boolean {
  return key.split(':').includes(value);
}

/**
 * 📁 ***"Skeleton row count matches the expected result so the page height is
 * stable."***
 *
 * ⚡ **The expected result is the count this section had last time**, which is
 * the only honest source: ⛔ **a fixed `3` makes the page jump on every section
 * that is not three rows long**, which is precisely what the rule forbids.
 *
 * ⚠️ **`null` means nothing is known yet** — a first visit — **and then a
 * stated default is used rather than nothing.** ⛔ **Zero skeleton rows would
 * paint an empty section during a load**, which is [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md)
 * one level up: *a pending read must never render as an empty result.*
 */
export const FIRST_VISIT_ROWS = 3;

export function skeletonRows(lastKnownCount: number | null): number {
  if (lastKnownCount === null) return FIRST_VISIT_ROWS;
  // ⛔ **A section that was genuinely empty still skeletons.** ⚡ It may not be
  // empty this time, and painting nothing would state an answer the read has
  // not returned.
  return Math.max(1, lastKnownCount);
}

/**
 * 🔴 **Expansion, and the three rules that constrain it.**
 *
 * 📁 *"Only one section is expanded at a time"* · *"the URL updates so an
 * expanded section is shareable"* · *"anchor links from the page nav
 * auto-expand the target section."*
 *
 * ⚡ **All three are one fact: WHICH section is expanded lives in the URL.**
 * ⛔ **Held in component state instead, the first rule needs a coordinator, the
 * second is impossible and the third needs the nav to reach into the section.**
 * ✅ **In the URL, all three fall out** — one value cannot name two sections, a
 * link carries it, and an anchor is a link.
 */
export const EXPANDED_PARAM = 'section';

/**
 * ⚡ **Which section is expanded, read from the URL and validated against the
 * sections that exist.**
 *
 * ⛔ **An unknown id expands nothing** — 📁 the same refusal
 * [`reachable`](../../app/(onboarding)/onboarding/goals-form.ts) makes for a
 * goal naming a destination with no route ([B-256](../../../docs/BUGS.md)):
 * **an identifier this product has never heard of is not evidence that a
 * section exists.**
 */
export function expandedSection(
  params: URLSearchParams,
  sections: readonly AccountSection[],
): string | null {
  const asked = params.get(EXPANDED_PARAM);
  if (asked === null) return null;
  return sections.some((section) => section.id === asked) ? asked : null;
}

/**
 * ✅ **The URL for a section's expanded view**, which is what makes it
 * shareable.
 *
 * ⚠️ **Every other parameter is preserved.** ⛔ Rebuilding the query string
 * from this one value would silently drop whatever else the page is carrying,
 * and a share link that loses the reader's filters is a different page.
 */
export function withExpanded(params: URLSearchParams, sectionId: string | null): URLSearchParams {
  const next = new URLSearchParams(params);
  if (sectionId === null) next.delete(EXPANDED_PARAM);
  else next.set(EXPANDED_PARAM, sectionId);
  return next;
}

/**
 * 📁 ***"Anchor links from the page nav auto-expand the target section."***
 *
 * ⚡ **A fragment and the expansion parameter are the same intent expressed
 * twice**, so the rail's `#tech-stack` resolves here rather than the rail
 * learning about expansion.
 */
export function expansionFromAnchor(
  hash: string,
  sections: readonly AccountSection[],
): string | null {
  const id = hash.replace(/^#/, '');
  if (id === '') return null;
  return sections.some((section) => section.id === id) ? id : null;
}

/**
 * 🔴 **A positive empty is not a gap** — 📁 *"'no risk indicators' is good
 * news, not a gap."*
 *
 * ⛔ **This is the sentence most likely to be lost in implementation**, because
 * both cases render *"nothing here"* and only the tone differs. ⚠️ **A rep who
 * reads a clean risk list as a missing one goes looking for data that is
 * absent because there is none to have.**
 *
 * ⚡ **The tone is a property of the QUESTION, not of the result** — *are there
 * risks?* is good news when the answer is none; *what technology do they run?*
 * is not. **So it belongs beside the section, and it is stated per section
 * rather than inferred from a count.**
 */
export type EmptyTone = 'good-news' | 'neutral';

export const EMPTY_TONE: Readonly<Record<string, EmptyTone>> = {
  // ⚡ **Nothing weighed against this account is good news**, and the design
  // names this exact case.
  risks: 'good-news',
  // ⚠️ **A quiet timeline is NOT good news and is not bad news** — it is a fact
  // about how much has been observed, and calling it either would be a
  // judgement this file has no source for.
  signals: 'neutral',
  activity: 'neutral',
  opportunities: 'neutral',
} as const;

export function emptyTone(sectionId: string): EmptyTone {
  return EMPTY_TONE[sectionId] ?? 'neutral';
}

/**
 * 📁 ***"Sections load independently — a slow enrichment never delays the score
 * or the deal."***
 *
 * ⛔ **The rule is about what a page must NOT do**, so what it needs is a
 * refusal rather than a helper. ⚡ **A section's state is a function of that
 * section's own read and nothing else** — this signature takes one section's
 * flags and has no parameter through which another section's could arrive.
 *
 * ⚠️ **`isError` is checked before `isEmpty`** — 📁 [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md):
 * *a failed read must never render as an empty result.*
 */
export function resolveState(read: {
  readonly isLoading: boolean;
  readonly isError: boolean;
  readonly count: number;
}): Extract<SectionState, 'loading' | 'error' | 'empty'> | 'ready' {
  if (read.isError) return 'error';
  if (read.isLoading) return 'loading';
  if (read.count === 0) return 'empty';
  return 'ready';
}

/**
 * ⚡ **A contribution's severity, derived from a field the domain already
 * publishes and from nothing else.**
 *
 * ⛔ **`dissenting` is the ONLY thing mapped**, and it is mapped to `watch`
 * rather than `risk`. 📁 The Contribution Ledger records it as *signals reading
 * the same evidence differently* — **which is a reason to look, not a verdict**
 * — and `ai_reasoning_engine` carries the same concept as
 * `support.contested`. ✅ **The page already renders a `ContestedNote` for it**,
 * so the concept is this screen's, not a new one.
 *
 * ⛔ **`points`, `posture` and `relevance` are deliberately NOT mapped.** ⚡ A
 * low-scoring contribution is not a risk, and calling one a risk would be this
 * file inventing a judgement `buying_score_engine` owns and does not make.
 *
 * ⚠️ **Structural rather than typed on `ScoreContribution`**, so this law file
 * imports no API type and cannot drift with one.
 */
export function contributionSeverities(
  contributions: readonly { readonly dissenting: boolean }[] | undefined,
): readonly SectionSeverity[] {
  return (contributions ?? []).map((c) => (c.dissenting ? 'watch' : 'none'));
}

/**
 * 📁 ***"States what is missing versus what is still trustworthy, then retry
 * plus a correlation ID."***
 *
 * ⚡ **The correlation id already exists and no section on this page passed
 * it**: `ApiError.correlationId` is populated from the API's `correlation_id`
 * on every failure, and [`StatedAbsence`](../../components/feedback/stated-absence.tsx)
 * has accepted one all along. ⛔ **Half a rule built is the shape that reads as
 * done** — a reader who reports *"it failed"* with no reference makes the
 * failure unfindable in a log that already recorded it.
 *
 * 🔴 **An empty string is NOT a correlation id, and this is the guard.**
 * ⚠️ `client.ts` constructs `ApiError` with `correlation_id: ''` when the
 * *token* request fails — **before any API call is made, so there is no
 * correlated request to find.** ⛔ Passed through, that renders a reference
 * label with nothing after it, **which tells a reader to quote something that
 * does not exist.**
 */
export function correlationOf(error: unknown): string | undefined {
  if (!(error instanceof ApiError)) return undefined;
  return error.correlationId === '' ? undefined : error.correlationId;
}
