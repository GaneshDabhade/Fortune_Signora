/**
 * **Account 360's section rail, and the sections nothing can fill** —
 * [TASK-1415](../../../docs/BACKLOG.md), against 📁
 * `Fortune Signora Account 360.dc.html`.
 *
 * ## 🔴 Why an absent section is RENDERED rather than omitted
 *
 * 📁 **[§20c](../../../CLAUDE.md)**: *"screens without a shipped module behind
 * them ship a designed empty state."* ⛔ **And an omission is not one.**
 *
 * ⚠️ **Seven of the design's fifteen sections have nothing behind them**
 * ([`lib/accounts/sections.ts`](../../lib/accounts/sections.ts) is the
 * measurement). **A page that simply left them out would be
 * indistinguishable from a page with a bug** — a rep who has seen the design
 * would assume the screen was broken, and the next lane could not tell which
 * it was either.
 *
 * ✅ **So each says what it would show and what Signora cannot answer yet.**
 * ⛔ **Never *"coming soon"*** — 📁 the rail already paid for that once: *"at
 * M12.3, three of six said `coming soon` on the screen a customer sees
 * first."*
 */

'use client';

import { cn } from '@/lib/design/cn';
import { onThisPage, type AccountSection } from '@/lib/accounts/sections';

/**
 * 📁 **The design's *"On this page"* rail.**
 *
 * ⚡ **Every section, including the ones that cannot be filled**, because the
 * rail is a map of the record and a map that hides the empty rooms is one
 * nobody can trust — 📁 the same reasoning `rail.ts` records for a restricted
 * navigation destination: *"a hidden destination teaches a person the feature
 * does not exist, so they ask for the wrong thing or ask nobody."*
 */
export function OnThisPage({ className }: { className?: string }) {
  const sections = onThisPage();

  return (
    <nav aria-label="On this page" className={cn('flex flex-col gap-1', className)}>
      <p className="mb-1 text-2xs font-semibold uppercase tracking-wide text-content-subtle">
        On this page
      </p>
      {sections.map((section) => (
        <a
          key={section.id}
          href={`#${section.id}`}
          // ⛔ **A dimmed entry, never a hidden one.** ⚡ The design's own
          // treatment for a destination that exists and cannot be entered.
          className={cn(
            'rounded px-2 py-1 text-sm transition-colors',
            'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2',
            'focus-visible:outline-accent',
            section.supply === 'supplied'
              ? 'text-content-muted hover:bg-surface-sunken hover:text-content'
              : 'text-content-subtle hover:text-content-muted',
          )}
        >
          {section.label}
        </a>
      ))}
    </nav>
  );
}

/**
 * ⛔ **A section the platform cannot fill.**
 *
 * 🔴 **This is NOT an empty state and the difference is the whole component.**
 * 📁 [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md) applied one level up:
 * **an empty section means *this account has none*; an absent one means
 * *Signora cannot answer the question at all*** — and a rep who reads the
 * first when the second is true concludes their account is quiet, which is a
 * commercial decision made on a false reading.
 */
export function AbsentSection({ section }: { section: AccountSection }) {
  if (section.supply !== 'absent') return null;

  return (
    <section
      id={section.id}
      aria-labelledby={`${section.id}-heading`}
      className="flex flex-col gap-2"
    >
      <h2 id={`${section.id}-heading`} className="text-sm font-semibold text-content">
        {section.label}
      </h2>
      <div className="rounded-lg border border-dashed border-border-strong bg-surface px-4 py-4">
        {/* ⛔ **The sentence is the deliverable.** 📁 It says what the section
            would show and what is missing — never that it is *"coming soon"*,
            which tells somebody to wait without saying for what. */}
        <p className="text-sm leading-6 text-content-muted">{section.absence}</p>
      </div>
    </section>
  );
}
