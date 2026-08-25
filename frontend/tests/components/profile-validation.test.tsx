/**
 * **Screen `07 · Loading, validation & error`**, against
 * `docs/design-snapshot/screens/Fortune Signora User Profile.dc.html`.
 *
 * 📁 **The design's own `validation` table, verbatim:**
 *
 * > ***"Display name — 2–32 characters, trimmed. Emoji allowed, control
 * > characters stripped. Validated on blur."***
 * > ***"Save — Explicit, with a count of changed fields."***
 *
 * 📁 **And the sentence under the validation card:**
 *
 * > ***"Validation runs on blur, never per keystroke. The Save button stays
 * > enabled — pressing it moves focus to the first problem instead of doing
 * > nothing."***
 *
 * 🔴 **This was not a missing nicety.** 📁 `schemas.py:714` has always carried
 * `min_length=2`, so a one-character name **reached the server and came back a
 * `422`** — which the panel rendered as *"Check your connection and try
 * again."* ⛔ **The connection was fine.** These assert the stated refusal that
 * replaced the false one.
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const getPreferences = vi.hoisted(() => vi.fn());
const changePreferences = vi.hoisted(() => vi.fn());
vi.mock('@/lib/api/preferences', () => ({
  getPreferences: (...a: unknown[]) => getPreferences(...a),
  changePreferences: (...a: unknown[]) => changePreferences(...a),
}));
vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: () => ({ activeWorkspace: { id: 'ws-1', name: 'Northwind' } }),
}));

import { ProfilePanel } from '@/app/(app)/profile/profile-panel';
import { displayNameProblem, normalizeDisplayName } from '@/lib/profile/display-name';

const DEFAULTS = {
  theme: 'system',
  density: 'comfortable',
  time_format: '24h',
  timezone: null,
  language: null,
  pronouns: null,
  display_name: null,
  ai_insights: true,
  ai_drafts: true,
  always_show_citations: false,
  answer_style: 'direct',
  confidence_floor: 3,
} as const;

beforeEach(() => {
  getPreferences.mockReset().mockResolvedValue({ ...DEFAULTS });
  changePreferences.mockReset().mockImplementation(async (_ws, c) => ({ ...DEFAULTS, ...c }));
});

describe('the rule itself', () => {
  it('does not refuse an empty field, because the field is optional', () => {
    // ⛔ **A validator that made this a problem would make an optional field
    // mandatory** — the panel sends `null` for it, which is a real answer.
    expect(displayNameProblem('')).toBeNull();
    expect(displayNameProblem('   ')).toBeNull();
  });

  it('refuses one character, in the design own words', () => {
    expect(displayNameProblem('A')).toBe('At least 2 characters');
    // ⚡ Trimmed FIRST — otherwise a space is a character.
    expect(displayNameProblem(' A ')).toBe('At least 2 characters');
  });

  it('counts code points, so a two-emoji name is two characters and passes', () => {
    // ⛔ `'🙂🙂'.length` is **4** in UTF-16. A `.length` floor would pass this
    // for the wrong reason and a `.length` ceiling would refuse it at sixteen.
    expect(displayNameProblem('🙂🙂')).toBeNull();
    expect(displayNameProblem('🙂')).toBe('At least 2 characters');
  });

  it('🔴 holds a joined emoji together — the exception the strip rule needs', () => {
    // The woman-technologist glyph is U+1F469 · U+200D · U+1F4BB. **Stripping
    // `Cf` wholesale would split one glyph into two** and silently rewrite
    // what somebody typed.
    const engineer = '\u{1F469}\u200D\u{1F4BB}';
    expect(normalizeDisplayName(`${engineer}x`)).toBe(`${engineer}x`);
  });

  it('🔴 counts a joined emoji as THREE, because that is what the server counts', () => {
    /**
     * ⚠️ **This assertion was written the other way round and was wrong.**
     * ⛔ It claimed *one glyph, one character* — which is the **grapheme**
     * reading, and is not what either side implements.
     *
     * 🔴 **The client must agree with `schemas.py:714`, and Python's `len()`
     * counts code points.** ⚡ A grapheme-aware count here would call a name
     * too short that the server accepts, or accept one it refuses — **which
     * re-opens the exact defect this file exists to close**: a refusal the
     * screen cannot explain because it did not predict it.
     *
     * ✅ **So the rule is not *what looks like one character*; it is *what the
     * server will count*.** The joiner survives normalisation; it is simply
     * not free.
     */
    const engineer = '\u{1F469}\u200D\u{1F4BB}';
    expect([...engineer]).toHaveLength(3);
    expect(displayNameProblem(engineer)).toBeNull();
  });

  it('strips control characters rather than refusing them', () => {
    // ⚠️ **Written as escapes on purpose** — a literal control character in a
    // test asserting that control characters are stripped is a line nobody can
    // review, and it does not survive a copy/paste through a terminal.
    expect(normalizeDisplayName('Aur\u0007\u0008lie')).toBe('Aurlie');
    // A tab is `Cc` too, and a name pasted out of a spreadsheet carries one.
    expect(normalizeDisplayName('Aur\u0009elie')).toBe('Aurelie');
    // ⛔ **A newline is stripped, not turned into a space** — the design says
    // stripped, and substituting would invent a character nobody typed.
    expect(normalizeDisplayName('Aur\u000Aelie')).toBe('Aurelie');
  });

  it('refuses thirty-three, and accepts thirty-two', () => {
    expect(displayNameProblem('a'.repeat(32))).toBeNull();
    expect(displayNameProblem('a'.repeat(33))).toBe('At most 32 characters');
  });
});

