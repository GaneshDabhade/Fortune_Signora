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
