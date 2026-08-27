/**
 * **The saved-views strip on Companies** — 📁 `Fortune Signora Companies.dc.html`,
 * with [B-1055](../../../docs/BUGS.md)'s keyboard grammar.
 *
 * 🔴 **Nothing rendered this component.** ⚡ It carries a roving tab index and
 * four arrow keys, which is precisely the shape that fails silently.
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { ViewTabs } from '@/app/(app)/accounts/view-tabs';

/** ⚡ **Two saved views plus *All companies* is three tabs**, which is the
 *  smallest strip where wrapping is observable in both directions. */
const VIEWS = [
  { id: 'v1', name: 'Enterprise', scope: 'workspace' },
  { id: 'v2', name: 'My accounts', scope: 'personal' },
];
const TAB_COUNT = VIEWS.length + 1;

function strip(overrides: Record<string, unknown> = {}) {
  const onSelect = vi.fn();
  const view = render(
    <ViewTabs
      views={VIEWS as never}
      loading={false}
      selected={null}
      onSelect={onSelect}
      mode="table"
      onMode={() => {}}
      refusal={null}
      {...overrides}
    />,
  );
  return { onSelect, view };
}

describe('♿ the strip moves under the arrows and leaves under Tab', () => {
  it('🔴 exactly one tab is a tab stop', () => {
    // ⛔ **Without a roving index `Tab` walks every saved view** before it
    // reaches the list those views are for.
    strip();
    const tabs = screen.getAllByRole('tab');
    expect(tabs.filter((t) => t.getAttribute('tabindex') === '0')).toHaveLength(1);
    expect(tabs).toHaveLength(TAB_COUNT);
  });

  it('✅ → ← Home End all move, and they wrap', async () => {
    /**
     * ⛔ **A roving index without arrow keys would put every unselected view
     * out of the keyboard's reach** — 📁 [B-1055](../../../docs/BUGS.md), and
     * that is a regression rather than a fix.
     */
    const { onSelect } = strip();
    // ⚡ **Focus a tab and type there** — the handler sits on the tablist and
    // the event bubbles, which is the arrangement the component chose so one
    // listener serves every tab.
    (screen.getAllByRole('tab')[0] as HTMLElement).focus();

    await userEvent.keyboard('{ArrowRight}');
    expect(onSelect).toHaveBeenLastCalledWith('v1');

    // ⚡ **Wrapping backwards from the first reaches the last** — the design's
    // strip is short and stalling at an end is what a person notices.
    await userEvent.keyboard('{ArrowLeft}');
    expect(onSelect).toHaveBeenLastCalledWith('v2');

    await userEvent.keyboard('{End}');
    expect(onSelect).toHaveBeenLastCalledWith('v2');

    // ⛔ **Home returns `null`, not the string `all`** — the strip's own
    // spelling is internal and the caller's contract is unchanged.
    await userEvent.keyboard('{Home}');
    expect(onSelect).toHaveBeenLastCalledWith(null);
  });

  it('♿ every tab names the panel it controls', () => {
    // 📁 [B-1055](../../../docs/BUGS.md): *"a tablist owes two things beyond
    // the role"*, and this is the second.
    strip();
    for (const tab of screen.getAllByRole('tab')) {
      expect(tab.getAttribute('aria-controls')).toBe('companies-saved-view-panel');
    }
  });
});

describe('📁 a refusal that is usually not an error announces politely', () => {
  it('🔴 `status`, never `alert`', () => {
    /**
     * 📁 **`System States` `4.1.3`**: *"Region errors and retries announce
     * politely. **Only a state that ends the session** — 500, maintenance —
     * announces assertively, once."*
     *
     * ⛔ **And this is not even an error most of the time.** The component's
     * own note: *"the store is workspace-wide and holds four screens'
     * declarations, so a Reports definition in this row is ordinary."*
     * ⚡ **Interrupting somebody to say something ordinary happened is the
     * worst version of an assertive announcement.**
     *
     * ⚠️ **No competing document** — `Companies` publishes no `a11y` array and
     * no announcement rule, so `System States` governs alone. ⛔ Unlike
     * [C-1572](../../../docs/LANE_COORDINATION.md), where two documents
     * disagree and this lane changed nothing.
     */
    strip({ refusal: 'That view describes Reports, so it was not applied here.' });

    const notice = screen.getByText(/That view describes Reports/);
    expect(notice).toHaveAttribute('role', 'status');
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('⛔ and nothing is announced when there is nothing to say', () => {
    // ⚡ **An empty live region is not a courtesy** — it is a node a screen
    // reader watches for changes that never come.
    strip();
    expect(screen.queryByRole('status')).toBeNull();
  });
});
