/**
 * **Two shared components that shipped without their test** —
 * 📁 [§20c](../../../CLAUDE.md): *"A genuinely new component belongs in
 * `components/ui` **with its tokens and its test**."*
 *
 * 🔴 **`PasswordStrength` and `FilterChip` had neither a test nor any file
 * that rendered them**, which is the condition that let
 * [B-1085](../../../docs/BUGS.md) ship on Home. ⚡ **Nothing was wrong in
 * either** — this is the witness, and the design claims strong enough to pin.
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { FilterChip, PasswordStrength, evaluatePassword } from '@/components/ui';

describe('🔴 the password meter REPORTS and never gates', () => {
  it('⛔ it offers no control at all — nothing here can refuse a form', () => {
    /**
     * 📁 **The component's own reviewed position, and the platform's**:
     * *"**Length is the only requirement** — composition rules push people
     * toward `Passw0rd!`, which is less entropy in a longer costume."*
     *
     * ⛔ **So drawing an unmet row and then refusing the form would invent a
     * business rule the product never adopted**, and drawing it as a
     * *requirement* while letting the form through would be the list lying
     * about itself. ⚡ **Enforcement lives in Better Auth's
     * `minPasswordLength`, and this asserts that it did not move here.**
     */
    const { container } = render(<PasswordStrength rules={evaluatePassword('short')} />);

    expect(container.querySelectorAll('button')).toHaveLength(0);
    expect(container.querySelectorAll('input')).toHaveLength(0);
    expect(container.querySelectorAll('[disabled]')).toHaveLength(0);
    // ⚡ **The vacuity half** — it must have rendered the rules, or a component
    // returning nothing satisfies every assertion above.
    expect(screen.getByText('Upper and lower case')).toBeInTheDocument();
  });

  it('♿ it is a meter with a real name, and it counts the rules that EXIST', () => {
    /**
     * ⚠️ **Three segments where the design draws four**, deliberately: it
     * counts the rules that exist rather than a number transcribed from a
     * mock. ⛔ **A fourth empty segment would be the missing breach check drawn
     * as though it were merely unmet.**
     */
    // ⚡ **Twelve characters** — `MINIMUM_PASSWORD_LENGTH`, and the first draft
    // of this test used eleven and read `2`. ⛔ **The rule is the platform's,
    // not a number this test gets to choose.**
    render(<PasswordStrength rules={evaluatePassword('Abcdefghijk1')} />);
    const meter = screen.getByRole('meter', { name: 'Password strength' });

    expect(meter).toHaveAttribute('aria-valuemax', '3');
    expect(meter).toHaveAttribute('aria-valuenow', '3');

    // ⛔ **And it moves** — a meter pinned at its maximum would pass the two
    // assertions above and report nothing.
    const weak = render(<PasswordStrength rules={evaluatePassword('abc')} />);
    expect(
      screen.getAllByRole('meter', { name: 'Password strength' })[1],
    ).toHaveAttribute('aria-valuenow', '0');
    weak.unmount();
  });

  it('⛔ it announces POLITELY, because it changes on every keystroke', () => {
    /**
     * 📁 The component's own reason: *"`role="alert"` would interrupt a
     * screen-reader user mid-word."* ⚡ **This is the same distinction
     * [C-1572](../../../docs/LANE_COORDINATION.md) is open on**, settled here
     * because nothing in this one is contested.
     */
    const { container } = render(<PasswordStrength rules={evaluatePassword('a')} />);
    const list = container.querySelector('ul');

    expect(list).toHaveAttribute('aria-live', 'polite');
    expect(container.querySelector('[role="alert"]')).toBeNull();
  });

  it('♿ every glyph is hidden, because the row beside it already says the same thing', () => {
    // ⚡ `accessibility.spec.ts` counts `main svg:not([aria-hidden])`, so an
    // unhidden tick would be a finding on whatever page rendered this.
    const { container } = render(<PasswordStrength rules={evaluatePassword('Abcdefghijk1')} />);
    const svgs = [...container.querySelectorAll('svg')];

    expect(svgs.length).toBeGreaterThan(0);
    for (const svg of svgs) {
      expect(svg.getAttribute('aria-hidden')).not.toBeNull();
    }
  });
});

describe('📁 a filter chip is one object, named, and says whether it is applied', () => {
  const OPTIONS = [
    { value: 'q', label: 'This quarter' },
    { value: 'y', label: 'This year' },
  ];

  it('♿ its accessible name is the question, not the field it happens to sit on', () => {
    /**
     * ⛔ **Three unlabelled selects on one row are three identical controls to
     * a screen reader**, and *"Sort by"* / *"Then sort by"* are two different
     * questions. ⚡ **`label` overrides `field` for exactly that.**
     */
    render(
      <FilterChip field="Period" label="Then sort by" value="" options={OPTIONS} onChange={() => {}} />,
    );

    expect(screen.getByRole('combobox', { name: 'Then sort by' })).toBeInTheDocument();
    // ⚡ **And it falls back to the field** rather than to nothing.
    render(<FilterChip field="Stage" value="" options={OPTIONS} onChange={() => {}} />);
    expect(screen.getByRole('combobox', { name: 'Stage' })).toBeInTheDocument();
  });

  it('⛔ applied and available do not look the same', () => {
    /**
     * 📁 *"Tinted chip = global and persistent · outlined chip = local and
     * transient"*, and the design's applied arrangement is *"`--sunken`, no
     * border, 600 weight"* — ⚡ **because an APPLIED control and an AVAILABLE
     * one must not read alike.**
     */
    const empty = render(
      <FilterChip field="Period" value="" options={OPTIONS} onChange={() => {}} />,
    );
    const available = empty.container.firstElementChild as HTMLElement;
    expect(available.classList.contains('border')).toBe(true);
    empty.unmount();

    const set = render(
      <FilterChip field="Period" value="q" options={OPTIONS} onChange={() => {}} />,
    );
    const applied = set.container.firstElementChild as HTMLElement;
    expect(applied.classList.contains('bg-surface-sunken')).toBe(true);
    expect(applied.className).not.toContain('border border-border');
  });

  it('✅ choosing the placeholder clears rather than selecting an empty string', async () => {
    // ⛔ **`null` is *no filter*, and `''` would be *a filter whose value is
    // nothing*** — a caller cannot tell those apart from the same value.
    const onChange = vi.fn();
    render(
      <FilterChip field="Period" value="q" options={OPTIONS} onChange={onChange} />,
    );

    await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Period' }), '');
    expect(onChange).toHaveBeenCalledWith(null);
  });
});
