'use client';

import { Button, Select } from '@/components/ui';
import {
  COLUMNS,
  type ColumnId,
  type Density,
  type Filters,
  NO_FILTERS,
  isFiltered,
} from '@/lib/accounts/table';

/**
 * **The Companies toolbar** — [TASK-1475](../../../../docs/BACKLOG.md), against
 * 📁 `Fortune Signora Companies.dc.html`.
 *
 * ⚡ **Every control here narrows or renders what has already been read.** ⛔
 * **None of them claims to search the book**: 📁 the endpoint publishes `limit`
 * and `cursor` and nothing else, so a filter that looked like it searched
 * 8,412 while searching 50 would be the quietest lie on the screen — **and the
 * count beside them says which it is.**
 */
export interface ToolbarProps {
  readonly density: Density;
  readonly onDensity: (density: Density) => void;
  readonly columns: readonly ColumnId[];
  readonly onColumns: (columns: readonly ColumnId[]) => void;
  readonly filters: Filters;
  readonly onFilters: (filters: Filters) => void;
  readonly kinds: readonly string[];
  readonly sources: readonly string[];
  /**
   * ⚡ **Every account in the workspace, or `null` while the count has not
   * answered** — 📁 `accounts-count`.
   *
   * ⛔ **`null` rather than falling back to the loaded figure.** The design's
   * *"312 of 8,412"* is a claim about the book; **printing the page size in
   * its place would be wrong by more with every page, and look right on the
   * first.**
   */
  readonly total: number | null;
  readonly shown: number;
  readonly loaded: number;
}

export function AccountsToolbar({
  density,
  onDensity,
  columns,
  onColumns,
  filters,
  onFilters,
  kinds,
  sources,
  total,
  shown,
  loaded,
}: ToolbarProps) {
  const chosen = new Set<ColumnId>(columns);

  return (
    <div
      data-testid="accounts-toolbar"
      className="mb-4 flex flex-col gap-3 border-b border-border-soft pb-4"
    >
      <div className="flex flex-wrap items-center gap-2">
        {/* 📁 *"Density"* — ⚡ **the profile's own vocabulary**, because a person
            already sets this about themselves. */}
        <Select
          label="Density"
          labelHidden
          value={density}
          onChange={(event) => onDensity(event.target.value as Density)}
          options={[
            { value: 'comfortable', label: 'Comfortable' },
            { value: 'compact', label: 'Compact' },
          ]}
        />

      </div>

      {/* 📁 *"Filters · Add condition"* — ⛔ **only over fields the contract
          publishes.** 📁 The design's *"Renewal within 90 days"* and *"Score
          below 50"* are both [C-209](../../../../docs/LANE_COORDINATION.md)'s. */}
      <div className="flex flex-wrap items-end gap-2" role="group" aria-label="Filters">
        {/* 📁 **The design's own label**, in its own treatment — 11px, 600,
            +0.05em, uppercase, `--ink-4`. ⚡ §04 reserves uppercase for column
            heads and one eyebrow per page, **and this is the page's one.** */}
        <span className="self-center text-2xs font-semibold uppercase tracking-[0.05em] text-content-subtle">
          Filters
        </span>
        <label className="flex flex-col gap-1 text-xs text-content-muted">
          Name contains
          <input
            type="search"
            value={filters.name}
            onChange={(event) => onFilters({ ...filters, name: event.target.value })}
            className="h-control-md rounded border border-border bg-surface px-2 text-sm text-content"
          />
        </label>

        <Select
          label="Kind"
          value={filters.kind ?? ''}
          onChange={(e) => onFilters({ ...filters, kind: e.target.value === '' ? null : e.target.value })}
          options={[{ value: '', label: 'Any kind' }, ...kinds.map((k) => ({ value: k, label: k }))]}
        />

        <Select
          label="Source"
          value={filters.source ?? ''}
          onChange={(e) =>
            onFilters({ ...filters, source: e.target.value === '' ? null : e.target.value })
          }
          options={[
            { value: '', label: 'Any source' },
            ...sources.map((s) => ({ value: s, label: s })),
          ]}
        />

        {/* ⛔ **Two conditions, not one dropdown.** ⚡ *Never observed* is the
            ABSENCE of an observation and *older than* is an old one — 📁 the
            contract's own distinction, and folding them would let a staleness
            filter claim Signora had looked. */}
        <Select
          label="Last observed"
          value={filters.neverObserved ? 'never' : (filters.staleAfterDays?.toString() ?? '')}
          onChange={(event) => {
            const value = event.target.value;
            onFilters({
              ...filters,
              neverObserved: value === 'never',
              staleAfterDays: value === '' || value === 'never' ? null : Number(value),
            });
          }}
          options={[
            { value: '', label: 'Any time' },
            { value: '7', label: 'Older than 7 days' },
            { value: '30', label: 'Older than 30 days' },
            { value: 'never', label: 'Never observed' },
          ]}
        />

        {isFiltered(filters) ? (
          <Button variant="ghost" onClick={() => onFilters(NO_FILTERS)}>
            Clear filters
          </Button>
        ) : null}
      </div>

      <div className="flex flex-wrap items-center gap-3">
        {/* 🔴 **The sentence that keeps the filters honest**, and it now
            states the design's own figure.
 
            📁 The design prints *"312 of 8,412"*. ⚠️ **This comment used to
            say the total was not published by this read, and that was true
            until `accounts-count` existed** — 📁 [§2](../../../../CLAUDE.md):
            a claim about the present is corrected rather than left standing.
 
            ⛔ **The total is still omitted when the count has not answered**,
            and the loaded figure is never printed in its place: **inventing
            the number a seller trusts most is the quietest lie on the
            screen.** */}
        <p className="text-2xs text-content-subtle" data-testid="companies-count">
          {total !== null
            ? `${shown.toLocaleString()} of ${total.toLocaleString()}`
            : isFiltered(filters)
              ? `${shown} of ${loaded} loaded`
              : `${loaded} loaded`}
        </p>

        <details className="text-xs">
          <summary className="cursor-pointer text-content-muted">
            Columns · {chosen.size} of {COLUMNS.length}
          </summary>
          <div className="mt-2 flex flex-col gap-1 rounded border border-border-soft bg-surface p-2">
            {COLUMNS.map((column) => (
              <label key={column.id} className="flex items-center gap-2 text-content">
                <input
                  type="checkbox"
                  checked={column.pinned === true || chosen.has(column.id)}
                  /* ⛔ **Company cannot be turned off** — the design pins it
                     left, and a row you cannot identify is not a narrower
                     table. */
                  disabled={column.pinned === true}
                  onChange={() =>
                    onColumns(
                      chosen.has(column.id)
                        ? columns.filter((id) => id !== column.id)
                        : [...columns, column.id],
                    )
                  }
                />
                {column.label}
              </label>
            ))}
          </div>
        </details>
      </div>
    </div>
  );
}
