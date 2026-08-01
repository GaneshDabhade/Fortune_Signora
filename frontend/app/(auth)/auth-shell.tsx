import Link from 'next/link';
import type { ReactNode } from 'react';

/**
 * The frame every authentication screen sits in.
 *
 * **The first screen a customer ever sees, and until now the one screen not
 * built from the design system.** `app/(auth)` reached straight for Tailwind's
 * default palette, which every other surface forbids — because
 * `design-tokens.test.tsx` scanned `components/` and nothing else. A rule with
 * a gap in its enforcement is a rule the code will eventually find the gap in;
 * the check now covers this directory (ADR-0033).
 *
 * Deliberately quiet. Somebody here is not evaluating Signora yet; they are
 * trying to get in, and every element that is not the form is in their way.
 */
export function AuthShell({
  title,
  description,
  children,
  footer,
}: {
  title: string;
  description?: string;
  children: ReactNode;
  footer?: ReactNode;
}) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-surface-sunken p-6">
      <div className="w-full max-w-sm">
        <div className="flex flex-col gap-6 rounded-lg border border-border bg-surface p-8">
          <div className="flex flex-col gap-1">
            <h1 className="text-lg font-semibold text-content">{title}</h1>
            {description ? (
              <p className="text-sm leading-6 text-content-muted">{description}</p>
            ) : null}
          </div>
          {children}
        </div>
        {footer ? (
          <p className="mt-4 text-center text-sm text-content-muted">{footer}</p>
        ) : null}
      </div>
    </main>
  );
}

/** A link between authentication screens, styled once so five pages agree. */
export function AuthLink({ href, children }: { href: string; children: ReactNode }) {
  return (
    <Link
      href={href}
      className="rounded font-medium text-content underline decoration-border underline-offset-4 transition-colors hover:decoration-content-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
    >
      {children}
    </Link>
  );
}
