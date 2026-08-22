'use client';

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

import { cn } from '@/lib/design/cn';

/**
 * **Toast** — [TASK-1449](../../../docs/BACKLOG.md), against 📁
 * [Design System v2](../../../docs/design-snapshot/screens/) `toasts` — three
 * worked examples ([D-138](../../../docs/DECISION_REGISTER.md)).
 *
 * > 📁 **Shell rule 11**: ***"Toasts confirm background outcomes only, never
 * > required reading."***
 *
 * ## ⚡ Moved into the library, which is why the row exists
 *
 * ⛔ **It lived at `components/feedback/toast.tsx`** — a shared platform
 * primitive outside the shared library. 📁 [§20c](../../../CLAUDE.md): *"a
 * genuinely new component belongs in `components/ui` with its tokens and its
 * test."*
 *
 * ## 📁 The design's three kinds, and the third is the one usually missed
 *
 * | Kind | Example | Action | Dismissal |
 * |---|---|---|---|
 * | `success` | *"Export ready — 8,412 rows"* | `Download` | auto |
 * | `undo` | *"Close date updated · committed optimistically"* | `Undo` | auto, **and longer** |
 * | `failure` | *"Sync failed for 12 accounts"* | `View` | ⛔ **stays until dismissed** |
 *
 * 🔴 **The third carries its own rule in the design's own copy**: *"8,400
 * synced. **This stays until dismissed**."* ⚡ **Auto-dismissing a failure the
 * person has not read is how a failed action becomes an unexplained one** —
 * and it is the failure that carries the correlation id support needs.
 *
 * ## 🔴 `undo` is a kind rather than a flag, and [TASK-1452](../../../docs/BACKLOG.md) is why
 *
 * ⛔ **The table's inline editing must *"commit on ⏎ optimistically, and
 * surface undo in the toast for 10 seconds"*** — and when that row shipped,
 * **this component had no action and auto-dismissed at 6000ms.** ⚡ So
 * `EditableCell` handed both values back to its caller and **the undo had
 * nowhere to go.** ✅ **It has somewhere now**, and the ten seconds is the
 * design's number rather than a convention.
 */
export type ToastKind = 'success' | 'undo' | 'failure';

/**
 * ⚠️ **The previous vocabulary, kept as an alias rather than rewritten across
 * every caller in this row.** ⛔ **`info` had no design kind and no caller** —
 * measured: every `toast()` call in the product passes `success` or `error`.
 * ⚡ **`error` maps to `failure`**, which is the same thing said in the
 * design's word.
 */
export type ToastTone = 'success' | 'error' | 'info';

export interface ToastAction {
  label: string;
  onAction: () => void;
}

export interface Toast {
  id: string;
  /** ⚡ The design's kind. `tone` is accepted for callers not yet migrated. */
  kind?: ToastKind;
  tone?: ToastTone;
  message: string;
  /** Shown beneath the message. Used for `correlation_id`, so a user can
   * quote something that finds the exact request in the logs. */
  detail?: string;
  /**
   * 📁 **The design gives every kind an action** — `Download`, `Undo`, `View`.
   * ⛔ **Optional, because a toast whose action does nothing is worse than a
   * toast without one** ([§2](../../../CLAUDE.md)).
   */
  action?: ToastAction;
}

/** 📁 *"surface undo in the toast for 10 seconds"* — [TASK-1452](../../../docs/BACKLOG.md). */
export const UNDO_DISMISS_MS = 10_000;

/** ⚡ `error` is the old word for the design's `failure`. */
export function kindOf(input: Pick<Toast, 'kind' | 'tone'>): ToastKind {
  if (input.kind !== undefined) return input.kind;
  return input.tone === 'error' ? 'failure' : 'success';
}

interface ToastContextValue {
  toast: (toast: Omit<Toast, 'id'>) => void;
  dismiss: (id: string) => void;
  toasts: readonly Toast[];
}

const ToastContext = createContext<ToastContextValue | null>(null);

const AUTO_DISMISS_MS = 6000;

