'use client';

import { useRef, type ClipboardEvent, type KeyboardEvent } from 'react';

import { cn } from '@/lib/design/cn';

/**
 * **A one-time code, one box per character** —
 * [TASK-1410](../../../docs/BACKLOG.md).
 *
 * ## ⚠️ The row said this already existed. It did not, and the reason is worth keeping
 *
 * 📁 **[TASK-1410](../../../docs/BACKLOG.md) reads: *"the OTP input from
 * TASK-486 — six single-character boxes already went INTO `components/ui`; a
 * second one here is the duplication that rule exists to prevent."***
 * ⛔ **Measured before building: `components/ui` had twenty-nine files and no
 * code input, and the only per-character field in the repository was an
 * onboarding form.**
 *
 * ⚡ **[TASK-486](../../../docs/BACKLOG.md) did not build it, deliberately, and
 * was right**: 📁 `verification.test.tsx` asserts the absence — *"never draws
 * six code boxes, because nothing would verify them… a control whose outcome
 * cannot depend on its input is a false affordance."* **At the time
 * `better-auth/plugins/email-otp` was installed and unregistered.**
 *
 * ✅ **It is registered now** — [`lib/auth/server.ts`](../../lib/auth/server.ts),
 * `emailOTP({ otpLength: 6 })`, closing
 * [C-241](../../../docs/LANE_COORDINATION.md) — **so the refusal's premise has
 * expired and a typed code can be checked.** 📁 **Screen `07` is a shipped
 * row's and is NOT changed here**;
 * [C-264](../../../docs/LANE_COORDINATION.md) asks whether it should now use
 * this, and the component is in the library so that whichever way it is ruled,
 * the second caller takes this one rather than writing another.
 *
 * ## 📁 `length` is a prop and its DEFAULT is the design's
 *
 * ⛔ **Six is not a preference.** 📁 The design says *"Enter the 6-digit
 * code"* and `emailOTP` is configured `otpLength: 6`; **the two already agree
 * and this component must not become a third opinion.** ⚡ **The prop exists
 * because a backup code is a different length**, which the step-up dialog
 * needs — **not so a caller can pick a number.**
 *
 * ## ⛔ Paste fills every box, because that is how a code arrives
 *
 * **Nobody types a code they were sent; they copy it.** ⚡ **A six-box input
 * that accepts a paste into the first box only is worse than one text field**
 * — it looks like it worked and holds one character.
 *
 * ## ♿ One accessible field, not six unlabelled ones
 *
 * ⛔ **Six inputs each announcing *"digit 3 of 6"* is a screen reader reading
 * a form six times.** ⚡ **The group carries the label and the boxes carry
 * their position**, and `autocomplete="one-time-code"` is on the first so the
 * platform's own suggestion lands where a person is looking.
 */

export interface CodeInputProps {
  value: string;
  onChange: (value: string) => void;
  /** 📁 Six by default — the design's number and `emailOTP`'s. */
  length?: number;
  /** What the group is for, e.g. *"Verification code"*. Required: a code field with no name is a box. */
  label: string;
  disabled?: boolean;
  /** Set when the code was wrong. ⛔ **The digits are NOT cleared** — retyping six characters to fix one is the design's named complaint. */
  invalid?: boolean;
  /**
   * 🔴 **The id of the element carrying the reason** — 📁 `Security Center`'s
   * `2.4.7`: *"in the error state the ring is risk-coloured **and the message is
   * programmatically associated**."*
   *
   * ⛔ **`aria-invalid` alone tells a screen-reader user that something is
   * wrong and never what.** ⚡ Both callers already render the sentence
   * adjacently; **nothing connected it to the control**, so the announcement
   * and the field were two facts a reader had to join themselves.
   *
   * ⚠️ **Applied only while `invalid`** — 📁 an `aria-describedby` pointing at
   * an element that is not rendered is a dangling reference, and the callers
   * render the message conditionally.
   */
  errorId?: string;
  className?: string;
}

