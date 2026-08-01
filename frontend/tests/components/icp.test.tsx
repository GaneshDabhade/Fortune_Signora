/**
 * The screen where a customer says who buys what they sell.
 *
 * These assert the rules that keep a *description* honest: that it is saved
 * whole, that it is stored in the customer's own words, that a concurrent save
 * is refused rather than resolved, and — the one that matters most — that
 * nothing on this screen grades a company against the description.
 */
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactElement } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { IcpEditor } from '@/components/commercial/icp';
import type { IcpDeclaration, ProductCatalog, ProductIcp } from '@/lib/api/types';

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

function profile(overrides: Partial<ProductIcp> = {}): ProductIcp {
  return {
    product_id: CORE,
    industries: ['Financial Services'],
    countries: ['United Kingdom'],
    employees: { minimum: 200, maximum: 2000 },
    notes: '',
    ...overrides,
  };
}

function declaration(overrides: Partial<IcpDeclaration> = {}): IcpDeclaration {
  return {
    version: 3,
    profiles: [profile()],
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
  overrides: Partial<IcpDeclaration> = {},
  catalogOverrides: Partial<ProductCatalog> = {},
) {
  return withQuery(
    <IcpEditor
      catalog={catalog(catalogOverrides)}
      declaration={declaration(overrides)}
      workspaceId={WORKSPACE}
    />,
  );
}

/** The first profile in the request the component made. */
function firstProfile(): ProductIcp {
  const [entry] = (sent().body as { profiles: ProductIcp[] }).profiles;
  expect(entry, 'the request carried no profile').toBeDefined();
  return entry as ProductIcp;
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

beforeEach(() => {
  request.mockReset();
  request.mockResolvedValue(declaration({ version: 4 }));
});

describe('a company that has described nobody', () => {
  it('says so per product rather than showing an error', () => {
    render(editor({ version: 0, profiles: [], updated_at: null, updated_by: null }));

    expect(screen.getByText('Nobody described yet.')).toBeInTheDocument();
  });

  it('claims no author or date it does not have', () => {
    const { container } = render(
      editor({ version: 0, profiles: [], updated_at: null, updated_by: null }),
    );

    expect(container.textContent).not.toMatch(/version 0/i);
    expect(container.textContent).not.toMatch(/last changed/i);
  });

  it('asks for a product before a buyer', () => {
    // An ideal customer is the kind of company that buys something specific,
    // so there is nothing to describe until the catalog says what.
    render(
      editor(
        { version: 0, profiles: [], updated_at: null, updated_by: null },
        { version: 0, products: [], updated_at: null, updated_by: null },
      ),
    );

    expect(screen.getByText('Add a product first')).toBeInTheDocument();
  });
});

describe('the description is saved whole', () => {
  it('sends every product described, not just the edited one', async () => {
    // The declaration is the versioned unit. Sending one change would make
    // what gets stored depend on what was there when the request arrived.
    const user = userEvent.setup();
    render(
      editor(
        { profiles: [profile(), profile({ product_id: ENTERPRISE })] },
        {
          products: [
            { id: CORE, name: 'Revenue Cloud', description: '' },
            { id: ENTERPRISE, name: 'Enterprise', description: '' },
          ],
        },
      ),
    );

    await user.click(
      screen.getByRole('button', { name: 'Describe who buys Revenue Cloud' }),
    );
    await user.type(screen.getByLabelText('Industries'), 'Insurance');
    await user.click(screen.getByRole('button', { name: 'Add industries' }));
    await user.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() => expect(request).toHaveBeenCalled());
    const body = sent().body as { profiles: ProductIcp[] };
    expect(body.profiles.map((entry) => entry.product_id)).toEqual([CORE, ENTERPRISE]);
  });

  it('quotes the version it is replacing', async () => {
    const user = userEvent.setup();
    render(editor());

    await user.click(
      screen.getByRole('button', { name: 'Describe who buys Revenue Cloud' }),
    );
    await user.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() => expect(request).toHaveBeenCalled());
    expect(sent().body.expected_version).toBe(3);
    expect(sent().method).toBe('PUT');
    expect(sent().path).toBe(`/workspaces/${WORKSPACE}/icp`);
  });

  it('removing a description sends the others, never a delete', async () => {
    // Nothing is deleted: a change is a new version, and the one that
    // contained the description stays readable.
    const user = userEvent.setup();
    render(
      editor(
        { profiles: [profile(), profile({ product_id: ENTERPRISE })] },
        {
          products: [
            { id: CORE, name: 'Revenue Cloud', description: '' },
            { id: ENTERPRISE, name: 'Enterprise', description: '' },
          ],
        },
      ),
    );

    await user.click(
      screen.getByRole('button', { name: 'Remove the description for Revenue Cloud' }),
    );

    await waitFor(() => expect(request).toHaveBeenCalled());
    const body = sent().body as { profiles: ProductIcp[] };
    expect(body.profiles.map((entry) => entry.product_id)).toEqual([ENTERPRISE]);
    expect(sent().method).toBe('PUT');
  });
});

