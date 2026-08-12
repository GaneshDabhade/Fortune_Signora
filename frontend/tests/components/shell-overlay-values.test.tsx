/**
 * **§09 and §12 · the numbers reach the markup as numbers** —
 * [TASK-1462](../../../docs/BACKLOG.md).
 *
 * 🔴 **The geometry itself is asserted in a browser** —
 * [`shell-values.spec.ts`](../e2e/shell-values.spec.ts) — **because jsdom
 * cannot compute a width.** ⚡ **What is asserted HERE is the thing a browser
 * cannot show: that the value travels from the contract**, so a later edit
 * back to a Tailwind class fails at the cheapest gate rather than at the
 * slowest one.
 *
 * ⚠️ **Both defects this file guards against looked deliberate.** 📁 The
 * palette read `max-w-xl` — **576px wearing the name *extra large*** — and
 * `pt-[10vh]`, **a round number one digit from the design's.**
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('@/lib/shell/workspace-label', () => ({ useWorkspaceLabel: () => undefined }));

import { CommandPalette } from '@/components/ui/command-palette';
import { Drawer } from '@/components/ui';
import { ASSISTANT_DRAWER_WIDTH, PALETTE } from '@/lib/shell/overlays';

describe('📁 the design’s numbers, in one place', () => {
  it('✅ §09 · 640px, anchored at 14vh', () => {
    expect(PALETTE).toEqual({ width: 640, anchorPercent: 14 });
  });

  it('✅ §12 · the assistant drawer is 420px', () => {
    expect(ASSISTANT_DRAWER_WIDTH).toBe(420);
  });
});

describe('🔴 §09 · the palette reads the contract rather than a class', () => {
  function open() {
    render(
      <CommandPalette
        open
        onClose={() => {}}
        items={[]}
        query=""
        onQueryChange={() => {}}
        onSelect={() => {}}
        placeholder="Search Signora"
      />,
    );
    return screen.getByRole('dialog');
  }

  it('🔴 its maximum width is the design’s number, not `max-w-xl`', () => {
    // ⛔ **`max-w-xl` is 576px.** ⚡ **The class name says nothing about the
    // number, which is why the wrong one survived review.**
    const panel = open();
    expect(panel).toHaveStyle({ maxWidth: '640px' });
    expect(panel.className).not.toContain('max-w-xl');
  });

  it('🔴 it is anchored at 14vh, and the anchor is on the scrim it sits in', () => {
    const anchor = open().parentElement;
    expect(anchor).toHaveStyle({ paddingTop: '14vh' });
    expect(anchor?.className).not.toContain('pt-[10vh]');
  });
});

describe('🔴 §12 · the assistant drawer carries a width at all', () => {
  /**
   * ⚡ **The failure this replaces was not a wrong number — it was NO number.**
   * ⛔ **`copilot.tsx` quoted *"non-modal 420px drawer"* in prose and passed
   * nothing**, and the panel opened at **1265px** in a browser at 1280.
   */
  it('🔴 a drawer given a width applies it', () => {
    render(
      <Drawer open onClose={() => {}} title="Ask Signora" width={ASSISTANT_DRAWER_WIDTH}>
        <p>anything</p>
      </Drawer>,
    );

    expect(screen.getByRole('complementary')).toHaveStyle({ maxWidth: '420px' });
  });

  /**
   * ⛔ **And a drawer given none stays unconstrained**, which is the behaviour
   * a caller inside an already-sized container depends on — ⚡ **the prop is
   * optional on purpose, and this is the assertion that keeps it honest.**
   */
  it('✅ a drawer given none does not invent one', () => {
    render(
      <Drawer open onClose={() => {}} title="Something else">
        <p>anything</p>
      </Drawer>,
    );

    expect(screen.getByRole('complementary').style.maxWidth).toBe('');
  });
});
