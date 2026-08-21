'use client';

import { useEffect, useRef } from 'react';

import { HM_COPY_04 } from '@/lib/home/copy';
import { useAcknowledgeSetupComplete, usePreferences } from '@/lib/query/hooks/preferences';

/**
 * 📁 **Home's state 04 — `state.activated`.**
 *
 * > Entry: *"All blocking cards complete."*
 * > Renders: *"Composition switches to SELLER, OPERATIONS or EXECUTIVE on the
 * > next render. **A one-time strip states that setup is finished and what
 * > changed.**"*
 * >
 * > **`AC-H03`** — *"Complete the last blocking card: the next render is the role
 * > composition, with the setup-complete strip shown **exactly once**."*
 *
 * ### 🔴 *Once* is recorded on render, not on dismiss
 *
 * ⛔ **There is no dismiss control**, and adding one would change the promise
 * from *"shown once"* to *"shown until dismissed"* — ⚡ **somebody who read it
 * and navigated away would meet it again tomorrow**, which is the behaviour the
 * word *one-time* exists to rule out.
 *
 * ✅ **So the acknowledgement fires on first paint**, and the server holds it:
 * 📁 the same rule activation's skip follows — *"nothing about activation lives
 * in `localStorage`"* — and a browser-held flag would show the strip again on
 * every new device.
 *
 * ### ⚠️ It renders on the ROLE composition, which is the point
 *
 * 📁 State 04 is not an activation state: *"composition switches to SELLER,
 * OPERATIONS or EXECUTIVE."* ⛔ **A strip drawn on the activation composition
 * would announce completion beside the steps it just completed.** ✅ The strip
 * belongs to the first data composition a person sees.
 *
 * ### ⛔ It never says setup is complete when it is not
 *
 * `complete` is the caller's, derived from the workspace's own connections. ⚡
 * **This component asserts nothing about activation** — it renders a sentence
 * and records that it did.
 */
export interface SetupCompleteStripProps {
  readonly workspaceId: string | null;
  /** 📁 *"All blocking cards complete."* ⛔ `false` while unresolved. */
  readonly complete: boolean;
  /** ⛔ **`true` on the activation composition**, where the strip must not show. */
  readonly activation: boolean;
}

export function SetupCompleteStrip({
  workspaceId,
  complete,
  activation,
}: SetupCompleteStripProps) {
  const preferences = usePreferences(workspaceId);
  const acknowledge = useAcknowledgeSetupComplete(workspaceId);

  const seen = preferences.data?.setup_complete_seen;
  const show = !activation && complete && seen === false;

  /**
   * ⚠️ **Guarded against a second write within one mount.** React may call an
   * effect twice in development, and the mutation is not idempotent from the
   * client's side — ⛔ **the server is** (*"the first moment wins"*), so a
   * duplicate costs a request rather than a wrong answer. **The ref removes the
   * request.**
   */
  const recorded = useRef(false);

  // ⛔ **`acknowledge` is deliberately outside the dependency list.** It is a new
  // object on every render, so depending on it would re-run this effect forever.
  // ✅ **The ref is what makes that safe** rather than the list.
  const fire = acknowledge.mutate;
  useEffect(() => {
    if (!show || recorded.current) return;
    recorded.current = true;
    fire();
  }, [show, fire]);

  // ⛔ **Silent until the preference is known.** ⚡ Rendering while unread would
  // show the strip to somebody who was told last week, on every slow connection.
  if (!show) return null;

  return (
    /**
     * ♿ **`role="status"`** — 📁 4.1.3: *"entry announces once."* The greeting
     * already owns the assertive queue, and this is a fact rather than an
     * interruption.
     */
    <div
      role="status"
      className="flex flex-wrap items-center gap-x-3 gap-y-2 rounded-lg border border-success-line bg-success-subtle px-4 py-3"
      data-testid="setup-complete"
    >
      <span
        aria-hidden
        /* 📁 The design's completed mark — *"`markBg: var(--pos)`, `markFg:
           the design's white"*. ⛔ **`text-accent-contrast` rather than a new token**: the
           design's hero states *"0 new components or tokens"*, and
           `shell/activation.tsx:230` already pairs exactly this filled-success
           chip with that foreground. */
        className="grid h-5 w-5 flex-none place-items-center rounded-sm border border-success bg-success text-xs font-bold text-accent-contrast"
      >
        ✓
      </span>
      {/* 📁 `HM-COPY-04`, verbatim: *"Setup is complete. Home now shows your
          accounts, deals and signals."* ⛔ **It states what CHANGED**, which is
          the design's own requirement for this strip. */}
      <p className="text-label leading-[1.5] text-content">{HM_COPY_04}</p>
    </div>
  );
}
