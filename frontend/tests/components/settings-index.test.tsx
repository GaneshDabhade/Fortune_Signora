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
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
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
vi.mock('@/components/ui/toast', () => ({ useToast: () => ({ toast: vi.fn() }) }));

import SettingsPage from '@/app/(app)/settings/page';

const WORKSPACE = {
  id: 'aaaaaaaa-1111-4111-8111-111111111111',
  name: 'Acme Revenue',
  created_at: '2026-08-01T09:00:00Z',
};

/**
 * ⚡ **A `QueryClientProvider`, because the page now READS.**
 *
 * ⛔ **It did not before**: `/settings` was six cards of static copy, so the
 * only thing to mock was the workspace context. 📁 **The design's page renders
 * the audit log inline** — `useOrganizationHistory` — **so the census now has
 * to mount a component that queries.**
 *
 * ⚠️ **This is a harness change, not a weakening.** ✅ **Every assertion below
 * is unchanged**, and the one that matters — *every settings route has an
 * entrance* — is the invariant `infra/reachability.py` enforces from the other
 * side.
 */
function draw(): ReactElement {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return (
    <QueryClientProvider client={client}>
      <SettingsPage />
    </QueryClientProvider>
  );
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
    // 📁 **The design's section is titled *"Integrations"* and its link opens
    // the Connection Center.** ⛔ **The assertion was `{ name: 'Connections' }`
    // exactly**, which pinned the old index card's link text rather than the
    // property: *the Connection Center has an entrance*. ⚡ **That property is
    // what B-nnn was about** — *"shipped complete and linked from nowhere"* —
    // **and it holds under either wording.**
    render(draw());

    expect(screen.getByRole('link', { name: /connections/i })).toHaveAttribute(
      'href',
      '/settings/connections',
    );
  });

  it('says what a connection is for, in the customer’s terms', () => {
    // Not "OAuth", not "integration adapter", not "provider". A salesperson
    // reads this to decide whether it is worth their afternoon (ADR-0034).
    render(draw());

    // ⚡ **`getAllByText`, because the design says it TWICE** — the section's
    // meta line and the sentence beneath it — ⛔ and a `getByText` that throws
    // on the design being consistent is asserting the wrong thing.
    expect(
      screen.getAllByText(/systems Signora reads from/i)[0]!,
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
    // 🔴 **The sentence this asserted belonged to the index card the design
    // replaced**, and the ambiguity it resolved is gone with it: 📁 **there is
    // no longer a Settings screen titled *Your business***, so two screens no
    // longer share a title. ⚡ **What survives is that the editor is reachable
    // and named in the customer's words**, which is what the row was for.
    render(draw());

    expect(screen.getByRole('link', { name: 'Change what you sell' })).toHaveAttribute(
      'href',
      '/settings/products',
    );
  });
});
