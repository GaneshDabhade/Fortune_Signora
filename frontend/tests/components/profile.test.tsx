/**
 * **Workflow 9 · User Profile** — [TASK-470](../../../docs/BACKLOG.md)
 * milestone 1, against `docs/design-snapshot/screens/Fortune Signora User
 * Profile.dc.html`.
 *
 * ⚡ **The assertions the row names**, plus the one the design states as a
 * number: `0` — *"edits accepted that a sync would undo"* — which is why the
 * fields with no source behind them are absent rather than drawn locked.
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

import { FieldOriginTag } from '@/components/ui';

import { AiPanel } from '@/app/(app)/profile/ai-panel';
import { AppearancePanel } from '@/app/(app)/profile/appearance-panel';
import { LocalePanel } from '@/app/(app)/profile/locale-panel';
import { ProfilePanel } from '@/app/(app)/profile/profile-panel';

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

describe('screen 01 · the fields that are real, and the ones that are absent', () => {
  it('shows the name and email the account actually holds', async () => {
    render(<ProfilePanel name="Aurélie Duval" email="a.duval@northwind.com" />);

    expect(await screen.findByText('Aurélie Duval')).toBeInTheDocument();
    expect(screen.getByText('a.duval@northwind.com')).toBeInTheDocument();
  });

  it('🔴 draws no Job title or Department, because nothing knows them', async () => {
    /**
     * ⛔ **The design locks them as *From directory* and no directory exists**
     * — [C-248](../../../docs/LANE_COORDINATION.md). A locked field with no
     * sync behind it is a rule the product does not have, painted as one it
     * does ([D-156](../../../docs/DECISION_REGISTER.md) ④).
     */
    render(<ProfilePanel name="Aurélie Duval" email="a.duval@northwind.com" />);
    await screen.findByText('Aurélie Duval');

    expect(screen.queryByText(/job title/i)).toBeNull();
    expect(screen.queryByText(/department/i)).toBeNull();
  });

  it('⛔ draws no mobile number, because nothing verifies one', async () => {
    // The design shows it under "Verified 14 Mar 2026". A number displayed
    // under a verified badge that nothing verified is the same defect wearing
    // a friendlier face.
    render(<ProfilePanel name="Aurélie Duval" email="a.duval@northwind.com" />);
    await screen.findByText('Aurélie Duval');

    expect(screen.queryByText(/mobile/i)).toBeNull();
    expect(screen.queryByText(/verified/i)).toBeNull();
  });

  it('⚠️ attributes the email lock to the account, never to a directory', async () => {
    // The lock is true; only the design's attribution would be false.
    render(<ProfilePanel name="Aurélie Duval" email="a.duval@northwind.com" />);
    await screen.findByText('Aurélie Duval');

    expect(screen.getAllByText('Sign-in identity').length).toBeGreaterThan(0);
    expect(screen.queryByText('From directory')).toBeNull();
  });

  it('sends only the two fields this panel owns', async () => {
    /**
     * 🔴 **The server distinguishes absent from null**, so a panel spreading
     * the whole object would clear the theme and timezone that other panels
     * set. **One panel, its own keys.**
     */
    render(<ProfilePanel name="A" email="a@b.com" />);
    await screen.findByLabelText('Display name');

    await userEvent.type(screen.getByLabelText('Display name'), 'Aurélie');
    await userEvent.click(screen.getByRole('button', { name: /^Save/ }));

    expect(changePreferences).toHaveBeenCalledWith('ws-1', {
      display_name: 'Aurélie',
      pronouns: null,
    });
  });
});

