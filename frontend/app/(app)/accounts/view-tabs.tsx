'use client';

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

export type ViewMode = 'table' | 'cards';

export interface ViewTabsProps {
  readonly views: readonly SavedView[];
  readonly loading: boolean;
  readonly selected: string | null;
  readonly onSelect: (id: string | null) => void;
  readonly mode: ViewMode;
  readonly onMode: (mode: ViewMode) => void;
}

/** 📁 The design's own last tab — *"All companies"*, and it is the default. */
const ALL = 'All companies';

export function ViewTabs({
  views,
  loading,
  selected,
  onSelect,
  mode,
  onMode,
}: ViewTabsProps) {
  return (
    <div className="mb-4 flex flex-wrap items-center gap-1.5 border-b border-border-soft">
      <div role="tablist" aria-label="Saved views" className="flex flex-wrap items-center gap-1.5">
        <Tab label={ALL} active={selected === null} onSelect={() => onSelect(null)} />
        {views.map((view) => (
          <Tab
            key={view.id}
            label={view.name}
            active={selected === view.id}
            onSelect={() => onSelect(view.id)}
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
          📁 *"Table · Cards · Board"*. ⛔ **Board is absent and deliberately
          so**: it groups by a column, and every groupable column the design
          names is [C-209](../../../../docs/LANE_COORDINATION.md)'s. **A third
          tab grouping by `kind` would be the design's word on a different
          idea** — and a control that silently did nothing is
          [B-255](../../../../docs/BUGS.md). */}
      <div
        role="group"
        aria-label="View"
        className="mb-1.5 ml-auto flex rounded-md bg-surface-sunken p-0.5"
      >
        {(['table', 'cards'] as const).map((value) => (
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
  );
}

function Tab({
  label,
  active,
  onSelect,
}: {
  label: string;
  active: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      role="tab"
      aria-selected={active}
      onClick={onSelect}
      className={cn(
        // 📁 *"padding:9px 12px;border-radius:8px 8px 0 0"* — square at the
        // bottom, because the tab meets the row's rule there.
        '-mb-px rounded-t-md px-3 py-2 text-sm transition-colors',
        'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2',
        'focus-visible:outline-accent',
        active
          ? 'border-b-2 border-accent bg-surface-sunken font-semibold text-content'
          : 'border-b-2 border-transparent font-normal text-content-muted hover:text-content',
      )}
    >
      {label}
    </button>
  );
}
