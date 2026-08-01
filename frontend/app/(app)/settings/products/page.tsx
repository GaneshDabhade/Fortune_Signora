'use client';

import { BuyingCommitteeEditor } from '@/components/commercial/committee';
import { CommercialFocusEditor } from '@/components/commercial/focus';
import { IcpEditor } from '@/components/commercial/icp';
import { ProductCatalogEditor } from '@/components/commercial/products';
import { NoWorkspace } from '@/components/workspace/no-workspace';
import { SkeletonText } from '@/components/ui';
import {
  useBuyingCommittee,
  useCommercialFocus,
  useIcpDeclaration,
  useProductCatalog,
} from '@/lib/query/hooks/commercial';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';

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
  const committee = useBuyingCommittee(activeWorkspace?.id ?? null);
  const focus = useCommercialFocus(activeWorkspace?.id ?? null);

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
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
    </div>
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
