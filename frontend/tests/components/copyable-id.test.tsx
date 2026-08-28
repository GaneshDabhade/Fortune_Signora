/**
 * **The correlation id, copyable** — 📁 `System States` §03 and
 * `Workspace Setup` `2.5.8`.
 *
 * 🔴 **Nothing rendered this component either.** ⚡ It is the control somebody
 * uses at the worst moment — reading an error to a support conversation — and
 * its target size was inherited rather than stated.
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { CopyableId } from '@/components/ui/copyable-id';

const writeText = vi.hoisted(() => vi.fn());

beforeEach(() => {
  vi.clearAllMocks();
  writeText.mockResolvedValue(undefined);
  Object.defineProperty(navigator, 'clipboard', {
    value: { writeText },
    configurable: true,
  });
});

describe('📁 2.5.8 — a copy button is ≥ 24px, and says so itself', () => {
  it('🔴 the floor is stated rather than inherited', () => {
    /**
     * ⛔ **It was `px-2 py-1 text-2xs` and nothing else**, so the height was
     * `8px + whatever line-height it inherited`. ⚡ **`--text-2xs` is 11px and
     * the config sets it size-only**, so a parent with `leading-none` renders a
     * 19px target and a parent with `leading-6` a 32px one — **from identical
     * markup.**
     *
     * ⚠️ **A target whose size depends on where it is placed is not a target
     * size.** 📁 The same lesson `icon-button.tsx` records: *"`px-1` around a
     * `›` is padding round a narrow glyph, not a target."*
     *
     * ⚠️ **Classes, not measured pixels** — jsdom applies no stylesheet, so a
     * rect here is zero and would pass any value. **A class assertion can
     * fail, which is the honest instrument available.**
     */
    render(<CopyableId value="a1b2c3" />);
    const button = screen.getByRole('button');

    expect(button.classList.contains('min-h-6')).toBe(true);
    // ⚡ **`inline-flex` is what makes a min-height bite on a button whose
    // content is a text run** — without it the class is decoration.
    expect(button.classList.contains('inline-flex')).toBe(true);
    // 📁 **The repository's own touch floor**, the same one `Button` and the
    // accounts toolbar use.
    expect(button.classList.contains('coarse:min-h-11')).toBe(true);
  });

  it('✅ it names itself and the value it will copy', () => {
    // ⛔ **A bare id is not a control** — the word `Copy` is what makes it one,
    // and it is inside the button rather than beside it.
    render(<CopyableId value="a1b2c3" />);
    const button = screen.getByRole('button');

    expect(button).toHaveTextContent('a1b2c3');
    expect(button).toHaveTextContent('Copy');
  });

  it('🔴 a failed copy says so, and never reports success', async () => {
    /**
     * ⛔ **The clipboard can refuse** — an insecure origin, a denied
     * permission, a browser that does not implement it. ⚡ **Reporting
     * *Copied* into that is the false claim this repository refuses**, and it
     * is worse here than most: **the person is mid-incident, pasting an id
     * that is not on their clipboard.**
     */
    writeText.mockRejectedValue(new Error('denied'));
    render(<CopyableId value="a1b2c3" />);

    await userEvent.click(screen.getByRole('button'));

    expect(await screen.findByText('Copy failed')).toBeInTheDocument();
    expect(screen.queryByText('Copied')).toBeNull();
  });

  it('✅ and a successful one confirms', async () => {
    render(<CopyableId value="a1b2c3" />);
    await userEvent.click(screen.getByRole('button'));

    expect(await screen.findByText('Copied')).toBeInTheDocument();
    expect(writeText).toHaveBeenCalledWith('a1b2c3');
  });
});
