/**
 * **The three refusals every saved-view consumer owes** —
 * [455 §4](../../../docs/architecture/455-context-definitions-r02-r03.md).
 *
 * ## 🔴 Why this is shared when the declarations are not
 *
 * 📁 **455 §4 on `workspace_tenancy`**: ***"Never parses, validates, executes,
 * ranks or optimises a declaration. Never knows what a filter or a sort
 * means."*** ⛔ **So nothing on the server will ever tell a screen that a
 * declaration is wrong**, and ✅ **every consumer has to refuse what it cannot
 * read.**
 *
 * ⚡ **The SHAPE of each declaration belongs to its own screen and is not
 * shared** — 📁 455 names four consumers and each owns its own meaning.
 * ✅ **The three refusals are identical for all of them**, because they are
 * about the STORE rather than about any screen: **the store is workspace-wide,
 * it is opaque, and it outlives the build that wrote a row.**
 *
 * ## ⚠️ Extracted on the SECOND caller, deliberately — not the first
 *
 * 📁 **455 §4**: *"a contract proven by one real caller before six adopt it…
 * a port with seven simultaneous first callers has no chance of being
 * corrected cheaply."* ✅ **The working list was that first caller**
 * ([TASK-452](../../../docs/BACKLOG.md)); **Reports is the second**
 * ([TASK-1417](../../../docs/BACKLOG.md)), **and two callers is where a shared
 * frame stops being speculation** ([§6](../../../CLAUDE.md): *do not add
 * generalization for hypothetical future needs*).
 */

/** ⚡ **What a consumer must state about itself** to be able to refuse. */
export interface DeclarationKind {
  /** ⛔ **Which screen's declaration this is.** Never shared between two. */
  readonly kind: string;
  /**
   * ⚡ **Bumped only when an OLD declaration would be MISREAD by this screen** —
   * ⛔ **never when a field is added.** **Adding one leaves every existing
   * declaration readable**, because a missing key means *not narrowed*, which
   * is what those declarations meant when they were written.
   */
  readonly version: number;
  /**
   * 📁 **The screen's own name, in the customer's words**
   * ([ADR-0034](../../../docs/architecture/adr/0034-ubiquitous-language.md)) —
   * it appears in the sentence a person reads, so it is never a module name.
   */
  readonly screen: string;
}

/**
 * ⚡ **Why a stored declaration cannot be opened here**, or `null` when it can.
 *
 * ⛔ **A sentence rather than a boolean**, because the screen has to be able to
 * say WHICH view it cannot open — 📁 the same reasoning `LockedField` applies:
 * *a lock with no reason is worse than an absent field, because the customer
 * now knows something is missing and not why.*
 */
export function whyNotReadable(declaration: unknown, self: DeclarationKind): string | null {
  if (typeof declaration !== 'object' || declaration === null || Array.isArray(declaration)) {
    return 'This view was saved in a form this screen cannot read.';
  }

  const candidate = declaration as { kind?: unknown; version?: unknown };

  if (candidate.kind !== self.kind) {
    /**
     * ⚡ **The commonest real case, and it is not an error.** 📁 The store is
     * workspace-wide and 455 names four consumers, **so a Reports definition
     * and a working-list view sit in the same list** — ⛔ **and opening one on
     * the other would silently show the wrong records.**
     */
    return 'This view belongs to a different screen.';
  }

  if (typeof candidate.version !== 'number' || candidate.version > self.version) {
    // ⚠️ **Newer than this build.** ⛔ **Refused rather than partly applied**:
    // the customer would get something that is neither what they saved nor
    // what they asked for, and nothing would say so.
    return 'This view was saved by a newer version of Signora.';
  }

  return null;
}
