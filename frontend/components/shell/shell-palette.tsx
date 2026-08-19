'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';

import { CommandPalette, type CommandItem } from '@/components/ui';
import { useCopilot } from '@/components/shell/copilot';
import { useAccountSearch } from '@/lib/query/hooks/search';
import { useAccountIdentities } from '@/lib/query/hooks';
import { useRecentlyViewed } from '@/lib/query/hooks/recently-viewed';
import { RAIL_DESTINATIONS } from '@/components/shell/navigation';
import { can, guardFor, type Capability, type WorkspaceRole } from '@/lib/state/permissions';
import { useWorkspaceLabel } from '@/lib/shell/workspace-label';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';

/**
 * **The palette, mounted** — [TASK-1442](../../../docs/BACKLOG.md), resolving
 * 📁 [C-259](../../../docs/LANE_COORDINATION.md).
 *
 * ## 🔴 The palette was complete, tested, and mounted by nothing
 *
 * ⛔ **`⌘K` belonged to `account-search.tsx`:72**, which bound it on the
 * document and focused its own input. ⚡ **So the shortcut worked and opened
 * the wrong thing**: 📁 the App Shell binds it to the palette — *"Search —
 * opens the palette on click or ⌘K"* — and 📁 shell rule 07 says *"anything
 * clickable is reachable in the palette."*
 *
 * ⚠️ **Account search is ONE GROUP inside it, not the thing that owns the
 * shortcut.**
 *
 * ## 🔴 The sentence that stood here was a MISQUOTE, and it is why nothing failed
 *
 * ⛔ **It read: *"The design's groups are `Ask Signora` · `Recents` · `Actions` ·
 * `Navigate`"*** — ⚠️ **four, presented as a quotation.** 📁 **The design names
 * SEVEN and fixes their order:**
 *
 * > 📁 ***"Group order is fixed — Ask Signora, Recents, Records, Reports,
 * > Actions, Navigate, Settings — with five per group and a keyboard-reachable
 * > 'show all'."***
 *
 * 🔴 **So the palette was not incomplete by omission; it was complete against a
 * misquote** — 📁 [TASK-1484](../../../docs/BACKLOG.md), and *"a comment that
 * misstates the design is the defect that produced the code."*
 *
 * ## ⚡ Why the shell owns this and not the search box
 *
 * 📁 [C-259](../../../docs/LANE_COORDINATION.md)'s finding was that **neither
 * candidate row could mount it alone**: the palette must reach destinations
 * the search box knows nothing about. ✅ **The shell knows both** — it holds
 * the rail's destinations and it sits above every module.
 *
 * ⛔ **And it is guarded.** 📁 `navigation.tsx` already refuses to render a
 * destination the caller cannot reach; **a palette that offered the same
 * destination would be a second answer to *what can this person reach*** —
 * exactly what the rail's own comment warns about. ✅ **So the same
 * `guardFor`/`can` pair filters both.**
 */

/**
 * 📁 **The design's seven, in the design's order** — ***"Group order is
 * fixed"***.
 *
 * ⛔ **Exported so the test asserts the DESIGN's list rather than the code's**,
 * by name and position. ⚡ **A group with nothing in it is not rendered** — the
 * order is a statement about where a group sits when it has contents, never a
 * promise that seven headings appear.
 */
export const PALETTE_GROUPS = [
  'Ask Signora',
  'Recents',
  'Records',
  'Reports',
  'Actions',
  'Navigate',
  'Settings',
] as const;

/** 📁 ***"…with five per group and a keyboard-reachable 'show all'."*** */
export const PER_GROUP = 5;

/**
 * 📁 **The settings surface's own entries, in its own words.**
 *
 * ⛔ **Not invented here and not re-worded**: every label is the string
 * `app/(app)/settings/page.tsx` renders for that link, so the palette and the
 * page cannot drift into two names for one destination
 * ([§2](../../../CLAUDE.md)).
 *
 * ⚠️ **`/settings` is `workspace:update`-guarded and the guard matches by
 * prefix**, so a member is offered none of these — the same `guardFor`/`can`
 * pair the rail and the `Navigate` group already use.
 */
const SETTINGS_DESTINATIONS = [
  { href: '/settings/products', label: 'Change what you sell' },
  { href: '/settings/organization', label: 'Organization setup' },
  { href: '/settings/team', label: 'Your team' },
  { href: '/settings/connections', label: 'Connections' },
  { href: '/settings/audit', label: 'Audit log' },
] as const;

