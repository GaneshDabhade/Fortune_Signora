/**
 * **The shell's transient surfaces, and the numbers the design states for
 * them** — [TASK-1462](../../../docs/BACKLOG.md), against
 * `docs/design-snapshot/screens/Fortune Signora App Shell.dc.html`
 * ([D-138](../../../docs/DECISION_REGISTER.md)).
 *
 * ## 🔴 Why the numbers live here and not in the markup
 *
 * ⚡ **The same reason [`SEARCH_WIDTH`](top-bar.ts) exists**: a Tailwind
 * arbitrary value puts the design's number in the one place nothing can check
 * it. ⛔ **`max-w-xl` is not 640px — it is 576px** — and that is not a
 * hypothetical: **it is what the palette shipped as**, and it read as correct
 * to every reviewer because the class name says *extra large* rather than
 * saying a number.
 *
 * ## ⚠️ §12 and §14 are two surfaces, and the row that sent this lane here
 * conflated them
 *
 * 📁 **§12 — the assistant**: *"opens as a **non-modal 420px** drawer that
 * **pushes content**"*.
 * 📁 **§14 — the context drawer**: *"**Modal**, right-hand, **480 / 640 /
 * 800px**, for a task with a definite end… a header with the object name, a
 * scrolling body, and a **pinned footer**"*.
 *
 * 🔴 **They differ in MODALITY, which is a behavioural contract and not a
 * width.** ⛔ **So the three context-drawer sizes are NOT published here**:
 * [`Drawer`](../../components/ui/drawer.tsx) is §12's assistant panel — its
 * own header says so, and says why it is not `Dialog` with different padding —
 * **and giving it 480/640/800 would size one surface with another's numbers.**
 *
 * ⚡ **The context drawer does not exist.** ⛔ **Building it here would be a
 * surface with no caller**, which this lane has now found five times and
 * refused to create twice in one day
 * ([C-1427](../../../docs/LANE_COORDINATION.md)).
 */

/**
 * 📁 **§09 — *"640px, anchored at 14vh, modal elevation, available from every
 * surface including inside dialogs."***
 *
 * ⚠️ **`anchorPercent`, not `anchorVh`.** ⚡ **`vh` is the unit the design
 * wrote it in and a percentage is what a test can measure** — 📁 the row
 * demands *"palette top offset = 14% of viewport height"*, **asserted from
 * geometry rather than from a class name.**
 */
export const PALETTE = { width: 640, anchorPercent: 14 } as const;

/**
 * 📁 **§12 — *"a non-modal 420px drawer that pushes content."***
 *
 * ⚠️ **This number existed only in a doc comment.** 🔴 **`copilot.tsx` quoted
 * *"420px"* in its own header and mounted a `Drawer` that is `w-full`**, so
 * the assistant panel opened at whatever width its parent happened to be.
 * ⛔ **[TASK-1462](../../../docs/BACKLOG.md) lists the copilot's 420 among the
 * values it *"must NOT touch — verified"*, and the verification was of the
 * comment rather than of the panel.**
 */
export const ASSISTANT_DRAWER_WIDTH = 420;
