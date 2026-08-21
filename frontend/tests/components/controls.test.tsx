import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { Avatar, TOOLTIP_DELAY_MS, TabPanel, Tabs, Tooltip, initialsFor } from '@/components/ui';

/**
 * **Tabs, Avatar and Tooltip** — [TASK-1448](../../../docs/BACKLOG.md).
 *
 * ⛔ **All three landed WITH a caller**, which is this row's own rule: 📁 *"a
 * component with no caller is what [TASK-1451](../../../docs/BACKLOG.md)
 * exists to prevent."*
 */

function tabs(onChange = vi.fn(), value: 'open' | 'snoozed' | 'closed' = 'open') {
  render(
    <>
      <Tabs
        label="Queue state"
        idBase="queue"
        value={value}
        onChange={onChange}
        items={[
          { value: 'open', label: 'Needs review', badge: 3 },
          { value: 'snoozed', label: 'Snoozed' },
          { value: 'closed', label: 'Closed' },
        ]}
      />
      <TabPanel idBase="queue" value={value}>
        The {value} queue
      </TabPanel>
    </>,
  );
  return onChange;
}

describe('🔴 Tabs — the half the local implementation was missing', () => {
  it('⛔ arrow keys move between tabs, which `role="tab"` alone only promises', () => {
    /**
     * 🔴 **`signal-queue.tsx` had `role="tab"` and `aria-selected` and nothing
     * else.** ⚡ **A `tablist` without arrow-key navigation announces itself as
     * tabs and behaves like a row of buttons** — a screen-reader user who hears
     * *"tab, 1 of 3"* and presses `→` gets nothing. ⛔ **That is
     * [§2](../../../CLAUDE.md)'s decorative role**, and it is why this
     * migration is not cosmetic.
     */
    const onChange = tabs();
    const list = screen.getByRole('tablist', { name: 'Queue state' });
    within(list).getByRole('tab', { selected: true }).focus();

    // ⚡ Fired on the list, which is where the handler lives.
    list.dispatchEvent(
      Object.assign(new KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true })),
    );
    expect(onChange).toHaveBeenCalledWith('snoozed');
  });

  it('⛔ and it wraps, so the last tab is no harder to reach than the first', () => {
    const onChange = tabs(vi.fn(), 'open');
    const list = screen.getByRole('tablist', { name: 'Queue state' });
    list.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowLeft', bubbles: true }));
    expect(onChange).toHaveBeenCalledWith('closed');
  });

  /**
   * 🔴 **[B-1055](../../../docs/BUGS.md) — the half `aria-selected` hid.**
   *
   * ⛔ **QE measured six `role="tab"` on `/signals`, zero with `aria-controls`,
   * and zero `role="tabpanel"` in the whole document.** ⚡ **The existing
   * coverage above checks arrow keys and the roving index — the parts that were
   * already right** — which is exactly why this survived: ⚠️ **a test that
   * asserts the presence of `role="tab"` cannot see that the role names
   * nothing.**
   *
   * ✅ **So this asserts the ASSOCIATION**, in both directions, by resolving the
   * ids rather than by trusting them to be spelled the same twice.
   */
  it('♿ every tab names the panel it controls, and the panel names it back', () => {
    tabs(vi.fn(), 'snoozed');

    const panel = screen.getByRole('tabpanel');
    const strip = screen.getAllByRole('tab');
    expect(strip).toHaveLength(3);

    // ⛔ **Every tab, not just the selected one** — an unselected tab that
    // controls nothing is the same defect one keypress away.
    for (const tab of strip) {
      expect(tab.getAttribute('aria-controls')).toBe(panel.id);
    }

    // ⚡ **And back**: the panel is labelled by whichever tab is SELECTED, so a
    // screen reader names the panel with the content it is showing.
    const selected = screen.getByRole('tab', { selected: true });
    expect(panel.getAttribute('aria-labelledby')).toBe(selected.id);
    expect(selected).toHaveAccessibleName(/Snoozed/);
  });

  it('♿ a roving tabindex, so Tab leaves the strip rather than walking it', () => {
    // ⛔ Without it every tab is a tab stop, which is the behaviour the arrow
    // keys exist to replace.
    tabs();
    const all = screen.getAllByRole('tab');
    expect(all.filter((t) => t.getAttribute('tabindex') === '0')).toHaveLength(1);
    expect(all.filter((t) => t.getAttribute('tabindex') === '-1')).toHaveLength(2);
  });

  it('✅ a badge renders only when given, never as a zero', () => {
    tabs();
    expect(screen.getByRole('tab', { name: /Needs review/ })).toHaveTextContent('3');
    expect(screen.getByRole('tab', { name: 'Snoozed' })).not.toHaveTextContent('0');
  });
});

