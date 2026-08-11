/**
 * **`/w/:workspace/home`** — the entry engine's landing route, and from
 * [TASK-1405](../../../../../../docs/BACKLOG.md) it renders **Home's
 * composition** rather than standing in for it.
 *
 * ## 🔴 What changed, and why the previous line was right when it was written
 *
 * 📁 **[TASK-1438](../../../../../../docs/BACKLOG.md) made this
 * `export { default } from '../../../page'`** so eight of the engine's
 * twenty-four rules — ⛔ **including 24, the default and most common outcome** —
 * stopped returning 404. ✅ **That was correct**, and its own comment named what
 * would replace it: *"Home's COMPOSITION is TASK-1405's resolver and TASK-1406's
 * card registry, both of which are on `main` and waiting for a catalogue."*
 *
 * ⚡ **They are no longer waiting.** 📁 [`home.tsx`](./home.tsx) is the caller
 * both were written for, and `resolveComposition` had **zero** callers until it.
 *
 * ## ⛔ It still does not adopt the entry engine
 *
 * 📁 **[D-205](../../../../../../docs/DECISION_REGISTER.md) stands and
 * [TASK-1401](../../../../../../docs/BACKLOG.md) stays `BLOCKED`.** ⚡ **This
 * route renders a destination; it does not decide who arrives at it.**
 *
 * 🔴 **The workspace is still read from the segment by the provider and
 * validated against the API's membership list** — 📁 *"the stored id is a hint,
 * never a grant"*, and **a URL segment is exactly as untrusted.**
 */
import { Home } from './home';

export default function HomePage() {
  return <Home />;
}
