/**
 * The first thing in Signora that writes.
 *
 * Everything else on the brief reports what the pipeline computed. These
 * assert the rules that keep a *decision* honest: that the legal moves come
 * from the server, that a refusal is shown in the domain's own words, and
 * that nothing appears to have happened until it has.
 */
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactElement } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { WorkflowActions } from '@/components/intelligence/workflow';
import { WorkflowStage } from '@/components/intelligence/opportunity';
import { ApiError } from '@/lib/api/client';
import type { AccountOpportunity } from '@/lib/api/types';

const request = vi.hoisted(() => vi.fn());

vi.mock('@/lib/api/client', async () => {
  const actual = await vi.importActual<typeof import('@/lib/api/client')>(
    '@/lib/api/client',
  );
  return { ...actual, apiRequest: request };
});

const VIEWER = 'aaaaaaaa-1111-4111-8111-111111111111';
const COLLEAGUE = 'bbbbbbbb-2222-4222-8222-222222222222';

function opportunity(overrides: Partial<AccountOpportunity> = {}): AccountOpportunity {
  return {
    id: 'cccccccc-3333-4333-8333-333333333333',
    account_id: 'dddddddd-4444-4444-8444-444444444444',
    stage: 'tracking',
    owner_id: null,
    opened_at: '2026-07-01T00:00:00Z',
    opened_by: 'automatic',
    score_at_open: 35,
    contested_at_open: false,
    score: 50,
    score_change_since_open: 15,
    evidence: 'current',
    history: [],
    allowed_next: ['closed_lost', 'dismissed', 'engaged'],
    ...overrides,
  };
}

function withQuery(node: ReactElement) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return <QueryClientProvider client={client}>{node}</QueryClientProvider>;
}

/** The request the component actually made. Asserted through a helper so a
 * missing call fails as "nothing was sent" rather than as an index error. */
function sent(): { path: string; method?: string; body: Record<string, unknown> } {
  const call = request.mock.calls[0];
  expect(call, 'nothing was sent to the API').toBeDefined();
  const [path, options] = call as [string, { method?: string; body: Record<string, unknown> }];
  return { path, method: options.method, body: options.body };
}

function actions(overrides: Partial<AccountOpportunity> = {}) {
  return withQuery(
    <WorkflowActions
      opportunity={opportunity(overrides)}
      workspaceId="eeeeeeee-5555-4555-8555-555555555555"
      viewerId={VIEWER}
    />,
  );
}

beforeEach(() => {
  request.mockReset();
});

describe('the moves offered are the ones the domain allows', () => {
  it('draws exactly what the server sent', () => {
    render(actions());

    expect(screen.getByRole('button', { name: "I'm working this" })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Lost' })).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: 'Not a real opportunity' }),
    ).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Won' })).not.toBeInTheDocument();
  });

  it('draws nothing at all on a won deal', () => {
    // Terminal, and the server says so by sending an empty list. **No empty
    // toolbar and no disabled buttons** — a control that cannot be used
    // teaches a reader to distrust the ones that can.
    const { container } = render(
      actions({ stage: 'closed_won', allowed_next: [], owner_id: VIEWER }),
    );

    expect(container).toBeEmptyDOMElement();
  });

  it('offers reopening on a dismissed account', () => {
    // A dismissal is a judgement about Signora, not a deletion. Being able to
    // take it back is what makes it safe to make.
    render(actions({ stage: 'dismissed', allowed_next: ['engaged', 'tracking'] }));

    expect(screen.getByRole('button', { name: 'Track this again' })).toBeInTheDocument();
  });

  it('reimplements no transition rule of its own', () => {
    // If the client held its own table it would contradict the server the
    // moment either changed. The proof is that an implausible list still
    // renders verbatim.
    render(actions({ stage: 'tracking', allowed_next: ['closed_won'] }));

    expect(screen.getByRole('button', { name: 'Won' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: "I'm working this" })).not.toBeInTheDocument();
  });
});

describe('every decision carries a sentence', () => {
  it('asks a different question for each decision', async () => {
    // A single "Reason" label collects a single kind of sentence. On a
    // dismissal this is the only feedback Signora ever gets about its own
    // qualification quality.
    const user = userEvent.setup();
    render(actions());

    await user.click(screen.getByRole('button', { name: 'Not a real opportunity' }));

    expect(
      screen.getByLabelText("Why shouldn't Signora have shown you this?"),
    ).toBeInTheDocument();
  });

  it('cannot be confirmed while the reason is empty', async () => {
    const user = userEvent.setup();
    render(actions());

    await user.click(screen.getByRole('button', { name: "I'm working this" }));

    expect(screen.getByRole('button', { name: 'Take it on' })).toBeDisabled();
  });

  it('will not accept whitespace as an explanation', async () => {
    const user = userEvent.setup();
    render(actions());

    await user.click(screen.getByRole('button', { name: "I'm working this" }));
    await user.type(screen.getByLabelText('Why are you taking this on?'), '   ');

    expect(screen.getByRole('button', { name: 'Take it on' })).toBeDisabled();
    expect(request).not.toHaveBeenCalled();
  });

  it('says the reason is permanent before it is written', async () => {
    // It is appended to a record nothing can edit, under the seller's name.
    // Saying so afterwards would be an apology rather than a warning.
    const user = userEvent.setup();
    render(actions());

    await user.click(screen.getByRole('button', { name: "I'm working this" }));

    expect(screen.getByText(/recorded against this account permanently/i)).toBeInTheDocument();
  });
});

