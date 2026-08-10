'use client';

import { useEffect, useId, useMemo, useRef, useState } from 'react';

import { cn } from '@/lib/design/cn';

export interface CommandItem {
  id: string;
  label: string;
  /** The group this item belongs to. Items are rendered in the order given,
   * grouped by first appearance — the palette never sorts, because the
   * caller's order is the caller's ranking. */
  group: string;
  /** A short right-aligned note: a record's type, a shortcut, a count. */
  meta?: string;
  glyph?: string;
}

export interface CommandPaletteProps {
  open: boolean;
  onClose: () => void;
  items: CommandItem[];
  /** ⌘K opened it to *"Search or ask…"* (§07), so the caller owns the query
   * and the filtering — the palette does not decide what matches. */
  query: string;
  onQueryChange: (query: string) => void;
  /** `panel` is ⌘↵ — §12's *"open in panel"*, the second destination the
   * design gives every result. A caller with nowhere to put a panel simply
   * treats both the same. */
  onSelect: (item: CommandItem, where: 'here' | 'panel') => void;
  placeholder?: string;
  /**
   * 🔴 **What the caller's search is DOING** — [TASK-481](../../../docs/BACKLOG.md).
   *
   * ⛔ **Before this prop the palette had one branch for an empty list and it
   * read *"Nothing matches"*** — so a search **still in flight**, a search that
   * **failed**, and a query **nobody has typed** all rendered as *no results*.
   *
   * 🔴 **[P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md): *a failed read must
   * never render as an empty result.*** ⚡ **On a search surface that is the
   * most expensive version of the confusion**: *"nothing matches"* is a
   * **statement about the customer's data**, and a person who reads it about a
   * request that never completed concludes the record is gone.
   * 📁 **[C-226](../../../docs/LANE_COORDINATION.md) found that exact mistake
   * six times on one screen.**
   *
   * ⚠️ **Defaults to `ready`**, so every existing caller keeps its behaviour
   * and this is additive rather than a breaking change to a frozen component
   * ([§20c](../../../CLAUDE.md)).
   */
  status?: SearchStatus;
}

/**
 * ⚡ **Four states, because they are four different sentences.**
 *
 * ⛔ **Not a boolean and not `isLoading | isError`.** A pair of booleans has a
 * fourth combination that means nothing — *loading and failed at once* — and
 * the first caller to set both decides what it renders. **A union has exactly
 * the states that exist.**
 */
export type SearchStatus = 'idle' | 'loading' | 'ready' | 'error';

/**
 * The fastest path to anything, and the second of §12's four overlays that
 * did not exist.
 *
 * **Design System v2 §12**: *"the palette is the fastest path to anything and
 * now answers questions directly"*, with the key map stated in the design
 * itself — *"↑↓ navigate ↵ open ⌘↵ open in panel"* and `esc` to leave.
 *
 * ### The keyboard map is the component, not an affordance on it
 *
 * ⚡ **Those four keys are the whole reason a palette is faster than a menu.**
 * They are implemented here rather than described: the footer hint and the
 * handler read from **one table**, so a hint promising a key nothing binds is
 * not expressible. **A legend that can drift from the behaviour it documents
 * is worse than no legend** — it is read as a contract.
 *
 * ### Why the caller filters
 *
 * ⛔ **This component does not match, rank or sort.** *"Answers questions
 * directly"* means a result set can come from a query engine rather than from
 * substring matching, and a palette that filtered locally would quietly
 * discard whatever the caller had already ranked. **It renders what it is
 * given, in the order it is given**, and groups by first appearance.
 */
