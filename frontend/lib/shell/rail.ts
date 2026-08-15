/**
 * **The rail's law** — [TASK-1408](../../../docs/BACKLOG.md), against
 * `docs/design-snapshot/screens/Fortune Signora App Shell.dc.html`
 * ([D-138](../../../docs/DECISION_REGISTER.md)).
 *
 * ## 🔴 The two rules that are not styling
 *
 * **① A restricted destination stays visible.** 📁 *"Restricted destinations
 * stay visible at 45% with a lock and **explain on click**."* ⛔ **The
 * ordinary instinct is to hide what somebody cannot reach**, and the design
 * refuses it: **a hidden destination teaches a person the feature does not
 * exist**, so they ask for the wrong thing or ask nobody. ⚡ **A locked one
 * that explains itself sends them to the person who can grant it** — the same
 * reasoning [TASK-1409](../../../docs/BACKLOG.md)'s `403` follows, and the
 * same reason `/invite/expired` names a person rather than a control.
 *
 * ⚠️ **This is presentational and never enforcement** ([§20c](../../../CLAUDE.md)):
 * **Casbin on the server is the authorization decision.** Dimming a rail item
 * is a courtesy; it must never be the only check.
 *
 * **② Depth stops at two.** 📁 *"Second level indents to 30px and **never
 * nests further**"*, and the rationale says why: 📁 *"Depth lives in records,
 * so the rail never grows a third level."* ⛔ **A third level is how a rail
 * becomes a sitemap** — and 📁 *"nine destinations is the limit at which
 * scanning beats searching."*
 */

/** 📁 *"Nine destinations is the limit at which scanning beats searching."* */
export const MAX_DESTINATIONS = 9;

/** 📁 *"Second level indents to 30px and never nests further."* */
export const MAX_DEPTH = 2;

/** 📁 *"232px expanded, 56px collapsed."* */
export const RAIL_WIDTH = { expanded: 232, collapsed: 56 } as const;

/**
 * 📁 **Tab order — *"rail → filter strip → content → utility panel."***
 *
 * ⚡ **Recorded as data because it is an accessibility contract**, not a
 * consequence of DOM order: the utility panel is visually beside the content
 * and comes after it, which is the one pair a source-order layout would get
 * backwards.
 */
export const TAB_ORDER = ['rail', 'filter-strip', 'content', 'utility-panel'] as const;

export interface RailDestination {
  id: string;
  label: string;
  /** 1 or 2 — {@link MAX_DEPTH}. */
  depth: number;
  /**
   * ⛔ **Restricted means *visible and locked*, never absent.** See ① above.
   */
  restricted?: boolean;
  /** 📁 *"Counts are neutral; a dot means unread and only Signals uses it."* */
  count?: number;
  unread?: boolean;
}

/**
 * ⛔ **A rail that would exceed nine destinations or two levels is a defect,
 * not something to truncate silently.**
 *
 * ⚡ **It returns the reasons rather than a boolean** — a caller that added a
 * tenth destination needs to be told which rule it broke, and a `false` sends
 * them to read the design rather than the message.
 */
export function railViolations(destinations: readonly RailDestination[]): string[] {
  const problems: string[] = [];

  // Only top-level entries count toward nine — a second level is detail
  // inside a destination, not another destination.
  const topLevel = destinations.filter((d) => d.depth === 1).length;
  if (topLevel > MAX_DESTINATIONS) {
    problems.push(
      `${topLevel} destinations: the rail holds ${MAX_DESTINATIONS}, "the limit at which scanning beats searching".`,
    );
  }

  const tooDeep = destinations.filter((d) => d.depth > MAX_DEPTH || d.depth < 1);
  for (const d of tooDeep) {
    problems.push(`"${d.label}" is at depth ${d.depth}: the rail never nests past ${MAX_DEPTH}.`);
  }

  // 📁 *"a dot means unread and only Signals uses it."*
  for (const d of destinations) {
    if (d.unread === true && d.id !== 'signals') {
      problems.push(`"${d.label}" shows an unread dot: only Signals does.`);
    }
  }

  return problems;
}

/**
 * ⛔ **Restricted destinations are never filtered out.** ⚡ **This function
 * exists so the rule has a name a reviewer can search for** — the tempting
 * change is a one-line `.filter()` in the component, and it would look like
 * tidying.
 */
export function visibleDestinations(
  destinations: readonly RailDestination[],
): readonly RailDestination[] {
  return destinations;
}

/**
 * 📁 **Collapse *"persists per user, per device class"*** — both, and the
 * device class is the half that is easy to drop.
 *
 * ⚡ **A phone and a desktop are different answers to the same question.**
 * Collapsing the rail on a laptop must not collapse it on the tablet the same
 * person picks up next, so the key carries both.
 *
 * ⛔ **The user id is required.** A key without it is shared by every account
 * on a shared machine, which leaks one person's preference to another and,
 * on a kiosk, hints that somebody else uses this product.
 */
