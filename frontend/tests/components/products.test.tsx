/**
 * The first screen where a customer tells Signora something.
 *
 * Every other surface reports what the pipeline computed or records a decision
 * about it. These assert the rules that keep a *declaration* honest: that the
 * catalog is saved whole, that a product's identity survives editing, that a
 * concurrent save is refused rather than resolved, and that nothing is
 * optimistically shown as saved before it is.
 */
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactElement } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { ProductCatalogEditor } from '@/components/commercial/products';
import { ApiError } from '@/lib/api/client';
import type { ProductCatalog } from '@/lib/api/types';

const request = vi.hoisted(() => vi.fn());

vi.mock('@/lib/api/client', async () => {
  const actual =
    await vi.importActual<typeof import('@/lib/api/client')>('@/lib/api/client');
  return { ...actual, apiRequest: request };
});

const WORKSPACE = 'aaaaaaaa-1111-4111-8111-111111111111';
const CORE = 'bbbbbbbb-2222-4222-8222-222222222222';

function catalog(overrides: Partial<ProductCatalog> = {}): ProductCatalog {
  return {
    version: 2,
    products: [{ id: CORE, name: 'Revenue Cloud', description: 'Pipeline generation' }],
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

function editor(overrides: Partial<ProductCatalog> = {}) {
  return withQuery(
    <ProductCatalogEditor catalog={catalog(overrides)} workspaceId={WORKSPACE} />,
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

beforeEach(() => {
  request.mockReset();
  request.mockResolvedValue(catalog({ version: 3 }));
});

describe('a workspace that has declared nothing', () => {
  it('invites the first product rather than showing an error', () => {
    // Version 0 is the state every workspace starts in, not a fault.
    render(editor({ version: 0, products: [], updated_at: null, updated_by: null }));

    expect(screen.getByText('No products yet')).toBeInTheDocument();
    expect(
      screen.getAllByRole('button', { name: /add product/i }).length,
    ).toBeGreaterThan(0);
  });

  it('claims no author or date it does not have', () => {
    const { container } = render(
      editor({ version: 0, products: [], updated_at: null, updated_by: null }),
    );

    expect(container.textContent).not.toMatch(/version 0/i);
    expect(container.textContent).not.toMatch(/last changed/i);
  });
});

describe('the catalog is saved whole', () => {
  it('sends every product, not just the new one', async () => {
    // The catalog is the versioned unit. Sending a change would make what
    // gets stored depend on what was there when the request arrived.
    const user = userEvent.setup();
    render(editor());

    await user.click(screen.getByRole('button', { name: /add product/i }));
    await user.type(screen.getByLabelText('Name'), 'Enterprise');
    await user.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() => expect(request).toHaveBeenCalled());
    const body = sent().body as { products: { name: string }[] };
    expect(body.products.map((p) => p.name)).toEqual(['Revenue Cloud', 'Enterprise']);
  });

  it('quotes the version it is replacing', async () => {
    // What turns a colleague's concurrent save into a refusal this caller can
    // act on, rather than an overwrite neither of them sees.
    const user = userEvent.setup();
    render(editor());

    await user.click(screen.getByRole('button', { name: /add product/i }));
    await user.type(screen.getByLabelText('Name'), 'Enterprise');
    await user.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() => expect(request).toHaveBeenCalled());
    expect(sent().body.expected_version).toBe(2);
    expect(sent().method).toBe('PUT');
  });

  it('removing a product sends the list without it', async () => {
    const user = userEvent.setup();
    render(editor());

    await user.click(screen.getByRole('button', { name: /remove Revenue Cloud/i }));

    await waitFor(() => expect(request).toHaveBeenCalled());
    expect(sent().body.products).toEqual([]);
  });
});

describe('a product keeps its identity', () => {
  it('editing a name reuses the same id', async () => {
    // Everything declared later cites a product id. A rename that minted a
    // new one would orphan every reference to it.
    const user = userEvent.setup();
    render(editor());

    await user.click(screen.getByRole('button', { name: /edit Revenue Cloud/i }));
    await user.clear(screen.getByLabelText('Name'));
    await user.type(screen.getByLabelText('Name'), 'Revenue Platform');
    await user.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() => expect(request).toHaveBeenCalled());
    const body = sent().body as { products: { id: string; name: string }[] };
    expect(body.products).toEqual([
      { id: CORE, name: 'Revenue Platform', description: 'Pipeline generation' },
    ]);
  });

  it('adding a product mints an id in the browser', async () => {
    // Client-chosen ids are what make saving idempotent: a retried request
    // cannot duplicate a product.
    const user = userEvent.setup();
    render(editor({ version: 0, products: [], updated_at: null, updated_by: null }));

    await user.click(screen.getAllByRole('button', { name: /add product/i })[0]!);
    await user.type(screen.getByLabelText('Name'), 'Core');
    await user.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() => expect(request).toHaveBeenCalled());
    const body = sent().body as { products: { id: string }[] };
    expect(body.products[0]!.id).toMatch(/^[0-9a-f-]{36}$/i);
  });
});

describe('what a product must have', () => {
  it('cannot be saved without a name', async () => {
    const user = userEvent.setup();
    render(editor());

    await user.click(screen.getByRole('button', { name: /add product/i }));

    expect(screen.getByRole('button', { name: 'Save' })).toBeDisabled();
  });

  it('will not accept whitespace as a name', async () => {
    const user = userEvent.setup();
    render(editor());

    await user.click(screen.getByRole('button', { name: /add product/i }));
    await user.type(screen.getByLabelText('Name'), '   ');

    expect(screen.getByRole('button', { name: 'Save' })).toBeDisabled();
    expect(request).not.toHaveBeenCalled();
  });

  it('says a description is optional and worth writing', async () => {
    const user = userEvent.setup();
    render(editor());

    await user.click(screen.getByRole('button', { name: /add product/i }));

    expect(screen.getByText(/optional\. worth writing/i)).toBeInTheDocument();
  });
});

describe('a concurrent edit is shown, not resolved', () => {
  it('repeats what the server actually said', async () => {
    const user = userEvent.setup();
    request.mockRejectedValue(
      new ApiError(409, {
        code: 'catalog_version_conflict',
        message:
          'the catalog is at version 3, not 2. Somebody else changed it since you opened this page — reload to see their version before saving yours, so neither of you loses work.',
        correlation_id: 'x',
      }),
    );
    render(editor());

    await user.click(screen.getByRole('button', { name: /remove Revenue Cloud/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent(
      /somebody else changed it/i,
    );
  });

  it('claims nothing it does not know when the request never arrived', async () => {
    const user = userEvent.setup();
    request.mockRejectedValue(new TypeError('Failed to fetch'));
    render(editor());

    await user.click(screen.getByRole('button', { name: /remove Revenue Cloud/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent(/nothing has changed/i);
  });

  it('leaves the catalog on screen unchanged after a refusal', async () => {
    // Not optimistic. A list that removed a row and was then refused would be
    // the one place the screen stated something untrue.
    const user = userEvent.setup();
    request.mockRejectedValue(new TypeError('Failed to fetch'));
    render(editor());

    await user.click(screen.getByRole('button', { name: /remove Revenue Cloud/i }));

    await screen.findByRole('alert');
    expect(screen.getByText('Revenue Cloud')).toBeInTheDocument();
  });
});

describe('the reader is told this is versioned', () => {
  it('says which version is in force and that none are lost', () => {
    render(editor());

    expect(screen.getByText(/version 2/i)).toBeInTheDocument();
    expect(screen.getByText(/never an edit/i)).toBeInTheDocument();
  });
});
