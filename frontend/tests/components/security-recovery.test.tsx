/**
 * **§04 · Recovery, and §02's *What Signora never does*** —
 * [TASK-1414](../../../docs/BACKLOG.md).
 *
 * ⚠️ **The row calls this *"the sentence the row is really about"***: *"the
 * design has an explicit section stating the product's own limits, and it must
 * be built as content the product commits to, not as filler."*
 */
import { render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { RecoveryPanel } from '@/app/(app)/profile/security/recovery-panel';
import { NEVER_DOES } from '@/app/(app)/profile/security/rules';

describe('🔴 a route that does not exist says so, on the screen', () => {
  /**
   * ⛔ **The design draws four routes as though all four work.** ⚡ **This is
   * the assertion that fails if the *not built* sentence is ever dropped to
   * make the list look even** — which is exactly how a dead end ships.
   */
  it('🔴 admin-assisted recovery is marked unbuilt AND explains itself', () => {
    render(<RecoveryPanel />);

    const routes = screen.getAllByTestId('recovery-route');
    const unbuilt = routes.filter((route) => route.dataset.built === 'false');

    expect(unbuilt).toHaveLength(1);
    expect(unbuilt[0]).toHaveTextContent('Admin-assisted recovery');
    expect(unbuilt[0]).toHaveTextContent('does not exist yet');
    expect(unbuilt[0]).toHaveTextContent('do not plan on it');
  });

  /**
   * ⛔ **An unbuilt route must not print a duration.** ⚡ ***24–48 hours* beside
   * a route nobody can take is the most precise false claim on the page** —
   * somebody would wait for it.
   */
  it('⛔ an unbuilt route states no time it would take', () => {
    render(<RecoveryPanel />);

    const unbuilt = screen
      .getAllByTestId('recovery-route')
      .find((route) => route.dataset.built === 'false');

    expect(unbuilt).not.toHaveTextContent(/hours|minutes|Immediate/);
  });

  it('✅ every route states what it proves, because that is what the design asks of it', () => {
    render(<RecoveryPanel />);

    for (const route of screen.getAllByTestId('recovery-route')) {
      expect(route).toHaveTextContent(/Proves|prove/);
    }
  });

  it('✅ the SSO dead end is said plainly rather than discovered after four steps', () => {
    render(<RecoveryPanel />);

    expect(
      screen.getByText(/no self-service reset for accounts that sign in through an identity provider/i),
    ).toBeInTheDocument();
  });
});

describe('📁 what Signora never does', () => {
  it('✅ all four commitments are rendered, verbatim', () => {
    render(<RecoveryPanel />);

    const list = screen.getByTestId('never-does');
    for (const commitment of NEVER_DOES) {
      expect(within(list).getByText(commitment)).toBeInTheDocument();
    }
  });

  /**
   * ⚡ **The sentence that makes the list usable rather than decorative** — it
   * tells a reader what to conclude when they meet one of the four.
   */
  it('✅ and the list says what to do with it', () => {
    render(<RecoveryPanel />);

    expect(screen.getByText(/it is not Signora/)).toBeInTheDocument();
  });
});
