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
import { describe, expect, it } from 'vitest';

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
        published={{ Activity: <p>the history</p> }}
      />,
    );

    expect(container).toBeEmptyDOMElement();
    expect(screen.queryByRole('complementary')).toBeNull();
  });

  it('⚡ keeps every tab NAMED in the 28px rail, where no label can show', () => {
    // ♿ The rail is 28px wide, so the label is one character. A button whose
    // accessible name is "A" is a button called nothing.
    render(
      <UtilityPanel
        state="tab-rail"
        width={PANEL_WIDTH.smallLaptop}
        activeTab="Activity"
        onTab={() => {}}
        published={{}}
      />,
    );

    for (const tab of ['Insights', 'Activity', 'Notes']) {
      expect(screen.getByRole('tab', { name: tab }), tab).toBeVisible();
    }
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
        published={{ Activity: <p>the history</p> }}
      />,
    );

    expect(screen.queryByText('the history')).toBeNull();
    expect(screen.queryByRole('tabpanel')).toBeNull();
  });

  it("📁 takes the design's widths from the constant, never from a literal", () => {
    render(
      <UtilityPanel
        state="open"
        width={PANEL_WIDTH.desktop}
        activeTab="Activity"
        onTab={() => {}}
        published={{}}
      />,
    );

    expect(screen.getByRole('complementary')).toHaveStyle({ width: '360px' });
  });
});
