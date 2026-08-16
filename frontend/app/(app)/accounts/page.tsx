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
import { NothingSaid, StageBadge } from '@/components/accounts/account-commercial';
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
import { Fragment, useMemo, useState } from 'react';

import { formatDay } from '@/components/intelligence/dates';
import { EntityName } from '@/components/intelligence/entity-name';
import { StatedAbsence } from '@/components/feedback/stated-absence';
import { NoWorkspace } from '@/components/workspace/no-workspace';
import {
  Breadcrumb,
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
import {
  apply as applyDeclaration,
  declare as declareCompanies,
  whyNotReadableHere,
  type CompaniesDeclaration,
} from '@/lib/accounts/view';
import { AccountsToolbar } from './toolbar';
import { ViewTabs, type ViewMode } from './view-tabs';
import {
  DEFAULT_COLUMNS,
  formatMoney,
  NO_FILTERS,
  ROW_PADDING,
  type ColumnId,
  type Density,
  type Filters,
  applyFilters,
  applySort,
  choicesFor,
  groupRows,
  type GroupKey,
  type Sort,
  toCsv,
  visibleColumns,
} from '@/lib/accounts/table';
import { cn } from '@/lib/design/cn';
import { useAccountsCount } from '@/lib/query/hooks/accounts-count';
import { useSavedViews, useSaveView } from '@/lib/query/hooks/saved-views';
import { PAGE_SIZE, useAccountsList } from '@/lib/query/hooks/accounts-list';
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
/** 📁 **The design's pager control** — *"height:28px; padding:0 10px;
 *  border-radius:7px; border:1px solid var(--line-soft)"*. ⚡ **`--line-soft`
 *  and not `--line`**, which is what the design draws here and is the
 *  distinction the product-wide border correction established: containers and
 *  dividers take the soft hairline. */
const PAGER =
  'inline-flex h-control-sm items-center rounded-md border border-border-soft px-2.5 ' +
  'text-xs font-medium text-content hover:bg-surface-sunken ' +
  'disabled:cursor-not-allowed disabled:text-content-subtle disabled:hover:bg-transparent ' +
  'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 ' +
  'focus-visible:outline-accent';

export default function CompaniesPage() {
  const { activeWorkspace } = useWorkspaceContext();
  const workspaceId = activeWorkspace?.id ?? null;
  const accounts = useAccountsList(workspaceId);
  /**
   * 📁 **The design's header states the size of the book beside the size of
   * the page** — *"8,412 total · 312 in view"*.
   *
   * ⛔ **The loaded count cannot answer the first.** `accounts-list` is
   * keyset-paginated, so counting what has arrived measures the fetch — **and
   * printing that beside the word *total* is wrong by more with every page.**
   */
  const total = useAccountsCount(workspaceId);
  /**
   * 📁 **The design's tab row** — the workspace's shared views.
   *
   * ⛔ **Selecting one does not yet narrow the table.** ⚡ **`declaration` is
   * the view's own query and this screen does not interpret it**; applying it
   * would mean re-implementing a query language on the client, and a tab that
   * silently filtered by a rule nobody could see would be worse than one that
   * only marks where you are. **The gap is the apply, not the read.**
   */
  const savedViews = useSavedViews(workspaceId);
  const [selectedView, setSelectedView] = useState<string | null>(null);
  /** ⚡ **Why the chosen view could not be opened**, or `null`. ⛔ **A sentence
   *  rather than a boolean**, because the screen has to say which view and why
   *  — 📁 the same rule `LockedField` applies: a lock with no reason is worse
   *  than an absent field. */
  const [viewRefusal, setViewRefusal] = useState<string | null>(null);
  const saveView = useSaveView(workspaceId);

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
  const [mode, setMode] = useState<ViewMode>('table');
  const [density, setDensity] = useState<Density>('comfortable');
  /** ⚡ **`null` is the endpoint's own order** — oldest first, which is stable
   *  because *"a list ordered by anything the graph recomputes would reshuffle
   *  underneath somebody reading it."* */
  const [sort, setSort] = useState<Sort | null>(null);
  const [group, setGroup] = useState<GroupKey | null>(null);
  /** 📁 **The design's collapsible groups** — *"groups collapse, and a collapsed
   *  group still shows its worst status."* ⚡ **Collapsed rather than expanded
   *  is the stored set**, so changing the grouping opens everything rather than
   *  hiding rows behind a label the customer has not seen before. */
  const [collapsed, setCollapsed] = useState<ReadonlySet<string>>(new Set());
  const [columns, setColumns] = useState<readonly ColumnId[]>(DEFAULT_COLUMNS);
  const [filters, setFilters] = useState<Filters>(NO_FILTERS);

  const pages = accounts.data?.pages ?? [];
  const current = pages[page]?.items ?? [];
  const loadedAll = useMemo(() => pages.flatMap((p) => p.items), [pages]);
  // ⚠️ **`new Date()` is read once per render rather than per row**, so every
  // row on one screen is aged against one moment.
  // ⚡ **Filter, then order.** ⛔ **Never the reverse** — sorting rows that are
  // about to be discarded is work for nothing, and the two are independent so
  // the cheaper one goes first.
  const shown = useMemo(
    () => applySort(applyFilters(current, filters, new Date()), sort),
    [current, filters, sort],
  );
  /** 📁 **The design's grouped table**, or `null` when nothing is grouped —
   *  ⛔ **`null` rather than one group of everything**, which would draw a
   *  header a customer never asked for. */
  const groups = useMemo(() => groupRows(shown, group), [shown, group]);
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
        /* 📁 **The design's breadcrumb** — *"Accounts / Companies"*. ⚡ Shell
           rule 6: *"mandatory below the first level"*, and this is the second.
           ⛔ **The trail mirrors the data hierarchy, not the click path** —
           `Breadcrumb`'s own rule, so a deep link from Slack reads the same as
           a click from the rail. */
        eyebrow={
          <Breadcrumb
            trail={[
              { label: 'Accounts', kind: 'link', href: '/accounts' },
              { label: 'Companies', kind: 'current' },
            ]}
          />
        }
        /* 🔴 **The design's header actions, and only the one that exists.**
           📁 It draws *Import · Export · New company*. ⚡ **Export has a
           contract and is rendered here, in the design's position** — it was
           sitting in the toolbar, which is not where the design puts it.
           ⛔ **Import and New company are NOT rendered as disabled buttons**:
           📁 [B-255](../../../../docs/BUGS.md) — *a control that silently does
           nothing is worse than one that is absent* — and neither has an
           endpoint behind it. **Their absence is stated in the description
           rather than drawn as dead chrome.** */
        secondaryActions={
          <Button variant="ghost" onClick={exportCsv}>
            Export
          </Button>
        }
        /* 📁 **The design's two counts, on the title's line.** ⚡ **The total
           comes from its own read**; ⛔ **it is omitted rather than guessed
           while that read is in flight or has failed** — a header that printed
           the loaded count as the total would be the quiet kind of wrong. */
        titleMeta={
          <span className="tabular-nums">
            {/* ⛔ **Guarded on the NUMBER, not the object.** ⚠️ A response
                that arrived without a total is still a defined object, and
                `data !== undefined` let it through — **the header crashed on
                `toLocaleString`, which the component suite caught.** ✅ The
                total is printed when there is one, and omitted when there is
                not. */}
            {typeof total.data?.total === 'number'
              ? `${total.data.total.toLocaleString()} total · `
              : ''}
            {shown.length.toLocaleString()} in view
          </span>
        }
        description={
          <>
            Every account you can see, in one surface.{' '}
            {/* 🔴 **This sentence read *"Score, owner, value and renewal are
                not on this list yet"* and three of the four have since landed**
                — owner and segment on ADR-0411, Open ACV and Renewal on
                **ADR-0409, ratified 2026-08-12.** ⛔ **A screen describing its
                own absences has to keep the list true**, or it is the
                confidently wrong statement [§2](../../../../CLAUDE.md) is
                written against.

                ⚡ **Signora score is the one that is genuinely nowhere**, and
                naming only it is what makes the sentence worth reading. */}
            <span className="text-content-muted">
              A Signora score is not on this list yet. Value, renewal and stage arrive from a
              connected system — until one is connected they read as not reported, never as
              zero.
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
          {/* 📁 **The design's saved-view row, with the switcher on its right.**
          ⛔ **The switcher was above the filters**, which is not a place the
          design has. */}
      <ViewTabs
        views={savedViews.data?.items ?? []}
        loading={savedViews.isLoading}
        selected={selectedView}
        /**
         * 🔴 **Opening a view APPLIES it, or says why it cannot.**
         *
         * ⛔ **Never partly applied.** 📁 `working-list.ts` names the outcome:
         * *"the customer gets a list that is neither what they saved nor what
         * they asked for, and nothing says so."* ⚡ **The store is
         * workspace-wide and holds four screens' declarations**, so a Reports
         * definition sitting in this tab row is the ordinary case rather than
         * an error — **and the refusal says which it is.**
         */
        onSelect={(id) => {
          setSelectedView(id);
          setViewRefusal(null);
          if (id === null) {
            setFilters(NO_FILTERS);
            setGroup(null);
            setSort(null);
            return;
          }
          const view = savedViews.data?.items.find((candidate) => candidate.id === id);
          if (view === undefined) return;
          const why = whyNotReadableHere(view.declaration);
          if (why !== null) {
            setViewRefusal(why);
            return;
          }
          const applied = applyDeclaration(view.declaration as unknown as CompaniesDeclaration);
          setFilters(applied.filters);
          setGroup(applied.group);
          setSort(applied.sort);
          setPage(0);
        }}
        refusal={viewRefusal}
        onSave={
          // ⛔ **Offered only when it can work.** ⚡ A save with no workspace is
          // a control that fails after the click, which is B-255 with a delay.
          workspaceId === null
            ? undefined
            : (name: string) =>
                saveView.mutate(
                  {
                    name,
                    declaration: declareCompanies(filters, group, sort) as unknown as Record<
                      string,
                      unknown
                    >,
                  },
                  { onSuccess: (view) => setSelectedView(view.id) },
                )
        }
        saving={saveView.isPending}
        mode={mode}
        onMode={setMode}
      />

      <AccountsToolbar
        density={density}
        onDensity={setDensity}
        columns={columns}
        onColumns={setColumns}
        filters={filters}
        onFilters={setFilters}
        sort={sort}
        onSort={setSort}
        group={group}
        onGroup={setGroup}
        kinds={choicesFor(current, 'kind')}
        sources={choicesFor(current, 'source')}
        total={typeof total.data?.total === 'number' ? total.data.total : null}
        shown={shown.length}
        loaded={current.length}
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
          ) : mode === 'board' ? (
            /* 📁 **Board** — *"same data, same filters, same selection"*, laid
               out as one lane per group. ⚡ **It IS the grouping**, rendered
               sideways, which is why it reuses `groupRows` rather than
               grouping a second time ([§2](../../../../CLAUDE.md)). */
            <BoardLanes
              groups={groups}
              density={density}
              onGroup={() => setGroup('renewal')}
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
                    <TH
                      key={column.id}
                      scope="col"
                      /* 📁 **The design right-aligns the figures** — Open ACV
                         and Renewal — **and the header follows the body.** ⛔ A
                         heading that aligned differently from its column reads
                         as a different column. */
                      className={column.numeric ? 'text-right' : undefined}
                    >
                      {column.label}
                    </TH>
                  ))}
                </TR>
              </THead>
              <TBody>
                {(groups ?? [{ label: '', rows: shown, openAcv: null }]).map((bucket) => (
                  <Fragment key={bucket.label}>
                    {/* 📁 **The design's group header row** — *"Renewal in Q3
                        FY26 · 18 companies · $7.42M"* — on `--bg`, spanning the
                        table, with a soft hairline beneath.

                        ⛔ **Two figures, not four.** The design also prints a
                        status badge and an average score; **a badge is a
                        classification nothing stores and the average needs the
                        score column that has no source.** ⚡ **A header carrying
                        two true figures is worth more than one carrying two
                        true and two invented.** */}
                    {groups === null ? null : (
                      <TR>
                        <TD
                          colSpan={shownColumns.length + 1}
                          className="bg-canvas py-2.5 text-sm"
                        >
                          <span className="flex flex-wrap items-center gap-2.5">
                            {/* 📁 **The design's chevron**, and it is the
                                control rather than a decoration beside one. */}
                            <button
                              type="button"
                              aria-expanded={!collapsed.has(bucket.label)}
                              onClick={() =>
                                setCollapsed((was) => {
                                  const next = new Set(was);
                                  if (!next.delete(bucket.label)) next.add(bucket.label);
                                  return next;
                                })
                              }
                              className="flex items-center gap-2.5 rounded text-left focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
                            >
                              <span aria-hidden="true" className="text-xs text-content-subtle">
                                {collapsed.has(bucket.label) ? '▸' : '▾'}
                              </span>
                              <span className="font-semibold text-content">{bucket.label}</span>
                            </button>
                            <span className="tabular-nums text-content-subtle">
                              {bucket.rows.length.toLocaleString()}
                              {bucket.rows.length === 1 ? ' company' : ' companies'}
                            </span>
                            {/* ⛔ **Omitted, never zero.** 📁 A `$0` subtotal
                                over a group nobody has reported a figure for
                                would be the header stating a fact no source
                                supplied — and `groupRows` also withholds it
                                when two currencies are present, because
                                ADR-0409 forbids converting one into the
                                other. */}
                            {bucket.openAcv === null ? null : (
                              <span className="tabular-nums text-content-subtle">
                                · {formatMoney(bucket.openAcv)}
                              </span>
                            )}
                          </span>
                        </TD>
                      </TR>
                    )}
                {(collapsed.has(bucket.label) ? [] : bucket.rows).map((row) => (
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
                      <TD
                        key={column.id}
                        className={cn(
                          ROW_PADDING[density],
                          // 📁 `font-variant-numeric:tabular-nums` — the design
                          // sets it on every figure so a column of numbers has
                          // one edge rather than a ragged one.
                          column.numeric && 'text-right tabular-nums',
                        )}
                      >
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
                        ) : column.id === 'acv' ? (
                          /* ⛔ **Never a bare number, and never a zero.** ⚡ The
                             currency travels with the figure or the fact does
                             not exist (ADR-0409 §3) — and an unstated ACV is a
                             dash, because `$0` is something a seller would act
                             on. */
                          row.commercial.open_acv === null ? (
                            <NothingSaid />
                          ) : (
                            formatMoney(row.commercial.open_acv)
                          )
                        ) : column.id === 'renewal' ? (
                          row.commercial.renewal_date === null ? (
                            <NothingSaid />
                          ) : (
                            formatDay(row.commercial.renewal_date)
                          )
                        ) : column.id === 'stage' ? (
                          /* ⚠️ **The customer's own word, always** — 📁
                             ADR-0409 §5: *"the tenant's stage label is
                             provenance and is never reasoned over."* ⚡ **A
                             stage Signora has not mapped still shows**, which
                             is the state the CRM Integrations design counts
                             rather than hides. */
                          row.commercial.stage === null ? (
                            <NothingSaid />
                          ) : (
                            <StageBadge stage={row.commercial.stage} />
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
                  </Fragment>
                ))}
              </TBody>
            </Table>
            </>
          )}

          <nav
            aria-label="Pages"
            data-testid="accounts-pager"
            className="mt-4 flex flex-wrap items-center gap-3 border-t border-border-soft pt-3"
          >
            {/* 📁 **The design's own sentence** — *"Rows 1–8 of 312"*, 12px,
                `--ink-3`, tabular numerals, on the row's left.

                ⛔ **The denominator is the WORKSPACE total, and only when the
                count has answered.** ⚡ **Never the loaded figure in its
                place**: it would read correctly on the first page and be wrong
                by more with every page after it.

                ⚠️ **The design also says *"virtualised beyond 100"***. **This
                table renders every row it has read** — a page is 50 — **so the
                clause is omitted rather than claimed.** */}
            <span className="text-2xs tabular-nums text-content-subtle">
              {shown.length === 0
                ? 'No rows'
                : `Rows ${(page * PAGE_SIZE + 1).toLocaleString()}–${(
                    page * PAGE_SIZE + shown.length
                  ).toLocaleString()}${
                    typeof total.data?.total === 'number'
                      ? ` of ${total.data.total.toLocaleString()}`
                      : ''
                  }`}
            </span>

            <span className="ml-auto flex items-center gap-1.5">
              <button
                type="button"
                onClick={() => setPage((was) => Math.max(0, was - 1))}
                disabled={page === 0}
                className={PAGER}
              >
                Previous
              </button>
              {/* 🔴 **The current page, and no numbers around it.**

                  📁 **The design draws *1 2 3*.** ⛔ **Keyset pagination cannot
                  offer them**: a cursor names where the NEXT page resumes, so
                  page 3 is unreachable without walking pages 1 and 2 — and the
                  endpoint refuses offsets for a stated reason: *"the graph is
                  written continuously, so an offset page would skip or repeat
                  rows between two requests and a customer paging the list would
                  silently miss accounts."*

                  ⚡ **So the current page renders in the design's brand pill and
                  the neighbours are absent rather than dead.** 📁
                  [B-255](../../../../docs/BUGS.md): a control that silently
                  does nothing is worse than one that is absent. */}
              <span
                aria-current="page"
                className="inline-flex h-control-sm min-w-[2rem] items-center justify-center rounded-md bg-accent px-2.5 text-xs font-semibold tabular-nums text-accent-contrast"
              >
                {page + 1}
              </span>
              <button
                type="button"
                onClick={goNext}
                disabled={!hasNext || accounts.isFetchingNextPage}
                className={PAGER}
              >
                {accounts.isFetchingNextPage ? 'Loading…' : 'Next'}
              </button>
            </span>
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
/**
 * 📁 **Board view** — the design's third mode.
 *
 * ⛔ **A board without a grouping is not a board.** ⚡ **So an ungrouped board
 * states what it needs and offers it**, rather than drawing one lane containing
 * everything — which would look like a board that had failed.
 *
 * ⚠️ **Lanes scroll horizontally and each lane scrolls vertically**, which is
 * what makes a board readable at 8,412 accounts. ⛔ **No drag between lanes**:
 * a lane is a renewal quarter or a CRM stage, **and both are facts a customer's
 * own system reports** — dragging one would be this screen writing a claim it
 * does not own ([ADR-0409](../../../../docs/architecture/adr/0409-commercial-account-facts.md):
 * absence is never inferred, and neither is presence).
 */
function BoardLanes({
  groups,
  density,
  onGroup,
}: {
  groups: readonly {
    label: string;
    rows: readonly import('@/lib/api/types').ListedAccount[];
    openAcv: import('@/lib/api/types').Money | null;
  }[] | null;
  density: Density;
  onGroup: () => void;
}) {
  if (groups === null) {
    return (
      <EmptyState
        icon={Building2}
        title="A board needs a grouping"
        description="Choose what the lanes should be — renewal quarter, stage, kind or source — and the same companies rearrange into columns."
        action={
          <Button variant="secondary" onClick={onGroup}>
            Group by renewal quarter
          </Button>
        }
      />
    );
  }
  return (
    <div data-testid="accounts-board" className="flex gap-3 overflow-x-auto pb-2">
      {groups.map((lane) => (
        <section
          key={lane.label}
          aria-label={lane.label}
          className="flex max-h-[34rem] w-72 flex-none flex-col rounded-lg border border-border-soft bg-canvas"
        >
          {/* 📁 **The lane head carries the group header's own two figures** —
              ⛔ **the same two**, because a board and a grouped table are one
              grouping shown twice and a third figure in one of them would make
              them disagree. */}
          <header className="flex flex-wrap items-baseline gap-2 border-b border-border-soft px-3 py-2.5">
            <span className="text-sm font-semibold text-content">{lane.label}</span>
            <span className="text-2xs tabular-nums text-content-subtle">
              {lane.rows.length.toLocaleString()}
            </span>
            {lane.openAcv === null ? null : (
              <span className="ml-auto text-2xs tabular-nums text-content-subtle">
                {formatMoney(lane.openAcv)}
              </span>
            )}
          </header>
          <div className="min-h-0 flex-1 overflow-y-auto p-2">
            <CardGrid rows={lane.rows} density={density} board />
          </div>
        </section>
      ))}
    </div>
  );
}

function CardGrid({
  rows,
  density,
  board = false,
}: {
  rows: readonly import('@/lib/api/types').ListedAccount[];
  density: Density;
  /** ⚡ **One column inside a lane**, where the grid is three across. ⛔ **The
   *  CARD is unchanged** — 📁 the design's board and card views draw the same
   *  card, and a board-specific variant would be the second definition
   *  [§20c](../../../../CLAUDE.md) forbids. */
  board?: boolean;
}) {
  return (
    <ul
      data-testid={board ? undefined : 'accounts-cards'}
      className={cn(
        'grid gap-3',
        board ? 'grid-cols-1' : 'smalllaptop:grid-cols-2 laptop:grid-cols-3',
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
