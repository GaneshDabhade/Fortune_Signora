'use client';

import type { ListedAccount } from '@/lib/api/types';
import {
  AccountOwner,
  UnassignedOwner,
  ownerFor,
} from '@/components/accounts/account-owner';
import {
  AccountSegments,
  UnsegmentedAccount,
  membershipFor,
} from '@/components/accounts/account-segments';
import { AccountTags, tagsFor } from '@/components/accounts/account-tags';
import { AddTagControl } from '@/components/accounts/add-tag-control';
import { BulkBar } from '@/components/accounts/bulk-bar';
import type { Selection } from '@/lib/accounts/selection';
import {
  NOTHING_SELECTED,
  headerState,
  isSelected,
  offersSelectAll,
  resolvedIds,
  selectAllMatching,
  selectOnScreen,
  selectedCount,
  toggle,
} from '@/lib/accounts/selection';
import {
  useAccountTagAssignments,
  useAccountTags,
  useCreateTag,
  useProposeTagBatch,
} from '@/lib/query/hooks/account-tags';
import { useAccountAssignments } from '@/lib/query/hooks/account-assignments';
import {
  useAccountSegmentMemberships,
  useAccountSegments,
} from '@/lib/query/hooks/account-segments';
import { useWorkspaceMembers } from '@/lib/query/hooks/team';
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

  // ⚡ **Only the rows on screen**, and only when the Tags column is on. 📁 A
  // page of forty is one question; the next page is a different one, and the
  // query key says so. ⛔ **Asking for tags nobody is looking at is a request
  // whose answer is thrown away.**
  const taggable = useMemo(
    () => (columns.includes('tags') ? shown.map((r) => r.account.account_id) : []),
    [columns, shown],
  );
  /**
   * 🔴 **NOT conditional on the Tags column, and the journey is what found
   * that** — [TASK-466](../../../docs/BACKLOG.md).
   *
   * ⛔ **It was `columns.includes('tags') ? workspaceId : null`, and the
   * consequence was that *Add tag* never rendered**: the control is hidden
   * while the vocabulary is unread, `DEFAULT_COLUMNS` does not include `tags`,
   * so a customer who had not turned the column on could not label anything.
   *
   * ⚡ **A bulk action's availability must not depend on which columns somebody
   * chose to look at.** ⚠️ **The ASSIGNMENTS read stays conditional** — that
   * one genuinely is the column's data, and asking for tags nobody is looking
   * at is a request whose answer is thrown away.
   */
  const vocabulary = useAccountTags(workspaceId);
  /** ⛔ **Asked only when the column is on**, exactly as the tag reads are —
   * a request for owners nobody is looking at is work the customer pays for
   * and cannot see. */
  const ownerIds = useMemo(
    () => (columns.includes('owner') ? shown.map((r) => r.account.account_id) : []),
    [columns, shown],
  );
  const owners = useAccountAssignments(workspaceId, ownerIds);
  /** ⚡ **The member list the screen already holds**, which is what turns a
   * `member_user_id` into somebody a person recognises. */
  const members = useWorkspaceMembers(columns.includes('owner') ? workspaceId : null);
  /** ⛔ **Asked only when the column is on**, on the same terms as the owner
   *  and tag reads. */
  const segmentIds = useMemo(
    () => (columns.includes('segment') ? shown.map((r) => r.account.account_id) : []),
    [columns, shown],
  );
  const segmentMemberships = useAccountSegmentMemberships(workspaceId, segmentIds);
  /** ⚡ **The directory the screen already holds**, which is what turns a
   *  `segment_id` into a name a person recognises — the same shape the tag
   *  vocabulary serves for chips. */
  const segments = useAccountSegments(columns.includes('segment') ? workspaceId : null);
  const assignments = useAccountTagAssignments(workspaceId, taggable);

  const [selection, setSelection] = useState<Selection>(NOTHING_SELECTED);
  const createTag = useCreateTag(workspaceId);
  const proposeBatch = useProposeTagBatch(workspaceId);
  const onScreen = useMemo(() => shown.map((r) => r.account.account_id), [shown]);
  /**
   * 🔴 **The design's *"Select all 312"* is NOT offered, and the reason is that
   * 312 has no source** — [TASK-466](../../../docs/BACKLOG.md).
   *
   * 📁 `CursorPage` publishes `items`, `next_cursor` and `has_more` and **no
   * total** — measured, and deliberate: 📁 the accounts read's own words are
   * that *"the graph is written continuously"*, which is why it is keyset
   * rather than offset. ⛔ **A count over a set that changes between two
   * requests is a number that is wrong by the time it renders.**
   *
   * ⚠️ **Using the loaded count instead would be the same word in two
   * meanings**: the customer reads *"Select all 312"* and gets the 50 in hand.
   * 📁 [`table.ts`](../../../lib/accounts/table.ts) already names that class —
   * *"an export named 'all companies' that contained 50 would be the worst
   * kind of wrong: silently plausible."*
   *
   * ✅ **So the control is absent rather than approximate**, and the header
   * checkbox still selects everything on screen. **Recorded here and raised as
   * [C-1505](../../../docs/LANE_COORDINATION.md)** rather than left as a
   * missing button somebody re-derives.
   */
  const totalMatching = onScreen.length;

  if (workspaceId === null) return <NoWorkspace />;

  const hasNext = page + 1 < pages.length || accounts.hasNextPage === true;

  const goNext = () => {
    if (page + 1 < pages.length) {
      setPage(page + 1);
      return;
    }
    void accounts.fetchNextPage().then(() => setPage((was) => was + 1));
  };

  const download = (rows: readonly ListedAccount[], name: string) => {
    const csv = toCsv(rows, shownColumns);
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = name;
    link.click();
    URL.revokeObjectURL(url);
  };

  const exportCsv = () => download(shown, 'companies.csv');

  /**
   * ⛔ **`undefined` when the selection cannot be enumerated**, which is what
   * removes the control rather than letting it lie.
   *
   * 📁 *"Select all 312"* on a table holding 50 names a set the SERVER
   * resolves. ⚡ **Exporting the 50 would produce a file the customer believes
   * holds 312** — [`table.ts`](../../lib/accounts/table.ts)'s own words:
   * *"the worst kind of wrong — silently plausible."* ⚠️ **Resolving it needs
   * a server-side export, which no endpoint offers**, so the honest answer is
   * no button.
   */
  const exportSelection = (() => {
    const ids = resolvedIds(selection);
    if (ids === null) return undefined;
    const wanted = new Set(ids);
    return () =>
      download(
        loadedAll.filter((row) => wanted.has(row.account.account_id)),
        'selected-companies.csv',
      );
  })();

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
            <>
            <BulkBar
              count={selectedCount(selection)}
              onSelectAll={
                offersSelectAll(selection, onScreen, totalMatching)
                  ? () => setSelection(selectAllMatching(totalMatching))
                  : undefined
              }
              selectAllCount={
                offersSelectAll(selection, onScreen, totalMatching) ? totalMatching : undefined
              }
              onClear={() => setSelection(NOTHING_SELECTED)}
              onExport={exportSelection}
              addTag={
                <AddTagControl
                  count={selectedCount(selection)}
                  tags={vocabulary.data?.tags ?? []}
                  /* ⛔ **`undefined` while the selection cannot be enumerated
                     OR the vocabulary is unread.** The first is the same
                     refusal Export makes; the second keeps an unread list from
                     rendering as *"no tags"*. */
                  onPropose={
                    resolvedIds(selection) === null || vocabulary.data === undefined
                      ? undefined
                      : (tagId) => {
                          proposeBatch.mutate(
                            { tagId, accounts: resolvedIds(selection) ?? [] },
                            { onSuccess: () => setSelection(NOTHING_SELECTED) },
                          );
                        }
                  }
                  onCreate={(name) => createTag.mutate({ name, tone: 'neutral' })}
                  pending={proposeBatch.isPending || createTag.isPending}
                />
              }
            />
            <Table>
              <THead>
                <TR>
                  <TH scope="col" className="w-8">
                    <input
                      type="checkbox"
                      aria-label="Select the companies on this page"
                      checked={headerState(selection, onScreen) === 'all'}
                      /* ⚡ **Mixed is a real third state.** A box that showed
                         ticked while half the rows were unselected would make
                         *Select all* look like a no-op. */
                      ref={(box) => {
                        if (box !== null) {
                          box.indeterminate = headerState(selection, onScreen) === 'some';
                        }
                      }}
                      onChange={() =>
                        setSelection(
                          headerState(selection, onScreen) === 'all'
                            ? NOTHING_SELECTED
                            : selectOnScreen(onScreen),
                        )
                      }
                    />
                  </TH>
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
                    <TD className={ROW_PADDING[density]}>
                      <input
                        type="checkbox"
                        aria-label={`Select ${row.account.name ?? row.account.account_id}`}
                        checked={isSelected(selection, row.account.account_id)}
                        onChange={() =>
                          setSelection(toggle(selection, row.account.account_id, onScreen))
                        }
                      />
                    </TD>
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
                        ) : column.id === 'owner' ? (
                          /* ⛔ **Joined, never read from the row**, on the same
                             terms as tags: an assignment is
                             `commercial_profile`'s and an account is
                             `knowledge_graph`'s (§5). ⚡ **And the id becomes a
                             person only here** — ADR-0411 stores a reference
                             precisely so a name is never duplicated. */
                          ownerFor(row.account.account_id, owners.data?.assignments) ===
                          undefined ? (
                            /* ⚠️ **Only once the read has ARRIVED.** While it
                               is in flight the cell renders nothing —
                               forty rows saying *Unassigned* during a load is
                               forty false statements (P-A). */
                            owners.isSuccess ? (
                              <UnassignedOwner />
                            ) : null
                          ) : (
                            <AccountOwner
                              assignment={ownerFor(
                                row.account.account_id,
                                owners.data?.assignments,
                              )}
                              members={members.data?.items ?? []}
                            />
                          )
                        ) : column.id === 'segment' ? (
                          /* ⛔ **Joined, never read from the row**, on the same
                             terms as owner and tags (§5). ⚡ **A LIST rather
                             than one value**: the design's panel counts overlap
                             by construction, and rendering only the first would
                             be this screen choosing which of a customer's
                             groupings matters. */
                          membershipFor(
                            row.account.account_id,
                            segmentMemberships.data?.memberships,
                          ) === undefined ? (
                            /* ⚠️ **Only once the read has ARRIVED.** Forty rows
                               saying *No segment* during a load is forty false
                               statements (P-A). */
                            segmentMemberships.isSuccess ? (
                              <UnsegmentedAccount />
                            ) : null
                          ) : (
                            <AccountSegments
                              membership={membershipFor(
                                row.account.account_id,
                                segmentMemberships.data?.memberships,
                              )}
                              segments={segments.data?.segments ?? []}
                            />
                          )
                        ) : column.id === 'tags' ? (
                          /* ⛔ **Joined, never read from the row.** A tag is
                             `commercial_profile`'s and an account is
                             `knowledge_graph`'s — the screen reads both and
                             joins them rather than buying a cross-module
                             dependency for a column (§5). */
                          <AccountTags
                            tags={tagsFor(
                              row.account.account_id,
                              assignments.data?.assignments,
                              vocabulary.data?.tags,
                            )}
                          />
                        ) : (
                          column.read?.(row)
                        )}
                      </TD>
                    ))}
                  </TR>
                ))}
              </TBody>
            </Table>
            </>
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
