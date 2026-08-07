import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { LockedField } from '@/components/ui';

/**
 * TASK-468 — Organization setup.
 *
 * **These assert the design's stated rules, not its markup.** The rule that
 * matters most is its own rationale: *"Locked is shown, not hidden — removing
 * them from the page makes administrators think the product lost a feature."*
 * A test that only counted headings would pass while the screen quietly
 * dropped every capability the platform cannot yet do.
 */

const workspace = {
  id: 'w-1',
  name: 'Northwind',
  created_at: '2026-03-14T09:00:00Z',
  updated_at: '2026-03-14T09:00:00Z',
};

const state = {
  workspaces: [workspace],
  activeWorkspace: workspace as typeof workspace | null,
  setActiveWorkspace: vi.fn(),
  isLoading: false,
  error: null as Error | null,
};

const createMutate = vi.fn();

vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: () => state,
}));
vi.mock('@/lib/query/hooks', () => ({
  useCreateWorkspace: () => ({ mutate: createMutate, isPending: false }),
}));
vi.mock('@/components/feedback/toast', () => ({
  useToast: () => ({ toast: vi.fn() }),
}));

const { default: OrganizationSetupPage } = await import(
  '@/app/(app)/settings/organization/page'
);

function reset(overrides: Partial<typeof state> = {}) {
  Object.assign(state, {
    workspaces: [workspace],
    activeWorkspace: workspace,
    setActiveWorkspace: vi.fn(),
    isLoading: false,
    error: null,
    ...overrides,
  });
  createMutate.mockReset();
}

describe('LockedField', () => {
  it('requires a reason, because a padlock without one is worse than an absent field', () => {
    render(<LockedField label="Data region" reason="Not yet selectable." />);
    expect(screen.getByText('Data region')).toBeInTheDocument();
    expect(screen.getByText('Not yet selectable.')).toBeInTheDocument();
  });

  it('renders no value when none is known, rather than inventing one', () => {
    const { container } = render(
      <LockedField label="Brand colour" reason="Not yet selectable." />,
    );
    // Two paragraphs would mean a value was rendered; P-A: an absent read
    // must never render as a real one.
    expect(container.querySelectorAll('p')).toHaveLength(1);
  });

  it('renders a value when there is one', () => {
    render(<LockedField label="Region" value="eu-west" reason="Permanent." />);
    expect(screen.getByText('eu-west')).toBeInTheDocument();
  });
});

describe('Organization setup', () => {
  it('names every capability the design specifies, including the ones not built', () => {
    reset();
    render(<OrganizationSetupPage />);
    // The design's own sections. Dropping one because its backend is absent
    // is exactly what its rationale forbids.
    for (const heading of ['Overview', 'Branding', 'Domains', 'Switching', 'Danger zone']) {
      expect(screen.getByText(heading)).toBeInTheDocument();
    }
  });

  it('shows the five absent capabilities locked, each with a reason', () => {
    reset();
    render(<OrganizationSetupPage />);
    for (const label of [
      'Organization URL',
      'Data region',
      'Logo',
      'Brand colour',
      'Delete this organization',
    ]) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
  });

  it('invents no value for any capability the platform cannot answer', () => {
    reset();
    render(<OrganizationSetupPage />);
    // A region selector, a colour swatch or a URL would each be mock business
    // data (§20c) — and worse than absent, because a customer would use them.
    expect(screen.queryByRole('combobox')).not.toBeInTheDocument();
    expect(screen.queryByText(/signora\.app\//)).not.toBeInTheDocument();
  });

  it('renders what the platform genuinely knows', () => {
    reset();
    render(<OrganizationSetupPage />);
    expect(screen.getByText('Northwind')).toBeInTheDocument();
  });

  it('creates through the existing path, trimmed', async () => {
    reset();
    const user = userEvent.setup();
    render(<OrganizationSetupPage />);
    await user.type(screen.getByLabelText('Organization name'), '  Northwind APAC  ');
    await user.click(screen.getByRole('button', { name: 'Create organization' }));
    expect(createMutate).toHaveBeenCalledWith('Northwind APAC', expect.anything());
  });

  it('refuses to submit a blank name', async () => {
    reset();
    const user = userEvent.setup();
    render(<OrganizationSetupPage />);
    await user.type(screen.getByLabelText('Organization name'), '   ');
    expect(screen.getByRole('button', { name: 'Create organization' })).toBeDisabled();
    expect(createMutate).not.toHaveBeenCalled();
  });

  it('renders a failed read as an error, never as an empty organization', () => {
    // P-A, and the state §13 says gets skipped. An empty screen here would
    // tell an administrator their organization has no settings.
    reset({ error: new Error('down'), activeWorkspace: null, workspaces: [] });
    render(<OrganizationSetupPage />);
    // ⚠️ **Asserted on the sentence, not on a role.** `StatedAbsence`'s `page`
    // variant renders through `EmptyState`, so the shape of a failed read and
    // an empty one is identical and **the copy is the whole of what
    // distinguishes them** — which is precisely why P-A insists the sentence
    // is stated rather than implied. A test asserting `role="alert"` here
    // would be asserting something the shared component does not do.
    expect(screen.getAllByText(/could not load/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Signora could not load/)).toBeInTheDocument();
    expect(screen.queryByText('Danger zone')).not.toBeInTheDocument();
  });

  it('distinguishes a single organization from a missing one', () => {
    reset();
    render(<OrganizationSetupPage />);
    expect(screen.getByText('This is your only organization')).toBeInTheDocument();
  });

  it('offers the other organizations when there are any', () => {
    const second = { ...workspace, id: 'w-2', name: 'Northwind APAC' };
    reset({ workspaces: [workspace, second] });
    render(<OrganizationSetupPage />);
    expect(screen.getByRole('button', { name: 'Northwind APAC' })).toBeInTheDocument();
  });

  it('marks the organization currently open, so switching is not guesswork', () => {
    const second = { ...workspace, id: 'w-2', name: 'Northwind APAC' };
    reset({ workspaces: [workspace, second] });
    render(<OrganizationSetupPage />);
    expect(screen.getByRole('button', { name: 'Northwind' })).toHaveAttribute(
      'aria-current',
      'true',
    );
  });

  it('never shows a customer the platform word', () => {
    reset();
    const { container } = render(<OrganizationSetupPage />);
    // ADR-0034, and the reason C-239 exists: the design says "workspace"
    // throughout and a customer may not be shown it.
    expect(container.textContent).not.toMatch(/workspace/i);
  });
});
