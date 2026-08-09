/**
 * **The top bar's closed slot set** — [TASK-1408](../../../docs/BACKLOG.md),
 * against `docs/design-snapshot/screens/Fortune Signora App Shell.dc.html`
 * ([D-138](../../../docs/DECISION_REGISTER.md)).
 *
 * > 📁 **Rule 2 — *"No module may add anything to the top bar."***
 * > 📁 **Anatomy — *"Orientation and identity only… No module actions ever."***
 *
 * ## ⚡ The rule is enforced by absence, not by review
 *
 * ⛔ **There is no `addTopBarItem`, no `slots` prop, no `children`.** **A
 * module cannot add to the top bar because the top bar exposes no way to add
 * to it** — which is [§2](../../../CLAUDE.md)'s *prefer a violation that is
 * unrepresentable over one that is merely discouraged*, applied to the one
 * shell rule most likely to be broken by a reasonable person.
 *
 * ⚠️ **It will be attempted.** **Every module has one control it believes is
 * global** — an export button, a workspace-wide filter, a *"new"* action. 📁
 * **Rule 3 is where those belong**: *"One primary action per view, and it
 * lives in the page header."* ⚡ **The page header is the module's; the top
 * bar is not.**
 *
 * ## 📁 Why the order is fixed rather than conventional
 *
 * **The design's own note**: *"Help before account, **always last**. Avatar is
 * the only circle in the shell."* ⚡ **The avatar's uniqueness is what makes
 * it findable without reading** — a second circle anywhere in the frame costs
 * that, which is why the slot set being closed protects a visual property and
 * not only a governance one.
 */

/**
 * 📁 **The five slots the design draws, in its order, left to right.**
 *
 * ⛔ **`as const` is load-bearing**: it is what makes {@link TopBarSlot} a
 * closed union, so a module naming a sixth slot fails to compile rather than
 * rendering one.
 */
export const TOP_BAR_SLOTS = [
  'breadcrumb',
  'search',
  'system-status',
  'notifications',
  'help',
  'account',
] as const;

export type TopBarSlot = (typeof TOP_BAR_SLOTS)[number];

/**
 * 📁 **Each slot's fixed geometry**, from the design's own table. ⚡ **Kept as
 * data because two of them are conditional** and a conditional written inline
 * in a component is a rule nobody can find later.
 */
export const SLOT_SPEC: Record<TopBarSlot, { width: number | 'flex' | 'auto'; height: number }> = {
  // 📁 *"flex, min 0. Truncates from the middle. Never wraps."*
  breadcrumb: { width: 'flex', height: 32 },
  // 📁 *"224 × 32. Widens to 320px on focus at ≥1600px."*
  search: { width: 224, height: 32 },
  // 📁 *"auto × 32"* — it sizes to its label, which is why hiding the label
  // changes the slot's width and why that is a rule rather than a style.
  'system-status': { width: 'auto', height: 32 },
  notifications: { width: 32, height: 32 },
  // 📁 *"32 + 32. Help before account, always last."*
  help: { width: 32, height: 32 },
  account: { width: 32, height: 32 },
};

/** 📁 *"Widens to 320px on focus at ≥1600px"* — both conditions, not either. */
export const SEARCH_WIDTH = { rest: 224, focused: 320, focusWidensAbove: 1600 } as const;

/**
 * 📁 **System status: *"Green pill hides its label at <1280px; amber and red
 * always show it."***
 *
 * ⚡ **The asymmetry is the whole rule.** **A healthy system may go quiet on a
 * narrow screen; a degraded one may not.** ⛔ **Hiding *"degraded"* to save
 * 60px is the platform choosing its own convenience over the customer knowing
 * why their data looks wrong.**
 */
export function statusLabelVisible(
  tone: 'healthy' | 'degraded' | 'down',
  viewportWidth: number,
): boolean {
  return tone === 'healthy' ? viewportWidth >= 1280 : true;
}

/**
 * 📁 **Notifications: *"Count badge caps at 99+."*** ⛔ **A four-digit badge
 * breaks the 32px slot** — and beyond a hundred the exact number stops being
 * information anybody acts on.
 */
export const BADGE_CAP = 99;

export function badgeLabel(count: number): string | null {
  if (count <= 0) return null;
  return count > BADGE_CAP ? `${BADGE_CAP}+` : String(count);
}