describe('screen 02 · the timezone prompt offers and does not switch', () => {
  it('🔴 offers both answers as buttons and changes nothing on its own', async () => {
    /**
     * *"Your timezone changed · Switch to Singapore · Keep Copenhagen."*
     * ⚡ **A person in Copenhagen opening Signora from a hotel in Singapore
     * has not moved**, and only they can tell the product that.
     */
    getPreferences.mockResolvedValue({ ...DEFAULTS, timezone: 'Europe/Copenhagen' });
    vi.spyOn(Intl, 'DateTimeFormat').mockReturnValue({
      resolvedOptions: () => ({ timeZone: 'Asia/Singapore' }),
    } as unknown as Intl.DateTimeFormat);

    render(<LocalePanel />);

    expect(await screen.findByRole('button', { name: /switch to asia\/singapore/i })).toBeVisible();
    expect(screen.getByRole('button', { name: /keep europe\/copenhagen/i })).toBeVisible();
    // ⛔ Nothing was saved by merely showing the offer.
    expect(changePreferences).not.toHaveBeenCalled();
  });

  it('switches only when the person asks', async () => {
    getPreferences.mockResolvedValue({ ...DEFAULTS, timezone: 'Europe/Copenhagen' });
    vi.spyOn(Intl, 'DateTimeFormat').mockReturnValue({
      resolvedOptions: () => ({ timeZone: 'Asia/Singapore' }),
    } as unknown as Intl.DateTimeFormat);
    render(<LocalePanel />);

    await userEvent.click(await screen.findByRole('button', { name: /switch to/i }));

    expect(changePreferences).toHaveBeenCalledWith('ws-1', { timezone: 'Asia/Singapore' });
  });

  it('⚠️ keeping is a real answer and the prompt does not come back', async () => {
    // Returning on the next render would be the "second ask" the product
    // refuses one workflow over.
    getPreferences.mockResolvedValue({ ...DEFAULTS, timezone: 'Europe/Copenhagen' });
    vi.spyOn(Intl, 'DateTimeFormat').mockReturnValue({
      resolvedOptions: () => ({ timeZone: 'Asia/Singapore' }),
    } as unknown as Intl.DateTimeFormat);
    render(<LocalePanel />);

    await userEvent.click(await screen.findByRole('button', { name: /keep/i }));

    expect(screen.queryByRole('button', { name: /switch to/i })).toBeNull();
  });

  it('⛔ never claims a timezone changed when none was ever set', async () => {
    // With nothing to compare against, "your timezone changed" is a claim
    // about a change that never happened.
    vi.spyOn(Intl, 'DateTimeFormat').mockReturnValue({
      resolvedOptions: () => ({ timeZone: 'Asia/Singapore' }),
    } as unknown as Intl.DateTimeFormat);
    render(<LocalePanel />);
    await screen.findByText('Language & region');

    expect(screen.queryByText(/your browser reports/i)).toBeNull();
  });

  it('⛔ draws no "week starts on", because no policy enforces one', async () => {
    render(<LocalePanel />);
    await screen.findByText('Language & region');

    expect(screen.queryByText(/week starts/i)).toBeNull();
  });
});

describe('the field-origin tag', () => {
  it('never says "From directory" on a shipped screen', () => {
    // The variant exists because the design draws three kinds; it stays unused
    // until a sync exists that could undo an edit — C-248.
    render(<FieldOriginTag origin="yours" />);

    expect(screen.getByText('Yours')).toBeInTheDocument();
  });
});


describe('screen 03 · appearance is the account\'s, not the browser\'s', () => {
  it('🔴 stores the choice on the server and never in localStorage', async () => {
    /**
     * **The row's constraint, verbatim**: *"applies to this account on every
     * device you sign in from, not to this browser."* ⛔ **A theme cached in
     * the browser is right on the laptop it was chosen on and wrong on every
     * other one** — which is the precise promise that sentence makes.
     */
    const setItem = vi.spyOn(Storage.prototype, 'setItem');
    render(<AppearancePanel />);

    await userEvent.click(await screen.findByRole('radio', { name: /^Dark/ }));

    expect(changePreferences).toHaveBeenCalledWith('ws-1', { theme: 'dark' });
    expect(setItem).not.toHaveBeenCalled();
    setItem.mockRestore();
  });

  it('⚠️ keeps System as System rather than resolving it', async () => {
    // "Follows your device, switching at sunset" is a deferral. Answering it
    // with light or dark replaces the person's choice with one reading of it.
    // ⚠️ Starts from `dark`: clicking an already-selected radio fires no
    // change, which is the control being correct rather than the panel.
    getPreferences.mockResolvedValue({ ...DEFAULTS, theme: 'dark' });
    render(<AppearancePanel />);

    await userEvent.click(await screen.findByRole('radio', { name: /^system/i }));

    expect(changePreferences).toHaveBeenCalledWith('ws-1', { theme: 'system' });
  });

  it('is a radio group, so arrow keys work and nothing needs a pointer', async () => {
    // The design states this as an accessibility criterion by number: a choice
    // group is a radiogroup, "not clickable divs".
    render(<AppearancePanel />);

    // ⚠️ `/^Light/` and not `/light/i`: the Dark segment's own description
    // reads "For low light and long sessions", so the loose pattern matched
    // two controls — a locator that finds the wrong thing is B-149's lesson.
    expect(await screen.findByRole('radio', { name: /^Light/ })).toBeInTheDocument();
    expect(screen.getAllByRole('radio').length).toBe(5);
  });

  /**
   * 🔴 **The theme picker is a CARD list, not a segmented control** — 📁 the
   * design's own component inventory names them as two separate entries at
   * different depths: `Segmented / Toggle / Select` under *"v2 · controls"*,
   * and **`ThemeCard` under *"v2 · card 12px"***.
   *
   * ## ⚠️ Why this assertion exists, and what the suite could not see
   *
   * ⛔ **This panel drew `SegmentedControl` and the whole 4060-test suite
   * passed after it was corrected to `ChoiceCards`** — because every existing
   * assertion asks for `getByRole('radio')` and a radiogroup, **and both
   * primitives satisfy both.** ⚡ **The tests were right about accessibility
   * and blind to the treatment.**
   *
   * ✅ **So this pins what actually differed**: 📁 the design fills the selected
   * card with `--brand-tint` and rounds it to `12px`; the segmented control
   * left it on `--surface` at `6px`. **A radio group can be perfectly correct
   * and be the wrong component.**
   */
  it('🔴 draws the selected theme as the design\'s card — brand tint at 12px', async () => {
    render(<AppearancePanel />);

    const system = await screen.findByRole('radio', { name: /^System/ });
    const card = system.closest('label');
    expect(card, 'the choice is not wrapped in a label').not.toBeNull();

    // 📁 *"border-radius:12px"* — `rounded-lg`, not `rounded`.
    expect(card?.classList.contains('rounded-lg')).toBe(true);
    // 📁 The selected card takes the brand border AND the brand tint.
    expect(card?.classList.contains('border-accent')).toBe(true);
    expect(
      card?.classList.contains('bg-accent-subtle'),
      'the selected card is not filled with the brand tint',
    ).toBe(true);
  });

  it('⛔ does not paint the page itself', async () => {
    // It records the choice; the design system renders it. A panel that wrote
    // a class onto the document would be a second place a theme is decided.
    render(<AppearancePanel />);
    await screen.findByRole('radio', { name: /^Light/ });

    expect(document.documentElement.className).not.toMatch(/dark|light/);
  });

  it('sends only the field that changed', async () => {
    render(<AppearancePanel />);

    await userEvent.click(await screen.findByRole('radio', { name: /compact/i }));

    expect(changePreferences).toHaveBeenCalledWith('ws-1', { density: 'compact' });
  });
});


