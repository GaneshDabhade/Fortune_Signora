/**
 * **One presentation for every refused gate** — [TASK-1423](../../../docs/BACKLOG.md),
 * against 📁 `Fortune Signora Security Gates.dc.html`.
 *
 * 🔴 **Nothing rendered this component either**, and it is what a person meets
 * when Signora refuses them — 📁 the screen where saying nothing is least
 * affordable.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { GateScreen } from '@/app/(auth)/gate/gate-screen';
import { GATE_COPY, GATE_REASONS } from '@/lib/entry/gates';

describe('📁 1.3.1 — every gate is a region with an accessible name', () => {
  for (const reason of GATE_REASONS) {
    it(`✅ ${reason}`, () => {
      /**
       * 📁 ***"Every gate is a region with an accessible name describing the
       * boundary, not the failure."***
       *
       * ⛔ **It was a bare `<div>`** — no landmark and no name — so a screen
       * reader moving by region skipped the only content on the page.
       */
      render(<GateScreen reason={reason} />);
      const region = screen.getByRole('region', { name: GATE_COPY[reason].title });

      expect(region).toBeInTheDocument();
      // ⚡ **The name comes from the heading rather than a second string** —
      // 📁 §2, one authoritative representation. A separate `aria-label` would
      // be a copy of the title that could drift from it.
      expect(
        region.querySelector(`#${CSS.escape(region.getAttribute('aria-labelledby') as string)}`),
      ).toHaveTextContent(GATE_COPY[reason].title);
    });
  }
});

describe('📁 2.4.3 — focus moves to the gate heading', () => {
  it('🔴 the heading is focused on arrival', () => {
    /**
     * ⛔ **Focus stayed wherever the previous page left it**, so a
     * screen-reader user arriving at a refusal was told nothing about why
     * until they navigated to it themselves.
     *
     * ⚡ **This is also how the gate announces.** 📁 `4.1.3` asks for one
     * announcement; **a live region here would announce nothing**, because its
     * content never changes after mount.
     */
    render(<GateScreen reason="INTENT_NOT_MEMBER" />);
    const heading = screen.getByRole('heading', {
      name: 'You are not a member of that organization',
    });

    expect(heading).toHaveFocus();
    // ⚠️ **A focus TARGET, never a tab stop** — a heading in the tab order
    // would add a stop to every gate for no gain.
    expect(heading).toHaveAttribute('tabindex', '-1');
  });
});

describe('⛔ what a refusal must never do', () => {
  it('📁 offers an action only where there is somewhere real to go', () => {
    /**
     * 📁 **The copy table's own rule**: *"`null` only where the honest answer
     * is **nothing you can do here***"*, and then the body has to say who can.
     *
     * ⛔ **Offering *"contact support"* as a button would dress a dead end as
     * a route** — the false-affordance class this repository keeps refusing.
     */
    render(<GateScreen reason="ACCOUNT_DELETED" />);
    expect(screen.queryByRole('link')).toBeNull();
    // ⚡ **And the body names who can help**, which is what makes the absent
    // control honest rather than merely absent.
    expect(screen.getByText(/administers your organization/)).toBeInTheDocument();
  });

  it('✅ and offers one where the person does have access to something', () => {
    render(<GateScreen reason="INTENT_NOT_MEMBER" />);
    expect(
      screen.getByRole('link', { name: 'Go to your organizations' }),
    ).toHaveAttribute('href', '/workspaces');
  });

  it('⛔ never names the reason code, in any gate', () => {
    // 📁 *"What happened, in the customer's words — never the reason code."*
    for (const reason of GATE_REASONS) {
      const view = render(<GateScreen reason={reason} />);
      expect(view.container.textContent ?? '').not.toContain(reason);
      view.unmount();
    }
  });
});