export function CodeInput({
  value,
  onChange,
  length = 6,
  label,
  disabled = false,
  invalid = false,
  errorId,
  className,
}: CodeInputProps) {
  const boxes = useRef<(HTMLInputElement | null)[]>([]);
  const characters = Array.from({ length }, (_, i) => value[i] ?? '');

  /** ⛔ Digits only, and never longer than the code. */
  const clean = (raw: string): string => raw.replace(/\D/g, '').slice(0, length);

  const focusBox = (index: number): void => {
    boxes.current[Math.max(0, Math.min(index, length - 1))]?.focus();
  };

  const setAt = (index: number, character: string): void => {
    const digits = clean(character);
    if (digits === '') return;
    // ⚡ **Typing into the middle of a filled code overwrites forwards**, which
    // is what somebody correcting one character expects — not an insert that
    // shifts every digit after it.
    const next = characters.slice();
    for (let i = 0; i < digits.length && index + i < length; i += 1) {
      next[index + i] = digits[i] as string;
    }
    onChange(next.join('').slice(0, length));
    focusBox(index + digits.length);
  };

  const onKeyDown = (index: number) => (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Backspace') {
      event.preventDefault();
      const next = characters.slice();
      if (next[index] !== '') {
        // Clear this box and stay: one press, one character.
        next[index] = '';
        onChange(next.join(''));
        return;
      }
      // Already empty — step back and clear that one, so holding backspace
      // walks the code out rather than stalling.
      if (index > 0) {
        next[index - 1] = '';
        onChange(next.join(''));
        focusBox(index - 1);
      }
      return;
    }
    if (event.key === 'ArrowLeft') {
      event.preventDefault();
      focusBox(index - 1);
    }
    if (event.key === 'ArrowRight') {
      event.preventDefault();
      focusBox(index + 1);
    }
  };

  const onPaste = (event: ClipboardEvent<HTMLInputElement>) => {
    // ⛔ **Handled here rather than left to the browser**: a native paste into
    // a `maxLength={1}` box keeps the first character and drops the rest.
    event.preventDefault();
    const digits = clean(event.clipboardData.getData('text'));
    if (digits === '') return;
    onChange(digits);
    focusBox(digits.length);
  };

  return (
    <div
      role="group"
      aria-label={label}
      // ♿ The group carries the error, so a screen reader hears it once rather
      // than once per box.
      aria-invalid={invalid || undefined}
      // 📁 **`2.4.7` — *"the message is programmatically associated."***
      // ⛔ **Only while invalid**: the callers render the sentence
      // conditionally, and a reference to an absent element is worse than none.
      aria-describedby={invalid && errorId !== undefined ? errorId : undefined}
      className={cn('flex gap-2', className)}
    >
      {characters.map((character, index) => (
        <input
          // ⛔ **The index IS the identity here** and that is not the usual
          // caveat: the boxes are a fixed-length positional array, never
          // reordered and never filtered, so position is the stable key. (No
          // eslint-disable: this repository does not configure
          // `react/no-array-index-key`, and a directive naming a rule that
          // does not exist is itself an error.)
          key={index}
          ref={(node) => {
            boxes.current[index] = node;
          }}
          value={character}
          onChange={(event) => setAt(index, event.target.value)}
          onKeyDown={onKeyDown(index)}
          onPaste={onPaste}
          onFocus={(event) => event.target.select()}
          disabled={disabled}
          inputMode="numeric"
          // 📁 Only the first box claims it: the platform fills a code into
          // one field, and six competing claims is how it fills none.
          autoComplete={index === 0 ? 'one-time-code' : 'off'}
          maxLength={1}
          aria-label={`${label}, character ${index + 1} of ${length}`}
          className={cn(
            // 📁 **`Security Center` states the cell three times and agrees with
            // itself**: the `otp()` renderer's literal `width: 38, height: 44,
            // borderRadius: 8`, the hierarchy row *"OtpInput — 6 cells, one
            // field · input 44px"*, and `2.5.8`: *"OTP cells are 38 × 44px."*
            // ⛔ **This was `h-12 w-10` — 48 × 40, taller and narrower than
            // every one of them.** ⚡ **Moving it is the UI Migration Program,
            // not a breach of the freeze**: 📁 [§20c](../../CLAUDE.md) —
            // *"the direction of the change: toward the finalized design is the
            // migration; away from it, to suit one caller, is the defect."*
            //
            // ⚠️ **`rounded-md` is already right and the reason is a trap worth
            // leaving written down**: Tailwind's own `rounded-md` is 6px, but
            // `--radius-md` overrides it to **8px**, which is the design's.
            // ⛔ **Reading the utility name rather than the token would have
            // "fixed" a corner that was never wrong.**
            'h-11 w-[38px] rounded-md border text-center',
            // 📁 *"fontFamily: ui-monospace, fontSize: 17, fontWeight: 600."*
            // ⚡ **Monospace is the substantive half** — a code is read back
            // character by character, and `BackupCodes` already uses it for
            // exactly that. ⚠️ **17px has no token** (`--text-lg` is 18,
            // `--text-base` 16) and one pixel does not justify a scale step
            // that no other role asks for: 📁 the config's own rule, *"only the
            // roles this row adds or corrects."*
            'font-mono text-lg font-semibold',
            'bg-surface text-content transition-colors',
            'disabled:opacity-60',
            // ⛔ **NOT a risk-coloured focus ring, and that is a precedence
            // decision rather than an omission.** 📁 `Security Center` `2.4.7`
            // asks for one; 📁 **§17 Design System `2.4.7` says the indicator is
            // *"2px brand focus ring at 2px offset plus a border change; never
            // suppressed"*** — brand, unconditionally, with **the border**
            // carrying the state. ✅ **The Design System outranks a screen
            // document, `Input` behaves identically, and this already does
            // both halves**: the global `:focus-visible` paints the brand
            // indicator and `border-danger` is the border change.
            invalid ? 'border-danger' : 'border-border-strong',
          )}
        />
      ))}
    </div>
  );
}
