/**
 * **What Companies saves when somebody saves a view** — 📁 the finalized
 * Companies design's *"Save to view"*, on the contract
 * [455 §4](../../../docs/architecture/455-context-definitions-r02-r03.md)
 * established and [TASK-450](../../../docs/BACKLOG.md)–[TASK-452](../../../docs/BACKLOG.md)
 * built and promoted.
 *
 * ## 🔴 The declaration belongs to the CONSUMER
 *
 * 📁 **455 §4 on `workspace_tenancy`**: ***"Never parses, validates, executes,
 * ranks or optimises a declaration. Never knows what a filter or a sort
 * means."*** ⚡ **The store keeps an opaque `dict`**, so the meaning lives in
 * the screen that has one — and **Companies is the third such screen**, after
 * the working list and Reports.
 *
 * ⛔ **That cuts both ways.** **Nothing on the server will ever tell this
 * screen that a declaration is wrong**, so ✅ **it has to refuse one it cannot
 * read** — 📁 which is what [`whyNotReadable`](../views/declaration.ts) is,
 * extracted on the second caller and reused unchanged here rather than
 * reimplemented. ⛔ **A third copy of the three refusals would be the copy that
 * stops being fixed** ([§2](../../../CLAUDE.md)).
 *
 * ## ⚠️ Why the shape is the toolbar's and not the working list's
 *
 * 📁 `working-list.ts` declares `owner`, `raises` and `by` **and reads them
 * from the URL**, because *"the URL is already where that screen keeps the
 * three."* ⛔ **Companies keeps its narrowing in component state**, and a
 * declaration built from the URL would save a view that did not match what the
 * person was looking at. ⚡ **So this declares from the state the screen
 * actually renders from.**
 *
 * ## ⛔ What a saved Companies view deliberately does not carry
 *
 * **Columns and density.** 📁 The design puts them on the toolbar beside
 * *Group* and *Sort*, and it would be reasonable to save them — ⚠️ **but they
 * are how a person likes to READ a list, not which accounts the list holds.**
 * **The views are shared** — 📁 `useSavedViews`: *"everybody in the workspace
 * sees the same list… there is deliberately no **my views** filter"* — **so a
 * saved column choice would reach across a colleague's own preference.**
 * ✅ **A view names a set of companies; a preference stays with the person.**
 */

import { whyNotReadable, type DeclarationKind } from '@/lib/views/declaration';

import {
  NO_FILTERS,
  type Filters,
  type GroupKey,
  type Sort,
  type SortDirection,
  type SortKey,
  type SortTerm,
  GROUPABLE,
  SORTABLE,
} from './table';

/**
 * ⚡ **Bumped only when an OLD declaration would be MISREAD by this screen** —
 * ⛔ **never when a filter is added.** **Adding one leaves every existing view
 * readable**, because a missing key means *not narrowed*, which is what those
 * views meant when they were written.
 */
export const COMPANIES_DECLARATION_VERSION = 1;

const COMPANIES: DeclarationKind = {
  kind: 'companies',
  version: COMPANIES_DECLARATION_VERSION,
  // 📁 **The customer's word, because it appears in the sentence they read**
  // ([ADR-0034](../../../docs/architecture/adr/0034-ubiquitous-language.md)).
  screen: 'Companies',
};

export interface CompaniesDeclaration {
  readonly kind: 'companies';
  readonly version: number;
  readonly filters: Filters;
  /** `null` is *not grouped*, which is a real state rather than a missing one. */
  readonly group: GroupKey | null;
  /** ⚡ **Up to two terms**; empty is the endpoint's own order, oldest first. */
  readonly sort: Sort;
}

export function declare(
  filters: Filters,
  group: GroupKey | null,
  sort: Sort,
): CompaniesDeclaration {
  return { kind: 'companies', version: COMPANIES_DECLARATION_VERSION, filters, group, sort };
}

/**
 * ⚡ **Why a stored view cannot be opened here**, or `null` when it can.
 *
 * ⛔ **A sentence rather than a boolean**, because the screen has to say WHICH
 * view it cannot open — 📁 the same reasoning `LockedField` applies: *a lock
 * with no reason is worse than an absent field.*
 */
export function whyNotReadableHere(declaration: unknown): string | null {
  const frame = whyNotReadable(declaration, COMPANIES);
  if (frame !== null) return frame;

  const candidate = declaration as Partial<CompaniesDeclaration>;
  if (typeof candidate.filters !== 'object' || candidate.filters === null) {
    return 'This view is missing the conditions it was saved with.';
  }
  // ⛔ **A grouping or sort this build has never heard of is REFUSED, not
  // dropped.** ⚡ **Silently ignoring it gives the customer a list that is
  // neither what they saved nor what they asked for, and nothing says so** —
  // 📁 the exact outcome `working-list.ts` calls the worst one.
  if (
    candidate.group !== null &&
    candidate.group !== undefined &&
    !GROUPABLE.some((option) => option.key === candidate.group)
  ) {
    return 'This view groups by something this screen no longer offers.';
  }
  if (candidate.sort !== null && candidate.sort !== undefined) {
    // ⚠️ **A view saved before sort took two keys carried ONE OBJECT.** ⛔ It is
    // refused rather than guessed at: a single term read as an array would
    // apply an arrangement the person never saved.
    if (!Array.isArray(candidate.sort)) {
      return 'This view sorts by something this screen no longer offers.';
    }
    for (const term of candidate.sort as SortTerm[]) {
      if (
        typeof term !== 'object' ||
        term === null ||
        !SORTABLE.some((option) => option.key === term.key) ||
        (term.direction !== 'asc' && term.direction !== 'desc')
      ) {
        return 'This view sorts by something this screen no longer offers.';
      }
    }
  }
  return null;
}

/**
 * **A stored declaration, as this screen's state.**
 *
 * ⚠️ **Call `whyNotReadableHere` FIRST.** ⛔ **This assumes a readable
 * declaration and fills the gaps with *not narrowed*** — which is correct for a
 * view written before a filter existed, and wrong for one this screen cannot
 * read at all.
 */
export function apply(declaration: CompaniesDeclaration): {
  filters: Filters;
  group: GroupKey | null;
  sort: Sort;
} {
  return {
    // ⚡ **Spread over the defaults**, so a view saved before a condition
    // existed reads as *not narrowed by it* rather than as `undefined`.
    filters: { ...NO_FILTERS, ...declaration.filters },
    group: declaration.group ?? null,
    sort: (declaration.sort ?? []).map((term) => ({
      key: term.key as SortKey,
      direction: term.direction as SortDirection,
    })),
  };
}
