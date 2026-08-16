/**
 * **The Companies table's law: which columns exist, how they are filtered, and
 * at what density** — [TASK-1475](../../../docs/BACKLOG.md).
 *
 * ## 🔴 Every column here is a field the contract publishes
 *
 * 📁 **The design draws nine**: Company · Segment · Open ACV · Signora score ·
 * Renewal · Owner · Tags. ⛔ **Five of those had no source when this file was
 * written.** ⚡ **Two now do**: **Tags** shipped as
 * [TASK-466](../../../docs/BACKLOG.md) and **Owner** as
 * [TASK-1479](../../../docs/BACKLOG.md) slice ⓶, both on
 * [ADR-0411](../../../docs/architecture/adr/0411-customer-organized-account-metadata.md)
 * — **the ruling C-1425 was waiting for.** ⚠️ **Segment is still absent and is
 * NOT the same concept as this module's ICP-segment**, which is why it has not
 * followed them. **Open ACV and
 * Renewal are refused in writing** by
 * [`crm.py`](../../../backend/modules/provider_normalization/infrastructure/mappers/crm.py):
 * *"contract value, renewal date… have no canonical attribute, and
 * `ClaimAttribute` says an RFC extends it."* 📁 **[C-209](../../../docs/LANE_COORDINATION.md)
 * is that decision and this file does not pre-empt it.**
 *
 * ⚡ **So a column is defined only where a field exists**, and the type makes
 * the alternative unwriteable: `read` takes a `ListedAccount` and there is
 * nowhere to return a value from.
 *
 * > ⛔ **A column of `—` is worse than an absent column**: it says Signora
 * > looked and found nothing, when the truth is that nothing was ever asked.
 */
import { formatDay } from '@/components/intelligence/dates';
import type { ListedAccount } from '@/lib/api/types';

export type ColumnId =
  | 'company'
  | 'kind'
  | 'sources'
  | 'agreement'
  | 'freshness'
  | 'owner'
  | 'segment'
  | 'tags';

export interface ColumnSpec {
  readonly id: ColumnId;
  readonly label: string;
  /** ⛔ **Company cannot be turned off.** 📁 The design pins it left — *"company
   *  and score pin left… so horizontal scroll never produces a seam"* — and a
   *  table of rows you cannot identify is not a narrower table, it is a broken
   *  one. */
  readonly pinned?: true;
  /**
   * ⛔ **Absent where the value is not ON the row**, and `tags` is the first
   * such column — [TASK-466](../../../docs/BACKLOG.md).
   *
   * ⚡ **The header comment above says a column exists only where a field
   * exists, and that is still true**: a tag has a source, just not on
   * `ListedAccount`. 📁 It is `commercial_profile`'s and an account is
   * `knowledge_graph`'s, so **folding one into the other's response would be a
   * cross-module dependency bought for a column**
   * ([§5](../../../CLAUDE.md)). ✅ **The screen reads both and joins them,
   * which is the boundary working rather than an omission.**
   *
   * ⚠️ **So `read` is optional rather than returning `''`.** A column that
   * answered the empty string would say *"Signora looked and found nothing"*
   * for an account that simply is not in this answer — 📁 the exact
   * `—`-versus-absent distinction this file's header refuses.
   */
  readonly read?: (row: ListedAccount) => string;
}

/** ⚡ **Freshness in days, or `null` when no source has ever reported.** 📁 The
 *  contract's own words: *"not when Signora last looked."* */
export function daysSinceObserved(row: ListedAccount, now: Date): number | null {
  const at = row.account.last_observed_at;
  if (at === null) return null;
  const then = new Date(at);
  if (Number.isNaN(then.getTime())) return null;
  return Math.floor((now.getTime() - then.getTime()) / 86_400_000);
}

export const COLUMNS: readonly ColumnSpec[] = [
  { id: 'company', label: 'Company', pinned: true, read: (r) => r.account.name ?? '' },
  { id: 'kind', label: 'Kind', read: (r) => r.kind },
  { id: 'sources', label: 'Sources', read: (r) => String(r.account.source_count) },
  { id: 'agreement', label: 'Name agreement', read: (r) => r.account.agreement },
  {
    id: 'freshness',
    label: 'Last observed',
    /**
     * ⚡ **A date a person reads, not the wire format.**
     *
     * ⛔ **This printed the raw ISO string** — `2026-07-28T00:00:00Z` — **in a
     * table cell.** 🔴 **The headed screenshot is what found it**: every gate
     * was green, because a timestamp rendered verbatim is a correct string.
     *
     * ✅ **`formatDay` is reused rather than reimplemented** — 📁 the
     * intelligence surfaces already answer *what day was this* and a second
     * formatter would eventually disagree with the first
     * ([§2](../../../CLAUDE.md), truth has one representation).
     *
     * ⚠️ **`Never` is kept as-is.** 📁 Null means no source has ever reported
     * anything, and that is a different fact from an old date rather than a
     * missing one.
     */
    read: (r) =>
      r.account.last_observed_at === null ? 'Never' : formatDay(r.account.last_observed_at),
  },
  // ⚡ **Released by [C-1425](../../../docs/LANE_COORDINATION.md)**, which the
  // header above records as one of the five columns with no source. **It has
  // one now** — [ADR-0411](../../../docs/architecture/adr/0411-customer-organized-account-metadata.md).
  // ⚡ **Owner gained a source on 2026-08-14** — TASK-1479 slice ⓶ built it,
  // and the header note above recorded it as one of the five columns that had
  // none. ⛔ **Like Tags, it has no `read`**: it is a different bounded
  // context's fact, joined by the screen from its own endpoint rather than
  // carried on the account row (§5).
  { id: 'owner', label: 'Owner' },
  // ⚡ **Segment gained a source on 2026-08-15** — TASK-1479 slice ⓶b, and the
  // third of the five source-less columns the header above records to get one.
  // ⛔ **No `read`, for the reason Tags and Owner have none**: a saved grouping
  // is `commercial_profile`'s and an account is `knowledge_graph`'s, so the
  // screen joins them from a second endpoint rather than reading a field the
  // account row does not carry (§5).
  { id: 'segment', label: 'Segment' },
  { id: 'tags', label: 'Tags' },
];

