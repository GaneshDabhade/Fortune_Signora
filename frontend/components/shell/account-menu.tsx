'use client';

import Link from 'next/link';
import { useEffect, useRef, useState, type ReactNode } from 'react';

import { ThemeToggle } from '@/components/shell/theme-toggle';
import { Avatar } from '@/components/ui';
import { cn } from '@/lib/design/cn';
import { SLOT_SPEC } from '@/lib/shell/top-bar';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';
import type { WorkspaceRole } from '@/lib/state/permissions';

/**
 * **The top bar's fifth slot** — [TASK-1440](../../../docs/BACKLOG.md), against
 * 📁 `docs/design-snapshot/screens/Fortune Signora App Shell.dc.html`
 * ([D-138](../../../docs/DECISION_REGISTER.md)).
 *
 * > 📁 ***"Help & account · 32 + 32 · Help before account, always last. Avatar
 * > is the only circle in the shell."***
 *
 * ## ⚡ This is where `Sign out` goes, and that is the whole point of the row
 *
 * 📁 **[TASK-1440](../../../docs/BACKLOG.md) names its own risk**: ⛔ *"keeping
 * `Sign out` visible because removing it feels like a regression."* **It is not
 * a regression, because the control does not disappear — it moves to where the
 * design puts it**, one click behind the avatar, 📁 *"below a hairline"* and
 * *"the only red text"*.
 *
 * ⚠️ **And the frame it leaves was breaking a rule the shell publishes as
 * code.** 📁 `lib/shell/constitution.ts` exports rule 02 — *"No module may add
 * anything to the top bar"* — while a theme toggle and a sign-out button sat in
 * it. ✅ **Both are inside this menu now**, which is the design's answer for
 * both.
 *
 * ## 📁 The design's layout, followed rather than approximated
 *
 * ***"280px, right-aligned to the avatar, 8px below the top bar. Identity
 * block, appearance control, six items, then sign out below a hairline."***
 * ⚡ **Every number here is that sentence.**
 *
 * ## ⛔ Three of the six items have no destination, and they are ABSENT
 *
 * ✅ **Measured against the route tree, not assumed** — `/profile`,
 * `/settings/organization` and `/settings/team` exist; **notification
 * settings, keyboard shortcuts and *what's new* have no route.** ⛔ **They are
 * not rendered disabled and not rendered as *coming soon*.**
 *
 * 📁 **[`navigation.tsx`](navigation.tsx) already paid for the alternative and
 * recorded the price**: *"an entry that leads nowhere advertises absence —
 * three of six said coming soon on the screen a customer sees first."*
 * ⚡ **Three of six again, and the same answer.**
 * ⛔ **[C-269](../../../docs/LANE_COORDINATION.md) carries the general case.**
 */

/**
 * 📁 **The design's six items.** ⛔ **`href: null` means the destination does
 * not exist, and an item with no destination is not rendered** — the field is
 * here rather than the list being pre-filtered so **the absence is visible to
 * the next reader** instead of looking like the design has three items.
 */
const ITEMS: readonly { label: string; href: string | null }[] = [
  { label: 'Profile & preferences', href: '/profile' },
  { label: 'Notification settings', href: null },
  // ⚠️ **The design's label is *"Workspace settings"* and this says
  // *organization*.** ⛔ **Not a liberty** — 📁 `vocabulary.test.tsx` fails the
  // build on *workspace* in a string a customer reads, because **ADR-0034
  // renamed it outward and forbade the rename travelling inward.** ⚡ The route
  // is still `/settings/organization`, and the shell already says *"your
  // organizations"* three feet away; **two words for one thing on one screen is
  // worse than diverging from the design's caption.**
  { label: 'Organization settings', href: '/settings/organization' },
  { label: 'Members & roles', href: '/settings/team' },
  { label: 'Keyboard shortcuts', href: null },
  { label: "What's new", href: null },
];

export interface AccountMenuProps {
  /** 📁 *"Always states name, email, role and workspace."* */
  email: string;
  role: WorkspaceRole | null;
  /**
   * ⚡ **The sign-out control, passed in rather than built here.**
   * ⛔ **Its markup lives in `app/(app)/authenticated-shell.tsx`, which is
   * OUTSIDE this row's 🟢 `components/shell/**` budget** — so this slot gives
   * it the design's position and does not re-author it. ⚠️ **Its internal
   * arrangement still differs from the design's *only red text* and is a
   * finding to raise, not an edit to make here.**
   */
  signOut: ReactNode;
}

