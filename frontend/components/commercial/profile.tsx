'use client';

import Link from 'next/link';

import { PART_LABELS, size } from '@/components/commercial/vocabulary';
import { formatDay } from '@/components/intelligence/dates';
import { Badge, EmptyState } from '@/components/ui';
import type {
  BuyingCommittee,
  CommercialFocus,
  IcpDeclaration,
  Product,
  ProductCatalog,
  TargetAccountList,
} from '@/lib/api/types';

/**
 * What this company sells, who buys it, and who has to agree — **read, not
 * authored.**
 *
 * ### Why this exists
 *
 * **`policy.csv` grants a `member` read on all five declarations, and until now
 * not one of them reached a seller.** Five separate grants, each taken on the
 * reasoning that *every seller needs to see the catalog*, all of them landing
 * on a screen behind `workspace:update`. **[C-008](../../../docs/LANE_COORDINATION.md),
 * open since 2026-08-02, ruled 2026-08-03: option C now, option D next.**
 *
 * ### It reads; it never matches
 *
 * **Nothing here says whether an account fits.** Comparing a real company to a
 * description is *matching*, matching has no owner ([C-002](../../../docs/LANE_COORDINATION.md)),
 * and it is explicitly not Commercial Profile's — the module records and
 * computes nothing (ADR-0035). So this surface has no verdict, no score, no
 * rank, and no field that could carry one. **That is the boundary the ruling
 * drew between stage 1 and stage 2**, and it is what makes stage 1 buildable
 * today without settling a single ownership question.
 *
 * ### The shape is the customer's, not the API's
 *
 * The authoring screen renders five declarations as five editors in a column,
 * because each arrived in its own slice. **A reader does not have five
 * questions; they have one, asked about each product** — *what is this, who
 * buys it, and who has to sign?* Three of the five declarations cite a product,
 * so the product is the spine and the others hang off it:
 *
 * ```
 *   what we are pushing            ← focus, if there is one
 *   ├─ Product              name · description
 *   │    who buys it        industries · countries · size
 *   │    who has to agree   title · part
 *   └─ …
 *   companies we are chasing       ← target accounts, if there are any
 * ```
 *
 * **Focus leads because it is the only one that expires.** The others describe
 * what is permanently true of the business; focus says what is true this
 * quarter, and a seller reading this page to decide their next move needs the
 * perishable fact first.
 */

interface CommercialProfileProps {
  catalog: ProductCatalog;
  icp: IcpDeclaration;
  committee: BuyingCommittee;
  focus: CommercialFocus;
  targets: TargetAccountList;
  /** Where a reader who *can* change this is sent. **Null for a member**, who
   * would otherwise be offered a link into a screen the server refuses. */
  authoringHref: string | null;
}

export function CommercialProfile({
  catalog,
  icp,
  committee,
  focus,
  targets,
  authoringHref,
}: CommercialProfileProps) {
  // **Nothing declared at all is one state, not five.** A page that renders
  // nothing is indistinguishable from a broken one (D36), and five separate
  // *not declared yet* notes would be the same absence said five times.
  if (catalog.products.length === 0 && targets.accounts.length === 0) {
    return <NothingDeclared authoringHref={authoringHref} />;
  }

  return (
    <div className="flex flex-col gap-8">
      <FocusBlock focus={focus} catalog={catalog} />
      <ProductBlock catalog={catalog} icp={icp} committee={committee} />
      <TargetsBlock targets={targets} />
    </div>
  );
}

/**
 * Nobody has told Signora anything about this business yet.
 *
 * **The empty state teaches rather than reports** — and what it teaches depends
 * on whether the reader can do anything about it. An owner gets the way to fix
 * it; a member gets the reason the rest of the product is thin, and is told who
 * can change that. **Offering a member a link into `/settings` would be a
 * control that goes nowhere**, which costs more trust than an absent one
 * (principle 8).
 */
function NothingDeclared({ authoringHref }: { authoringHref: string | null }) {
  return (
    <EmptyState
      title="Nothing declared yet"
      description={
        authoringHref === null
          ? 'Signora matches what your company sells against what it finds. Nobody in your organization has written that down yet — an owner can, in Settings.'
          : 'Signora matches what your company sells against what it finds. Tell it what you sell and it has something to compare against.'
      }
      action={
        authoringHref === null ? undefined : (
          <Link
            href={authoringHref}
            className="text-sm font-medium text-accent hover:text-accent-hover"
          >
            Declare what you sell
          </Link>
        )
      }
    />
  );
}

/**
 * What the business is pushing right now.
 *
 * **Absent when there is none** (R1-06 · D6), and first when there is — it is
 * the one declaration on this page with a shelf life, and a seller deciding
 * what to do next needs the perishable fact before the permanent ones.
 */
function FocusBlock({ focus, catalog }: { focus: CommercialFocus; catalog: ProductCatalog }) {
  const named = focus.products
    .map((id) => catalog.products.find((product) => product.id === id)?.name)
    .filter((name): name is string => Boolean(name));

  if (focus.objective === '' && named.length === 0) return null;

  return (
    <section className="flex flex-col gap-2">
      <h2 className="text-sm font-semibold text-content">What we are pushing</h2>
      {focus.objective === '' ? null : (
        <p className="text-sm leading-6 text-content">{focus.objective}</p>
      )}
      {named.length === 0 ? null : (
        <p className="text-sm text-content-muted">{named.join(' · ')}</p>
      )}
      <Declared at={focus.updated_at} />
    </section>
  );
}

