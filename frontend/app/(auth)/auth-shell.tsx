import Link from 'next/link';
import type { ReactNode } from 'react';

import { AuthModeIndicator } from '@/components/ui/auth-mode-indicator';

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
  /**
   * The product mark above the card.
   *
   * ⚡ **Off for Welcome, and only for Welcome.** The design puts the brand
   * *inside* that one card — a 36px badge over a 22px heading — because
   * Welcome **is** the branding moment. Rendering the shell's small mark above
   * it as well would print *Fortune Signora* twice on the first screen an
   * enterprise buyer sees.
   */
  mark = true,
  /** Rendered inside the card **above** the heading — Welcome's brand block. */
  masthead,
}: {
  title: string;
  description?: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
  region?: ReactNode;
  mark?: boolean;
  masthead?: ReactNode;
}) {
  return (
    <main
      className={[
        // Mobile: the card is the page, so the page carries no padding of its
        // own beyond the 20px gutters the design names.
        'flex min-h-screen flex-col bg-surface-sunken px-5 py-8',
        // Tablet: top-aligned at 96px rather than centred.
        'phone:items-center phone:px-6 phone:pt-24',
        // Desktop: centred, with a 64px floor.
        'smalllaptop:justify-center smalllaptop:py-16',
      ].join(' ')}
    >
      {/* ⚡ **`max-w-card`, not an arbitrary 400px** — TASK-491 gap ⑦, and
          [D-162](../../../docs/DECISION_REGISTER.md) ④ named this exact line.
          **The measurement is the Design System's**, so the screen consumes it
          rather than restating it. */}
      <div className="flex w-full flex-col phone:max-w-card">
        {/* The product mark, above the card. `Fortune Signora` is the combined
            brand and this is a branding surface — the sign-in page is named in
            §4's list, so the full mark is correct here and `Signora` alone is
            correct once the application is open.

            ⚡ **It is a link, and that is what gives Welcome a door.** The
            design's hierarchy puts Welcome at the root; ours cannot be, because
            `/` is the shell's entry resolver and a signed-in person's way in. **A
            product mark that goes home is how every real product behaves**, so
            the entrance is the ordinary one rather than a back-link invented to
            satisfy `reachability`. */}
        {mark ? (
          <Link
            href="/welcome"
            className="mb-6 flex items-center justify-center gap-2 rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2"
          >
            <span
              aria-hidden
              className="flex h-8 w-8 items-center justify-center rounded-md bg-accent text-xs font-semibold text-accent-contrast"
            >
              FS
            </span>
            <span className="text-sm font-semibold text-content">Fortune Signora</span>
          </Link>
        ) : null}

        <div
          className={[
            'flex flex-col gap-6 bg-surface',
            // Mobile drops the frame entirely rather than shrinking it.
            'rounded-none border-0 p-0 shadow-none',
            'phone:rounded-xl phone:border phone:border-border phone:p-8 phone:shadow',
          ].join(' ')}
        >
          {masthead}
          <div className="flex flex-col gap-1">
            {/* ⚡ **20px/700, which is `--text-xl` exactly** — every card
                heading in the design is `font-size:20px;font-weight:700`
                (Welcome's is 22px, and **the Design System's scale has no
                22px**). It was `text-lg`/600. [D-163](../../../docs/DECISION_REGISTER.md):
                *"do not introduce workflow-specific visual overrides where the
                Design System should define the behavior"* — so the token is
                used and an arbitrary 22px size is not written.

                ⚠️ **The first draft of this comment quoted the arbitrary class
                it was refusing to use, and `design-tokens.test.tsx` failed on
                it.** The check reads source text, so it cannot tell a class
                from prose about a class — **and that is the correct trade**:
                the alternative is a checker that parses JSX to permit a
                sentence nobody needed to write. */}
            <h1 className="text-xl font-bold tracking-tight text-content">{title}</h1>
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

        {/* **The authentication mode, where the question is actually asked** —
            [TASK-473](../../../docs/BACKLOG.md).

            ⚡ **Mounted HERE and not in the application shell**, for two
            reasons that both point the same way. 📁 **The failure the row
            names happens at sign-in**: *"a reviewer walking the first hour
            cannot tell whether they signed in as a seeded demo account or
            created one."* ⛔ **And `components/shell/app-shell.tsx` is 🔴,
            which this row's budget does not grant** — it grants *"a new
            observable on the auth configuration"*, and this is the auth
            surface.

            ⚠️ **`AuthShell` is a server component and so is the indicator**,
            which is what keeps `SIGNORA_ENVIRONMENT` on the server. A client
            component would have needed it published as `NEXT_PUBLIC_`.

            ⛔ **The PLACEMENT is deliberately the least opinionated one
            available** — below the region line, in a slot that already exists
            for ambient text. 📁 **[D-129](../../../docs/DECISION_REGISTER.md)
            and the row: *"how the mode is displayed… the treatment is the
            approved design's, and [410](../../../docs/architecture/410-approved-ui-specification.md)
            is the authority. This row delivers the fact and refuses to invent
            the presentation."* ✅ **410 may move it; nothing about
            `authMode()` moves with it.** */}
        <div className="mt-4 flex justify-center">
          <AuthModeIndicator />
        </div>
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
