/**
 * **The user menu states the design's four facts** —
 * [B-429](../../../docs/BUGS.md), App Shell §11.
 *
 * 🔴 **Three of four shipped, and the fourth was explained away.** 📁 The menu
 * carried a comment reading *"Name is not stated, because the platform does not
 * publish one — the session carries an email and nothing else."*
 *
 * ⛔ **The reasoning was sound and the premise was false.** 📁 Registration
 * requires a full name, `profile/page.tsx` already reads `user?.name` from the
 * same session, and [`layout.tsx`](../../app/\(app\)/layout.tsx) had
 * `session.user.name` **in scope on the line that dropped it.**
 *
 * ⚡ **[§2](../../../CLAUDE.md): a comment justifying absent behaviour is a
 * false claim sitting in the codebase** — and this one read as a considered
 * design decision, which is how it survived review and promotion.
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: () => ({
    activeWorkspace: { id: 'w1', name: 'Northwind Global' },
    workspaces: [{ id: 'w1', name: 'Northwind Global' }],
    isLoading: false,
  }),
}));

import { AccountMenu } from '@/components/shell/account-menu';
import { ThemeProvider } from '@/lib/state/theme-provider';

const EMAIL = 'marta@northwind.com';

async function open(name: string | null) {
  render(
    <ThemeProvider>
      <AccountMenu email={EMAIL} name={name} role="owner" signOut={<button>Sign out</button>} />
    </ThemeProvider>,
  );
  await userEvent.click(screen.getByRole('button', { name: `Account menu for ${EMAIL}` }));
  return screen.getByRole('menu', { name: 'Account' });
}

describe('🔴 all four facts, not three', () => {
  /**
   * 🔴 **The assertion the defect failed**, and 📁 the design's own example:
   * *"MR · Marta Reinhardt · marta@northwind.com · Admin · Northwind Global"*.
   */
  it('🔴 states the name, the email, the role and the workspace', async () => {
    const menu = await open('Marta Reinhardt');

    expect(menu).toHaveTextContent('Marta Reinhardt');
    expect(menu).toHaveTextContent(EMAIL);
    expect(menu).toHaveTextContent(/owner/i);
    expect(menu).toHaveTextContent('Northwind Global');
  });

  /**
   * ⛔ **The half of the old comment that was RIGHT, and it stays right.**
   *
   * ⚡ **A name is never derived from the address.** 📁 *"Inventing a display
   * name from the local part would be the shell asserting a fact about a person
   * it does not have"* — **that sentence was correct and only its premise was
   * wrong.**
   */
  it('⛔ says nothing about a name it was not given', async () => {
    const menu = await open(null);

    expect(menu).toHaveTextContent(EMAIL);
    // ⛔ **`marta` must not appear as a name of its own.**
    expect(menu.textContent).not.toMatch(/\bMarta\b/);
    // ✅ **And the other three facts are unaffected** — one absent fact does
    // not take the rest with it.
    expect(menu).toHaveTextContent(/owner/i);
    expect(menu).toHaveTextContent('Northwind Global');
  });

  /**
   * 📁 **The design's avatar reads *"MR"* for *Marta Reinhardt***, which an
   * address cannot produce. ⛔ **The address is the fallback, never the
   * source.**
   */
  it('✅ the initials come from the name when there is one', async () => {
    render(
      <ThemeProvider>
        <AccountMenu
          email={EMAIL}
          name="Marta Reinhardt"
          role="owner"
          signOut={<button>Sign out</button>}
        />
      </ThemeProvider>,
    );

    expect(screen.getByText('MR')).toBeInTheDocument();
  });
});
