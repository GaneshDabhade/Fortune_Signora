/**
 * What a brand-new account actually sees.
 *
 * **A page-level test, deliberately.** The defect (D36) was not that a
 * component was missing — it was that *every branch on the page tested a
 * falsy value*, so nothing rendered at all. A component test on the empty
 * state would have passed throughout the bug's lifetime.
 *
 * This became testable, and findable, only once somebody could sign in.
 */
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactElement } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const workspaceContext = vi.hoisted(() => vi.fn());
const accounts = vi.hoisted(() => vi.fn());
const identities = vi.hoisted(() => vi.fn());
const catalog = vi.hoisted(() => vi.fn());
const decided = vi.hoisted(() => vi.fn());
const targets = vi.hoisted(() => vi.fn());

vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: workspaceContext,
}));

vi.mock('@/lib/query/hooks/commercial', () => ({
  useTargetAccounts: targets,
}));

vi.mock('@/lib/query/hooks', () => ({
  useAccounts: accounts,
  useAccountIdentities: identities,
  useSignalCatalog: catalog,
  useDecidedAccounts: decided,
}));

import AttentionPage from '@/app/(app)/page';

const IDLE = { data: undefined, isLoading: false, isError: false };

function withQuery(node: ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={client}>{node}</QueryClientProvider>;
}

beforeEach(() => {
  // Exactly what react-query returns for a disabled query: not loading, not
  // errored, no data. Reproducing that shape is the whole point — it is what
  // made every branch fall through.
  accounts.mockReturnValue(IDLE);
  identities.mockReturnValue(IDLE);
  // A reader with no organization has decided about nothing, and the section
  // renders nothing for an empty page — which is what keeps this screen's
  // assertion (*a heading and nothing else is a bug*) meaningful.
  decided.mockReturnValue(IDLE);
  catalog.mockReturnValue(IDLE);
  // No declaration loaded: the empty state keeps its established wording
  // rather than guessing, which is the case this screen is about.
  targets.mockReturnValue(IDLE);
});

describe('a signed-in reader who belongs to no organization', () => {
  it('is told why the screen is empty, rather than shown an empty screen', () => {
    workspaceContext.mockReturnValue({
      workspaces: [],
      activeWorkspace: null,
      isLoading: false,
    });

    render(withQuery(<AttentionPage />));

    expect(screen.getByText(/not part of an organization yet/i)).toBeInTheDocument();
  });

  it('is not told anything while the answer is still being fetched', () => {
    // Announcing "you belong to no organization" during the first paint would be a
    // confident wrong answer to somebody who has three.
    workspaceContext.mockReturnValue({
      workspaces: [],
      activeWorkspace: null,
      isLoading: true,
    });

    render(withQuery(<AttentionPage />));

    expect(screen.queryByText(/not in a workspace yet/i)).not.toBeInTheDocument();
  });

  it('sees the ordinary empty state once they have one', () => {
    // A workspace with no accounts is a different sentence with a different
    // next action, and the page must not confuse the two.
    workspaceContext.mockReturnValue({
      workspaces: [{ id: 'w1', name: 'Acme' }],
      activeWorkspace: { id: 'w1', name: 'Acme' },
      isLoading: false,
    });
    accounts.mockReturnValue({ data: { items: [] }, isLoading: false, isError: false });

    render(withQuery(<AttentionPage />));

    expect(screen.queryByText(/not in a workspace yet/i)).not.toBeInTheDocument();
  });

  it('never renders a heading and nothing else', () => {
    // **The regression this file exists for.** The page had four branches and
    // all four tested a falsy value, so a reader with no workspace got the
    // title and blank space — indistinguishable from a broken page.
    workspaceContext.mockReturnValue({
      workspaces: [],
      activeWorkspace: null,
      isLoading: false,
    });

    const { container } = render(withQuery(<AttentionPage />));
    const body = (container.textContent ?? '').replace(
      /Attention|Accounts your evidence says are worth a look, most pressing first\./g,
      '',
    );

    expect(body.trim().length).toBeGreaterThan(0);
  });
});

describe('an empty list says why it is empty', () => {
  // **One sentence used to cover two different situations.** "Nothing needs
  // your attention" is true of a workspace Signora has watched for weeks. It
  // is not true of one that has never been told which companies to watch —
  // there the product reported an empty *result* where the truth was an empty
  // *input*, and a new customer would reasonably conclude Signora had looked.

  beforeEach(() => {
    workspaceContext.mockReturnValue({
      workspaces: [{ id: 'w1', name: 'Acme' }],
      activeWorkspace: { id: 'w1', name: 'Acme' },
      isLoading: false,
    });
    accounts.mockReturnValue({ ...IDLE, data: { items: [], next_cursor: null, has_more: false } });
  });

  it('tells a new organization that nobody has asked Signora anything', () => {
    targets.mockReturnValue({ ...IDLE, data: { version: 0, accounts: [], updated_at: null, updated_by: null } });

    render(withQuery(<AttentionPage />));

    expect(screen.getByText(/does not know which companies to watch/i)).toBeInTheDocument();
  });

  it('says it is empty because it was not asked, not because it found nothing', () => {
    targets.mockReturnValue({ ...IDLE, data: { version: 0, accounts: [], updated_at: null, updated_by: null } });

    render(withQuery(<AttentionPage />));

    expect(screen.getByText(/not because it found nothing/i)).toBeInTheDocument();
  });

  it('keeps the established wording once companies have been declared', () => {
    // A workspace that is being watched and has nothing hot today is the case
    // the original sentence was written for, and it stays.
    targets.mockReturnValue({
      ...IDLE,
      data: { version: 3, accounts: [{ id: 'a', name: 'Initech' }], updated_at: '2026-08-01T09:00:00Z', updated_by: 'u1' },
    });

    render(withQuery(<AttentionPage />));

    expect(screen.getByText('Nothing needs your attention')).toBeInTheDocument();
  });

  it('does not guess while the declaration is still loading', () => {
    // Announcing "nobody has told Signora anything" to a workspace that has is
    // the confident wrong answer this page refuses everywhere else.
    targets.mockReturnValue(IDLE);

    render(withQuery(<AttentionPage />));

    expect(screen.getByText('Nothing needs your attention')).toBeInTheDocument();
  });

  it('offers no control, because the reader may not be able to use one', () => {
    // The guided first run is C-007 and is deliberately unscheduled; a call to
    // action here would answer part of it by accident. An owner has Settings
    // in the navigation, and a member cannot declare a watch list at all.
    targets.mockReturnValue({ ...IDLE, data: { version: 0, accounts: [], updated_at: null, updated_by: null } });

    render(withQuery(<AttentionPage />));

    expect(screen.queryByRole('link', { name: /settings/i })).toBeNull();
  });
});
