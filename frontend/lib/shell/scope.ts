/**
 * **Global scope, and what a module may do to it** —
 * [TASK-1408](../../../docs/BACKLOG.md), against
 * `docs/design-snapshot/screens/Fortune Signora App Shell.dc.html`
 * ([D-138](../../../docs/DECISION_REGISTER.md)).
 *
 * > 📁 **Rule 4 — *"Global scope is read, never overridden, by a module."***
 * > 📁 **Rule 5 — *"Module filters narrow global scope and are outlined, not
 * > tinted."***
 * > 📁 **Precedence — *"Module filters narrow global scope; they never widen
 * > it. **A module cannot silently leave the global period.**"***
 *
 * ## 🔴 Why widening is the defect and not merely a rule
 *
 * ⚡ **The filter strip is a promise about what is on screen.** A seller sets
 * the period to *Q3* and reads every number below it as Q3. ⛔ **A module that
 * quietly widens to *"last 12 months"* — because its own chart looks better
 * with more points — produces a figure that is correct for a question nobody
 * asked**, sitting under a chip that says Q3.
 *
 * **Nothing about that is visible.** The number is right, the label is right,
 * and they describe different periods. ⚡ **So the narrowing is enforced here
 * rather than reviewed**, and {@link narrow} refuses rather than clamps —
 * a silent clamp would produce the correct scope and hide the bug that a
 * module tried.
 *
 * 📁 **Four dimensions, deliberately**: *"Four dimensions cover every module's
 * question. **A fifth belongs to a module, not the shell.**"*
 */

/** 📁 *"period, region, segment, owner"* — the global scope, and all of it. */
export const SCOPE_DIMENSIONS = ['period', 'region', 'segment', 'owner'] as const;
export type ScopeDimension = (typeof SCOPE_DIMENSIONS)[number];

/**
 * A scope value is a set of admitted members per dimension. **An absent
 * dimension means *unconstrained*** — which is why widening is expressible
 * and has to be refused explicitly.
 */
export type Scope = Partial<Record<ScopeDimension, readonly string[]>>;

/** Is `inner` a subset of `outer` on this dimension? An absent outer is all. */
function within(inner: readonly string[], outer: readonly string[] | undefined): boolean {
  if (outer === undefined) return true;
  return inner.every((v) => outer.includes(v));
}

/**
 * ⛔ **Refuses rather than clamps.** ⚡ **A clamp would silently produce the
 * right scope and hide that a module tried to leave it** — and the module
 * would go on believing it had the period it asked for, which is how the
 * mismatch reaches a customer.
 *
 * @throws when the module's filter would admit anything global scope excludes.
 */
export function narrow(global: Scope, moduleFilter: Scope): Scope {
  const widened: string[] = [];

  for (const dim of SCOPE_DIMENSIONS) {
    const inner = moduleFilter[dim];
    if (inner === undefined) continue;
    if (!within(inner, global[dim])) {
      widened.push(
        `${dim}: module admits [${inner.join(', ')}] which global scope does not`,
      );
    }
  }

  if (widened.length > 0) {
    throw new ScopeWidenedError(widened);
  }

  // The narrowed result: the module's constraint where it has one, the
  // global one everywhere else.
  const out: Scope = {};
  for (const dim of SCOPE_DIMENSIONS) {
    const value = moduleFilter[dim] ?? global[dim];
    if (value !== undefined) out[dim] = value;
  }
  return out;
}

export class ScopeWidenedError extends Error {
  constructor(readonly violations: readonly string[]) {
    super(
      `A module filter may only narrow global scope (shell rule 5). ${violations.join('; ')}.`,
    );
    this.name = 'ScopeWidenedError';
  }
}

/**
 * 📁 **Visual grammar — *"Tinted chip = global and persistent. Outlined chip =
 * local and transient."***
 *
 * ⚡ **The tint is not decoration: it is how a person tells what survives
 * navigation.** ⛔ **A module rendering its own filter tinted claims
 * persistence it does not have**, and the customer returns expecting the
 * filter still applied.
 */
export function chipStyle(origin: 'global' | 'module'): 'tinted' | 'outlined' {
  return origin === 'global' ? 'tinted' : 'outlined';
}

/**
 * 📁 **Rule 8 — *"Context that describes content goes in the utility panel;
 * anything with a Save goes in a drawer."*** 📁 **And the panel's own
 * *Never*: *"No forms with a Save, no multi-step flows, no destructive
 * actions."***
 *
 * ⚡ **The reason is dismissal, not taxonomy.** **The panel has no confirm
 * step** — 📁 the drawer's does: *"Escape and scrim click close only when
 * nothing is lost. Otherwise a confirm offers Keep editing, Discard, Save
 * draft."* ⛔ **So a form in the panel is a form somebody loses by clicking
 * a table row**, which is the move the panel exists to make cheap.
 */
export type Surface = 'utility-panel' | 'drawer';

export function surfaceFor(content: {
  hasSave?: boolean;
  multiStep?: boolean;
  destructive?: boolean;
}): Surface {
  return content.hasSave === true || content.multiStep === true || content.destructive === true
    ? 'drawer'
    : 'utility-panel';
}
