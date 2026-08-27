/**
 * **The last surfaces nothing rendered** — [TASK-1441](../../../docs/BACKLOG.md).
 *
 * 🔴 **Forty-seven components had no test that rendered them.** ⚡ Home,
 * onboarding, the gate screen, the saved-view strip and two library components
 * now do; **these are the remainder that can be rendered without a page's worth
 * of scaffolding.**
 *
 * ⛔ **The sweep is the same one B-1085 would have failed**: the text a
 * customer sees, checked for the four ways an absence arrives and for comment
 * markers. ⚠️ **Plus the claims each surface states strongly enough to pin.**
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => '/',
}));

import { PosturePanel } from '@/app/(app)/profile/security/posture-panel';
import { AccountName } from '@/components/intelligence/account-name';
import { DroppedWithTheirProduct } from '@/components/commercial/catalog-scope';

const NEVER = ['undefined', 'null', 'NaN', '[object Object]', '/**', '*/'];

function clean(container: HTMLElement) {
  const text = container.textContent ?? '';
  expect(text.trim().length).toBeGreaterThan(0);
  for (const forbidden of NEVER) expect(text).not.toContain(forbidden);
}

describe('🔴 the security posture strip says “Not known”, and never “none”', () => {
  it('⛔ a failed read is a stated absence, not a zero', () => {
    /**
     * 📁 **The panel's own rule, and it is [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md)'s
     * worst case**: *"a failed read must never render as an empty result —
     * here the empty result would read `Open alerts: none`."*
     *
     * ⛔ **`Not known` and never `None`, `0` or an em dash.** ⚡ **A dash is
     * read as *nothing to report*, which is the false reassurance this whole
     * panel exists to refuse** — on a page written for *"someone who thinks
     * they have been compromised, reading it in under a minute, while
     * frightened."*
     */
    const { container } = render(<PosturePanel factors={null} sessions={null} />);
    clean(container);

    // ⚠️ **Scoped to the VALUE, not the panel's prose.** ⛔ The first version
    // banned an em dash anywhere in `textContent` and fired on ordinary
    // punctuation — **the too-wide-and-loud instrument, which costs time
    // rather than a wrong answer, and is still the wrong question.**
    const values = screen
      .getAllByTestId('posture-cell')
      .map((cell) => cell.querySelector('dd span')?.textContent?.trim() ?? '');

    expect(values).toHaveLength(5);
    for (const value of values) {
      expect(value).toBe('Not known');
      // ⛔ **Never a dash, a zero or *None*** — each of those reads as
      // *nothing to report*, which is the false reassurance this panel refuses.
      expect(['—', '–', '-', '0', 'None', '']).not.toContain(value);
    }
  });

  it('✅ every cell carries a WORD beside its colour', () => {
    /**
     * 📁 **`Security Center` `1.4.1`**: *"Every risk signal carries a word
     * beside its colour."* ⚡ **Three of five cells cannot answer**, and the
     * word for that is *Not known*.
     */
    render(<PosturePanel factors={2} sessions={3} />);
    for (const cell of screen.getAllByTestId('posture-cell')) {
      expect((cell.textContent ?? '').trim().length).toBeGreaterThan(0);
    }
  });
});

describe('⛔ an account with no name distinguishes “not named” from “not arrived”', () => {
  it('🔴 pending and absent are different renders', () => {
    /**
     * 📁 **The component's own contract**: *"`null` means the identity surface
     * says **nobody has named it** — not that the answer has not arrived. That
     * is `pending`."*
     *
     * ⚡ **This is [[absence-collapsed-into-a-value]] refused at the type
     * level**, and the render has to keep the two apart or the type buys
     * nothing.
     */
    const waiting = render(
      <AccountName name={null} pending absent="No name on record" href="/a/1" />,
    );
    const whileWaiting = waiting.container.textContent ?? '';
    waiting.unmount();

    const { container } = render(
      <AccountName name={null} pending={false} absent="No name on record" href="/a/1" />,
    );
    clean(container);

    expect(container.textContent).toContain('No name on record');
    expect(container.textContent).not.toBe(whileWaiting);
  });

  it('✅ and a named account is a link to its record', () => {
    render(<AccountName name="Vantage Logistics" pending={false} absent="—" href="/a/1" />);
    expect(screen.getByRole('link', { name: 'Vantage Logistics' })).toHaveAttribute(
      'href',
      '/a/1',
    );
  });
});

describe('📁 what was dropped is stated, never silently filtered', () => {
  it('⛔ the count is named', () => {
    // ⚡ **A list that quietly omits rows is the failure P-A names**, one
    // surface along: the reader cannot tell a short list from a filtered one.
    const { container } = render(<DroppedWithTheirProduct count={3} />);
    clean(container);
    expect(container.textContent).toContain('3');
  });

  it('✅ and nothing is said when nothing was dropped', () => {
    const { container } = render(<DroppedWithTheirProduct count={0} />);
    expect(container.textContent ?? '').toBe('');
  });
});
