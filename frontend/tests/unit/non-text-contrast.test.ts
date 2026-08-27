/**
 * **📁 Design System §17 `1.4.11` — non-text contrast, measured.**
 *
 * > ***"Every control border, chart series and status dot clears 3:1 against
 * > its own ground."***
 *
 * ## 🔴 Half of that sentence is false of the design's OWN palette
 *
 * ⛔ **`--border` on `--surface` measures `1.43:1` light and `1.52:1` dark**,
 * and it is not this repository's number — 📁 **the Design System declares
 * `--border: 33 20% 89%` against `--card: 0 0% 100%`, which is `1.26:1` before
 * any implementation is involved.**
 *
 * ⚠️ **So this is a conflict inside one authoritative document**, not an
 * implementation defect: **§17's accessibility claim contradicts the palette
 * the same document ships.** 📁 [C-1569](../../../docs/LANE_COORDINATION.md).
 *
 * ⛔ **NOT asserted here, and not fixed.** ⚡ **Darkening `--border` to clear
 * 3:1 would change every surface in the product and contradict the design's own
 * value** — that is the design's decision, not a lane's.
 *
 * ## ✅ The other half holds, and nothing guarded it
 *
 * **Status dots and the focus indicator clear 3:1 in both themes**, by a wide
 * margin. ⚡ **That is the half of `1.4.11` a token edit could silently break**
 * — 📁 the same argument `home-contrast.test.ts` makes for `1.4.3`: *"an edit
 * that keeps every rule and halves a ratio passes every gate this repository
 * had."*
 */
import { describe, expect, it } from 'vitest';

import { ratio } from '../support/contrast';

/**
 * 📁 **The dots the product actually renders**, and their real grounds.
 *
 * ⛔ **Not every token pair.** 📁 `home-contrast.test.ts`'s rule, and it is the
 * twin of §2's *"a guard that cannot fail is documentation pretending to be
 * code"*: **a guard that fails on something nobody ships teaches people to
 * ignore it.**
 */
const NON_TEXT: readonly (readonly [string, string, string])[] = [
  ['the risk dot on a card — AccountSectionShell, SystemStatus', 'danger', 'surface'],
  ['the watch dot on a card', 'warning', 'surface'],
  ['the healthy dot on a card', 'success', 'surface'],
  ['the accent dot — unread notifications, nav markers', 'accent', 'surface'],
  ['a status dot on the page ground', 'danger', 'canvas'],
  ['the focus indicator line on a card', 'accent', 'surface'],
  ['the focus indicator line on the page ground', 'accent', 'canvas'],
];

/** 📁 §17 `1.4.11`'s threshold, and WCAG 2.1's for non-text contrast. */
const NON_TEXT_MINIMUM = 3;

describe.each(['light', 'dark'] as const)('📁 §17 1.4.11 — the %s theme', (theme) => {
  it.each(NON_TEXT)('%s clears 3:1', (_label, foreground, background) => {
    expect(ratio(foreground, background, theme)).toBeGreaterThanOrEqual(NON_TEXT_MINIMUM);
  });
});

/**
 * ⚠️ **The vacuity half, and it is the assertion that makes the rest mean
 * something.**
 *
 * ⛔ **A `ratio()` that returned a large constant would satisfy every
 * assertion above** — 📁 the instrument-too-narrow failure, which passes
 * silently. ✅ **So the measurement is checked against a pair whose answer is
 * known independently**, and against one that must FAIL.
 */
describe('⚠️ the measurement itself', () => {
  it('reads genuinely different values for the two themes', () => {
    expect(ratio('danger', 'surface', 'light')).not.toBeCloseTo(
      ratio('danger', 'surface', 'dark'),
      2,
    );
  });

  /**
   * 🔴 **The pair the design claims and its own palette refuses.**
   *
   * ⛔ **Asserted as FAILING, deliberately** — 📁 [C-1569](../../../docs/LANE_COORDINATION.md).
   * ⚡ **This is the honest way to hold a known conflict**: the number is
   * recorded where a reader will see it, and **the day somebody resolves
   * C-1569 by darkening the token, this test goes red and asks them to move
   * the pair into `NON_TEXT` above.**
   *
   * ⚠️ **It is not a licence.** A guard that asserted the border *passes* would
   * be false; one that ignored it would let the conflict drift out of sight.
   */
  it('🔴 records that --border does NOT clear 3:1, in either theme', () => {
    for (const theme of ['light', 'dark'] as const) {
      expect(
        ratio('border', 'surface', theme),
        `--border now clears 3:1 in ${theme} — resolve C-1569 and move this pair into NON_TEXT`,
      ).toBeLessThan(NON_TEXT_MINIMUM);
    }
  });
});
