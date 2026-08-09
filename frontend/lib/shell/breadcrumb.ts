/**
 * **The breadcrumb trail's law** — [TASK-1408](../../../docs/BACKLOG.md),
 * against `docs/design-snapshot/screens/Fortune Signora App Shell.dc.html`
 * ([D-138](../../../docs/DECISION_REGISTER.md)).
 *
 * > 📁 **Rule 6 — *"Breadcrumbs are mandatory below the first level."***
 * > 📁 **Top-bar slot — *"Truncates from the middle. Never wraps. Always
 * > present below level one."***
 *
 * ## ⚡ Why the collapse is arithmetic rather than CSS
 *
 * 📁 **The design names the threshold**: the *Deep drill-down* case shows
 * **four levels in full**, and the *Collapsed* case — labelled *"Beyond four
 * levels"* — replaces the middle with `…`.
 *
 * ⛔ **`text-overflow: ellipsis` would give the wrong answer.** It truncates
 * by *pixels*, so the same trail collapses differently on two screens and the
 * segment that disappears is whichever happens to overflow. 📁 **The design
 * removes the MIDDLE and always keeps the first and the last two** — the
 * root, the parent and where you are — **because those are the three a person
 * navigates by.**
 *
 * ⚡ **And it is `…` as a MENU, not as text**: the collapsed case marks that
 * segment `'menu'`. **The hidden levels stay reachable** rather than becoming
 * an unnavigable gap.
 */

/**
 * 📁 The five kinds the design draws. **`workspace` is its own kind**, from
 * the *Cross-workspace* case — 📁 *"Guest or partner context"* — because a
 * trail that begins in another workspace must say so rather than looking like
 * an ordinary root.
 */
export type CrumbKind = 'link' | 'current' | 'menu' | 'workspace';

export interface Crumb {
  label: string;
  kind: CrumbKind;
  href?: string;
  /** 📁 *"Current record carries its dot"* — a status tone, never decoration. */
  tone?: 'risk' | 'warn' | 'positive';
}

/** 📁 *"Beyond four levels"* — four render in full; five or more collapse. */
export const MAX_VISIBLE = 4;

/**
 * 📁 **Rule 6.** ⛔ **One level is not a trail** — the *Two levels* case is
 * labelled *"Minimum where breadcrumbs appear"*, so a single crumb renders
 * nothing rather than a lonely root.
 */
export function isRequired(trail: readonly Crumb[]): boolean {
  return trail.length >= 2;
}

/**
 * 📁 **Collapse from the middle, keeping the first and the last two.**
 *
 * ⚠️ **The design's collapsed example is `Reports › … › Stage velocity ›
 * Negotiation cohort`** — first, menu, then the final two. ⛔ **Not the last
 * one**: dropping the parent leaves somebody unable to step up one level,
 * which is the move a breadcrumb exists for.
 */
export function collapse(trail: readonly Crumb[]): Crumb[] {
  if (trail.length <= MAX_VISIBLE) return [...trail];
  const first = trail[0];
  if (first === undefined) return [];
  return [
    first,
    { label: '…', kind: 'menu' as const },
    ...trail.slice(-2),
  ];
}

/**
 * ⛔ **A trail whose last segment is not `current` is malformed**, and saying
 * so beats rendering it. **The design's every case ends in `current`** — the
 * page you are on is the one segment that is never a link, because a link to
 * here is a control that does nothing (§2).
 */
export function isWellFormed(trail: readonly Crumb[]): boolean {
  if (trail.length === 0) return true;
  const last = trail[trail.length - 1];
  if (last === undefined || last.kind !== 'current') return false;
  // ⛔ Exactly one `current`, and it is the last.
  return trail.filter((c) => c.kind === 'current').length === 1;
}
