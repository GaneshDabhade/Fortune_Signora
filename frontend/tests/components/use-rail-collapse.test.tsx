/**
 * **Rail collapse, remembered** — [TASK-1408](../../../docs/BACKLOG.md).
 *
 * ⚡ **The two cases that matter are both about not losing something**: a
 * preference that must not cross device classes, and a keystroke that must
 * not fire while somebody is typing.
 */
import { act, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it } from 'vitest';

import { useRailCollapse } from '@/lib/shell/use-rail-collapse';
import { collapseKey } from '@/lib/shell/rail';

function Harness({ userId }: { userId: string | null }) {
  const { collapsed, toggle, device } = useRailCollapse(userId);
  return (
    <div>
      <span data-testid="state">{collapsed ? 'collapsed' : 'expanded'}</span>
      <span data-testid="device">{device}</span>
      <button type="button" onClick={toggle}>
        Toggle
      </button>
      <input aria-label="Search" />
    </div>
  );
}

function setViewport(width: number) {
  Object.defineProperty(window, 'innerWidth', { value: width, configurable: true });
  act(() => {
    window.dispatchEvent(new Event('resize'));
  });
}

beforeEach(() => {
  window.localStorage.clear();
  setViewport(1440);
});

describe('the preference is remembered', () => {
  it('starts expanded, then applies what was stored', async () => {
    // ⛔ The first paint is always expanded — reading storage during render
    // would disagree with the server's markup and lose the tree.
    window.localStorage.setItem(collapseKey('u1', 'regular'), 'true');
    render(<Harness userId="u1" />);
    expect(await screen.findByText('collapsed')).toBeInTheDocument();
  });

  it('writes the preference on toggle', async () => {
    render(<Harness userId="u1" />);
    await userEvent.click(screen.getByRole('button', { name: 'Toggle' }));
    expect(window.localStorage.getItem(collapseKey('u1', 'regular'))).toBe('true');
  });
});

describe('🔴 a preference must not cross device classes or users', () => {
  it('⚡ collapsing on a desktop does not collapse the phone', () => {
    /**
     * 📁 *"per user, **per device class**."* ⛔ **Dropping the device half
     * folds the rail on a phone, where 56px of rail is the only navigation
     * there is.**
     */
    window.localStorage.setItem(collapseKey('u1', 'regular'), 'true');
    render(<Harness userId="u1" />);
    setViewport(500);
    expect(screen.getByTestId('device')).toHaveTextContent('compact');
    // The compact class has no stored preference, so it stays expanded.
    expect(screen.getByTestId('state')).toHaveTextContent('expanded');
  });

  it('⛔ one account’s preference is not another’s', () => {
    window.localStorage.setItem(collapseKey('u1', 'regular'), 'true');
    render(<Harness userId="u2" />);
    expect(screen.getByTestId('state')).toHaveTextContent('expanded');
  });

  it('a signed-out shell remembers nothing rather than sharing a key', () => {
    render(<Harness userId={null} />);
    expect(window.localStorage.length).toBe(0);
  });
});

describe('📁 `[` toggles collapse', () => {
  it('folds the rail from the keyboard', async () => {
    render(<Harness userId="u1" />);
    // `[[` is user-event's escape for a literal `[` — a bare one opens a key
    // descriptor, which is what three failures here were.
    await userEvent.keyboard('[[');
    expect(screen.getByTestId('state')).toHaveTextContent('collapsed');
  });

  it('🔴 ⛔ does nothing while somebody is typing', async () => {
    /**
     * ⚡ **`[` is an ordinary character.** **A seller typing an account name
     * into search would fold the navigation mid-word**, and the shortcut is
     * worth nothing next to that.
     */
    render(<Harness userId="u1" />);
    const search = screen.getByLabelText('Search');
    await userEvent.click(search);
    await userEvent.keyboard('[[');
    expect(screen.getByTestId('state')).toHaveTextContent('expanded');
    expect(search).toHaveValue('[');
  });

  it('⛔ ignores the modified forms, which belong to the browser', async () => {
    render(<Harness userId="u1" />);
    await userEvent.keyboard('{Meta>}[[{/Meta}');
    expect(screen.getByTestId('state')).toHaveTextContent('expanded');
  });
});
