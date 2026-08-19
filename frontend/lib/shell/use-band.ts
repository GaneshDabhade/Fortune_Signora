'use client';

import { useEffect, useState } from 'react';

import { type Band, bandFor } from './rail';

/**
 * **Which of the design's four responsive regimes the viewport is in** —
 * against 📁 `Fortune Signora App Shell.dc.html` **§20**
 * ([D-138](../../../docs/DECISION_REGISTER.md)).
 *
 * > 📁 ***"The shell yields in a fixed order as width disappears: utility panel
 * > first, then the rail's labels, then the rail itself, then the filter strip,
 * > and only then does content reflow."***
 *
 * ## ⚡ One measurement, one answer
 *
 * ⛔ **This is not a licence to branch on width.** 📁 **Anything that can
 * respond through flex, grid, `minmax()` or wrapping must do so** — a component
 * that reads the band to choose a padding has taken a breakpoint where the
 * layout already had one.
 *
 * ✅ **It exists for the one thing CSS cannot express: a STATE TRANSITION.**
 * 📁 The design names two — *"rail becomes a sheet from a top-bar button"* and
 * *"filter strip collapses to one 'Scope' button with a count"* — **and both
 * replace one set of controls with a different one**, which is a different
 * question from how wide anything is.
 *
 * ⚠️ **`laptop` on the server, deliberately.** ⛔ **There is no viewport
 * there**, so the first paint is the reference band and the measurement
 * corrects it — the same shape [`use-rail-collapse.ts`](use-rail-collapse.ts)
 * already uses, for the same reason.
 */
export function useBand(): Band {
  const [band, setBand] = useState<Band>('laptop');

  useEffect(() => {
    const measure = () => setBand(bandFor(window.innerWidth));
    measure();
    window.addEventListener('resize', measure);
    return () => window.removeEventListener('resize', measure);
  }, []);

  return band;
}