describe('screen 07 · validation, in place', () => {
  it('🔴 says nothing while a name is being typed through one character', async () => {
    /**
     * 📁 ***"Validation runs on blur, never per keystroke."***
     *
     * ⚡ **Every name passes through one character on its way to two**, so a
     * validator that ran on input would call somebody wrong for typing.
     */
    const user = userEvent.setup();
    render(<ProfilePanel name="Aurélie Duval" email="a@b.com" />);

    const field = await screen.findByLabelText('Display name');
    await user.type(field, 'A');

    expect(screen.queryByText('At least 2 characters')).not.toBeInTheDocument();
  });

  it('says it once the field is left', async () => {
    const user = userEvent.setup();
    render(<ProfilePanel name="Aurélie Duval" email="a@b.com" />);

    const field = await screen.findByLabelText('Display name');
    await user.type(field, 'A');
    await user.tab();

    expect(await screen.findByText('At least 2 characters')).toBeInTheDocument();
    // ♿ The message is the field's, programmatically — not a loose paragraph.
    expect(field).toHaveAttribute('aria-invalid', 'true');
  });

  it('🔴 Save moves focus to the problem rather than reaching the server', async () => {
    /**
     * 📁 ***"The Save button stays enabled — pressing it moves focus to the
     * first problem instead of doing nothing."***
     *
     * ⛔ **This is the assertion that would have caught the false
     * instruction**: before it, the `PATCH` went out, the server refused it on
     * `min_length=2`, and the screen blamed the network.
     */
    const user = userEvent.setup();
    render(<ProfilePanel name="Aurélie Duval" email="a@b.com" />);

    const field = await screen.findByLabelText('Display name');
    await user.type(field, 'A');
    await user.click(screen.getByRole('button', { name: /^Save/ }));

    expect(changePreferences).not.toHaveBeenCalled();
    expect(field).toHaveFocus();
    expect(await screen.findByText('At least 2 characters')).toBeInTheDocument();
    // ⛔ **And not the sentence that sent people to look at their router.**
    expect(screen.queryByText(/Check your connection/)).not.toBeInTheDocument();
  });

  it('the control stays enabled, because a disabled Save withholds the reason', async () => {
    const user = userEvent.setup();
    render(<ProfilePanel name="Aurélie Duval" email="a@b.com" />);

    const field = await screen.findByLabelText('Display name');
    await user.type(field, 'A');

    expect(screen.getByRole('button', { name: /^Save/ })).toBeEnabled();
  });
});

describe('screen 07 · Save carries a count of changed fields', () => {
  it('names no count before anything is changed', async () => {
    render(<ProfilePanel name="Aurélie Duval" email="a@b.com" />);
    // ⛔ **Not "Save 0 changes"** — a label that argues with its own button.
    expect(await screen.findByRole('button', { name: 'Save changes' })).toBeInTheDocument();
  });

  it('counts one, then two, and says "change" for one of them', async () => {
    const user = userEvent.setup();
    render(<ProfilePanel name="Aurélie Duval" email="a@b.com" />);

    await user.type(await screen.findByLabelText('Display name'), 'Aurélie');
    expect(screen.getByRole('button', { name: 'Save 1 change' })).toBeInTheDocument();

    await user.type(screen.getByLabelText('Pronouns'), 'she/her');
    expect(screen.getByRole('button', { name: 'Save 2 changes' })).toBeInTheDocument();
  });

  it('🔴 does not count a value that was typed and typed back', async () => {
    /**
     * ⚡ **The baseline is what the server last returned**, so returning a
     * field to its stored value is not a change. ⛔ A count measured against a
     * snapshot of the empty form would report one here.
     */
    getPreferences.mockResolvedValue({ ...DEFAULTS, display_name: 'Aurélie' });
    const user = userEvent.setup();
    render(<ProfilePanel name="Aurélie Duval" email="a@b.com" />);

    const field = await screen.findByLabelText('Display name');
    await user.clear(field);
    await user.type(field, 'Aurélie');

    expect(screen.getByRole('button', { name: 'Save changes' })).toBeInTheDocument();
  });

  it('does not count whitespace the PATCH would strip anyway', async () => {
    getPreferences.mockResolvedValue({ ...DEFAULTS, display_name: 'Aurélie' });
    const user = userEvent.setup();
    render(<ProfilePanel name="Aurélie Duval" email="a@b.com" />);

    const field = await screen.findByLabelText('Display name');
    await user.type(field, '   ');

    expect(screen.getByRole('button', { name: 'Save changes' })).toBeInTheDocument();
  });
});
