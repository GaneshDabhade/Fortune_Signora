'use client';

import { IcpEditor } from '@/components/commercial/icp';
import { ProductCatalogEditor } from '@/components/commercial/products';
import { NoWorkspace } from '@/components/workspace/no-workspace';
import { SkeletonText } from '@/components/ui';
import { useIcpDeclaration, useProductCatalog } from '@/lib/query/hooks/commercial';
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
      {isError ? (
        <p className="text-sm leading-6 text-content-muted">
          Your products could not be loaded. That is a fault in Signora, not a missing
          catalog — nothing you have declared has been lost.
        </p>
      ) : null}
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
    </div>
  );
}
