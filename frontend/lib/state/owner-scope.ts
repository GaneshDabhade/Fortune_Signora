/**
 * Whose work a list of accounts is showing.
 *
 * ⚠️ **This said *"the attention list"* and that screen is retired** — 📁 the
 * App Shell names nine destinations and Attention is not among them. ✅ **The
 * scope survives it**: Companies reads it, and the brief reads the same query
 * to offer *next*.
 *
 * **In the URL, not in state**, and for three reasons the product owner named:
 * it survives a refresh, it survives browser back, and it can be opened in a
 * second tab as a different view. **A `useState` would lose all three**, and a
 * persisted preference would decide for a seller what they were looking at
 * before they arrived.
 *
 * **And it has to travel on the account link.** The brief reads the same query
 * to offer *next* (D41) — a seller walking their own accounts who is then
 * offered somebody else's has been dropped out of the list they were working.
 *
 * The convention is the one `/settings/connections` already uses: read with
 * `useSearchParams`, write by navigating.
 */

export type OwnerScope = 'all' | 'mine' | 'unassigned';

const SCOPES: readonly OwnerScope[] = ['all', 'mine', 'unassigned'];

/** What a customer calls each one. `All` rather than `Everything`: it labels a
 * filter, and the shortest true word wins on a control read at a glance. */
export const SCOPE_WORDS: Record<OwnerScope, string> = {
  all: 'All',
  mine: 'Mine',
  unassigned: 'Unassigned',
};

/**
 * The scope a URL is asking for.
 *
 * **An unknown value reads as `all` rather than failing.** A hand-edited or
 * stale link should show a seller their accounts, not an error — the value is
 * a view preference, and there is nothing to protect.
 */
export function scopeFrom(value: string | null | undefined): OwnerScope {
  return SCOPES.includes(value as OwnerScope) ? (value as OwnerScope) : 'all';
}

/** A link that keeps the current view. `all` is the default, so it is left out
 * — a clean URL is the one a seller copies. */
export function withScope(path: string, scope: OwnerScope): string {
  return scope === 'all' ? path : `${path}?owner=${scope}`;
}
