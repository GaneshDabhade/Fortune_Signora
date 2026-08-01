/**
 * The screen where a customer says what they are pushing.
 *
 * These assert the rules that keep a *declaration of intent* honest: that it
 * is saved whole, that a product is in focus or not rather than ranked, that
 * the version line is visible because this is the declaration that goes stale,
 * and that a concurrent save is refused rather than resolved.
 */
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactElement } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { CommercialFocusEditor } from '@/components/commercial/focus';
import type { CommercialFocus, ProductCatalog } from '@/lib/api/types';

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
    products: [
      { id: CORE, name: 'Revenue Cloud', description: '' },
      { id: ENTERPRISE, name: 'Enterprise', description: '' },
    ],
    updated_at: '2026-08-01T09:00:00Z',
    updated_by: 'cccccccc-3333-4333-8333-333333333333',
    ...overrides,
  };
}

function focus(overrides: Partial<CommercialFocus> = {}): CommercialFocus {
  return {
    version: 3,
    products: [CORE],
    objective: 'Land three health systems',
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
  overrides: Partial<CommercialFocus> = {},
  catalogOverrides: Partial<ProductCatalog> = {},
) {
  return withQuery(
    <CommercialFocusEditor
      catalog={catalog(catalogOverrides)}
      focus={focus(overrides)}
      workspaceId={WORKSPACE}
    />,
  );
}

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
  request.mockResolvedValue(focus({ version: 4 }));
});

describe('a company that has declared no focus', () => {
  it('claims no author or date it does not have', () => {
    const { container } = render(
      editor({ version: 0, products: [], objective: '', updated_at: null, updated_by: null }),
    );

    expect(container.textContent).not.toMatch(/version 0/i);
    expect(container.textContent).not.toMatch(/last changed/i);
  });

  it('asks for a product before a focus', () => {
    render(
      editor(
        { version: 0, products: [], objective: '', updated_at: null, updated_by: null },
        { version: 0, products: [], updated_at: null, updated_by: null },
      ),
    );

    expect(screen.getByText('Add a product first')).toBeInTheDocument();
  });

  it('offers to write an objective rather than showing an empty line', () => {
    render(editor({ objective: '' }));

    expect(screen.getByRole('button', { name: 'Add an objective' })).toBeInTheDocument();
  });
});

describe('a product is in focus, or it is not', () => {
  it('states which with aria-pressed rather than a position', () => {
    // **No first, second, third.** The roadmap's word for this capability is
    // *business priorities*, and an ordinal is what that word invites.
    render(editor());

    expect(screen.getByRole('button', { name: 'Revenue Cloud' })).toHaveAttribute(
      'aria-pressed',
      'true',
    );
    expect(screen.getByRole('button', { name: 'Enterprise' })).toHaveAttribute(
      'aria-pressed',
      'false',
    );
  });

  it('adds a product to the focus and sends the whole list', async () => {
    const user = userEvent.setup();
    render(editor());

    await user.click(screen.getByRole('button', { name: 'Enterprise' }));

    await waitFor(() => expect(request).toHaveBeenCalled());
    expect(sent().body.products).toEqual([CORE, ENTERPRISE]);
    expect(sent().method).toBe('PUT');
    expect(sent().path).toBe(`/workspaces/${WORKSPACE}/focus`);
  });

  it('removes one without disturbing the objective', async () => {
    const user = userEvent.setup();
    render(editor());

    await user.click(screen.getByRole('button', { name: 'Revenue Cloud' }));

    await waitFor(() => expect(request).toHaveBeenCalled());
    expect(sent().body.products).toEqual([]);
    expect(sent().body.objective).toBe('Land three health systems');
  });

  it('quotes the version it is replacing', async () => {
    const user = userEvent.setup();
    render(editor());

    await user.click(screen.getByRole('button', { name: 'Enterprise' }));

    await waitFor(() => expect(request).toHaveBeenCalled());
    expect(sent().body.expected_version).toBe(3);
  });

  it('sends no rank, weight or position', async () => {
    const user = userEvent.setup();
    render(editor());

    await user.click(screen.getByRole('button', { name: 'Enterprise' }));

    await waitFor(() => expect(request).toHaveBeenCalled());
    expect(Object.keys(sent().body).sort()).toEqual([
      'expected_version',
      'objective',
      'products',
    ]);
  });
});

