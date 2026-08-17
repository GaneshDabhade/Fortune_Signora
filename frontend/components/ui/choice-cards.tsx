'use client';

import { useId } from 'react';

import { cn } from '@/lib/design/cn';

export interface Choice {
  readonly value: string;
  readonly label: string;
  /** The design gives every role and goal a supporting line. */
  readonly description?: string;
}

export interface ChoiceCardsProps {
  /** Announced to assistive technology as the group's question. */
  readonly legend: string;
  readonly legendHidden?: boolean;
  readonly choices: readonly Choice[];
  readonly value: string | null;
  readonly onChange: (value: string) => void;
  readonly name: string;
  readonly className?: string;
}

/**
 * **The role grid on screen `05`** — [TASK-469](../../../docs/BACKLOG.md).
 *
 * ⚠️ **This said *"the industries on screen `04`* and the roles on `05`"* and
 * screen 04 no longer uses it** — 📁 the design draws industry as 32px chips,
 * not cards, so `company-form.tsx` renders its own. **Corrected rather than
 * left standing** ([§2](../../../CLAUDE.md)): a component docstring naming a
 * caller it no longer has is the drift that makes the next reader widen a
 * change to protect a consumer that is not there.
 *
 * ### 🔴 Real radios, and the design says so by number
 *
 * *"Choice grids are `radiogroup` or `group` with checkboxes, **not clickable
 * divs**"* (WCAG 1.3.1), and *"Arrow keys move within a choice group, Tab
 * moves between groups… **nothing needs a pointer**"* (2.1.1).
 *
 * ⚡ **A native `<input type="radio">` inside a `<fieldset>` gets all of that
 * without a keyboard handler** — arrow-key roving, the group boundary, form
 * semantics and the announcement. **A div with `role="radio"` would need
 * every one of them written and kept working**, which is the class of code
 * that quietly rots into an unreachable control ([B-312](../../../docs/BUGS.md)
 * is that defect one component over).
 *
 * ### ⛔ Selecting never advances
 *
 * *"Selecting a choice never advances automatically. The user commits with
 * the primary action"* (3.2.2). **So `onChange` reports and nothing here
 * routes.** A grid that advanced would take the decision away from somebody
 * who clicked to read the description.
 *
 * ### ⚠️ The mark carries the state, not the tint
 *
 * *"Never colour alone — the control mark carries it."* The radio is visible
 * and filled; the brand border and tint are on top of that, never instead.
 */
