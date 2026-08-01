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