describe('the objective is the customer’s words', () => {
  it('saves what they typed, trimmed and nothing else', async () => {
    const user = userEvent.setup();
    render(editor());

    await user.click(screen.getByRole('button', { name: 'Edit' }));
    const field = screen.getByLabelText('What you are trying to do');
    await user.clear(field);
    await user.type(field, '  Expand into EMEA  ');
    await user.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() => expect(request).toHaveBeenCalled());
    expect(sent().body.objective).toBe('Expand into EMEA');
    expect(sent().body.products).toEqual([CORE]);
  });

  it('cancelling restores what was there', async () => {
    const user = userEvent.setup();
    render(editor());

    await user.click(screen.getByRole('button', { name: 'Edit' }));
    await user.type(screen.getByLabelText('What you are trying to do'), ' and more');
    await user.click(screen.getByRole('button', { name: 'Cancel' }));

    expect(screen.getByText('Land three health systems')).toBeInTheDocument();
    expect(request).not.toHaveBeenCalled();
  });
});

describe('the version line is the answer to “is this still true?”', () => {
  it('says when it was last changed', () => {
    // **No period field, on purpose.** A typed "Q3 2026" would be a second
    // version of this fact, free to disagree with it.
    render(editor());

    expect(screen.getByText(/last changed/i)).toBeInTheDocument();
  });

  it('claims no period of its own', () => {
    const { container } = render(editor());

    for (const invented of [/\bQ[1-4]\b/, /\bquarter ends\b/i, /\bexpires\b/i]) {
      expect(container.textContent).not.toMatch(invented);
    }
  });
});

describe('a refusal is shown, never resolved', () => {
  it('reports what the server said when a colleague saved first', async () => {
    const user = userEvent.setup();
    const { ApiError } = await import('@/lib/api/client');
    request.mockRejectedValue(
      new ApiError(409, {
        code: 'focus_version_conflict',
        message: 'your focus is at version 4, not 3. Reload before saving.',
        correlation_id: 'corr-1',
      }),
    );
    render(editor());

    await user.click(screen.getByRole('button', { name: 'Enterprise' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('version 4, not 3');
  });

  it('shows nothing as saved before the server accepted it', async () => {
    const user = userEvent.setup();
    let resolve: (value: CommercialFocus) => void = () => {};
    request.mockReturnValue(
      new Promise<CommercialFocus>((settle) => {
        resolve = settle;
      }),
    );
    render(editor());

    await user.click(screen.getByRole('button', { name: 'Enterprise' }));

    expect(screen.getByRole('button', { name: 'Enterprise' })).toHaveAttribute(
      'aria-pressed',
      'false',
    );
    resolve(focus({ version: 4 }));
  });
});

describe('B-005 · a product removed from the catalog', () => {
  const GONE = 'ffffffff-6666-4666-8666-666666666666';

  function orphaned() {
    return withQuery(
      <CommercialFocusEditor
        catalog={catalog()}
        focus={focus({ products: [CORE, GONE] })}
        workspaceId={WORKSPACE}
      />,
    );
  }

  it('is never sent back to the server', async () => {
    const user = userEvent.setup();
    render(orphaned());

    await user.click(screen.getByRole('button', { name: 'Enterprise' }));

    await waitFor(() => expect(request).toHaveBeenCalled());
    expect(sent().body.products).not.toContain(GONE);
  });

  it('is said out loud rather than dropped quietly', () => {
    render(orphaned());

    expect(screen.getByRole('status')).toHaveTextContent(/no longer sell/i);
  });
});
