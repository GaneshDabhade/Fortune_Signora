/**
 * **Whether the shell knows which organization it is in** — the gate that
 * decides between the frame's content and a skeleton.
 *
 * ⚡ **A pure function rather than a branch in the shell**, for the reason
 * 📁 [`rail.ts`](./rail.ts) already gives about its own rulings: a branch inside
 * a component can only be tested through the component, and this one has four
 * inputs and a defect that only appears in one of the sixteen combinations.
 *
 * ## 🔴 The combination it was written for: [B-237](../../../docs/BUGS.md)'s `/`
 *
 * ⛔ **An errored read was treated as *not yet known*, and that turned the whole
 * screen into a loop that never ended.**
 *
 * ⚡ **`shouldRetry` allows two retries for a 5xx, and a query stays `pending`
 * while its retries are in flight** — so `isLoading` is true for ~3s of every
 * cycle. **The gate was shut almost continuously.** ✅ **And the ~30ms it
 * opened was exactly long enough to do damage**: the entry page mounted, its
 * `useWorkspaces` observer was added to a query holding no data, React Query
 * refetched on mount, and **the gate shut again.**
 *
 * ```
 *   1.04  2.03  0.03  │  1.02  2.04  0.03  │  1.01  2.02  0.03  │  …
 *   └── the two retries ──┘  └── a fresh query, 30ms after the error
 * ```
 *
 * 🔴 **QE measured 22 reads in 22 seconds and `isError` reached and discarded
 * every time.** ⛔ **The entry page's own `unresolved` branch was never allowed
 * to render**, so a customer saw *"Loading…"* indefinitely rather than the
 * failure the page was ready to state.
 *
 * ✅ **A failed read IS an answer.** ⚡ *"We could not find out"* is knowing
 * something; the screens below can then say so — 📁
 * [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md).
 */
export function workspaceKnown(input: {
  /** The read is in flight, retries included. */
  readonly isLoading: boolean;
  /** ⚡ **Truthiness, not `!== null`.** ⛔ A caller that omits it must not be
   *  read as having failed — the mistake that turned twelve tests red once. */
  readonly error: unknown;
  readonly activeWorkspace: unknown;
  readonly workspaceCount: number;
}): boolean {
  // 🔴 **First, and deliberately.** ⛔ Every other clause below asks *"has the
  // answer arrived?"*, and a failure IS an arrival.
  if (input.error) return true;

  /**
   * ⚠️ **`!isLoading` alone is not sufficient, and that is the subtle half.**
   * 📁 The provider chooses the active workspace in an effect that runs *after*
   * the list arrives, so there is a render where loading has finished and
   * `activeWorkspace` is still `null`. **The question is answered when there is
   * an active organization, or when the list came back and there are none.**
   */
  return !input.isLoading && (input.activeWorkspace !== null || input.workspaceCount === 0);
}

/**
 * 🔴 **Whether the person must choose** — 📁 the Workspace Chooser's **rule 7**,
 * `WS_AMBIGUOUS`: *"Two or more active memberships and no pin, no last-used.
 * The system genuinely cannot decide. The chooser is mandatory here and only
 * here."*
 *
 * ## ⛔ Why this exists rather than a fifth clause in `workspaceKnown`
 *
 * ⚠️ **`workspaceKnown` answers *has the answer arrived?* and it is still
 * right to say NO here** — the list has settled and nothing is selected, which
 * is genuinely not an answer about *which organization this is*.
 *
 * ⚡ **This is a different question: *whose answer is it?*** ⛔ **And it has a
 * different consequence** — the shell renders a skeleton while the answer is
 * merely late, and **navigates when the answer is the person's to give.**
 * Collapsing the two would make a skeleton mean *"we are waiting for you"*,
 * which no skeleton can say.
 *
 * ## 🔴 [B-245](../../../docs/BUGS.md) is what the absence cost
 *
 * ⛔ **The provider used to answer for them** — `workspaces[0]`, over a
 * newest-first list — **so the newest organization became every fresh
 * browser's default, permanently, and nothing in the product deletes one.**
 *
 * ⚠️ **`> 1`, not `>= 1`.** 📁 **Rule 6**: *"exactly one active membership —
 * nothing to choose. No picker, no confirmation, no strip."* ⛔ **A person
 * with one organization must never see the chooser**, and the provider enters
 * it for them; **a count of one reaching here would be a defect upstream, not
 * a reason to ask.**
 *
 * ⚡ **`error` short-circuits first, and it is not defensive noise.** ⛔ A
 * failed read reports zero memberships, and **routing somebody to the chooser
 * because their organizations could not be loaded would state something about
 * their access from a fact about a request** — 📁
 * [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md).
 */
export function workspaceChoiceRequired(input: {
  readonly isLoading: boolean;
  readonly error: unknown;
  readonly activeWorkspace: unknown;
  readonly workspaceCount: number;
}): boolean {
  if (input.error) return false;
  if (input.isLoading) return false;
  return input.activeWorkspace === null && input.workspaceCount > 1;
}
