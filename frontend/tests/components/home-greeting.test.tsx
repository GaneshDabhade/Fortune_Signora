/**
 * 📁 **Home's greeting and scope line** — `Fortune Signora Home.dc.html`
 * hierarchy 3: *"Name, date, and a count of what needs attention. The count is
 * the smallest useful summary and **replaces a metrics row**."*
 *
 * ⚡ **A greeting is where warmth outruns the facts.** 📁 The design bans
 * *"Welcome back"*, *"You're all caught up!"* and the exclamation mark **by
 * name** — ⛔ **and the count beneath it is a read that can fail**, on the first
 * line of the first screen, **which is the place a reader trusts most.**
 */
import { render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { HomeGreeting, type HomeGreetingProps } from '@/components/home/greeting';

/** ⚡ **A fixed clock**, so *"Good morning"* and the date are facts rather than
 *  whatever hour the suite happened to run at. */
const NOON = new Date('2026-08-13T13:00:00Z');

const BASE: HomeGreetingProps = {
  name: 'Aurélie Dubois',
  workspace: 'Northwind Global',
  composition: 'seller',
  compositionKnown: true,
  attention: 3,
  attentionFailed: false,
  meetings: null,
  activation: null,
};

function greeting(over: Partial<HomeGreetingProps> = {}) {
  return render(<HomeGreeting {...BASE} {...over} />);
}

/** 📁 The scope line — the one polite announcement per entry. */
function scope(): HTMLElement {
  const el = document.querySelector('[aria-live="polite"]');
  if (el === null) throw new Error('no polite live region — the scope line is the only one');
  return el as HTMLElement;
}

beforeEach(() => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  vi.setSystemTime(NOON);
});
afterEach(() => {
  vi.useRealTimers();
});

describe('⛔ the greeting is what a colleague says, and the design bans the rest by name', () => {
  it('📁 greets the time of day and a FIRST name', () => {
    greeting();
    // 📁 The design greets *"Aurélie"*, not a full name.
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Good afternoon, Aurélie');
    expect(screen.getByRole('heading', { level: 1 }).textContent ?? '').not.toContain('Dubois');
  });

  it('⛔ never says Welcome back, never claims you are caught up, never exclaims', () => {
    greeting();
    const text = document.body.textContent ?? '';

    expect(text).not.toMatch(/welcome back/i);
    expect(text).not.toMatch(/caught up/i);
    expect(text).not.toContain('!');
  });

  it('⚡ and greets without a name rather than inventing one', () => {
    greeting({ name: null });
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Good afternoon');
    expect(screen.getByRole('heading', { level: 1 }).textContent ?? '').not.toMatch(/,\s*$/);
  });
});

describe('🔴 P-A — the count is a read, and it has three different nothings', () => {
  it('⛔ says NOTHING while the count is unknown, never “0 things”', () => {
    greeting({ attention: null });

    // ✅ **The pin** — the line rendered, carrying the date.
    expect(scope().textContent ?? '').toMatch(/August/);
    expect(scope().textContent ?? '').not.toMatch(/needs you|need you/);
    expect(scope().textContent ?? '').not.toMatch(/\b0\b/);
  });

  it('🔴 says the check FAILED when it failed — not that nothing needs you', () => {
    /**
     * ⚠️ **Rendering *"nothing needs you today"* from a failed read is
     * [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md) in the one place a
     * reader would trust it most** — ⛔ **it is the sentence that sends
     * somebody home.**
     */
    greeting({ attention: null, attentionFailed: true });

    expect(scope().textContent ?? '').toMatch(/we could not check what needs you/);
    expect(scope().textContent ?? '').not.toMatch(/nothing needs you/);
  });

  it('✅ and a genuine zero DOES say nothing needs you', () => {
    // ⚡ **The vacuity half of both above.** Without it, *never says nothing
    // needs you* would pass on a line that cannot say it at all.
    greeting({ attention: 0 });
    expect(scope().textContent ?? '').toMatch(/nothing needs you today/);
  });

  it('⚠️ counts in the reader’s grammar', () => {
    greeting({ attention: 1 });
    expect(scope().textContent ?? '').toMatch(/1 thing needs you today/);
    greeting({ attention: 3 });
    expect(document.body.textContent ?? '').toMatch(/3 things need you today/);
  });
});

describe('⛔ an unresolved composition is not the fallback composition', () => {
  it('🔴 names the organization alone until the resolver has answered', () => {
    /**
     * 🔴 **`composition` alone cannot say whether it was RESOLVED.** 📁 Rule 1's
     * input is *"has any integration ever completed a sync"* — a read — **and
     * until it lands the resolver falls through to rule 5**, so `seller` means
     * both *"resolved: seller"* and *"not yet known"*.
     *
     * ⚠️ **Naming the wrong composition is the same class of claim as rendering
     * `0` for a count that has not arrived.**
     */
    greeting({ compositionKnown: false });

    expect(scope().textContent ?? '').toContain('Northwind Global');
    expect(scope().textContent ?? '').not.toContain('Seller');
  });

  it('✅ and names it once it has', () => {
    greeting({ compositionKnown: true });
    expect(scope().textContent ?? '').toContain('Northwind Global · Seller');
  });

  it('⛔ omits the meetings clause entirely, because no calendar producer exists', () => {
    greeting();
    expect(scope().textContent ?? '').not.toMatch(/meeting/i);
  });
});

describe('📁 states 01 and 03 REPLACE the greeting rather than appending to it', () => {
  it('⛔ opens with one sentence, not two', () => {
    // 📁 *"Good afternoon, Dana — let us get you connected"* would be two
    // openings; the design gives state 01 one sentence.
    greeting({ activation: { done: 0, total: 3 } });

    const h1 = screen.getByRole('heading', { level: 1 });
    expect(h1).toHaveTextContent('Let us get Northwind Global connected');
    expect(h1.textContent ?? '').not.toMatch(/Good (morning|afternoon|evening)/);
  });

  it('⚡ state 03 counts the step it is ON, not the one just finished', () => {
    greeting({ activation: { done: 1, total: 3 } });
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Step 2 of 3');
  });

  it('⛔ and never promises a duration, because nothing measures one', () => {
    /**
     * 📁 *"the estimate comes from measured p50 completion time, not a guess"* —
     * ⛔ **and nothing measures one**, so the clause is omitted rather than
     * filled with a plausible number.
     */
    for (const activation of [{ done: 0, total: 3 }, { done: 1, total: 3 }]) {
      const { unmount } = greeting({ activation });
      expect(document.body.textContent ?? '').not.toMatch(/minute|about \d+ min/i);
      unmount();
    }
  });

  it('🔴 and shows the time-of-day greeting when activation has not RESOLVED', () => {
    // ⛔ **Opening with *"let us get you connected"* to somebody who already has
    // is the one thing this sentence must never do**, so `null` means silent.
    greeting({ activation: null });
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Good afternoon');
    expect(document.body.textContent ?? '').not.toMatch(/let us get/i);
  });
});

describe('♿ one announcement per entry, and a heading entry can reach', () => {
  it('📁 4.1.3 — exactly one polite live region carries the whole sentence', () => {
    greeting();
    // ⛔ **Never one announcement per card** — a reader hears this once.
    expect(document.querySelectorAll('[aria-live]')).toHaveLength(1);
    expect(scope()).toHaveAttribute('aria-live', 'polite');
  });

  it('📁 2.4.3 — the heading is focusable without joining the tab order', () => {
    greeting();
    expect(screen.getByRole('heading', { level: 1 })).toHaveAttribute('tabindex', '-1');
  });
});
