/**
 * **The design's eighteen state rules, as assertions** —
 * [TASK-1476](../../../docs/BACKLOG.md), against 📁
 * `Fortune Signora Account 360.dc.html` §*States*.
 *
 * ⚡ **Each test names the design sentence it enforces**, because a rule
 * paraphrased into a test is a rule nobody can check against the source.
 */
import { describe, expect, it } from 'vitest';

import { ACCOUNT_SECTIONS } from '@/lib/accounts/sections';
import {
  EXPANDED_PARAM,
  FIRST_VISIT_ROWS,
  collapseKey,
  collapsedHeader,
  emptyTone,
  expandedSection,
  expansionFromAnchor,
  keyMentions,
  resolveState,
  skeletonRows,
  withExpanded,
  correlationOf,
  worstSeverity,
} from '@/lib/accounts/section-state';
import { isLegal } from '@/lib/system-states/ladder';
import { ApiError } from '@/lib/api/client';

describe('🔴 collapsing cannot hide a risk', () => {
  /** 📁 *"Header keeps the count and the worst status."* */
  it('folds to the WORST, never the first and never the commonest', () => {
    expect(worstSeverity(['good', 'good', 'risk', 'good'])).toBe('risk');
    expect(worstSeverity(['risk', 'good'])).toBe('risk');
    expect(worstSeverity(['good', 'watch'])).toBe('watch');
  });

  it('⚠️ a section with no status concept reports `none`, which is not `good`', () => {
    // ⛔ **Different claims.** *Nothing here has a status* is not *everything
    // here is fine*, and a header that said the second would be inventing one.
    expect(worstSeverity([])).toBe('none');
    expect(worstSeverity(['none', 'none'])).toBe('none');
    expect(worstSeverity(['none', 'good'])).toBe('good');
  });

  it('states the count even when it is zero', () => {
    // 📁 A collapsed header that omitted the number makes *nothing here* and
    // *not loaded* indistinguishable.
    expect(collapsedHeader([])).toEqual({ count: 0, worst: 'none' });
    expect(collapsedHeader(['good', 'risk', 'watch'])).toEqual({ count: 3, worst: 'risk' });
  });
});

describe('🔴 a collapse preference is per account TYPE, never per record', () => {
  /**
   * 📁 ***"State persists per user and per account type, not per record."***
   *
   * ⛔ **Keying by `accountId` is the obvious implementation and the one the
   * design forbids.** ⚡ This is the assertion that fails if somebody adds it.
   */
  it('two companies share one preference', () => {
    expect(collapseKey('u1', 'company', 'tech-stack')).toBe(
      collapseKey('u1', 'company', 'tech-stack'),
    );
  });

  it('⛔ and the key cannot carry a record id', () => {
    const key = collapseKey('u1', 'company', 'tech-stack');
    expect(keyMentions(key, 'acct-9f2b')).toBe(false);
    expect(keyMentions(key, 'company')).toBe(true);
    expect(keyMentions(key, 'u1')).toBe(true);
  });

  it('two account TYPES do not share one, and two users do not either', () => {
    expect(collapseKey('u1', 'company', 'tech-stack')).not.toBe(
      collapseKey('u1', 'person', 'tech-stack'),
    );
    expect(collapseKey('u1', 'company', 'tech-stack')).not.toBe(
      collapseKey('u2', 'company', 'tech-stack'),
    );
  });
});

describe('📁 the page height is stable while it loads', () => {
  /** 📁 *"Skeleton row count matches the expected result."* */
  it('skeletons as many rows as the section had last time', () => {
    expect(skeletonRows(7)).toBe(7);
    expect(skeletonRows(1)).toBe(1);
  });

  it('⚠️ a first visit uses the stated default rather than nothing', () => {
    expect(skeletonRows(null)).toBe(FIRST_VISIT_ROWS);
  });

  it('⛔ never zero, because painting nothing states an answer the read has not returned', () => {
    // 📁 P-A one level up: a PENDING read must not render as an empty result.
    expect(skeletonRows(0)).toBeGreaterThan(0);
  });
});

