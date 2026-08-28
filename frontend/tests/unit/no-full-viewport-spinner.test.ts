import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

/**
 * **📁 `Session Continuity`'s contract, item 3, and it names its own
 * enforcement**:
 *
 * > ***"No code path renders a full-viewport spinner or a blank frame.
 * > **Grep for one before merge.**"***
 *
 * ⚡ **This is the grep, made permanent.** ⛔ **A rule enforced by remembering
 * to grep is enforced until the first person who does not** — 📁
 * [§2](../../../CLAUDE.md): *confidence must come from enforceable behaviour,
 * never from a reassuring comment.*
 *
 * ## ⚠️ Scoped to route-level `loading.tsx`, deliberately
 *
 * ⚡ **In Next.js that file IS the full viewport** — it replaces the whole
 * segment while the route resolves, which is what *full-viewport* means here.
 * ⛔ **NOT a ban on spinners everywhere**: `Button`'s loading state is a 16px
 * spinner inside a control the person just pressed, and the sign-in step list
 * marks the active step the same way. **Those are progress on a painted frame,
 * which is the opposite of what the rule forbids.**
 *
 * ## 🔴 The rule holds today, and that is the point of writing it down
 *
 * ⛔ **All seventeen route loaders already render skeletons.** ⚡ **A guard
 * written while a rule holds is the only kind that can prove it kept
 * holding** — this one exists so the eighteenth route cannot quietly be a
 * spinner.
 */
function loadingFiles(dir: string, found: string[] = []): string[] {
  for (const entry of readdirSync(dir)) {
    const path = join(dir, entry);
    if (statSync(path).isDirectory()) {
      loadingFiles(path, found);
    } else if (entry === 'loading.tsx') {
      found.push(path);
    }
  }
  return found;
}

/** ⛔ **A spinner, or a frame with nothing in it.** */
const FORBIDDEN = [
  'animate-spin',
  'Loader2',
  'Spinner',
  // ⚡ **A full-viewport height on the thing that IS the viewport** — the
  // design's *blank frame*, whatever is or is not inside it.
  'h-screen',
  'min-h-screen',
];

describe('📁 no route loader is a full-viewport spinner or a blank frame', () => {
  const files = loadingFiles('app');

  it('⚡ the sweep finds the loaders it is meant to read', () => {
    /**
     * 🔴 **The vacuity half, and this guard needs it more than most.** ⛔ **A
     * directory walk that returned nothing would report every rule satisfied**
     * — 📁 [`verify-the-instrument-before-the-subject`], and an empty glob is
     * the commonest way a source sweep lies.
     */
    expect(files.length).toBeGreaterThanOrEqual(17);
    expect(files).toContain(join('app', '(app)', 'loading.tsx'));
  });

  for (const file of files) {
    it(`✅ ${file}`, () => {
      const source = readFileSync(file, 'utf8');

      for (const forbidden of FORBIDDEN) {
        expect(source).not.toContain(forbidden);
      }

      /**
       * 📁 **The rule's other half** — *"every skeleton matches its
       * destination footprint."* ⚠️ **The footprint is not checkable from
       * source**, but ⛔ **the absence of ANY loading treatment is**: a loader
       * with neither a spinner nor a skeleton is the *blank frame* the same
       * sentence forbids.
       *
       * ## ⚠️ One exception, and it is the design's rather than a concession
       *
       * 🔴 **The first version of this guard demanded a `Skeleton` and fired
       * on `app/(app)/loading.tsx`, which is CORRECT.** 📁 It is the entry
       * resolver, and 📁 `Authenticated Entry`'s sole-workspace rule is
       * *"enter it. **No confirmation, no picker, no interstitial**"* —
       * ⛔ **a skeleton on the way to a redirect is an interstitial that
       * flashes on every sign-in.**
       *
       * ⚡ **So a segment may render nothing VISIBLE, and then it owes an
       * announcement**: `sr-only` with a live region, so a screen-reader user
       * hears that something is happening instead of silence. **That is a
       * deliberate non-visual loader, not a blank frame** — and requiring the
       * announcement is what keeps the exception from becoming a hole.
       */
      const visible = /Skeleton/.test(source);
      const announcedOnly = /sr-only/.test(source) && /role="status"|aria-live/.test(source);
      expect(visible || announcedOnly).toBe(true);
    });
  }
});
