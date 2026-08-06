/**
 * **P-A · Stated absence, as one implementation — TASK-445.**
 *
 * The principle was ratified with **nine recorded instances and zero
 * implementations**, and the Register's annotation was *"name before the
 * ninth"*. The ninth arrived as C-226 — six at once on one screen, fixed by
 * four different lanes. **Every fix was correct and local, which is how nine
 * became nine.**
 *
 * These assert the sentence, and the last one asserts that a tenth cannot be
 * written without anybody noticing — which is the part that makes this a
 * capability rather than a tidy-up.
 */
import { render, screen } from '@testing-library/react';
import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

import { StatedAbsence } from '@/components/feedback/stated-absence';

describe('a failed read says what it could not load', () => {
  it('names the thing, so the sentence is actionable', () => {
    // "Something went wrong" tells a seller nothing they can act on.
    render(<StatedAbsence subject="what changed at this account" />);

    expect(
      screen.getByText(/Signora could not load what changed at this account/i),
    ).toBeInTheDocument();
  });

  it('says what is still true, because that is the fear', () => {
    /** **The half that stops rework.** What a failed read makes somebody
     * afraid of is that their data is gone — and that fear is what makes
     * people re-enter work they did not need to. */
    render(<StatedAbsence subject="your accounts" />);

    expect(screen.getByText(/Nothing has changed/i)).toBeInTheDocument();
  });

  it('says what to do, which is always the same thing', () => {
    render(<StatedAbsence subject="your accounts" />);

    expect(screen.getByText(/reload to try again/i)).toBeInTheDocument();
  });

  it('lets a surface say something stronger when something stronger is true', () => {
    // A customer's own declarations are safe in a way a derived read is not,
    // and the copy said so before this component existed. It still can.
    render(
      <StatedAbsence
        subject="what your organization sells"
        reassurance="Nothing your organization has declared has been lost"
      />,
    );

    expect(
      screen.getByText(/Nothing your organization has declared has been lost/i),
    ).toBeInTheDocument();
  });

  it('never blames the account for a failure of ours', () => {
    /** **C-226's own sentence.** A failed read that renders as *this account
     * has nothing* is a claim about the customer's pipeline rather than about
     * our request. */
    const { container } = render(<StatedAbsence subject="what changed at this account" />);

    for (const blame of [/no activity/i, /nothing here/i, /nothing to show/i, /is empty/i]) {
      expect(container.textContent).not.toMatch(blame);
    }
  });

  it('renders as a page, a card or a paragraph without changing the sentence', () => {
    // **Three shapes were real and each is right where it sits.** The
    // duplication was never the chrome; it was the sentence.
    for (const as of ['page', 'card', 'inline'] as const) {
      const { container, unmount } = render(<StatedAbsence as={as} subject="your accounts" />);
      expect(container.textContent).toMatch(/Signora could not load your accounts/i);
      unmount();
    }
  });
});

describe('a tenth local implementation cannot be written quietly', () => {
  /** **The guard, and the reason this is a capability rather than a
   * tidy-up.** Nine correct local fixes are how P-A stayed unimplemented for
   * nine instances; the tenth would have been correct too. This is what makes
   * the tenth arrive as a failing test instead. */
  const ROOTS = ['components', join('app', '(app)')];

  function sources(dir: string): { name: string; source: string }[] {
    const out: { name: string; source: string }[] = [];
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      const full = join(dir, entry.name);
      if (entry.isDirectory()) out.push(...sources(full));
      else if (entry.name.endsWith('.tsx')) out.push({ name: full, source: readFileSync(full, 'utf8') });
    }
    return out;
  }

  it('no surface writes the failed-read sentence for itself', () => {
    const offenders = ROOTS.flatMap((root) => sources(join(process.cwd(), root)))
      .filter(({ name }) => !name.includes('stated-absence'))
      .filter(({ source }) => /could not load/i.test(source))
      .map(({ name }) => name.split('frontend/').pop());

    expect(
      offenders,
      'a surface is writing its own failed-read copy — use StatedAbsence',
    ).toEqual([]);
  });
});