export function ChoiceCards({
  legend,
  legendHidden = false,
  choices,
  value,
  onChange,
  name,
  className,
}: ChoiceCardsProps) {
  const groupId = useId();

  return (
    <fieldset className={cn('flex flex-col gap-2.5', className)}>
      <legend className={cn('text-sm font-medium text-content', legendHidden && 'sr-only')}>
        {legend}
      </legend>
      {/* 📁 *"grid-template-columns:1fr 1fr; gap:10px"*. ⚡ One column below the
          phone width, where two 15px-padded cards cannot both be read. */}
      <div className="grid gap-2.5 phone:grid-cols-2">
        {choices.map((choice) => {
          const inputId = `${groupId}-${choice.value}`;
          const selected = choice.value === value;

          return (
            <label
              key={choice.value}
              htmlFor={inputId}
              className={cn(
                // 📁 *"padding:14px 15px; border-radius:12px"*.
                'cursor-pointer rounded-lg border px-[15px] py-[14px] transition-colors',
                // The focus ring is on the label because the input is the
                // thing focused and the card is the thing seen — 2px at 2px
                // offset, the design's own figure, on cards and fields alike.
                //
                // ⚠️ **`has-[:focus-visible]`, not `focus-within`** — 📁 the
                // design draws the selected card with a brand border and tint
                // and **no ring**, and `focus-within` fires on a mouse click,
                // so every card kept a 2px ring after being picked. ⛔ **Found
                // in the screenshot, not by a gate**: the keyboard ring was
                // correct throughout and only the pointer path was wrong.
                'has-[:focus-visible]:outline-none has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-accent has-[:focus-visible]:ring-offset-2',
                selected
                  ? // ⚡ **The selected card loses its shadow.** 📁 The design
                    // gives `--e1` to the unselected cards and `none` to the
                    // chosen one, so the choice settles into the surface
                    // rather than lifting off it.
                    'border-accent bg-accent-subtle'
                  : 'border-border-soft bg-surface shadow-sm hover:border-border',
              )}
            >
              <span className="flex items-center gap-[9px]">
                {/* ♿ **A real radio, moved out of sight rather than replaced.**
                    ⛔ `sr-only` keeps it focusable, arrow-navigable and
                    announced — 📁 *"choice grids are `radiogroup`… not
                    clickable divs"* — while the design's 16px dot beside it is
                    what a sighted person actually sees. */}
                <input
                  type="radio"
                  id={inputId}
                  name={name}
                  value={choice.value}
                  checked={selected}
                  onChange={() => onChange(choice.value)}
                  className="sr-only"
                />
                <span
                  aria-hidden
                  // ⛔ **Decorative, so it is never a pointer target.** Without
                  // this the dot sits over the `sr-only` input and intercepts
                  // the click — **found by Playwright refusing to `check()` the
                  // radio**, which is the same defect a person would meet as a
                  // card that ignores one particular pixel.
                  className={cn(
                    'pointer-events-none',
                    // 📁 *"width:16px;height:16px;border:1.5px solid"*.
                    'grid h-4 w-4 flex-none place-items-center rounded-full border-[1.5px] transition-colors',
                    selected ? 'border-accent bg-accent' : 'border-border',
                  )}
                >
                  {/* 📁 The 6px inner dot. ⚠️ **The mark carries the state, not
                      the tint** — *"never colour alone."* */}
                  <span
                    className={cn(
                      'h-1.5 w-1.5 rounded-full',
                      selected ? 'bg-accent-contrast' : 'bg-transparent',
                    )}
                  />
                </span>
                {/* ⚠️ **`text-label`, not the mock's literal 13px** — 📁 the
                    Design System's nine type roles have no 13px step, and
                    `Label · 12.5 / 1.45 / 600` is the role this is. **An
                    arbitrary size here would survive a type-scale change
                    unaltered**, which is what `design-tokens.test.tsx` refuses
                    inside `components/ui`. 📁 Raised as [C-1527](../../../docs/LANE_COORDINATION.md).
                    ⚠️ **That guard reads raw source, so it flags the pattern in
                    prose too** — [B-275](../../../docs/BUGS.md). */}
                <span className="text-label text-content">{choice.label}</span>
              </span>
              {choice.description ? (
                // 📁 *"margin-top:6px; padding-left:25px"* — the description
                // aligns under the label, clear of the dot. 📁 `Caption ·
                // 12 / 1.5 / 400` for the same reason as the label above.
                <span className="mt-1.5 block pl-[25px] text-xs leading-[1.45] text-content-muted">
                  {choice.description}
                </span>
              ) : null}
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}

export interface MultiChoiceCardsProps extends Omit<ChoiceCardsProps, 'value' | 'onChange'> {
  readonly value: readonly string[];
  readonly onChange: (value: readonly string[]) => void;
  /** The design's limit. Reaching it disables the rest rather than hiding it. */
  readonly max: number;
  /**
   * The sentence under the group. *"The fourth goal beyond the limit dims to
   * 55% **with the reason stated in the footer count**"* — the dimming alone
   * would be a control that stopped working without saying why.
   */
  readonly countLabel: (selected: number, max: number) => string;
}

/**
 * **The goal grid** — screen `06`, up to three.
 *
 * ### ⛔ The fourth is disabled, never silently dropped
 *
 * *"The fourth selection is disabled, not silently ignored."* ⚡ **Disabled
 * and still visible**, so a person can see what they would have to give up —
 * which is a different experience from a choice that simply stops responding.
 *
 * ⚠️ **Already-selected boxes never disable.** At the limit the remaining
 * three dim and the chosen three stay live, because **deselecting must always
 * work** — a limit that trapped somebody at their first three guesses would
 * be worse than no limit.
 */
export function MultiChoiceCards({
  legend,
  legendHidden = false,
  choices,
  value,
  onChange,
  name,
  max,
  countLabel,
  className,
}: MultiChoiceCardsProps) {
  const groupId = useId();
  const chosen = new Set(value);
  const atLimit = value.length >= max;

  const toggle = (candidate: string) => {
    if (chosen.has(candidate)) {
      onChange(value.filter((v) => v !== candidate));
      return;
    }
    if (atLimit) return;
    // Appended rather than sorted: the design says the goals order the home
    // page, so selection order is information and must survive.
    onChange([...value, candidate]);
  };

  return (
    <fieldset className={cn('flex flex-col gap-2.5', className)}>
      <legend className={cn('text-sm font-medium text-content', legendHidden && 'sr-only')}>
        {legend}
      </legend>
      <div className="flex flex-col gap-2">
        {choices.map((choice) => {
          const inputId = `${groupId}-${choice.value}`;
          const selected = chosen.has(choice.value);
          const blocked = atLimit && !selected;

          return (
            <label
              key={choice.value}
              htmlFor={inputId}
              className={cn(
                'flex items-start gap-3 rounded-md border p-3 transition-colors',
                'focus-within:outline-none focus-within:ring-2 focus-within:ring-accent focus-within:ring-offset-2',
                selected
                  ? 'border-accent bg-accent-subtle'
                  : 'border-border-soft bg-surface hover:border-border',
                blocked ? 'cursor-not-allowed opacity-55' : 'cursor-pointer',
              )}
            >
              <input
                type="checkbox"
                id={inputId}
                name={name}
                value={choice.value}
                checked={selected}
                disabled={blocked}
                onChange={() => toggle(choice.value)}
                className="mt-0.5 h-4 w-4 shrink-0 accent-accent"
              />
              <span className="flex flex-col gap-0.5">
                <span className="text-sm font-medium text-content">{choice.label}</span>
                {choice.description ? (
                  <span className="text-xs leading-5 text-content-muted">{choice.description}</span>
                ) : null}
              </span>
            </label>
          );
        })}
      </div>
      {/* ⚡ **A status, not an alert.** *"Progress changes and autosave
          confirmations are status messages, not alerts — they do not
          interrupt"* (4.1.3). The count changes on every click, and an alert
          would talk over somebody choosing quickly. */}
      <p role="status" className="text-xs text-content-muted">
        {countLabel(value.length, max)}
      </p>
    </fieldset>
  );
}
