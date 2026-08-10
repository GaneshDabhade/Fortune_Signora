import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { Dialog } from '@/components/ui';

/**
 * **`Dialog`'s two accessibility properties** —
 * [B-315](../../../docs/BUGS.md) and [B-312](../../../docs/BUGS.md).
 *
 * ⛔ **[§20c](../../../CLAUDE.md): an accessibility issue is a defect class,
 * not an enhancement, and never waits for a frozen foundation.**
 *
 * ⚡ **Both defects were invisible to a sighted mouse user**, which is why
 * neither was caught by looking at a screen — and why they are pinned here.
 */

function dialog(props: Partial<Parameters<typeof Dialog>[0]> = {}) {
  return render(
    <Dialog open onClose={vi.fn()} title="Evidence" {...props}>
      <p>Only text, and nothing to press.</p>
    </Dialog>,
  );
}

describe('🔴 B-315 — every dialog claimed the same id', () => {
  it('⛔ two dialogs in one document do not share a title id', () => {
    /**
     * ⚡ **The defect was invisible to a sighted user and wrong for everybody
     * else**: `aria-labelledby` pointed at a literal `"dialog-title"`, so with
     * two dialogs present **a screen reader could be told the wrong title.**
     */
    const { container } = render(
      <>
        <Dialog open onClose={vi.fn()} title="First" />
        <Dialog open onClose={vi.fn()} title="Second" />
      </>,
    );

    const ids = [...container.querySelectorAll('h2[id]')].map((h) => h.id);
    expect(ids).toHaveLength(2);
    expect(new Set(ids).size, 'two dialogs share one title id').toBe(2);
    expect(ids).not.toContain('dialog-title');
  });

  it('✅ and each dialog points at its OWN title', () => {
    // ⚡ **Unique is not sufficient** — two unique ids wired to the wrong
    // headings would pass the check above and still mislabel both dialogs.
    const { container } = render(
      <>
        <Dialog open onClose={vi.fn()} title="First" />
        <Dialog open onClose={vi.fn()} title="Second" />
      </>,
    );

    for (const el of container.querySelectorAll('dialog')) {
      const labelledBy = el.getAttribute('aria-labelledby');
      expect(labelledBy).toBeTruthy();
      expect(within(el as HTMLElement).getByRole('heading').id).toBe(labelledBy);
    }
  });
});

describe('🔴 B-312 — a dialog a keyboard could not reach anything inside', () => {
  it('⛔ a dialog carrying ONLY text still contains something focusable', () => {
    /**
     * 📁 **The probe that found it**: `BODY · BODY · BODY …` eight times.
     * ⚠️ **The focus trap was never broken** — it held trivially, because
     * there was nowhere for focus to go. 📁 *"The half nobody asserts is that
     * a dialog contains something."*
     *
     * ⛔ **This is the case that failed**: no footer, no controls, only prose.
     */
    const { container } = dialog();
    const focusable = container.querySelectorAll(
      'a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])',
    );
    expect(focusable.length).toBeGreaterThan(0);
  });

  it('✅ the close control is Dialog\'s, not the caller\'s', () => {
    /**
     * 🔴 **The defect class is *a `Dialog` need not contain anything
     * focusable*.** ⛔ **A dialog that is accessible only when its caller
     * happens to pass a Cancel button is not accessible** — so the control
     * lives in the header and no caller can omit it.
     */
    dialog();
    expect(screen.getByRole('button', { name: 'Close' })).toBeInTheDocument();
  });

  it('✅ and it closes', async () => {
    // ⛔ **A control that does nothing is the §2 defect**, and an accessibility
    // fix that adds one would be worse than the gap it filled.
    const onClose = vi.fn();
    dialog({ onClose });
    await userEvent.click(screen.getByRole('button', { name: 'Close' }));
    expect(onClose).toHaveBeenCalled();
  });

  it('♿ the control names the outcome rather than the glyph', () => {
    // A screen reader reading "✕" tells somebody nothing they can act on.
    dialog();
    const close = screen.getByRole('button', { name: 'Close' });
    expect(close).toHaveAccessibleName('Close');
    expect(close.textContent).toBe('✕');
  });
});
