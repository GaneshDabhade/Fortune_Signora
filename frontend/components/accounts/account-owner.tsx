/**
 * **The Companies table's Owner column** — [TASK-1479](../../../docs/BACKLOG.md)
 * slice ⓶, against 📁 `Fortune Signora Companies.dc.html` and
 * [ADR-0411](../../../docs/architecture/adr/0411-customer-organized-account-metadata.md).
 *
 * ## 🔴 The server sends an id, and this is where it becomes a person
 *
 * 📁 **The ruling stores a reference so that a name is never duplicated** —
 * *"a person who leaves must not leave a dangling string."* ⚡ **So the id is
 * resolved here, against the member list the screen already holds**, and a
 * name never travels on the assignment response. ⛔ **A name on the wire would
 * be stale the day somebody changed theirs.**
 *
 * ## ⚠️ Three states, and only one of them is "nobody"
 *
 * 📁 [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md): **a failed read must
 * never render as an empty result**, and its loading cousin — **an unresolved
 * read must not render as an empty one.**
 *
 * | | |
 * |---|---|
 * | **Unread** | ⛔ **Nothing.** The answer has not arrived, and *Unassigned* would be a claim |
 * | **Assigned to somebody the member list does not know** | ⚡ **A stated absence, not a blank** — the reference outlived the membership, which is the one case ADR-0411's design makes visible rather than silent |
 * | **Genuinely unassigned** | *Unassigned*, which is a real answer |
 */
import type { Membership } from '@/lib/api/types';
import type { AccountAssignment } from '@/lib/query/hooks/account-assignments';

export interface AccountOwnerProps {
  /** ⛔ **`undefined` while the read is in flight**, and that is not the same
   * as no owner. */
  readonly assignment?: AccountAssignment;
  readonly members: readonly Membership[];
}

/**
 * Pick one account's owner out of the assignments the page fetched.
 *
 * ⚡ **Returns `undefined` for *not found in this answer*, which the component
 * renders as nothing** — the caller cannot accidentally turn an unread page
 * into forty *Unassigned* cells.
 */
export function ownerFor(
  accountId: string,
  assignments: readonly AccountAssignment[] | undefined,
): AccountAssignment | undefined {
  return assignments?.find(
    (assignment) => assignment.account_id === accountId && assignment.role === 'owner',
  );
}

export function AccountOwner({ assignment, members }: AccountOwnerProps) {
  if (assignment === undefined) {
    // ⛔ **Nothing, deliberately.** This is *"the answer has not arrived"* and
    // *"nobody owns this"* collapsed into one prop by the caller — and the
    // caller distinguishes them by passing `undefined` only while unread.
    return null;
  }

  const member = members.find((candidate) => candidate.user_id === assignment.member_user_id);
  if (member !== undefined) {
    // ⚡ **`member_email` when it is known, and D23's wording when it is not.**
    // 📁 The convention already exists in Team Management — *"Somebody here"*,
    // **rather than an identifier dressed as information** — and inventing a
    // second answer for the same absence would be the duplicated vocabulary
    // §4 forbids.
    //
    // ⛔ **The platform has no NAME to give**: Better Auth owns user identity
    // and runs in the Next.js tier, so the Python API has none
    // ([C-024](../../../docs/LANE_COORDINATION.md), ADR-0026). **An email is
    // what a person recognises here, and it is what Team Management shows.**
    return <span>{member.member_email ?? 'Somebody here'}</span>;
  }

  // ⚡ **The case the reference model makes visible.** Somebody holds this
    // account and is no longer in the member list — 📁 exactly what
  // [C-1510](../../../docs/LANE_COORDINATION.md) asks the product owner
  // about. ⛔ **Rendering their raw id would show a customer a UUID; showing
  // nothing would hide that the account is held at all.**
  return <span className="text-muted-foreground italic">No longer a member</span>;
}

/**
 * What an account with no owner shows.
 *
 * ⚠️ **A separate export rather than a branch inside `AccountOwner`**, because
 * the caller is the only thing that knows whether an absent assignment means
 * *unread* or *unassigned* — and folding both into one component is how the
 * loading state comes to render as a claim.
 */
export function UnassignedOwner() {
  return <span className="text-muted-foreground">Unassigned</span>;
}
