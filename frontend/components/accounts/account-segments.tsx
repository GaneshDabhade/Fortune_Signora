/**
 * **The Companies table's Segment column** — [TASK-1479](../../../docs/BACKLOG.md)
 * slice ⓶b, against 📁 `Fortune Signora Companies.dc.html` and
 * [ADR-0411](../../../docs/architecture/adr/0411-customer-organized-account-metadata.md).
 *
 * ## ⚠️ The design draws segments twice, and the two do not share a vocabulary
 *
 * | | |
 * |---|---|
 * | **The `Segment` column** | one value per row, from a tier vocabulary — `Enterprise`, `Mid-market` |
 * | **The `Segments` panel** | five named groupings with counts — `Board reporting set`, `Competitive watch` |
 * |
 *
 * ⛔ **No row's cell holds a panel segment's name, and no panel entry is called
 * `Enterprise`.** 📁 **[D-235](../../../docs/DECISION_REGISTER.md) ② ruled that
 * this column carries the ADR-0411 meaning**, so **the panel's groupings are
 * what it renders** — and **[C-1511](../../../docs/LANE_COORDINATION.md) asks
 * the product owner what the tier values were.**
 *
 * ⚡ **Which is why the cell renders a LIST rather than one value.** A company
 * can be in *Board reporting set* and *Competitive watch* at once, and the
 * membership model is what the panel requires; **rendering only the first
 * would be this component choosing which of a customer's groupings matters.**
 *
 * ## 🔴 Three states, and only one of them is "none"
 *
 * 📁 [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md)'s loading cousin, the
 * same rule the Owner column follows: **an unresolved read must not render as
 * an empty one.**
 */
import { Badge } from '@/components/ui/badge';
import type {
  AccountSegment,
  AccountSegmentMembership,
} from '@/lib/query/hooks/account-segments';

export interface AccountSegmentsProps {
  /** ⛔ **`undefined` while the read is in flight**, and that is not the same
   *  as *in no grouping*. */
  readonly membership?: AccountSegmentMembership;
  readonly segments: readonly AccountSegment[];
}

/**
 * Pick one account's groupings out of the memberships the page fetched.
 *
 * ⚡ **Returns `undefined` for *not found in this answer*, which the component
 * renders as nothing** — the caller cannot accidentally turn an unread page
 * into forty *No segment* cells.
 */
export function membershipFor(
  accountId: string,
  memberships: readonly AccountSegmentMembership[] | undefined,
): AccountSegmentMembership | undefined {
  return memberships?.find((entry) => entry.account_id === accountId);
}

export function AccountSegments({ membership, segments }: AccountSegmentsProps) {
  if (membership === undefined) {
    // ⛔ **Nothing, deliberately.** The answer has not arrived, and the caller
    // is the only thing that knows whether an absent membership means *unread*
    // or *in no grouping*.
    return null;
  }

  // ⚡ **Resolved against the directory, and an id with no segment is dropped.**
  // 📁 The two reads are separate requests, so a grouping created between them
  // is a transient the customer should never see as a broken chip — the same
  // rule the Tags column records, and the next directory fetch resolves it.
  //
  // ✅ **Order is the directory's**, which is name order from the server, so
  // the same company renders its groupings the same way on every visit.
  const named = segments.filter((segment) =>
    membership.segment_ids.includes(segment.segment_id),
  );

  if (named.length === 0) {
    // ⚠️ **The read arrived and this company is in no grouping.** ⛔ Rendering
    // nothing here would be indistinguishable from the unread state above,
    // and the two are different facts.
    return <UnsegmentedAccount />;
  }

  return (
    <span className="flex flex-wrap gap-1">
      {named.map((segment) => (
        <Badge key={segment.segment_id} tone="neutral">
          {segment.name}
        </Badge>
      ))}
    </span>
  );
}

/**
 * What a company in no saved grouping shows.
 *
 * ⚠️ **A separate export rather than a branch the caller cannot reach**, on
 * the same terms as `UnassignedOwner`: the caller is the only thing that knows
 * whether an absent membership means *unread* or *none*, and folding both into
 * one component is how a loading state comes to render as a claim.
 */
export function UnsegmentedAccount() {
  return <span className="text-content-subtle">No segment</span>;
}
