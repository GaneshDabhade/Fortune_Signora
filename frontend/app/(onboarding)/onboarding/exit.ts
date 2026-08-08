/**
 * **Where onboarding lets go** — [TASK-469](../../../../docs/BACKLOG.md).
 *
 * ## 🔴 This is a seam, and it exists because the flow may not choose
 *
 * **The coordination source carries a notice naming this row directly**
 * (`origin/coordination`, republished 2026-08-08, [D-144](../../../../docs/DECISION_REGISTER.md)
 * is what makes that a ref this lane reads):
 *
 * > ***"D-193/D-194: 'Authenticated Entry' is now the authority for ALL
 * > post-login behaviour. TASK-468 and TASK-469 (both yours) have NO DEFINED
 * > EXIT and the spec says both must exit through `resolveEntry` with
 * > `intent=null` — do NOT choose a destination in either flow."***
 *
 * ### ⛔ What could not be done, and why it was not faked
 *
 * **`resolveEntry` does not exist**, and **D-193/D-194 are not in the decision
 * register on `origin/integration`** — both measured this poll, not assumed.
 * [§20e](../../../../CLAUDE.md) is explicit that **executable work comes from
 * `integration` and nowhere else**, and that a ruling is *authoritative* when
 * the product owner makes it but only *actionable* when `integration` records
 * it. **Writing a `resolveEntry` here would be this lane inventing the spec's
 * shape**, and the next row would inherit a guess wearing a ruling's name.
 *
 * ### ✅ What could be done, and is
 *
 * **The prohibition needs nothing that does not exist.** *"Do not choose a
 * destination in the flow"* is obeyable today: the choice is no longer made
 * inside a form — it is made **once, here, on a line whose whole purpose is to
 * be replaced.**
 *
 * ⚠️ **The behaviour is unchanged on purpose.** `/` is where the flow already
 * landed, so this moves nothing a customer would notice; **it converts a
 * decision scattered through a screen into one seam a later row deletes.**
 * ⛔ **Changing the destination as well would be choosing one**, which is the
 * thing the notice forbids.
 */

/**
 * The destination a finished or abandoned run hands back to.
 *
 * 🔴 **When D-193/D-194 reach `integration`, this function becomes
 * `resolveEntry({ intent: null })` and nothing else in the flow changes.**
 * That is the entire reason it is a function and not a string constant: a
 * constant would still have to be *read* at three call sites, and the row that
 * lands the spec would be editing three of them.
 */
export function onboardingExit(): string {
  // ⛔ Not a product decision. It is today's behaviour, held in one place
  // until the authority for post-login entry exists on the branch this lane
  // builds from.
  return '/';
}
