/**
 * **Suggesting the address an organization will live at** — 📁 screen `03`.
 *
 * > *"Workspace URL · `eu.signora.app/northwind` · **Checked as you type,
 * > 300ms after you stop. Permanent once created.**"*
 *
 * ### ⚡ The client suggests; the person decides; the server validates
 *
 * ⛔ **The backend deliberately does NOT derive a slug from a name.** 📁
 * `CreateWorkspaceInput.slug` says why: the value stored is *the one they
 * accepted*, and deriving it a second time server-side would be two producers
 * of one permanent identifier ([§2](../../../CLAUDE.md)).
 *
 * ✅ **So this is a suggestion and never a guarantee.** It can produce
 * something the domain refuses — an empty string from a name of pure
 * punctuation, for instance — **and that is correct**: the field is editable,
 * the availability check runs on what is actually in it, and `Create` is
 * refused until the server agrees.
 */

/** 📁 Mirrors `MIN_WORKSPACE_SLUG_LENGTH` / `MAX_WORKSPACE_SLUG_LENGTH`. */
export const MIN_SLUG = 3;
export const MAX_SLUG = 63;

/**
 * A first guess at the address, from whatever the organization is called.
 *
 * ⚠️ **Diacritics are folded rather than dropped.** *Ærø Logistik* becomes
 * `aero-logistik` and not `r-logistik` — ⛔ **a name losing its first letter
 * because of an accent is the kind of quiet wrong that nobody reports.**
 */
export function suggestSlug(name: string): string {
  return name
    .normalize('NFKD')
    // Strip the combining marks NFKD just separated out.
    .replace(/[̀-ͯ]/g, '')
    .replace(/[ÆæŒœØøÅåÐðÞþß]/g, (c) => DIGRAPHS[c] ?? c)
    .toLowerCase()
    // Anything that is not a hostname character becomes a boundary.
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, MAX_SLUG)
    // A trim to MAX_SLUG can leave a trailing hyphen behind.
    .replace(/-+$/, '');
}

/** ⚡ **The letters NFKD cannot decompose**, because they are not accented
 *  forms of anything — they are their own letters. */
const DIGRAPHS: Record<string, string> = {
  Æ: 'ae', æ: 'ae', Œ: 'oe', œ: 'oe',
  Ø: 'o', ø: 'o', Å: 'aa', å: 'aa',
  Ð: 'd', ð: 'd', Þ: 'th', þ: 'th', ß: 'ss',
};
