'use client';

import { Badge, Card, CardBody, EmptyState, SkeletonText } from '@/components/ui';
import { StatedAbsence } from '@/components/feedback/stated-absence';
import { formatDay } from '@/components/intelligence/dates';
import type { BadgeTone } from '@/components/ui';
import type { IcpSegmentSummary, ProductCatalog } from '@/lib/api/types';

/**
 * Who this organization sells to.
 *
 * **The screen that did not exist.** An ideal customer used to be reachable
 * only through the product it belonged to, so *"show me everything we've said
 * about who buys from us"* had no page — and a company selling one thing to
 * two different kinds of buyer could not say so at all.
 *
 * ### It lists; it never rates
 *
 * Nothing here says whether a segment is good, broad, effective or better than
 * another. Answering that needs matching against real companies, which is
 * built elsewhere and does not exist yet — so the screen has no verdict to
 * show and no field that could carry one.
 *
 * ### Designed for fifty, not for one
 *
 * A one-item list that becomes a different screen at two items is a redesign
 * the customer performs on our behalf. So there is one layout: a list, with
 * the same row whether a workspace has one segment or forty.
 */

const STATE_LABEL: Record<IcpSegmentSummary['state'], string> = {
  draft: 'Not published yet',
  published: 'In use',
  archived: 'Archived',
};

// `In use` is deliberately the plainest of the three: it is the normal state,
// and a badge that shouts on every row stops meaning anything.
const STATE_TONE: Record<IcpSegmentSummary['state'], BadgeTone> = {
  draft: 'warning',
  published: 'success',
  archived: 'neutral',
};

/**
 * Product names for one segment, and an honest count of what is missing.
 *
 * **The catalog decides what can be shown.** A segment keeps naming a product
 * the customer has since removed — the reference is part of what they said —
 * and the row says so rather than silently listing fewer products than the
 * segment has. The same rule the ICP editor already follows (B-005).
 */
export function productNames(
  segment: IcpSegmentSummary,
  catalog: ProductCatalog | undefined,
): { named: string[]; missing: number } {
  if (!catalog) return { named: [], missing: 0 };
  const byId = new Map(catalog.products.map((product) => [product.id, product.name]));
  const named = segment.product_ids
    .map((id) => byId.get(id))
    .filter((name): name is string => name !== undefined);
  return { named, missing: segment.product_ids.length - named.length };
}

function ProductList({ named, missing }: { named: string[]; missing: number }) {
  if (named.length === 0 && missing === 0) {
    return <span className="text-sm text-content-muted">No products yet</span>;
  }
  return (
    <span className="text-sm text-content-muted">
      {named.join(' · ')}
      {missing > 0 ? (
        <span className="text-content-muted">
          {named.length > 0 ? ' · ' : ''}
          {missing === 1
            ? 'one product you no longer sell'
            : `${missing} products you no longer sell`}
        </span>
      ) : null}
    </span>
  );
}

export function SegmentList({
  segments,
  catalog,
  isLoading,
  isError,
}: {
  segments: IcpSegmentSummary[];
  catalog: ProductCatalog | undefined;
  isLoading: boolean;
  isError: boolean;
}) {
  if (isLoading) return <SkeletonText lines={3} />;

  if (isError) {
    return (
      <StatedAbsence
        announce="assertive"
        subject="who you sell to"
        reassurance="Nothing your organization has declared has been lost"
      />
    );
  }

  if (segments.length === 0) {
    // **A statement about the product working, never an apology for empty
    // data.** This is the common state for a new organization and it is
    // designed first rather than last.
    return (
      <EmptyState
        title="You haven't described who buys from you yet"
        description="Tell Signora the kinds of company that buy each of your products, and it will know what to look for."
      />
    );
  }

  return (
    <ul className="flex flex-col gap-3">
      {segments.map((segment) => {
        const products = productNames(segment, catalog);
        return (
          <li key={segment.id}>
            <Card>
              <CardBody>
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <h3 className="text-base font-medium text-content">{segment.name}</h3>
                  <Badge tone={STATE_TONE[segment.state]}>{STATE_LABEL[segment.state]}</Badge>
                </div>
                <div className="mt-1">
                  <ProductList named={products.named} missing={products.missing} />
                </div>
                <p className="mt-2 text-sm text-content-muted">
                  {/* Version is said in the customer's words. "v3" is our
                      bookkeeping; "changed 3 times" is what they asked. */}
                  Last changed {formatDay(segment.last_changed_at)}
                  {segment.version > 1 ? ` · revised ${segment.version - 1} times` : null}
                </p>
              </CardBody>
            </Card>
          </li>
        );
      })}
    </ul>
  );
}
