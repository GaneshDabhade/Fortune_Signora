/**
 * **What a proposed tag batch says to the person who proposed it.**
 *
 * 🔴 **The copy lives here because it makes two claims and both are
 * load-bearing** — 📁 `commercial_profile/interface/router.py:676`: ***"201,
 * and it proposes rather than applies. Nothing is tagged by this request."***
 * under **ADR-0405**, *an action is approved before it is effective*.
 *
 * ⛔ **The call site used to clear the selection and say nothing at all**, so a
 * customer selected companies, chose a tag, watched the selection vanish and
 * saw no row change. 📁 [B-255](../../../docs/BUGS.md): *a control that
 * silently does nothing is worse than one that is absent.*
 */

/** ⚡ **The count comes from the server**, not from the selection — the two
 *  differ when the same account is selected twice, and the server de-duplicates
 *  (`len(dict.fromkeys(...))`). */
export function proposedMessage(itemCount: number): string {
  const noun = itemCount === 1 ? 'company' : 'companies';
  return `Proposed a tag for ${itemCount} ${noun}`;
}

/**
 * ⚠️ **Two sentences, and neither works alone.**
 *
 * ⛔ ***"Nothing is tagged yet"*** on its own reads as a failure. ⛔ ***"once it
 * is approved"*** on its own implies an approval that is coming — and 📁 the
 * screen ADR-0405 puts approval on **does not exist**: `action-batches` has
 * zero frontend consumers, and there is no route that lists batches to build
 * one from. 🔴 [C-1554](../../../docs/LANE_COORDINATION.md).
 *
 * ✅ **So it states the mechanism and the absence together**, which is the same
 * honesty the avatar block uses one screen over — *"uploading a photo and
 * choosing a colour are not available yet."*
 */
export const PROPOSED_DETAIL =
  'Nothing is tagged yet. A batch takes effect once it is approved, and approving is not built yet.';
