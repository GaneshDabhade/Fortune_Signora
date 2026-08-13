/**
 * **Selecting companies to act on together** — [TASK-466](../../../docs/BACKLOG.md),
 * against 📁 `Fortune Signora Companies.dc.html`.
 *
 * ## 🔴 The design draws two different *all*s, and confusing them is the defect
 *
 * 📁 ***"✓ 41 selected of 312 in view · Select all 312"*** — **the header
 * checkbox selects the rows ON SCREEN; the link beside it selects the whole
 * filtered set.** ⛔ **A bulk action applied to the wrong one is applied to
 * accounts the customer never saw**, which on *Add tag* is untidy and on
 * anything destructive is not.
 *
 * ⚡ **So the two are separate states rather than one flag with a count.** The
 * type carries which the customer chose, and a caller cannot read *"how many"*
 * without also reading *"which set."*
 *
 * ## ⛔ What this file does NOT know
 *
 * **It holds ids, never rows.** A page turn replaces the rows and must not
 * empty the selection — 📁 the design keeps the bar up across pages, and a
 * selection that silently reset would apply an action to fewer accounts than
 * the customer was told.
 */

/**
 * ⚡ **Two shapes, and the discriminant is the point.**
 *
 * `explicit` names ids. `all-matching` names none — **because the set is
 * whatever the filters currently match, which the server resolves and the
 * client must not enumerate.** 📁 The design's *"Select all 312"* on a table
 * showing 50 is exactly that: the customer chose a *query*, not 312 rows they
 * have looked at.
 */
export type Selection =
  | { readonly kind: 'explicit'; readonly ids: ReadonlySet<string> }
  | { readonly kind: 'all-matching'; readonly count: number };

export const NOTHING_SELECTED: Selection = { kind: 'explicit', ids: new Set() };

export function isEmpty(selection: Selection): boolean {
  return selection.kind === 'explicit' && selection.ids.size === 0;
}

/** How many companies an action would touch. */
export function selectedCount(selection: Selection): number {
  return selection.kind === 'explicit' ? selection.ids.size : selection.count;
}

export function isSelected(selection: Selection, id: string): boolean {
  // ⚡ **Every row reads as selected under `all-matching`**, which is what the
  // customer asked for — and the header checkbox stays ticked as they page.
  return selection.kind === 'all-matching' || selection.ids.has(id);
}

/**
 * ⛔ **Toggling one row leaves `all-matching`**, and does not merely remove an
 * id from it.
 *
 * ⚡ **There is no such thing as *"all 312 except this one"* in a set the
 * client cannot enumerate** — so un-ticking a row collapses the selection to
 * the rows actually on screen, minus that one. 📁 **The customer sees the
 * count drop from 312 to 49, which is honest**: they no longer have the whole
 * filtered set selected, and a bar that kept saying 311 would be describing a
 * set nothing could produce.
 */
export function toggle(
  selection: Selection,
  id: string,
  onScreen: readonly string[],
): Selection {
  if (selection.kind === 'all-matching') {
    return { kind: 'explicit', ids: new Set(onScreen.filter((each) => each !== id)) };
  }
  const ids = new Set(selection.ids);
  if (ids.has(id)) ids.delete(id);
  else ids.add(id);
  return { kind: 'explicit', ids };
}

/**
 * 📁 **The header checkbox** — *"41 selected of 312 in view"*.
 *
 * ⚡ **It selects what is on screen and nothing else**, so a customer who
 * ticks it has selected rows they can see.
 */
export function selectOnScreen(onScreen: readonly string[]): Selection {
  return { kind: 'explicit', ids: new Set(onScreen) };
}

/** 📁 **The link beside it** — *"Select all 312"*. */
export function selectAllMatching(count: number): Selection {
  return { kind: 'all-matching', count };
}

/**
 * ⚡ **Whether the header checkbox shows ticked, mixed, or empty.**
 *
 * ⛔ **Mixed is a real third state, not a rounding of *some*.** 📁 A checkbox
 * that showed ticked while half the rows were unselected would make *Select
 * all* look like a no-op, and a customer would press an action believing it
 * covered the page.
 */
export type HeaderState = 'none' | 'some' | 'all';

export function headerState(selection: Selection, onScreen: readonly string[]): HeaderState {
  if (selection.kind === 'all-matching') return 'all';
  if (onScreen.length === 0) return 'none';
  const chosen = onScreen.filter((id) => selection.ids.has(id)).length;
  if (chosen === 0) return 'none';
  return chosen === onScreen.length ? 'all' : 'some';
}

/**
 * 🔴 **Whether *Select all N* is worth offering at all.**
 *
 * ⛔ **Not when the filtered set is already on screen.** 📁 The design shows it
 * beside *"41 selected of 312 in view"* — **the link exists because there are
 * accounts the customer has not seen.** ⚡ Offering it on a 12-row result would
 * be a control that changes nothing, and a person who pressed it and saw no
 * count change would reasonably think the product was broken.
 */
export function offersSelectAll(
  selection: Selection,
  onScreen: readonly string[],
  totalMatching: number,
): boolean {
  return (
    selection.kind === 'explicit' &&
    onScreen.length > 0 &&
    totalMatching > onScreen.length
  );
}

/**
 * ⛔ **Which rows an action can be given, and it is deliberately partial.**
 *
 * ⚡ **`all-matching` returns `null` rather than the rows on screen.** 📁 The
 * customer selected 312 and the client holds 50; **handing an action the 50
 * would apply it to a sixth of what the bar says.** The caller must resolve
 * the set on the server or refuse — and `null` is what makes that
 * unforgettable.
 */
export function resolvedIds(selection: Selection): readonly string[] | null {
  return selection.kind === 'explicit' ? [...selection.ids] : null;
}
