'use client';

import { BuyingCommitteeEditor } from '@/components/commercial/committee';
import { CommercialFocusEditor } from '@/components/commercial/focus';
import { CompetitorsEditor } from '@/components/commercial/competitors';
import { TargetAccountsEditor } from '@/components/commercial/target-accounts';
import { IcpEditor } from '@/components/commercial/icp';
import { SegmentList } from '@/components/commercial/segments';
import { ProductCatalogEditor } from '@/components/commercial/products';
import { NoWorkspace } from '@/components/workspace/no-workspace';
import { SkeletonText } from '@/components/ui';
import {
  useBuyingCommittee,
  useCommercialFocus,
  useIcpDeclaration,
  useIcpSegments,
  useProductCatalog,
  useCompetitors,
  useTargetAccounts,
} from '@/lib/query/hooks/commercial';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';
import { ReadingColumn } from '../../reading-column';

/**
 * What this organization sells.
 *
 * **The head of the pipeline, as a screen.** Signora has ten stages that
 * process companies and, until this page, nothing that recorded what the
 * customer sells to them. Every later declaration — who buys it, who decides,
 * which accounts to watch — refers to a product declared here.
 *
 * ### Why it lives under settings
 *
 * `/settings/*` is already guarded to owners (`GUARDED_ROUTES`), which is
 * exactly right: declaring what the company sells is an administrative act,
 * not something an individual seller changes. The server enforces it
 * independently — a member's write is refused with 403 — and the route guard
 * is the courtesy, never the enforcement.
 */
export default function ProductsPage() {
  const { activeWorkspace, isLoading: workspacesLoading } = useWorkspaceContext();
  const { data, isLoading, isError } = useProductCatalog(activeWorkspace?.id ?? null);
  const icp = useIcpDeclaration(activeWorkspace?.id ?? null);
  const segments = useIcpSegments(activeWorkspace?.id ?? null);
  const committee = useBuyingCommittee(activeWorkspace?.id ?? null);
  const focus = useCommercialFocus(activeWorkspace?.id ?? null);
  const targets = useTargetAccounts(activeWorkspace?.id ?? null);
  // The sixth declaration, and like the fifth it cites no product.
  const competitors = useCompetitors(activeWorkspace?.id ?? null);

  return (
    <ReadingColumn>
      <header>
        <h1 className="text-xl font-semibold text-content">Your business</h1>
        <p className="mt-1 text-sm text-content-muted">
          What Signora needs to know about your company before it can tell you anything
          useful about anyone else&apos;s.
        </p>
      </header>

      {!workspacesLoading && activeWorkspace === null ? <NoWorkspace /> : null}
      {isLoading ? <SkeletonText lines={4} /> : null}
      {isError ? <CouldNotLoad what="products" /> : null}
      {/* **B-006.** Each section reports its own failure. Rendering a section
          only when its data arrives, and explaining only the catalog's error,
          made an outage indistinguishable from a feature the customer does not
          have — the same shape of defect as D36, where every branch on a page
          tested a falsy value and nothing rendered at all. */}
      {icp.isError ? <CouldNotLoad what="ideal customer" /> : null}
      {committee.isError ? <CouldNotLoad what="buying committee" /> : null}
      {focus.isError ? <CouldNotLoad what="focus" /> : null}
      {targets.isError ? <CouldNotLoad what="accounts" /> : null}
      {data ? (
        <ProductCatalogEditor catalog={data} workspaceId={activeWorkspace?.id ?? null} />
      ) : null}
      {/* The ideal customer reads the catalog, so it renders once both have
          arrived. Two queries rather than one endpoint returning both: they
          are versioned separately, and a screen that fetched them together
          would be the first place they looked like one thing. */}
      {data && icp.data ? (
        <IcpEditor
          catalog={data}
          declaration={icp.data}
          workspaceId={activeWorkspace?.id ?? null}
        />
      ) : null}
      {/* **Who you sell to, as a list.** Reads the catalog for product names
          and renders whatever the segments query returned — including nothing,
          which is the common state for a new organization and is designed as a
          statement rather than an apology. It renders independently of the
          editor above: the two read different tables, and one failing must not
          take the other with it (B-006). */}
      <section className="flex flex-col gap-3">
        <div>
          <h2 className="text-base font-medium text-content">Who you sell to</h2>
          <p className="mt-1 text-sm text-content-muted">
            Every kind of company that buys from you. One product can be bought by
            several, and one of these can buy several products.
          </p>
        </div>
        <SegmentList
          segments={segments.data?.items ?? []}
          catalog={data}
          isLoading={segments.isLoading}
          isError={segments.isError}
        />
      </section>
      {data && committee.data ? (
        <BuyingCommitteeEditor
          catalog={data}
          declaration={committee.data}
          workspaceId={activeWorkspace?.id ?? null}
        />
      ) : null}
      {data && focus.data ? (
        <CommercialFocusEditor
          catalog={data}
          focus={focus.data}
          workspaceId={activeWorkspace?.id ?? null}
        />
      ) : null}
      {/* **The one declaration that cites no product**, so it needs no catalog
          and renders independently of it. A customer can name the companies
          they are chasing before they have written down what they sell. */}
      {targets.data ? (
        <TargetAccountsEditor
          accounts={targets.data}
          workspaceId={activeWorkspace?.id ?? null}
        />
      ) : null}
      {/* **Last, because it is the only one about a risk.** A customer
          describes their business before they describe what threatens it, and
          the order of the page is the order of that conversation. */}
      {competitors.data ? (
        <CompetitorsEditor
          declared={competitors.data}
          workspaceId={activeWorkspace?.id ?? null}
        />
      ) : null}
    </ReadingColumn>
  );
}

/**
 * A section that could not be loaded.
 *
 * **The wording is the point.** A customer who cannot see their ideal customer
 * needs to know that Signora failed rather than that they never declared one —
 * and that nothing they wrote has been lost. Page-local rather than shared:
 * one page has four of them, and no other page has any.
 */
function CouldNotLoad({ what }: { what: string }) {
  return (
    <p className="text-sm leading-6 text-content-muted">
      Your {what} could not be loaded. That is a fault in Signora, not a missing
      declaration — nothing you have declared has been lost.
    </p>
  );
}
