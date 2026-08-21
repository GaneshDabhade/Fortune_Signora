'use client';

import { useEffect } from 'react';

import { cn } from '@/lib/design/cn';
import {
  COMPOSITION_NAME,
  switchableCompositions,
  type Composition,
  type StatedRole,
} from '@/lib/home/composition';
import { useChangePreferences } from '@/lib/query/hooks/preferences';

/**
 * 📁 **Home's composition switcher** — `Fortune Signora Home.dc.html` §10 and
 * U-02.
 *
 * > 📁 ***"From the composition control in the page header. Two roles only;
 * > single-role people do not see it."*** · Key: **`V`**.
 *
 * ## ⛔ Absent, not disabled, for a single-composition reader
 *
 * 📁 *"single-role people do not see an unnecessary switcher."* ⚡ **A control
 * with one option is a control that does nothing** — [B-255](../../../docs/BUGS.md).
 *
 * ## ⛔ Switching never creates a route
 *
 * 📁 *"switching must preserve the Home route."* ⚡ **It writes a preference**,
 * and the resolver's rule 2 reads it on the next render. **There is no
 * navigation in this file.**
 *
 * ## ⚠️ It persists, and U-02 says that is only half decided
 *
 * 📁 **U-02**: *"Whether a dual-role person switching composition sets that
 * preference permanently or only for the session is undecided."* 📁 **Its own
 * interim ruling**: *"switching persists for the session; the profile preference
 * is the only permanent setting."*
 *
 * 🔴 **This persists to the profile preference, and the deviation is deliberate
 * and reported.** ⛔ **A session-only switch has nowhere to live**: Home holds no
 * client state store, `localStorage` is forbidden for Home state by contract item
 * 8, and inventing a session store for one control would be the speculative
 * mechanism [§6](../../../CLAUDE.md) refuses. ✅ **The behaviour is the design's
 * own permanent option**, it is reversible from the same control, and 📁
 * [C-1530](../../../docs/LANE_COORDINATION.md) asks the product owner to close
 * U-02 either way.
 */
export interface CompositionSwitcherProps {
  readonly current: Composition;
  readonly statedRole: StatedRole | null;
  readonly workspaceId: string | null;
  readonly className?: string;
}

export function CompositionSwitcher({
  current,
  statedRole,
  workspaceId,
  className,
}: CompositionSwitcherProps) {
  const change = useChangePreferences(workspaceId);
  const options = switchableCompositions(statedRole);

  /**
   * 📁 **`V` switches composition** — §10's keyboard table.
   *
   * ⛔ **Never while somebody is typing.** ⚡ A single-letter shortcut that fires
   * inside a field is the shape that makes people distrust every shortcut, so the
   * handler stands down for inputs, textareas and anything `contenteditable`.
   */
  useEffect(() => {
    if (options.length < 2) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== 'v' && event.key !== 'V') return;
      if (event.metaKey || event.ctrlKey || event.altKey) return;
      const target = event.target as HTMLElement | null;
      if (
        target !== null &&
        (target.isContentEditable ||
          ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName))
      ) {
        return;
      }
      const next = options[(options.indexOf(current) + 1) % options.length]!;
      change.mutate({ home_composition: next });
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [options, current, change]);

  // ⛔ **Absent for a single-composition reader.**
  if (options.length < 2) return null;

  return (
    /**
     * ♿ **A real `radiogroup`**, because it is a choice between named views and
     * the design draws it as a segmented control — 📁 the same treatment the App
     * Shell's theme control gets, for the same reason: the options are visible.
     */
    <div
      role="radiogroup"
      aria-label="Home composition"
      className={cn(
        'flex flex-none gap-[3px] rounded-md bg-surface-sunken p-[3px]',
        className,
      )}
    >
      {options.map((option) => {
        const active = option === current;
        return (
          <button
            key={option}
            type="button"
            role="radio"
            aria-checked={active}
            disabled={change.isPending}
            onClick={() => change.mutate({ home_composition: option })}
            className={cn(
              'rounded-sm px-2.5 py-1 text-2xs font-semibold transition-colors',
              'disabled:opacity-50 ',
              active
                ? 'bg-surface text-content shadow-sm'
                : 'text-content-subtle hover:text-content',
            )}
          >
            {COMPOSITION_NAME[option]}
          </button>
        );
      })}
    </div>
  );
}
