'use client';

import { useId, useRef, type KeyboardEvent, type ReactNode } from 'react';

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
 */

export interface TabItem<T extends string> {
  value: T;
  label: ReactNode;
  /** ⚡ 📁 *"the count is on the tab"* — optional, and absent rather than zero. */
  badge?: ReactNode;
}

export interface TabsProps<T extends string> {
  /** ♿ Required — a `tablist` with no name is unusable by screen reader. */
  label: string;
  items: readonly TabItem<T>[];
  value: T;
  onChange: (value: T) => void;
  className?: string;
}

export function Tabs<T extends string>({
  label,
  items,
  value,
  onChange,
  className,
}: TabsProps<T>) {
  const listId = useId();
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
            id={`${listId}-${item.value}`}
            aria-selected={selected}
            // ⛔ **Roving tabindex.** Without it every tab is a tab stop, and
            // `Tab` walks the strip instead of leaving it — which is the
            // behaviour the arrow keys exist to replace.
            tabIndex={selected ? 0 : -1}
            onClick={() => onChange(item.value)}
            className={cn(
              'rounded-md border px-3 py-1.5 text-sm transition-colors',
              'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2',
              'focus-visible:outline-accent',
              selected
                ? // 📁 §10: sunken fill, ink at 600, brand edge.
                  'border-accent bg-surface-sunken font-semibold text-content'
                : 'border-border text-content-muted hover:text-content',
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
