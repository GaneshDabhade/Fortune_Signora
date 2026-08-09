/**
 * **Screen `08 · Skip, resume, and the three interruption states`** —
 * [TASK-469](../../../docs/BACKLOG.md) milestone 2.
 *
 * ⚡ **The design's note is what is asserted**, because it is the part a later
 * change is most likely to break by good intentions:
 *
 * > 📁 ***"States the consequence in product terms and lets them go. No dark
 * > pattern, no second ask."***
 *
 * ⛔ **"No second ask" is a property, and a property can be tested.** *"Looks
 * right"* cannot.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import {
  SkipSetup,
  SECONDS_PER_STEP,
  consequence,
  formatSetupEstimate,
} from '@/app/(onboarding)/onboarding/skip-setup';
import { onboardingExit } from '@/app/(onboarding)/onboarding/exit';

const push = vi.fn();
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: (href: string) => push(href) }),
}));

function open() {
  return userEvent.click(screen.getByRole('button', { name: 'Skip setup' }));
}

describe('the consequence is stated in product terms', () => {
  it('⚡ names what Signora will do differently, not what the form is missing', () => {
    const text = consequence('Logistics & transport');
    // 📁 The design's own two consequences.
    expect(text).toMatch(/general benchmarks/i);
    expect(text).toMatch(/home page will show everything rather than your priorities/i);
    // ⛔ Never the language of an incomplete form.
    expect(text).not.toMatch(/steps? remaining|incomplete|unfinished|required/i);
  });

  it('🔴 templates the industry from the run and never hardcodes the design’s example', () => {
    /**
     * ⛔ **The design writes *"logistics companies your size"* because its
     * example workspace is a logistics company** — that word is the run's
     * answer to screen `04`, not product copy. **Shipping it literally would
     * put a fixture on a customer's screen**, which is the defect
     * `no-mock-data.test.tsx` exists for and the reason `SIZE_BANDS` was
     * renamed.
     */
    expect(consequence('Manufacturing')).toContain('manufacturing companies your size');
    expect(consequence('Logistics & transport')).not.toContain('manufacturing');
  });

  it('✅ falls back to the generic form when screen 04 was never answered', () => {
    // ⚠️ **The common path, not the edge** — somebody skipping is likely not
    // to have answered it.
    for (const missing of [null, undefined, '']) {
      const text = consequence(missing);
      expect(text).toContain('ones matched to companies like yours');
      expect(text).not.toMatch(/\bundefined\b|\bnull\b/);
    }
  });
});

describe('the estimate is the design’s arithmetic', () => {
  it('⚡ prints seconds, derived from “two questions left — about 40 seconds”', () => {
    expect(SECONDS_PER_STEP).toBe(20);
    expect(formatSetupEstimate(2)).toBe('40s');
  });

  it('counts the questions outstanding, and `welcome` is not a question', () => {
    // company, you, goals, connect outstanding → 4 × 20s.
    render(<SkipSetup completedIds={['welcome', 'workspace']} industry={null} />);
    return open().then(() => {
      expect(screen.getByRole('button', { name: /Finish setup — 80s/ })).toBeInTheDocument();
    });
  });
});

describe('⛔ no dark pattern, and no second ask', () => {
  it('leaves immediately when Skip is pressed', async () => {
    push.mockClear();
    render(<SkipSetup completedIds={['welcome', 'workspace', 'company']} industry="Software" />);
    await open();
    await userEvent.click(screen.getByRole('button', { name: 'Skip' }));

    // 🔴 **One navigation, to the flow's single exit seam.** ⛔ Not a second
    // dialog, not a re-worded offer, not a toast that offers to undo.
    expect(push).toHaveBeenCalledTimes(1);
    expect(push).toHaveBeenCalledWith(onboardingExit());
  });

  it('🔴 asks exactly once — pressing Skip opens no further prompt', async () => {
    push.mockClear();
    render(<SkipSetup completedIds={['welcome']} industry={null} />);
    await open();
    expect(screen.getAllByRole('dialog')).toHaveLength(1);

    await userEvent.click(screen.getByRole('button', { name: 'Skip' }));
    // ⛔ **The property, asserted rather than promised**: no dialog appeared
    // to replace the one that was there.
    await waitFor(() => expect(push).toHaveBeenCalled());
    expect(screen.queryAllByRole('dialog').length).toBeLessThanOrEqual(1);
    expect(screen.queryByText(/are you sure|really|confirm/i)).not.toBeInTheDocument();
  });

  it('✅ Finish setup only closes — it navigates nowhere', async () => {
    push.mockClear();
    render(<SkipSetup completedIds={['welcome']} industry={null} />);
    await open();
    await userEvent.click(screen.getByRole('button', { name: /Finish setup/ }));

    // ⚡ They are already on the step they were on; continuing is the
    // ABSENCE of a navigation.
    expect(push).not.toHaveBeenCalled();
  });

  it('⛔ skipping records nothing — no write leaves this component', () => {
    /**
     * **The whole-flow form of the rule `company-form.tsx` states for one
     * step**: *"a skip that quietly confirmed four guesses"* is an answer
     * nobody gave.
     *
     * ⚠️ **The first version of this case asserted the keys of an object
     * literal written in the test** — `Object.keys({ completedIds, industry })`
     * — **which could not fail whatever the component did.** ⛔ That is
     * [§2](../../../CLAUDE.md)'s *guard that cannot fail*, and this file
     * would have shipped it. **Replaced with a read of the source**, which
     * fails the moment somebody adds a save on the way out.
     */
    const src = readFileSync(
      join(process.cwd(), 'app/(onboarding)/onboarding/skip-setup.tsx'),
      'utf8',
    );
    const code = src.replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/.*$/gm, '');
    expect(code).not.toMatch(/\bfetch\s*\(|useMutation|\bsave|\bpatch|\bpost\b/i);
    // ✅ And the guard is proved able to fire: the same pattern is present in
    // a sibling that legitimately does write.
    const writer = readFileSync(
      join(process.cwd(), 'app/(onboarding)/onboarding/use-onboarding.ts'),
      'utf8',
    );
    expect(writer).toMatch(/\bfetch\s*\(|useMutation|\bsave|\bpatch|\bpost\b/i);
  });
});
