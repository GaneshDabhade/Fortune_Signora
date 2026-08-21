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
      <legend
        className={cn('text-sm font-medium text-content', legendHidden && 'sr-only')}
      >
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
                // ♿ **`focus-proxy`** — 📁 [B-1058](../../../docs/BUGS.md).
                // ⛔ **The radio is `sr-only`, so the global rule fires on a 1px
                // element nobody can see.** ⚡ **The class moves WHERE the
                // indicator is drawn and not WHAT it is**: one declaration, in
                // `globals.css`, shared with the two other composite controls.
                'focus-proxy',
                //
                // ⚠️ **`has-[:focus-visible]`, not `focus-within`** — 📁 the
                // design draws the selected card with a brand border and tint
                // and **no ring**, and `focus-within` fires on a mouse click,
                // so every card kept a 2px ring after being picked. ⛔ **Found
                // in the screenshot, not by a gate**: the keyboard ring was
                // correct throughout and only the pointer path was wrong.
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

export interface MultiChoiceCardsProps extends Omit<
  ChoiceCardsProps,
  'value' | 'onChange'
> {
  readonly value: readonly string[];
  readonly onChange: (value: readonly string[]) => void;
  /** The design's limit. Reaching it disables the rest rather than hiding it. */
  readonly max: number;
}

/**
 * ⚠️ **`countLabel` was a prop here and is gone.** 📁 The design puts the
 * count in the **action row** — *"`margin-left:auto` · 3 of 3 selected"* —
 * beside the primary button and not under the group. ⛔ **Rendering it in both
 * places would be two representations of one number** ([§2](../../../CLAUDE.md)),
 * and the `role="status"` announcement has to live wherever the visible text
 * does or a screen reader hears a count that is not on screen. **The screen
 * owns it.**
 */

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
      <legend
        className={cn('text-sm font-medium text-content', legendHidden && 'sr-only')}
      >
        {legend}
      </legend>
      {/* 📁 *"flex-direction:column; gap:9px"*. */}
      <div className="flex flex-col gap-[9px]">
        {choices.map((choice) => {
          const inputId = `${groupId}-${choice.value}`;
          const selected = chosen.has(choice.value);
          const blocked = atLimit && !selected;

          return (
            <label
              key={choice.value}
              htmlFor={inputId}
              className={cn(
                // 📁 *"padding:13px 15px; border-radius:12px; gap:12px"*.
                'flex items-start gap-3 rounded-lg border px-[15px] py-[13px] transition-colors',
                selected
                  ? 'border-accent bg-accent-subtle'
                  : 'border-border-soft bg-surface hover:border-border',
                // ⚠️ **The 55% dim belongs to the LIMIT, not to being
                // unselected.** 📁 The mock shows every unpicked row at 0.55
                // because it is drawn at three-of-three — ⛔ **dimming them
                // before the limit is reached would present a live control as
                // a dead one.**
                blocked ? 'cursor-not-allowed opacity-55' : 'cursor-pointer',
              )}
            >
              {/* ♿ Same pattern as the role card: a real checkbox out of
                  sight, the design's box drawn beside it. */}
              <input
                type="checkbox"
                id={inputId}
                name={name}
                value={choice.value}
                checked={selected}
                disabled={blocked}
                onChange={() => toggle(choice.value)}
                className="sr-only"
              />
              <span
                aria-hidden
                className={cn(
                  // 📁 **4px, which is `--r-xs`** — *"Checkbox, tag, inline
                  // code"*. ⚠️ **The mock draws 5px and the Design System's
                  // radius scale has no such step** ([C-1527](../../../docs/LANE_COORDINATION.md)
                  // is the same disagreement one property over).
                  'pointer-events-none mt-0.5 grid h-4 w-4 flex-none place-items-center rounded-xs border-[1.5px] transition-colors',
                  selected ? 'border-accent bg-accent' : 'border-border',
                )}
              >
                {/* 📁 The design's tick, at 9px/700. ⚠️ **The mark carries the
                    state** — *"never colour alone."* */}
                {selected ? (
                  <svg
                    width="9"
                    height="9"
                    viewBox="0 0 16 16"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2.4"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="text-accent-contrast"
                  >
                    <path d="M3.5 8.5l3 3 6-6" />
                  </svg>
                ) : null}
              </span>
              <span className="min-w-0 flex-1">
                <span className="block text-sm font-semibold text-content">
                  {choice.label}
                </span>
                {choice.description ? (
                  <span className="mt-[3px] block text-xs leading-[1.5] text-content-muted">
                    {choice.description}
                  </span>
                ) : null}
              </span>
              {/* 📁 **The design's tag, and it is the reason the dim is not
                  mute.** *"The fourth selection is disabled, not silently
                  ignored"* — ⚡ **`Max 3` on the rows that cannot be picked
                  says why they look different**, right where somebody is
                  clicking. */}
              <span
                className={cn(
                  'flex-none rounded-xs px-2 py-0.5 text-2xs font-semibold',
                  selected
                    ? 'bg-surface text-accent'
                    : 'bg-surface-sunken text-content-subtle',
                )}
              >
                {selected ? 'Selected' : `Max ${max}`}
              </span>
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}
