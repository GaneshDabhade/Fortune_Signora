'use client';

import { X } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

import { cn } from '@/lib/design/cn';
import { useRecordEntry } from '@/lib/query/hooks/preferences';

/**
 * 📁 **Home hierarchy 2 — the workspace confirmation strip.**
 *
 * > **Home**: *"Workspace confirmation strip, if any. **Four seconds after a
 * > resolved entry**, per Entry rule 12. **Absent on the second entry of the
 * > day.**"*
 * >
 * > **Authenticated Entry rule 12**: *"Several memberships, last-used recorded and
 * > healthy. Enter the last used. **The workspace strip confirms which for four
 * > seconds.**"*
 * >
 * > **Entry rule 11**: *"Exactly one membership. Enter it. **No confirmation, no
 * > picker, no interstitial.**"*
 * >
 * > **Entry, motion**: *"Fades in with the shell, holds four seconds, fades out.
 * > **Never slides — it is not an alert.**"* `160 / 4000ms`
 * >
 * > **Entry, reduced motion**: *"All cross-fades become instant swaps. **The
 * > confirmation strip persists until dismissed rather than timing out.**"*
 * >
 * > **`2.4.11`**: *"The confirmation strip… **reduce the scroll area rather than
 * > overlaying it**, so a focused element is never hidden behind sticky chrome."*
 * >
 * > **`3.2.5`**: *"**No entry state auto-navigates after a delay.** The
 * > confirmation strip times out visually but changes nothing."*
 *
 * ## 🔴 One membership means no strip at all
 *
 * ⛔ **Not *a strip that says you have one workspace*.** 📁 Rule 11 is explicit —
 * *"no confirmation, no picker, no interstitial"* — and the design's reasoning is
 * that there is nothing to confirm when there was never a choice.
 *
 * ## ⚡ Why the entry is recorded here and not by the shell
 *
 * 📁 Home is where rule 12 *terminates* — its own reconciliation table says
 * *"rules 11, 12, 19, 20, 21, 24 all terminate here"* — and **the answer to *is
 * this the first entry today* is only available from the write itself.** ⛔ A
 * shell that recorded the entry earlier would make Home's question unanswerable,
 * because `last_entered_at` would already be today.
 *
 * ## ⛔ It times out visually and changes nothing
 *
 * 📁 `3.2.5`. ⚡ **The strip unmounts; no navigation, no refetch, no state
 * anybody else reads.** A four-second timer that did something would be an
 * auto-navigation wearing a courtesy's clothes.
 */
export interface WorkspaceStripProps {
  readonly workspaceId: string | null;
  readonly workspaceName: string | null;
  /** 📁 **Rule 11 vs rule 12.** ⛔ One membership renders nothing. */
  readonly memberships: number;
}

/** 📁 *"Holds four seconds"* — Entry's own duration, `4000ms`. */
const HOLD_MS = 4000;
/** ⚡ **Matches `duration-150` below**, so the unmount waits for the fade. */
const FADE_MS = 150;

/**
 * 🔴 **Whether reduced motion is in effect** — 📁 Entry: *"all cross-fades become
 * instant swaps. **The confirmation strip persists until dismissed rather than
 * timing out.**"*
 *
 * ⚡ **The device's setting, read at runtime.** ⛔ **Not the `reduce_motion`
 * preference**, whose own contract says it is *"the OVERRIDE, not the device's
 * setting"* and that `false` *"leaves the media query in charge"* — so a
 * preference alone would miss every person who set it in their operating system.
 *
 * ⚠️ **The CSS half is already handled** by `motion-reduce:transition-none`
 * below; **this is the half CSS cannot do** — cancelling a timer rather than
 * shortening an animation. 📁 *"Persists until dismissed"* is a behaviour, not a
 * duration.
 */
function useReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false);

  useEffect(() => {
    const media = window.matchMedia('(prefers-reduced-motion: reduce)');
    setReduced(media.matches);
    const listen = (event: MediaQueryListEvent) => setReduced(event.matches);
    media.addEventListener('change', listen);
    return () => media.removeEventListener('change', listen);
  }, []);

  return reduced;
}