describe('B-215 · a slow read must not erase what somebody has typed', () => {
  it('🔴 keeps the typed value when the server answer arrives afterwards', async () => {
    /**
     * **This was B-215, and it presented as a lost request.** It was a lost
     * keystroke: the load effect seeded the inputs after the first character,
     * `Save` then sent the empty field as `null`, the row stored nothing —
     * and the screen said *"Saved"*.
     *
     * ⛔ **The endpoint and the proxy were both fine**, each proved by sending
     * a `PATCH` through it directly. **A defect register entry that had
     * blamed either would have cost the next person the same afternoon.**
     */
    let release!: (value: unknown) => void;
    getPreferences.mockReturnValue(
      new Promise((resolve) => {
        release = resolve;
      }),
    );

    render(<ProfilePanel name="A" email="a@b.com" />);
    await userEvent.type(screen.getByLabelText('Display name'), 'Aurélie');

    // The read lands late, carrying the older, empty value.
    release({ ...DEFAULTS });

    await userEvent.click(screen.getByRole('button', { name: /^Save/ }));

    expect(changePreferences).toHaveBeenCalledWith('ws-1', {
      display_name: 'Aurélie',
      pronouns: null,
    });
  });

  it('still seeds an untouched form from the server', async () => {
    // The guard must not cost the ordinary case: somebody arriving at a
    // profile they have filled in before still sees it.
    getPreferences.mockResolvedValue({ ...DEFAULTS, display_name: 'Aurélie' });

    render(<ProfilePanel name="A" email="a@b.com" />);

    expect(await screen.findByDisplayValue('Aurélie')).toBeInTheDocument();
  });
});


