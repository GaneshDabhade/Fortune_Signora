'use client';

import { usePathname } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';

/**
 * **The route announcement** — [TASK-1444](../../../docs/BACKLOG.md), 📁 App
 * Shell rule **4.1.3**: *"Route changes, sync results and agent state changes
 * announce once, politely."*
 *
 * ## 🔴 A client-side route change is silent by default
 *
 * ⛔ **Nothing in the DOM tells a screen reader the page changed.** ⚡ **A
 * sighted user sees the content replace itself; a screen-reader user hears
 * nothing at all** and has to go looking for whether the link worked.
 *
 * ## ⚡ Once, and politely — both halves are the rule
 *
 * ⛔ **`aria-live="assertive"` would interrupt whatever the person is
 * reading**, which is the opposite of helpful during navigation they
 * initiated. ✅ **`polite` waits for a pause.**
 *
 * ⛔ **And ONCE**: the announcement is skipped on first mount, because **the
 * initial page load is not a route CHANGE** — announcing it would talk over
 * the page a person has only just arrived at.
 *
 * 📁 **The landmark is `output[status]`** — *"polite live region,
 * deduplicated"* — which is why an unchanged path announces nothing.
 */
export function RouteAnnouncer() {
  const pathname = usePathname();
  const [message, setMessage] = useState('');
  const previous = useRef<string | null>(null);

  useEffect(() => {
    // ⛔ **First mount is not a change.** `previous` starts `null` precisely so
    // the arrival itself is silent.
    if (previous.current !== null && previous.current !== pathname) {
      setMessage(pageTitle());
    }
    previous.current = pathname;
  }, [pathname]);

  return (
    <output aria-live="polite" className="sr-only">
      {message}
    </output>
  );
}

/**
 * 🔴 **[B-1077](../../../docs/BUGS.md) — this announced `Navigated to ${pathname}`,
 * and on Home that is a thirty-six character UUID spoken aloud:**
 *
 * ```
 * "Navigated to /w/4e158d14-ab29-4b23-b99d-a8b10986f8e5/home"
 * ```
 *
 * ⛔ **`/w/<uuid>/home` is platform vocabulary** — 📁
 * [ADR-0034](../../../docs/architecture/adr/0034-ubiquitous-language.md), and
 * **the translation is supposed to live at the frontend edge.** ⚠️ **A
 * screen-reader user is the ONLY user who hears this**, so it was the one
 * audience served worst.
 *
 * ## 📁 The design names the replacement, so this is not a choice
 *
 * 📁 **App Shell, the `main` landmark**: *"The content region. Receives focus on
 * route change and **announces the new page title**."*
 *
 * ⛔ **`document.title` cannot answer it** — only the root layout declares one
 * (`'Signora'`), so it is identical on every screen.
 *
 * ✅ **The page's own `h1` IS the page title**, and it is a producer that
 * already exists, is already guarded, and already speaks the customer's words:
 *
 * - 📁 `page-heading-role.test.tsx` **enumerates every route-level `h1` with a
 *   verdict**, so a screen without one is unrepresentable rather than merely
 *   unlisted.
 * - 📁 `vocabulary.test.tsx` **already keeps the platform's words out of it**,
 *   so the announcement inherits ADR-0034 rather than restating it.
 *
 * ⚡ **And it cannot drift.** ⛔ **A route→label map would be a second
 * representation of every screen's name** ([§2](../../../CLAUDE.md)) — **and
 * the rail already holds one in `RAIL_DESTINATIONS`**, so a third would be
 * worse than the defect.
 *
 * ## ⚠️ Silence rather than a guess when there is no heading
 *
 * ⛔ **A page with no `h1` is itself a defect the heading guard catches.**
 * ⚡ **Announcing nothing is honest; announcing a route is not** — so the
 * fallback is silence rather than the string this row exists to remove.
 */
function pageTitle(): string {
  const heading = document.querySelector('main h1')?.textContent?.trim();
  return heading === undefined || heading === '' ? '' : heading;
}