/**
 * ⚡ **Two of the design's seven groups have nothing to put in them TODAY, and
 * this is the measurement rather than a decision.**
 *
 * | Group | Measured |
 * |---|---|
 * | **`Reports`** | ⛔ `app/(app)/reports/` holds two files, **neither of which
 *   issues a query** — `grep -rn "useQuery\|apiRequest"` returns nothing — and
 *   the screen renders *"No reports yet"*. **There is no report to list.**
 *   ⚡ This is the same measurement 📁 [TASK-1416](../../../docs/BACKLOG.md) has
 *   been skipped on five times |
 * | **`Actions`** | ⛔ The design's examples are *"Export current view"* and
 *   *"Run renewal risk sweep"*. **Export exists only inside the Companies bulk
 *   bar and the audit page — it is SELECTION-scoped**, and the palette is
 *   global and knows no selection. **A global action would be a new one** |
 *
 * ⛔ **So neither is rendered**, and 📁 [TASK-1484](../../../docs/BACKLOG.md)'s
 * own bound is why: *"do not add a search backend to satisfy a heading."* ⚡ **An
 * empty heading is the false-affordance class this shell has refused three
 * times** — the bell before it had something to show, the assistant's absent
 * input, the *"Notification settings"* link to an unbuilt screen.
 */
export const GROUPS_WITH_NO_SOURCE_TODAY = ['Reports', 'Actions'] as const;

/** 📁 **`Records`' contents, said in the customer's word for each kind** —
 *  ⛔ the server's `result_type` is the platform's vocabulary and stops here. */
const KIND: Record<string, string> = { company: 'Company', technology: 'Technology', person: 'Person' };

