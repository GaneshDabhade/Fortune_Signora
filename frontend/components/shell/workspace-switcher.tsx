'use client';

import Link from 'next/link';
import { useEffect, useId, useMemo, useRef, useState } from 'react';

import { Skeleton } from '@/components/ui';
import { cn } from '@/lib/design/cn';
import { RAIL_WIDTH } from '@/lib/shell/rail';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';
// ⚡ **Shared with the standalone chooser** — [TASK-1421](../../../docs/BACKLOG.md).
// ⛔ Two implementations would eventually render different initials for one
// organization, in the rail and on the chooser.
import { initialsFor } from '@/lib/workspace/initials';

/**
 * **The workspace switcher, in the rail** — [TASK-1441](../../../docs/BACKLOG.md),
 * against 📁 `docs/design-snapshot/screens/Fortune Signora App Shell.dc.html`
 * §*Workspace switcher* ([D-138](../../../docs/DECISION_REGISTER.md)).
 *
 * > 📁 ***"Placement at the top of the rail matches the mental model:
 * > everything below belongs to it."***
 *
 * ## ⚡ This is the move [C-274](../../../docs/LANE_COORDINATION.md) was waiting for
 *
 * ⛔ **[TASK-1440](../../../docs/BACKLOG.md) was told to remove the switcher
 * from the top bar and this lane refused**, because its designed destination —
 * here — did not exist yet: **removing it then would have deleted a customer's
 * only way to change workspace rather than moved it.** ✅ **[D-225](../../../docs/DECISION_REGISTER.md)
 * §4 later ruled exactly that**, and the row is now the move it was always
 * meant to be.
 *
 * ## 🔴 Four of the design's row facts have no source, and they are ABSENT
 *
 * 📁 **The design's row is *"22px avatar, name, role and environment,
 * right-hand tag"*, grouped by organisation.** ⛔ **Measured 2026-08-10:
 * `Workspace` publishes `id`, `name`, `created_at`, `updated_at`.** **Nothing
 * else exists.**
 *
 * | Design | Source |
 * |---|---|
 * | Name · avatar | ✅ **`name`, and initials derived from it** |
 * | Organisation grouping | ⛔ **no parent organisation on the contract** |
 * | Role per workspace | ⛔ **`useViewerRole` answers for the ACTIVE one only** |
 * | Environment · sandbox | ⛔ **no field, and [C-256](../../../docs/LANE_COORDINATION.md) already carries the sandbox gap** |
 * | Right-hand tag | ⛔ **it renders the three above** |
 *
 * ⚠️ **Role and environment are the two the design gives a SAFETY reason for**:
 * 📁 *"role and environment on the row prevent the classic mistake of editing
 * production while thinking it is sandbox."* ⛔ **So their absence is not
 * cosmetic and is raised as [C-276](../../../docs/LANE_COORDINATION.md)** —
 * **a switcher that cannot tell you which environment you are entering is the
 * condition that warning describes.**
 *
 * ⛔ **Nothing is invented to fill them.** A tag reading *"Prod"* on every row
 * because no field says otherwise is worse than no tag: **it would be the
 * product asserting a fact it does not have, about the one thing the design
 * says people get wrong.**
 *
 * ## ✅ What IS built, because it has everything it needs
 *
 * 📁 **Route preservation** — *"switching keeps the current route when it
 * exists in the destination"* — ⚡ **the design's own rationale is that it
 * *"makes multi-workspace comparison a two-second task"*.** ✅ **Every route in
 * this product exists in every workspace** (there is no per-workspace route
 * tree), **so *when it exists* is satisfied by staying put** — and the provider
 * re-reads scoped data on the id change.
 *
 * 📁 **`⌘⇧W` from anywhere · `1`–`9` by position · type to filter · `⏎`
 * switches · focus returns to the trigger on close.** ⚡ **All five are
 * behaviour, and none needs a field the platform lacks.**
 *
 * ## ⚠️ A literal foreground was written here first, and a guard caught a dark-theme defect
 *
 * ⛔ **The design draws the selected row's avatar on a white foreground**, so a
 * literal read as faithful. 📁 **`design-tokens.test.tsx` refused it twice** —
 * once in the class and once in a comment quoting the value, ⚡ **which is the
 * guard being right about prose as well as code.**
 *
 * 🔴 **And it was not merely untokenised.** **`--color-accent-contrast` inverts
 * between the two themes** — it is near-white on light and near-black on dark,
 * because the dark theme's accent is a LIGHTER blue. ⛔ **A fixed white
 * foreground would have been unreadable on the dark theme.** ✅ **A colour in
 * the design is a value for ONE theme; the token is the value for both.**
 */

