/**
 * **Home is one route with four compositions** —
 * 📁 `docs/design-snapshot/screens/Fortune Signora Home.dc.html`
 * ([D-138](../../../docs/DECISION_REGISTER.md)).
 *
 * > 📁 ***"Resolution is a pure function of three inputs. Activation state, then
 * > a stored preference, then the primary role. Evaluated in that order, first
 * > match wins, no network call inside the decision."***
 *
 * ## ⚡ The Home document is the composition authority, and it changed two things
 *
 * ⚠️ **This file was written against `Fortune Signora Authenticated Entry`**, and
 * 📁 **the Home document supersedes it as the composition authority** — its own
 * reconciliation table says so: *"Executive Dashboard remains the design of
 * composition one; composition authority moves here."* **Two corrections
 * follow.**
 *
 * ### 🔴 ① The fallback is SELLER, not activation
 *
 * 📁 **Rule 5: *"Anything else — AE, AM, CSM, analyst, guest with membership …
 * The default and the most common outcome."*** ⛔ **This returned `activation`
 * for an unknown role**, which state 04 forbids: *"All blocking cards complete →
 * composition switches to SELLER, OPERATIONS or EXECUTIVE."* **A fully activated
 * workspace whose reader has no stated role would have rendered a setup sequence
 * for a product that is already set up.**
 *
 * ### ✅ ② The primary role now EXISTS, and [C-268](../../../docs/LANE_COORDINATION.md) is closed
 *
 * ⚠️ **This file said *"the platform publishes no such thing"* and that was true
 * when it was written.** ⚡ **Onboarding screen `05` asks for it** — 📁 *"Role and
 * team size. **Role sets the home page and the alert routing**"* — and stores it
 * on the run with its provenance. **The design said what the field was for; the
 * flow now collects it.**
 *
 * ⛔ **`Membership.role` is still NOT it** (`owner | member` is a membership fact,
 * not a job), and ⛔ **`CommitteeRole` is still not it** — that is a seat at the
 * *customer's* buying committee, and resolving somebody's Home from it would be
 * reading the wrong company's org chart. **Both near-misses are kept on the
 * record because both are one grep away from looking correct.**
 *
 * ## ⚡ Still total, and that is the App Shell's guarantee
 *
 * 📁 ***"A composition always resolves, so Home ALWAYS renders."*** Every input
 * returns a composition, including the one where nothing is known.
 */

/**
 * 📁 **The design's four.** ⛔ A closed union, so a fifth is unrepresentable
 * rather than discouraged ([§2](../../../CLAUDE.md)).
 */
export type Composition = 'executive' | 'seller' | 'revenue_operations' | 'activation';

/** 📁 What each composition answers, in the design's words. */
export const COMPOSITION_QUESTION: Readonly<Record<Composition, string>> = Object.freeze({
  executive: 'How are we doing?',
  seller: 'What do I do today?',
  revenue_operations: 'Is the system healthy?',
  activation: 'How do I begin?',
});

/** 📁 The design's short label for each. */
export const COMPOSITION_NAME: Readonly<Record<Composition, string>> = Object.freeze({
  executive: 'Executive',
  seller: 'Seller',
  revenue_operations: 'Revenue operations',
  activation: 'Activation',
});

/**
 * 📁 **Onboarding screen `05`'s six roles**, which are the only stated roles this
 * product has. ⛔ **Not re-declared here** — the values are
 * `backend/modules/workspace_tenancy/domain/onboarding.py`'s `Role`, and a second
 * list would be the copy that drifts ([§2](../../../CLAUDE.md)).
 */
export type StatedRole =
  | 'revenue_leader'
  | 'account_executive'
  | 'sales_operations'
  | 'customer_success'
  | 'marketing'
  | 'executive';

