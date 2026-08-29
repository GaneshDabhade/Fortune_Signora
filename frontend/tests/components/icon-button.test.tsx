/**
 * **The icon control's geometry, and the reason it is a component** — 📁 the
 * App Shell's §04 `topBarSlots` and §21 `a11yRules`
 * ([D-138](../../../docs/DECISION_REGISTER.md)).
 *
 * > 📁 ***"Notifications — 32 × 32."*** · ***`2.5.8` — "Every top-bar control
 * > is a 32px target with 8px separation; 44px on touch."***
 *
 * ## ⛔ It was extracted to fix a measured defect, and nothing witnessed it
 *
 * ⚠️ **Found by asking which components nothing names**: 2 of 131. 📁 Its own
 * docstring records what it was built for — **the rail collapse toggle was
 * `18 × 32` and the sheet close `21 × 32`**, both from `rounded p-1`, **so the
 * control was as wide as whatever character was inside it and `«` and `✕` are
 * narrow.**
 *
 * 🔴 **A target must own its geometry, never inherit it from its content** —
 * ⛔ **and that is precisely the claim no assertion had ever read.** ⚡ **A
 * regression to padding would look identical in review and in every screenshot
 * that does not happen to contain a narrow glyph.**
 *
 * ⚠️ **`classList.contains`, never `toContain`** — 📁
 * [B-1091](../../docs/BUGS.md): `h-8` is a substring of `h-80`, and a
 * responsive prefix satisfies a substring match while inverting the rule.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { IconButton } from '@/components/ui/icon-button';

const control = () => screen.getByRole('button');

describe('🔴 the target owns its geometry, which is why this component exists', () => {
  it('📁 `md` is the shell’s 32px furniture', () => {
    render(<IconButton label="Notifications">🔔</IconButton>);

    expect(control().classList.contains('h-8')).toBe(true);
    expect(control().classList.contains('w-8')).toBe(true);
  });

  it('📁 `sm` is 24px — `2.5.8`’s floor, and still above it', () => {
    /**
     * ⛔ **Not a smaller default.** 📁 The component's own words: *"it exists
     * for a control that sits inside a dense row of content, and it still
     * clears the minimum."* ⚡ **`h-5` would be 20px and below the floor**,
     * which is the mistake a size scale invites.
     */
    render(
      <IconButton label="Remove" size="sm">
        ✕
      </IconButton>,
    );

    expect(control().classList.contains('h-6')).toBe(true);
    expect(control().classList.contains('w-6')).toBe(true);
  });

  it('⛔ never shrinks, because a flex row will take the pixels if it can', () => {
    // ⚡ **`shrink-0` is the half that survives a crowded top bar.** A target
    // that is 32px until the row runs out of space is 32px in every screenshot
    // and smaller for the person on the narrow window.
    render(<IconButton label="Help">?</IconButton>);

    expect(control().classList.contains('shrink-0')).toBe(true);
  });

  it('♿ 📁 `2.5.8` — 44px on touch, as a MINIMUM rather than a size step', () => {
    /**
     * ⛔ **`min-h`/`min-w`, not `h`/`w`.** ⚡ **A coarse-pointer size step
     * would replace the design's 32px**; a minimum leaves it intact wherever a
     * mouse is pointing and only grows the target where a finger is.
     */
    render(<IconButton label="Notifications">🔔</IconButton>);

    expect(control().classList.contains('coarse:min-h-11')).toBe(true);
    expect(control().classList.contains('coarse:min-w-11')).toBe(true);
  });
});

describe('♿ the control is announced once, and by its outcome', () => {
  it('📁 the label names the OUTCOME, and the glyph is hidden from the reader', () => {
    /**
     * ⛔ **A screen-reader user cannot see which way a chevron points**, so the
     * accessible name is *"Collapse navigation"* and never *"chevron"*.
     * ⚡ **And the glyph is `aria-hidden`**: announcing both reads the control
     * twice, which is the defect a decorative character quietly creates.
     */
    render(<IconButton label="Collapse navigation">«</IconButton>);

    expect(screen.getByRole('button', { name: 'Collapse navigation' })).toBeVisible();

    const glyph = control().querySelector('[aria-hidden]');
    expect(glyph, 'the glyph is not hidden, so it is announced beside the label').not.toBeNull();
    expect(glyph?.textContent).toBe('«');
  });

  it('states whether the surface it opens is open, when it opens one', () => {
    const { rerender } = render(
      <IconButton label="Open navigation" expanded={false}>
        ☰
      </IconButton>,
    );
    expect(control()).toHaveAttribute('aria-expanded', 'false');

    rerender(
      <IconButton label="Open navigation" expanded>
        ☰
      </IconButton>,
    );
    expect(control()).toHaveAttribute('aria-expanded', 'true');
  });

  it('⛔ and says nothing about expansion when it opens nothing', () => {
    /**
     * ⚡ **Absent, not `false`.** ⛔ **`aria-expanded="false"` tells a reader
     * there is something to open** — so a control that merely acts would be
     * announced as a collapsed disclosure.
     */
    render(<IconButton label="Help">?</IconButton>);

    expect(control()).not.toHaveAttribute('aria-expanded');
  });
});

describe('⛔ a control inside a form must not submit it', () => {
  it('is `type="button"` by default, and never inferred', () => {
    /**
     * 📁 The component's own words: *"a control inside a form that omits this
     * submits it, which is the quietest possible defect."* ⚡ **HTML's default
     * for `<button>` is `submit`**, so this is a real reversal rather than a
     * restatement.
     */
    render(<IconButton label="Clear">✕</IconButton>);

    expect(control()).toHaveAttribute('type', 'button');
  });

  it('⚡ but a caller that genuinely wants to submit still can', () => {
    // ⛔ **A default, not a lock.** Forcing `button` would make the component
    // unusable for the one case where submitting is the point.
    render(
      <IconButton label="Search" type="submit">
        🔍
      </IconButton>,
    );

    expect(control()).toHaveAttribute('type', 'submit');
  });

  it('passes the click through, which is the whole point of a button', () => {
    const onClick = vi.fn();
    render(
      <IconButton label="Dismiss" onClick={onClick}>
        ✕
      </IconButton>,
    );

    control().click();

    expect(onClick).toHaveBeenCalledOnce();
  });
});