/** 📁 *"Search appears above six workspaces."* ⛔ Six, not five. */
const SEARCH_APPEARS_ABOVE = 6;

/** 📁 *"1–9 selects by position."* ⛔ Nine, because a tenth has no key. */
const POSITION_KEYS = 9;

/**
 * 📁 *"Administrative actions are always the last two rows."*
 *
 * ⛔ **The design's two are not named, and only destinations that exist are
 * offered** — 📁 **there is no create-workspace route**, and a row leading
 * nowhere is [C-269](../../../docs/LANE_COORDINATION.md)'s finding again.
 */
const ADMIN_ACTIONS: readonly { label: string; href: string }[] = [
  { label: 'Organization settings', href: '/settings/organization' },
  { label: 'Members & roles', href: '/settings/team' },
];

export function WorkspaceSwitcher({ collapsed = false }: { collapsed?: boolean }) {
  const { workspaces, activeWorkspace, setActiveWorkspace, isLoading } =
    useWorkspaceContext();
  const [open, setOpen] = useState(false);
  const [filter, setFilter] = useState('');
  const triggerRef = useRef<HTMLButtonElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const searchRef = useRef<HTMLInputElement>(null);
  const listId = useId();

  const shown = useMemo(() => {
    const needle = filter.trim().toLowerCase();
    if (needle === '') return workspaces;
    return workspaces.filter((w) => w.name.toLowerCase().includes(needle));
  }, [workspaces, filter]);

  /**
   * 🔴 **`role="menu"` promises arrow keys, and this component had none.**
   *
   * ⛔ **Every row was a `<button>` reachable only by `Tab`**, which is what a
   * *list of buttons* offers — ⚡ **but a `menu` puts most screen readers into
   * application mode, where `Tab` is intercepted and the arrows are the way
   * through.** 📁 **The rule is the panel's own, one component along**:
   * [B-1055](../../../docs/BUGS.md) — *"the role is claimed only when it is
   * true."* **Here the role was true about the shape and false about the
   * keyboard.**
   *
   * ⚠️ **The items are the workspace rows AND the two administrative rows**, in
   * DOM order, because that is what the menu contains and a person arrowing
   * down expects to reach the end of it rather than stop halfway.
   */
  const itemsRef = useRef<(HTMLElement | null)[]>([]);
  const [activeItem, setActiveItem] = useState(0);

  /**
   * ⛔ **Filtering renumbers the rows**, so an index held across a keystroke
   * points at a different organization — or at nothing.
   */
  useEffect(() => {
    setActiveItem(0);
  }, [filter]);

  /**
   * ⛔ **The count comes from the DATA, never from the ref array.** ⚡ A ref
   * array holds `null` where a row has unmounted and keeps its length until
   * React writes over it, **so `itemsRef.current.length` is stale exactly when
   * the filter has just changed** — which is the moment somebody presses
   * `End`. **`shown` cannot be stale: it is what was rendered.**
   */
  const focusItem = (index: number) => {
    const total = shown.length + ADMIN_ACTIONS.length;
    if (total === 0) return;
    // ⚡ **Wraps, both ways** — the menu is short and a person holding ArrowDown
    // should not have to notice they reached the bottom.
    const next = ((index % total) + total) % total;
    setActiveItem(next);
    itemsRef.current[next]?.focus();
  };

  const onMenuKey = (event: React.KeyboardEvent) => {
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      // ⚡ **From the filter field, ArrowDown enters the list at the top**
      // rather than at wherever focus last was — somebody who has just typed is
      // looking at the first match.
      focusItem(event.target === searchRef.current ? 0 : activeItem + 1);
      return;
    }
    if (event.key === 'ArrowUp') {
      event.preventDefault();
      focusItem(event.target === searchRef.current ? -1 : activeItem - 1);
      return;
    }
    if (event.key === 'Home') {
      event.preventDefault();
      focusItem(0);
      return;
    }
    if (event.key === 'End') {
      event.preventDefault();
      focusItem(shown.length + ADMIN_ACTIONS.length - 1);
    }
  };

  const close = (returnFocus: boolean) => {
    setOpen(false);
    setFilter('');
    // 📁 *"Focus returns to the trigger on close."* ⚡ Without it a keyboard
    // user who presses Escape is returned to the top of the document.
    if (returnFocus) triggerRef.current?.focus();
  };

  /**
   * 🔴 **📁 `Workspace Chooser` §4.1.3: *"Switch start announces politely with
   * the destination name."*** ⛔ **Nothing announced at all.**
   *
   * ⚡ **A switch changes every scoped figure on the screen without moving the
   * page**, so a sighted reader sees the numbers change and a screen-reader
   * user is told nothing whatsoever.
   *
   * ⚠️ **Held OUTSIDE the menu deliberately.** ⛔ The menu unmounts on close and
   * `choose` closes it in the same tick — **a live region inside it would be
   * removed before the announcement could be read.**
   *
   * ⛔ **The design's second sentence — *"completion announces once with the
   * workspace and the landing route"* — is NOT implemented.** ⚡ This component
   * sets the active organization and returns; **it cannot observe when the
   * re-read finished**, and announcing completion at the moment of the request
   * would be claiming an arrival that has not happened.
   * 🔴 [C-1558](../../../docs/LANE_COORDINATION.md).
   */
  const [switchingTo, setSwitchingTo] = useState<string | null>(null);

  const choose = (id: string) => {
    setSwitchingTo(workspaces.find((each) => each.id === id)?.name ?? null);
    // 📁 *"Switching keeps the current route when it exists in the
    // destination."* ⛔ **No navigation happens here** — every route exists in
    // every workspace, so staying put IS route preservation, and the provider
    // re-reads scoped data from the new id.
    setActiveWorkspace(id);
    close(true);
  };

  // 📁 *"⌘⇧W opens the switcher from anywhere."*
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key.toLowerCase() !== 'w' || !event.shiftKey) return;
      if (!event.metaKey && !event.ctrlKey) return;
      event.preventDefault();
      setOpen(true);
      // ⚡ The trigger may not be mounted below `md`, where the rail is not
      // rendered; opening still works because the menu is anchored to the
      // container rather than to the trigger.
      window.setTimeout(() => searchRef.current?.focus(), 0);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        close(true);
        return;
      }
      // 📁 *"1–9 selects by position."* ⛔ Not while typing into the filter —
      // a person searching for "1Password" must be able to type a digit.
      if (document.activeElement === searchRef.current) return;
      const position = Number(event.key);
      if (!Number.isInteger(position) || position < 1 || position > POSITION_KEYS) return;
      const target = shown[position - 1];
      if (target !== undefined) {
        event.preventDefault();
        choose(target.id);
      }
    };
    const onPointer = (event: MouseEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) close(false);
    };
    document.addEventListener('keydown', onKey);
    document.addEventListener('mousedown', onPointer);
    return () => {
      document.removeEventListener('keydown', onKey);
      document.removeEventListener('mousedown', onPointer);
    };
  });

  if (isLoading) {
    return (
      <Skeleton className="mx-3 mt-3 h-[38px] rounded-md" />
    );
  }
  if (activeWorkspace === null) return null;

  const searchable = workspaces.length > SEARCH_APPEARS_ABOVE;

  return (
    <div ref={containerRef} className="relative px-3 pt-3">
      {/* ♿ **Polite, never assertive** — 📁 §4.1.3 reserves assertive for a
          state that ends the session. ⚡ **`sr-only` rather than hidden**: an
          `aria-live` region that is `display:none` announces nothing. */}
      <p role="status" className="sr-only">
        {switchingTo === null ? '' : `Switching to ${switchingTo}`}
      </p>
      <button
        ref={triggerRef}
        type="button"
        onClick={() => setOpen((was) => !was)}
        aria-expanded={open}
        aria-haspopup="menu"
        aria-controls={open ? listId : undefined}
        // ⛔ **The accessible name says *organization*** — ADR-0034, and the
        // reason the old select carried: a screen-reader user hearing
        // *"workspace"* would be the only customer ever told the internal word.
        aria-label={`Active organization: ${activeWorkspace.name}. Change it.`}
        // 📁 *"Trigger 38px tall inside the rail."*
        className={cn(
          'flex h-[38px] w-full items-center gap-2.5 rounded-md px-2 text-sm transition-colors',
          'hover:bg-surface-sunken',
          collapsed && 'justify-center px-0',
        )}
        title={collapsed ? activeWorkspace.name : undefined}
      >
        {/* 📁 *"22px avatar."* ⛔ `rounded-md`, not a circle — the top bar's
            account avatar is the only circle in the shell. */}
        <span
          aria-hidden
          className="grid h-[22px] w-[22px] flex-none place-items-center rounded-md bg-accent text-2xs font-semibold text-accent-contrast"
        >
          {initialsFor(activeWorkspace.name)}
        </span>
        {collapsed ? null : (
          <>
            <span className="min-w-0 flex-1 truncate text-left font-medium text-content">
              {activeWorkspace.name}
            </span>
            <span aria-hidden className="flex-none text-2xs text-content-subtle">
              ⌄
            </span>
          </>
        )}
      </button>

      {open ? (
        <div
          id={listId}
          role="menu"
          aria-label="Switch organization"
          onKeyDown={onMenuKey}
          // 📁 *"Menu 340px at --e4."* ⚡ `--shadow-xl` IS `--e4` — the fourth
          // elevation TASK-491 added for surfaces that sit over the page.
          style={{ width: 340, maxWidth: `calc(100vw - ${RAIL_WIDTH.collapsed}px)` }}
          className="absolute left-3 top-[calc(100%+6px)] z-30 overflow-hidden rounded-lg border border-border-soft bg-surface shadow-xl"
        >
          {searchable ? (
            <div className="border-b border-border-soft p-2">
              <input
                ref={searchRef}
                type="search"
                value={filter}
                onChange={(event) => setFilter(event.target.value)}
                // 📁 *"type to filter"* — and the label says organization.
                aria-label="Filter organizations"
                placeholder="Filter…"
                className="h-8 w-full rounded-md bg-surface-sunken px-2.5 text-sm text-content placeholder:text-content-subtle "
              />
            </div>
          ) : null}

          <ul className="max-h-72 overflow-y-auto py-1">
            {shown.length === 0 ? (
              // ⛔ Names the query rather than saying *no results*.
              <li className="px-3 py-2.5 text-sm text-content-muted">
                No organization matches “{filter}”.
              </li>
            ) : (
              shown.map((workspace, index) => {
                const current = workspace.id === activeWorkspace.id;
                return (
                  <li key={workspace.id}>
                    <button
                      type="button"
                      role="menuitemradio"
                      aria-checked={current}
                      ref={(node) => {
                        itemsRef.current[index] = node;
                      }}
                      // ⛔ **Roving, not every item at 0** — 📁 the same
                      // correction `utility-panel.tsx` needed: *"all three read
                      // `null` before, so `Tab` walked the strip instead of
                      // leaving it."* ⚡ **One stop for the whole menu.**
                      tabIndex={index === activeItem ? 0 : -1}
                      onFocus={() => setActiveItem(index)}
                      onClick={() => choose(workspace.id)}
                      className={cn(
                        'flex w-full items-center gap-2.5 px-3 py-2 text-left text-sm transition-colors',
                        ' focus-visible:bg-surface-sunken',
                        current
                          ? 'bg-accent-subtle font-semibold text-accent'
                          : 'text-content-muted hover:bg-surface-sunken hover:text-content',
                      )}
                    >
                      <span
                        aria-hidden
                        className={cn(
                          'grid h-[22px] w-[22px] flex-none place-items-center rounded-md text-2xs font-semibold',
                          current
                            ? 'bg-accent text-accent-contrast'
                            : 'bg-surface-sunken text-content-muted',
                        )}
                      >
                        {initialsFor(workspace.name)}
                      </span>
                      <span className="min-w-0 flex-1 truncate">{workspace.name}</span>
                      {/* 🔴 **📁 `Workspace Chooser` §1.4.1, and the third of the
                          three markers it names was missing.**

                          > ***"The selected row uses the brand tint, a
                          > 600-weight name and the word 'Current'. Colour alone
                          > never marks selection."***

                          ✅ **The tint and the weight were both here.** ⛔ **The
                          word was not** — `grep` for it returned zero. ⚡ **The
                          weight difference is a real non-colour signal, so this
                          was not *colour alone***; it is the design naming three
                          markers and the product carrying two, and **a 600-weight
                          name is the weakest of the three for a reader with low
                          vision.**

                          ♿ **`aria-checked` on the `menuitemradio` already tells
                          assistive technology** — ⛔ **so this is the SIGHTED
                          half**, which is what 1.4.1 is about. */}
                      {current ? (
                        <span className="flex-none text-2xs font-semibold uppercase tracking-wide text-accent">
                          Current
                        </span>
                      ) : null}
                      {/* 📁 *"1–9 selects by position."* ⚡ The hint is shown so
                          the shortcut is discoverable rather than documented
                          somewhere a customer will not read. */}
                      {index < POSITION_KEYS ? (
                        <kbd className="flex-none rounded bg-surface-sunken px-1.5 text-2xs font-normal text-content-subtle">
                          {index + 1}
                        </kbd>
                      ) : null}
                    </button>
                  </li>
                );
              })
            )}
          </ul>

          {/* 📁 *"Administrative actions are always the last two rows."* */}
          <div className="border-t border-border-soft py-1">
            {ADMIN_ACTIONS.map((action, offset) => (
              <Link
                key={action.href}
                href={action.href}
                role="menuitem"
                ref={(node) => {
                  itemsRef.current[shown.length + offset] = node;
                }}
                tabIndex={shown.length + offset === activeItem ? 0 : -1}
                onFocus={() => setActiveItem(shown.length + offset)}
                onClick={() => close(false)}
                className="block px-3 py-2 text-sm text-content-muted transition-colors hover:bg-surface-sunken hover:text-content focus-visible:bg-surface-sunken"
              >
                {action.label}
              </Link>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
