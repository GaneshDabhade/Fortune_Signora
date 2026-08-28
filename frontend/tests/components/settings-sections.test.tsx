/**
 * 📁 **The Settings navigation and its section shells** — `Fortune Signora
 * Settings`.
 *
 * ⛔ **323 lines and nothing rendered them.** ⚡ **The screen's whole argument
 * is about ABSENCE** — ten of fourteen navigation items lead to a capability
 * this product does not have — **so the assertions that matter are about what
 * is drawn where nothing can fill it.**
 */
import { render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import {
  AbsentSettings,
  ElsewhereSettings,
  SettingsNav,
  SettingsSectionShell,
} from '@/components/settings/sections';
import { SETTINGS_NAV, SETTINGS_SECTIONS } from '@/lib/settings/sections';

const absent = SETTINGS_SECTIONS.find((s) => s.supply === 'absent');
const supplied = SETTINGS_SECTIONS.find((s) => s.supply === 'supplied');

describe('📁 the navigation lists every section, including the empty rooms', () => {
  it('⛔ draws all fourteen items, not only the four with a producer', () => {
    render(<SettingsNav />);
    const nav = screen.getByRole('navigation', { name: 'Settings sections' });

    const items = within(nav).getAllByRole('link');
    const expected = SETTINGS_NAV.flatMap((g) => g.items);
    expect(items).toHaveLength(expected.length);

    // 📁 *"a map that hides the empty rooms is one nobody can trust"* — the
    // rule Account 360's rail already follows.
    for (const item of expected) {
      expect(within(nav).getByRole('link', { name: item.label })).toBeInTheDocument();
    }
  });

  it('⚡ keeps the four groups, because collapsing the rail is not flattening it', () => {
    render(<SettingsNav />);
    const nav = screen.getByRole('navigation', { name: 'Settings sections' });
    for (const group of SETTINGS_NAV) {
      expect(within(nav).getByText(group.label)).toBeInTheDocument();
    }
  });

  it('⛔ marks NO item active, because the design specifies the look and not the rule', () => {
    /**
     * 📁 **The design states the appearance exactly** — `--brand-ink` on
     * `--brand-tint` at 600 — **and never says what MAKES an item active.**
     *
     * 🔴 **And its own navigation makes any anchor-derived rule ambiguous**:
     * *SSO* and *SCIM* both point at `#sso`, *API keys* and *Webhooks* both at
     * `#api`. ⛔ **Any rule reading the anchor marks TWO items active** and the
     * design shows one. ⚡ **Asserted here so a future scroll-spy cannot be
     * added without confronting the ambiguity.**
     */
    render(<SettingsNav />);
    const nav = screen.getByRole('navigation', { name: 'Settings sections' });

    expect(within(nav).queryByRole('link', { current: true })).toBeNull();
    for (const link of within(nav).getAllByRole('link')) {
      expect(link).not.toHaveAttribute('aria-current');
      expect(link.className).not.toContain('bg-accent-subtle');
    }

    // ⚠️ **The duplicate-anchor fact itself**, so the ambiguity is recorded
    // rather than remembered.
    const hrefs = within(nav).getAllByRole('link').map((a) => a.getAttribute('href'));
    expect(new Set(hrefs).size).toBeLessThan(hrefs.length);
  });

  it('⚡ every item points at a section that exists', () => {
    // ⛔ **A nav entry anchoring at nothing is a door to a wall**, and the
    // duplicate anchors above make that easy to introduce unnoticed.
    const ids = new Set(SETTINGS_SECTIONS.map((s) => s.id));
    for (const item of SETTINGS_NAV.flatMap((g) => g.items)) {
      expect(ids, `nav item "${item.label}" anchors at #${item.section}`).toContain(
        item.section,
      );
    }
  });
});

describe('♿ a section is a labelled region with a heading', () => {
  it('📁 names the region by its own heading, so landmark navigation reaches it', () => {
    if (supplied === undefined) throw new Error('no supplied section to render');
    render(
      <SettingsSectionShell section={supplied}>
        <p>body</p>
      </SettingsSectionShell>,
    );

    const region = screen.getByRole('region', { name: supplied.title });
    expect(region).toHaveAttribute('id', supplied.id);
    expect(within(region).getByRole('heading', { name: supplied.title })).toBeInTheDocument();
    expect(within(region).getByText(supplied.meta)).toBeInTheDocument();
    expect(within(region).getByText('body')).toBeInTheDocument();
  });
});

describe('🔴 an absent capability is stated, never drawn as a control', () => {
  it('⛔ renders the sentence and nothing operable', () => {
    if (absent === undefined) throw new Error('no absent section to render');
    render(<AbsentSettings section={absent} />);

    // ✅ **The pin** — something rendered, so the absences below are answers.
    expect(screen.getByText(absent.absence ?? '')).toBeInTheDocument();
    // 📁 *"do not create placeholder functionality that makes an unavailable
    // capability appear operational."*
    expect(screen.queryByRole('button')).toBeNull();
    expect(screen.queryByRole('textbox')).toBeNull();
    expect(screen.queryByRole('combobox')).toBeNull();
    expect(screen.queryByRole('switch')).toBeNull();
    expect(screen.queryByRole('checkbox')).toBeNull();
  });

  it('⚡ and renders NOTHING at all for a section that is supplied', () => {
    // ⛔ **The vacuity half.** Without it, every assertion above would pass on
    // a component that returns null unconditionally.
    if (supplied === undefined) throw new Error('no supplied section to render');
    const { container } = render(<AbsentSettings section={supplied} />);
    expect(container).toBeEmptyDOMElement();
  });

  it('⛔ every absent section says WHY, because a padlock without a reason is worse', () => {
    for (const section of SETTINGS_SECTIONS.filter((s) => s.supply === 'absent')) {
      expect(section.absence, `${section.id} is absent and states no reason`).toBeTruthy();
    }
  });
});

describe('⚡ a section whose detail lives elsewhere links somewhere real', () => {
  it('📁 renders the sentence and a link, not a disabled control', () => {
    render(
      <ElsewhereSettings href="/settings/team" label="Open team settings">
        Managing people happens on its own screen.
      </ElsewhereSettings>,
    );

    expect(screen.getByText('Managing people happens on its own screen.')).toBeInTheDocument();
    const link = screen.getByRole('link', { name: 'Open team settings' });
    expect(link).toHaveAttribute('href', '/settings/team');
  });
});

describe('⚡ ADR-0034 — the platform’s word never reaches a Settings screen', () => {
  it('⛔ neither a section heading nor a navigation group says workspace', () => {
    /**
     * 📁 **[ADR-0034](../../../docs/architecture/adr/0034-ubiquitous-language.md)**:
     * *"a customer says Organization; the platform says workspace… the
     * translation lives at the frontend edge."*
     *
     * ⚠️ **`vocabulary.test.tsx` walks `app` and `components`.** ⛔ **These
     * strings live in `lib/settings/sections.ts`**, which it does not walk —
     * ⚡ **so this is the render saying what a source guard scoped past.**
     */
    render(<SettingsNav />);
    const nav = screen.getByRole('navigation', { name: 'Settings sections' });
    expect(nav.textContent ?? '').not.toMatch(/workspace/i);

    for (const section of SETTINGS_SECTIONS) {
      const { container, unmount } = render(
        <SettingsSectionShell section={section}>
          <p>body</p>
        </SettingsSectionShell>,
      );
      expect(container.textContent ?? '', `section "${section.id}"`).not.toMatch(
        /workspace/i,
      );
      unmount();
    }
  });
});
