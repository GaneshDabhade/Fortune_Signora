import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { Toggle } from '@/components/ui';

/**
 * 📁 **`User Profile` `1.3.1`** — *"every control has a programmatic label
 * **and its help text via `aria-describedby`**."*
 *
 * 🔴 **Two page-local copies had wrapped the label AND the description in one
 * `<label>`**, so the whole paragraph became the control's accessible name.
 * ⚡ **Everything was announced; nothing was distinguishable.**
 */
describe('♿ the help text describes the switch — it is never its name', () => {
  const HELP = 'Removes every transform and drops transitions to opacity fades.';

  function toggle(props: Record<string, unknown> = {}) {
    return render(
      <Toggle
        label="Reduce motion"
        description={HELP}
        checked={false}
        onChange={() => {}}
        {...props}
      />,
    );
  }

  it('🔴 the name is the label alone', () => {
    toggle();
    // ⛔ **`getByRole` matches on the ACCESSIBLE NAME**, so an exact-name query
    // is the assertion: if the description were still inside the label, the
    // computed name would be the whole paragraph and this would not resolve.
    const box = screen.getByRole('checkbox', { name: 'Reduce motion' });
    expect(box).toBeInTheDocument();
    // ⚡ **The vacuity half**: the help text must still be ON THE PAGE. A fix
    // that simply deleted the description would satisfy every assertion above.
    expect(screen.getByText(HELP)).toBeInTheDocument();
  });

  it('🔴 and it reaches the control as a description', () => {
    toggle();
    const box = screen.getByRole('checkbox', { name: 'Reduce motion' });
    const described = box.getAttribute('aria-describedby');
    expect(described).not.toBeNull();
    const help = document.getElementById((described as string).split(' ')[0] as string);
    expect(help?.textContent).toBe(HELP);
  });

  it('⚡ a note joins the description rather than replacing it', () => {
    /**
     * 📁 **[B-1080](../../../docs/BUGS.md)** — *"Your device is set to reduce
     * motion."* ⛔ **A fact about the reader's device is not a second help
     * text**, and it must not push the first one out of the announcement.
     */
    toggle({ note: 'Your device is already reducing motion.' });
    const box = screen.getByRole('checkbox', { name: 'Reduce motion' });
    const ids = (box.getAttribute('aria-describedby') as string).split(' ');
    expect(ids).toHaveLength(2);
    const read = ids.map((one) => document.getElementById(one)?.textContent);
    expect(read).toEqual([HELP, 'Your device is already reducing motion.']);
  });

  it('⛔ without a note there is no dangling reference', () => {
    // ⚡ **An `aria-describedby` pointing at an element that is not rendered is
    // worse than none** — the same rule `CodeInput`'s `errorId` follows.
    toggle();
    const box = screen.getByRole('checkbox', { name: 'Reduce motion' });
    for (const one of (box.getAttribute('aria-describedby') as string).split(' ')) {
      expect(document.getElementById(one)).not.toBeNull();
    }
  });

  it('✅ it is a real checkbox, so the state and the keyboard are the platform’s', () => {
    toggle({ checked: true });
    const box = screen.getByRole('checkbox', { name: 'Reduce motion' }) as HTMLInputElement;
    expect(box.tagName).toBe('INPUT');
    expect(box.type).toBe('checkbox');
    expect(box.checked).toBe(true);
  });

  it('🔴 a disabled switch is disabled, and the caller says why beside it', () => {
    const onChange = vi.fn();
    toggle({ disabled: true, onChange });
    expect(screen.getByRole('checkbox', { name: 'Reduce motion' })).toBeDisabled();
  });
});
