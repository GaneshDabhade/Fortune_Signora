/**
 * Whose work the attention list is showing.
 *
 * **In the URL, not in state**, for three reasons: it survives a refresh, it
 * survives browser back, and it can be opened in a second tab as a different
 * view. **And it has to travel on the account link** — the brief reads the
 * same query to offer *next* (D41), so a seller working their own accounts who
 * is then handed somebody else's has been dropped out of the list they were in.
 */
import { describe, expect, it } from 'vitest';

import { SCOPE_WORDS, scopeFrom, withScope } from '@/lib/state/owner-scope';

describe('the scope a URL is asking for', () => {
  it.each(['all', 'mine', 'unassigned'] as const)('reads %s', (scope) => {
    expect(scopeFrom(scope)).toBe(scope);
  });

  it('defaults to everything when the URL says nothing', () => {
    expect(scopeFrom(null)).toBe('all');
    expect(scopeFrom(undefined)).toBe('all');
  });

  it('shows a seller their accounts rather than failing on a stale link', () => {
    // A hand-edited or out-of-date link is a view preference, not a security
    // boundary. There is nothing here to protect by refusing.
    expect(scopeFrom('theirs')).toBe('all');
    expect(scopeFrom('')).toBe('all');
  });
});

describe('a link that keeps the current view', () => {
  it('carries the scope so the brief lands in the same list', () => {
    expect(withScope('/accounts/abc', 'mine')).toBe('/accounts/abc?owner=mine');
  });

  it('leaves the default out, because a clean URL is the one a seller copies', () => {
    expect(withScope('/accounts/abc', 'all')).toBe('/accounts/abc');
  });

  it('round-trips, which is the property the whole design rests on', () => {
    for (const scope of ['all', 'mine', 'unassigned'] as const) {
      const url = new URL(withScope('/', scope), 'https://x');
      expect(scopeFrom(url.searchParams.get('owner'))).toBe(scope);
    }
  });
});

describe('the words a customer reads', () => {
  it('names each view in one word', () => {
    // *All* rather than *Everything*: it labels a filter read at a glance, and
    // the shortest true word wins.
    expect(SCOPE_WORDS).toEqual({
      all: 'All',
      mine: 'Mine',
      unassigned: 'Unassigned',
    });
  });
});
