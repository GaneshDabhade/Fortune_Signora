'use client';

import { forwardRef } from 'react';

import { COMPOSITION_NAME, type Composition } from '@/lib/home/composition';
import { HM_COPY_01, HM_COPY_03 } from '@/lib/home/copy';

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
  /**
   * 🔴 **Whether the composition has actually been RESOLVED.**
   *
   * ⛔ `composition` alone cannot say. 📁 Rule 1's input is *"has any integration
   * ever completed a sync"*, which is a read — and until it lands the resolver
   * falls through to rule 5, **so `seller` means both *"resolved: seller"* and
   * *"not yet known"*.** ⚠️ Naming the wrong composition on the scope line is
   * the same class of claim as rendering `0` for a count that has not arrived.
   */
  readonly compositionKnown: boolean;
  /** `null` while the attention read is in flight. ⛔ **Never rendered as 0.** */
  readonly attention: number | null;
  readonly attentionFailed: boolean;
  /** ⛔ **`null` always today** — no calendar producer exists, and the design's
   *  *"2 meetings"* clause is omitted rather than guessed. */
  readonly meetings: number | null;
  /**
   * 🔴 **States 01 and 03 — the activation greeting.**
   *
   * 📁 The states table ties the sentence to what is complete rather than to the
   * clock: state 01 *"three activation cards, none complete… greeting reads 'Let
   * us get Northwind Global connected'"*, state 03 *"at least one blocking card
   * complete, at least one incomplete"* → `HM-COPY-03`.
   *
   * ⛔ **`null` on every data composition**, where the greeting is the time of
   * day and a name. ⚡ **And `null` until activation has resolved**, because
   * opening with *"let us get you connected"* to somebody who already has is the
   * one thing the sentence must never do.
   */
  readonly activation: ActivationGreeting | null;
}

/** What states 01 and 03 need, and nothing else. */
export interface ActivationGreeting {
  /** Blocking steps completed. `0` is state 01; `≥1` with work left is state 03. */
  readonly done: number;
  readonly total: number;
}

export const HomeGreeting = forwardRef<HTMLHeadingElement, HomeGreetingProps>(
  function HomeGreeting(
    {
      name,
      workspace,
      composition,
      compositionKnown,
      attention,
      attentionFailed,
      meetings,
      activation,
    },
    ref,
  ) {
    return (
      <div className="min-w-[15rem] flex-1">
        {/* ♿ **`tabIndex={-1}`** so entry can move focus here without putting the
            heading in the tab order — 📁 2.4.3, the same pattern onboarding uses. */}
        <h1
          ref={ref}
          tabIndex={-1}
          className="text-title font-bold leading-tight tracking-[-0.028em] text-content outline-none"
        >
          {activation === null || workspace === null
            ? `${greet()}${name === null ? '' : `, ${firstName(name)}`}`
            : /* 📁 **The whole greeting is replaced, not appended to.** ⛔ *"Good
                 afternoon, Dana — let us get you connected"* would be two
                 openings; the design gives state 01 one sentence. */
              activationSentence(workspace, activation)}
        </h1>
        {/* ♿ **One announcement per entry, never one per card** — 📁 4.1.3 and
            contract item 19. ⚡ This line carries workspace, composition and count,
            which is exactly the sentence the design says a reader hears once. */}
        <p
          aria-live="polite"
          className="mt-1.5 text-sm text-content-muted"
        >
          {[
            today(),
            workspace === null
              ? null
              : compositionKnown
                ? `${workspace} · ${COMPOSITION_NAME[composition]}`
                : // ⛔ **The workspace alone until the composition is known.** ⚡ The
                  // name is session data and needs no query; the composition is a
                  // read, and stating the fallback would name a composition this
                  // person may not be in.
                  workspace,
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

/**
 * 📁 **States 01 and 03**, chosen by what is complete.
 *
 * ⛔ **The `minutes` estimate is `null`** — 📁 *"the estimate comes from measured
 * p50 completion time, not a guess"*, and nothing measures one. The copy helper
 * omits the clause rather than inventing a figure.
 */
function activationSentence(workspace: string, { done, total }: ActivationGreeting): string {
  // ⚡ **`done === 0` is state 01 even when the roster has grown**, because the
  // states table ties the sentence to *"none complete"* rather than to the
  // member count — the member count decides which CARDS show, which is the
  // activation registry's business and not the greeting's.
  if (done === 0) return HM_COPY_01(workspace, total, null);
  return HM_COPY_03(workspace, Math.min(done + 1, total), total, null);
}

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