export function AccountMenu({ email, role, signOut }: AccountMenuProps) {
  const [open, setOpen] = useState(false);
  const { activeWorkspace } = useWorkspaceContext();
  const containerRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  // 📁 *"Esc closes and returns focus to the avatar."* ⚡ **Returning focus is
  // the half that is usually dropped**, and without it a keyboard user who
  // closes the menu is returned to the top of the document.
  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== 'Escape') return;
      setOpen(false);
      triggerRef.current?.focus();
    };
    const onPointer = (event: MouseEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener('keydown', onKey);
    document.addEventListener('mousedown', onPointer);
    return () => {
      document.removeEventListener('keydown', onKey);
      document.removeEventListener('mousedown', onPointer);
    };
  }, [open]);


  return (
    <div ref={containerRef} className="relative">
      <button
        ref={triggerRef}
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-haspopup="menu"
        // ♿ The control names the person, not the glyph. An avatar labelled
        // "avatar" tells a screen reader user nothing they can act on.
        aria-label={`Account menu for ${email}`}
        style={{ width: SLOT_SPEC.account.width, height: SLOT_SPEC.account.height }}
        className={cn(
          'flex shrink-0 items-center justify-center rounded-full',
          'transition-colors hover:text-content',
          'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2',
          'focus-visible:outline-accent',
        )}
      >
        {/* ⚡ **The shared `Avatar`** — [TASK-1448](../../../docs/BACKLOG.md).
            ⛔ **This circle was drawn by hand here** because `components/ui`
            had no avatar when [TASK-1440](../../../docs/BACKLOG.md) built the
            slot. ✅ **`decorative` because the button already carries the
            accessible name** — announcing the initials and then the address
            would read the same person twice. */}
        <Avatar name={email} decorative />
      </button>

      {open ? (
        <div
          role="menu"
          aria-label="Account"
          // 📁 *"280px, right-aligned to the avatar, 8px below the top bar."*
          className="absolute right-0 top-[calc(100%+8px)] z-20 w-[280px] rounded-md border border-border bg-surface shadow-lg"
        >
          {/* 📁 *"Always states name, email, role and workspace."*
              ⛔ **Name is not stated, because the platform does not publish
              one** — the session carries an email and nothing else. ⚡ Inventing
              a display name from the local part would be the shell asserting a
              fact about a person it does not have. */}
          <div className="border-b border-border px-3 py-3">
            <p className="truncate text-sm font-medium text-content" title={email}>
              {email}
            </p>
            <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
              {/* 📁 *"Role is a brand-tint chip so permission questions are
                  answered without navigating."* ⛔ Absent rather than guessed
                  while the role is still resolving. */}
              {role ? (
                <span className="rounded bg-accent-subtle px-1.5 py-0.5 text-xs font-medium capitalize text-accent">
                  {role}
                </span>
              ) : null}
              {activeWorkspace ? (
                <span className="truncate text-xs text-content-muted">
                  {activeWorkspace.name}
                </span>
              ) : null}
            </div>
          </div>

          {/* ── The appearance control ────────────────────────────────────
              📁 *"Theme as a three-way control makes 'follow the OS'
              discoverable rather than hidden."*

              ⛔ **`ThemeToggle` is REUSED, not reimplemented.** ⚡ **A
              hand-rolled three-way control was written here first and a guard
              caught it**: 📁 `design-tokens.test.tsx` — *"only the toggle
              itself may know a theme exists. Any other component branching on
              it would need editing when a third theme is added."* ✅ **The
              guard was right and the duplicate is gone** — this slot supplies
              the design's POSITION for the control, and the control is the one
              that already existed. */}
          <div className="border-b border-border px-3 py-2.5">
            <p className="mb-1.5 text-xs font-medium uppercase tracking-wide text-content-subtle">
              Appearance
            </p>
            <ThemeToggle />
          </div>

          <div className="py-1">
            {ITEMS.filter((item) => item.href !== null).map((item) => (
              <Link
                key={item.label}
                href={item.href as string}
                role="menuitem"
                onClick={() => setOpen(false)}
                className="block px-3 py-2 text-sm text-content-muted transition-colors hover:bg-surface-sunken hover:text-content focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-accent"
              >
                {item.label}
              </Link>
            ))}
          </div>

          {/* 📁 *"then sign out below a hairline."* */}
          <div className="border-t border-border px-3 py-2.5">{signOut}</div>
        </div>
      ) : null}
    </div>
  );
}

/**
 * ⚡ **Exported for the slot test only** — it asserts the design's list against
 * this one rather than against a copy of it, so 📁 [D-137](../../../docs/DECISION_REGISTER.md)'s
 * *"the copy is always the one somebody reads"* does not apply to the test.
 */
export const ACCOUNT_MENU_ITEMS = ITEMS;
