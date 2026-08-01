/**
 * The screen where a customer says who has to agree.
 *
 * These assert the rules that keep a *declaration* honest: that it is saved
 * whole, that roles are job titles rather than people, that a concurrent save
 * is refused rather than resolved, and — the one that matters most — that the
 * screen ranks nobody and assesses nothing.
 */
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactElement } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { BuyingCommitteeEditor } from '@/components/commercial/committee';
import type {
  BuyingCommittee,
  ProductCatalog,
  ProductCommittee,
} from '@/lib/api/types';

const request = vi.hoisted(() => vi.fn());

vi.mock('@/lib/api/client', async () => {
  const actual =
    await vi.importActual<typeof import('@/lib/api/client')>('@/lib/api/client');
  return { ...actual, apiRequest: request };
});

const WORKSPACE = 'aaaaaaaa-1111-4111-8111-111111111111';
const CORE = 'bbbbbbbb-2222-4222-8222-222222222222';
const ENTERPRISE = 'dddddddd-4444-4444-8444-444444444444';

function catalog(overrides: Partial<ProductCatalog> = {}): ProductCatalog {
  return {
    version: 2,
    products: [{ id: CORE, name: 'Revenue Cloud', description: 'Pipeline generation' }],
    updated_at: '2026-08-01T09:00:00Z',
    updated_by: 'cccccccc-3333-4333-8333-333333333333',
    ...overrides,
  };
}

function committee(overrides: Partial<ProductCommittee> = {}): ProductCommittee {
  return {
    product_id: CORE,
    roles: [{ title: 'Chief Financial Officer', part: 'economic_buyer' }],
    ...overrides,
  };
}

function declaration(overrides: Partial<BuyingCommittee> = {}): BuyingCommittee {
  return {
    version: 3,
    committees: [committee()],
    updated_at: '2026-08-01T09:00:00Z',
    updated_by: 'cccccccc-3333-4333-8333-333333333333',
    ...overrides,
  };
}

function withQuery(node: ReactElement) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return <QueryClientProvider client={client}>{node}</QueryClientProvider>;
}

function editor(
  overrides: Partial<BuyingCommittee> = {},
  catalogOverrides: Partial<ProductCatalog> = {},
) {
  return withQuery(
    <BuyingCommitteeEditor
      catalog={catalog(catalogOverrides)}
      declaration={declaration(overrides)}
      workspaceId={WORKSPACE}
    />,
  );
}

/** The request the component actually made. */
function sent(): { path: string; method?: string; body: Record<string, unknown> } {
  const call = request.mock.calls[0];
  expect(call, 'nothing was sent to the API').toBeDefined();
  const [path, options] = call as [
    string,
    { method?: string; body: Record<string, unknown> },
  ];
  return { path, method: options.method, body: options.body };
}

function firstCommittee(): ProductCommittee {
  const [entry] = (sent().body as { committees: ProductCommittee[] }).committees;
  expect(entry, 'the request carried no committee').toBeDefined();
  return entry as ProductCommittee;
}

beforeEach(() => {
  request.mockReset();
  request.mockResolvedValue(declaration({ version: 4 }));
});

describe('a company that has declared no committee', () => {
  it('says so per product rather than showing an error', () => {
    render(editor({ version: 0, committees: [], updated_at: null, updated_by: null }));

    expect(screen.getByText('Nobody described yet.')).toBeInTheDocument();
  });

  it('claims no author or date it does not have', () => {
    const { container } = render(
      editor({ version: 0, committees: [], updated_at: null, updated_by: null }),
    );

    expect(container.textContent).not.toMatch(/version 0/i);
    expect(container.textContent).not.toMatch(/last changed/i);
  });

  it('asks for a product before a committee', () => {
    render(
      editor(
        { version: 0, committees: [], updated_at: null, updated_by: null },
        { version: 0, products: [], updated_at: null, updated_by: null },
      ),
    );

    expect(screen.getByText('Add a product first')).toBeInTheDocument();
  });
});

describe('the committee is saved whole', () => {
  it('sends every product with a committee, not just the edited one', async () => {
    const user = userEvent.setup();
    render(
      editor(
        { committees: [committee(), committee({ product_id: ENTERPRISE })] },
        {
          products: [
            { id: CORE, name: 'Revenue Cloud', description: '' },
            { id: ENTERPRISE, name: 'Enterprise', description: '' },
          ],
        },
      ),
    );

    await user.click(
      screen.getByRole('button', { name: 'Describe who decides about Revenue Cloud' }),
    );
    await user.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() => expect(request).toHaveBeenCalled());
    const body = sent().body as { committees: ProductCommittee[] };
    expect(body.committees.map((entry) => entry.product_id)).toEqual([CORE, ENTERPRISE]);
  });

  it('quotes the version it is replacing', async () => {
    const user = userEvent.setup();
    render(editor());

    await user.click(
      screen.getByRole('button', { name: 'Describe who decides about Revenue Cloud' }),
    );
    await user.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() => expect(request).toHaveBeenCalled());
    expect(sent().body.expected_version).toBe(3);
    expect(sent().method).toBe('PUT');
    expect(sent().path).toBe(`/workspaces/${WORKSPACE}/buying-committee`);
  });

  it('removing a committee sends the others, never a delete', async () => {
    const user = userEvent.setup();
    render(
      editor(
        { committees: [committee(), committee({ product_id: ENTERPRISE })] },
        {
          products: [
            { id: CORE, name: 'Revenue Cloud', description: '' },
            { id: ENTERPRISE, name: 'Enterprise', description: '' },
          ],
        },
      ),
    );

    await user.click(
      screen.getByRole('button', { name: 'Remove the committee for Revenue Cloud' }),
    );

    await waitFor(() => expect(request).toHaveBeenCalled());
    const body = sent().body as { committees: ProductCommittee[] };
    expect(body.committees.map((entry) => entry.product_id)).toEqual([ENTERPRISE]);
    expect(sent().method).toBe('PUT');
  });
});

