/**
 * **The activation progress line** — [TASK-1424](../../../docs/BACKLOG.md),
 * against 📁 `Fortune Signora Home.dc.html` §*Activation*.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const useIntegrations = vi.fn();
const usePreferences = vi.fn();
const mutate = vi.fn();

vi.mock('@/lib/query/hooks/integrations', () => ({
  useIntegrations: (...a: unknown[]) => useIntegrations(...a),
}));
vi.mock('@/lib/query/hooks/preferences', () => ({
  usePreferences: (...a: unknown[]) => usePreferences(...a),
  useSkipInvite: () => ({ mutate, isPending: false }),
}));
vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: () => ({ activeWorkspace: { id: 'w1' } }),
}));
/**
 * ⚠️ **Mocked because `useActivationState` reads the roster** — 📁 *"invite
 * complete means members count is greater than one"*.
 *
 * ⛔ **`useActivationState` itself is deliberately NOT mocked.** ⚡ The line under
 * test is *"progress counts blocking cards only"*, and stubbing the hook would
 * leave nothing here asserting that the count comes from real connections.
 * ✅ **Three mocked reads, one real derivation.**
 */
vi.mock('@/lib/query/hooks/team', () => ({
  useWorkspaceMembers: () => ({ data: { items: [{ user_id: 'me', role: 'owner' }] } }),
}));

const { ActivationProgress } = await import('@/components/home/activation-progress');

const system = (capability: string, working = true) => ({
  integration: 'x',
  capabilities: [capability],
  connectable: true,
  working,
  needs_attention: false,
  connections: [],
});

beforeEach(() => {
  useIntegrations.mockReset();
  usePreferences.mockReset();
  mutate.mockReset();
  usePreferences.mockReturnValue({ data: { first_run_dismissed: true, invite_hidden: false } });
});

describe('📁 "progress counts blocking cards only"', () => {
  it('🔴 reads "of 2" with three cards on the page, because one is optional', () => {
    // ⛔ **Counting the optional card would tell somebody they are two-thirds
    // done when they are finished.**
    useIntegrations.mockReturnValue({ data: [] });

    render(<ActivationProgress />);

    expect(screen.getByText(/Step 1 of 2/)).toBeVisible();
  });

  it('reports the optional card BESIDE the count, never inside it', () => {
    useIntegrations.mockReturnValue({ data: [] });

    render(<ActivationProgress />);

    expect(screen.getByText(/1 optional/)).toBeVisible();
  });

  it('advances as a blocking step completes', () => {
    useIntegrations.mockReturnValue({ data: [system('crm_activity')] });

    render(<ActivationProgress />);

    expect(screen.getByText(/Step 2 of 2/)).toBeVisible();
  });

  it('⛔ and never counts past the total when everything blocking is done', () => {
    useIntegrations.mockReturnValue({
      data: [system('crm_activity'), system('meetings')],
    });

    render(<ActivationProgress />);

    expect(screen.getByText(/Step 2 of 2/)).toBeVisible();
    expect(screen.queryByText(/Step 3/)).not.toBeInTheDocument();
  });
});

describe('🔴 "reversible from the progress line"', () => {
  /**
   * ⚡ **The card is hidden, so the control to bring it back cannot live on the
   * card.** ⛔ **This line is the only place a person can reach it**, which is
   * exactly why the design put it here — and a product that shipped the skip
   * without this would have hidden something for thirty days with no way back.
   */
  it('offers the restore only while the step is hidden', () => {
    useIntegrations.mockReturnValue({ data: [] });
    usePreferences.mockReturnValue({ data: { first_run_dismissed: true, invite_hidden: true } });

    render(<ActivationProgress />);
    screen.getByRole('button', { name: /Show the skipped step/i }).click();

    expect(mutate).toHaveBeenCalledWith(false);
  });

  it('⛔ and offers nothing when there is nothing to restore', () => {
    useIntegrations.mockReturnValue({ data: [] });

    render(<ActivationProgress />);

    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });
});

describe('⛔ silence until both answers are known', () => {
  it('renders nothing while the connections are unread', () => {
    // ⚡ **A line that counted an unread connection as *not done* would tell
    // somebody they had made no progress**, which is worse than a moment of
    // silence.
    useIntegrations.mockReturnValue({ data: undefined, isLoading: true });

    const { container } = render(<ActivationProgress />);

    expect(container).toBeEmptyDOMElement();
  });

  it('renders nothing while the preference is unread', () => {
    useIntegrations.mockReturnValue({ data: [] });
    usePreferences.mockReturnValue({ data: undefined, isLoading: true });

    const { container } = render(<ActivationProgress />);

    expect(container).toBeEmptyDOMElement();
  });
});
