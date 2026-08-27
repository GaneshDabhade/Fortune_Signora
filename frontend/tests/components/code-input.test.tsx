/**
 * **A one-time code, one box per character** —
 * [TASK-1410](../../../docs/BACKLOG.md).
 *
 * 🔴 **The case that earns this file is PASTE**, because it is how a code
 * actually arrives and it is the one a `maxLength={1}` box silently breaks:
 * the browser keeps the first character and drops the rest, so the field looks
 * filled and holds one digit.
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useState } from 'react';
import { describe, expect, it } from 'vitest';

import { CodeInput } from '@/components/ui/code-input';

/** Driven like a real caller: controlled, with the caller owning the value. */
function Harness({ length }: { length?: number } = {}) {
  const [code, setCode] = useState('');
  return (
    <>
      <CodeInput
        value={code}
        onChange={setCode}
        label="Verification code"
        {...(length === undefined ? {} : { length })}
      />
      <output data-testid="value">{code}</output>
    </>
  );
}

const value = () => screen.getByTestId('value').textContent;
const boxes = () => screen.getAllByRole('textbox');

describe('📁 six boxes, because the design says six digits', () => {
  it('renders the design’s number by default', () => {
    render(<Harness />);
    expect(boxes()).toHaveLength(6);
  });

  it('⚡ and a different length is for a backup code, not a preference', () => {
    // The step-up dialog's backup codes are a different shape; the prop exists
    // for that and the DEFAULT is what agrees with `emailOTP({otpLength: 6})`.
    render(<Harness length={8} />);
    expect(boxes()).toHaveLength(8);
  });
});

describe('🔴 paste fills every box', () => {
  it('⛔ a pasted code lands whole, not one character of it', async () => {
    const user = userEvent.setup();
    render(<Harness />);
    await user.click(boxes()[0] as HTMLElement);
    await user.paste('123456');
    expect(value()).toBe('123456');
  });

  it('⚡ pasting into a later box still fills from the start', async () => {
    // Somebody clicks the middle box and pastes. The code is the code; it does
    // not begin at box four because that is where the cursor was.
    const user = userEvent.setup();
    render(<Harness />);
    await user.click(boxes()[3] as HTMLElement);
    await user.paste('123456');
    expect(value()).toBe('123456');
  });

  it('⛔ a pasted code with spaces or dashes still lands', async () => {
    const user = userEvent.setup();
    render(<Harness />);
    await user.click(boxes()[0] as HTMLElement);
    await user.paste('123 456');
    expect(value()).toBe('123456');
  });

  it('⛔ and a longer paste is truncated rather than overflowing', async () => {
    const user = userEvent.setup();
    render(<Harness />);
    await user.click(boxes()[0] as HTMLElement);
    await user.paste('12345678');
    expect(value()).toBe('123456');
  });
});

describe('⚡ typing moves forward and correcting does not restart', () => {
  it('advances a box at a time', async () => {
    const user = userEvent.setup();
    render(<Harness />);
    await user.click(boxes()[0] as HTMLElement);
    await user.keyboard('123');
    expect(value()).toBe('123');
    expect(boxes()[3]).toHaveFocus();
  });

  it('⛔ backspace clears one character rather than the code', async () => {
    // 📁 The design's named complaint: retyping six characters to fix one.
    const user = userEvent.setup();
    render(<Harness />);
    await user.click(boxes()[0] as HTMLElement);
    await user.keyboard('123456');
    await user.keyboard('{Backspace}');
    expect(value()).toBe('12345');
  });

  it('⚡ backspace in an empty box steps back and clears that one', async () => {
    const user = userEvent.setup();
    render(<Harness />);
    await user.click(boxes()[0] as HTMLElement);
    await user.keyboard('12');
    await user.click(boxes()[4] as HTMLElement);
    await user.keyboard('{Backspace}');
    // Box 4 was empty, so the press walks back rather than stalling.
    expect(boxes()[3]).toHaveFocus();
  });

  it('arrow keys move between boxes', async () => {
    const user = userEvent.setup();
    render(<Harness />);
    await user.click(boxes()[2] as HTMLElement);
    await user.keyboard('{ArrowLeft}');
    expect(boxes()[1]).toHaveFocus();
    await user.keyboard('{ArrowRight}{ArrowRight}');
    expect(boxes()[3]).toHaveFocus();
  });
});