describe('what the customer typed is what is sent', () => {
  it('keeps their capitalisation', async () => {
    // A screen that records has no business tidying somebody's words.
    const user = userEvent.setup();
    render(editor({ profiles: [] }));

    await user.click(
      screen.getByRole('button', { name: 'Describe who buys Revenue Cloud' }),
    );
    await user.type(screen.getByLabelText('Industries'), 'Financial Services');
    await user.click(screen.getByRole('button', { name: 'Add industries' }));
    await user.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() => expect(request).toHaveBeenCalled());
    expect(firstProfile().industries).toEqual(['Financial Services']);
  });

  it('sends no size when neither bound was given', async () => {
    // "No size preference" is said by leaving size out, not by an empty range
    // — which the server refuses outright.
    const user = userEvent.setup();
    render(editor({ profiles: [] }));

    await user.click(
      screen.getByRole('button', { name: 'Describe who buys Revenue Cloud' }),
    );
    await user.type(screen.getByLabelText('Industries'), 'Insurance');
    await user.click(screen.getByRole('button', { name: 'Add industries' }));
    await user.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() => expect(request).toHaveBeenCalled());
    expect(firstProfile().employees).toBeNull();
  });

  it('sends one bound when only one was given', async () => {
    const user = userEvent.setup();
    render(editor({ profiles: [] }));

    await user.click(
      screen.getByRole('button', { name: 'Describe who buys Revenue Cloud' }),
    );
    await user.type(screen.getByLabelText('Smallest, in people'), '500');
    await user.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() => expect(request).toHaveBeenCalled());
    expect(firstProfile().employees).toEqual({ minimum: 500, maximum: null });
  });

  it('refuses to send a description with nothing in it', async () => {
    // The server refuses it too. Here it is a disabled button, because
    // refusing before somebody has typed anything is not news to them.
    const user = userEvent.setup();
    render(editor({ profiles: [] }));

    await user.click(
      screen.getByRole('button', { name: 'Describe who buys Revenue Cloud' }),
    );

    expect(screen.getByRole('button', { name: 'Save' })).toBeDisabled();
    expect(request).not.toHaveBeenCalled();
  });

  it('does not add the same industry twice', async () => {
    const user = userEvent.setup();
    render(editor({ profiles: [] }));

    await user.click(
      screen.getByRole('button', { name: 'Describe who buys Revenue Cloud' }),
    );
    await user.type(screen.getByLabelText('Industries'), 'Fintech');
    await user.click(screen.getByRole('button', { name: 'Add industries' }));
    await user.type(screen.getByLabelText('Industries'), 'fintech');
    await user.click(screen.getByRole('button', { name: 'Add industries' }));
    await user.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() => expect(request).toHaveBeenCalled());
    expect(firstProfile().industries).toEqual(['Fintech']);
  });
});

