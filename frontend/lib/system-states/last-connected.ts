'use client';

/**
 * **When Signora last reached its own service** —
 * [TASK-1436](../../../docs/BACKLOG.md), carved out of
 * [TASK-1409](../../../docs/BACKLOG.md) by
 * [D-215](../../../docs/DECISION_REGISTER.md).
 *
 * > 📁 **System States §04, *No internet · cold start***: ***"Last connected 3
 * > minutes ago · retrying in 8s"***
 *
 * ## 🔴 The write is the row, not the render
 *
 * ⚠️ **The row names its own failure mode before it happens**: *"a relative
 * time that says **last connected 0 minutes ago** forever because nothing
 * writes it."* ⛔ **So {@link recordConnection} exists first and
 * {@link lastConnected} second**, and the API client calls the former on every
 * successful response — **not a heartbeat, not a poll**: ⚡ **any successful
 * request already proves the connection, and a timer proving it again would be
 * traffic that exists to make a label true.**
 *
 * ## ⚡ Why `localStorage` and not memory
 *
 * 📁 **The screen this feeds is a COLD START** — *"there is no cached session
 * to fall back on"*. ⛔ **An in-memory value is gone exactly when the sentence
 * is needed**, which would leave the label to be invented or dropped. **It is
 * one number per browser and it is not workspace data**, so it carries no
 * tenant scope and nothing here is a tenancy concern.
 *
 * ⚠️ **A failed read is swallowed** — `localStorage` throws in private modes.
 * **The comparison is [`use-rail-collapse.ts`](../shell/use-rail-collapse.ts),
 * which swallows for the same reason, against
 * [`copyable-id.tsx`](../../components/ui/copyable-id.tsx), which REPORTS**:
 * ⛔ **nobody is relying on this having been written**, and a screen that fails
 * because it could not read a timestamp is worse than one that omits a phrase.
 */

const KEY = 'signora.last-connected';

/**
 * ⛔ **Called on a successful API response and nowhere else.**
 *
 * ⚡ **`Date.now()` rather than a server time.** The sentence is *"last
 * connected 3 minutes ago"* — **it measures how long THIS DEVICE has been
 * cut off**, and a server clock cannot answer that: the whole premise is that
 * the server is unreachable when it is read.
 */
export function recordConnection(at: number = Date.now()): void {
  try {
    window.localStorage.setItem(KEY, String(at));
  } catch {
    // See the note above: nobody relies on this having been written.
  }
}

/**
 * The last successful connection, or `null` if this browser has never had one.
 *
 * ⛔ **`null` is a real answer and callers must render it as one.** ⚡ **A
 * first-ever visit with no network has nothing to say**, and *"last connected
 * just now"* would be a fabrication on the one screen the design asks to be
 * *"honest about having nothing."*
 */
export function lastConnected(): number | null {
  try {
    const raw = window.localStorage.getItem(KEY);
    if (raw === null) return null;
    const at = Number(raw);
    // ⛔ A corrupted or hand-edited value is *no answer*, never `NaN` rendered
    // into a sentence.
    return Number.isFinite(at) && at > 0 ? at : null;
  } catch {
    return null;
  }
}

/**
 * 📁 ***"last connected 3 minutes ago"*** — **the design's own phrasing**, and
 * the units it uses.
 *
 * ⛔ **No `Intl.RelativeTimeFormat`.** ⚡ **It renders *"3 minutes ago"* but
 * also *"in 3 minutes"* and negotiates locale**, and this string is one half of
 * a sentence the design wrote — **the formatter would decide wording the design
 * already decided.** ✅ **A future translation is a translation of this
 * sentence, not of a library's.**
 */
export function describeLastConnected(at: number | null, now: number = Date.now()): string | null {
  if (at === null) return null;
  const seconds = Math.max(0, Math.round((now - at) / 1000));
  if (seconds < 60) return 'Last connected less than a minute ago';
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `Last connected ${minutes} ${minutes === 1 ? 'minute' : 'minutes'} ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `Last connected ${hours} ${hours === 1 ? 'hour' : 'hours'} ago`;
  const days = Math.round(hours / 24);
  return `Last connected ${days} ${days === 1 ? 'day' : 'days'} ago`;
}

/**
 * 📁 ***"a single retry that actually re-checks rather than reloading."***
 *
 * ## 🔴 Why the distinction is not pedantry, in the row's own words
 *
 * ⛔ ***"A reload on a cold start with no network returns the browser's own
 * error page"*** — ⚡ **the customer loses the product's designed state and
 * gets the browser's undesigned one, which is the one screen Signora cannot
 * style.** **So this probes and returns an answer; it never navigates.**
 *
 * ⚡ **It asks Signora's own service rather than `navigator.onLine`.** 📁 The
 * design distinguishes *"your network"* from *"our service"*, and
 * `navigator.onLine` answers neither reliably — **a captive portal reports
 * online.** ⛔ **`cache: 'no-store'` because a cached 200 would report a
 * connection that does not exist**, which is the failure this whole screen is
 * about.
 */
export async function probeConnection(signal?: AbortSignal): Promise<boolean> {
  try {
    const response = await fetch('/api/health', {
      method: 'GET',
      cache: 'no-store',
      ...(signal ? { signal } : {}),
    });
    if (response.ok) recordConnection();
    return response.ok;
  } catch {
    // A network failure is the answer, not an error to propagate: the caller
    // asked *is it back?* and *no* is a legitimate reply.
    return false;
  }
}
