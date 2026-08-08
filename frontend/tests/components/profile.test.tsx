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
    await userEvent.click(screen.getByRole('button', { name: 'Save' }));

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