/**
 * 📁 **The design's rules 3 and 4, as a table rather than a chain of `if`s.**
 *
 * | Rule | Design's wording | Onboarding's roles |
 * |---|---|---|
 * | 3 | *"CRO, CEO, VP or Sales Director"* | `revenue_leader` · `executive` |
 * | 4 | *"RevOps, workspace admin or integration admin"* | `sales_operations` |
 * | 5 | *"AE, AM, CSM, analyst, guest"* | everything else |
 *
 * ⛔ **`marketing` resolves to SELLER and that is a reading, not an omission.**
 * 📁 Rule 3 lists revenue leadership by title and rule 4 lists operators;
 * marketing is neither, so rule 5 — *"anything else"* — takes it. ⚠️ **Recorded
 * because it is the one role of the six the design does not name.**
 */
const COMPOSITION_FOR_ROLE: Readonly<Record<StatedRole, Composition>> = Object.freeze({
  revenue_leader: 'executive',
  executive: 'executive',
  sales_operations: 'revenue_operations',
  account_executive: 'seller',
  customer_success: 'seller',
  marketing: 'seller',
});

/**
 * 📁 **The three inputs, in the design's own order.**
 *
 * ⛔ **No network call may be made from inside the decision** — the design says
 * so, and it is why these are values rather than hooks.
 */
export interface CompositionInput {
  /**
   * 📁 **Rule 1 — *"No integration has ever completed a sync."***
   *
   * ⚠️ **This used to be *"the workspace holds nothing"*, read from the target-
   * account version.** ⛔ **That is a different question**: a workspace can
   * declare no target accounts and still be fully connected, and the design's
   * test is about *connection*, not content. 📁 Content emptiness is state `05`
   * (`no-business-data`), which renders a role composition rather than
   * activation — **so conflating them sent a set-up customer back to setup.**
   */
  readonly neverSynced: boolean;
  /**
   * 📁 **Rule 2 — *"Person has set a start-page preference of a specific
   * composition… Honoured over role."*** `null` when they have not.
   */
  readonly preference: Composition | null;
  /**
   * 📁 **Rules 3–5 — the person's stated role**, from onboarding screen `05`.
   * `null` when they skipped that step, which rule 5 covers.
   */
  readonly statedRole: StatedRole | null;
}

/**
 * **Total by construction**, and the order is the design's.
 *
 * ⚡ **Activation precedes preference and role, deliberately.** 📁 The design's
 * own reason: *"a workspace with no connected source cannot render a data
 * composition regardless of who is looking at it"*, and P-01 — *"rendering an
 * empty executive dashboard to an executive is the worst first impression
 * available."*
 *
 * ⛔ **A preference cannot override activation**, which is why rule 1 is checked
 * before it. ✅ **A preference DOES override role**, which is why it is checked
 * before that.
 */
export function resolveComposition(input: CompositionInput): Composition {
  // 📁 Rule 1.
  if (input.neverSynced) return 'activation';
  // 📁 Rule 2.
  if (input.preference !== null) return input.preference;
  // 📁 Rules 3 and 4.
  if (input.statedRole !== null) return COMPOSITION_FOR_ROLE[input.statedRole];
  // 📁 Rule 5 — *"the default and the most common outcome."*
  return 'seller';
}

/**
 * 📁 **Which compositions a person may switch between** — *"only users with
 * multiple permitted compositions see it"*, and *"single-role people do not see
 * an unnecessary switcher."*
 *
 * ⚡ **A person may always reach the composition their role resolves to, and the
 * SELLER default**, because the design describes exactly that case: *"a person
 * with two roles gets the narrower one and may switch once, remembered."*
 *
 * ⛔ **Activation is never switchable.** 📁 It is resolved by a fact about the
 * workspace, not a preference — offering a way out of it would offer a way to
 * hide setup from somebody who still has to do it.
 */
export function switchableCompositions(statedRole: StatedRole | null): readonly Composition[] {
  if (statedRole === null) return ['seller'];
  const own = COMPOSITION_FOR_ROLE[statedRole];
  return own === 'seller' ? ['seller'] : [own, 'seller'];
}
