'use client';

import { useRef, type KeyboardEvent } from 'react';

import { tabId, tabPanelId } from '@/components/ui/tabs';
import { cn } from '@/lib/design/cn';
import type { SavedView } from '@/lib/api/types';

/**
 * **The design's saved-view row** — 📁 `Fortune Signora Companies.dc.html`.
 *
 * > **`display:flex;align-items:center;gap:6px;border-bottom:1px solid
 * > var(--line-soft)`**, tabs on the left, **the view-mode switcher pushed
 * > right on the same line.**
 *
 * ## 🔴 One row, two controls — and that is the design's composition
 *
 * ⛔ **The switcher was on its own line above the filters**, which is not a
 * place the design has. 📁 **It belongs on the tab row's right**, and the
 * relationship between the two is the point: *which set of companies* and *how
 * to draw them* are the two questions a seller answers before reading anything.
 *
 * ## ⚡ The active tab is a bottom rule, never a fill
 *
 * 📁 ***"border-bottom:2px solid var(--brand)"*** with a `--sunken` field and a
 * 600 label; the rest are 400 on `--ink-3` with no rule. ⛔ **`margin-bottom:-1px`
 * so the active tab's rule sits ON the row's hairline** rather than above it —
 * without it the two lines stack and the tab reads as underlined twice.
 *
 * ## ⛔ No counts, and no badges — because nothing publishes them
 *
 * 📁 The design draws *41* beside each name and *Live · AI · Shared* after
 * some. ⚠️ **`SavedViewResponse` carries neither** — a count needs the view's
 * `declaration` run against the book, and a badge is a classification nothing
 * stores. ✅ **The names render; the numbers are not invented.**
 */

export type ViewMode = 'table' | 'cards' | 'board';

export interface ViewTabsProps {
  readonly views: readonly SavedView[];
  readonly loading: boolean;
  readonly selected: string | null;
  readonly onSelect: (id: string | null) => void;
  readonly mode: ViewMode;
  readonly onMode: (mode: ViewMode) => void;
  /** ⚡ **Why the chosen view could not be opened**, or `null`. */
  readonly refusal: string | null;
}

/** 📁 The design's own last tab — *"All companies"*, and it is the default. */
const ALL = 'All companies';

/**
 * ♿ **The id base this strip shares with the list it controls** — 📁
 * [B-1055](../../../../docs/BUGS.md). ⛔ **Exported**, because the panel is the
 * caller's markup and the two halves must resolve to the same id or the link is
 * decoration.
 */
export const VIEW_TABS = 'companies-saved-view';

/**
 * ♿ **`null` is a selection, and a selection needs an id.** ⚡ The *All
 * companies* tab has no `SavedView` behind it, so the strip and the panel agree
 * on one spelling for it here rather than each inventing one.
 */
export function viewTabValue(selected: string | null): string {
  return selected ?? 'all';
}

