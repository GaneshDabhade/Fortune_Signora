/**
 * **The rail's collapse, wired into the frame** —
 * [TASK-1408](../../../docs/BACKLOG.md).
 *
 * ⚡ **The law and the hook are tested elsewhere** — `tests/unit/rail.test.ts`
 * and `tests/components/use-rail-collapse.test.tsx`. **These are the things
 * only the assembled shell can get wrong**: whether the control says what it
 * does, and whether the width is the design's rather than a literal somebody
 * typed.
 */
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('@/components/shell/navigation', () => ({
  Navigation: () => <nav aria-label="Primary" />,
  MobileNavigation: () => <nav aria-label="Primary mobile" />,
}));
vi.mock('@/components/shell/workspace-selector', () => ({ WorkspaceSelector: () => null }));
vi.mock('@/components/intelligence/account-search', () => ({ AccountSearch: () => null }));
vi.mock('@/components/shell/theme-toggle', () => ({ ThemeToggle: () => null }));

import { AppShell } from '@/components/shell/app-shell';
import { RAIL_WIDTH, collapseKey } from '@/lib/shell/rail';

beforeEach(() => {
  window.localStorage.clear();
  Object.defineProperty(window, 'innerWidth', { value: 1440, configurable: true });
});

function shell(userId: string | null = 'u1') {
  return render(
    <AppShell role="owner" userId={userId} signOut={<button type="button">Sign out</button>}>
      <p>Content</p>
    </AppShell>,
  );
}

describe('the rail carries the design’s two widths', () => {
  it('⛔ reads them from RAIL_WIDTH rather than a literal in the markup', () => {
    const { container } = shell();
    const aside = container.querySelector('aside');
    expect(aside).toHaveStyle({ width: `${RAIL_WIDTH.expanded}px` });
    expect(aside).toHaveAttribute('data-collapsed', 'false');
  });

  it('collapses to 56px and remembers it', async () => {
    const { container } = shell();
    await userEvent.click(screen.getByRole('button', { name: 'Collapse navigation' }));
    expect(container.querySelector('aside')).toHaveStyle({
      width: `${RAIL_WIDTH.collapsed}px`,
    });
    expect(window.localStorage.getItem(collapseKey('u1', 'regular'))).toBe('true');
  });
});

describe('♿ the control names the outcome, not the glyph', () => {
  it('⚡ a screen reader user cannot see which way a chevron points', () => {
    shell();
    const toggle = screen.getByRole('button', { name: 'Collapse navigation' });
    expect(toggle).toHaveAttribute('aria-expanded', 'true');
  });

  it('and the name flips with the state', async () => {
    shell();
    await userEvent.click(screen.getByRole('button', { name: 'Collapse navigation' }));
    const toggle = screen.getByRole('button', { name: 'Expand navigation' });
    expect(toggle).toHaveAttribute('aria-expanded', 'false');
  });
});

describe('⚡ the wordmark goes when the rail does', () => {
  it('⛔ 56px cannot hold it, and a clipped wordmark reads as a rendering fault', async () => {
    // ⚠️ **Scoped to the rail deliberately.** The shell renders a SECOND
    // wordmark in the header below `md`, where the rail does not exist —
    // an unscoped query matches both and this test found that.
    const { container } = shell();
    const rail = () => container.querySelector('aside') as HTMLElement;
    expect(within(rail()).getByText('Signora')).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Collapse navigation' }));
    expect(within(rail()).queryByText('Signora')).not.toBeInTheDocument();
  });
});

describe('⛔ navigation survives the collapse', () => {
  it('the rail still holds its destinations at 56px', async () => {
    shell();
    await userEvent.click(screen.getByRole('button', { name: 'Collapse navigation' }));
    // 📁 Collapsed is narrower, never emptier — the destinations remain and
    // expose their labels as accessible names.
    expect(screen.getByRole('navigation', { name: 'Primary' })).toBeInTheDocument();
  });

  it('a shell with no resolved viewer still works, and remembers nothing', async () => {
    shell(null);
    await userEvent.click(screen.getByRole('button', { name: 'Collapse navigation' }));
    expect(window.localStorage.length).toBe(0);
  });
});