/**
 * The catalog, and everything that cites it.
 *
 * **One card per product rather than three lists keyed by `product_id`.** The
 * join is the reader's question — *who buys this one, and who signs for it* —
 * and doing it here rather than in three separate sections is the difference
 * between a page about a business and a page about an API.
 */
function ProductBlock({
  catalog,
  icp,
  committee,
}: {
  catalog: ProductCatalog;
  icp: IcpDeclaration;
  committee: BuyingCommittee;
}) {
  if (catalog.products.length === 0) return null;

  // **A fact true of every product is said once, not once per product.** If no
  // product has an ideal customer described, five identical *nobody has said*
  // lines is noise a reader learns to skip — and skipping is how they miss the
  // one that appears when a colleague describes the sixth.
  const anyIcp = icp.profiles.length > 0;
  const anyCommittee = committee.committees.length > 0;

  return (
    <section className="flex flex-col gap-3">
      <h2 className="text-sm font-semibold text-content">What we sell</h2>
      <ul className="divide-y divide-border rounded-md border border-border">
        {catalog.products.map((product) => (
          <ProductRow
            key={product.id}
            product={product}
            icp={icp.profiles.find((one) => one.product_id === product.id) ?? null}
            committee={committee.committees.find((one) => one.product_id === product.id) ?? null}
            sayMissingIcp={anyIcp}
            sayMissingCommittee={anyCommittee}
          />
        ))}
      </ul>
      {anyIcp ? null : (
        <p className="text-xs text-content-subtle">
          Nobody has described who buys these yet.
        </p>
      )}
      {anyCommittee ? null : (
        <p className="text-xs text-content-subtle">
          Nobody has described who has to agree yet.
        </p>
      )}
      <Declared at={catalog.updated_at} />
    </section>
  );
}

function ProductRow({
  product,
  icp,
  committee,
  sayMissingIcp,
  sayMissingCommittee,
}: {
  product: Product;
  icp: IcpDeclaration['profiles'][number] | null;
  committee: BuyingCommittee['committees'][number] | null;
  sayMissingIcp: boolean;
  sayMissingCommittee: boolean;
}) {
  const buyer = icp === null ? [] : [...icp.industries, ...icp.countries, size(icp.employees)].filter(
    (part) => part !== '',
  );

  return (
    <li className="flex flex-col gap-2 px-4 py-3">
      <div className="flex flex-col gap-0.5">
        <p className="text-sm font-medium text-content">{product.name}</p>
        {product.description === '' ? null : (
          <p className="text-sm leading-6 text-content-muted">{product.description}</p>
        )}
      </div>

      {buyer.length > 0 ? (
        <Line label="Who buys it">
          <span className="text-sm text-content-muted">{buyer.join(' · ')}</span>
        </Line>
      ) : sayMissingIcp ? (
        <Line label="Who buys it">
          <span className="text-sm text-content-subtle">Nobody has said yet</span>
        </Line>
      ) : null}

      {icp !== null && icp.notes !== '' ? (
        <p className="text-sm leading-6 text-content-muted">{icp.notes}</p>
      ) : null}

      {committee !== null && committee.roles.length > 0 ? (
        <Line label="Who has to agree">
          <ul className="flex flex-wrap items-center gap-x-3 gap-y-1">
            {committee.roles.map((role) => (
              <li key={`${role.part}-${role.title}`} className="flex items-center gap-1.5">
                <span className="text-sm text-content">{role.title}</span>
                <Badge tone="neutral">{PART_LABELS[role.part]}</Badge>
              </li>
            ))}
          </ul>
        </Line>
      ) : sayMissingCommittee ? (
        <Line label="Who has to agree">
          <span className="text-sm text-content-subtle">Nobody has said yet</span>
        </Line>
      ) : null}
    </li>
  );
}

/**
 * A labelled fact about a product.
 *
 * **The label is fixed-width and subtle so the eye runs down it**, which is
 * what makes three products scannable rather than read — the same property the
 * triage strip optimises for one level up.
 */
function Line({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-0.5 phone:flex-row phone:gap-3">
      <span className="shrink-0 text-xs text-content-subtle phone:w-32 phone:pt-0.5">{label}</span>
      <div className="min-w-0">{children}</div>
    </div>
  );
}

/**
 * The companies this business has said it is chasing.
 *
 * **Absent when there are none**, and deliberately unranked — the declaration
 * carries no order and inventing one here would be Signora grading a customer's
 * own list.
 */
function TargetsBlock({ targets }: { targets: TargetAccountList }) {
  if (targets.accounts.length === 0) return null;

  return (
    <section className="flex flex-col gap-2">
      <h2 className="text-sm font-semibold text-content">Companies we are chasing</h2>
      <p className="text-sm leading-6 text-content-muted">
        {targets.accounts.map((account) => account.name).join(' · ')}
      </p>
      <Declared at={targets.updated_at} />
    </section>
  );
}

/**
 * When somebody last said this.
 *
 * **Provenance is always visible** (principle 2) — and on a page a seller is
 * being asked to sell from, *how old is this* is the question that decides
 * whether they trust it. Absent at version 0, where there is nothing to date.
 */
function Declared({ at }: { at: string | null }) {
  if (at === null) return null;
  return <p className="text-xs text-content-subtle">Last declared {formatDay(at)}</p>;
}
