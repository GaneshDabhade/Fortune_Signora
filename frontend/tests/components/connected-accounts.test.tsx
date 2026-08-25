/**
 * **Screen `05 · Connected accounts & sessions`**, against
 * `docs/design-snapshot/screens/Fortune Signora User Profile.dc.html`.
 *
 * 🔴 **The defect these were written for is a claim, not a control.** ⛔ The
 * section rendered *"This section is not built yet — the accounts you have
 * connected, their scope, and **every session signed in as you**"* **while the
 * card at the foot of the same screen linked to sessions and described them in
 * the same words.** 📁 [§2](../../CLAUDE.md): the repository must not assert
 * something untrue of itself, and a screen contradicting itself is the version
 * a reader trusts least.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { ConnectedAccountsPanel } from '@/app/(app)/profile/connected-accounts-panel';

describe('screen 05 · the half that is built', () => {
  it('🔴 does not call sessions unbuilt, and routes to them', () => {
    render(<ConnectedAccountsPanel />);

    // ⛔ **The sentence that was wrong.** `authClient.listSessions()` has been
    // listing, revoking and signing out everywhere for some time.
    expect(screen.queryByText(/not built yet/i)).not.toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Your sessions' })).toHaveAttribute(
      'href',
      '/profile/security',
    );
  });

  it('keeps the design’s honest clause about the identity provider', () => {
    render(<ConnectedAccountsPanel />);

    // 📁 ***"Your identity provider may still hold a session — we say so
    // rather than implying we control it."*** ⚡ The clause is the point: a
    // sign-out that overclaims is worse than one that explains its limit.
    expect(screen.getByText(/identity provider may\s+still hold its own/)).toBeInTheDocument();
  });
});

describe('screen 05 · the half that has no producer', () => {
  it('🔴 says why a personal connection cannot exist, rather than showing an empty table', () => {
    /**
     * ⚡ **Measured, not assumed**: every route in
     * `integrations/interface/router.py` is `/workspaces/{workspace_id}/…`,
     * and `user_id` appears only as `actor_id`.
     *
     * ⛔ **An empty "Connected accounts" table would invite somebody to look
     * for a Connect button that does not exist** — an absence dressed as
     * information.
     */
    render(<ConnectedAccountsPanel />);

    expect(screen.queryByRole('table')).not.toBeInTheDocument();
    expect(
      screen.getByText(/belongs to an organization rather than to a person/),
    ).toBeInTheDocument();
  });

  it('sends somebody looking for Salesforce to where it actually lives', () => {
    render(<ConnectedAccountsPanel />);

    // ⚡ The reason this section is thin is that the capability sits at a
    // different SCOPE — so the honest answer names the scope, not the gap.
    expect(
      screen.getByRole('link', { name: 'Organization connections' }),
    ).toHaveAttribute('href', '/settings/connections');
  });

  it('⛔ does not promise that each connection names what it reads', () => {
    /**
     * 📁 The design's §05 continues *"Each one names exactly what it reads."*
     * ⛔ **That is a promise about rows that do not exist**, and carrying it
     * here would describe the capability by its future behaviour — the same
     * defect as a docstring asserting an absence that has since been filled,
     * pointed the other way.
     */
    render(<ConnectedAccountsPanel />);

    expect(screen.queryByText(/names exactly what it reads/)).not.toBeInTheDocument();
  });
});
