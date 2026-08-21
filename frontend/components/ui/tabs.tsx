'use client';

import { useRef, type KeyboardEvent, type ReactNode } from 'react';

import { cn } from '@/lib/design/cn';

/**
 * **Tabs** — [TASK-1448](../../../docs/BACKLOG.md), against 📁
 * [Design System v2](../../../docs/design-snapshot/screens/) §10 *Controls*,
 * `tabs` ([D-138](../../../docs/DECISION_REGISTER.md)).
 *
 * ## 🔴 It existed already, in one workflow, which is the reason this row ran
 *
 * ⛔ **`signal-queue.tsx` implemented `role="tab"` locally** — 📁 **the only
 * workflow-local reimplementation [498](../../../docs/architecture/498-common-platform-audit.md)
 * found in the whole audit.** ⚡ **A second one would have been a second answer
 * to *what does a tab look like and how does it behave*, and the two would
 * diverge the first time either was touched.**
 *
 * ## ⚡ The design's grammar, and the half the local one was missing
 *
 * 📁 **§10**: the selected tab carries **`--sunken` fill, `--ink` at weight
 * 600, and a `--brand` edge**; the rest are `--ink-3` at 400 over a
 * `--line-soft` edge. ✅ **An edge and a weight, not colour alone** — the same
 * reason the table's selection rule carries a 2px edge.
 *
 * 🔴 **The local implementation had `role="tab"` and `aria-selected` and
 * nothing else.** ⛔ **A `tablist` without arrow-key navigation is a control
 * that announces itself as tabs and then behaves like a row of buttons** — and
 * a screen-reader user who hears *"tab, 1 of 3"* and presses `→` gets nothing.
 * ✅ **Arrow keys, `Home` and `End` are here**, which is what makes the role
 * true rather than decorative ([§2](../../../CLAUDE.md)).
 *
 * ## 🔴 The other half of the role, added by [B-1055](../../../docs/BUGS.md)
 *
 * ⛔ **A `tab` that names nothing it controls is half a control.** ♿ **WAI-ARIA's
 * tabs pattern is a two-way contract** — the tab points at its panel with
 * `aria-controls`, the panel points back with `aria-labelledby` — ⚡ **and with
 * neither, a screen-reader user is told *"tab, selected"* and given no way to
 * reach what the tab just changed.** 🔴 **Measured on `/signals`: six
 * `role="tab"`, zero `aria-controls`, and zero `role="tabpanel"` in the whole
 * document.**
 *
 * ⚠️ **`aria-selected` alone is what made this look correct**, which is why the
 * guard added with the fix asserts the *association* rather than the role.
 *
 * ⚡ **`idBase` is required rather than generated**, and that is the point:
 * ⛔ **a caller cannot render tabs without deciding what panel they control.**
 * ✅ **The same grammar serves the two tablists that do not use this component**
 * — 📁 `shell/utility-panel.tsx` and 📁 `app/(app)/accounts/view-tabs.tsx` —
 * so there is one answer to *how is a tab linked to its panel*, not three.
 */

export interface TabItem<T extends string> {
  value: T;
  label: ReactNode;
  /** ⚡ 📁 *"the count is on the tab"* — optional, and absent rather than zero. */
  badge?: ReactNode;
}

/**
 * ♿ **The tab's id, which its panel names back.** ⛔ **Derived, never authored
 * at the call site**: two spellings of the same link is how the link rots.
 */
export function tabId(idBase: string, value: string): string {
  return `${idBase}-tab-${value.replace(/\s+/g, '-').toLowerCase()}`;
}

/** ♿ **The panel's id, which every tab in the strip points at.** */
export function tabPanelId(idBase: string): string {
  return `${idBase}-panel`;
}

/**
 * ♿ **The panel half of the contract** — 📁 [B-1055](../../../docs/BUGS.md).
 *
 * ⛔ **No `tabIndex` here.** ⚡ The APG asks for one only when the panel holds
 * nothing focusable; **ours all do**, and adding a stop to each would lengthen
 * the keyboard path QE measured as clean for no gain.
 */
export function TabPanel({
  idBase,
  value,
  className,
  children,
}: {
  idBase: string;
  /** ⚡ **The SELECTED tab** — the panel is labelled by what it is showing. */
  value: string;
  className?: string;
  children: ReactNode;
}) {
  return (
    <div
      role="tabpanel"
      id={tabPanelId(idBase)}
      aria-labelledby={tabId(idBase, value)}
      className={className}
    >
      {children}
    </div>
  );
}

export interface TabsProps<T extends string> {
  /** ♿ Required — a `tablist` with no name is unusable by screen reader. */
  label: string;
  /**
   * ♿ **Required.** ⛔ **The caller must own the id the panel shares**, so that
   * rendering a tab strip without a `TabPanel` is a thing you have to go out of
   * your way to do rather than the default ([B-1055](../../../docs/BUGS.md)).
   */
  idBase: string;
  items: readonly TabItem<T>[];
  value: T;
  onChange: (value: T) => void;
  className?: string;
}

export function Tabs<T extends string>({
  label,
  idBase,
  items,
  value,
  onChange,
  className,
}: TabsProps<T>) {
  const refs = useRef(new Map<T, HTMLButtonElement>());

  /**
   * 📁 **The `tablist` keyboard contract**, which the local implementation had
   * none of. ⛔ **`→ ← Home End` and wrap-around** — a tab strip that stops at
   * its ends makes the last tab harder to reach than the first.
   */
  const onKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    const index = items.findIndex((item) => item.value === value);
    if (index === -1) return;

    let next: number | null = null;
    if (event.key === 'ArrowRight') next = (index + 1) % items.length;
    if (event.key === 'ArrowLeft') next = (index - 1 + items.length) % items.length;
    if (event.key === 'Home') next = 0;
    if (event.key === 'End') next = items.length - 1;
    if (next === null) return;

    event.preventDefault();
    const target = items[next];
    if (target === undefined) return;
    onChange(target.value);
    // ⚡ **Focus follows selection**, which is the automatic-activation pattern
    // the role expects when a panel changes without a further keypress.
    refs.current.get(target.value)?.focus();
  };

  return (
    <div
      role="tablist"
      aria-label={label}
      onKeyDown={onKeyDown}
      className={cn('flex flex-wrap gap-2', className)}
    >
      {items.map((item) => {
        const selected = item.value === value;
        return (
          <button
            key={item.value}
            ref={(node) => {
              if (node) refs.current.set(item.value, node);
              else refs.current.delete(item.value);
            }}
            role="tab"
            type="button"
            id={tabId(idBase, item.value)}
            aria-selected={selected}
            // ♿ **The half that was missing.** Every tab in the strip points at
            // the one panel it swaps; the panel points back at whichever tab is
            // selected ([B-1055](../../../docs/BUGS.md)).
            aria-controls={tabPanelId(idBase)}
            // ⛔ **Roving tabindex.** Without it every tab is a tab stop, and
            // `Tab` walks the strip instead of leaving it — which is the
            // behaviour the arrow keys exist to replace.
            tabIndex={selected ? 0 : -1}
            onClick={() => onChange(item.value)}
            className={cn(
              'rounded-md border px-3 py-1.5 text-sm transition-colors',
              selected
                ? // 📁 §10: sunken fill, ink at 600, brand edge.
                  'border-accent bg-surface-sunken font-semibold text-content'
                : 'border-border-soft text-content-muted hover:text-content',
            )}
          >
            {item.label}
            {item.badge !== undefined ? (
              <span className="ml-2 tabular-nums text-content-subtle">{item.badge}</span>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}
