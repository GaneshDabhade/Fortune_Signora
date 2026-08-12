'use client';

import { Building2 } from 'lucide-react';
import { useMemo, useState } from 'react';

import { EntityName } from '@/components/intelligence/entity-name';
import { StatedAbsence } from '@/components/feedback/stated-absence';
import { NoWorkspace } from '@/components/workspace/no-workspace';
import {
  Button,
  Card,
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
import { AccountsToolbar } from './toolbar';
import {
  DEFAULT_COLUMNS,
  NO_FILTERS,
  ROW_PADDING,
  type ColumnId,
  type Density,
  type Filters,
  applyFilters,
  choicesFor,
  toCsv,
  visibleColumns,
} from '@/lib/accounts/table';
import { cn } from '@/lib/design/cn';
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

  /**
   * 🔴 **Previous / Next over the cursor, and it REPLACED *Load more*** —
   * [TASK-1475](../../../../docs/BACKLOG.md), 📁
   * [C-1431](../../../../docs/LANE_COORDINATION.md).
   *
   * ⛔ **Not numbered pages and not a total**, however the mock draws them: 📁
   * the endpoint is keyset *deliberately* — *"an offset page would skip or
   * repeat rows… a customer paging the list would silently miss accounts"* —
   * **and a total is a count the contract does not return.**
   *
   * ⚡ **A page index over what `useInfiniteQuery` has already fetched.**
   * `Next` shows the next page and fetches it only if it is not held; `Previous`
   * never refetches. ⛔ **The old `Load more` accumulated pages into one list**,
   * which is a different product: it grows the page under somebody scanning it
   * and makes *"which page am I on"* unanswerable.
   */
  const [page, setPage] = useState(0);
  const [mode, setMode] = useState<'table' | 'cards'>('table');
  const [density, setDensity] = useState<Density>('comfortable');
  const [columns, setColumns] = useState<readonly ColumnId[]>(DEFAULT_COLUMNS);
  const [filters, setFilters] = useState<Filters>(NO_FILTERS);

  const pages = accounts.data?.pages ?? [];
  const current = pages[page]?.items ?? [];
  const loadedAll = useMemo(() => pages.flatMap((p) => p.items), [pages]);
  // ⚠️ **`new Date()` is read once per render rather than per row**, so every
  // row on one screen is aged against one moment.
  const shown = useMemo(() => applyFilters(current, filters, new Date()), [current, filters]);
  const shownColumns = useMemo(() => visibleColumns(columns), [columns]);

  if (workspaceId === null) return <NoWorkspace />;

  const hasNext = page + 1 < pages.length || accounts.hasNextPage === true;

  const goNext = () => {
    if (page + 1 < pages.length) {
      setPage(page + 1);
      return;
    }
    void accounts.fetchNextPage().then(() => setPage((was) => was + 1));
  };

  const exportCsv = () => {
    const csv = toCsv(shown, shownColumns);
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = 'companies.csv';
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <>
      <PageHeader
        title="Companies"
        description={
          <>
            Every account you can see, in one surface.{' '}
            {/* ⚡ **The absent columns are named to the reader.** ⛔ A screen
                that silently draws four of nine columns reads as a broken
                table; one that says what it does not have yet reads as an
                honest one. 📁 **Score, owner, value, renewal, segment and tags
                are [C-209](../../../../docs/LANE_COORDINATION.md) and
                [C-1425](../../../../docs/LANE_COORDINATION.md)**, not
                omissions. */}
            <span className="text-content-muted">
              Score, owner, value and renewal are not on this list yet — open an account to see
              what Signora holds.
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
      ) : loadedAll.length === 0 ? (
        <EmptyState
          icon={Building2}
          title="No companies yet"
          description="Companies appear here as Signora resolves them from your connected sources. Connect a source and the first ones arrive with it."
        />
      ) : (
        <>
          <AccountsToolbar
            mode={mode}
            onMode={setMode}
            density={density}
            onDensity={setDensity}
            columns={columns}
            onColumns={setColumns}
            filters={filters}
            onFilters={setFilters}
            kinds={choicesFor(current, 'kind')}
            sources={choicesFor(current, 'source')}
            shown={shown.length}
            loaded={current.length}
            onExport={exportCsv}
          />

          {/* ⛔ **A filter that matches nothing is not an empty book.** ⚡ **The
              two are different sentences and this screen has both**: the empty
              state above says no company exists; this says the narrowing
              excluded them all. */}
          {shown.length === 0 ? (
            <EmptyState
              icon={Building2}
              title="No companies match these filters"
              description="Nothing on this page matches. Clear a condition, or move to the next page — filters narrow what has been read, not the whole book."
            />
          ) : mode === 'cards' ? (
            <CardGrid rows={shown} density={density} />
          ) : (
            <Table>
              <THead>
                <TR>
                  {shownColumns.map((column) => (
                    <TH key={column.id} scope="col">
                      {column.label}
                    </TH>
                  ))}
                </TR>
              </THead>
              <TBody>
                {shown.map((row) => (
                  <TR key={row.account.account_id}>
                    {shownColumns.map((column) => (
                      <TD key={column.id} className={ROW_PADDING[density]}>
                        {column.id === 'company' ? (
                          /* ✅ **Reused, not rebuilt** — `EntityName` carries the
                             name, the agreement state and the *no source has
                             named it* fallback, and it is what the attention
                             list and search both render. */
                          <EntityName
                            identity={row.account}
                            fallbackId={row.account.account_id}
                            href={`/accounts/${row.account.account_id}`}
                          />
                        ) : (
                          column.read(row)
                        )}
                      </TD>
                    ))}
                  </TR>
                ))}
              </TBody>
            </Table>
          )}

          <nav
            aria-label="Pages"
            data-testid="accounts-pager"
            className="mt-4 flex items-center gap-3"
          >
            <Button
              variant="secondary"
              onClick={() => setPage((was) => Math.max(0, was - 1))}
              disabled={page === 0}
            >
              Previous
            </Button>
            <Button
              variant="secondary"
              onClick={goNext}
              disabled={!hasNext || accounts.isFetchingNextPage}
            >
              {accounts.isFetchingNextPage ? 'Loading…' : 'Next'}
            </Button>
            {/* ⛔ **A page number, never a page COUNT.** ⚡ **Keyset cannot know
                how many pages exist without reading them**, and printing a
                denominator would be the fabricated total
                [C-1431](../../../../docs/LANE_COORDINATION.md) refuses. */}
            <span className="text-2xs text-content-subtle">Page {page + 1}</span>
          </nav>
        </>
      )}
    </>
  );
}

