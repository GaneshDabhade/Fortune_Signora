'use client';

import { usePathname, useRouter, useSearchParams } from 'next/navigation';

import { cn } from '@/lib/design/cn';

import { AccessibilityPanel } from './accessibility-panel';
import { AiPanel } from './ai-panel';
import { AppearancePanel } from './appearance-panel';
import { AvatarArea } from './avatar-area';
import { ConnectedAccountsPanel } from './connected-accounts-panel';
import { DataRightsPanel } from './data-rights-panel';
import { LocalePanel } from './locale-panel';
import { ProfilePanel } from './profile-panel';
import { ShortcutsPanel } from './shortcuts-panel';

/**
 * **The finalized User Profile design's `ProfileShell`.**
 *
 * 📁 `Fortune Signora User Profile.dc.html` — ***"display:grid;
 * grid-template-columns:212px 1fr"***, the rail on `--bg-rail` behind a
 * `--line-soft` right border, inside one 16px card.
 *
 * ## 🔴 Why this replaces the previous layout rather than sitting beside it
 *
 * ⛔ **The page was one long column of panels.** ⚡ **That is not a smaller
 * version of this design; it is a different information architecture** — the
 * design's sections are *destinations behind a rail*, and stacking them makes
 * every one of them scroll past a reader who wanted one.
 *
 * ⚠️ **So the stack is gone rather than wrapped.** 📁 [§20c](../../../../CLAUDE.md)
 * and the standing correction: *do not create a hybrid of the old
 * implementation and the final design.*
 *
 * ## ⚡ The rail is the design's, not the shell's
 *
 * ⛔ **This is NOT `components/shell/navigation.tsx`.** 📁 The application rail
 * carries nine product destinations; **this one carries the eight sections of
 * one screen**, and reusing the shell's would put a screen's internal
 * structure into the product's global navigation.
 *
 * ## 🔴 The section lives in the URL
 *
 * ⚡ **So a section is linkable, survives a reload, and the back button works**
 * — 📁 the same reason the account brief's expansion is a query parameter
 * rather than component state. ⛔ **An unknown section falls back to the first
 * rather than rendering nothing**: an identifier this screen has never heard of
 * is not evidence that a section exists.
 */

export interface ProfileSection {
  readonly id: string;
  readonly label: string;
  /**
   * ⚡ **Whether the product can fill this section today** — the same contract
   * [`SettingsSection`](../../../lib/settings/sections.ts) and
   * [`AccountSection`](../../../lib/accounts/sections.ts) already carry.
   *
   * ⛔ **Added because a section was MISSING from this list entirely** —
   * 📁 the design's `nav` declares **nine** and this declared **eight**, with
   * *Notifications* absent from the register rather than marked absent in it.
   * ⚠️ **Which is indistinguishable from a bug to the next reader**, and is the
   * failure Account 360's registry states in its own words.
   */
  readonly supply: 'supplied' | 'absent';
  /**
   * 📁 **What a customer is told where the section cannot be filled.**
   * ⛔ **Required when `absent`**, and it says what the section would show and
   * what Signora cannot do yet — ⛔ **never what the READER has not set up**,
   * 📁 [B-299](../../../../docs/BUGS.md) ⑦.
   *
   * ⚡ **One source.** ⛔ `SectionNotBuilt` held its own `WHAT` map, so the
   * sentence lived here and there — **two representations of one string**
   * ([§2](../../../../CLAUDE.md)).
   */
  readonly absence?: string;
}

/**
 * 📁 **The design's `nav` array, in its order.**
 *
 * ⛔ **Eight entries, and every one is the design's.** ⚠️ **Keyboard shortcuts
 * IS one of them** — the design's `ShortcutTable` is a reference, and
 * `SHORTCUT_GROUPS` is the canonical source it will read. **Removing the
 * section because the shell has an overlay was the wrong correction**: the
 * design puts the reference here too, and one registry can feed two surfaces
 * without becoming two registries.
 */
export const PROFILE_SECTIONS: readonly ProfileSection[] = [
  { id: 'profile', label: 'Profile', supply: 'supplied' },
  { id: 'language', label: 'Language & region', supply: 'supplied' },
  { id: 'appearance', label: 'Appearance', supply: 'supplied' },
  { id: 'accessibility', label: 'Accessibility', supply: 'supplied' },
  { id: 'shortcuts', label: 'Keyboard shortcuts', supply: 'supplied' },
  { id: 'ai', label: 'AI preferences', supply: 'supplied' },
  /**
   * 🔴 **📁 The design's `nav` declares this and the register did not** —
   * seventh of nine, between *AI preferences* and *Connected accounts*.
   *
   * ⛔ **Measured, not assumed**: `workspace_tenancy`'s `Notifier` port
   * publishes **one verb and no channel adapters** — *"a request for an
   * unconfigured channel FAILS, and a default of `{IN_APP}` would be exactly
   * the fallback that rule refuses."* ⚡ **Three notification routes exist —
   * feed, read, unread — and all three are in-app.** ⛔ **No endpoint carries a
   * channel choice, a digest or a quiet-hours window.**
   */
  {
    id: 'notifications',
    label: 'Notifications',
    supply: 'absent',
    absence:
      'Which notifications reach you, where they go, and when they are held back. Signora notifies you in the app; it cannot yet send to email or Slack, or hold anything until you are ready to read it.',
  },
  { id: 'accounts', label: 'Connected accounts', supply: 'supplied' },
  {
    id: 'activity',
    label: 'Activity & security',
    // ⚡ **`supplied`, because one row of it IS built** — `DataRightsPanel`
    // renders above the notice. ⛔ **The section is not absent; part of it is**,
    // and the shell composes the two.
    supply: 'supplied',
  },
];

