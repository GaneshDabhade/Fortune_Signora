'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';

import { CommandPalette, type CommandItem } from '@/components/ui';
import { useAccountSearch } from '@/lib/query/hooks/search';
import { RAIL_DESTINATIONS } from '@/components/shell/navigation';
import { can, guardFor, type Capability, type WorkspaceRole } from '@/lib/state/permissions';
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
 * shortcut.** 📁 The design's groups are `Ask Signora` · `Recents` · `Actions`
 * · `Navigate`, and account results sit among them.
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

export function ShellPalette({ role }: { role: WorkspaceRole | null }) {
  const router = useRouter();
  const { activeWorkspace } = useWorkspaceContext();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');

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
    // 📁 **`Navigate` — the destinations the shell owns.** ⛔ **Filtered by the
    // same guard the rail applies**, so the palette is not a second answer to
    // *what can this person reach*.
    const navigate: CommandItem[] = RAIL_DESTINATIONS.filter((item) => {
      const guard = guardFor(item.href);
      return guard === undefined || can(role, guard.requires as Capability);
    }).map((item) => ({
      id: `nav:${item.href}`,
      label: item.label,
      group: 'Navigate',
      meta: item.href,
    }));

    // 📁 **Accounts — ONE group, not the owner of the shortcut.** ⚡ The
    // palette never sorts, so the server's group order is preserved: *"the
    // caller's order is the caller's ranking."*
    //
    // 🔴 **`coverage` is read before `results`, always.** 📁 The type says why,
    // and the product owner ruled it on 2026-08-05: *"the absence of results
    // and the absence of the group represent different business meanings."*
    // ⛔ **A palette that flattened every group would collapse *nothing
    // matched* into *we did not look*** — so a group Signora did not search is
    // skipped entirely rather than contributing an empty stretch of list.
    const accounts: CommandItem[] = (groups ?? [])
      .filter((group) => group.coverage === 'searched')
      .flatMap((group) =>
        group.results.map((result) => ({
          id: `account:${result.account.account_id}`,
          // ⛔ **`matched_name`, not the account's current name.** It is what
          // the person typed against, and showing a different string would
          // make a correct match look like a wrong one.
          label: result.matched_name,
          group: group.result_type === 'company' ? 'Companies' : 'Technologies',
          // ⚡ **Says so when the name has changed**, which is the one fact
          // that makes a match look wrong when it is right.
          meta: result.is_renamed ? 'renamed' : undefined,
        })),
      );

    return [...accounts, ...navigate];
  }, [groups, role]);

  const close = () => {
    setOpen(false);
    setQuery('');
  };

  return (
    <CommandPalette
      open={open}
      onClose={close}
      items={items}
      query={query}
      onQueryChange={setQuery}
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
        close();
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
