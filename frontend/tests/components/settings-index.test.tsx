/**
 * Whether every settings page can be reached.
 *
 * **`/settings` is the only entrance to `/settings/*`.** Navigation is two
 * entries by design (D38), neither of them a settings child, so a page absent
 * from this screen is a page nobody can open.
 *
 * The Connection Center was in exactly that state: complete — backend, screen,
 * OAuth flow, disconnect, its own tests — and **linked from nowhere.** Every
 * component test for it passed the whole time, because none of them could ask
 * the only question that mattered: *can a customer get here?*
 *
 * **So this test is a route census, not a rendering test.** It asserts that
 * each `/settings/*` route in the application has a link on this page — which
 * is the assertion that would have failed.
 */
import { render, screen } from '@testing-library/react';
import { readdirSync } from 'node:fs';
import { join } from 'node:path';
import type { ReactElement } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const workspaceContext = vi.hoisted(() => vi.fn());

vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: workspaceContext,
}));

vi.mock('@/lib/query/hooks', () => ({
  useCreateWorkspace: () => ({ mutate: vi.fn(), isPending: false }),
}));

// The toast provider lives in the shell, above this page. Stubbed rather than
// wrapped: nothing here raises a toast, and a provider in the tree would be
// scaffolding the assertions do not use.
vi.mock('@/components/feedback/toast', () => ({ useToast: () => ({ toast: vi.fn() }) }));

import SettingsPage from '@/app/(app)/settings/page';

const WORKSPACE = {
  id: 'aaaaaaaa-1111-4111-8111-111111111111',
  name: 'Acme Revenue',
  created_at: '2026-08-01T09:00:00Z',
};

function draw(): ReactElement {
  return <SettingsPage />;
}

beforeEach(() => {
  workspaceContext.mockReturnValue({
    workspaces: [WORKSPACE],
    activeWorkspace: WORKSPACE,
    setActiveWorkspace: vi.fn(),
    isLoading: false,
  });
});

/**
 * Every directory under `app/(app)/settings` holding a `page.tsx` is a route a
 * customer can be sent to. Read from the filesystem rather than listed here on
 * purpose: **a hand-written list would have to be remembered**, and the defect
 * this test exists for was somebody not remembering.
 */
function settingsRoutes(): string[] {
  const dir = join(process.cwd(), 'app', '(app)', 'settings');
  return readdirSync(dir, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => `/settings/${entry.name}`);
}

describe('every settings page has a way in', () => {
  it('finds more than one settings route, or this test is asserting nothing', () => {
    // A census that censuses zero rows passes silently forever.
    expect(settingsRoutes().length).toBeGreaterThan(1);
  });

  it.each(settingsRoutes())('links to %s', (href) => {
    render(draw());

    const links = screen.getAllByRole('link').map((link) => link.getAttribute('href'));
    expect(links).toContain(href);
  });
});

describe('the entrance the Connection Center never had', () => {
  it('offers Connections by name', () => {
    render(draw());

    expect(screen.getByRole('link', { name: 'Connections' })).toBeVisible();
  });

  it('says what a connection is for, in the customer’s terms', () => {
    // Not "OAuth", not "integration adapter", not "provider". A salesperson
    // reads this to decide whether it is worth their afternoon (ADR-0034).
    render(draw());

    expect(
      screen.getByText(/systems Signora reads from to work out which accounts/i),
    ).toBeVisible();
  });

  it('still offers the commercial profile, which was the only link before', () => {
    // **The link is named for the verb since CX-05**, not for the noun. The
    // noun now belongs to `/business`, which is where everybody — including a
    // member — reads it; this card is the half only an owner can do.
    render(draw());

    expect(screen.getByRole('link', { name: 'Change what you sell' })).toBeVisible();
  });

  it('tells an owner that reading it lives somewhere everybody can reach', () => {
    // Two screens would otherwise share the title *Your business* with nothing
    // saying which is which.
    render(draw());

    expect(screen.getByText(/everyone in your organization can/i)).toBeVisible();
  });
});