/** ⚡ **The design's own parameter-free default** — the first section. */
export const DEFAULT_SECTION = PROFILE_SECTIONS[0]!.id;

export const SECTION_PARAM = 'section';

/**
 * ⛔ **An unknown id resolves to the first section, never to nothing.**
 *
 * ⚡ **The same refusal the account brief makes** for a section identifier the
 * product has never heard of.
 */
export function resolveSection(asked: string | null): string {
  if (asked === null) return DEFAULT_SECTION;
  return PROFILE_SECTIONS.some((section) => section.id === asked)
    ? asked
    : DEFAULT_SECTION;
}

/**
 * ⚠️ **The sections are rendered HERE rather than by a child function.**
 *
 * 🔴 **`page.tsx` is a server component, and a function cannot cross the
 * server/client boundary** — passing `children: (section) => ReactNode` made
 * the whole route fail to render, which the headed journey caught as *"Your
 * profile" not found*. ⚡ **The identity comes across as two strings instead**,
 * which serializes, and the switch lives on this side of the line.
 */
export function ProfileShell({ name, email }: { name: string | null; email: string }) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const current = resolveSection(params.get(SECTION_PARAM));

  const go = (id: string) => {
    const next = new URLSearchParams(params.toString());
    if (id === DEFAULT_SECTION) next.delete(SECTION_PARAM);
    else next.set(SECTION_PARAM, id);
    const query = next.toString();
    router.replace(query === '' ? pathname : `${pathname}?${query}`, { scroll: false });
  };

  return (
    <div
      className={cn(
        'overflow-hidden rounded-lg border border-border-soft bg-surface shadow-sm',
        // 📁 ***"grid-template-columns:212px 1fr"***.
        //
        // 🔴 **[B-298](../../../../docs/BUGS.md) — `laptop:`, not
        // `smalllaptop:`.** 📁 **`Fortune Signora User Profile` gives THREE
        // bands and this had two**: *"≥ 1280px — **212px rail** beside a
        // two-column form"*, *"768–1279px — **Rail becomes a horizontal
        // scroller of section chips**"*, and a mobile treatment below that.
        // ⛔ **`smalllaptop:` handed 1024–1279 the desktop layout**, so the
        // whole middle band was drawn as something the design draws at no
        // width — the identical defect the Settings rail had, one screen over.
        'grid grid-cols-1 laptop:grid-cols-[212px_1fr]',
      )}
    >
      <nav
        aria-label="Profile settings"
        className={cn(
          'bg-canvas px-3.5 py-5',
          // ⚡ **A right border beside the content, a bottom border above it** —
          // the divider follows the axis rather than disappearing. ⛔ **The
          // scroller band is ABOVE**, so it keeps the bottom border.
          'border-b border-border-soft laptop:border-b-0 laptop:border-r',
        )}
      >
        {/* 📁 *"Rail becomes a horizontal scroller of section chips"* at
            `768–1279px`. ⛔ **`shrink-0` on every chip**: a flex row allowed to
            shrink does not scroll, it compresses — which is the truncation the
            design rules out by name. */}
        <ul
          className={cn(
            'flex flex-col gap-0.5',
            'tablet:flex-row tablet:items-center tablet:gap-1.5 tablet:overflow-x-auto',
            'laptop:flex-col laptop:items-stretch laptop:gap-0.5 laptop:overflow-x-visible',
          )}
        >
          {PROFILE_SECTIONS.map((section) => {
            const selected = section.id === current;
            return (
              <li key={section.id}>
                <button
                  type="button"
                  onClick={() => go(section.id)}
                  // ♿ **The selected state is announced, not only tinted.**
                  aria-current={selected ? 'page' : undefined}
                  className={cn(
                    'w-full rounded-md px-2.5 py-1.5 text-left text-sm',
                    'tablet:w-auto tablet:shrink-0 tablet:whitespace-nowrap',
                    'laptop:w-full',
                    selected
                      ? 'bg-surface font-semibold text-content shadow-sm'
                      : 'font-medium text-content-muted hover:bg-surface hover:text-content',
                  )}
                >
                  {section.label}
                </button>
              </li>
            );
          })}
        </ul>

        {/* 📁 **The design's own block, verbatim, beneath the rail.** ⚡ **It is
            the screen's one privacy claim** and it belongs where a reader is
            deciding what to put in these fields. */}
        {/* ⛔ **Hidden in the scroller band, not deleted.** ⚡ A 3-line privacy
            block inside a horizontal chip rail would either force the rail
            taller than its chips or scroll away sideways; 📁 the design draws
            it *"beneath the rail"*, and in this band there is no beneath. It
            returns at `laptop:` where the rail is a rail again. */}
        <div className="mt-5 rounded-md bg-surface-sunken p-3 tablet:hidden laptop:block">
          <p className="text-xs font-semibold text-content">Yours alone</p>
          <p className="mt-1 text-xs leading-5 text-content-muted">
            Nothing on these pages is visible to other members except your name, avatar,
            title and department.
          </p>
        </div>
      </nav>

      <div className="min-w-0 p-5 smalllaptop:p-6">
        {current === 'profile' ? (
          <>
            <AvatarArea name={name} email={email} />
            <ProfilePanel name={name} email={email} />
          </>
        ) : null}
        {current === 'language' ? <LocalePanel /> : null}
        {current === 'appearance' ? <AppearancePanel /> : null}
        {current === 'accessibility' ? <AccessibilityPanel /> : null}
        {current === 'ai' ? <AiPanel /> : null}
        {/* ✅ **Built** — the registry the `?` overlay reads, rendered by the
            component they now share. ⛔ **No *Customise* control**: the design's
            conflict rule describes an editor, and no preference field or
            endpoint stores a binding. */}
        {current === 'shortcuts' ? <ShortcutsPanel /> : null}
        {/* 🔴 **The design's seventh nav entry, stated rather than omitted.**
            ⛔ **It was missing from `PROFILE_SECTIONS` entirely**, so the rail
            had eight where the design draws nine — and an omitted section is
            indistinguishable from a broken one. */}
        {current === 'notifications' ? <SectionAbsence section="notifications" /> : null}
        {/* 🔴 **Activity is PART built now, and the split is the point.** 📁
            The design's Activity screen holds a timeline, a visibility table
            and the *"Your data"* block. ✅ **One row of that block is
            producer-backed and shipped** — leaving the organization, unblocked
            by [C-207](../../../docs/LANE_COORDINATION.md)'s closure. ⛔ **The
            rest still says so**, rather than the whole section claiming to be
            unbuilt while a live control sits inside it. */}
        {current === 'activity' ? (
          <div className="flex flex-col gap-6">
            <DataRightsPanel />
            <ActivityNotBuilt />
          </div>
        ) : null}
        {/* 🔴 **Was `SectionNotBuilt`, and the notice was untrue.** ⚡ It
            claimed *"every session signed in as you"* was unbuilt while the
            card at the foot of this same screen links to it. **Half of §05 is
            shipped and half has no producer**, and the section now says which
            is which — 📁 [§2](../../../../CLAUDE.md). */}
        {current === 'accounts' ? <ConnectedAccountsPanel /> : null}
      </div>
    </div>
  );
}