const KINDS: Record<ToastKind, string> = {
  // 📁 The design tints the first two `--pos` and the third `--risk`.
  success: 'border-success bg-success-subtle text-success',
  undo: 'border-success bg-success-subtle text-success',
  failure: 'border-danger bg-danger-subtle text-danger',
};

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const dismiss = useCallback((id: string) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  const toast = useCallback(
    (input: Omit<Toast, 'id'>) => {
      const id = crypto.randomUUID();
      setToasts((current) => [...current, { ...input, id }]);

      // 🔴 **The dismissal rule, per kind, and the design states it in copy.**
      // ⛔ **A failure stays until dismissed** — *"This stays until dismissed"*
      // — because auto-dismissing one the person has not read is how a failed
      // action becomes an unexplained one, and it carries the correlation id
      // support needs.
      const kind = kindOf(input);
      if (kind === 'failure') return;
      // ⚡ **Undo gets the design's ten seconds**, which is longer than an
      // ordinary confirmation for the obvious reason: it is the only window in
      // which the person can change their mind.
      setTimeout(() => dismiss(id), kind === 'undo' ? UNDO_DISMISS_MS : AUTO_DISMISS_MS);
    },
    [dismiss],
  );

  const value = useMemo(() => ({ toast, dismiss, toasts }), [toast, dismiss, toasts]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <ToastViewport toasts={toasts} onDismiss={dismiss} />
    </ToastContext.Provider>
  );
}

function ToastViewport({
  toasts,
  onDismiss,
}: {
  toasts: readonly Toast[];
  onDismiss: (id: string) => void;
}) {
  return (
    // aria-live="polite" so a toast is announced without interrupting what
    // the user is currently doing; "assertive" would talk over them.
    <div
      aria-live="polite"
      aria-atomic="false"
      className="pointer-events-none fixed bottom-4 right-4 z-50 flex w-full max-w-sm flex-col gap-2"
    >
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={cn(
            // 🔴 **`rounded-lg` (12px) and `shadow-lg` (`--e3`).** 📁 **§05
            // assigns `12px --r-lg` to *"Card, menu, popover, TOAST, chart
            // container"* and §06 assigns `--e3` to *"Menu, popover, tooltip,
            // TOAST, inline AI answer"*.** ⛔ **This was `rounded` (8px) and
            // `shadow` (`--e2`)** — a step low on both.
            //
            // ⚠️ **§12's prose says dialog, drawer, palette and toast *"share
            // one language: 16px radius … --e4"*, which would make a toast a
            // dialog.** ⛔ **The two SCALES name toast explicitly and disagree
            // with it**, and a scale that lists the element by name is more
            // specific than a sentence grouping four surfaces — 📁 the same
            // reading as [C-1547](../../../docs/LANE_COORDINATION.md).
            'pointer-events-auto flex items-start gap-3 rounded-lg border px-4 py-3 shadow-lg',
            KINDS[kindOf(toast)],
          )}
        >
          <div className="flex-1 text-sm">
            <p className="font-medium">{toast.message}</p>
            {toast.detail ? (
              <p className="mt-0.5 font-mono text-xs opacity-80">{toast.detail}</p>
            ) : null}
          </div>
          {/* 📁 **The design's action** — `Download`, `Undo`, `View`. ⚡ It
              dismisses too: leaving the toast up after the person has acted
              would make them dismiss the same outcome twice. */}
          {toast.action !== undefined ? (
            <button
              type="button"
              onClick={() => {
                toast.action?.onAction();
                onDismiss(toast.id);
              }}
              className="shrink-0 rounded text-sm font-semibold underline underline-offset-4 "
            >
              {toast.action.label}
            </button>
          ) : null}
          <button
            type="button"
            onClick={() => onDismiss(toast.id)}
            aria-label="Dismiss notification"
            className="shrink-0 text-current opacity-60 transition-opacity hover:opacity-100"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  );
}

export function useToast(): ToastContextValue {
  const context = useContext(ToastContext);
  if (!context) throw new Error('useToast must be used within ToastProvider');
  return context;
}
