'use client';

import { Building2 } from 'lucide-react';

import { EntityName } from '@/components/intelligence/entity-name';
import { StatedAbsence } from '@/components/feedback/stated-absence';
import { NoWorkspace } from '@/components/workspace/no-workspace';
import {
  Button,
  EmptyState,
  PageHeader,
  SkeletonText,
  TBody,
  TD,
  TH,
  THead,
  TR,
  Table,
} from '@/components/ui';
import { useAccountsList } from '@/lib/query/hooks/accounts-list';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';

/**
 * **Companies — every account this workspace knows** —
 * [TASK-440](../../../../docs/BACKLOG.md), against 📁
 * [`Fortune Signora Companies.dc.html`](../../../../docs/design-snapshot/screens/)
 * ([D-138](../../../../docs/DECISION_REGISTER.md)).
 *
 * ## 🔴 Attention answers *"who do I call today"*. This answers *"where is everything"*
 *
 * ⚡ **Two questions, two reads, two screens** — and 📁
 * [446](../../../../docs/architecture/446-companies-traceability-audit.md)
 * confused them: **it described this table as *"every company this workspace
 * watches"* and cited `GET /accounts`, which returns open opportunities.**
 * ⛔ **The correct read is `GET /workspaces/{id}/accounts-list`**, which
 * [TASK-472](../../../../docs/BACKLOG.md) built for exactly this screen.
 *
 * ## ⛔ The design draws nine columns and the contract publishes two
 *
 * 📁 **The design's table**: a selection box, an avatar, the name, and six more
 * columns of score, stage, owner and money. 🔴 **`ListedAccount` carries
 * `account` and `kind`. That is the whole contract.**
 *
 * ⚠️ **So seven columns are ABSENT rather than empty, and that is deliberate**
 * ([§20c](../../../../CLAUDE.md)): *"never introduce mock business data —
 * screens without a shipped module behind them ship a designed empty state."*
 * ⛔ **A column of `—` would be worse than no column**: it says Signora looked
 * and found nothing, when the truth is that nothing was ever asked.
 *
 * ⚡ **The gap is stated to the reader in the header rather than hidden**, and
 * raised as [C-289](../../../../docs/LANE_COORDINATION.md) so the columns
 * arrive as their reads do — the same treatment the rail gives a destination
 * with no route.
 *
 * ## 🔴 A failed read must never render as an empty list
 *
 * 📁 **[P-A](../../../../docs/DOMAIN_DISCOVERY_REGISTER.md) ·
 * [C-226](../../../../docs/LANE_COORDINATION.md)**, and this screen is where it
 * bites hardest: ⛔ **8,412 rows and zero look identical to a seller when the
 * difference is an outage.** ✅ **`error` is checked before `data`, always.**
 */
export default function CompaniesPage() {
  const { activeWorkspace } = useWorkspaceContext();
  const workspaceId = activeWorkspace?.id ?? null;
  const accounts = useAccountsList(workspaceId);

  if (workspaceId === null) return <NoWorkspace />;

  const rows = accounts.data?.pages.flatMap((page) => page.items) ?? [];
  // ⛔ **Counted from what arrived, never claimed.** 📁 The design prints
  // *"8,412 total · 312 in view"*, and **the total is not published by this
  // read** — ⚠️ **printing one would be inventing the number a seller trusts
  // most.** ✅ **So the header says how many have loaded**, which is true.
  const loaded = rows.length;

  return (
    <>
      <PageHeader
        title="Companies"
        description={
          <>
            Every account you can see, in one surface.{' '}
            {/* ⚡ **The absent columns are named to the reader.** ⛔ A screen
                that silently draws two of nine columns reads as a broken table;
                one that says what it does not have yet reads as an honest one.
                📁 The same choice `freshness.tsx` makes about *"last checked"*. */}
            <span className="text-content-muted">
              Score, owner, stage and value are not on this list yet — open an account to see them.
            </span>
          </>
        }
      />

      {/* 🔴 **`isError` FIRST.** 📁 [P-A](../../../../docs/DOMAIN_DISCOVERY_REGISTER.md):
          a failed read must never render as an empty result. ⚠️ **On this screen
          the two are indistinguishable to a seller**, and the wrong one costs
          them a morning of believing their book is gone. */}
      {accounts.isError ? (
        <StatedAbsence
          as="page"
          icon={Building2}
          subject="your companies"
          reassurance="Nothing has been lost — no account has been removed"
        />
      ) : accounts.isLoading ? (
        <SkeletonText lines={6} />
      ) : rows.length === 0 ? (
        <EmptyState
          icon={Building2}
          title="No companies yet"
          // ⛔ **Never *"coming soon"*, and never a blank.** ⚡ **It names the
          // one thing that puts a company here**, so somebody who wants rows
          // knows what produces them.
          description="Companies appear here as Signora resolves them from your connected sources. Connect a source and the first ones arrive with it."
        />
      ) : (
        <>
          <Table>
            <THead>
              <TR>
                <TH scope="col">Company</TH>
                {/* 📁 **`kind` is read, never assumed.** The endpoint: *"the
                    list answers for companies today and the graph knows more
                    kinds than it can search."* */}
                <TH scope="col">Kind</TH>
                <TH scope="col">Sources</TH>
              </TR>
            </THead>
            <TBody>
              {rows.map((row) => (
                <TR key={row.account.account_id}>
                  <TD>
                    {/* ✅ **Reused, not rebuilt** — `EntityName` already carries
                        the name, the agreement state and the *no source has
                        named it* fallback, and it is what the attention list
                        and search both render. ⛔ **A second name renderer
                        would be a second answer to *what is this called*.** */}
                    <EntityName
                      identity={row.account}
                      fallbackId={row.account.account_id}
                      href={`/accounts/${row.account.account_id}`}
                    />
                  </TD>
                  <TD>{row.kind}</TD>
                  {/* ⚡ **The denominator behind `agreement`**, which the
                      contract publishes and the design's table does not draw —
                      ✅ **shown because it is real**, where the six columns the
                      design does draw are not. */}
                  <TD>{row.account.source_count}</TD>
                </TR>
              ))}
            </TBody>
          </Table>

          <p className="mt-3 text-2xs text-content-subtle" data-testid="companies-count">
            {loaded} loaded
          </p>

          {/* ⛔ **A button, not an infinite scroll.** ⚡ **The cursor is opaque
              by contract and the page boundary is stable**; a scroll listener
              would fetch on a viewport event the customer did not ask for, and
              a seller scanning a book of 8,000 loses their place when the list
              grows underneath them. */}
          {accounts.hasNextPage ? (
            <Button
              variant="secondary"
              onClick={() => void accounts.fetchNextPage()}
              disabled={accounts.isFetchingNextPage}
              className="mt-4"
            >
              {accounts.isFetchingNextPage ? 'Loading…' : 'Load more'}
            </Button>
          ) : null}
        </>
      )}
    </>
  );
}
