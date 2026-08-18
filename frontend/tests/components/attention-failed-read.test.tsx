/**
 * **A failed workspace read is not an empty one** —
 * [B-237](../../../docs/BUGS.md).
 *
 * 🔴 **[P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md)**: ***a failed read
 * must never render as an empty result*** — ⚠️ **and this was its worst
 * instance.** ⛔ **Every earlier one made a section look empty; this one made
 * the customer's own membership look absent**, and the copy invited them to
 * create an organization they already had.
 */
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, expect, it, vi } from 'vitest';

vi.mock('next/navigation', () => ({
  useSearchParams: () => new URLSearchParams(),
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => '/',
}));

let context = {
  activeWorkspace: null as { id: string; name: string } | null,
  workspaces: [] as unknown[],
  setActiveWorkspace: vi.fn(),
  isLoading: false,
  error: null as Error | null,
};
vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: () => context,
}));

import AttentionPage from '@/app/(app)/attention/page';

function renderPage() {
  return render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <AttentionPage />
    </QueryClientProvider>,
  );
}

describe('🔴 B-237 · the two states are told apart', () => {
  it('⛔ a FAILED read never says the customer has no organization', () => {
    /**
     * ⚠️ **The false claim is the defect, not the missing spinner.** **The
     * customer IS a member** — and the copy it used invites them to create a
     * duplicate.
     */
    context = { ...context, activeWorkspace: null, isLoading: false, error: new Error('500') };

    renderPage();

    expect(screen.queryByText(/You are not part of an organization yet/i)).toBeNull();
  });

  it('✅ and says the read failed instead', () => {
    context = { ...context, activeWorkspace: null, isLoading: false, error: new Error('500') };

    renderPage();

    expect(screen.getByText(/could not load your organizations/i)).toBeVisible();
  });

  it('⚡ a SUCCESSFUL read that returned nothing still says so', () => {
    // ⛔ **The fix must not swallow the real empty state.** A brand-new
    // customer genuinely has no organization, and that screen is their
    // onboarding path.
    context = { ...context, activeWorkspace: null, isLoading: false, error: null };

    renderPage();

    expect(screen.getByText(/You are not part of an organization yet/i)).toBeVisible();
  });
});
