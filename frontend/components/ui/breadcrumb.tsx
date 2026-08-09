import Link from 'next/link';

import { cn } from '@/lib/design/cn';
import { collapse, isRequired, isWellFormed, type Crumb } from '@/lib/shell/breadcrumb';

/**
 * **The breadcrumb, rendered** — [TASK-1408](../../../docs/BACKLOG.md),
 * shell rule 6, against
 * `docs/design-snapshot/screens/Fortune Signora App Shell.dc.html`.
 *
 * > 📁 **Top-bar slot — *"Truncates from the middle. Never wraps. Always
 * > present below level one."***
 *
 * ## ⛔ The trail is a prop, not something this component derives
 *
 * ⚡ **Deriving a trail from the URL would put routing knowledge in the
 * shell**, and 📁 [D-193](../../../docs/DECISION_REGISTER.md) says modules
 * register capabilities rather than the frame deciding them —
 * [D-194](../../../docs/DECISION_REGISTER.md) already found five modules
 * routing and [TASK-1408](../../../docs/BACKLOG.md) names *"the temptation to
 * put routing in the shell"* as its own risk. **A `/accounts/[id]` segment is
 * an account's NAME, and only the module holding that record knows it.**
 *
 * ## ⚡ `never wraps` is why the collapse happens before layout
 *
 * ⛔ **Truncation is computed from the trail's LENGTH, in
 * [`lib/shell/breadcrumb.ts`](../../lib/shell/breadcrumb.ts), not from
 * available pixels.** **Two people on two screens see the same segments
 * removed** — and it is always the middle, never the parent.
 */
export function Breadcrumb({ trail, className }: { trail: readonly Crumb[]; className?: string }) {
  // 📁 Rule 6 — *"mandatory below the first level"*, and nothing at it.
  if (!isRequired(trail)) return null;

  if (!isWellFormed(trail)) {
    // ⛔ **Loud in development, silent in production.** A malformed trail is a
    // caller's defect, and rendering it would show a link to the page the
    // person is already on — §2's control that does nothing.
    if (process.env.NODE_ENV !== 'production') {
      throw new Error(
        'A breadcrumb trail must end in exactly one `current` segment (shell rule 6).',
      );
    }
    return null;
  }

  const shown = collapse(trail);

  return (
    <nav
      aria-label="Breadcrumb"
      // 📁 *"Never wraps"* — and `min-w-0` is what lets it shrink inside the
      // top bar's flex row rather than pushing the other slots out.
      className={cn('flex min-w-0 items-center gap-1.5 text-sm', className)}
    >
      <ol className="flex min-w-0 items-center gap-1.5">
        {shown.map((crumb, i) => {
          return (
            <li key={`${crumb.label}-${i}`} className="flex min-w-0 items-center gap-1.5">
              {i > 0 ? (
                <span aria-hidden className="text-content-subtle">
                  /
                </span>
              ) : null}
              <Segment crumb={crumb} />
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

// `last` is deliberately absent: the segment branches on `crumb.kind`, and a
// position argument nothing reads is Decorative Logic (§2).
function Segment({ crumb }: { crumb: Crumb }) {
  // 📁 *"Current record carries its dot"* — a status tone, never decoration.
  const dot =
    crumb.tone === undefined ? null : (
      <span
        aria-hidden
        className={cn(
          'mr-1.5 inline-block h-1.5 w-1.5 shrink-0 rounded-full',
          crumb.tone === 'risk' && 'bg-danger',
          crumb.tone === 'warn' && 'bg-warning',
          crumb.tone === 'positive' && 'bg-success',
        )}
      />
    );

  if (crumb.kind === 'current') {
    return (
      <span
        aria-current="page"
        className="flex min-w-0 items-center truncate font-medium text-content"
      >
        {dot}
        <span className="truncate">{crumb.label}</span>
      </span>
    );
  }

  if (crumb.kind === 'menu') {
    // ⚡ **The collapsed segment is a control, not an ellipsis.** ⛔ The hidden
    // levels stay reachable — a trail that silently drops them is a trail
    // that cannot be navigated back up.
    return (
      <button
        type="button"
        aria-label="Show hidden breadcrumb levels"
        className="rounded px-1 text-content-subtle transition-colors hover:text-content focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
      >
        {crumb.label}
      </button>
    );
  }

  const label = (
    <span className={cn('truncate', crumb.kind === 'workspace' && 'font-medium text-content')}>
      {crumb.label}
    </span>
  );

  // ⚠️ **A crumb with no `href` renders as text, not as a dead link.** The
  // cross-workspace root often has none — 📁 *"guest or partner context"* — and
  // a link that goes nowhere is worse than a label.
  return crumb.href === undefined ? (
    <span className="flex min-w-0 items-center text-content-muted">{label}</span>
  ) : (
    <Link
      href={crumb.href}
      className="flex min-w-0 items-center rounded text-content-muted transition-colors hover:text-content focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
    >
      {label}
    </Link>
  );
}
