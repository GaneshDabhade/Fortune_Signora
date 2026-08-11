'use client';

import { useEffect, useState } from 'react';
import { Sparkles } from 'lucide-react';

import { Drawer } from '@/components/ui';
import { cn } from '@/lib/design/cn';
import { useWorkspaceLabel } from '@/lib/shell/workspace-label';

/**
 * **Ask Signora — the assistant entry and its panel** —
 * [TASK-482](../../../docs/BACKLOG.md), 📁 App Shell **§12**.
 *
 * ## 📁 Four doors, one room
 *
 * > ***"Wherever it opens from, the assistant inherits the current scope,
 * > states that scope above the input, and opens as a non-modal 420px drawer
 * > that pushes content. There is no floating bubble: a persistent circle in
 * > the corner is a consumer pattern and it covers data."***
 *
 * ✅ **`Drawer` already existed, tested, with ZERO callers** — ⛔ **so this
 * mounts it rather than building a second overlay.** 📁 The row's own rule:
 * *"the same primitive [TASK-480](../../../docs/BACKLOG.md) needs — one, not
 * two"*, and [D-189](../../../docs/DECISION_REGISTER.md) §3's
 * whichever-lands-first. ⚡ **`Drawer` is already non-modal and already pushes
 * content**, because §14 stated the mechanism rather than the look — **which
 * is why it is the right primitive rather than a dialog with different
 * padding.**
 *
 * ## 🔴 It says it cannot answer, and that is the slice
 *
 * ⛔ **There is no route and no request shape** — both Epic G's — and
 * 📁 **[C-334](../../../docs/LANE_COORDINATION.md) means there is no host
 * credential.** ⚡ **So the panel STATES that**, and the row's Definition of
 * Done is explicit about why: **a panel that renders a hopeful empty state
 * instead of saying so is the false-affordance class this lane has refused
 * three times.**
 *
 * ⚠️ **The refusal is not an error state either.** **Nothing failed** — the
 * capability is not built — and 📁 borrowing
 * [`StatedAbsence`](../feedback/stated-absence.tsx)'s *"reload to try again"*
 * would be a false instruction, exactly as it would be for the attribution
 * strip's absent confidence ([TASK-1411](../../../docs/BACKLOG.md)).
 *
 * ⛔ **And there is no input box.** ⚡ **A text field that accepts a question
 * nothing will answer is worse than no field**: somebody types their real
 * question, loses it, and learns the product is unreliable rather than
 * unfinished. **The scope line and the honest sentence are what ship.**
 *
 * ## ⚠️ Two of the four doors are elsewhere, by design
 *
 * ✅ **This owns the keyboard door and the shell's entry control.** ⛔ **The
 * table-selection door and the explain-this-metric door belong to the surfaces
 * that own those controls** — 📁 `table.tsx`'s AI summary row and
 * [TASK-1411](../../../docs/BACKLOG.md)'s attribution strip — **and building
 * them here would put shell code inside a data table.**
 */

/** 📁 The design's own binding, from §15's shortcut table: *Ask Signora ⌘⇧A*. */
export const ASK_SIGNORA_KEY = { key: 'a', meta: true, shift: true } as const;

export function Copilot({ scope }: { scope?: string }) {
  const [open, setOpen] = useState(false);
  /**
   * 📁 **§19 — *"search, notifications and the assistant all carry the
   * workspace name in their header"*** ([TASK-1463](../../../docs/BACKLOG.md)).
   *
   * ⚡ **The caller's `scope` wins.** 📁 §12 gives the assistant a scope of its
   * own — *"Scoped to EMEA enterprise · Q3 · 2 filters"* — and that is a
   * NARROWER statement than the workspace. ⛔ **Replacing it with the workspace
   * name would widen what the panel claims to be answering within**, which is
   * the direction [`scope.ts`](../../lib/shell/scope.ts) refuses by name.
   */
  const workspaceLabel = useWorkspaceLabel();
  const scopeLine = scope ?? workspaceLabel;

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      // ⚡ **`metaKey || ctrlKey`** — the palette's own rule, so one product
      // does not bind ⌘ on a Mac and something else on Windows.
      if (!(event.metaKey || event.ctrlKey) || !event.shiftKey) return;
      if (event.key.toLowerCase() !== ASK_SIGNORA_KEY.key) return;
      event.preventDefault();
      setOpen((was) => !was);
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  return (
    <>
      {/* ⛔ **Not a floating bubble.** 📁 The design refuses one by name — *"a
          persistent circle in the corner is a consumer pattern and it covers
          data."* ⚡ **This is a control in the flow of the shell's utilities.** */}
      <button
        type="button"
        onClick={() => setOpen(true)}
        aria-haspopup="dialog"
        aria-expanded={open}
        className={cn(
          'inline-flex items-center gap-2 rounded-md px-2 py-1.5 text-sm',
          'text-content-muted transition-colors hover:bg-surface-sunken hover:text-content',
          'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent',
        )}
      >
        <Sparkles aria-hidden className="h-4 w-4 text-ai" />
        Ask Signora
      </button>

      <Drawer
        open={open}
        onClose={() => setOpen(false)}
        title="Ask Signora"
        // 📁 *"states that scope above the input"* — ⛔ **and when there is no
        // scope the line is absent rather than saying *everything*, which
        // would be a claim about what the assistant can see.**
        {...(scopeLine === undefined ? {} : { scope: scopeLine })}
      >
        <div className="flex flex-col gap-3">
          {/**
           * 🔴 **The honest sentence, and it is the row's Definition of Done.**
           *
           * ⚡ **Three parts**: what it cannot do · why · what is true instead.
           * ⛔ **No *"try again"***, because nothing failed — 📁 the same
           * distinction [TASK-1411](../../../docs/BACKLOG.md) drew between an
           * absent confidence and a failed read.
           */}
          <p className="text-sm leading-6 text-content">
            Signora cannot answer questions here yet.
          </p>
          <p className="text-sm leading-6 text-content-muted">
            The reasoning that explains accounts is already running — you can read it on
            any account, under <span className="text-content">In plain language</span>,
            with the evidence behind every sentence. What does not exist yet is a way to
            ask it something new.
          </p>
          <p className="text-sm leading-6 text-content-muted">
            This panel is here so you know where it will be, and so nothing pretends to
            answer in the meantime.
          </p>
        </div>
      </Drawer>
    </>
  );
}
