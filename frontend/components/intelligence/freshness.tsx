import { howLongAgo } from '@/components/intelligence/dates';

/**
 * How current Signora's knowledge of an account is.
 *
 * **The product's whole promise is *here is what changed*, and until now it
 * never said when it last learned anything.** A seller reading a score has no
 * way to tell *"nothing is happening at this account"* from *"nothing has
 * reached us since March"* — and those demand opposite actions. One is a
 * reason to stop working the account; the other is a reason to distrust the
 * page.
 *
 * ### It says *observed*, not *checked*, and the difference is not pedantry
 *
 * **Signora cannot currently say when it last looked.** `provider_sync` records
 * a run but carries no subject, so it cannot say *which* account it was for;
 * `provider_watermark.position` is per subject but advances only when records
 * arrive, so an account a provider checked and found nothing about is
 * indistinguishable from one it never checked. The only per-account fact that
 * exists is when the newest evidence was **observed by the provider that
 * reported it**.
 *
 * So that is what this says. Rendering *"Last checked today"* on a fact that
 * means *"the newest thing we hold was seen today"* would be the product
 * claiming a capability it does not have, on the surface where trust is being
 * built. The gap is real and is recorded for a later slice; **the honest
 * smaller sentence ships now.**
 *
 * ### Why days rather than hours
 *
 * `howLongAgo` is day-precision by an existing decision this reuses rather than
 * relitigates: evidence decays in bands measured in weeks, and a provider's
 * `observed_at` is frequently day-granular anyway. *"2 hours ago"* would be
 * false precision — a resolution the pipeline does not have, printed in a place
 * a customer would take literally.
 *
 * ### Where this goes next
 *
 * The eventual shape is a shared vocabulary for *last updated*, *last
 * researched*, *last synchronized*, *awaiting provider update*, *never
 * collected* and *collection in progress*. **None of those is built here**, and
 * no prop anticipates them (§6). What makes the evolution natural is that this
 * component owns the *sentence*, not the caller — a second kind arrives as a
 * second export beside this one, or as a prop the day there are two callers,
 * and no call site has to change to allow either.
 *
 * ⚡ **The second kind arrived, as `LastChecked` below.** A second export
 * rather than a prop, because the two answer different questions on different
 * screens — and this one's refusal to say *checked* is not relaxed by the
 * other becoming able to say it.
 */
export function Freshness({ observedAt }: { observedAt: string | null }) {
  return (
    <p className="text-xs text-content-subtle">
      {observedAt === null
        ? // **Absence stated, never blank.** A missing line reads as a page
          // that forgot to render something; this reads as an answer, and it
          // is the answer that should stop a seller trusting the score above.
          //
          // `null` only — the caller renders nothing at all until the identity
          // has arrived, because *not yet known* and *nobody has ever reported
          // anything* are different facts and only one of them is this
          // sentence.
          'No evidence collected yet'
        : `Latest evidence · ${howLongAgo(observedAt)}`}
    </p>
  );
}

/**
 * Whether Signora has actually looked at a company, and when — **A7**.
 *
 * **The half `Freshness` above deliberately refuses.** That line says when the
 * newest evidence was *observed by a provider*; it cannot say when anybody last
 * *looked*, because until `attempted_at` shipped nothing recorded it. So a
 * seller reading *"Latest evidence · 5 weeks ago"* could not tell whether the
 * account went quiet or the pipeline did — and those demand opposite actions.
 *
 * ### It says *checked*, and that word is now true
 *
 * `Freshness` still may not use it and its test still asserts the refusal.
 * **That refusal is not lifted here; it is scoped.** The fact behind this line
 * is a completed read of a named company, written on every run whether or not
 * anything came back — so on this screen *checked* is a claim the repository
 * supports, and on the brief it still is not.
 *
 * ### Four states, and none may collapse into another
 *
 * The pair that matters is *nobody has looked* against *somebody looked and
 * there was nothing there*: identical before this slice, opposite in what a
 * seller should do about them. The fourth — evidence with no recorded attempt —
 * is what rows written before the column existed look like, and it says so
 * rather than inventing a date or claiming nobody checked.
 */
export function LastChecked({
  lastAttempt,
  storedAnything,
}: {
  lastAttempt: string | null;
  storedAnything: boolean;
}) {
  return (
    <p className="text-xs text-content-subtle">{sentence(lastAttempt, storedAnything)}</p>
  );
}

function sentence(lastAttempt: string | null, storedAnything: boolean) {
  if (lastAttempt === null) {
    // **Absence stated, never blank** — the same rule the line above follows.
    // The two cases differ, and a customer who has been told *"not checked
    // yet"* about a company Signora demonstrably holds evidence for would be
    // reading something false.
    return storedAnything
      ? 'Checked · we did not record when'
      : 'Not checked yet';
  }
  return storedAnything
    ? `Checked ${howLongAgo(lastAttempt)}`
    : // **The sentence the whole slice exists for.** Somebody looked and there
      // was nothing there, which is a fact about the account rather than about
      // Signora — and the previous screen could only render it as silence.
      `Checked ${howLongAgo(lastAttempt)} · nothing found`;
}
