/**
 * **Home is a slot, not a screen** — [TASK-1405](../../../docs/BACKLOG.md),
 * against `docs/design-snapshot/screens/Fortune Signora Authenticated Entry.dc.html`
 * ([D-138](../../../docs/DECISION_REGISTER.md)).
 *
 * > 📁 ***"One route, four compositions."*** **`/w/:workspace/home`. What
 * > renders there is resolved from their role, and the resolution is a
 * > composition of cards from a shared catalogue — not a separate screen with
 * > its own layout, navigation or breadcrumb."***
 *
 * ## ⛔ Four compositions, and this file does not invent a fifth
 *
 * 📁 **The design names exactly four and gives each a question it answers.**
 * They are a closed union here for the reason [§2](../../../CLAUDE.md) prefers:
 * **a fifth is unrepresentable rather than discouraged.**
 *
 * ## 🔴 Three of the four cannot be resolved today, and that is raised rather than guessed
 *
 * 📁 **The design resolves a composition from *"the person's primary role"* —
 * CRO, CEO, VP · AE, AM, CSM · RevOps, admin.** ⛔ **The platform publishes no
 * such thing.** **Measured before writing this file**: `Membership.role` is
 * `'owner' | 'member'` and nothing else, and there is no persona, job title or
 * primary-role field on any published contract.
 *
 * ⚠️ **`CommitteeRole` is NOT it, and the near-miss is worth recording.** It
 * carries titles like *"VP of Revenue Operations"* and would read as the answer
 * — but it is **a seat at the *customer's* buying committee**, a fact about an
 * account Signora tracks, not about the person signed in. **Rendering someone's
 * Home from it would be reading the wrong company's org chart.**
 *
 * ✅ **So `Activation` resolves and the other three do not**, and the
 * difference is not a preference: 📁 the design's own qualifier for Activation
 * is ***"Any role, empty workspace"*** — **emptiness is a fact the platform
 * has, and role is not.** ⛔ **[C-268](../../../docs/LANE_COORDINATION.md)
 * carries the gap.**
 *
 * ## ⚡ The guarantee the App Shell depends on
 *
 * 📁 ***"A composition always resolves, so Home ALWAYS renders."*** **That is
 * what `resolveComposition` is for, and why it is total**: it takes what is
 * known and returns a composition for every input, including the one where
 * nothing is known yet.
 */

/**
 * 📁 **The design's four, by its own abbreviations and names.**
 *
 * ⛔ **Not an enum of screens.** Each is a *composition of cards from a shared
 * catalogue*, and the catalogue is what later rows fill.
 */
export type Composition = 'executive' | 'seller' | 'revenue_operations' | 'activation';

/** 📁 What each composition answers, in the design's words. */
export const COMPOSITION_QUESTION: Readonly<Record<Composition, string>> = Object.freeze({
  executive: 'How are we doing?',
  seller: 'What do I do today?',
  revenue_operations: 'Is the system healthy?',
  activation: 'How do I begin?',
});

/** 📁 The design's short label for each, used where a composition is named. */
export const COMPOSITION_NAME: Readonly<Record<Composition, string>> = Object.freeze({
  executive: 'Executive',
  seller: 'Seller',
  revenue_operations: 'Revenue operations',
  activation: 'Activation',
});

/**
 * What the resolver is allowed to look at.
 *
 * ⛔ **`primaryRole` is `null` on every caller today and the type says so
 * rather than the comment.** When a module publishes it, this gains a value and
 * the resolver's rules below start distinguishing the other three — **no caller
 * changes.**
 */
export interface CompositionInput {
  /**
   * ⚡ **Whether the workspace holds anything yet.** 📁 The design's qualifier
   * for Activation is *"Any role, empty workspace"*, so this is the one signal
   * that genuinely decides a composition today.
   */
  readonly workspaceIsEmpty: boolean;
  /**
   * 📁 The person's primary role — CRO · AE · RevOps and the rest.
   * ⛔ **`null` until something publishes it** ([C-268](../../../docs/LANE_COORDINATION.md)).
   */
  readonly primaryRole: 'executive' | 'seller' | 'revenue_operations' | null;
}

/**
 * **Total by construction** — 📁 *"a composition always resolves, so Home
 * ALWAYS renders."*
 *
 * ⛔ **Order matters and it is the design's, not a convenience.** **Emptiness
 * wins over role**: 📁 Activation is *"Any role, empty workspace"*, so a CRO
 * whose workspace holds nothing is asked *"How do I begin?"* rather than shown
 * an executive dashboard of nothing. **A composition of six empty cards is the
 * failure this ordering prevents.**
 *
 * ⚠️ **The fallback is Activation and that is a decision, not a default.** With
 * no role published, the alternative was to pick one of the other three, and
 * **picking would be inventing what a person is** — the thing
 * [D-167](../../../docs/DECISION_REGISTER.md) §4 forbids. **Activation is the
 * only composition that is honest about knowing nothing**: it asks how to
 * begin, which is true of a person the platform cannot yet describe.
 */
export function resolveComposition(input: CompositionInput): Composition {
  if (input.workspaceIsEmpty) return 'activation';
  return input.primaryRole ?? 'activation';
}
