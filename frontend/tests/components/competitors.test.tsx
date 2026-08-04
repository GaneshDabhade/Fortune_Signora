/**
 * The screen where a customer says what they are up against.
 *
 * These assert the rules that keep the sixth declaration honest: that the list
 * is saved whole, that a name is stored exactly as typed, that an entry keeps
 * its identity across a rename, that a concurrent save is refused rather than
 * resolved — and the two that are this declaration's own: **that nothing on
 * the screen grades a competitor**, and **that an empty list a customer chose
 * reads differently from one they never wrote.**
 */
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactElement } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { CompetitorsEditor } from '@/components/commercial/competitors';
import type { DeclaredCompetitors } from '@/lib/api/types';

const request = vi.hoisted(() => vi.fn());

vi.mock('@/lib/api/client', async () => {
  const actual =
    await vi.importActual<typeof import('@/lib/api/client')>('@/lib/api/client');
  return { ...actual, apiRequest: request };
});

const WORKSPACE = 'aaaaaaaa-1111-4111-8111-111111111111';
const SALESFORCE = 'bbbbbbbb-2222-4222-8222-222222222222';

function declared(overrides: Partial<DeclaredCompetitors> = {}): DeclaredCompetitors {
  return {
    version: 3,
    competitors: [{ id: SALESFORCE, name: 'Salesforce' }],
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

function editor(overrides: Partial<DeclaredCompetitors> = {}) {
  return withQuery(
    <CompetitorsEditor declared={declared(overrides)} workspaceId={WORKSPACE} />,
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
  request.mockResolvedValue(declared({ version: 4 }));
});

describe('a workspace that has said nothing', () => {
  it('invites the first competitor rather than showing an error', () => {
    render(
      editor({ version: 0, competitors: [], updated_at: null, updated_by: null }),
    );

    expect(screen.getByText('No competitors yet')).toBeInTheDocument();
  });

  it('shows no version line, because there is no author and no moment', () => {
    render(
      editor({ version: 0, competitors: [], updated_at: null, updated_by: null }),
    );

    expect(screen.queryByText(/Version/)).not.toBeInTheDocument();
  });
});

describe('a workspace that chose to track nobody', () => {
  it('says so rather than asking for the first one again', () => {
    render(editor({ version: 1, competitors: [] }));

    expect(
      screen.getByText('You have said you do not track competitors'),
    ).toBeInTheDocument();
  });

  it('is distinguishable from never having been asked', () => {
    render(editor({ version: 1, competitors: [] }));

    expect(screen.queryByText('No competitors yet')).not.toBeInTheDocument();
  });
});

describe('adding a competitor', () => {
  it('sends the whole list, not the change', async () => {
    render(editor());

    await userEvent.type(screen.getByLabelText('Competing product'), 'HubSpot');
    await userEvent.click(screen.getByRole('button', { name: 'Add' }));

    await waitFor(() => expect(request).toHaveBeenCalled());
    const body = sent().body as { competitors: { name: string }[] };
    expect(body.competitors.map((c) => c.name)).toEqual(['Salesforce', 'HubSpot']);
  });

  it('sends the version it read, so a colleague who saved first wins', async () => {
    render(editor());

    await userEvent.type(screen.getByLabelText('Competing product'), 'HubSpot');
    await userEvent.click(screen.getByRole('button', { name: 'Add' }));

    await waitFor(() => expect(request).toHaveBeenCalled());
    expect(sent().body.expected_version).toBe(3);
  });

  it('keeps the name exactly as typed, resolving nothing', async () => {
    render(editor());

    await userEvent.type(screen.getByLabelText('Competing product'), 'salesforce.com');
    await userEvent.click(screen.getByRole('button', { name: 'Add' }));

    await waitFor(() => expect(request).toHaveBeenCalled());
    const body = sent().body as { competitors: { name: string }[] };
    expect(body.competitors[1]?.name).toBe('salesforce.com');
  });

  it('mints an id in the browser, so saving twice cannot duplicate', async () => {
    render(editor());

    await userEvent.type(screen.getByLabelText('Competing product'), 'HubSpot');
    await userEvent.click(screen.getByRole('button', { name: 'Add' }));

    await waitFor(() => expect(request).toHaveBeenCalled());
    const body = sent().body as { competitors: { id: string }[] };
    expect(body.competitors[1]?.id).toMatch(/^[0-9a-f-]{36}$/);
  });

  it('refuses a name already on the list, whatever the casing', async () => {
    render(editor());

    await userEvent.type(screen.getByLabelText('Competing product'), '  SALESFORCE ');
    await userEvent.click(screen.getByRole('button', { name: 'Add' }));

    expect(request).not.toHaveBeenCalled();
  });

  it('cannot be submitted empty', () => {
    render(editor());

    expect(screen.getByRole('button', { name: 'Add' })).toBeDisabled();
  });
});

describe('removing a competitor', () => {
  it('sends the list without it, keeping every other entry identical', async () => {
    render(editor({ competitors: [
      { id: SALESFORCE, name: 'Salesforce' },
      { id: 'dddddddd-4444-4444-8444-444444444444', name: 'HubSpot' },
    ] }));

    await userEvent.click(screen.getByRole('button', { name: 'Remove Salesforce' }));

    await waitFor(() => expect(request).toHaveBeenCalled());
    const body = sent().body as { competitors: { id: string; name: string }[] };
    expect(body.competitors).toEqual([
      { id: 'dddddddd-4444-4444-8444-444444444444', name: 'HubSpot' },
    ]);
  });
});

describe('what the screen refuses to say', () => {
  it('grades nobody', () => {
    /**
     * The word a threat level would arrive under. A competitor is *about* a
     * risk, so a number feels natural here — and it would be a customer-typed
     * weight in the head of the pipeline that nothing reviews.
     */
    render(editor());

    const page = document.body.textContent ?? '';
    for (const word of ['Threat', 'Severity', 'Priority', 'Rank', 'Score']) {
      expect(page).not.toContain(word);
    }
  });

  it('does not promise an alert the platform cannot yet raise', () => {
    render(editor());

    const page = document.body.textContent ?? '';
    for (const promise of ['alert', 'notify', 'warn', 'monitor']) {
      expect(page.toLowerCase()).not.toContain(promise);
    }
  });
});

describe('when the server refuses', () => {
  it('says so instead of showing the list as saved', async () => {
    request.mockRejectedValue(new Error('boom'));
    render(editor());

    await userEvent.type(screen.getByLabelText('Competing product'), 'HubSpot');
    await userEvent.click(screen.getByRole('button', { name: 'Add' }));

    expect(await screen.findByRole('alert')).toBeInTheDocument();
  });
});

describe('provenance', () => {
  it('names the version and says every one is kept', () => {
    render(editor());

    expect(screen.getByText(/Version 3/)).toBeInTheDocument();
    expect(screen.getByText(/never an edit/)).toBeInTheDocument();
  });
});