describe('what gets sent', () => {
  it('assigns the account to whoever took it on, and says so first', async () => {
    const user = userEvent.setup();
    request.mockResolvedValue({ stage: 'engaged' });
    render(actions());

    await user.click(screen.getByRole('button', { name: "I'm working this" }));
    expect(screen.getByText('This account will be assigned to you.')).toBeInTheDocument();

    await user.type(
      screen.getByLabelText('Why are you taking this on?'),
      'Met their VP last week.',
    );
    await user.click(screen.getByRole('button', { name: 'Take it on' }));

    await waitFor(() => expect(request).toHaveBeenCalled());
    const call = sent();
    expect(call.path).toContain('/opportunities/cccccccc-3333-4333-8333-333333333333/states');
    expect(call.method).toBe('POST');
    expect(call.body).toEqual({
      stage: 'engaged',
      reason: 'Met their VP last week.',
      owner_id: VIEWER,
    });
  });

  it('never names its own actor', async () => {
    // A request able to say who decided could sign somebody else's name to a
    // dismissal, and the workflow history is the one record in Signora that
    // nothing recomputes if it is wrong.
    const user = userEvent.setup();
    request.mockResolvedValue({ stage: 'dismissed' });
    render(actions());

    await user.click(screen.getByRole('button', { name: 'Not a real opportunity' }));
    await user.type(
      screen.getByLabelText("Why shouldn't Signora have shown you this?"),
      'They are a reseller.',
    );
    await user.click(screen.getByRole('button', { name: 'Dismiss it' }));

    await waitFor(() => expect(request).toHaveBeenCalled());
    expect(Object.keys(sent().body)).toEqual(['stage', 'reason']);
  });

  it('does not reassign an account its holder is already working', async () => {
    // Re-stating ownership that has not changed would be a state row that
    // changes nothing, which the domain refuses as noise in the audit trail.
    const user = userEvent.setup();
    request.mockResolvedValue({ stage: 'closed_won' });
    render(
      actions({ stage: 'engaged', owner_id: VIEWER, allowed_next: ['closed_won'] }),
    );

    await user.click(screen.getByRole('button', { name: 'Won' }));
    await user.type(screen.getByLabelText('What won it?'), 'Signed a two-year deal.');
    await user.click(screen.getByRole('button', { name: 'Record the win' }));

    await waitFor(() => expect(request).toHaveBeenCalled());
    expect(sent().body).not.toHaveProperty('owner_id');
  });
});

describe('a refusal is shown, in the words that explain it', () => {
  it('repeats what the server actually said', async () => {
    const user = userEvent.setup();
    request.mockRejectedValue(
      new ApiError(422, {
        code: 'transition_refused',
        message:
          "'closed_won' cannot become 'engaged'. A won deal does not reopen — the next deal at that account is genuinely a new opportunity.",
        correlation_id: 'x',
      }),
    );
    render(actions());

    await user.click(screen.getByRole('button', { name: "I'm working this" }));
    await user.type(screen.getByLabelText('Why are you taking this on?'), 'Trying it.');
    await user.click(screen.getByRole('button', { name: 'Take it on' }));

    expect(await screen.findByRole('alert')).toHaveTextContent(/a won deal does not reopen/i);
  });

  it('claims nothing it does not know when the request never arrived', async () => {
    const user = userEvent.setup();
    request.mockRejectedValue(new TypeError('Failed to fetch'));
    render(actions());

    await user.click(screen.getByRole('button', { name: "I'm working this" }));
    await user.type(screen.getByLabelText('Why are you taking this on?'), 'Trying it.');
    await user.click(screen.getByRole('button', { name: 'Take it on' }));

    expect(await screen.findByRole('alert')).toHaveTextContent(/nothing has changed/i);
  });

  it('keeps the dialog open so the sentence is not lost', async () => {
    // Retyping an explanation after a refusal is the fastest way to teach
    // somebody to write a shorter one.
    const user = userEvent.setup();
    request.mockRejectedValue(
      new ApiError(422, { code: 'transition_refused', message: 'No.', correlation_id: 'x' }),
    );
    render(actions());

    await user.click(screen.getByRole('button', { name: "I'm working this" }));
    await user.type(screen.getByLabelText('Why are you taking this on?'), 'A careful sentence.');
    await user.click(screen.getByRole('button', { name: 'Take it on' }));

    await screen.findByRole('alert');
    expect(screen.getByLabelText('Why are you taking this on?')).toHaveValue(
      'A careful sentence.',
    );
  });
});

describe('who holds an account', () => {
  it('says "you" to the person holding it', () => {
    render(
      <WorkflowStage
        opportunity={opportunity({ stage: 'engaged', owner_id: VIEWER })}
        viewerId={VIEWER}
      />,
    );

    expect(screen.getByText(/you hold this/)).toBeInTheDocument();
  });

  it('never renders an identifier for anybody else', () => {
    // **D23.** Better Auth owns user profiles in the Next.js tier and the
    // Python tier verifies tokens without learning who a person is, so an
    // owner arrives as an identifier and nothing more. A raw one on screen
    // would be the same absence dressed as information.
    const { container } = render(
      <WorkflowStage
        opportunity={opportunity({ stage: 'engaged', owner_id: COLLEAGUE })}
        viewerId={VIEWER}
      />,
    );

    expect(screen.getByText(/held by someone else/)).toBeInTheDocument();
    expect(container.textContent).not.toContain(COLLEAGUE);
  });

  it('still says nobody has taken a tracked account', () => {
    render(<WorkflowStage opportunity={opportunity()} viewerId={VIEWER} />);

    expect(screen.getByText(/nobody has taken it yet/)).toBeInTheDocument();
  });
});