/**
 * 📁 **Card view** — *"same data, same filters, same selection — for scanning
 * by account rather than by column."*
 *
 * ⚡ **The same rows and the same filter result**, which is what makes it a
 * view rather than a second screen. ⛔ **It draws only fields that exist**, for
 * the reason the table does.
 */
function CardGrid({
  rows,
  density,
}: {
  rows: readonly import('@/lib/api/types').ListedAccount[];
  density: Density;
}) {
  return (
    <ul
      data-testid="accounts-cards"
      className={cn(
        'grid gap-3 smalllaptop:grid-cols-2 laptop:grid-cols-3',
        density === 'compact' && 'gap-2',
      )}
    >
      {rows.map((row) => (
        <li key={row.account.account_id}>
          <Card className={cn('h-full', density === 'compact' ? 'p-3' : 'p-4')}>
            <EntityName
              identity={row.account}
              fallbackId={row.account.account_id}
              href={`/accounts/${row.account.account_id}`}
            />
            <dl className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-content-muted">
              <div className="flex gap-1">
                <dt>Kind</dt>
                <dd className="text-content">{row.kind}</dd>
              </div>
              <div className="flex gap-1">
                <dt>Sources</dt>
                <dd className="text-content">{row.account.source_count}</dd>
              </div>
            </dl>
          </Card>
        </li>
      ))}
    </ul>
  );
}
