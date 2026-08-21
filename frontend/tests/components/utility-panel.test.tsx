/**
 * **The utility panel, as a customer meets it** —
 * [TASK-1433](../../../docs/BACKLOG.md).
 *
 * 🔴 **The row's risk decides what is asserted here**: ⚠️ ***"building the
 * chrome because it is the easy half. The chrome is not the deliverable."***
 *
 * ⛔ **So there is no test that a panel slides.** ✅ **These assert the three
 * things that are product rather than furniture**: **a module's content
 * actually arrives in a tab · the panel is ABSENT rather than empty where the
 * design gives it no width · and a tab nobody filled says what belongs there
 * rather than carrying invented copy.**
 */
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { UtilityPanel } from '@/components/shell/utility-panel';
import { PANEL_WIDTH } from '@/lib/shell/utility-panel';

describe("🔴 the panel carries a MODULE's content, and owns none of it", () => {
  it('renders what a module published into the active tab', () => {
    render(
      <UtilityPanel
        state="open"
        width={PANEL_WIDTH.laptop}
        activeTab="Activity"
        onTab={() => {}}
        onOpen={() => {}}
        published={{ Activity: <p>the account&rsquo;s history</p> }}
      />,
    );

    const panel = screen.getByRole('complementary');
    expect(within(panel).getByText("the account’s history")).toBeVisible();
  });

  it("⛔ shows the ACTIVE tab's content and not another tab's", () => {
    // ⚡ A panel that rendered every published node at once would be a stack of
    // three contexts, which is the opposite of a docked one.
    render(
      <UtilityPanel
        state="open"
        width={PANEL_WIDTH.laptop}
        activeTab="Insights"
        onTab={() => {}}
        onOpen={() => {}}
        published={{ Activity: <p>the history</p>, Insights: <p>the health</p> }}
      />,
    );

    expect(screen.getByText('the health')).toBeVisible();
    expect(screen.queryByText('the history')).toBeNull();
  });

  it('⛔ says what a tab is FOR when nothing published into it', () => {
    /**
     * 📁 **The row is explicit**: *"Insights and Notes are tab stubs only if
     * the design's own empty state is used; never invented copy."* ⚡ **And it
     * names the purpose rather than the emptiness**, because the panel is
     * *"docked context"* — somebody who opened it wants to know what would
     * appear, not that nothing has.
     */
    render(
      <UtilityPanel
        state="open"
        width={PANEL_WIDTH.laptop}
        activeTab="Notes"
        onTab={() => {}}
        onOpen={() => {}}
        published={{}}
      />,
    );

    expect(screen.getByText(/no notes to dock/i)).toBeVisible();
  });
});

