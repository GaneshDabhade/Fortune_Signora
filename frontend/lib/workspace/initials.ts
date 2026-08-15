/**
 * What an organization is abbreviated to, **in the one place both surfaces
 * read** — [TASK-1421](../../../docs/BACKLOG.md).
 *
 * 📁 **`Fortune Signora Workspace Chooser.dc.html` §03**: *"Both call
 * `selectWorkspace` and both render **the same membership row component**.
 * Only the container, the chrome and the escape behaviour differ."*
 *
 * ⚠️ **The whole row is NOT shared, and that is a measurement rather than a
 * shortcut.** ⛔ **The switcher's row is a `menuitemradio` carrying a
 * position shortcut and a current-selection state; the chooser's is a list
 * item in a 520px column with a group heading.** ⚡ **Sharing them would mean
 * a component with two sets of semantics chosen by a flag**, which is the
 * *"bent to suit one caller"* shape [§20c](../../../CLAUDE.md) refuses.
 *
 * ✅ **What genuinely must not differ is the IDENTITY** — the two letters a
 * person recognises their own organization by. ⛔ **Two implementations of
 * that would eventually disagree**, and a customer would see `NG` in the rail
 * and `NO` on the chooser for one organization. 📁 [§2](../../../CLAUDE.md),
 * *truth has exactly one authoritative representation.*
 */

/**
 * Two letters, derived from the name and never stored.
 *
 * ⛔ **`??` for a name that is entirely whitespace**, which the API's
 * `min_length=1` makes unreachable through the product — **and a crash in a
 * switcher is a worse answer than two question marks.**
 */
export function initialsFor(name: string): string {
  const words = name.trim().split(/\s+/).filter(Boolean);
  const first = words[0];
  if (first === undefined) return '??';
  const last = words[words.length - 1] ?? first;
  if (words.length === 1) return first.slice(0, 2).toUpperCase();
  return `${first.slice(0, 1)}${last.slice(0, 1)}`.toUpperCase();
}
