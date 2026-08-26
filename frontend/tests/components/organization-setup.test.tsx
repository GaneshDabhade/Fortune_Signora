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
vi.mock('@/components/ui/toast', () => ({
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
    // ⚠️ **A name AND an address now** — 📁 screen `03` made the slug required
    // and the server refuses to invent one. ⚡ **The suggestion is the
    // client's**, from `lib/workspace/slug.ts`, and it is asserted here so a
    // change to the suggester cannot silently alter what this form sends.
    expect(createMutate).toHaveBeenCalledWith(
      { name: 'Northwind APAC', slug: 'northwind-apac' },
      expect.anything(),
    );
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

/**
 * 🔴 **The one field 📁 the design marks EDITABLE was the one shown bare.**
 *
 * 📁 `Fortune Signora Settings.dc.html` → `workspaceFields`:
 * `{ label: 'Workspace name', note: 'Shown in the rail and on exports',
 * action: 'Edit', locked: false }`.
 *
 * ⛔ **There is no `PATCH /workspaces/{id}`** — measured against
 * `openapi.json`, the API offers `POST` and `GET` and nothing else. **So the
 * name cannot be changed.**
 *
 * ⚠️ **Five fields on this page already say why they are locked.** **This one
 * said nothing**, so a reader looking for the rename the design promises could
 * not tell a missing control from a missing feature — ⛔ **which is the
 * distinction every other absence on this screen is careful to draw.**
 */
describe('🔴 the organization name says why it cannot be renamed', () => {
  it('states the absence beside the value, not instead of it', () => {
    render(<OrganizationSetupPage />);

    // ✅ **The value is still there** — this is a locked fact, not a missing one.
    expect(screen.getByText(workspace.name)).toBeInTheDocument();
    expect(screen.getByText(/nothing can rename one/i)).toBeInTheDocument();
  });

  /**
   * ⛔ **No internal vocabulary in customer copy.**
   *
   * ⚠️ **The first draft of this banned the substring *"not built"* and fired
   * on three sentences, two of which are fine** — *"a custom URL needs the
   * change procedure… which is not built"* explains WHICH mechanism is
   * missing, after saying what the product does. ⛔ **That is the
   * instrument-too-wide failure**: it fails loudly on things that are not
   * defects, which is the fastest way to get an assertion deleted.
   *
   * ✅ **What it caught was real**: *"**The design requires** every choice to
   * clear a 4.5:1 contrast check"* — **a customer has no design document**, and
   * told that *the design* requires something they learn that Signora has an
   * internal artefact rather than what the product will do for them. 📁 The
   * same class as [ADR-0034](../../../CLAUDE.md)'s *workspace* reaching a
   * screen.
   *
   * ⚡ **So the oracle names the vocabulary rather than the phrasing.**
   */
  it('⛔ and never explains itself with an internal artefact', () => {
    const { container } = render(<OrganizationSetupPage />);
    const text = container.textContent ?? '';

    for (const leak of [
      /\bthe design (requires|says|specifies|draws)\b/i,
      /\bcoming soon\b/i,
      /\bthe backlog\b/i,
      /\bnot implemented\b/i,
      /\bTODO\b/,
    ]) {
      expect(text, `customer copy leaks internal vocabulary: ${leak}`).not.toMatch(leak);
    }

    // ⚠️ **Vacuity half** — the page rendered something to check.
    expect(text.length).toBeGreaterThan(200);
  });
});
