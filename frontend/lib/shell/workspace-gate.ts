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
