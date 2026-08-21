'use client';

import { usePathname, useRouter, useSearchParams } from 'next/navigation';

import { cn } from '@/lib/design/cn';

import { AccessibilityPanel } from './accessibility-panel';
import { AiPanel } from './ai-panel';
import { AppearancePanel } from './appearance-panel';
import { AvatarArea } from './avatar-area';
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
  { id: 'profile', label: 'Profile' },
  { id: 'language', label: 'Language & region' },
  { id: 'appearance', label: 'Appearance' },
  { id: 'accessibility', label: 'Accessibility' },
  { id: 'shortcuts', label: 'Keyboard shortcuts' },
  { id: 'ai', label: 'AI preferences' },
  { id: 'accounts', label: 'Connected accounts' },
  { id: 'activity', label: 'Activity & security' },
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
        // 📁 ***"grid-template-columns:212px 1fr"***. ⚡ **One column below
        // `smalllaptop`**, which is this product's own band — ⛔ not a new
        // breakpoint, and not Tailwind's `sm:`, which generates no CSS here.
        'grid grid-cols-1 smalllaptop:grid-cols-[212px_1fr]',
      )}
    >
      <nav
        aria-label="Profile settings"
        className={cn(
          'bg-canvas px-3.5 py-5',
          // ⚡ **A right border on wide, a bottom border when stacked** — the
          // divider follows the axis rather than disappearing.
          'border-b border-border-soft smalllaptop:border-b-0 smalllaptop:border-r',
        )}
      >
        <ul className="flex flex-col gap-0.5">
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
        <div className="mt-5 rounded-md bg-surface-sunken p-3">
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
        {current === 'accounts' || current === 'activity' ? (
          <SectionNotBuilt section={current} />
        ) : null}
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
function SectionNotBuilt({ section }: { section: string }) {
  const WHAT: Record<string, string> = {
    accounts:
      'The accounts you have connected, their scope, and every session signed in as you.',
    activity:
      'What you have done in Signora, what is visible to others, and your data rights.',
  };
  return (
    <div className="rounded-md border border-border-soft bg-surface-sunken p-5">
      <p className="text-sm leading-6 text-content-muted">{WHAT[section]}</p>
      <p className="mt-2 text-xs leading-5 text-content-subtle">
        This section is not built yet.
      </p>
    </div>
  );
}
