/**
 * **The Companies table's law: which columns exist, how they are filtered, and
 * at what density** — [TASK-1475](../../../docs/BACKLOG.md).
 *
 * ## 🔴 Every column here is a field the contract publishes
 *
 * 📁 **The design draws nine**: Company · Segment · Open ACV · Signora score ·
 * Renewal · Owner · Tags. ⛔ **Five of those had no source when this file was
 * written. Four do now**, each released by a ruling rather than by this file
 * deciding it could:
 *
 * | Column | Released by |
 * |---|---|
 * | **Tags** | [TASK-466](../../../docs/BACKLOG.md) · [ADR-0411](../../../docs/architecture/adr/0411-customer-organized-account-metadata.md) |
 * | **Owner** | [TASK-1479](../../../docs/BACKLOG.md) slice ⓶ · ADR-0411 |
 * | **Segment** | TASK-1479 slice ⓶b · ADR-0411 |
 * | **Open ACV · Renewal** | ⚡ **[ADR-0409](../../../docs/architecture/adr/0409-commercial-account-facts.md), ratified 2026-08-12** |
 *
 * > ⚠️ **This header said Open ACV and Renewal were *"refused in writing"* by
 * > [`crm.py`](../../../backend/modules/provider_normalization/infrastructure/mappers/crm.py).**
 * > 🔴 **That was true when it was written and stopped being true on
 * > 2026-08-12.** 📁 ADR-0409 §4: *"`crm.py`'s refusal is **discharged** by
 * > this ADR, not overridden"* — **and a claim about the present is corrected
 * > rather than left standing** ([§2](../../../CLAUDE.md)).
 *
 * ⛔ **Signora score is the one that is still nowhere**, and it has no column.
 *
 * ⚡ **So a column is defined only where a field exists**, and the type makes
 * the alternative unwriteable: `read` takes a `ListedAccount` and there is
 * nowhere to return a value from.
 *
 * > ⛔ **A column of `—` is worse than an absent column** ***when nothing was
 * > ever asked.*** ✅ **Where the read path exists, `—` is the honest answer**:
 * > it says Signora asked and no source has answered — see `NOTHING_SAID`.
 */
import { formatDay } from '@/components/intelligence/dates';
import type { AccountCommercial, ListedAccount, Money } from '@/lib/api/types';

export type ColumnId =
  | 'company'
  | 'segment'
  | 'acv'
  | 'renewal'
  | 'owner'
  | 'tags'
  | 'stage'
  | 'kind'
  | 'sources'
  | 'agreement'
  | 'freshness';

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
  /** 📁 **The design right-aligns Open ACV and Renewal and sets
   *  `font-variant-numeric:tabular-nums`.** ⚡ **A property of the column, not
   *  of the cell** — declared once so a figure cannot align one way in the
   *  header and another in the body. */
  readonly numeric?: true;
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

/**
 * 📁 **The design prints a figure, never a raw number** — *"$1,240,000"*,
 * `font-variant-numeric:tabular-nums`.
 *
 * ⛔ **The currency is the source's and is never converted.** 📁 [ADR-0409](../../../docs/architecture/adr/0409-commercial-account-facts.md)
 * §5 — *"a rate is applied at a moment… a converted figure stored on a claim
 * is correct briefly and wrong permanently."* ⚡ **So the browser's own
 * formatter is given the claim's currency and left to place the symbol**,
 * which is also how a European tenant's `EUR` renders correctly without this
 * file knowing a single symbol.
 */
export function formatMoney(money: Money): string {
  return new Intl.NumberFormat(undefined, {
    style: 'currency',
    currency: money.currency,
    maximumFractionDigits: 0,
  }).format(money.amount);
}

/**
 * ⚡ **What a cell shows when nothing has been said.**
 *
 * 🔴 **This is the one string on the screen that is easiest to get wrong.**
 * ⛔ **Not `0`, not `$0`, not *"None"*** — 📁 ADR-0409 §5: *"absence is never
 * inferred, defaulted or zero-filled"*, and a zero ACV is a figure a seller
 * would act on.
 *
 * ⚠️ **An em dash is honest HERE and was not before this read existed.** 📁
 * This file's own header refuses `—` *"when the truth is that nothing was ever
 * asked"* — ✅ **the read path now asks**, so the cell means *Signora asked and
 * no source has answered*, which is exactly what a dash says.
 */
export const NOTHING_SAID = '—';

/** ⚠️ **`is_mapped` is a state the product SHOWS.** 📁 The CRM Integrations
 *  design — *"214 opportunities now sit in stages Signora treats as
 *  unmapped"* — ⛔ so an unmapped stage renders the customer's own word rather
 *  than being hidden or guessed at. */
export function stageLabel(commercial: AccountCommercial): string {
  return commercial.stage === null ? NOTHING_SAID : commercial.stage.label;
}

