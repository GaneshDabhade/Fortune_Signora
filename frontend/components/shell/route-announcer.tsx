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
      setMessage(`Navigated to ${pathname}`);
    }
    previous.current = pathname;
  }, [pathname]);

  return (
    <output aria-live="polite" className="sr-only">
      {message}
    </output>
  );
}
