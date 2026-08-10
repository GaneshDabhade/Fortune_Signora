/**
 * **`/w/:workspace/home`** — [TASK-1438](../../../../../../docs/BACKLOG.md),
 * the route the entry engine already returns.
 *
 * ## 🔴 Eight of the engine's twenty-four rules stop returning 404 here
 *
 * 📁 [`lib/entry/rules.ts`](../../../../../lib/entry/rules.ts):52 has named
 * this path since [TASK-1400](../../../../../../docs/BACKLOG.md) — *"the one
 * authenticated landing route"* — and **nothing served it.** ⚡
 * [500](../../../../../../docs/architecture/500-authenticated-entry-reconciliation.md)
 * §3 requested every destination the engine can return and **eighteen came
 * back 404**; this one route answers **rules 11 · 12 · 14 · 19 · 20 · 21 · 22
 * · 24**, ⛔ **including 24, the default and most common outcome.**
 *
 * ## ⛔ It does NOT adopt the entry engine
 *
 * 📁 **[D-205](../../../../../../docs/DECISION_REGISTER.md) stands and
 * [TASK-1401](../../../../../../docs/BACKLOG.md) stays `BLOCKED`.** ⚡ **This
 * row creates ONE destination the engine already names.** ⛔ Wiring
 * `resolveEntry` here would be this row taking that one's scope, and eleven
 * of the engine's other destinations still render nothing.
 *
 * ## ⚡ It renders what `/` renders, and that is the whole change
 *
 * 📁 The row is explicit: *"`/w/:workspace/home` renders what `/` renders
 * today… nothing else moves."* ⛔ **So this is not a new screen.** **Home's
 * COMPOSITION is [TASK-1405](../../../../../../docs/BACKLOG.md)'s resolver and
 * [TASK-1406](../../../../../../docs/BACKLOG.md)'s card registry**, both of
 * which are on `main` and waiting for a catalogue — **inventing a composition
 * here would be a third answer to what Home shows.**
 *
 * 🔴 **The workspace is read from the segment by the provider, not here** —
 * and it is validated against the API's membership list exactly as the stored
 * id always was. 📁 *"The stored id is a hint, never a grant."* ⚡ **A URL
 * segment is exactly as untrusted**, so a member of nothing typing another
 * workspace's id lands where a non-member lands.
 */
export { default } from '../../../page';