export function WorkspaceStrip({ workspaceId, workspaceName, memberships }: WorkspaceStripProps) {
  const record = useRecordEntry(workspaceId);
  const [firstToday, setFirstToday] = useState<boolean | null>(null);
  const [dismissed, setDismissed] = useState(false);

  /**
   * ⚠️ **Fired once per mount, and the ref is what makes that true.** React calls
   * an effect twice in development, and **the second call would answer `false`**
   * — the first one has already recorded today's entry — which would suppress the
   * strip on a genuine first entry.
   *
   * ⛔ **Not guarded by the mutation's own state**, which is not settled yet when
   * the second call would go out.
   */
  const asked = useRef(false);
  const fire = record.mutateAsync;

  useEffect(() => {
    if (workspaceId === null || asked.current) return;
    asked.current = true;
    void fire()
      .then((entry) => setFirstToday(entry.first_entry_today))
      // ⛔ **A failed entry record shows no strip.** ⚡ It is a courtesy, and
      // guessing *"probably your first visit"* is the one thing it must not do.
      .catch(() => setFirstToday(false));
  }, [workspaceId, fire]);

  const present = memberships > 1 && firstToday === true && !dismissed;
  const reduceMotion = useReducedMotion();

  /**
   * 📁 ***"Fades in with the shell, holds four seconds, fades out. Never slides
   * — it is not an alert."*** `160 / 4000ms`.
   *
   * ⚡ **Two phases rather than one timer**: `faded` drives the opacity, and the
   * unmount waits for the transition so the strip is not cut off mid-fade.
   * ⛔ **`duration-150` rather than an arbitrary `160ms`** — the type and radius
   * scales are tokens here and so is the motion scale; 📁 the App Shell already
   * fades at `duration-150`, and a bespoke step would be the same defect
   * `design-tokens.test.tsx` catches for colour.
   */
  const [faded, setFaded] = useState(true);

  useEffect(() => {
    if (!present) return;
    // ⚡ **One frame later**, so the browser has a `0` to transition from.
    const raf = requestAnimationFrame(() => setFaded(false));
    return () => cancelAnimationFrame(raf);
  }, [present]);

  useEffect(() => {
    if (!present || reduceMotion) return;
    const hold = setTimeout(() => setFaded(true), HOLD_MS);
    // ⚡ **Unmounted after the fade**, not with it. 📁 `3.2.5` — *"the strip
    // times out visually but changes nothing"*, so this is the only thing the
    // timeout does.
    const gone = setTimeout(() => setDismissed(true), HOLD_MS + FADE_MS);
    return () => {
      clearTimeout(hold);
      clearTimeout(gone);
    };
  }, [present, reduceMotion]);

  if (!present || workspaceName === null) return null;

  return (
    /**
     * ♿ **`role="status"`** — 📁 4.1.3, *"entry announces once"*, and the greeting
     * already owns that sentence. ⛔ **Not `alert`**: confirming where somebody
     * already is is not an interruption.
     *
     * ⛔ **In flow, never overlaid** — 📁 `2.4.11`: *"reduce the scroll area rather
     * than overlaying it."* ⚡ **And it fades rather than slides**, which the
     * design says by name: *"never slides — it is not an alert."*
     */
    <div
      role="status"
      data-testid="workspace-confirmation"
      className={cn(
        'flex flex-wrap items-center gap-x-3 gap-y-2 rounded-lg border border-border-soft bg-surface px-4 py-2.5 shadow-sm',
        // ⛔ **Opacity only. Never a transform** — 📁 *"never slides."*
        'transition-opacity duration-150 motion-reduce:transition-none',
        faded ? 'opacity-0' : 'opacity-100',
      )}
    >
      {/* 📁 **The customer's word is *organization*** — ADR-0034, and the strip is
          the one place the product names where somebody is. */}
      <p className="text-label leading-[1.5] text-content-muted">
        You are working in <span className="font-semibold text-content">{workspaceName}</span>.
      </p>
      {/* 📁 *"Dismissible, never blocking."* ⛔ **No switcher here** — the App
          Shell owns switching, and Home's non-goals keep it there. */}
      <button
        type="button"
        onClick={() => setDismissed(true)}
        aria-label="Dismiss"
        className="ml-auto grid h-6 w-6 place-items-center rounded-md text-content-subtle transition-colors hover:bg-surface-sunken hover:text-content focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
      >
        <X className="h-3.5 w-3.5" aria-hidden />
      </button>
    </div>
  );
}
