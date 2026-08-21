/**
 * **A section stays a section in every state** — [TASK-1476](../../../docs/BACKLOG.md),
 * against 📁 `Fortune Signora Account 360.dc.html` §*States*.
 *
 * ⚡ **These assert the rules that survive a state change**, which is the half
 * a unit test on the law cannot reach: the law says what the header should
 * FOLD to; only a render says whether the header is still there once the
 * section is shut.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { AccountSectionShell } from '@/components/accounts/section';

function shell(props: Partial<Parameters<typeof AccountSectionShell>[0]> = {}) {
  return render(
    <AccountSectionShell
      id="score"
      heading="What contributed"
      severities={['none', 'watch', 'none']}
      viewerId="u1"
      kind={null}
      {...props}
    >
      <p>the body</p>
    </AccountSectionShell>,
  );
}

describe('📁 "every section is a labelled region with a heading" — in EVERY state', () => {
  /**
   * 🔴 **This is a regression guard with a real defect behind it.** ⚠️ The
   * first version of this component made the heading a `span` inside the
   * toggle button, **which removed every section from the document outline**.
   * ⛔ A screen-reader user navigating by heading lost the page.
   */
  it('the heading is a heading, and stays one when the section is shut', () => {
    shell();
    expect(screen.getByRole('heading', { name: /What contributed/ })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /What contributed/ }));
    expect(screen.getByRole('heading', { name: /What contributed/ })).toBeInTheDocument();
  });

  it('the region is labelled by that heading', () => {
    const { container } = shell();
    const section = container.querySelector('section');
    expect(section?.getAttribute('aria-labelledby')).toBe('score-heading');
  });
});

describe('🔴 collapsing cannot hide a risk', () => {
  /** 📁 *"Header keeps the count and the worst status."* */
  it('the count and the worst status survive the collapse', () => {
    shell();
    fireEvent.click(screen.getByRole('button', { name: /What contributed/ }));

    // ⛔ **Still on screen with the body shut.** ⚡ A section folded to its
    // heading alone is the one outcome the design forbids.
    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.getByText('worth watching')).toBeInTheDocument();
  });

  it('⚠️ a section with no status shows a count and no dot', () => {
    // ⛔ *Nothing here has a status* must not render as *everything is fine*.
    shell({ severities: ['none', 'none'] });
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.queryByText('nothing of concern')).not.toBeInTheDocument();
    expect(screen.queryByText('a risk')).not.toBeInTheDocument();
  });
});

describe('⚡ the disclosure says what it is doing', () => {
  it('aria-expanded tracks the body, and the body is hidden rather than unmounted', () => {
    shell();
    const toggle = screen.getByRole('button', { name: /What contributed/ });
    expect(toggle).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByText('the body')).toBeVisible();

    fireEvent.click(toggle);
    expect(toggle).toHaveAttribute('aria-expanded', 'false');
    // ⚠️ **Hidden, not removed.** ⛔ Unmounting would drop scroll position and
    // any in-flight state the body holds, and 📁 the design's Expanded rule
    // asks for scroll to be RESTORED rather than reset.
    expect(screen.getByText('the body')).not.toBeVisible();
  });
});

describe('⛔ nothing is persisted under an owner or a type this page does not know', () => {
  /**
   * 📁 **[B-261](../../../docs/BUGS.md).** ⚠️ Account 360 does not publish the
   * account TYPE, and the design keys this preference **per type, never per
   * record**. ⚡ **So the preference is not stored at all** — ⛔ storing it
   * under a guessed type puts it somewhere a rep cannot get it back from, and
   * a wrong preference is worse than none.
   */
  it('an unknown account type writes nothing', () => {
    window.localStorage.clear();
    shell({ kind: null, viewerId: 'u1' });
    fireEvent.click(screen.getByRole('button', { name: /What contributed/ }));
    expect(window.localStorage.length).toBe(0);
  });

  it('an unknown viewer writes nothing either', () => {
    window.localStorage.clear();
    shell({ kind: 'company', viewerId: null });
    fireEvent.click(screen.getByRole('button', { name: /What contributed/ }));
    expect(window.localStorage.length).toBe(0);
  });

  it('✅ and a known viewer and type write under the TYPE key, with no record in it', () => {
    window.localStorage.clear();
    shell({ kind: 'company', viewerId: 'u1' });
    fireEvent.click(screen.getByRole('button', { name: /What contributed/ }));

    const keys = Object.keys(window.localStorage);
    expect(keys).toHaveLength(1);
    expect(keys[0]).toContain('company');
    expect(keys[0]).toContain('u1');
    expect(window.localStorage.getItem(keys[0]!)).toBe('collapsed');
  });
});