export const COLUMNS: readonly ColumnSpec[] = [
  { id: 'company', label: 'Company', pinned: true, read: (r) => r.account.name ?? '' },
  // ⚡ **Segment gained a source on 2026-08-15** — TASK-1479 slice ⓶b. ⛔ **No
  // `read`, for the reason Tags and Owner have none**: a saved grouping is
  // `commercial_profile`'s and an account is `knowledge_graph`'s, so the screen
  // joins them from a second endpoint rather than reading a field the account
  // row does not carry (§5).
  { id: 'segment', label: 'Segment' },
  /**
   * ⚡ **Released by [ADR-0409](../../../docs/architecture/adr/0409-commercial-account-facts.md)**,
   * ratified 2026-08-12 — **the ruling this file's header recorded as pending
   * under its old number.** ⛔ **The refusal it quotes from `crm.py` is
   * discharged by that ADR rather than overridden**, and the mapper's comment
   * now cites it.
   *
   * ⚠️ **The column exists because the FIELD exists**, which is this file's
   * law. **Whether a value arrives depends on a customer connecting a
   * system** — 📁 [409](../../../docs/architecture/409-inbound-source-port-contract.md)
   * steps 3–5, `provider_platform`'s and held on
   * [C-300](../../../docs/LANE_COORDINATION.md). ⛔ **Nothing here fabricates
   * one in the meantime.**
   */
  {
    id: 'acv',
    label: 'Open ACV',
    numeric: true,
    read: (r) => (r.commercial.open_acv === null ? '' : formatMoney(r.commercial.open_acv)),
  },
  {
    id: 'renewal',
    label: 'Renewal',
    numeric: true,
    read: (r) =>
      r.commercial.renewal_date === null ? '' : formatDay(r.commercial.renewal_date),
  },
  // ⚡ **Owner gained a source on 2026-08-14** — TASK-1479 slice ⓶. ⛔ **Like
  // Tags, it has no `read`**: a different bounded context's fact, joined by the
  // screen from its own endpoint (§5).
  { id: 'owner', label: 'Owner' },
  { id: 'tags', label: 'Tags' },
  /**
   * ⛔ **Available, and not one of the design's drawn columns.** 📁 The design's
   * table draws Company · Segment · Open ACV · Signora score · Renewal · Owner
   * · Tags, and shows stage in the expanded row and the context drawer instead.
   *
   * ✅ **It is offered in `Columns · 9 of 42` because the contract publishes
   * it** — ⚠️ **which is the opposite of inventing a column: the field is real,
   * and the design's own control is a set larger than the default.**
   */
  { id: 'stage', label: 'Stage', read: (r) => r.commercial.stage?.label ?? '' },
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
];

/** 📁 The design's `Columns · 9 of 42` control. ⛔ **The pinned column is always
 *  in the set**, so a stored choice cannot produce an unidentifiable row. */
export const DEFAULT_COLUMNS: readonly ColumnId[] = [
  'company',
  'segment',
  'acv',
  'renewal',
  'owner',
  'tags',
];

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

/**
 * **One active condition, in the design's own grammar** — 📁 `Fortune Signora
 * Companies.dc.html`.
 *
 * > **`Renewal · within · 90 days ×`** — ⚡ **three parts and a remove**, where
 * > the field is `--ink-4`, the operator `--ink-3` and the value 600 weight.
 *
 * ⛔ **The design's own four conditions cannot be built** — *Renewal within 90
 * days*, *Score below 50*, *Last touch older than 14 days* and *Procurement
 * never engaged* are all [C-209](../../docs/LANE_COORDINATION.md)'s, with no
 * field behind any of them.
 *
 * ✅ **The grammar is the design's and the conditions are this contract's.**
 * ⚠️ **That distinction is the whole point**: the shape a seller reads is the
 * design's, and every value in it is one the product can actually answer.
 */
export interface Condition {
  readonly id: keyof Filters;
  readonly field: string;
  readonly operator: string;
  readonly value: string;
}

/**
 * **The active conditions, in the order the design reads them.**
 *
 * ⛔ **Only what is set.** 📁 The design draws a chip per *condition*, never a
 * chip per available field — **a row reading *Any kind*, *Any source*, *Any time*
 * would state three conditions where none exist.**
 */
export function conditionsOf(filters: Filters): readonly Condition[] {
  const out: Condition[] = [];
  if (filters.name !== '')
    out.push({ id: 'name', field: 'Name', operator: 'contains', value: filters.name });
  if (filters.kind !== null)
    out.push({ id: 'kind', field: 'Kind', operator: 'is', value: filters.kind });
  if (filters.source !== null)
    out.push({ id: 'source', field: 'Source', operator: 'is', value: filters.source });
  if (filters.staleAfterDays !== null)
    out.push({
      id: 'staleAfterDays',
      field: 'Last observed',
      operator: 'older than',
      value: `${filters.staleAfterDays} days`,
    });
  // ⛔ **Its own condition, not a value of the one above.** ⚡ *Never observed*
  // and *older than 30 days* are different questions, and a chip that folded
  // them together could not be removed independently.
  if (filters.neverObserved)
    out.push({ id: 'neverObserved', field: 'Last observed', operator: 'is', value: 'Never' });
  return out;
}

/** ⚡ **Clearing one condition leaves the others standing** — the `×` on a chip
 *  removes that condition and nothing else. */
export function without(filters: Filters, id: keyof Filters): Filters {
  switch (id) {
    case 'name':
      return { ...filters, name: '' };
    case 'kind':
      return { ...filters, kind: null };
    case 'source':
      return { ...filters, source: null };
    case 'staleAfterDays':
      return { ...filters, staleAfterDays: null };
    case 'neverObserved':
      return { ...filters, neverObserved: false };
  }
}
