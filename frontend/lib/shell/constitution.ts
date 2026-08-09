/**
 * **The shell's constitution** — [TASK-1408](../../../docs/BACKLOG.md), against
 * `docs/design-snapshot/screens/Fortune Signora App Shell.dc.html`
 * ([D-138](../../../docs/DECISION_REGISTER.md)).
 *
 * > 📁 ***"Every module mounts inside this frame. No component is redesigned
 * > here."***
 *
 * ## ⚡ Why the rules are code rather than a comment
 *
 * 🔴 **The row makes them the acceptance criteria** ([D-210](../../../docs/DECISION_REGISTER.md)):
 * *"the design ends with a numbered constitution and it is what makes every
 * later workflow consistent — read it before the screens."*
 *
 * ⛔ **A constitution in prose is a constitution nobody can violate loudly.**
 * **Fourteen of these govern what a *module* may do to the frame**, and the
 * modules are written by later slices — so the rules have to outlive the
 * session that read them. **`shell-constitution.test.ts` parses the design and
 * compares against this file**, which is the same technique
 * [`lib/system-states/ladder.ts`](../system-states/ladder.ts) uses and the
 * reason a transcription error in either one fails a gate instead of shipping.
 *
 * ⚠️ **Rule 14 is the one that makes the other thirteen durable**: *"Every new
 * shell capability is an amendment to this document, not a local decision."*
 * ⛔ **So this file is not a place to add a rule.** A rule arrives here only
 * after it arrives in the design.
 */

/**
 * 📁 **The fourteen, verbatim and in the design's order.** ⛔ **Order is
 * load-bearing** — they are cited by number in the row and in review.
 */
export const SHELL_RULES = [
  'Modules own the content region and nothing else.',
  'No module may add anything to the top bar.',
  'One primary action per view, and it lives in the page header.',
  'Global scope is read, never overridden, by a module.',
  'Module filters narrow global scope and are outlined, not tinted.',
  'Breadcrumbs are mandatory below the first level.',
  'Anything clickable is reachable in the palette.',
  'Context that describes content goes in the utility panel; anything with a Save goes in a drawer.',
  'Drawers never stack; a second task replaces the first.',
  'At most two banners, environment before commercial.',
  'Toasts confirm background outcomes only, never required reading.',
  'AI surfaces inherit the current scope and state it in their header.',
  'Errors render inside the shell unless the shell itself failed.',
  'Every new shell capability is an amendment to this document, not a local decision.',
] as const;

export type ShellRule = (typeof SHELL_RULES)[number];

/**
 * 📁 **The frame's regions, top to bottom, with the design's own sizes.**
 *
 * ⚡ **The order is the deliverable.** 📁 **Rule 10 — *"At most two banners,
 * environment before commercial"*** — is a statement about *this* sequence,
 * and it is the one a later slice is most likely to break by adding a banner
 * where it is convenient.
 */
export const SHELL_REGIONS = [
  'environment-banner',
  'trial-banner',
  'top-bar',
  'filter-strip',
  'utility-panel',
] as const;
export type ShellRegion = (typeof SHELL_REGIONS)[number];

/**
 * 📁 **The two banner kinds, and the distinction is a rule rather than a
 * style.**
 *
 * **Environment** — 📁 *"Only for sandbox, impersonation and read-only
 * maintenance. **Never for marketing.** Dismissible only when the state is not
 * risky."*
 *
 * **Commercial** — 📁 *"One at a time, dismissible for the session, and never
 * covering the top bar. **Suppressed entirely inside sandbox.**"*
 *
 * ⛔ **A risky environment banner is undismissable**, and that is not a
 * courtesy to remove later: *"Viewing as J. Okafor · every action is logged"*
 * is the sentence that stops somebody believing they are themselves.
 */
export type BannerKind = 'environment' | 'commercial';

export interface BannerRule {
  kind: BannerKind;
  /** 📁 Rule 10's ordering — environment before commercial, always. */
  order: number;
  dismissible: boolean;
  /** 📁 *"Suppressed entirely inside sandbox"* applies to commercial only. */
  suppressedInSandbox: boolean;
}

/**
 * ⚠️ **`risky` is an input because dismissibility depends on it**, not on the
 * banner's kind alone — 📁 *"dismissible only when the state is not risky."*
 * **Impersonation and read-only maintenance are risky; sandbox is not.**
 */
export function bannerRule(kind: BannerKind, risky: boolean): BannerRule {
  return kind === 'environment'
    ? { kind, order: 0, dismissible: !risky, suppressedInSandbox: false }
    : { kind, order: 1, dismissible: true, suppressedInSandbox: true };
}

/** 📁 Rule 10 — *"at most two"*, and it is a maximum rather than a target. */
export const MAX_BANNERS = 2;

/**
 * 📁 **Rule 10, applied.** Returns the banners the frame may actually show,
 * in the design's order.
 *
 * ⛔ **Commercial banners vanish in sandbox rather than queueing.** A trial
 * countdown over a copy of production is an upsell aimed at data that is not
 * real, and 📁 §04's *"no dark patterns"* rule names *"no upsell to someone
 * without the authority to buy"* as the same family.
 */
export function admitBanners<T extends { kind: BannerKind; risky?: boolean }>(
  requested: readonly T[],
  inSandbox: boolean,
): { banner: T; rule: BannerRule }[] {
  // ⚠️ **The banner travels WITH its rule, deliberately.** An earlier version
  // returned rules alone and left the caller to line them back up by index —
  // ⛔ **which is wrong the moment a caller passes commercial first**, because
  // sorting moves it and the indices stop corresponding. **A pairing that
  // cannot come apart beats a comment telling the caller not to separate it**
  // (§2, *types should make incorrect architecture impossible*).
  return requested
    .map((banner) => ({ banner, rule: bannerRule(banner.kind, banner.risky ?? false) }))
    .filter(({ rule }) => !(inSandbox && rule.suppressedInSandbox))
    .sort((a, b) => a.rule.order - b.rule.order)
    .slice(0, MAX_BANNERS);
}

/**
 * 📁 **Rule 13 — *"Errors render inside the shell unless the shell itself
 * failed."*** ⚡ **This is the seam to [TASK-1409](../../../docs/BACKLOG.md)'s
 * ladder**, and the two documents agree without either one being adjusted:
 * that row says *"app scope renders INSIDE this frame; platform scope replaces
 * it."*
 *
 * ⛔ **Region and page scope render inside. App and platform replace the
 * frame.** **The `500` is the interesting case and the design puts it inside**
 * — a client crash still leaves navigation worth keeping, and taking the frame
 * away removes the only route out.
 */
export function rendersInsideShell(scope: 'region' | 'page' | 'app' | 'platform'): boolean {
  return scope !== 'platform';
}