describe('📁 Avatar — the only circle in the shell', () => {
  it('⛔ it is a circle, and that is a rule rather than a style', () => {
    // 📁 *"The avatar's uniqueness is what makes it findable without reading —
    // a second circle anywhere in the frame costs that."*
    const { container } = render(<Avatar name="Marta Reinhardt" />);
    expect(container.querySelector('.rounded-full')).not.toBeNull();
  });

  it('⚡ initials come from the ENDS, not the first two letters', () => {
    /**
     * ⛔ *"Vantage Logistics"* must read `VL`. ⚡ **`Va` would make every
     * account beginning with the same word look identical in a list**, which
     * is the one job initials have.
     */
    expect(initialsFor('Vantage Logistics')).toBe('VL');
    expect(initialsFor('Northwind Global Holdings')).toBe('NH');
    expect(initialsFor('Signora')).toBe('SI');
    expect(initialsFor('   ')).toBe('??');
  });

  it('♿ decorative hides it, so a name is not read twice', () => {
    // Announcing "MR" and then "M. Reinhardt" reads the same person twice.
    const { container } = render(<Avatar name="M. Reinhardt" decorative />);
    expect(container.querySelector('[aria-hidden="true"]')).not.toBeNull();
    expect(screen.queryByRole('img')).toBeNull();
  });

  it('♿ and it is named when it stands alone', () => {
    render(<Avatar name="M. Reinhardt" />);
    expect(screen.getByRole('img', { name: 'M. Reinhardt' })).toBeInTheDocument();
  });
});

describe('📁 Tooltip — the 300ms the title attribute cannot hold', () => {
  it('⚡ the delay is the design\'s number, exported rather than inlined', () => {
    // 📁 *"a 300ms tooltip"*. ⛔ A literal buried in a handler is a number
    // nobody can find when the rule changes.
    expect(TOOLTIP_DELAY_MS).toBe(300);
  });

  it('⛔ it does not appear immediately on hover', async () => {
    /**
     * ⚡ **The delay is the point**: a pointer crossing a control must not
     * flash a tooltip. ⛔ **`title` cannot express this** — the browser's
     * delay is its own and varies between engines, which is why this component
     * exists at all.
     */
    vi.useFakeTimers({ shouldAdvanceTime: true });
    render(
      <Tooltip content="Attention">
        <button type="button">Go</button>
      </Tooltip>,
    );
    await userEvent.hover(screen.getByRole('button'));
    expect(screen.queryByRole('tooltip')).toBeNull();

    vi.advanceTimersByTime(TOOLTIP_DELAY_MS);
    expect(await screen.findByRole('tooltip')).toHaveTextContent('Attention');
    vi.useRealTimers();
  });

  it('✅ focus shows it at once, because that is not passing through', async () => {
    render(
      <Tooltip content="Attention">
        <button type="button">Go</button>
      </Tooltip>,
    );
    screen.getByRole('button').focus();
    expect(await screen.findByRole('tooltip')).toBeInTheDocument();
  });

  it('⛔ it DESCRIBES and never names, so it is not the only label', async () => {
    /**
     * 📁 The design puts the accessible name first and the tooltip second, and
     * the order matters: ⛔ **a tooltip that is the only place a label exists
     * is unreachable by touch.** ✅ `aria-describedby`, never
     * `aria-labelledby`.
     */
    const { container } = render(
      <Tooltip content="Attention">
        <button type="button">Go</button>
      </Tooltip>,
    );
    screen.getByRole('button').focus();
    await screen.findByRole('tooltip');

    const wrapper = container.firstElementChild;
    expect(wrapper?.getAttribute('aria-describedby')).toBeTruthy();
    expect(wrapper?.getAttribute('aria-labelledby')).toBeNull();
  });
});
