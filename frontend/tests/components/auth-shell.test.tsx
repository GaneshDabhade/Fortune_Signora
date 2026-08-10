/**
 * **The authentication shell's frame** — [TASK-483](../../../docs/BACKLOG.md).
 *
 * ### ⚠️ This row was satisfied before it was claimed, and that is why it exists
 *
 * **The row's own premise concedes it**: *"the premise this row was written on
 * was wrong… `app/(auth)/auth-shell.tsx` exists."* **Every element it
 * enumerates was already delivered** by [TASK-467](../../../docs/BACKLOG.md)
 * milestone 1 and [TASK-491](../../../docs/BACKLOG.md), and is on `main`.
 *
 * ⛔ **So this file is the row's deliverable.** **A requirement that is met by
 * accident today is a requirement nothing protects tomorrow** — and the shell
 * is the one component every authentication screen composes, so a regression
 * in it is a regression in all of them at once. **`workflow1-login.spec.ts`
 * asserts the rendered geometry against a running browser; this asserts the
 * *composition*, which jsdom can see and which runs on every commit.**
 *
 * ⚡ **The design's own reason for the shell is why the frame is worth
 * guarding**: *"A single 400px card carries all 24 screens. Users learn the
 * surface once, and engineering builds one layout with a content slot instead
 * of twenty-four pages."*
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { AuthShell } from '@/app/(auth)/auth-shell';

/**
 * The card — the element carrying the frame.
 *
 * ⚠️ **Two elements, not one, and the first draft of this file conflated
 * them.** The **width** sits on an outer wrapper and the **radius, border and
 * elevation** on the card inside it, because the mark has to sit *above* the
 * card and *within* the same 400px column. **Found by the assertion failing,
 * which is the test doing its job before it ever guarded anything.**
 */
function card(): HTMLElement {
  const heading = screen.getByRole('heading', { level: 1 });
  const found = heading.parentElement?.parentElement;
  if (!found) throw new Error('the shell rendered no card around its heading');
  return found;
}

/** The 400px column: the card and the mark above it share it. */
function frame(): HTMLElement {
  const found = card().parentElement;
  if (!found) throw new Error('the shell rendered no width frame');
  return found;
}

/**
 * ⚠️ **What the assertions in this block DO and DO NOT prove** —
 * [B-175](../../../docs/BUGS.md).
 *
 * ⛔ **They check that a class string is applied. They do not check that any
 * CSS is emitted for it**, and on the commit that broke every authentication
 * screen they all passed: `theme.screens` had stopped defining `sm:` and
 * `lg:`, the utilities compiled to nothing, and the strings were still in the
 * attribute.
 *
 * 🔴 **So this block is the CALLER'S INTENT, and it is labelled as that.**
 * ✅ **The behaviour is asserted where it can be** —
 * [`tests/e2e/auth-layout.spec.ts`](../e2e/auth-layout.spec.ts) **compares the
 * computed radius, padding and justification across the design's bands in a
 * real browser**, and 📁 **removing a band turns it red**, which is the check
 * B-175 asked for.
 *
 * ⚡ **Both are kept deliberately.** ⛔ **A missing class is cheap to catch
 * here**; **a class that emits nothing can only be caught there.**
 */