export function CommandPalette({
  open,
  onClose,
  items,
  query,
  onQueryChange,
  onSelect,
  placeholder = 'Search or ask…',
  status = 'ready',
}: CommandPaletteProps) {
  const listId = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  const [active, setActive] = useState(0);

  /** Groups, in order of first appearance. §12 renders a labelled group per
   * kind; the order is the caller's and is never re-sorted here. */
  const groups = useMemo(() => {
    const order: string[] = [];
    const byGroup = new Map<string, CommandItem[]>();
    for (const item of items) {
      const existing = byGroup.get(item.group);
      if (existing) {
        existing.push(item);
      } else {
        order.push(item.group);
        byGroup.set(item.group, [item]);
      }
    }
    return order.map((label) => ({ label, items: byGroup.get(label) as CommandItem[] }));
  }, [items]);

  // The active index must stay inside a result set that changes on every
  // keystroke. Clamping on render rather than in the change handler keeps it
  // correct when `items` changes for a reason other than typing.
  const index = items.length === 0 ? -1 : Math.min(active, items.length - 1);

  useEffect(() => {
    if (open) {
      setActive(0);
      inputRef.current?.focus();
    }
  }, [open]);

  if (!open) return null;

  const move = (delta: number) => {
    if (items.length === 0) return;
    // Wraps, because a palette with six results should reach the last one by
    // pressing Up once rather than Down five times.
    setActive((current) => (current + delta + items.length) % items.length);
  };

  const handleKeyDown = (event: React.KeyboardEvent) => {
    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        move(1);
        return;
      case 'ArrowUp':
        event.preventDefault();
        move(-1);
        return;
      case 'Escape':
        event.preventDefault();
        onClose();
        return;
      case 'Enter': {
        const item = items[index];
        if (!item) return;
        event.preventDefault();
        // ⌘↵ / Ctrl+↵ is §12's "open in panel". Both modifiers, because the
        // design names one key and the product runs on two platforms.
        onSelect(item, event.metaKey || event.ctrlKey ? 'panel' : 'here');
        return;
      }
      default:
    }
  };

  return (
    // The scrim §12 specifies — 24% ink, and explicitly no blur.
    <div
      className="fixed inset-0 z-50 flex items-start justify-center bg-backdrop/25 p-4 pt-[10vh]"
      onClick={(event) => {
        if (event.currentTarget === event.target) onClose();
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={placeholder}
        // §12's shared plane, the same three terms as Drawer and Dialog.
        className={cn(
          'flex w-full max-w-xl flex-col overflow-hidden rounded-xl border border-border',
          'bg-surface text-content shadow-lg',
        )}
      >
        <input
          ref={inputRef}
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          aria-label={placeholder}
          aria-controls={listId}
          aria-activedescendant={index >= 0 ? `${listId}-${index}` : undefined}
          className={cn(
            'w-full border-b border-border bg-transparent px-4 py-3 text-sm',
            'text-content placeholder:text-content-subtle focus:outline-none',
          )}
        />

        <div id={listId} role="listbox" aria-label="Results" className="max-h-80 overflow-y-auto">
          {items.length === 0 ? (
            <PaletteState status={status} query={query} />
          ) : (
            groups.map((group) => (
              <div key={group.label}>
                <p className="px-4 pb-1 pt-3 text-2xs font-semibold uppercase tracking-wide text-content-subtle">
                  {group.label}
                </p>
                {group.items.map((item) => {
                  const position = items.indexOf(item);
                  const isActive = position === index;
                  return (
                    <div
                      key={item.id}
                      id={`${listId}-${position}`}
                      role="option"
                      aria-selected={isActive}
                      onMouseEnter={() => setActive(position)}
                      onClick={(event) =>
                        onSelect(item, event.metaKey || event.ctrlKey ? 'panel' : 'here')
                      }
                      className={cn(
                        'flex cursor-pointer items-center gap-3 px-4 py-2 text-sm',
                        isActive ? 'bg-accent-subtle text-content' : 'text-content-muted',
                      )}
                    >
                      {item.glyph ? <span aria-hidden>{item.glyph}</span> : null}
                      <span className="flex-1 truncate">{item.label}</span>
                      {item.meta ? (
                        <span className="text-xs text-content-subtle">{item.meta}</span>
                      ) : null}
                    </div>
                  );
                })}
              </div>
            ))
          )}
        </div>

        <footer className="flex gap-4 border-t border-border px-4 py-2 text-2xs text-content-subtle">
          {KEY_MAP.map((key) => (
            <span key={key.hint}>{key.hint}</span>
          ))}
        </footer>
      </div>
    </div>
  );
}

/**
 * §12's legend, and the source the handler above is written against.
 *
 * ⚡ **Exported so a test can bind the two together.** The failure this
 * prevents is the cheap one: a footer that promises `⌘↵ open in panel` after
 * somebody removes the modifier branch, leaving a legend that documents a
 * behaviour the component no longer has.
 */
export const KEY_MAP = [
  { key: 'ArrowUp/ArrowDown', hint: '↑↓ navigate' },
  { key: 'Enter', hint: '↵ open' },
  { key: 'Meta+Enter', hint: '⌘↵ open in panel' },
  { key: 'Escape', hint: 'esc close' },
] as const;

/**
 * **The four states an empty result list can be in** —
 * [TASK-481](../../../docs/BACKLOG.md).
 *
 * ⛔ **Four sentences, because they are four different facts about the world.**
 * ⚡ **The one that matters most is `error`**: 🔴 *"nothing matches"* is a
 * **statement about the customer's data**, and rendering it for a request that
 * never completed tells somebody their record is gone.
 * 📁 [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md), and
 * [C-226](../../../docs/LANE_COORDINATION.md) found the same confusion six
 * times on one screen.
 *
 * ⚠️ **`idle` is not silence.** A palette that opens to a blank box looks
 * broken for the half-second before anybody types, and 📁 the design's
 * placeholder — *"Search or ask…"* — is a prompt rather than an answer.
 */
function PaletteState({ status, query }: { status: SearchStatus; query: string }) {
  const line = 'px-4 py-6 text-center text-sm text-content-muted';

  if (status === 'error') {
    return (
      // ⚡ **Says what is still true, then what to do** — the same three-part
      // sentence `StatedAbsence` established, at the scale a palette can carry.
      <p role="alert" className={line}>
        Signora could not search just now. Nothing has changed — try again in a moment.
      </p>
    );
  }

  if (status === 'loading') {
    // ⛔ **Announced politely rather than assertively**: a search that resolves
    // in 200ms would otherwise interrupt a screen reader mid-word on every
    // keystroke.
    return (
      <p aria-live="polite" className={line}>
        Searching…
      </p>
    );
  }

  if (status === 'idle' || query === '') {
    // ⚡ **A query nobody has typed has no result to report.** Saying *nothing
    // matches ""* is answering a question that was not asked.
    return <p className={line}>Type to search accounts, people and settings.</p>;
  }

  return <p className={line}>Nothing matches “{query}”.</p>;
}