describe('🔴 an expanded section is shareable, singular, and reachable from the rail', () => {
  const params = (q: string) => new URLSearchParams(q);

  it('📁 "only one section is expanded at a time" — one URL value cannot name two', () => {
    expect(expandedSection(params('section=signals'), ACCOUNT_SECTIONS)).toBe('signals');
    // ⚡ Two values for one key: the reader gets one section, never both.
    const both = expandedSection(params('section=signals&section=score'), ACCOUNT_SECTIONS);
    expect(ACCOUNT_SECTIONS.some((s) => s.id === both)).toBe(true);
  });

  it('⛔ an id this page has never heard of expands nothing', () => {
    // 📁 B-256's refusal, one screen over: an unknown identifier is not
    // evidence that a destination exists.
    expect(expandedSection(params('section=something_nobody_built'), ACCOUNT_SECTIONS)).toBe(null);
    expect(expandedSection(params(''), ACCOUNT_SECTIONS)).toBe(null);
  });

  it('⚠️ expanding preserves every other parameter, so a share link is the same page', () => {
    const next = withExpanded(params('tab=overview&q=acme'), 'signals');
    expect(next.get('tab')).toBe('overview');
    expect(next.get('q')).toBe('acme');
    expect(next.get(EXPANDED_PARAM)).toBe('signals');
  });

  it('collapsing removes the parameter rather than emptying it', () => {
    // ⛔ `?section=` is a URL that claims a section is expanded and names none.
    const next = withExpanded(params('section=signals&tab=overview'), null);
    expect(next.has(EXPANDED_PARAM)).toBe(false);
    expect(next.get('tab')).toBe('overview');
  });

  it('📁 "anchor links from the page nav auto-expand the target section"', () => {
    expect(expansionFromAnchor('#signals', ACCOUNT_SECTIONS)).toBe('signals');
    expect(expansionFromAnchor('signals', ACCOUNT_SECTIONS)).toBe('signals');
    expect(expansionFromAnchor('#not-a-section', ACCOUNT_SECTIONS)).toBe(null);
    expect(expansionFromAnchor('', ACCOUNT_SECTIONS)).toBe(null);
  });
});

describe('🔴 a positive empty is good news, not a gap', () => {
  /** 📁 *"'no risk indicators' is good news, not a gap."* */
  it('the tone is a property of the question and is stated per section', () => {
    expect(emptyTone('risks')).toBe('good-news');
    expect(emptyTone('signals')).toBe('neutral');
  });

  it('⚠️ an unnamed section is neutral rather than good news', () => {
    // ⛔ Defaulting to good news would congratulate a customer on a gap.
    expect(emptyTone('tech-stack')).toBe('neutral');
    expect(emptyTone('nothing-like-this')).toBe('neutral');
  });
});

describe('⛔ a failed read never renders as an empty one', () => {
  /** 📁 [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md). */
  it('error outranks empty, and outranks loading', () => {
    expect(resolveState({ isLoading: false, isError: true, count: 0 })).toBe('error');
    expect(resolveState({ isLoading: true, isError: true, count: 0 })).toBe('error');
  });

  it('loading outranks empty, because a pending read has returned no answer', () => {
    expect(resolveState({ isLoading: true, isError: false, count: 0 })).toBe('loading');
  });

  it('and a genuinely empty read is empty', () => {
    expect(resolveState({ isLoading: false, isError: false, count: 0 })).toBe('empty');
    expect(resolveState({ isLoading: false, isError: false, count: 4 })).toBe('ready');
  });
});

describe('📁 "always scoped to the smallest failing section" is already law', () => {
  /**
   * ⚡ **This file defines no error vocabulary and this test is why.** ✅ The
   * ladder already refuses a page-scale failure inside a section, which is the
   * design's sentence enforced one layer down — ⛔ **a second vocabulary would
   * be two representations of one truth** ([§2](../../../CLAUDE.md)).
   */
  it('a section may render a region error and may NOT render a 500', () => {
    expect(isLegal('region', 'region-error')).toBe(true);
    expect(isLegal('region', '500')).toBe(false);
    expect(isLegal('region', 'skeleton')).toBe(true);
  });
});

describe('📁 "…then retry plus a correlation ID"', () => {
  /**
   * ⚡ **The id existed on every failure and no section passed it** —
   * [TASK-1476](../../../docs/BACKLOG.md). ⛔ **Half a rule built is the shape
   * that reads as done.**
   */
  it('an API failure yields its correlation id', () => {
    const failure = new ApiError(503, {
      code: 'upstream_unavailable',
      message: 'no',
      correlation_id: 'abc-123',
    });
    expect(correlationOf(failure)).toBe('abc-123');
  });

  /**
   * 🔴 **The guard, and it has a real source.** ⚠️ `client.ts` constructs an
   * `ApiError` with `correlation_id: ''` when the TOKEN request fails —
   * **before any API call is made, so there is no correlated request to
   * find.** ⛔ Passed through, a reader is told to quote a reference that does
   * not exist.
   */
  it('⛔ but an empty string is not an id', () => {
    const beforeAnyCall = new ApiError(401, {
      code: 'token_unavailable',
      message: 'no',
      correlation_id: '',
    });
    expect(correlationOf(beforeAnyCall)).toBeUndefined();
  });

  it('⚠️ and anything that is not an API failure has none', () => {
    // ⛔ A network drop, a thrown string, a React error — none of them was
    // recorded by a server, so none of them has a reference to quote.
    expect(correlationOf(new Error('offline'))).toBeUndefined();
    expect(correlationOf(null)).toBeUndefined();
    expect(correlationOf(undefined)).toBeUndefined();
  });
});
