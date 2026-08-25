/**
 * **The display name's rule, in one place** — 📁 `Fortune Signora User Profile`,
 * §07's `validation` table, verbatim:
 *
 * > ***"2–32 characters, trimmed. Emoji allowed, control characters stripped.
 * > Validated on blur."***
 *
 * ⚡ **It lives here rather than in the panel** because it is four separate
 * claims — a floor, a ceiling, a normalisation and a counting rule — and a
 * panel that inlined them would be the only place any of them could be read.
 */

/**
 * 🔴 **`\p{Cf}` is stripped EXCEPT the zero-width joiner, and that exception is
 * the whole reason this is not a one-line regex.**
 *
 * ⛔ **U+200D is a format character**, so the obvious rule — *strip `Cc` and
 * `Cf`* — deletes it. ⚡ **And U+200D is what holds a multi-part emoji
 * together**: `👩‍💻` is `U+1F469 U+200D U+1F4BB`, so stripping it turns one
 * glyph into two and silently rewrites what somebody typed.
 *
 * 📁 **The design allows emoji in the same sentence that asks for control
 * characters to be stripped**, so it cannot mean the reading that breaks them.
 */
const STRIPPED = /[\p{Cc}\p{Cf}]/gu;

/** ⚠️ **Spelled as an escape on purpose** — written literally it is invisible
 *  in this file, and an invisible character in the one rule that decides which
 *  invisible characters survive is a line nobody can review. */
const ZERO_WIDTH_JOINER = '\u200D';

/** Control characters out, surrounding whitespace out. Nothing else changes. */
export function normalizeDisplayName(raw: string): string {
  return raw.replace(STRIPPED, (ch) => (ch === ZERO_WIDTH_JOINER ? ch : '')).trim();
}

/**
 * ⚡ **Code points, not UTF-16 units.** ⛔ `'👩'.length` is 2, so a `.length`
 * check would refuse a one-emoji name for being *too short by one* while
 * counting it as two — wrong in both directions at once.
 */
function count(value: string): number {
  return [...value].length;
}

export const DISPLAY_NAME_MIN = 2;
export const DISPLAY_NAME_MAX = 32;

/**
 * The problem with this value, or `null` if there is none.
 *
 * ⛔ **Empty is not a problem.** ⚡ A display name is optional — the panel
 * sends `null` for it — so *"at least 2 characters"* is a rule about a name
 * somebody is giving, never a demand that they give one. **Refusing an empty
 * field would make an optional field mandatory by way of a validator.**
 */
export function displayNameProblem(raw: string): string | null {
  const value = normalizeDisplayName(raw);
  if (value === '') return null;
  if (count(value) < DISPLAY_NAME_MIN) return `At least ${DISPLAY_NAME_MIN} characters`;
  if (count(value) > DISPLAY_NAME_MAX) return `At most ${DISPLAY_NAME_MAX} characters`;
  return null;
}