/** 📁 The design's `Columns · 9 of 42` control. ⛔ **The pinned column is always
 *  in the set**, so a stored choice cannot produce an unidentifiable row. */
export const DEFAULT_COLUMNS: readonly ColumnId[] = ['company', 'kind', 'sources', 'freshness'];

export function visibleColumns(chosen: readonly ColumnId[]): readonly ColumnSpec[] {
  const wanted = new Set<ColumnId>(chosen);
  for (const column of COLUMNS) if (column.pinned) wanted.add(column.id);
  return COLUMNS.filter((column) => wanted.has(column.id));
}

/**
 * 📁 **Density** — the design's toolbar control. ⚡ **The vocabulary is the
 * profile's own** (`comfortable` | `compact`), because a person already sets
 * this about themselves and a second word for one idea is a second answer
 * ([§2](../../../CLAUDE.md)).
 */
export type Density = 'comfortable' | 'compact';

export const ROW_PADDING: Record<Density, string> = {
  comfortable: 'py-3',
  compact: 'py-1.5',
};

/**
 * 🔴 **Filters over fields that exist, and nothing else.**
 *
 * 📁 The design's chips read *"Renewal within 90 days"*, *"Score below 50"* —
 * ⛔ **both are C-209's.** ⚡ **What can be asked of this contract is who the
 * account is, where it came from, what kind it is, and how fresh it is.**
 */
export interface Filters {
  readonly name: string;
  readonly kind: string | null;
  readonly source: string | null;
  /** ⚡ **Older than this many days**, or `null` for no freshness condition.
   *  ⛔ **`never` is its own answer** and is not the same as *very old*. */
  readonly staleAfterDays: number | null;
  readonly neverObserved: boolean;
}

export const NO_FILTERS: Filters = {
  name: '',
  kind: null,
  source: null,
  staleAfterDays: null,
  neverObserved: false,
};

export function isFiltered(filters: Filters): boolean {
  return (
    filters.name.trim() !== '' ||
    filters.kind !== null ||
    filters.source !== null ||
    filters.staleAfterDays !== null ||
    filters.neverObserved
  );
}

/**
 * ⚠️ **Client-side, over the page in hand, and the screen says so.**
 *
 * ⛔ **The endpoint takes no filter parameters** — 📁 `accounts-list` publishes
 * `limit` and `cursor` and nothing else — **so a filter here narrows what has
 * been read, never the book.** ⚡ **That is a true statement a customer can act
 * on; a filter that silently searched one page of 8,412 while looking like it
 * searched all of them would not be.**
 */
export function applyFilters(
  rows: readonly ListedAccount[],
  filters: Filters,
  now: Date,
): readonly ListedAccount[] {
  const needle = filters.name.trim().toLowerCase();
  return rows.filter((row) => {
    if (needle !== '' && !(row.account.name ?? '').toLowerCase().includes(needle)) return false;
    if (filters.kind !== null && row.kind !== filters.kind) return false;
    if (filters.source !== null && row.account.source !== filters.source) return false;

    const age = daysSinceObserved(row, now);
    if (filters.neverObserved && age !== null) return false;
    if (filters.staleAfterDays !== null) {
      // ⛔ **Never-observed is not stale.** ⚡ **It is the absence of an
      // observation rather than an old one**, and folding the two would let a
      // *"older than 30 days"* chip claim Signora had looked.
      if (age === null || age < filters.staleAfterDays) return false;
    }
    return true;
  });
}

/** Every distinct value present in what has been read — ⛔ **never a fixed
 *  list**, which would offer a filter that matches nothing. */
export function choicesFor(
  rows: readonly ListedAccount[],
  of: 'kind' | 'source',
): readonly string[] {
  const seen = new Set<string>();
  for (const row of rows) {
    const value = of === 'kind' ? row.kind : row.account.source;
    if (value !== null && value !== '') seen.add(value);
  }
  return [...seen].sort();
}

/**
 * 📁 **The design's `Export`.** ⚡ **Exactly what is on screen** — the visible
 * columns, in their order, over the filtered rows.
 *
 * ⛔ **Not the whole book**: this screen has read one page and nothing else,
 * and an export named *"all companies"* that contained 50 would be the worst
 * kind of wrong — **silently plausible.**
 */
export function toCsv(
  rows: readonly ListedAccount[],
  columns: readonly ColumnSpec[],
): string {
  const escape = (value: string) =>
    /[",\n]/.test(value) ? `"${value.replaceAll('"', '""')}"` : value;
  // ⛔ **A column with no `read` is left OUT of the export, not exported
  // empty.** ⚡ An `Tags` header over a column of blanks would say Signora
  // looked and found nothing on every row — 📁 the `—`-versus-absent
  // distinction this file's header refuses, arriving in a file somebody opens
  // in a spreadsheet and believes.
  //
  // ⚠️ **Declared rather than silent**: [TASK-466](../../../docs/BACKLOG.md)
  // records it, and the first row that needs tags in an export will need the
  // joined read here too.
  const exportable = columns.filter((column) => column.read !== undefined);
  const header = exportable.map((column) => escape(column.label)).join(',');
  const body = rows.map((row) =>
    exportable.map((column) => escape(column.read!(row))).join(','),
  );
  return [header, ...body].join('\n');
}
