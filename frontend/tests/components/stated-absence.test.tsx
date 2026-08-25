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

  /**
   * ⚠️ **Comments are stripped before scanning, added by
   * [TASK-1428](../../../docs/BACKLOG.md), and it is not a loosening.**
   *
   * ⛔ **The guard fired on [`region-boundary.tsx`](../../components/ui/region-boundary.tsx)'s
   * JSDoc** — a comment that quotes the sentence **in order to explain that
   * the file no longer writes it.** ⚡ **That is
   * [B-318](../../../docs/BUGS.md)'s named class**: *"a Security Invariant
   * matches text, so a comment fails it."*
   *
   * ✅ **The alternative was rewording the comment**, and that is the wrong
   * repair: **it would have left the guard reading prose**, so the next
   * explanation of this very rule would fail it again. **The rule is about
   * rendered copy, so the guard now reads code.**
   */
  /**
   * ⚠️ **String-aware, and the naive version was [B-162](../../../docs/BUGS.md).**
   *
   * ⛔ **`replace(/\/\/.*$/gm, '')` deletes from the first `//` to the end of
   * the line, and `//` occurs inside every absolute URL.** **A line carrying a
   * link and rendered copy lost the copy**, so the guard stopped catching a
   * class it used to catch — ⚡ **and the class it lost is the one it exists
   * for: rendered text, not prose.**
   *
   * ✅ **Narrowing a guard is only safe if you measure what stops firing.**
   * **This walks the source instead**, tracking quotes and template literals,
   * so a `//` inside a string is text and a `//` outside one is a comment.
   */
  const code = (src: string): string => {
    let out = '';
    let quote: string | null = null;
    for (let i = 0; i < src.length; i += 1) {
      const c = src[i] as string;
      const next = src[i + 1];

      if (quote !== null) {
        out += c;
        if (c === '\\') {
          out += src[i + 1] ?? '';
          i += 1;
        } else if (c === quote) {
          quote = null;
        }
        continue;
      }

      if (c === "'" || c === '"' || c === '`') {
        quote = c;
        out += c;
        continue;
      }
      if (c === '/' && next === '*') {
        const end = src.indexOf('*/', i + 2);
        i = end === -1 ? src.length : end + 1;
        continue;
      }
      if (c === '/' && next === '/') {
        const nl = src.indexOf('\n', i);
        if (nl === -1) break;
        i = nl - 1;
        continue;
      }
      out += c;
    }
    return out;
  };

  const SENTENCE = /could not load/i;

  it('no surface writes the failed-read sentence for itself', () => {
    const offenders = ROOTS.flatMap((root) => sources(join(process.cwd(), root)))
      .filter(({ name }) => !name.includes('stated-absence'))
      .filter(({ source }) => SENTENCE.test(code(source)))
      .map(({ name }) => name.split('frontend/').pop());

    expect(
      offenders,
      'a surface is writing its own failed-read copy — use StatedAbsence',
    ).toEqual([]);
  });

  it('✅ and the guard is proved able to fire, on code and not on prose', () => {
    // ⚡ **§2 — *a guard that cannot fail is documentation pretending to be
    // code*.** Both halves asserted: it catches a real local sentence, and it
    // does NOT catch a comment saying the same words.
    expect(SENTENCE.test(code('const t = "Pipeline could not load";'))).toBe(true);
    expect(SENTENCE.test(code('// this file no longer says could not load'))).toBe(false);
    expect(SENTENCE.test(code('/** explains could not load */'))).toBe(false);

    // 🔴 **[B-162](../../../docs/BUGS.md), and each of these evaded the naive
    // strip.** ⛔ **`//` occurs inside every absolute URL**, so a line
    // carrying a link and rendered copy lost the copy.
    expect(
      SENTENCE.test(code('<a href="https://x.test">{"Pipeline could not load"}</a>')),
    ).toBe(true);
    expect(SENTENCE.test(code('const t = `Pipeline could not load`; // https://x'))).toBe(true);
    expect(SENTENCE.test(code("const t = 'a // b could not load';"))).toBe(true);
    // ⛔ And an escaped quote must not end the string early.
    expect(SENTENCE.test(code('const t = "it\\"s: could not load";'))).toBe(true);
  });
});

describe('📁 §4.1.3 — a failed read announces, and announces politely', () => {
  /**
   * 📁 `System States`, `a11y` §4.1.3, verbatim:
   *
   * > ***"Region errors and retries announce politely. Only a state that ends
   * > the session — 500, maintenance — announces assertively, once."***
   *
   * ⛔ **The page-level branch announced NOTHING**, across seven callers.
   * ⚠️ **Found by QE in a browser and reported as an observation they had
   * deliberately not established** — *"a full-page state rendering a heading
   * is legitimately not an alert, and asserting otherwise would be a
   * preference dressed as a finding."* ✅ **They were right: the absence of
   * `alert` is correct. The absence of any announcement was the defect.**
   */
  it('🔴 announces the failure politely', () => {
    render(<StatedAbsence as="page" subject="your organizations" />);

    const announcement = screen.getByRole('status');
    expect(announcement).toHaveTextContent(/could not load your organizations/i);
  });

  it('⛔ never assertively — that is reserved for a state that ends the session', () => {
    /**
     * ⚡ **The positive control.** ⛔ Without it, wrapping the block in
     * `role="alert"` would satisfy the test above while interrupting a
     * customer for a region read — which 📁 `system-state.tsx`'s own
     * `politeness()` reserves for `app` and `platform` scope.
     */
    render(<StatedAbsence as="page" subject="your organizations" />);

    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });
});
