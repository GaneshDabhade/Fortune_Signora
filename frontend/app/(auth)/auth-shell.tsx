import Link from 'next/link';
import type { ReactNode } from 'react';

/**
 * The one card every authentication screen sits in.
 *
 * **TASK-467 · Workflow 1**, against
 * `docs/design-snapshot/screens/Fortune Signora Authentication.dc.html`.
 *
 * ### One card, every state — and that is the design's own first rationale
 *
 * *"A single 400px card carries all 24 screens. Users learn the surface once,
 * and engineering builds one layout with a content slot instead of
 * twenty-four pages."* ⚡ **So this file is the layout and the screens are
 * content**, which is why it is worth rebuilding rather than extending: the
 * previous shell was a card that each page decorated differently.
 *
 * ### ⛔ Rebuilt from the design, not refined from what was here
 *
 * **[D-154](../../../docs/DECISION_REGISTER.md) forbids the other framing in
 * terms** — *"do not begin from the legacy implementation and iterate toward
 * the design"* — and [D-158](../../../docs/DECISION_REGISTER.md) says replace
 * the customer-visible experience wherever it differs. **It differed in every
 * measurement**: 384px not 400, `--radius-lg` not `--radius-xl`, no elevation,
 * no product mark, no legal or region line, and one responsive behaviour where
 * the design specifies three.
 *
 * ### The three breakpoints are three behaviours, not one that shrinks
 *
 * | | |
 * |---|---|
 * | **≥ 1024px** | Centred, **64px floor so it never sits under the fold** |
 * | **640–1023px** | **Top-aligned at 96px** — a tablet keyboard in portrait would otherwise push the primary action off screen |
 * | **< 640px** | ⚡ **The card becomes the page**: no border, no radius, no shadow, 20px gutters. *"Dropped rather than shrunk, which is what keeps it from looking like a website on a phone."* |
 *
 * ⛔ **Better Auth is untouched.** This is layout; it renders whatever the
 * screen inside it submits, and the Python tier still only verifies RS256
 * ([§13](../../../CLAUDE.md), [D-156](../../../docs/DECISION_REGISTER.md)).
 */
export function AuthShell({
  title,
  description,
  children,
  footer,
  /**
   * Printed under the card beside the region. **Enterprise buyers read this**
   * — the design's *"security details in plain sight"*: *"hiding them reads as
   * evasion."*
   */
  region,
}: {
  title: string;
  description?: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
  region?: ReactNode;
}) {
  return (
    <main
      className={[
        // Mobile: the card is the page, so the page carries no padding of its
        // own beyond the 20px gutters the design names.
        'flex min-h-screen flex-col bg-surface-sunken px-5 py-8',
        // Tablet: top-aligned at 96px rather than centred.
        'sm:items-center sm:px-6 sm:pt-24',
        // Desktop: centred, with a 64px floor.
        'lg:justify-center lg:py-16',
      ].join(' ')}
    >
      <div className="flex w-full flex-col sm:max-w-[400px]">
        {/* The product mark, above the card. `Fortune Signora` is the combined
            brand and this is a branding surface — the sign-in page is named in
            §4's list, so the full mark is correct here and `Signora` alone is
            correct once the application is open. */}
        <div className="mb-6 flex items-center justify-center gap-2">
          <span
            aria-hidden
            className="flex h-8 w-8 items-center justify-center rounded-md bg-accent text-xs font-semibold text-accent-contrast"
          >
            FS
          </span>
          <span className="text-sm font-semibold text-content">Fortune Signora</span>
        </div>

        <div
          className={[
            'flex flex-col gap-6 bg-surface',
            // Mobile drops the frame entirely rather than shrinking it.
            'rounded-none border-0 p-0 shadow-none',
            'sm:rounded-xl sm:border sm:border-border sm:p-8 sm:shadow',
          ].join(' ')}
        >
          <div className="flex flex-col gap-1">
            <h1 className="text-lg font-semibold text-content">{title}</h1>
            {description ? (
              <div className="text-sm leading-6 text-content-muted">{description}</div>
            ) : null}
          </div>
          {children}
        </div>

        {footer ? (
          <div className="mt-4 text-center text-sm text-content-muted">{footer}</div>
        ) : null}
        {region ? (
          <p className="mt-6 text-center text-xs text-content-subtle">{region}</p>
        ) : null}
      </div>
    </main>
  );
}


/**
 * A link inside the card.
 *
 * ⚡ **Kept, and kept deliberately.** [D-154](../../../docs/DECISION_REGISTER.md)
 * ② names *"accessibility implementations that already conform"* among the
 * things existing code keeps authority for, and this one does: it carries the
 * design's **2px brand focus ring at 2px offset** (its `2.4.7` criterion) and
 * underlines rather than relying on colour alone.
 */
export function AuthLink({ href, children }: { href: string; children: ReactNode }) {
  return (
    <Link
      href={href}
      className="rounded font-medium text-content underline decoration-border underline-offset-4 transition-colors hover:decoration-content-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2"
    >
      {children}
    </Link>
  );
}