export type DeviceClass = 'compact' | 'regular';

export function collapseKey(userId: string, device: DeviceClass): string {
  if (userId === '') throw new Error('collapse state is per user; a blank id would be shared');
  return `signora.rail.collapsed.${userId}.${device}`;
}

/**
 * 📁 **The design's four bands, as numbers the law can hold** —
 * [TASK-1443](../../../docs/BACKLOG.md), App Shell `breakpoints`.
 *
 * ⛔ **`deviceClassFor` hardcoded `768`** — Tailwind's `md`, a number the
 * design never names — **inside the rail's own law.** ⚡ **The design's bands
 * are 1600 · 1280 · 1024 · 640**, and *"< 1024px: rail becomes a sheet"* is
 * the boundary that actually decides whether a rail exists.
 */
export const BREAKPOINTS = {
  /** 📁 *"Below 640px: review, approve, comment and ask only."* */
  phone: 640,
  /** 📁 *"< 1024px: rail becomes a sheet from a top-bar button."* */
  smallLaptop: 1024,
  /** 📁 *"1280–1599 — the REFERENCE layout."* */
  laptop: 1280,
  /** 📁 *"≥ 1600 — rail 232px, utility panel 360px, both open."* */
  desktop: 1600,
} as const;

/**
 * 📁 **Which band a viewport is in**, by the design's name for it.
 *
 * ⚡ **Returned as a band rather than a boolean** because the design gives four
 * behaviours, not two — ⛔ and a helper answering *is this small* would have to
 * be replaced the first time a caller needed to tell a laptop from a desktop.
 */
export type Band = 'phone' | 'smallLaptop' | 'laptop' | 'desktop';

export function bandFor(viewportWidth: number): Band {
  if (viewportWidth >= BREAKPOINTS.desktop) return 'desktop';
  if (viewportWidth >= BREAKPOINTS.laptop) return 'laptop';
  if (viewportWidth >= BREAKPOINTS.smallLaptop) return 'smallLaptop';
  return 'phone';
}

/**
 * 📁 **Compact is *no rail at all*, which the design puts at 1024** — ⛔ not at
 * Tailwind's 768. ⚡ **The collapse preference is remembered per device class**,
 * so this boundary decides which of a person's two saved states applies.
 */
export function deviceClassFor(viewportWidth: number): DeviceClass {
  return viewportWidth < BREAKPOINTS.smallLaptop ? 'compact' : 'regular';
}

/**
 * **Whether the BAND decides the rail's state, rather than the person** —
 * [TASK-1473](../../../docs/BACKLOG.md), 📁 [D-233](../../../docs/DECISION_REGISTER.md)
 * rule ⓐ.
 *
 * > ✅ ***At 1024–1279 the band forces the rail to 56px. At ≥1280 the user's
 * > stored per-device-class preference decides.***
 *
 * ## 📁 The evidence is the utility panel, and it is worth carrying here
 *
 * ⚠️ **The design's band table is a set of FORCED states, and the panel is
 * what proves it**: the same `Small laptop` entry carries **`panelW: '0'` and
 * `panelDisplay: 'none'`** beside the rail line. ⚡ **The panel has its own
 * persisted preference** — *"Open state is remembered per module per user"* —
 * **and the band overrides it to `none`.** ⛔ **`none` is categorical, not a
 * proportion.** **Same band, same table, same document: it overrides a stored
 * preference for one component, so it overrides one for the other.**
 *
 * ⛔ **`railW` is NOT the evidence, and citing it was retracted.** 📁 Desktop
 * is `railW: '30%'` and Laptop is `railW: '28%'`, **and both are the same
 * 232px rail** — so it is a proportion of the mock diagram rather than a
 * specification, and the `28% → 12%` drop proves nothing either way.
 *
 * ## ⚡ Why the preference still does real work
 *
 * **There are four bands.** ⛔ The objection to ⓐ was *"a band-forced state
 * needs no stored preference, so per device class would do no work"* — ✅ **and
 * it does not survive counting them**: between **Desktop ≥1600** and **Laptop
 * 1280–1599** both states are permitted, and the preference is what chooses.
 */
export function bandForcesCollapse(band: Band): boolean {
  return band === 'smallLaptop';
}

/**
 * **The rail's actual state**, from the band and what the person asked for.
 *
 * ⛔ **A pure function rather than a branch in the hook**, so the ruling is
 * testable without a viewport, a person or a browser — and so the next lane
 * can find rule ⓐ by name rather than by reading an effect.
 *
 * ⚠️ **`phone` is deliberately NOT forced.** 📁 Below 1024 *"the rail becomes a
 * sheet from a top-bar button"* — **a sheet is neither expanded nor collapsed**,
 * and the shell already handles that separately. ⛔ **Returning `true` here
 * would make the sheet render at 56px**, which is a third state nobody drew.
 */
export function railIsCollapsed(band: Band, storedPreference: boolean): boolean {
  return bandForcesCollapse(band) ? true : storedPreference;
}
