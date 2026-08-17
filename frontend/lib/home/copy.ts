/**
 * **Home's copy table, verbatim** — 📁 `Fortune Signora Home.dc.html` §10.
 *
 * > 📁 **Contract item 18: *"Every string is used verbatim from the copy table.
 * > No message is assembled from fragments at runtime."***
 *
 * ## ⚡ Why a module rather than strings at the call site
 *
 * ⛔ **A sentence built from fragments cannot be checked against the design.**
 * Holding them here makes the design's own ids the identity of each string, so a
 * reviewer can diff this file against §10 and a test can assert that a state
 * renders *its* copy rather than *a* sentence.
 *
 * ## 🔴 The ones that take a value take it as a whole template, never a fragment
 *
 * ⚡ **Where the design's string contains a number or a name, this exports a
 * function.** ⛔ **That is not assembly**: the sentence is one template with the
 * design's own punctuation and word order, and the caller supplies only what the
 * design itself shows as data.
 *
 * ## ⛔ Banned on Home, and the design lists them
 *
 * 📁 *"Banned on Home: 'Welcome back!', 'No data available', 'Get started',
 * 'You're all caught up!', any exclamation mark, and any empty state that does
 * not name what was checked."* ✅ **`home-copy.test.ts` asserts every string here
 * is clear of that list**, which is what keeps a future edit honest.
 */

/** 📁 `HM-COPY-01` — state 01, first-time workspace. */
export const HM_COPY_01 = (workspace: string, steps: number, minutes: number): string =>
  `Let us get ${workspace} connected. ${wordFor(steps)} steps, about ${minutes} minutes.`;

/** 📁 `HM-COPY-02` — state 02, a sync in flight. */
export const HM_COPY_02 = (read: number, ofAbout: number): string =>
  `Reading your Salesforce — ${read.toLocaleString()} of about ${ofAbout.toLocaleString()} accounts so far.`;

/** 📁 `HM-COPY-03` — state 03, partially activated. */
export const HM_COPY_03 = (
  workspace: string,
  step: number,
  of: number,
  minutes: number,
): string => `${workspace} is nearly ready. Step ${step} of ${of} · about ${minutes} minutes left.`;

/** 📁 `HM-COPY-04` — state 04, activation just finished. Shown exactly once. */
export const HM_COPY_04 = 'Setup is complete. Home now shows your accounts, deals and signals.';

/**
 * 📁 `HM-COPY-05` — state 05, `no-business-data`.
 *
 * ⚠️ **The design's string names Salesforce because its example connects it.**
 * ⛔ **The source is a value here rather than a literal** — naming a system the
 * customer has not connected would be a false claim, and it is the one word in
 * this sentence that must come from what actually synced.
 */
export const HM_COPY_05 = (source: string, syncedAgo: string): string =>
  `${source} is connected and synced ${syncedAgo}, but it returned no open opportunities. Signora needs records to work from.`;

/**
 * 📁 `HM-COPY-06` — state 06b, `no-results`. **A success state.**
 *
 * ⛔ **It names what was checked and when**, which is the design's own test for
 * whether *"nothing to do"* is credible.
 */
export const HM_COPY_06 = (accounts: number, deals: number, at: string): string =>
  `Nothing needs you this morning. Signora checked ${accounts.toLocaleString()} accounts and ${deals.toLocaleString()} open deals at ${at}.`;

/** 📁 `HM-COPY-07` — state 08, the briefing failed. */
export const HM_COPY_07 = (currentAsOf: string): string =>
  `Your briefing could not be generated. Everything else on this page is current as of ${currentAsOf}.`;

/** 📁 `HM-COPY-08` — state 09, a forbidden card. */
export const HM_COPY_08 = (card: string, permission: string, approvers: string): string =>
  `${card} needs the ${permission} permission. Approvers: ${approvers}.`;

/** 📁 `HM-COPY-09` — state 10, a disconnected source. */
export const HM_COPY_09 = (source: string, on: string, since: string): string =>
  `${source} disconnected on ${on}. Figures below are from the last successful sync, ${since}.`;

/** 📁 `HM-COPY-10` — state 11, a lagging source. */
export const HM_COPY_10 = (source: string, behind: string, upTo: string): string =>
  `${source} is about ${behind} behind. Figures reflect data up to ${upTo}.`;

/** 📁 `HM-COPY-11` — state 12, the activation registry returned nothing. */
export const HM_COPY_11 = 'Setup steps could not be loaded.';

/** 📁 `HM-COPY-12` — state 14, returning with activation outstanding. */
export const HM_COPY_12 = 'Calls are still not connected. Signora is scoring on CRM fields alone.';

/**
 * ⚡ **The design writes step counts as words** — *"Two steps, about 15
 * minutes"* — **and as digits inside *"Step 2 of 2"***. ⛔ **Both are the
 * design's**, so this converts only where the design does.
 */
function wordFor(n: number): string {
  return ['Zero', 'One', 'Two', 'Three', 'Four', 'Five', 'Six'][n] ?? String(n);
}
