'use client';

import { useId } from 'react';

import { cn } from '@/lib/design/cn';

export interface Segment {
  readonly value: string;
  readonly label: string;
  /** The design gives each theme a supporting line. Optional, because the
   * time-format control has none. */
  readonly description?: string;
}

export interface SegmentedControlProps {
  readonly legend: string;
  readonly legendHidden?: boolean;
  readonly segments: readonly Segment[];
  readonly value: string;
  readonly onChange: (value: string) => void;
  readonly name: string;
  readonly className?: string;
}

/**
 * **A segmented control** — [TASK-470](../../../docs/BACKLOG.md), the design's
 * *24-hour · 12-hour* and *Light · Dark · System*.
 *
 * ### 🔴 Radios, for the reason the choice grids are radios
 *
 * The design's accessibility criteria for this product are explicit that a
 * choice group is *"`radiogroup` or `group` with checkboxes, **not clickable
 * divs**"* and that *"arrow keys move within a choice group… **nothing needs a
 * pointer**"*.
 *
 * ⚡ **A native `<input type="radio">` in a `<fieldset>` gets roving arrow-key
 * movement, the group boundary and the announcement for free.** ⛔ **A row of
 * `<button>`s — which is what a segmented control usually is — gets none of
 * them**, and each would have to be written and kept working. **The visual is
 * a segmented control; the semantics are a radio group**, and only the first
 * of those is a styling decision.
 *
 * ### ⚠️ The selected segment is not carried by colour alone
 *
 * `aria-checked` comes from the input, and the label draws a border and a
 * weight change as well as a tint — *"never colour alone"*.
 */
export function SegmentedControl({
  legend,
  legendHidden = false,
  segments,
  value,
  onChange,
  name,
  className,
}: SegmentedControlProps) {
  const groupId = useId();
  const describes = segments.some((segment) => segment.description !== undefined);

  return (
    <fieldset className={cn('flex flex-col gap-2', className)}>
      <legend
        className={cn('text-sm font-medium text-content', legendHidden && 'sr-only')}
      >
        {legend}
      </legend>
      <div
        className={cn(
          'flex gap-1 rounded-md bg-surface-sunken p-1',
          // With descriptions the segments stack; without, they sit in a row —
          // the design draws both and they are the same control.
          describes ? 'flex-col' : 'flex-row',
        )}
      >
        {segments.map((segment) => {
          const inputId = `${groupId}-${segment.value}`;
          const selected = segment.value === value;

          return (
            <label
              key={segment.value}
              htmlFor={inputId}
              className={cn(
                'flex flex-1 cursor-pointer items-start gap-2 rounded px-3 py-2 text-sm transition-colors',
                // ♿ **The radio inside is `sr-only`** — 📁
                // [B-1058](../../../docs/BUGS.md), and see `choice-cards.tsx`.
                'focus-proxy',
                selected
                  ? 'border border-accent bg-surface font-semibold text-content shadow-sm'
                  : 'border border-transparent text-content-muted hover:text-content',
              )}
            >
              <input
                type="radio"
                id={inputId}
                name={name}
                value={segment.value}
                checked={selected}
                onChange={() => onChange(segment.value)}
                className={cn(
                  'mt-0.5 h-3.5 w-3.5 shrink-0 accent-accent',
                  !describes && 'sr-only',
                )}
              />
              <span className="flex flex-col gap-0.5">
                <span>{segment.label}</span>
                {segment.description ? (
                  <span className="text-xs font-normal leading-5 text-content-muted">
                    {segment.description}
                  </span>
                ) : null}
              </span>
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}
