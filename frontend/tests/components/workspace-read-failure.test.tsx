/**
 * 🔴 **[B-237](../../../docs/BUGS.md), reopened by QE on 2026-08-25 — a failed
 * workspace read rendered as *"You are not part of an organization yet"*, with
 * a `Create an organization` button beneath it.**
 *
 * 📁 [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md): ***a failed read must
 * never render as an empty result.*** ⚡ **These two states are opposite claims
 * about the customer's own account**, and the wrong one tells somebody who has
 * organizations that they have none — then offers to create one.
 *
 * ⚠️ **The capability was never missing.** `WorkspaceProvider` has exposed
 * `error` all along and **39 of its 43 consumers do not read it**;
 * `settings/audit/page.tsx` is the one screen in this family that did. **The
 * fix is that shape, applied to the three that did not.**
 */
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

let context: {
  workspaces: unknown[];
  activeWorkspace: unknown;
  isLoading: boolean;
  error: Error | null;
};

vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: () => context,
  WorkspaceProvider: ({ children }: { children: React.ReactNode }) => children,
}));

import HelpPage from '@/app/(app)/help/page';

beforeEach(() => {
  context = { workspaces: [], activeWorkspace: null, isLoading: false, error: null };
});

function renderHelp() {
  return render(
    <QueryClientProvider client={new QueryClient()}>
      <HelpPage />
    </QueryClientProvider>,
  );
}

describe('🔴 a workspace read that FAILED is never an organization you do not have', () => {
  it('states the failure rather than claiming the account is empty', () => {
    context.error = new Error('the workspace list could not be read');

    renderHelp();

    // ⛔ **The sentence B-237 was filed for.**
    expect(
      screen.queryByText('You are not part of an organization yet'),
    ).not.toBeInTheDocument();
    // ⛔ **And the button beneath it** — an offer to fix a problem the customer
    // does not have.
    expect(
      screen.queryByRole('link', { name: /Create an organization/ }),
    ).not.toBeInTheDocument();

    // ⚡ **Two matches by design** — `StatedAbsence as="page"` renders a title
    // and a description, and both name the subject.
    expect(screen.getAllByText(/could not load your organizations/i).length).toBeGreaterThan(0);
  });

  it('✅ still says so when the account genuinely has none', () => {
    /**
     * ⚡ **The positive control.** ⛔ Without it, a screen that rendered the
     * failure sentence unconditionally would pass the test above — which is
     * the class QE recorded in [B-1073](../../../docs/BUGS.md): *an assertion
     * that cannot tell a satisfied rule from an absent case.*
     */
    context.error = null;

    renderHelp();

    expect(screen.getByText('You are not part of an organization yet')).toBeInTheDocument();
  });

  it('🔴 draws neither while the read is still in flight', () => {
    // ⚠️ **`/help` had no loading guard at all**, so it showed the empty state
    // to every customer for as long as the read took.
    context.isLoading = true;

    renderHelp();

    expect(
      screen.queryByText('You are not part of an organization yet'),
    ).not.toBeInTheDocument();
  });
});
