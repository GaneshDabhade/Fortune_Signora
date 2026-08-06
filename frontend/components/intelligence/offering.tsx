import { PART_LABELS } from '@/components/commercial/vocabulary';
import { StatedAbsence } from '@/components/feedback/stated-absence';
import { Badge, Card, CardBody, CardHeader, CardTitle } from '@/components/ui';
import type { BuyingCommittee, ProductCatalog } from '@/lib/api/types';

/**
 * What your company sells, and who has to agree — **read on an account,
 * declared once.**
 *
 * ### This is stage 2 of [C-008](../../../docs/LANE_COORDINATION.md), and the
 * ruling names exactly these two declarations
 *
 * *"In-context placement of the two declarations that need no matching: the
 * buying committee where contacts appear, and what we sell on the brief.
 * **Explicitly not** 'this account fits ICP X', which waits on
 * [C-002](../../../docs/LANE_COORDINATION.md)."*
 *
 * Stage 1 shipped `/business`, where a seller can read all five declarations —
 * but only by leaving the account they are working. This closes the two
 * questions [C-008](../../../docs/LANE_COORDINATION.md) recorded against the AE
 * and the SDR — *"which of our products is this account even a candidate
 * for?"* and *"who normally has to sign off on a deal like this?"* — **at the
 * moment they are actually asked**, which is the whole argument for option D
 * over option C.
 *
 * ### The ideal customer is deliberately absent, and that is the scope bound
 *
 * `/business` shows *who buys it* — industries, countries, company size —
 * beside each product. **This section does not**, and the omission is the one
 * decision in it that a later change must not quietly reverse.
 *
 * An ICP rendered on one company's page is a description sitting next to a
 * real company, and a reader will complete the comparison whether or not the
 * product does. **Signora would then be understood to have made a claim it did
 * not make and cannot support**: comparing a real company to a description is
 * *matching*, matching has no owner, and it is explicitly not Commercial
 * Profile's — the module records and computes nothing
 * ([ADR-0035](../../../docs/architecture/adr/0035-commercial-profile.md)).
 *
 * **The ruling drew the line in exactly this place**, which is why it lists two
 * declarations rather than three. A seller who wants the ideal customer opens
 * `/business` and does the comparison knowingly.
 *
 * ### Nothing here is graded, ranked, or account-specific
 *
 * No fit, no verdict, no ordering by relevance to this company. The list is
 * identical on every account in the workspace, the sentence under the heading
 * says so, and there is no field on either contract that could carry a
 * judgement if one were wanted.
 *
 * ### Why the committee is here rather than beside contacts
 *
 * [C-008](../../../docs/LANE_COORDINATION.md) says *"the buying committee where
 * contacts appear"* — **and no contacts appear anywhere in Signora.** No
 * person's name enters the platform from any source, which is
 * [ADR-0400](../../../docs/architecture/adr/0400-person-as-an-entity.md)'s own
 * first question, checked and answered *no*; the People domain is
 * [TASK-427](../../../docs/BACKLOG.md) and is `SEQUENCED`.
 *
 * **The declaration answers the seller's question without them.** *Who normally
 * has to sign off* is a statement about roles, and the committee is roles by
 * construction — *"a role, never a person"*. Naming which individual holds each
 * seat is the part that needs people, and it belongs to Epic C rather than
 * here.
 */
export function WhatYouSell({
  catalog,
  committee,
  isError = false,
}: {
  catalog: ProductCatalog | undefined;
  /** Joined per product, the same way `/business` joins it. **Absent is a
   * normal state** — a workspace may declare a catalog and never describe who
   * signs for it. */
  committee: BuyingCommittee | undefined;
  /** **Absence and failure are two different facts** and this section is not
   * allowed to render them identically ([C-226](../../../docs/LANE_COORDINATION.md)).
   * A workspace that has declared nothing shows nothing; a read that failed
   * says so. */
  isError?: boolean;
}) {
  if (isError) return <Unavailable />;

  /**
   * **Version 0 means nothing has been declared**, which the contract
   * documents as different from a customer who declared an empty catalog.
   * Either way there is nothing to show, and a section explaining its own
   * absence on every account of a workspace that has not filled this in would
   * be noise on the page a seller lives on. The declaration screen is where
   * that prompt belongs — the same rule this page already applies to
   * competitors.
   */
  if (catalog === undefined || catalog.products.length === 0) return null;

  const committees = committee?.committees ?? [];
  // **A fact true of every product is said once, not once per product.** Five
  // identical *nobody has said* lines is noise a reader learns to skip — and
  // skipping is how they miss the one that appears when a colleague describes
  // the sixth. Copied in intent from `/business`, which learned it first.
  const anyCommittee = committees.length > 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle>What you sell</CardTitle>
      </CardHeader>
      <CardBody>
        <p className="text-xs text-content-subtle">
          {/* The sentence that stops the list being read as an account fact —
              the same job the competitor section's first line does, and for the
              same reason. */}
          Your declared catalog, the same on every account. Signora has not said this
          account is a candidate for any of it.
        </p>
        <ul className="mt-3 divide-y divide-border rounded-md border border-border">
          {catalog.products.map((product) => (
            <li key={product.id} className="flex flex-col gap-2 px-4 py-3">
              <div className="flex flex-col gap-0.5">
                <p className="text-sm font-medium text-content">{product.name}</p>
                {product.description === '' ? null : (
                  <p className="text-sm leading-6 text-content-muted">
                    {product.description}
                  </p>
                )}
              </div>
              <Signatories
                roles={
                  committees.find((one) => one.product_id === product.id)?.roles ?? []
                }
                sayMissing={anyCommittee}
              />
            </li>
          ))}
        </ul>
      </CardBody>
    </Card>
  );
}

/**
 * Who has to agree, for one product.
 *
 * **The part label comes from `components/commercial/vocabulary`**, which is
 * where `/business` reads it too. A second mapping of `CommitteePart` to
 * English here would be a second vocabulary — wrong the moment a part is added
 * and invisible when it is (`CLAUDE.md` §2).
 */
function Signatories({ roles, sayMissing }: { roles: BuyingCommittee['committees'][number]['roles']; sayMissing: boolean }) {
  if (roles.length === 0) {
    return sayMissing ? (
      <p className="text-sm text-content-subtle">Nobody has said who has to agree yet</p>
    ) : null;
  }

  return (
    <div className="flex flex-col gap-0.5 sm:flex-row sm:gap-3">
      <span className="shrink-0 text-xs text-content-subtle sm:w-32 sm:pt-0.5">
        Who has to agree
      </span>
      <ul className="flex flex-wrap items-center gap-x-3 gap-y-1">
        {roles.map((role) => (
          <li key={`${role.part}-${role.title}`} className="flex items-center gap-1.5">
            <span className="text-sm text-content">{role.title}</span>
            <Badge tone="neutral">{PART_LABELS[role.part]}</Badge>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Unavailable() {
  return (
    <StatedAbsence
      as="card"
      subject="what your organization sells"
      reassurance="Nothing your organization has declared has been lost"
    />
  );
}