export function ViewTabs({
  views,
  loading,
  selected,
  onSelect,
  mode,
  onMode,
  refusal,
}: ViewTabsProps) {
  const refs = useRef(new Map<string, HTMLButtonElement>());
  const register = (value: string, node: HTMLButtonElement | null) => {
    if (node) refs.current.set(value, node);
    else refs.current.delete(value);
  };

  /**
   * ♿ **`→ ← Home End`, with wrap-around** — 📁
   * [B-1055](../../../../docs/BUGS.md). ⛔ **A roving index without this would
   * put every unselected view out of the keyboard's reach**, which is a
   * regression rather than a fix.
   *
   * ⚡ **The order is the rendered order**: *All companies* first, then the
   * saved views as the strip draws them.
   */
  const order = [viewTabValue(null), ...views.map((view) => viewTabValue(view.id))];

  const onKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    const index = order.indexOf(viewTabValue(selected));
    if (index === -1) return;

    let next: number | null = null;
    if (event.key === 'ArrowRight') next = (index + 1) % order.length;
    if (event.key === 'ArrowLeft') next = (index - 1 + order.length) % order.length;
    if (event.key === 'Home') next = 0;
    if (event.key === 'End') next = order.length - 1;
    if (next === null) return;

    event.preventDefault();
    const value = order[next];
    if (value === undefined) return;
    // ⚡ **Back to `null` for *All companies*** — the strip's own spelling is
    // internal, and the caller's contract is unchanged.
    onSelect(value === viewTabValue(null) ? null : value);
    refs.current.get(value)?.focus();
  };

  return (
    <>
      <div className="mb-4 flex flex-wrap items-center gap-1.5 border-b border-border-soft">
        {/**
         * ♿ **A `tablist` owes two things beyond the role** — 📁
         * [B-1055](../../../../docs/BUGS.md): **each tab names the panel it
         * controls**, and **the strip moves under `→ ← Home End` with a roving
         * index** so `Tab` leaves it rather than walking every saved view.
         * ⚡ **The same grammar `components/ui/tabs.tsx` implements**, spelled the
         * same way on purpose — 🔴 **three tab strips with three keyboard
         * behaviours is the drift a shared component exists to prevent.**
         */}
        <div
          role="tablist"
          aria-label="Saved views"
          onKeyDown={onKeyDown}
          className="flex flex-wrap items-center gap-1.5"
        >
          <Tab
            value={viewTabValue(null)}
            label={ALL}
            active={selected === null}
            onSelect={() => onSelect(null)}
            register={register}
          />
          {views.map((view) => (
            <Tab
              key={view.id}
              value={viewTabValue(view.id)}
              label={view.name}
              active={selected === view.id}
              onSelect={() => onSelect(view.id)}
              register={register}
            />
          ))}
          {/* ⚡ **A stated wait, not a spinner** — 📁 the design's loading rule is
              that the shape stays and the content resolves. ⛔ **Never an empty
              row**: [P-A](../../../../docs/DOMAIN_DISCOVERY_REGISTER.md) — the
              absence of views and the absence of an answer are different facts. */}
          {loading ? (
            <span role="status" className="px-3 py-2 text-xs text-content-subtle">
              Loading views…
            </span>
          ) : null}
        </div>

        {/* 🔴 **The switcher, on the tab row's right — the design's position.**
            📁 *"Table · Cards · Board"*, three modes in a `--sunken` pill group
            with a shadow on the active one.

            ✅ **Board landed once `Group` did.** ⚠️ **This comment previously
            explained why Board could not exist — *"every groupable column the
            design names is C-209's"* — and that expired on 2026-08-12 when
            [ADR-0409](../../../../docs/architecture/adr/0409-commercial-account-facts.md)
            released renewal and stage. **A board needs a grouping and there are
            now four honest ones.** */}
        {/* 🔴 **`Save to view` is NOT on this row and that is the design.**
            📁 It lives in the FILTER row, right-aligned beside *"312 of 8,412"* —
            see [`toolbar.tsx`](./toolbar.tsx). ⚡ **The two rows have different
            jobs**: this one carries the views and the mode switcher; saving acts
            on the filter state, so it belongs beside the count that describes it.
            ⛔ **`ml-auto` moves to the mode switcher below**, which is now the
            only right-hand control on the row. */}

        <div
          role="group"
          aria-label="View"
          // ⚡ **The row's only right-hand control now**, so `ml-auto` is
          // unconditional — ⛔ the pairing it used to negotiate with `Save to
          // view` is gone, because that control moved to the row it acts on.
          className="mb-1.5 ml-auto flex rounded-md bg-surface-sunken p-0.5"
        >
          {(['table', 'cards', 'board'] as const).map((value) => (
            <button
              key={value}
              type="button"
              aria-pressed={mode === value}
              onClick={() => onMode(value)}
              className={cn(
                'rounded px-3 py-1 text-xs font-semibold capitalize transition-colors',
                mode === value
                  ? 'bg-surface text-content shadow-sm'
                  : 'text-content-muted hover:text-content',
              )}
            >
              {value}
            </button>
          ))}
        </div>
      </div>

      {/* 🔴 **The refusal, where the tab that caused it is.** ⛔ **An
          `alert`, because the customer asked for something and did not get
          it** — 📁 [P-A](../../../../docs/DOMAIN_DISCOVERY_REGISTER.md): a
          failed read must never render as an empty result, and a view that
          silently did not apply is exactly that.

          ⚡ **The commonest case is not an error**: the store is
          workspace-wide and holds four screens' declarations, so a Reports
          definition in this row is ordinary — **and the sentence says so
          rather than implying something broke.** */}
      {refusal === null ? null : (
        <p role="alert" className="-mt-2 mb-4 text-xs text-content-muted">
          {refusal}
        </p>
      )}
    </>
  );
}

function Tab({
  label,
  value,
  active,
  onSelect,
  register,
}: {
  value: string;
  label: string;
  active: boolean;
  onSelect: () => void;
  register: (value: string, node: HTMLButtonElement | null) => void;
}) {
  return (
    <button
      type="button"
      ref={(node) => register(value, node)}
      role="tab"
      id={tabId(VIEW_TABS, value)}
      aria-selected={active}
      // ♿ **The panel every tab in this strip swaps** — the company list below.
      aria-controls={tabPanelId(VIEW_TABS)}
      // ⛔ **Roving index.** Without it `Tab` walks every saved view before it
      // reaches the list those views are for.
      tabIndex={active ? 0 : -1}
      onClick={onSelect}
      className={cn(
        // 📁 *"padding:9px 12px;border-radius:8px 8px 0 0"* — square at the
        // bottom, because the tab meets the row's rule there.
        '-mb-px rounded-t-md px-3 py-2 text-sm transition-colors',
        active
          ? 'border-b-2 border-accent bg-surface-sunken font-semibold text-content'
          : 'border-b-2 border-transparent font-normal text-content-muted hover:text-content',
      )}
    >
      {label}
    </button>
  );
}
