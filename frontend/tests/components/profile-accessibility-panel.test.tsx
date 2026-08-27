/**
 * **Profile → Accessibility** — 📁 `Fortune Signora User Profile.dc.html`,
 * with [B-1080](../../../docs/BUGS.md) and [C-1573](../../../docs/LANE_COORDINATION.md).
 *
 * 🔴 **This panel was changed this session and had no test.** ⛔ **A fix QE
 * cannot exercise is a fix on the branch and nowhere else**, which is the half
 * of *complete* that source review never checks.
 */
import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const getPreferences = vi.hoisted(() => vi.fn());
const changePreferences = vi.hoisted(() => vi.fn());
const matches = vi.hoisted(() => ({ value: false }));

vi.mock('@/lib/api/preferences', () => ({ getPreferences, changePreferences }));
vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: () => ({ activeWorkspace: { id: 'w1', name: 'Northwind' } }),
}));

import { AccessibilityPanel } from '@/app/(app)/profile/accessibility-panel';

const PREFS = {
  reduce_motion: false,
  increase_contrast: false,
  always_show_focus_ring: false,
  underline_links: true,
  text_size: '100',
  screen_reader_verbosity: 'standard',
};

beforeEach(() => {
  vi.clearAllMocks();
  matches.value = false;
  getPreferences.mockResolvedValue(PREFS);
  changePreferences.mockResolvedValue(PREFS);
  vi.stubGlobal('matchMedia', (query: string) => ({
    matches: query.includes('reduce') ? matches.value : false,
    addEventListener: () => {},
    removeEventListener: () => {},
  }));
});

describe('🔴 B-1080 — the screen can be used to find out what the device is doing', () => {
  it('⛔ with the device reducing motion, it SAYS so', async () => {
    /**
     * 📁 **`2.3.3`**: *"Reduce motion is honoured from the system on first
     * load, **shown as pre-set rather than silently applied**."*
     *
     * ⛔ **QE measured both device states and got identical output** — the
     * screen could not distinguish *your device is reducing motion* from
     * *nothing is reducing motion*, **which is the state the design names
     * *silently applied*, in those words.**
     */
    matches.value = true;
    render(<AccessibilityPanel />);

    expect(
      await screen.findByText(/Your device is set to reduce motion/),
    ).toBeInTheDocument();
  });

  it('✅ and with the device silent, it says nothing about the device', async () => {
    // ⚡ **The vacuity half, and it is the whole finding**: if the sentence
    // appeared in both states the screen would be back where QE found it.
    render(<AccessibilityPanel />);
    await screen.findByLabelText('Reduce motion');

    expect(screen.queryByText(/Your device is set to reduce motion/)).toBeNull();
  });

  it('⛔ the toggle still reflects the STORED value, not the device', async () => {
    /**
     * 📁 [C-1573](../../../docs/LANE_COORDINATION.md) — **the design draws the
     * toggle ON from the system and that half is deliberately not built.**
     * ⛔ `reduce_motion` is a non-nullable boolean, so a toggle shown on from
     * the device would write `false` when clicked — **the value already there**
     * — and the control would move nothing and snap back.
     *
     * ⚠️ **This asserts the current, ruled-pending behaviour**, so the day the
     * field becomes tri-state this test names the row.
     */
    matches.value = true;
    render(<AccessibilityPanel />);

    const toggle = await screen.findByLabelText('Reduce motion');
    expect(toggle).not.toBeChecked();
  });
});

describe('♿ the help text describes each control and is never its name', () => {
  it('🔴 the name is the label alone, and the description reaches it as a description', async () => {
    /**
     * 📁 **`User Profile` `1.3.1`**: *"every control has a programmatic label
     * **and its help text via `aria-describedby`**."* ⛔ **Both local `Toggle`
     * copies wrapped label AND description in one `<label>`**, so a screen
     * reader announced the whole paragraph as the control's name.
     */
    matches.value = true;
    render(<AccessibilityPanel />);

    const toggle = await screen.findByLabelText('Reduce motion');
    const described = toggle.getAttribute('aria-describedby');
    expect(described).not.toBeNull();

    // ⚡ **Two ids while the device note is showing** — the help text AND the
    // fact about the device, in that order, neither replacing the other.
    const ids = (described as string).split(' ');
    expect(ids).toHaveLength(2);
    expect(document.getElementById(ids[0] as string)?.textContent).toContain(
      'Removes every transform',
    );
    expect(document.getElementById(ids[1] as string)?.textContent).toContain(
      'Your device is set to reduce motion',
    );
  });

  it('⛔ and a control with no device note has no dangling reference', async () => {
    render(<AccessibilityPanel />);
    const toggle = await screen.findByLabelText('Increase contrast');

    for (const id of (toggle.getAttribute('aria-describedby') as string).split(' ')) {
      expect(document.getElementById(id)).not.toBeNull();
    }
  });
});

describe('⛔ nothing is stored about the reader’s device', () => {
  it('🔴 rendering with the device reducing motion writes nothing', async () => {
    /**
     * 📁 **The panel's own standing argument, and it survives the fix**:
     * *"storing what the browser already reports would be the hidden input
     * [§2](../../../CLAUDE.md) forbids."* ⚡ **The value reaches a sentence and
     * nothing else.**
     */
    matches.value = true;
    render(<AccessibilityPanel />);
    await screen.findByText(/Your device is set to reduce motion/);

    await waitFor(() => expect(getPreferences).toHaveBeenCalled());
    expect(changePreferences).not.toHaveBeenCalled();
  });
});
