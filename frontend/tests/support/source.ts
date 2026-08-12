/**
 * **Shared source-walking for the guards that read the repository's own code.**
 *
 * 🔴 **Extracted 2026-08-12 for [B-252](../../../docs/BUGS.md)**, which found
 * [`library-reachability`](../components/library-reachability.test.tsx)
 * counting an identifier **in a comment** as a caller — ⛔ **so a doc-comment
 * could retire an orphan and the guard reported a PASS it had not earned.**
 *
 * ⚡ **The correct walker already existed**, written for
 * [`shortcut-registry`](../unit/shortcut-registry.test.ts) after that suite
 * found its own false positive. ⛔ **Copying it would have been a second
 * implementation of one behaviour** ([§2](../../../CLAUDE.md)), **and the copy
 * is always the one that stops being fixed** — 📁 so it moved here and both
 * guards import it.
 *
 * ⚠️ **Its fire-tests stay with the suite that owns them**, in
 * `shortcut-registry.test.ts`: the function moved, the proof did not.
 */

/**
 * ⚡ **Source with its comments removed, string-aware.**
 *
 * 🔴 **Needed because this suite found its own false positive on the first
 * run**: [`shortcuts.ts`](../../lib/shell/shortcuts.ts) DOCUMENTS that it was
 * measured against *"every `addEventListener('keydown'`"*, and the scan matched
 * the sentence describing the search. ⛔ **A file was reported as binding a key
 * because it explained the rule.**
 *
 * ⚠️ **And [B-162](../../../docs/BUGS.md) is the same defect in the other
 * direction** — a guard narrowed to strip comments started treating `//` in a
 * URL as the start of one, and stopped catching real matches. 📁 **Its lesson
 * is this function's shape**: *"narrowing a guard is only safe if you measure
 * what STOPS firing"* — ✅ **so the walker tracks quotes and template literals,
 * and both directions are fire-tested below.**
 */
export function withoutComments(source: string): string {
  let out = '';
  let i = 0;
  let quote: string | null = null;

  while (i < source.length) {
    const c = source[i];
    const next = source[i + 1];

    if (quote !== null) {
      out += c;
      if (c === '\\') {
        out += source[i + 1] ?? '';
        i += 2;
        continue;
      }
      if (c === quote) quote = null;
      i += 1;
      continue;
    }

    if (c === "'" || c === '"' || c === '`') {
      quote = c;
      out += c;
      i += 1;
      continue;
    }

    if (c === '/' && next === '/') {
      while (i < source.length && source[i] !== '\n') i += 1;
      continue;
    }

    if (c === '/' && next === '*') {
      i += 2;
      while (i < source.length && !(source[i] === '*' && source[i + 1] === '/')) i += 1;
      i += 2;
      continue;
    }

    out += c;
    i += 1;
  }

  return out;
}
