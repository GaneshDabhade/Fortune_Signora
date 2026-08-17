'use client';

import { forwardRef } from 'react';

import { COMPOSITION_NAME, type Composition } from '@/lib/home/composition';

/**
 * 📁 **Home's greeting and scope line** — `Fortune Signora Home.dc.html`
 * hierarchy 3: *"Name, date, and a count of what needs attention. The count is
 * the smallest useful summary and **replaces a metrics row**."*
 *
 * ### ⛔ Never skeletonised
 *
 * 📁 §09: *"Real immediately, from session data. Never skeletonised — the name
 * and date need no query."* ⚡ **The COUNT is the only part that waits**, and
 * while it waits it says nothing rather than `0` — 📁 *"never shown as 0 while
 * loading."*
 *
 * ### ⚠️ No exclamation mark, and no "Welcome back"
 *
 * 📁 The design bans both by name, along with *"You're all caught up!"*. ⚡ **The
 * greeting is the time of day and a name**, which is what a colleague says.
 */
export interface HomeGreetingProps {
  readonly name: string | null;
  readonly workspace: string | null;
  readonly composition: Composition;
  /** `null` while the attention read is in flight. ⛔ **Never rendered as 0.** */
  readonly attention: number | null;
  readonly attentionFailed: boolean;
  /** ⛔ **`null` always today** — no calendar producer exists, and the design's
   *  *"2 meetings"* clause is omitted rather than guessed. */
  readonly meetings: number | null;
}

export const HomeGreeting = forwardRef<HTMLHeadingElement, HomeGreetingProps>(
  function HomeGreeting({ name, workspace, composition, attention, attentionFailed, meetings }, ref) {
    return (
      <div className="min-w-[15rem] flex-1">
        {/* ♿ **`tabIndex={-1}`** so entry can move focus here without putting the
            heading in the tab order — 📁 2.4.3, the same pattern onboarding uses. */}
        <h1
          ref={ref}
          tabIndex={-1}
          className="text-[27px] font-bold leading-tight tracking-[-0.028em] text-content outline-none"
        >
          {greet()}
          {name === null ? '' : `, ${firstName(name)}`}
        </h1>
        {/* ♿ **One announcement per entry, never one per card** — 📁 4.1.3 and
            contract item 19. ⚡ This line carries workspace, composition and count,
            which is exactly the sentence the design says a reader hears once. */}
        <p
          aria-live="polite"
          className="mt-1.5 text-[13px] text-content-muted"
        >
          {[
            today(),
            workspace === null ? null : `${workspace} · ${COMPOSITION_NAME[composition]}`,
            scope(attention, attentionFailed),
            meetings === null ? null : `${meetings} meetings`,
          ]
            .filter((part): part is string => part !== null)
            .join(' · ')}
        </p>
      </div>
    );
  },
);

/** 📁 *"Good morning, Aurélie"* — the design's own greeting, by the clock. */
function greet(): string {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 18) return 'Good afternoon';
  return 'Good evening';
}

/** 📁 *"Thursday 13 August"* — weekday, day, month, and no year. */
function today(): string {
  return new Intl.DateTimeFormat(undefined, {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  }).format(new Date());
}

/**
 * 📁 *"3 things need you today"*.
 *
 * ⛔ **Silent while unknown, and honest when the read failed.** ⚠️ Rendering
 * *"0 things need you"* from a failed read is [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md)
 * in the one place a reader would trust it most.
 */
function scope(attention: number | null, failed: boolean): string | null {
  if (failed) return 'we could not check what needs you';
  if (attention === null) return null;
  if (attention === 0) return 'nothing needs you today';
  return `${attention} ${attention === 1 ? 'thing needs' : 'things need'} you today`;
}

/** ⚡ **The first name only.** 📁 The design greets *"Aurélie"*, not a full name. */
function firstName(name: string): string {
  return name.trim().split(/\s+/)[0] ?? name;
}
