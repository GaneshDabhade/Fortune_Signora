'use client';

import { ArrowDown, ArrowUp, Eye, EyeOff } from 'lucide-react';
import { useEffect, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Drawer } from '@/components/ui/drawer';
import { COMPOSITION_NAME, type Composition } from '@/lib/home/composition';
import type { CardContract, HomeCardLayout } from '@/lib/home/cards';

/**
 * 📁 **Home's *Customise* panel** — `Fortune Signora Home.dc.html` §10:
 *
 * > *"**Customise** — opens the card-order panel **as a drawer**. **Escape closes
 * > and returns focus to the trigger.**"* `⌘⇧H`
 * >
 * > **`3.2.3`** — *"**Card order within a composition is stable across visits.**"*
 * >
 * > **`U-05`, interim ruling** — *"**reorder and remove only.** Adding
 * > cross-composition cards is out of scope for the first implementation."*
 *
 * ## ⛔ Move buttons, not drag-and-drop
 *
 * ⚡ **The design says *card-order panel* and does not say how.** ⛔ **Drag is
 * unreachable without a pointer**, and 📁 `2.1.1` is not optional — a
 * keyboard-only reorder would have to be built alongside it anyway, so the
 * accessible mechanism is the only one built. ✅ **It also needs no new
 * dependency**, which [§6](../../../CLAUDE.md) would otherwise require an
 * approval for.
 *
 * ## ⛔ Removed, never absent
 *
 * 📁 `U-05` says *removal*, and 📁 `P-11`'s instinct one state over is that
 * **hidden capability is the most common cause of *"the product does not do X"*
 * when it does.** ⚡ **So a removed card stays in this panel**, greyed with a
 * restore control — the drawer is the one place a person can find it again.
 *
 * ## ⚡ Nothing is saved until *Save*
 *
 * ⛔ **A live-applying panel would reorder the page behind the drawer while
 * somebody was still deciding**, which is the reshuffle-under-the-cursor
 * 📁 `P-05` names. ✅ **Cancel is Escape**, which the `Drawer` already owns.
 */
export interface CustomiseDrawerProps {
  readonly open: boolean;
  readonly onClose: () => void;
  readonly composition: Composition;
  /** The composition's cards, in the order Home is currently drawing them. */
  readonly cards: readonly CardContract[];
  readonly layout: HomeCardLayout | undefined;
  readonly onSave: (layout: HomeCardLayout) => void;
  readonly saving: boolean;
}

export function CustomiseDrawer({
  open,
  onClose,
  composition,
  cards,
  layout,
  onSave,
  saving,
}: CustomiseDrawerProps) {
  /**
   * ⚡ **Seeded from what Home is drawing**, so the panel opens showing the page
   * as it stands rather than the registry's untouched order.
   */
  const [order, setOrder] = useState<string[]>([]);
  const [hidden, setHidden] = useState<string[]>([]);

  useEffect(() => {
    if (!open) return;
    // ⛔ **Re-seeded on every open**, so a cancelled edit is genuinely discarded
    // rather than waiting in state for the next time the drawer is opened.
    const drawn: string[] = cards.map((card) => card.id);
    const removed = (layout?.hidden ?? []).filter((id) => !drawn.includes(id));
    setOrder([...drawn, ...removed]);
    setHidden([...removed]);
  }, [open, cards, layout]);

  const move = (index: number, by: -1 | 1) => {
    setOrder((current) => {
      const next = [...current];
      const target = index + by;
      if (target < 0 || target >= next.length) return current;
      [next[index], next[target]] = [next[target]!, next[index]!];
      return next;
    });
  };

  const toggle = (id: string) => {
    setHidden((current) =>
      current.includes(id) ? current.filter((card) => card !== id) : [...current, id],
    );
  };

  /**
   * ⚡ Names come from the registry, so the panel says what the card says.
   *
   * ⚠️ **Keyed by `string`, not `CardId`.** ⛔ A stored arrangement may name a
   * card the composition no longer has — compositions change as Signora ships —
   * and 📁 a stale id is a stale preference rather than a fault.
   */
  const titles = new Map<string, string>(cards.map((card) => [card.id, card.title]));

  return (
    <Drawer
      open={open}
      onClose={onClose}
      title="Customise your home"
      /* 📁 The `Drawer`'s own `scope` — *"a panel that answers questions must say
         what it was asked about"*, and this one answers within one composition. */
      scope={COMPOSITION_NAME[composition]}
      footer={
        <div className="flex items-center justify-end gap-2">
          <Button variant="secondary" size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button size="sm" loading={saving} onClick={() => onSave({ order, hidden })}>
            Save
          </Button>
        </div>
      }
    >
      <p className="text-xs leading-[1.55] text-content-muted">
        {/* ⛔ **States the scope rather than promising more** — 📁 `U-05`'s
            interim is reorder and remove only, and Home's non-goals rule out
          *"configurable dashboards or a widget marketplace"*. */}
        Reorder these cards or take one away. This changes your home only, in{' '}
        {COMPOSITION_NAME[composition]}.
      </p>

      <ul className="mt-3 flex flex-col gap-1.5">
        {order.map((id, index) => {
          const away = hidden.includes(id);
          return (
            <li
              key={id}
              className="flex items-center gap-2 rounded-lg border border-border-soft bg-surface px-3 py-2"
            >
              <span
                className={
                  away
                    ? 'flex-1 text-xs text-content-subtle line-through'
                    : 'flex-1 text-xs text-content'
                }
              >
                {titles.get(id) ?? id}
              </span>
              {/* ♿ **Every control names the card it acts on**, so a screen
                  reader hears *"Move Recents up"* rather than four *"Move up"*s. */}
              <button
                type="button"
                aria-label={`Move ${titles.get(id) ?? id} up`}
                disabled={index === 0 || away}
                onClick={() => move(index, -1)}
                className="grid h-7 w-7 place-items-center rounded-md text-content-subtle transition-colors hover:bg-surface-sunken hover:text-content disabled:opacity-40 "
              >
                <ArrowUp className="h-3.5 w-3.5" aria-hidden />
              </button>
              <button
                type="button"
                aria-label={`Move ${titles.get(id) ?? id} down`}
                disabled={index === order.length - 1 || away}
                onClick={() => move(index, 1)}
                className="grid h-7 w-7 place-items-center rounded-md text-content-subtle transition-colors hover:bg-surface-sunken hover:text-content disabled:opacity-40 "
              >
                <ArrowDown className="h-3.5 w-3.5" aria-hidden />
              </button>
              {/* ⛔ **A removed card stays here** — the drawer is the only place
                  it can be found again. */}
              <button
                type="button"
                aria-label={`${away ? 'Restore' : 'Remove'} ${titles.get(id) ?? id}`}
                onClick={() => toggle(id)}
                className="grid h-7 w-7 place-items-center rounded-md text-content-subtle transition-colors hover:bg-surface-sunken hover:text-content "
              >
                {away ? (
                  <Eye className="h-3.5 w-3.5" aria-hidden />
                ) : (
                  <EyeOff className="h-3.5 w-3.5" aria-hidden />
                )}
              </button>
            </li>
          );
        })}
      </ul>
    </Drawer>
  );
}