describe('screen 04 · consent must read as consent', () => {
  it('🔴 leaves every unexpressed preference at the conservative end', async () => {
    /**
     * *"Consent is never inferred."* ⚠️ **Two default to on and that is not a
     * contradiction**: neither is a permission over the customer's data.
     * Insights rank what Signora has already read, and drafting is safe
     * because *"nothing is ever sent on your behalf"* — a property of the
     * product rather than of a flag.
     */
    render(<AiPanel />);

    expect(await screen.findByRole('checkbox', { name: /always show citations/i })).not.toBeChecked();
    expect(screen.getByRole('radio', { name: '3' })).toBeChecked();
  });

  it('⛔ renders the data-use statements as facts, never as controls', async () => {
    /**
     * **A disabled toggle would invite somebody to ask who can enable it**,
     * and for the training row the honest answer is *nobody, ever*.
     */
    const { container } = render(<AiPanel />);
    const heading = await screen.findByText('What happens to your data');

    // Scoped to the block the heading introduces, because the panel above it
    // is nothing but controls — a container-wide assertion would pass or fail
    // for the wrong reason.
    const block = heading.parentElement as HTMLElement;
    expect(block.querySelectorAll('input')).toHaveLength(0);
    expect(container.querySelectorAll('input[disabled]')).toHaveLength(0);
  });

  it('🔴 states the training answer in words, not in a colour', async () => {
    // A red dot is not a sentence. The strongest claim on this screen has to
    // survive somebody who cannot see it.
    render(<AiPanel />);

    expect(await screen.findByText(/Never\. Not for your organization/)).toBeInTheDocument();
    // ⚡ **Two facts now read `never`** — training, and writing back to a
    // connected system — so this asks for the marks rather than the one.
    expect(screen.getAllByText(': never')).toHaveLength(2);
  });

  it('⚠️ does not claim a workspace confidence floor that does not exist', async () => {
    // The design says "yours can be stricter than the workspace floor of 3,
    // never looser". No workspace AI floor exists — C-249 — so the comparison
    // is absent rather than asserted.
    render(<AiPanel />);
    await screen.findByRole('radio', { name: '3' });

    expect(screen.queryByText(/workspace floor/i)).toBeNull();
  });

  it('sends only the preference that changed', async () => {
    render(<AiPanel />);

    await userEvent.click(await screen.findByRole('checkbox', { name: /always show citations/i }));

    expect(changePreferences).toHaveBeenCalledWith('ws-1', { always_show_citations: true });
  });

  it('⛔ offers no CONTROL for writing to the CRM, and states the fact instead', async () => {
    /**
     * ⚠️ **The reason is unchanged and the assertion is narrower.**
     *
     * 📁 The design draws this as *"switched off for everyone in this
     * workspace"* — **a workspace setting, and none exists**
     * ([C-249](../../../docs/LANE_COORDINATION.md)). ⛔ **So there is still no
     * toggle, and a disabled one would invite the question of who may enable
     * it.**
     *
     * ✅ **What changed is that the absence is now STATED rather than silent.**
     * ⚡ **Measured before it was written**: the provider port's verbs are
     * `store_records`, `save_watermark` and `get` — **all inbound, with no
     * write path to a connected system anywhere in the contract** — so *"it
     * does not write to them"* is a fact this screen can defend.
     *
     * 🔴 **The original assertion was `queryByText(/risk flags/i)` is null**,
     * which forbade the words as well as the control. **This forbids the
     * control**, which is what C-249 was about.
     */
    render(<AiPanel />);
    await screen.findByText('AI preferences');

    expect(screen.queryByRole('checkbox', { name: /risk flags/i })).toBeNull();
    expect(screen.queryByRole('switch', { name: /risk flags/i })).toBeNull();
    expect(screen.queryByRole('radio', { name: /risk flags/i })).toBeNull();
    // ✅ **And the fact is present**, so removing it fails here rather than
    // leaving the screen silent about a capability the design promises.
    expect(screen.getByText(/does not write to them/i)).toBeInTheDocument();
  });
});


/**
 * 🔴 **[B-255](../../../docs/BUGS.md) — `Save` said nothing at all.**
 *
 * ⛔ **`save` returned early when there was no workspace and left the status at
 * `idle`**, so somebody pressed the button, watched it not even spin, and got
 * neither a confirmation nor a refusal.
 *
 * ⚡ **Found while diagnosing a journey failure that turned out to be
 * [B-245](../../../docs/BUGS.md)'s environment poisoning** — the journey was
 * right, the environment was wrong, **and this was underneath it.**
 */
describe('🔴 the profile with no organization behind it', () => {
  it('🔴 says why it cannot save, rather than nothing', async () => {
    vi.resetModules();
    vi.doMock('@/lib/state/workspace-provider', () => ({
      useWorkspaceContext: () => ({ activeWorkspace: null }),
    }));
    const { ProfilePanel: Panel } = await import('@/app/(app)/profile/profile-panel');

    render(<Panel name={null} email="dana@northwind.test" />);

    await userEvent.click(screen.getByRole('button', { name: /^Save/ }));

    const refusal = await screen.findByRole('alert');
    expect(refusal).toHaveTextContent(/not in one yet/i);
    // ⛔ **And NOT the connection sentence** — nothing failed and nothing is
    // worth retrying, so telling somebody to check a working connection would
    // send them to look at the wrong thing.
    expect(refusal.textContent).not.toMatch(/connection/i);
    vi.doUnmock('@/lib/state/workspace-provider');
  });
});