describe('📁 "skeleton row count matches the expected result"', () => {
  it('renders as many skeleton rows as the section had last time', () => {
    const { container } = shell({ isLoading: true, lastKnownCount: 6 });
    // ⚡ The body is the skeleton, and the count comes from the law rather
    // than from a literal in the component.
    expect(container.querySelectorAll('[aria-hidden="true"] > *').length).toBeGreaterThanOrEqual(6);
  });

  it('⛔ and never paints an empty body while a read is pending', () => {
    const { container } = shell({ isLoading: true, lastKnownCount: 0 });
    // 📁 P-A one level up: a pending read must not render as an empty result.
    expect(container.querySelectorAll('[aria-hidden="true"] > *').length).toBeGreaterThan(0);
    expect(screen.queryByText('the body')).not.toBeInTheDocument();
  });
});

/**
 * 🔴 **[B-1054](../../../docs/BUGS.md) — a failed read rendered its count as `0`.**
 *
 * ⛔ **QE induced it rather than waiting for it**: with
 * `…/accounts/{id}/observations` forced to **500**, the heading read ***"What
 * changed 0"*** above a body that correctly said *"Signora could not load what
 * changed at this account. Nothing has changed about the account — reload to
 * try again."* **Healthy, the same heading reads `21`.**
 *
 * ⚡ **The prose was exemplary and is not what the row is about.** 🔴 **`0` is a
 * measurement, and no measurement was obtained** — and a reader scanning
 * headings meets the number first.
 *
 * ⚠️ 📁 **The row's own note on method**: *"a test that only checks the healthy
 * path cannot see this."*
 */
describe('🔴 a count is a measurement, so a failed read publishes none', () => {
  it('⛔ renders no count at all when the read failed — not `0`', () => {
    shell({ isError: true, severities: [] });

    const region = screen.getByRole('region', { name: 'What contributed' });
    // ⛔ **No zero, and no number of any kind** in the header's count slot.
    expect(region.textContent).not.toMatch(/\b0\b/);
  });

  it("⚡ and no STALE count either — the figure is this render's", () => {
    // 📁 The row: *"not `0`, and not a stale count from a previous render."*
    const { rerender } = shell({ severities: ['none', 'none', 'watch'] });
    expect(screen.getByRole('region', { name: 'What contributed' })).toHaveTextContent('3');

    rerender(
      <AccountSectionShell
        id="score"
        heading="What contributed"
        severities={['none', 'none', 'watch']}
        viewerId="u1"
        kind={null}
        isError
      >
        <p>the body</p>
      </AccountSectionShell>,
    );
    const region = screen.getByRole('region', { name: 'What contributed' });
    expect(region.textContent).not.toMatch(/\b3\b/);
  });

  /**
   * ✅ **The rule the count exists for is untouched, and this is the assertion
   * that proves the fix did not soften it.**
   *
   * 📁 *"A positive empty is good news, not a gap"* — **a read that SUCCEEDS
   * and finds nothing still says `0`**, because *nothing here* and *could not
   * find out* are different sentences and must never render the same
   * ([P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md)).
   */
  it('✅ a SUCCESSFUL read that found nothing still says `0`', () => {
    shell({ severities: [] });
    expect(screen.getByRole('region', { name: 'What contributed' })).toHaveTextContent('0');
  });
});
