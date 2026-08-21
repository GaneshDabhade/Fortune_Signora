/**
 * 📁 **§08's second term on a date fact** — the design draws *"12 Oct 2026
 * **69 days**"*, and this is the arithmetic behind the qualifier.
 */
import { describe, expect, it } from 'vitest';

import { daysUntil } from '@/components/intelligence/dates';

const NOW = new Date('2026-08-04T12:00:00Z');

describe('the distance to a dated fact', () => {
  it('📁 counts the days the design draws beside the date', () => {
    expect(daysUntil('2026-10-12T00:00:00Z', NOW)).toBe('69 days');
  });

  /** ⚡ **The words a person would use**, matching this module's rule that
   *  precision nobody uses only creates doubt. */
  it('says today and tomorrow rather than 0 and 1', () => {
    expect(daysUntil('2026-08-04T18:00:00Z', NOW)).toBe('today');
    expect(daysUntil('2026-08-05T13:00:00Z', NOW)).toBe('tomorrow');
  });

  /** ⛔ **A lapsed renewal is not a countdown** — *"−3 days"* would read as a
   *  measurement rather than as something that has already happened. */
  it('⛔ never renders a negative countdown', () => {
    expect(daysUntil('2026-07-01T00:00:00Z', NOW)).toBe('passed');
  });

  /** ⚡ **Null rather than `Invalid Date`** — the caller omits the delta and the
   *  fact renders exactly as it did before the slot existed. */
  it('returns null for an unreadable date', () => {
    expect(daysUntil('not-a-date', NOW)).toBeNull();
  });
});