export function ShellPalette({
  role,
  roleKnown = true,
}: {
  role: WorkspaceRole | null;
  /**
   * 🔴 **Whether the role has ARRIVED**, which `role: null` cannot say —
   * 📁 [B-253](../../../docs/BUGS.md), and 🔴 [B-291](../../../docs/BUGS.md) is
   * what its absence cost HERE.
   *
   * ⚠️ **The rail has taken this since 2026-08-13 and the palette did not**, so
   * for the first seconds of every session **the rail offered `Settings` and
   * the palette refused it** — ⛔ **the palette being a second answer to *what
   * can this person reach***, which is exactly what this file's own comment
   * says it must never be.
   *
   * ⚡ **Defaulted to `true`** so the prop is additive: a caller that does not
   * know behaves as every caller did before.
   */
  roleKnown?: boolean;
}) {
  const router = useRouter();
  const { activeWorkspace } = useWorkspaceContext();
  // 📁 **§19 — the workspace name, and only when the reader has more than
  // one** ([TASK-1463](../../../docs/BACKLOG.md)). ⚡ **The palette already
  // scopes the SEARCH to `activeWorkspace`; this is what makes that scope
  // visible** — 📁 *"ambiguity here is what causes the wrong customer to be
  // discussed."*
  const workspaceLabel = useWorkspaceLabel();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  /** ⚡ **Which group the reader asked to see in full**, and only ever one. 📁
   *  *"a keyboard-reachable 'show all'"* — ⛔ it is a row, not a control, so it
   *  needs no second interaction model. */
  const [expanded, setExpanded] = useState<string | null>(null);
  const copilot = useCopilot();

  /** 📁 Session Continuity tier 4, the same read `card.recents` uses. */
  const recentRecords = useRecentlyViewed(activeWorkspace?.id ?? null);
  const names = useAccountIdentities(
    activeWorkspace?.id ?? null,
    (recentRecords.data ?? []).map((record) => record.entity_id),
  );

  // 📁 *"Search — opens the palette on click or ⌘K."* ⚡ **Bound on the
  // document**, because the whole value is reaching it from wherever you are —
  // the same reasoning `account-search.tsx` used for the shortcut it held.
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key.toLowerCase() !== 'k' || !(event.metaKey || event.ctrlKey)) return;
      event.preventDefault();
      setOpen(true);
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, []);

  const {
    data: groups,
    isFetching: searching,
    isError: searchFailed,
  } = useAccountSearch(activeWorkspace?.id ?? null, query);

  const items = useMemo<CommandItem[]>(() => {
    /**
     * 🔴 **An unresolved role offers the destination, never withholds it** —
     * 📁 `navigation.tsx`'s own rule, ratified by
     * [B-253](../../../docs/BUGS.md) and decided by the design rather than by a
     * lane: 📁 App Shell §16 *Cold boot*.
     *
     * ⚡ **Being briefly generous costs a refusal the server was always going
     * to give**; being briefly restrictive is *"a false claim about
     * entitlement"* on the surface a person reaches for first. ⛔ And
     * [§20c](../../../CLAUDE.md) already says this check is *"presentational…
     * never enforcement"*.
     */
    const reachable = (href: string) => {
      if (!roleKnown) return true;
      const guard = guardFor(href);
      return guard === undefined || can(role, guard.requires as Capability);
    };

    /**
     * 📁 **`Ask Signora`, and it is the affordance that EXISTS rather than the
     * one the design draws.**
     *
     * ⛔ **The design's item is *"Answer: why is EMEA enterprise slipping"***.
     * ⚠️ **The assistant cannot answer** — 📁
     * [TASK-482](../../../docs/BACKLOG.md) shipped it with **no input box** on
     * purpose (*"a field that swallows a question somebody actually typed is
     * worse than none"*), because [C-334](../../../docs/LANE_COORDINATION.md)
     * means there is no host credential. ⛔ **So an *Answer:* row would promise
     * a reply nothing can produce.**
     *
     * ✅ **What is offered is the door the rail already offers** — 📁 shell rule
     * 07: *"anything clickable is reachable in the palette."*
     */
    const ask: CommandItem[] =
      copilot === null
        ? []
        : [{ id: 'ask:signora', label: 'Ask Signora', group: 'Ask Signora', glyph: '✦', meta: '⌘⇧A' }];

    /**
     * 📁 **`Recents` — *"Vantage Logistics · Account"*.**
     *
     * ⚡ **The same read `card.recents` uses**, so the palette and Home agree on
     * what *recent* means without either defining it — 📁 Session Continuity
     * tier 4 owns that. ⛔ **An account whose name has not resolved is dropped
     * rather than listed as *"Unnamed account"***: 🔴
     * [B-290](../../../docs/BUGS.md) is that mistake one surface over, and a
     * palette row a reader cannot recognise is one they cannot choose.
     */
    const recents: CommandItem[] = (recentRecords.data ?? []).flatMap((record) => {
      const name = names.data?.get(record.entity_id)?.name ?? null;
      return name === null
        ? []
        : [{ id: `account:${record.entity_id}`, label: name, group: 'Recents', meta: 'Account' }];
    });

    /**
     * 📁 **`Records` — and it is a RENAME rather than a new read.**
     *
     * ⚠️ **[TASK-1484](../../../docs/BACKLOG.md) states this outcome up front**:
     * *"`Records` may end up as a rename of the existing account-search groups
     * rather than a new read. That is the correct outcome if so — do not add a
     * search backend to satisfy a heading."* ⛔ **The two kinds became the
     * row's `meta`**, so nothing is lost by folding them.
     *
     * 🔴 **`coverage` is read before `results`, always.** 📁 The product owner
     * ruled it on 2026-08-05: *"the absence of results and the absence of the
     * group represent different business meanings."* ⛔ **A group Signora did
     * not search is skipped entirely** rather than contributing an empty
     * stretch of list.
     */
    const records: CommandItem[] = (groups ?? [])
      .filter((group) => group.coverage === 'searched')
      .flatMap((group) =>
        group.results.map((result) => ({
          id: `account:${result.account.account_id}`,
          // ⛔ **`matched_name`, not the account's current name.** It is what
          // the person typed against, and showing a different string would
          // make a correct match look like a wrong one.
          label: result.matched_name,
          group: 'Records',
          // ⚡ **The kind, and *renamed* when that is the fact worth saying** —
          // a changed name is the one thing that makes a right match look wrong.
          meta: result.is_renamed
            ? `${KIND[group.result_type]} · renamed`
            : KIND[group.result_type],
        })),
      );

    // 📁 **`Navigate` — the destinations the shell owns.** ⛔ **Filtered by the
    // same guard the rail applies**, so the palette is not a second answer to
    // *what can this person reach*.
    const navigate: CommandItem[] = RAIL_DESTINATIONS.filter((item) =>
      reachable(item.href),
    ).map((item) => ({
      id: `nav:${item.href}`,
      label: item.label,
      group: 'Navigate',
      meta: item.href,
    }));

    /** 📁 **`Settings` — the settings page's own five, guarded the same way.** */
    const settings: CommandItem[] = SETTINGS_DESTINATIONS.filter((item) =>
      reachable(item.href),
    ).map((item) => ({
      id: `nav:${item.href}`,
      label: item.label,
      group: 'Settings',
      meta: item.href,
    }));

    const byGroup: Record<string, CommandItem[]> = {
      'Ask Signora': ask,
      Recents: recents,
      Records: records,
      Navigate: navigate,
      Settings: settings,
    };

    /**
     * 🔴 **The design's order, applied here rather than emerging from the
     * order the code happens to build things in.**
     *
     * 📁 `components/ui/command-palette.tsx` *"groups by first appearance"* and
     * **never sorts** — *"the caller's order is the caller's ranking"* — so the
     * fixed order is this caller's to state, and it is stated once.
     *
     * ⛔ **Five per group**, with 📁 *"a keyboard-reachable 'show all'"* — ⚡ an
     * ordinary row in the list, so ↑↓ and ↵ reach it with no second interaction
     * model.
     */
    return PALETTE_GROUPS.flatMap((group) => {
      const all = byGroup[group] ?? [];
      if (all.length === 0) return [];
      if (expanded === group || all.length <= PER_GROUP) return all;
      return [
        ...all.slice(0, PER_GROUP),
        {
          id: `expand:${group}`,
          label: `Show all ${all.length}`,
          group,
          meta: `${all.length - PER_GROUP} more`,
        },
      ];
    });
  }, [copilot, expanded, groups, names.data, recentRecords.data, role, roleKnown]);

  const close = () => {
    setOpen(false);
    setQuery('');
    // ⛔ **A group left expanded would still be expanded next time**, which is
    // a state the reader did not ask to keep across two different questions.
    setExpanded(null);
  };

  return (
    <CommandPalette
      open={open}
      onClose={close}
      items={items}
      query={query}
      onQueryChange={setQuery}
      {...(workspaceLabel === undefined ? {} : { scope: workspaceLabel })}
      /**
       * 🔴 **[TASK-481](../../../docs/BACKLOG.md) — the real status, so an
       * empty list means what it says.**
       *
       * ⛔ **Before this, a failed search rendered *"Nothing matches"***, which
       * is a statement about the customer's data rather than about the request
       * — 📁 [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md).
       *
       * ⚠️ **`isFetching` rather than `isLoading`.** ⚡ **`isLoading` is only
       * true for the FIRST fetch of a key**, so typing a second character
       * against a cached-then-refetching query would report *ready* while a
       * request was in flight — **and the palette would say *nothing matches*
       * about a search that had not finished.**
       *
       * ⛔ **Nav items are local and always present**, so the status describes
       * the ACCOUNT search only; the palette shows a state screen solely when
       * the whole list is empty, which is exactly when the distinction matters.
       */
      status={searchFailed ? 'error' : searching ? 'loading' : query === '' ? 'idle' : 'ready'}
      onSelect={(item) => {
        // 📁 *"a keyboard-reachable 'show all'"* — ⛔ **it expands the group and
        // the palette stays open.** ⚡ Closing here would make the one row whose
        // whole purpose is *show me more* the row that shows you less.
        if (item.id.startsWith('expand:')) {
          setExpanded(item.id.slice('expand:'.length));
          return;
        }
        close();
        // 📁 **§12's *Ask Signora*** — ⚡ the door the rail already opens, not a
        // second one. ⛔ **No question is carried**: the panel has no input, by
        // TASK-482's own refusal.
        if (item.id === 'ask:signora') {
          copilot?.open();
          return;
        }
        // ⛔ **No `panel` destination yet, and both are treated the same** —
        // 📁 the palette's own contract allows exactly that: *"a caller with
        // nowhere to put a panel simply treats both the same."* ⚡ **Inventing
        // a panel here would be this row building the utility panel**, which
        // is [TASK-1433](../../../docs/BACKLOG.md)'s.
        if (item.id.startsWith('nav:')) router.push(item.id.slice('nav:'.length));
        else if (item.id.startsWith('account:'))
          router.push(`/accounts/${item.id.slice('account:'.length)}`);
      }}
    />
  );
}