/**
 * ⚡ **A section the design defines and this slice has not built.**
 *
 * ⛔ **Not *coming soon*** — 📁 `navigation.tsx` already paid for that wording.
 * ✅ **It says what the section will hold**, so the rail describes the screen
 * honestly while the remaining slices land.
 */
/**
 * ⚡ **A whole section the product cannot fill, in the register's own words.**
 *
 * ⛔ **The sentence comes from `PROFILE_SECTIONS`, never from a map here** —
 * this component previously held its own `WHAT` lookup, **which is one string
 * in two places** ([§2](../../../../CLAUDE.md)) and the shape that lets a rail
 * entry and its panel eventually disagree.
 *
 * ⛔ **And it does NOT say *"not built yet"***. 📁 The registry rule the rest of
 * the product follows: *"an absent section states what it would show and what
 * Signora cannot answer yet, in the customer's words"* — ⚠️ **never a status
 * report about the engineering backlog**, which is what *"not built yet"* is.
 */
function SectionAbsence({ section }: { section: string }) {
  const declared = PROFILE_SECTIONS.find((entry) => entry.id === section);
  if (declared?.absence === undefined) return null;
  return (
    <div className="rounded-md border border-border-soft bg-surface-sunken p-5">
      <p className="text-sm leading-6 text-content-muted">{declared.absence}</p>
    </div>
  );
}

/**
 * 🔴 **Activity's PARTIAL absence, and it is a different sentence from a whole
 * one.** 📁 `DataRightsPanel` renders above this — **one row of the design's
 * *"Your data"* block is producer-backed and shipped** — so the notice names
 * what is still missing rather than claiming the section is empty.
 */
function ActivityNotBuilt() {
  return (
    <div className="rounded-md border border-border-soft bg-surface-sunken p-5">
      <p className="text-sm leading-6 text-content-muted">
        What you have done in Signora, and what is visible to others.
      </p>
      <p className="mt-2 text-xs leading-5 text-content-subtle">
        Signora does not record a personal activity history yet.
      </p>
    </div>
  );
}