describe('roles are job titles the customer typed', () => {
  it('sends the title and the part, and nothing else', async () => {
    // **A role has two fields.** A weight, a seniority or an importance would
    // each turn a declaration into a scoring input.
    const user = userEvent.setup();
    render(editor({ committees: [] }));

    await user.click(
      screen.getByRole('button', { name: 'Describe who decides about Revenue Cloud' }),
    );
    await user.type(screen.getByLabelText('Role'), 'Head of Clinical Informatics');
    await user.selectOptions(screen.getByLabelText('Part they play'), 'champion');
    await user.click(screen.getByRole('button', { name: 'Add role' }));
    await user.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() => expect(request).toHaveBeenCalled());
    expect(firstCommittee().roles).toEqual([
      { title: 'Head of Clinical Informatics', part: 'champion' },
    ]);
  });

  it('keeps the customer’s capitalisation', async () => {
    const user = userEvent.setup();
    render(editor({ committees: [] }));

    await user.click(
      screen.getByRole('button', { name: 'Describe who decides about Revenue Cloud' }),
    );
    await user.type(screen.getByLabelText('Role'), 'VP of RevOps');
    await user.click(screen.getByRole('button', { name: 'Add role' }));
    await user.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() => expect(request).toHaveBeenCalled());
    expect(firstCommittee().roles[0]?.title).toBe('VP of RevOps');
  });

  it('does not add the same title twice', async () => {
    const user = userEvent.setup();
    render(editor({ committees: [] }));

    await user.click(
      screen.getByRole('button', { name: 'Describe who decides about Revenue Cloud' }),
    );
    await user.type(screen.getByLabelText('Role'), 'CFO');
    await user.click(screen.getByRole('button', { name: 'Add role' }));
    await user.type(screen.getByLabelText('Role'), 'cfo');
    await user.click(screen.getByRole('button', { name: 'Add role' }));
    await user.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() => expect(request).toHaveBeenCalled());
    expect(firstCommittee().roles).toHaveLength(1);
  });

  it('two gatekeepers are allowed — only the title has to differ', async () => {
    const user = userEvent.setup();
    render(editor({ committees: [] }));

    await user.click(
      screen.getByRole('button', { name: 'Describe who decides about Revenue Cloud' }),
    );
    await user.type(screen.getByLabelText('Role'), 'Head of Security');
    await user.selectOptions(screen.getByLabelText('Part they play'), 'gatekeeper');
    await user.click(screen.getByRole('button', { name: 'Add role' }));
    await user.type(screen.getByLabelText('Role'), 'General Counsel');
    await user.click(screen.getByRole('button', { name: 'Add role' }));
    await user.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() => expect(request).toHaveBeenCalled());
    expect(firstCommittee().roles.map((role) => role.part)).toEqual([
      'gatekeeper',
      'gatekeeper',
    ]);
  });

  it('refuses to send a committee with nobody in it', async () => {
    // The server refuses it too. Here it is a disabled button, because
    // refusing before somebody has typed anything is not news to them.
    const user = userEvent.setup();
    render(editor({ committees: [] }));

    await user.click(
      screen.getByRole('button', { name: 'Describe who decides about Revenue Cloud' }),
    );

    expect(screen.getByRole('button', { name: 'Save' })).toBeDisabled();
    expect(request).not.toHaveBeenCalled();
  });
});

describe('a refusal is shown, never resolved', () => {
  it('reports what the server said when a colleague saved first', async () => {
    const user = userEvent.setup();
    const { ApiError } = await import('@/lib/api/client');
    request.mockRejectedValue(
      new ApiError(409, {
        code: 'committee_version_conflict',
        message: 'your buying committee is at version 4, not 3. Reload before saving.',
        correlation_id: 'corr-1',
      }),
    );
    render(editor());

    await user.click(
      screen.getByRole('button', { name: 'Describe who decides about Revenue Cloud' }),
    );
    await user.click(screen.getByRole('button', { name: 'Save' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('version 4, not 3');
  });
});

describe('it records seats; it evaluates nobody', () => {
  it('shows no influence, rank or assessment', () => {
    // **The boundary, on the screen.** A committee is one plausible field
    // away from an influence model, and the screen is where it would show.
    const { container } = render(editor());

    for (const verdict of [
      /\binfluence\b/i,
      /\bscore\b/i,
      /\brank/i,
      /\bseniority\b/i,
      /\bcomplete\b/i,
      /\bmissing\b/i,
      /\d+\s*%/,
    ]) {
      expect(container.textContent).not.toMatch(verdict);
    }
  });

  it('offers nowhere to name a person', () => {
    // A committee is a template of roles. Person entities are deferred
    // platform-wide, and a name field here would collect personal data with
    // no consumer and no declared basis for holding it.
    render(editor());

    expect(screen.queryByLabelText(/name/i)).not.toBeInTheDocument();
  });
});
