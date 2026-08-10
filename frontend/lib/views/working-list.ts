/**
 * **What the working list saves when somebody saves a view** —
 * [TASK-452](../../../docs/BACKLOG.md), on
 * [455 §4](../../../docs/architecture/455-context-definitions-r02-r03.md).
 *
 * ## 🔴 The declaration belongs to the CONSUMER, and that is the contract
 *
 * 📁 **455 §4 on `workspace_tenancy`**: ***"Never parses, validates, executes,
 * ranks or optimises a declaration. Never knows what a filter or a sort
 * means."*** ⚡ **The store keeps an opaque `dict`** — *"stores the query, the
 * filters and the sort — **not the results**"* — **so the meaning lives here,
 * in the screen that has one.**
 *
 * ⛔ **That cuts both ways.** **Nothing on the server will ever tell this
 * screen that a declaration is wrong**, so ✅ **this module has to be the thing
 * that refuses one it does not understand.**
 *
 * ## ⚡ One consumer, deliberately
 *
 * 📁 **455 §4**: *"a contract proven by one real caller before six adopt it…
 * a port with seven simultaneous first callers has no chance of being
 * corrected cheaply."* ✅ **The working list is that caller.** ⛔ **The other
 * three named consumers — App Shell, Global Search, Reports — get their own
 * declaration when they arrive**, and each owns its own shape.
 *
 * ## 🔴 Why a version, and why a refusal rather than a best effort
 *
 * ⚠️ **A saved view outlives the screen that wrote it.** 📁 The store is
 * explicit that *"a declaration is never edited — a change is a new version
 * naming the one it replaces"*, **so a view written in January is still
 * readable in June, by a list whose filters have moved on.**
 *
 * ⛔ **Applying a declaration this screen only partly recognises is the worst
 * outcome**: **the customer gets a list that is neither what they saved nor
 * what they asked for, and nothing says so.** ✅ **So an unrecognised
 * declaration is REFUSED and the reason is available to the caller** — the
 * same rule the attribution strip applies to an absent confidence
 * ([TASK-1411](../../../docs/BACKLOG.md)): **state the absence, never
 * approximate it.**
 */

import { scopeFrom, type OwnerScope } from '@/lib/state/owner-scope';

/**
 * ⚡ **Bumped only when an OLD declaration would be misread by this screen** —
 * ⛔ **not when a filter is added.** **Adding one leaves every existing view
 * readable**, because a missing key means *not narrowed*, which is what those
 * views meant when they were written.
 */
export const WORKING_LIST_DECLARATION_VERSION = 1;

/** ⚡ **The list's own three questions**, and the URL is already the source. */
export interface WorkingListDeclaration {
  readonly kind: 'working-list';
  readonly version: number;
  /** Whose accounts — `all` · `mine` · `unassigned`. */
  readonly owner: OwnerScope;
  /** Which question the list is narrowed to. `null` is *not narrowed*. */
  readonly raises: string | null;
  /** Where everything stands. `null` is *not grouped*. */
  readonly by: string | null;
}

/**
 * **The current list, as something that can be stored.**
 *
 * ⛔ **Reads the URL rather than component state**, because the URL is already
 * where this screen keeps the three — *"a refresh, a browser back and a second
 * tab"* — ⚡ **and a view saved from anything else would not match what the
 * person is looking at.**
 */
export function declare(params: URLSearchParams): WorkingListDeclaration {
  return {
    kind: 'working-list',
    version: WORKING_LIST_DECLARATION_VERSION,
    owner: scopeFrom(params.get('owner')),
    raises: params.get('raises'),
    by: params.get('by'),
  };
}

/**
 * ⚡ **Why a stored declaration cannot be applied**, or `null` when it can.
 *
 * ⛔ **A string rather than a boolean**, because the screen has to be able to
 * say WHICH view it cannot open — 📁 the same reasoning `LockedField` applies:
 * *a lock with no reason is worse than an absent field, because the customer
 * now knows something is missing and not why.*
 */
export function whyNotApplicable(declaration: unknown): string | null {
  if (typeof declaration !== 'object' || declaration === null) {
    return 'This view was saved in a form this list cannot read.';
  }

  const candidate = declaration as Partial<WorkingListDeclaration>;

  if (candidate.kind !== 'working-list') {
    /**
     * ⚡ **The commonest real case, and it is not an error.** 📁 The store is
     * workspace-wide and 455 names four consumers, **so a Reports view and a
     * working-list view sit in the same list** — ⛔ **and opening one on the
     * other would silently show the wrong records.**
     */
    return 'This view belongs to a different screen.';
  }

  if (typeof candidate.version !== 'number' || candidate.version > WORKING_LIST_DECLARATION_VERSION) {
    // ⚠️ **Newer than this build.** ⛔ **Refused rather than partly applied**:
    // the customer would get a list that is neither what they saved nor what
    // they asked for, and nothing would say so.
    return 'This view was saved by a newer version of Signora.';
  }

  return null;
}

/**
 * **A stored declaration as URL parameters**, or `null` if it cannot be read.
 *
 * ⚡ **Returns the query string rather than navigating**, so the caller owns
 * the routing and this stays testable without a router.
 */
export function apply(declaration: unknown): string | null {
  if (whyNotApplicable(declaration) !== null) return null;

  const { owner, raises, by } = declaration as WorkingListDeclaration;
  const params = new URLSearchParams();

  // ⛔ **`all` is the absence of a narrowing, so it is not written.** ⚡ A URL
  // carrying every default is a URL nobody can read at a glance, and
  // `scopeFrom` already answers `all` for a missing value.
  if (owner !== 'all') params.set('owner', owner);
  if (raises !== null && raises !== '') params.set('raises', raises);
  if (by !== null && by !== '') params.set('by', by);

  const query = params.toString();
  return query === '' ? '' : `?${query}`;
}

/**
 * ⚡ **What the saved view is called, when nobody typed a name.**
 *
 * ⛔ **Never *"Untitled"*.** 📁 The store bounds a name at 200 characters
 * *"long enough for a sentence a person would actually type"* — **so the
 * default describes the filters rather than apologising for their absence**,
 * and somebody scanning a list of views can tell them apart.
 */
export function describe(declaration: WorkingListDeclaration): string {
  const parts: string[] = [];
  if (declaration.owner === 'mine') parts.push('My accounts');
  else if (declaration.owner === 'unassigned') parts.push('Unassigned accounts');
  else parts.push('All accounts');
  if (declaration.raises !== null && declaration.raises !== '') {
    parts.push(`raising ${declaration.raises}`);
  }
  if (declaration.by !== null && declaration.by !== '') parts.push(`by ${declaration.by}`);
  return parts.join(' · ');
}
