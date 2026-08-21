/**
 * How Signora writes a date. **One definition, because two would diverge.**
 *
 * Day precision throughout: evidence decays in bands measured in weeks, and a
 * timestamp to the minute implies a resolution the pipeline does not have.
 */

/** A day, in the reader's locale — `12 Aug 2026`. */
export function formatDay(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

/**
 * How long ago, in the units a person would say it in.
 *
 * **Rounded down and coarse on purpose.** *"Five weeks ago"* is what a seller
 * repeats in a meeting; *"36 days ago"* is a number they would have to convert
 * before it meant anything. Precision nobody uses is precision that only
 * creates doubt about the rest.
 */
export function howLongAgo(iso: string, now: Date = new Date()): string {
  const days = Math.floor((now.getTime() - new Date(iso).getTime()) / 86_400_000);

  if (days <= 0) return 'today';
  if (days === 1) return 'yesterday';
  if (days < 14) return `${days} days ago`;
  if (days < 60) return `${Math.floor(days / 7)} weeks ago`;
  if (days < 365) return `${Math.floor(days / 30)} months ago`;
  return `${Math.floor(days / 365)} years ago`;
}

/**
 * 🔴 **📁 §08's second term on a date fact** — the design draws *"12 Oct 2026
 * **69 days**"*, and the qualifier is the distance to the date.
 *
 * ⚡ **Arithmetic on a published field, not a new fact.** ⛔ **No producer is
 * invented**: `renewal_date` is already on `AccountCommercial`, and this is the
 * same shape {@link howLongAgo} already applies in the other direction.
 *
 * ⚠️ **Day precision and rounded toward the reader**, matching this module's
 * rule — *"precision nobody uses is precision that only creates doubt."*
 *
 * ⛔ **Says nothing about urgency.** 📁 The design colours *"69 days"* in
 * `warn`, which implies a threshold — **the product defines none**, so this
 * returns the count and the caller renders it neutral.
 */
export function daysUntil(iso: string, now: Date = new Date()): string | null {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return null;
  const days = Math.round((then - now.getTime()) / 86_400_000);
  // ⚡ **A date that has passed is not a countdown**, and calling it
  // "−3 days" would read as a measurement rather than a lapse.
  if (days < 0) return 'passed';
  if (days === 0) return 'today';
  if (days === 1) return 'tomorrow';
  return `${days} days`;
}
