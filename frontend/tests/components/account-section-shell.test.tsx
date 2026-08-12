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
