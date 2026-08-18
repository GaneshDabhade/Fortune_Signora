/**
 * **Home's *Customise* arrangement, applied** — 📁 `Fortune Signora Home.dc.html`
 * §10 and `3.2.3`.
 *
 * > **`3.2.3`** — *"**Card order within a composition is stable across visits.**"*
 * >
 * > **`U-05`, interim** — *"**reorder and remove only.** Adding cross-composition
 * > cards is out of scope for the first implementation."*
 */
import { describe, expect, it } from 'vitest';

import { applyLayout, type CardContract } from '@/lib/home/cards';

const card = (id: string, title = id): CardContract =>
  ({ id, title, module: 'test', requires: null }) as CardContract;

/** The registry's own order for a composition. */
const REGISTRY = [
  card('daily-briefing'),
  card('needs-you-today'),
  card('meetings'),
  card('agent-queue'),
  card('recents'),
];

const ids = (cards: readonly CardContract[]) => cards.map((entry) => entry.id);

describe('⛔ no arrangement changes nothing', () => {
  it('renders the registry order when nobody has customised', () => {
    expect(ids(applyLayout(REGISTRY, undefined))).toEqual(ids(REGISTRY));
  });

  it('⛔ and an empty arrangement is not an empty Home', () => {
    // ⚡ An arrangement that names nothing has arranged nothing — every card is
    // *new* to it, so the registry decides. **`{}` is not `remove everything`.**
    expect(ids(applyLayout(REGISTRY, { order: [], hidden: [] }))).toEqual(ids(REGISTRY));
  });
});

describe('📁 "reorder" — 3.2.3', () => {
  it('🔴 puts the cards where the person left them', () => {
    const layout = {
      order: ['recents', 'needs-you-today', 'daily-briefing', 'meetings', 'agent-queue'],
      hidden: [],
    };

    expect(ids(applyLayout(REGISTRY, layout))).toEqual(layout.order);
  });

  /**
   * ⛔ **A card in neither list is NEW**, and it lands at its registry position
   * rather than at the end. ⚡ Appending would put every future card below the
   * one the person cared least about, and the registry's order is the design's
   * own recommendation about what to read first.
   */
  it('🔴 a card shipped after they customised is not hidden by the omission', () => {
    const layout = { order: ['recents', 'needs-you-today'], hidden: [] };

    const result = ids(applyLayout(REGISTRY, layout));

    expect(result).toContain('meetings');
    expect(result).toContain('daily-briefing');
    // The two they arranged come first, in their order.
    expect(result.slice(0, 2)).toEqual(['recents', 'needs-you-today']);
  });

  /**
   * ⚡ **Among cards nobody arranged, the registry's order survives.** ⛔ A stable
   * sort is what makes this true, and an unstable one would reshuffle Home
   * between renders on the same data.
   */
  it('keeps the registry order among the cards nobody arranged', () => {
    const layout = { order: ['recents'], hidden: [] };

    expect(ids(applyLayout(REGISTRY, layout))).toEqual([
      'recents',
      'daily-briefing',
      'needs-you-today',
      'meetings',
      'agent-queue',
    ]);
  });
});

describe('📁 "remove" — U-05', () => {
  it('🔴 takes a removed card off the page', () => {
    const layout = { order: [], hidden: ['meetings'] };

    expect(ids(applyLayout(REGISTRY, layout))).not.toContain('meetings');
  });

  /**
   * 🔴 **A removed card keeps its place in `order`**, so restoring it puts it
   * back where it was rather than at the end — 📁 the same instinct `P-05` states
   * for activation: *"reordering shifts the list under the cursor."*
   */
  it('🔴 restoring a removed card returns it to its own position', () => {
    const arranged = ['recents', 'meetings', 'needs-you-today', 'daily-briefing', 'agent-queue'];

    const removed = ids(applyLayout(REGISTRY, { order: arranged, hidden: ['meetings'] }));
    const restored = ids(applyLayout(REGISTRY, { order: arranged, hidden: [] }));

    expect(removed).toEqual(['recents', 'needs-you-today', 'daily-briefing', 'agent-queue']);
    expect(restored).toEqual(arranged);
  });

  it('removes several at once', () => {
    const layout = { order: [], hidden: ['meetings', 'agent-queue'] };

    expect(ids(applyLayout(REGISTRY, layout))).toEqual([
      'daily-briefing',
      'needs-you-today',
      'recents',
    ]);
  });
});

describe('⛔ an arrangement can never add a card — U-05', () => {
  /**
   * 📁 *"Adding cross-composition cards is out of scope for the first
   * implementation."* ⚡ **Unrepresentable rather than refused**: the function
   * filters and sorts what it was given, so there is no path by which a stored id
   * becomes a rendered card.
   */
  it('🔴 an id the composition does not have renders nothing', () => {
    const layout = { order: ['forecast-vs-plan', 'recents'], hidden: [] };

    const result = ids(applyLayout(REGISTRY, layout));

    expect(result).not.toContain('forecast-vs-plan');
    expect(result).toHaveLength(REGISTRY.length);
  });

  /**
   * ⚠️ **A stale id is a stale preference, not a fault.** ⛔ Compositions change
   * as Signora ships, and refusing to render Home over one would be the wrong
   * trade every time.
   */
  it('⛔ and hiding a card that no longer exists is harmless', () => {
    const layout = { order: [], hidden: ['a-card-that-was-retired'] };

    expect(ids(applyLayout(REGISTRY, layout))).toEqual(ids(REGISTRY));
  });
});