describe('the one card every authentication screen sits in', () => {
  it('carries the design width as a token, never as an arbitrary value', () => {
    // ⚡ **`max-w-card`, not `max-w-[400px]`.** The override was TASK-491 gap
    // ⑦ and its removal is what closed the loop: a gap named in the audit,
    // closed in the foundation, and the screen simplified rather than patched.
    render(<AuthShell title="Sign in">{null}</AuthShell>);

    expect(frame().className).toContain('phone:max-w-card');
    expect(frame().className).not.toMatch(/max-w-\[/);
  });

  it('applies the design radius and elevation classes — intent, not layout', () => {
    render(<AuthShell title="Sign in">{null}</AuthShell>);

    expect(card().className).toContain('phone:rounded-xl');
    expect(card().className).toContain('phone:shadow');
  });

  it('⚡ drops the frame below 640px rather than shrinking it', () => {
    /**
     * The design's words: *"dropped rather than shrunk, which is what keeps it
     * from looking like a website on a phone."* **Three behaviours, not one
     * that scales** — and the mobile one is the only one that removes things.
     */
    render(<AuthShell title="Sign in">{null}</AuthShell>);

    for (const dropped of ['rounded-none', 'border-0', 'shadow-none']) {
      expect(card().className).toContain(dropped);
    }
  });

  it('applies the top-alignment and centring classes — intent, not layout', () => {
    /**
     * A tablet keyboard in portrait would push the primary action off screen
     * if the card were centred, which is why the three are genuinely three.
     *
     * ⚠️ **This asserted `/lg:/` and kept passing after
     * [TASK-1443](../../../docs/BACKLOG.md) replaced Tailwind's `screens`** —
     * ⛔ **so it was proving that a class STRING was present, while the class
     * itself had stopped resolving to any width.** ⚡ **The behaviour it
     * names — centred on a desktop — had silently stopped happening.**
     *
     * ✅ **It now names the design's own band**, so the assertion fails if the
     * breakpoint is renamed again rather than passing over a dead utility.
     */
    render(<AuthShell title="Sign in">{null}</AuthShell>);
    const main = screen.getByRole('main');

    // ⚠️ **These name classes; they do not prove any of them render.**
    // 📁 [`auth-layout.spec.ts`](../e2e/auth-layout.spec.ts) is where the
    // computed padding and justification are compared across the bands.
    expect(main.className).toContain('phone:pt-24');
    expect(main.className).toContain('smalllaptop:justify-center');
    expect(main.className).toContain('px-5');
  });
});

describe('what sits above and below the card', () => {
  it('prints the product mark above it, linking to the front door', () => {
    render(<AuthShell title="Sign in">{null}</AuthShell>);

    const mark = screen.getByRole('link', { name: 'Fortune Signora' });
    expect(mark).toHaveAttribute('href', '/welcome');
  });

  it('⛔ suppresses the mark for Welcome, and only for Welcome', () => {
    /**
     * **Welcome *is* the branding moment** — a 36px badge over a 22px heading
     * inside the card. Printing the shell's small mark as well would put
     * *Fortune Signora* on screen twice on the first thing a buyer sees.
     */
    render(
      <AuthShell title="Fortune Signora" mark={false} masthead={<span>FS</span>}>
        {null}
      </AuthShell>,
    );

    expect(screen.queryByRole('link', { name: 'Fortune Signora' })).not.toBeInTheDocument();
    expect(screen.getByText('FS')).toBeVisible();
  });

  it('prints the region and status line below it when given one', () => {
    // The design's *"security details in plain sight"* — *"hiding them reads
    // as evasion."* Enterprise buyers read this line.
    render(
      <AuthShell title="Sign in" region={<span>EU · eu.signora.app</span>}>
        {null}
      </AuthShell>,
    );

    expect(screen.getByText('EU · eu.signora.app')).toBeVisible();
  });

  it('renders the screen it is given, because it is a layout and not a page', () => {
    render(
      <AuthShell title="Sign in">
        <p>the screen</p>
      </AuthShell>,
    );

    expect(screen.getByText('the screen')).toBeVisible();
    expect(screen.getByRole('heading', { level: 1, name: 'Sign in' })).toBeVisible();
  });

  it('gives every screen exactly one level-1 heading', () => {
    // A shell that emitted its own h1 beside the screen's would give every
    // authentication page two, which is an outline no screen reader can use.
    render(
      <AuthShell title="Sign in" description="to Northwind Global">
        <p>the screen</p>
      </AuthShell>,
    );

    expect(screen.getAllByRole('heading', { level: 1 })).toHaveLength(1);
  });
});
