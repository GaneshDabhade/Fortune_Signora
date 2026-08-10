'use client';

import Link from 'next/link';

import { CommercialProfile } from '@/components/commercial/profile';
import { StatedAbsence } from '@/components/feedback/stated-absence';
import { NoWorkspace } from '@/components/workspace/no-workspace';
import { PageHeader, SkeletonText } from '@/components/ui';
import { useSession } from '@/lib/auth/client';
import {
  useBuyingCommittee,
  useCommercialFocus,
  useIcpDeclaration,
  useProductCatalog,
  useTargetAccounts,
} from '@/lib/query/hooks/commercial';
import { useViewerRole } from '@/lib/query/hooks/team';
import { can } from '@/lib/state/permissions';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';

/**
 * *"What does my company sell, and who buys it?"* — **the question a seller
 * could not ask.**
 *
 * ### Why this route exists rather than a change to Settings
 *
 * `policy.csv` grants a `member` read on `product`, `icp`, `buying_committee`,
 * `commercial_focus` and `target_account` — **five separate decisions, each
 * taken on the reasoning that every seller needs to see the catalog.** Every
 * one of them landed on `/settings/products`, and `GUARDED_ROUTES` restricts
 * `/settings/*` to `workspace:update`. **So the API said yes five times and the
 * product said no.** [C-008](../../../../docs/LANE_COORDINATION.md), open since
 * 2026-08-02, ruled 2026-08-03: **option C now, option D next.**
 *
 * **A top-level route is member-reachable by construction, and that is the
 * whole argument for C over A.** `guardFor` is a deny-list — a route absent
 * from `GUARDED_ROUTES` needs only a resolved workspace — so this screen
 * required **no change to `permissions.ts`**, which is frozen frontend
 * foundation (§20c). The alternative, exempting one child of `/settings`,
 * would have changed the guard's shape to widen an *authoring* route, and
 * D38 rules against sending a seller into Settings to do their job.
 *
 * ### Reading and authoring are two jobs, and they now have two addresses
 *
 * `/settings/products` still authors, still owner-only, unchanged. **This
 * reads.** An owner has both doors and that is correct rather than duplicated:
 * *change what we sell* and *remind me what we sell* are asked at different
 * moments, by the same person, in different frames of mind.
 *
 * ### What it deliberately does not do
 *
 * **It does not say whether an account fits.** That is matching, matching has
 * no owner ([C-002](../../../../docs/LANE_COORDINATION.md)), and it is stage 2
 * of the ruling. Nothing on this page compares a real company to a description,
 * and there is no field that could carry the verdict if it did.
 */
export default function BusinessPage() {
  const { activeWorkspace, isLoading: workspacesLoading } = useWorkspaceContext();
  const workspaceId = activeWorkspace?.id ?? null;
  const { data: session } = useSession();
  const { role } = useViewerRole(workspaceId, session?.user?.id ?? null);

  const catalog = useProductCatalog(workspaceId);
  const icp = useIcpDeclaration(workspaceId);
  const committee = useBuyingCommittee(workspaceId);
  const focus = useCommercialFocus(workspaceId);
  const targets = useTargetAccounts(workspaceId);

  const loading =
    catalog.isLoading || icp.isLoading || committee.isLoading || focus.isLoading || targets.isLoading;
  // **One failure is the whole page's failure here, unlike the authoring
  // screen.** There, five editors each report their own outage because a
  // customer may still declare the other four. There is nothing to do here but
  // read, and a page silently missing one of five declarations would be read as
  // *we have not described that* — B-006's defect, on a screen where the reader
  // has no way to discover otherwise.
  const failed =
    catalog.isError || icp.isError || committee.isError || focus.isError || targets.isError;

  // **One derivation, two readers** — the header's edit link and the empty
  // state's. Computing it twice is how they eventually disagree about who may
  // author (`CLAUDE.md` §2, *truth has exactly one authoritative representation*).
  const authoring = can(role, 'workspace:update') ? '/settings/products' : null;

  const ready =
    catalog.data !== undefined &&
    icp.data !== undefined &&
    committee.data !== undefined &&
    focus.data !== undefined &&
    targets.data !== undefined;

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      {/* ⚡ **The shared header** — [TASK-1446](../../../../docs/BACKLOG.md).
          ⛔ **This screen used to author its own**, which is the class
          [498](../../../../docs/architecture/498-common-platform-audit.md)
          named: twenty-six route directories, each inventing the same strip.
          📁 Shell rule 03 — *"one primary action per view, and it lives in the
          page header"* — **is now structural: `primaryAction` is one slot.** */}
      <PageHeader
        title="Your business"
        description="What Signora compares every account against."
        // **An owner reading this can change it from here.** Without the link
        // they would have to know that the authoring screen is under Settings
        // and is called Products — which is the product asking somebody to
        // remember its own filing system. Absent for a member, whose only
        // recourse is a colleague, and for whom this would 403.
        primaryAction={
          authoring === null ? undefined : (
            // ⚠️ **The control is unchanged and that is deliberate.** §08 draws
            // the primary action as a brand fill, and `Button` has no `asChild`
            // — ⛔ **adding one is `button.tsx`, outside this row's 🟠 budget**
            // (a NEW component in `components/ui`). ✅ **This row owns the SLOT;
            // the control's appearance is a migration row's.**
            <Link
              href={authoring}
              className="shrink-0 rounded text-sm font-medium text-accent underline decoration-border underline-offset-4 transition-colors hover:decoration-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            >
              Change this
            </Link>
          )
        }
      />

      {!workspacesLoading && activeWorkspace === null ? <NoWorkspace /> : null}
      {loading ? <SkeletonText lines={5} /> : null}
      {failed ? (
        <StatedAbsence
          as="page"
          subject="your business"
          reassurance="That is a fault in Signora, not a missing declaration — nothing your organization has declared has been lost"
        />
      ) : null}
      {!failed && ready ? (
        <CommercialProfile
          catalog={catalog.data}
          icp={icp.data}
          committee={committee.data}
          focus={focus.data}
          targets={targets.data}
          authoringHref={authoring}
        />
      ) : null}
    </div>
  );
}