describe('a refusal is shown, never resolved', () => {
  it('reports what the server said when a colleague saved first', async () => {
    const user = userEvent.setup();
    const { ApiError } = await import('@/lib/api/client');
    request.mockRejectedValue(
      new ApiError(409, {
        code: 'icp_version_conflict',
        message: 'your ideal customer is at version 4, not 3. Reload before saving.',
        correlation_id: 'corr-1',
      }),
    );
    render(editor());

    await user.click(
      screen.getByRole('button', { name: 'Describe who buys Revenue Cloud' }),
    );
    await user.click(screen.getByRole('button', { name: 'Save' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('version 4, not 3');
  });

  it('shows nothing as saved before the server accepted it', async () => {
    const user = userEvent.setup();
    let resolve: (value: IcpDeclaration) => void = () => {};
    request.mockReturnValue(
      new Promise<IcpDeclaration>((settle) => {
        resolve = settle;
      }),
    );
    render(editor({ profiles: [] }));

    await user.click(
      screen.getByRole('button', { name: 'Describe who buys Revenue Cloud' }),
    );
    await user.type(screen.getByLabelText('Industries'), 'Insurance');
    await user.click(screen.getByRole('button', { name: 'Add industries' }));
    await user.click(screen.getByRole('button', { name: 'Save' }));

    // The row still says nobody has been described, because nobody has.
    expect(screen.getByText('Nobody described yet.')).toBeInTheDocument();
    resolve(declaration({ version: 4 }));
  });
});

describe('it describes; it never matches', () => {
  it('grades no company against the description', () => {
    // **The boundary, on the screen.** Comparing a real company to this needs
    // resolved facts about that company, which is built elsewhere. A verdict
    // here would be the product claiming something Signora has not concluded.
    const { container } = render(editor());

    // **Verdict shapes, not the bare word `match`.** The screen legitimately
    // says *"nothing is matched against a list"*, which is the rule rather
    // than a violation of it — and a guard that flags its own negation is the
    // kind that gets deleted within a week (the vocabulary test's lesson).
    for (const verdict of [
      /\bfit\b/i,
      /\bscore\b/i,
      /\brank/i,
      /\d+\s*%/,
      /\bmatches\b/i,
      /good match/i,
    ]) {
      expect(container.textContent).not.toMatch(verdict);
    }
  });

  it('shows the description back in the customer’s own words', () => {
    render(editor());

    expect(
      screen.getByText(/Financial Services · United Kingdom · 200–2,000 people/),
    ).toBeInTheDocument();
  });
});

describe('B-005 · a product removed from the catalog', () => {
  const GONE = 'ffffffff-6666-4666-8666-666666666666';

  function orphaned() {
    return withQuery(
      <IcpEditor
        catalog={catalog()}
        declaration={declaration({
          profiles: [profile(), profile({ product_id: GONE, industries: ['Retail'] })],
        })}
        workspaceId={WORKSPACE}
      />,
    );
  }

  it('is never sent back to the server', async () => {
    // **The defect this fixes.** The editor used to send everything stored
    // while rendering only what the catalog still had, so the request
    // consisted of a description for a product that no longer existed — and
    // the customer's own edit was dropped before it left the browser.
    const user = userEvent.setup();
    render(orphaned());

    await user.click(
      screen.getByRole('button', { name: 'Remove the description for Revenue Cloud' }),
    );

    await waitFor(() => expect(request).toHaveBeenCalled());
    const body = sent().body as { profiles: ProductIcp[] };
    expect(body.profiles.map((entry) => entry.product_id)).not.toContain(GONE);
  });

  it('is said out loud rather than dropped quietly', () => {
    // Dropping it is correct; doing it silently would be a second, quieter
    // defect. The last clause is the one that matters to a customer.
    render(orphaned());

    expect(screen.getByRole('status')).toHaveTextContent(
      /One entry here belongs to a product you no longer sell.*the version that holds it is kept/i,
    );
  });

  it('does not stop the customer saving what they can see', async () => {
    const user = userEvent.setup();
    render(orphaned());

    await user.click(
      screen.getByRole('button', { name: 'Describe who buys Revenue Cloud' }),
    );
    await user.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() => expect(request).toHaveBeenCalled());
    const body = sent().body as { profiles: ProductIcp[] };
    expect(body.profiles.map((entry) => entry.product_id)).toEqual([CORE]);
  });
});