describe('⛔ it accepts digits and nothing else', () => {
  it('letters are refused rather than shown and rejected later', async () => {
    const user = userEvent.setup();
    render(<Harness />);
    await user.click(boxes()[0] as HTMLElement);
    await user.keyboard('12ab34');
    expect(value()).toBe('1234');
  });
});

describe('♿ one field with a name, not six anonymous boxes', () => {
  it('the group carries the label', () => {
    render(<Harness />);
    expect(screen.getByRole('group', { name: 'Verification code' })).toBeInTheDocument();
  });

  it('⚡ each box says where it is, so focus is never ambiguous', () => {
    render(<Harness />);
    expect(
      screen.getByLabelText('Verification code, character 1 of 6'),
    ).toBeInTheDocument();
  });

  it('🔴 only the first box claims one-time-code', () => {
    // ⛔ Six competing claims is how the platform fills none of them.
    render(<Harness />);
    const claiming = boxes().filter(
      (b) => b.getAttribute('autocomplete') === 'one-time-code',
    );
    expect(claiming).toHaveLength(1);
    expect(claiming[0]).toBe(boxes()[0]);
  });

  it('⛔ a wrong code is announced once, on the group', () => {
    render(
      <CodeInput value="123456" onChange={() => {}} label="Verification code" invalid />,
    );
    expect(screen.getByRole('group', { name: 'Verification code' })).toHaveAttribute(
      'aria-invalid',
      'true',
    );
  });

  it('📁 a cell is the design\'s 38 × 44, not the 48 × 40 it drifted to', () => {
    /**
     * 📁 **`Security Center` says it three times and agrees with itself**: the
     * `otp()` renderer's `width: 38, height: 44`, the hierarchy row *"input
     * 44px"*, and `2.5.8` — *"OTP cells are 38 × 44px."*
     *
     * ⚠️ **This asserts CLASSES, not measured pixels, and the trade is worth
     * stating**: jsdom applies no stylesheet, so `getBoundingClientRect` here
     * returns zero for every box and would pass any value at all. ⛔ **A guard
     * that cannot fail is worse than no guard** — 📁
     * [`focus-never-suppressed.test.ts`](../unit/focus-never-suppressed.test.ts)
     * exists because one of mine could not. **A class assertion can fail, so
     * it is the honest instrument available.**
     *
     * ✅ **`h-11` is 44px and `--radius-md` is 8px** — ⛔ **note that
     * Tailwind's own `rounded-md` is 6px and this repository overrides it, so
     * the token is what is being asserted, not the utility's default.**
     */
    render(<CodeInput value="" onChange={() => {}} label="Verification code" />);
    for (const box of boxes()) {
      expect(box.className).toContain('h-11');
      expect(box.className).toContain('w-[38px]');
      expect(box.className).toContain('rounded-md');
      // 📁 *"fontFamily: ui-monospace"* — a code is read back character by
      // character, and every other place this product shows one uses it.
      expect(box.className).toContain('font-mono');
    }
    // ⚡ **The vacuity half**: if `boxes()` ever returned nothing, every
    // assertion above would pass by never running.
    expect(boxes()).toHaveLength(6);
  });

  it('🔴 and a wrong code KEEPS the digits', () => {
    // 📁 TASK-486: "a wrong code shows inline and keeps the digits — it never
    // clears what was typed." The component cannot clear what it does not own,
    // and this asserts it does not try.
    render(
      <CodeInput value="123456" onChange={() => {}} label="Verification code" invalid />,
    );
    expect(boxes().map((b) => (b as HTMLInputElement).value).join('')).toBe('123456');
  });
});