describe('♿ the landmark, and what a screen reader is told about it', () => {
  it("🔴 is labelled with its ACTIVE TAB, which is the design's own words", () => {
    // 📁 *"`aside[complementary]` — the utility panel, labelled with its active
    // tab."* ⛔ A constant name tells somebody choosing between landmarks
    // nothing about which context they are entering.
    const { rerender } = render(
      <UtilityPanel
        state="open"
        width={PANEL_WIDTH.laptop}
        activeTab="Activity"
        onTab={() => {}}
        onOpen={() => {}}
        published={{}}
      />,
    );
    expect(screen.getByRole('complementary', { name: 'Activity panel' })).toBeVisible();

    rerender(
      <UtilityPanel
        state="open"
        width={PANEL_WIDTH.laptop}
        activeTab="Notes"
        onTab={() => {}}
        onOpen={() => {}}
        published={{}}
      />,
    );
    expect(screen.getByRole('complementary', { name: 'Notes panel' })).toBeVisible();
  });

  it('⛔ renders NOTHING at all where the design gives the panel no width', () => {
    /**
     * 🔴 **Absent, not zero-width, and the difference is the whole assertion.**
     * ⚡ **A zero-width `aside` still offers a screen-reader user a
     * *complementary* region** — and on a phone it would contain nothing, so
     * they would enter it and find themselves nowhere.
     */
    const { container } = render(
      <UtilityPanel
        state="absent"
        width={null}
        activeTab="Activity"
        onTab={() => {}}
        onOpen={() => {}}
        published={{ Activity: <p>the history</p> }}
      />,
    );

    expect(container).toBeEmptyDOMElement();
    expect(screen.queryByRole('complementary')).toBeNull();
  });

  it('⚡ keeps every section NAMED in the 28px rail, where no label can show', () => {
    // ♿ The rail is 28px wide, so the label is one character. A button whose
    // accessible name is "A" is a button called nothing.
    //
    // 🔴 **`getByRole('tab')` here until [B-1055](../../../docs/BUGS.md).** ⛔ **That
    // is not a weakened assertion — it is the SAME assertion against the role
    // the control actually has.** ⚡ **Collapsed there is no panel**, so these
    // are disclosures that open one, and `getByRole('button')` is stricter
    // about what they are rather than looser.
    render(
      <UtilityPanel
        state="tab-rail"
        width={PANEL_WIDTH.smallLaptop}
        activeTab="Activity"
        onTab={() => {}}
        onOpen={() => {}}
        published={{}}
      />,
    );

    for (const tab of ['Insights', 'Activity', 'Notes']) {
      expect(screen.getByRole('button', { name: tab }), tab).toBeVisible();
    }
  });

  /**
   * 🔴 **[B-1055](../../../docs/BUGS.md) — a collapsed region must not publish
   * `role="tab"` for a panel it is not rendering.**
   *
   * ⛔ **QE measured three of them, and `document.querySelectorAll('[role=tabpanel]')`
   * empty.** ⚡ **A screen-reader user was told *"tab, selected"* and given
   * nothing to reach** — and the test below already recorded the missing panel
   * without anyone noticing it was half of a contradiction.
   */
  it('♿ claims no tab role in the rail, because there is no panel to control', () => {
    render(
      <UtilityPanel
        state="tab-rail"
        width={PANEL_WIDTH.smallLaptop}
        activeTab="Activity"
        onTab={() => {}}
        onOpen={() => {}}
        published={{}}
      />,
    );

    expect(screen.queryAllByRole('tab')).toEqual([]);
    expect(screen.queryByRole('tablist')).toBeNull();
    // ♿ **A disclosure, and it says so.**
    expect(screen.getByRole('button', { name: 'Insights' })).toHaveAttribute(
      'aria-expanded',
      'false',
    );
  });

  /**
   * 🔴 **The rail's controls did NOTHING a person could see.**
   *
   * ⛔ **Collapsed, `onTab` changed an invisible selection and no panel
   * appeared** — 📁 the provider's `setActiveTab` does not open the panel, and
   * the panel is the only thing that renders the tab's content. ⚡ **So a click
   * on a 24px icon on a 28px rail had no effect at all**, which is the defect
   * one layer beneath [B-1055](../../../docs/BUGS.md)'s role claim.
   */
  it('⛔ opening a section from the rail opens the panel, not just the selection', async () => {
    const onTab = vi.fn();
    const onOpen = vi.fn();
    render(
      <UtilityPanel
        state="tab-rail"
        width={PANEL_WIDTH.smallLaptop}
        activeTab="Activity"
        onTab={onTab}
        onOpen={onOpen}
        published={{}}
      />,
    );

    await userEvent.click(screen.getByRole('button', { name: 'Notes' }));

    expect(onTab).toHaveBeenCalledWith('Notes');
    expect(onOpen).toHaveBeenCalledTimes(1);
  });

  /**
   * ♿ **The two-way link, asserted by resolving the ids** — 📁
   * [B-1055](../../../docs/BUGS.md). ⛔ **Never by comparing two strings the
   * test itself spells**, which is a test that passes when both are wrong.
   */
  it('♿ open, every tab names the panel and the panel names its tab back', () => {
    render(
      <UtilityPanel
        state="open"
        width={PANEL_WIDTH.smallLaptop}
        activeTab="Notes"
        onTab={() => {}}
        onOpen={() => {}}
        published={{}}
      />,
    );

    const panel = screen.getByRole('tabpanel');
    const strip = screen.getAllByRole('tab');
    expect(strip).toHaveLength(3);
    for (const tab of strip) {
      expect(tab.getAttribute('aria-controls'), tab.textContent ?? '').toBe(panel.id);
    }

    const selected = screen.getByRole('tab', { selected: true });
    expect(panel.getAttribute('aria-labelledby')).toBe(selected.id);

    // ⛔ **Roving tabindex** — QE measured `null` on all three, so `Tab` walked
    // the strip instead of leaving it.
    expect(selected).toHaveAttribute('tabindex', '0');
    for (const tab of strip.filter((node) => node !== selected)) {
      expect(tab).toHaveAttribute('tabindex', '-1');
    }
  });

  /**
   * 🔴 **A roving tabindex without arrow keys is a REGRESSION, not a fix** —
   * the two unselected tabs leave the tab order and nothing brings the keyboard
   * to them. ⚡ **Same `→ ← Home End` grammar as `components/ui/tabs.tsx`**, on
   * purpose.
   */
  it('♿ arrow keys move the rail selection, which the roving index requires', () => {
    const onTab = vi.fn();
    render(
      <UtilityPanel
        state="open"
        width={PANEL_WIDTH.smallLaptop}
        activeTab="Insights"
        onTab={onTab}
        onOpen={() => {}}
        published={{}}
      />,
    );

    const list = screen.getByRole('tablist');
    list.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true }));
    expect(onTab).toHaveBeenCalledWith('Activity');

    list.dispatchEvent(new KeyboardEvent('keydown', { key: 'End', bubbles: true }));
    expect(onTab).toHaveBeenCalledWith('Notes');
  });

  it('⛔ shows no CONTENT in the tab rail, only the way back to it', () => {
    // 📁 *"Closes to a 28px tab rail"* — 28px cannot hold content, and
    // rendering it hidden would leave it in the accessibility tree.
    render(
      <UtilityPanel
        state="tab-rail"
        width={PANEL_WIDTH.smallLaptop}
        activeTab="Activity"
        onTab={() => {}}
        onOpen={() => {}}
        published={{ Activity: <p>the history</p> }}
      />,
    );

    expect(screen.queryByText('the history')).toBeNull();
    expect(screen.queryByRole('tabpanel')).toBeNull();
    // ⚡ **And therefore no tab either** — 📁 [B-1055](../../../docs/BUGS.md).
    // ⛔ **This assertion stood alone for months while three `role="tab"`
    // rendered beside it**, which is what a half-stated contract costs.
    expect(screen.queryAllByRole('tab')).toEqual([]);
  });

  it("📁 takes the design's widths from the constant, never from a literal", () => {
    render(
      <UtilityPanel
        state="open"
        width={PANEL_WIDTH.desktop}
        activeTab="Activity"
        onTab={() => {}}
        onOpen={() => {}}
        published={{}}
      />,
    );

    expect(screen.getByRole('complementary')).toHaveStyle({ width: '360px' });
  });
});
