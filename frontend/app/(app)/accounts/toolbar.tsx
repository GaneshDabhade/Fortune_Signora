'use client';

import { Button, Select } from '@/components/ui';
import { cn } from '@/lib/design/cn';
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
  readonly mode: 'table' | 'cards';
  readonly onMode: (mode: 'table' | 'cards') => void;
  readonly density: Density;
  readonly onDensity: (density: Density) => void;
  readonly columns: readonly ColumnId[];
  readonly onColumns: (columns: readonly ColumnId[]) => void;
  readonly filters: Filters;
  readonly onFilters: (filters: Filters) => void;
  readonly kinds: readonly string[];
  readonly sources: readonly string[];
  readonly shown: number;
  readonly loaded: number;
  readonly onExport: () => void;
}

export function AccountsToolbar({
  mode,
  onMode,
  density,
  onDensity,
  columns,
  onColumns,
  filters,
  onFilters,
  kinds,
  sources,
  shown,
  loaded,
  onExport,
}: ToolbarProps) {
  const chosen = new Set<ColumnId>(columns);

  return (
    <div
      data-testid="accounts-toolbar"
      className="mb-4 flex flex-col gap-3 border-b border-border pb-4"
    >
      <div className="flex flex-wrap items-center gap-2">
        {/* 📁 *"Table · Cards · Board"* — ⛔ **Board is absent**: it groups by a
            column, and every groupable column the design names is
            [C-209](../../../../docs/LANE_COORDINATION.md)'s. **A third tab that
            grouped by `kind` would be the design's word on a different idea.** */}
        <div role="group" aria-label="View" className="flex rounded-md bg-surface-sunken p-0.5">
          {(['table', 'cards'] as const).map((value) => (
            <button
              key={value}
              type="button"
              aria-pressed={mode === value}
              onClick={() => onMode(value)}
              className={cn(
                'rounded px-3 py-1 text-sm capitalize transition-colors',
                mode === value ? 'bg-surface text-content shadow-sm' : 'text-content-muted',
              )}
            >
              {value}
            </button>
          ))}
        </div>

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

        <Button variant="ghost" onClick={onExport} className="ml-auto">
          Export
        </Button>
      </div>

      {/* 📁 *"Filters · Add condition"* — ⛔ **only over fields the contract
          publishes.** 📁 The design's *"Renewal within 90 days"* and *"Score
          below 50"* are both [C-209](../../../../docs/LANE_COORDINATION.md)'s. */}
      <div className="flex flex-wrap items-end gap-2" role="group" aria-label="Filters">
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
        {/* 🔴 **The sentence that keeps the filters honest.** 📁 The design
            prints *"312 of 8,412"* — ⛔ **the total is not published by this
            read**, and printing one would invent the number a seller trusts
            most. ✅ **What is true is how many have been read.** */}
        <p className="text-2xs text-content-subtle" data-testid="companies-count">
          {isFiltered(filters) ? `${shown} of ${loaded} loaded` : `${loaded} loaded`}
        </p>

        <details className="text-xs">
          <summary className="cursor-pointer text-content-muted">
            Columns · {chosen.size} of {COLUMNS.length}
          </summary>
          <div className="mt-2 flex flex-col gap-1 rounded border border-border bg-surface p-2">
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
