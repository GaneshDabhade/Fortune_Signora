/**
 * The first thing in Signora that writes.
 *
 * Everything else on the brief reports what the pipeline computed. These
 * assert the rules that keep a *decision* honest: that the legal moves come
 * from the server, that a refusal is shown in the domain's own words, and
 * that nothing appears to have happened until it has.
 */
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
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
  const actual =
    await vi.importActual<typeof import('@/lib/api/client')>('@/lib/api/client');
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
  const [path, options] = call as [
    string,
    { method?: string; body: Record<string, unknown> },
  ];
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
    // "Lost without pursuing" from `tracking` — R4-02. The move is named for
    // where it came from as well as where it is going.
    expect(
      screen.getByRole('button', { name: 'Lost without pursuing' }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: 'Not a real opportunity' }),
    ).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Won' })).not.toBeInTheDocument();
  });

  it('offers no control at all on a won deal, and says why', () => {
    // Terminal, and the server says so by sending an empty list. **No empty
    // toolbar and no disabled buttons** — a control that cannot be used
    // teaches a reader to distrust the ones that can. That property is
    // asserted directly here rather than through an empty container, because
    // **silence is not an explanation** (LO-05): this is the one place in the
    // lifecycle where a reader can do nothing, so it is the one place that
    // has to say what happens instead.
    render(actions({ stage: 'closed_won', allowed_next: [], owner_id: VIEWER }));

    // **No stage move is offered**, which is the property: the domain sent an
    // empty list and a control that cannot be used teaches a reader to
    // distrust the ones that can.
    for (const move of ['Won', 'Lost', 'Not a real opportunity', "I'm working this"]) {
      expect(screen.queryByRole('button', { name: move })).toBeNull();
    }
    expect(screen.getByText(/Won deals stay won/)).toBeVisible();
  });

  it('offers the way back, which is not a reopening — LO-07', () => {
    // *"I clicked the wrong row"* had no answer at all. A won deal is
    // terminal, correctly, and the recourse the domain names — *the next deal
    // at that account is genuinely a new opportunity* — had no route into the
    // product until this one.
    render(actions({ stage: 'closed_won', allowed_next: [], owner_id: VIEWER }));

    expect(screen.getByRole('button', { name: 'Work this account again' })).toBeVisible();
  });

  it('says the closed deal is left alone before anything is opened', () => {
    // **The mistake is preserved rather than erased.** A one-click undo would
    // edit the past, and would quietly remove a false win from a figure
    // somebody may already have reported.
    render(actions({ stage: 'closed_won', allowed_next: [], owner_id: VIEWER }));
    fireEvent.click(screen.getByRole('button', { name: 'Work this account again' }));

    expect(screen.getByText(/stays exactly as it is/)).toBeVisible();
  });

  it('will not open one without a reason', () => {
    // The automatic path records the score and the policy that qualified it.
    // A human opening has neither, so the sentence is the only explanation the
    // new opportunity will ever carry.
    render(actions({ stage: 'closed_won', allowed_next: [], owner_id: VIEWER }));
    fireEvent.click(screen.getByRole('button', { name: 'Work this account again' }));

    expect(screen.getByRole('button', { name: 'Open it' })).toBeDisabled();
  });

  it('opens a new opportunity rather than changing the closed one', async () => {
    render(actions({ stage: 'closed_won', allowed_next: [], owner_id: VIEWER }));
    fireEvent.click(screen.getByRole('button', { name: 'Work this account again' }));
    fireEvent.change(screen.getByRole('textbox'), {
      target: { value: 'They came back for the second site.' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Open it' }));

    await waitFor(() => expect(request).toHaveBeenCalled());
    const call = sent();
    // Keyed by **account**, not by the closed opportunity — the new one is a
    // new aggregate, and posting to the old one's states would be the edit
    // this design refuses.
    expect(call.path).toMatch(/\/accounts\/[^/]+\/opportunity$/);
    expect(call.body).toEqual({ reason: 'They came back for the second site.' });
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
    expect(
      screen.queryByRole('button', { name: "I'm working this" }),
    ).not.toBeInTheDocument();
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

    expect(
      screen.getByText(/recorded against this account permanently/i),
    ).toBeInTheDocument();
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
    expect(call.path).toContain(
      '/opportunities/cccccccc-3333-4333-8333-333333333333/states',
    );
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
    render(actions({ stage: 'engaged', owner_id: VIEWER, allowed_next: ['closed_won'] }));

    await user.click(screen.getByRole('button', { name: 'Won' }));
    await user.type(screen.getByLabelText('What won it?'), 'Signed a two-year deal.');
    await user.click(screen.getByRole('button', { name: 'Record the win' }));

    await waitFor(() => expect(request).toHaveBeenCalled());
    expect(sent().body).not.toHaveProperty('owner_id');
  });
});

describe('a refusal is shown, in the words that explain it', () => {
  it('repeats what the server actually said', async () => {
    // Every refusal but one passes through: it is a statement about the
    // customer's own data that they can act on.
    const user = userEvent.setup();
    request.mockRejectedValue(
      new ApiError(422, {
        code: 'owner_not_a_member',
        message:
          'That person is not a member of this workspace and cannot hold work in it.',
        correlation_id: 'x',
      }),
    );
    render(actions());

    await user.click(screen.getByRole('button', { name: "I'm working this" }));
    await user.type(screen.getByLabelText('Why are you taking this on?'), 'Trying it.');
    await user.click(screen.getByRole('button', { name: 'Take it on' }));

    expect(await screen.findByRole('alert')).toHaveTextContent(
      /not a member of this workspace/i,
    );
  });

  it('answers a refused transition with what the reader can do about it', async () => {
    // **R4-03, and the one code that does not pass through.** A transition is
    // only refusable when the reader is out of date — the dialog offers
    // exactly `allowed_next`. The domain's explanation answers a question they
    // did not ask, in the platform's vocabulary, and leaves them nothing to do.
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

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent(/has moved since you opened this page/i);
    // No transition table, and no schema keys.
    expect(alert.textContent).not.toContain('closed_won');
    expect(alert.textContent).not.toContain('Allowed from here');
  });

  it('never shows a schema key or an identifier in a refusal', async () => {
    // The blanket property. A message that needs sanitising before display is
    // a message that will be shown unsanitised somewhere else (R4-03) — the
    // backend invariant asserts the same rule at the source.
    const user = userEvent.setup();
    request.mockRejectedValue(
      new ApiError(422, {
        code: 'transition_refused',
        message:
          'opportunity 6d1510af-4468-4ddc-924a-543c66975c28 is already engaged with the same owner.',
        correlation_id: 'x',
      }),
    );
    render(actions());

    await user.click(screen.getByRole('button', { name: "I'm working this" }));
    await user.type(screen.getByLabelText('Why are you taking this on?'), 'Trying it.');
    await user.click(screen.getByRole('button', { name: 'Take it on' }));

    const alert = await screen.findByRole('alert');
    expect(alert.textContent).not.toMatch(
      /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i,
    );
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
      new ApiError(422, {
        code: 'transition_refused',
        message: 'No.',
        correlation_id: 'x',
      }),
    );
    render(actions());

    await user.click(screen.getByRole('button', { name: "I'm working this" }));
    await user.type(
      screen.getByLabelText('Why are you taking this on?'),
      'A careful sentence.',
    );
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
    //
    // **The wording moved from *"held by someone else"* to *"held by somebody
    // here"* in LO-04**, and the property did not: this asserts that no
    // identifier reaches the screen, which is what D23 is actually about. The
    // sentence changed because the roster can now usually name the holder,
    // and the two phrasings needed to be the same phrase either way.
    const { container } = render(
      <WorkflowStage
        opportunity={opportunity({ stage: 'engaged', owner_id: COLLEAGUE })}
        viewerId={VIEWER}
      />,
    );

    expect(screen.getByText(/held by somebody here/)).toBeInTheDocument();
    expect(container.textContent).not.toContain(COLLEAGUE);
  });

  it('says how long they have held it — LO-06', () => {
    // *"You hold this"* is the same sentence on an account taken on this
    // morning and one taken on in March, and the second is the one a seller
    // wants to find on a Friday afternoon.
    const threeWeeksAgo = new Date(Date.now() - 21 * 86_400_000).toISOString();

    render(
      <WorkflowStage
        opportunity={opportunity({
          stage: 'engaged',
          owner_id: VIEWER,
          history: [
            {
              stage: 'engaged',
              owner_id: VIEWER,
              decided_by: VIEWER,
              reason: 'Met their VP.',
              occurred_at: threeWeeksAgo,
            },
          ],
        })}
        viewerId={VIEWER}
      />,
    );

    expect(screen.getByText(/you took this on 3 weeks ago/)).toBeInTheDocument();
  });

  it('measures no clock on a closed account', () => {
    // The clock stopped. *"You took this on five months ago"* under
    // *Closed — won* would be reporting a duration that means nothing; the
    // decision history is where a closed account's dates belong.
    render(
      <WorkflowStage
        opportunity={opportunity({
          stage: 'closed_won',
          owner_id: VIEWER,
          allowed_next: [],
          history: [
            {
              stage: 'closed_won',
              owner_id: VIEWER,
              decided_by: VIEWER,
              reason: 'Signed.',
              occurred_at: new Date(Date.now() - 150 * 86_400_000).toISOString(),
            },
          ],
        })}
        viewerId={VIEWER}
      />,
    );

    expect(screen.getByText(/you hold this/)).toBeInTheDocument();
    expect(screen.queryByText(/took this on/)).toBeNull();
  });

  it('names the holder once the roster can name them', () => {
    // **The line said *"someone else"* for three milestones**, and the comment
    // justifying it said Signora *can say nobody else's name* — true when it
    // was written, untrue since TM-01 gave a membership an address. The
    // product knew and did not say.
    render(
      <WorkflowStage
        opportunity={opportunity({ stage: 'engaged', owner_id: COLLEAGUE })}
        viewerId={VIEWER}
        people={new Map([[COLLEAGUE, 'ravi@acme.com']])}
      />,
    );

    expect(screen.getByText(/held by ravi@acme\.com/)).toBeInTheDocument();
  });

  it('still says nobody has taken a tracked account', () => {
    render(<WorkflowStage opportunity={opportunity()} viewerId={VIEWER} />);

    expect(screen.getByText(/nobody has taken it yet/)).toBeInTheDocument();
  });
});

describe('a decision is the end of the visit — R10-02', () => {
  // "You have finished with this account and the product does not know it."
  // The decision is the one moment the product can be certain the reader is
  // done, and it used to close the dialog and do nothing else.

  function next() {
    return { name: 'Initech', go: vi.fn() };
  }

  function withNext(offer: { name: string; go: () => void }) {
    return withQuery(
      <WorkflowActions
        opportunity={opportunity()}
        workspaceId="eeeeeeee-5555-4555-8555-555555555555"
        viewerId={VIEWER}
        next={offer}
      />,
    );
  }

  async function dismiss(user: ReturnType<typeof userEvent.setup>) {
    await user.click(screen.getByRole('button', { name: 'Not a real opportunity' }));
    await user.type(screen.getByLabelText(/Why/), 'Wrong segment.');
    await user.click(screen.getByRole('button', { name: 'Dismiss it' }));
    await waitFor(() => expect(request).toHaveBeenCalled());
  }

  it('offers the next account once the decision is recorded', async () => {
    const user = userEvent.setup();
    request.mockResolvedValue({ stage: 'dismissed' });
    render(withNext(next()));

    await dismiss(user);

    expect(await screen.findByRole('button', { name: /Next: Initech/ })).toBeVisible();
  });

  it('never navigates on its own', async () => {
    // **Deliberately not an automatic redirect.** A page that navigates itself
    // after you click something takes the reader's place away from them — and
    // a decision is exactly when somebody wants to check what they wrote.
    const user = userEvent.setup();
    const offer = next();
    request.mockResolvedValue({ stage: 'dismissed' });
    render(withNext(offer));

    await dismiss(user);

    expect(offer.go).not.toHaveBeenCalled();
  });

  it('offers staying as a real choice', async () => {
    const user = userEvent.setup();
    request.mockResolvedValue({ stage: 'dismissed' });
    render(withNext(next()));

    await dismiss(user);

    expect(await screen.findByRole('button', { name: 'Stay here' })).toBeVisible();
  });

  it('goes only when the reader says so', async () => {
    const user = userEvent.setup();
    const offer = next();
    request.mockResolvedValue({ stage: 'dismissed' });
    render(withNext(offer));

    await dismiss(user);
    await user.click(await screen.findByRole('button', { name: /Next: Initech/ }));

    expect(offer.go).toHaveBeenCalledOnce();
  });

  it('closes with nothing to offer when this is the last account', async () => {
    // An offer that goes nowhere is the affordance this surface refuses
    // everywhere else, so with no next the dialog behaves exactly as before.
    const user = userEvent.setup();
    request.mockResolvedValue({ stage: 'dismissed' });
    render(actions());

    await dismiss(user);

    expect(screen.queryByRole('button', { name: /^Next:/ })).toBeNull();
  });

  it('stops asking a question it has already been answered', async () => {
    // A dialog that keeps its form after the decision is recorded invites a
    // reader to answer twice, and the second attempt would be refused by a
    // domain that is right to refuse it.
    const user = userEvent.setup();
    request.mockResolvedValue({ stage: 'dismissed' });
    render(withNext(next()));

    await dismiss(user);

    expect(screen.queryByRole('button', { name: 'Dismiss it' })).toBeNull();
  });
});

describe('an account can be handed to a colleague — LO-01', () => {
  // **The capability was built and had no UI.** `POST /states` has accepted an
  // arbitrary `owner_id` since M6, validated the assignee's membership, and
  // returned `owner_not_a_member` when it failed. This dialog sent `viewerId`
  // and nothing else, so a seller could take an account on and **could not
  // hand one over** — until TM-01 made a person nameable
  // (49-lead-ownership.md §1).

  const COLLEAGUES = [
    { id: COLLEAGUE, name: 'ravi@acme.com' },
    { id: 'dddddddd-4444-4444-8444-444444444444', name: 'jo@acme.com' },
  ];

  function engaging(colleagues: readonly { id: string; name: string }[] = COLLEAGUES) {
    return withQuery(
      <WorkflowActions
        opportunity={opportunity({ stage: 'tracking', allowed_next: ['engaged'] })}
        workspaceId="eeeeeeee-5555-4555-8555-555555555555"
        viewerId={VIEWER}
        colleagues={colleagues}
      />,
    );
  }

  function open(node: ReactElement) {
    render(node);
    fireEvent.click(screen.getAllByRole('button')[0]!);
  }

  it('offers the colleagues by name, with you first', () => {
    open(engaging());

    const picker = screen.getByLabelText('Who is working this');
    const options = within(picker).getAllByRole('option');
    expect(options[0]).toHaveTextContent('You');
    expect(options.map((o) => o.textContent)).toContain('ravi@acme.com');
  });

  it('defaults to you, because that is the commonest case', () => {
    open(engaging());

    expect(screen.getByLabelText('Who is working this')).toHaveValue('');
  });

  it('assigns to the colleague who was chosen', async () => {
    open(engaging());
    fireEvent.change(screen.getByLabelText('Who is working this'), {
      target: { value: COLLEAGUE },
    });
    fireEvent.change(screen.getByRole('textbox'), {
      target: { value: 'Ravi knows their CTO.' },
    });
    // **The button says what it will do.** "Take it on" would describe a
    // different act than the one being performed.
    fireEvent.click(screen.getByRole('button', { name: 'Hand it to ravi@acme.com' }));

    await waitFor(() => expect(request).toHaveBeenCalled());
    expect(sent().body).toEqual({
      stage: 'engaged',
      reason: 'Ravi knows their CTO.',
      owner_id: COLLEAGUE,
    });
  });

  it('still assigns to you when nobody else is chosen', async () => {
    open(engaging());
    fireEvent.change(screen.getByRole('textbox'), {
      target: { value: 'Taking this on.' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Take it on' }));

    await waitFor(() => expect(request).toHaveBeenCalled());
    expect(sent().body).toEqual({
      stage: 'engaged',
      reason: 'Taking this on.',
      owner_id: VIEWER,
    });
  });

  it('offers nothing when there is nobody else in the organization', () => {
    // A one-person organization. An empty picker is a control that cannot be
    // used, which teaches a reader to distrust the ones that can.
    open(engaging([]));

    expect(screen.queryByLabelText('Who is working this')).toBeNull();
  });

  it('never offers it on a decision that does not change ownership', () => {
    // Closing or dismissing leaves ownership where it was, and a control there
    // would invite a change nobody asked for.
    render(
      withQuery(
        <WorkflowActions
          opportunity={opportunity({
            stage: 'engaged',
            owner_id: VIEWER,
            allowed_next: ['closed_lost'],
          })}
          workspaceId="eeeeeeee-5555-4555-8555-555555555555"
          viewerId={VIEWER}
          colleagues={COLLEAGUES}
        />,
      ),
    );
    fireEvent.click(screen.getAllByRole('button')[0]!);

    expect(screen.queryByLabelText('Who is working this')).toBeNull();
  });
});

describe('an account being worked can change hands — LO-04', () => {
  // **`allowed_next` structurally could not offer this.** It is the domain's
  // *stage* table, and a hand-over changes no stage — so an account being
  // worked offered `Won`, `Lost` and `Not a real opportunity` and **no way to
  // give it to anybody**. A seller going on leave had to close their accounts
  // to get them off their name (49-lead-ownership.md §13).

  const COLLEAGUES = [{ id: COLLEAGUE, name: 'ravi@acme.com' }];
  const WORKED = {
    stage: 'engaged',
    owner_id: VIEWER,
    allowed_next: ['closed_won', 'closed_lost', 'dismissed'],
  } satisfies Partial<AccountOpportunity>;

  function worked(
    overrides: Partial<AccountOpportunity> = {},
    colleagues: readonly { id: string; name: string }[] = COLLEAGUES,
    next?: { name: string; go: () => void },
  ) {
    return withQuery(
      <WorkflowActions
        opportunity={opportunity({ ...WORKED, ...overrides })}
        workspaceId="eeeeeeee-5555-4555-8555-555555555555"
        viewerId={VIEWER}
        colleagues={colleagues}
        {...(next ? { next } : {})}
      />,
    );
  }

  it('offers a hand-over on an account you are working', () => {
    render(worked());

    expect(screen.getByRole('button', { name: 'Hand it over' })).toBeVisible();
  });

  it('offers nothing to hand over when there is nobody to hand it to', () => {
    // A one-person organization. **A control that cannot complete is not
    // offered** rather than offered and refused.
    render(worked({}, []));

    expect(screen.queryByRole('button', { name: 'Hand it over' })).toBeNull();
  });

  it('offers nothing on a closed account', () => {
    // There is no live work to move. A won deal is terminal, and this must not
    // become the control that puts a button back on it.
    render(worked({ stage: 'closed_won', allowed_next: [], owner_id: VIEWER }));

    expect(screen.queryByRole('button', { name: 'Hand it over' })).toBeNull();
    expect(screen.queryByRole('button', { name: 'Take it over' })).toBeNull();
  });

  it('offers nothing on an account nobody holds', () => {
    // `I'm working this` already asks who is taking it. Two controls for one
    // act would be two ways to answer the same question.
    render(worked({ stage: 'tracking', owner_id: null, allowed_next: ['engaged'] }));

    expect(screen.queryByRole('button', { name: 'Hand it over' })).toBeNull();
  });

  it('names nobody by default, and will not send until somebody is named', () => {
    // **Handing an account over has no commonest case the product may
    // assume.** The first colleague in a list is not a guess, it is a person.
    render(worked());
    fireEvent.click(screen.getByRole('button', { name: 'Hand it over' }));

    expect(screen.getByLabelText('Who is taking it on')).toHaveValue('');
    fireEvent.change(screen.getByRole('textbox'), {
      target: { value: 'On leave until March.' },
    });
    // Scoped to the dialog: the toolbar control that opened it is still on the
    // page behind, and both legitimately read *Hand it over*.
    const confirm = within(screen.getByRole('dialog')).getByRole('button', {
      name: 'Hand it over',
    });
    expect(confirm).toBeDisabled();
  });

  it('records the same stage with a new owner', async () => {
    render(worked());
    fireEvent.click(screen.getByRole('button', { name: 'Hand it over' }));
    fireEvent.change(screen.getByLabelText('Who is taking it on'), {
      target: { value: COLLEAGUE },
    });
    fireEvent.change(screen.getByRole('textbox'), {
      target: { value: 'On leave until March.' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Hand it to ravi@acme.com' }));

    await waitFor(() => expect(request).toHaveBeenCalled());
    // **The stage does not move**, which is the whole point: ownership is not
    // a lifecycle state, and inventing `transferred` would have made an event
    // into one.
    expect(sent().body).toEqual({
      stage: 'engaged',
      reason: 'On leave until March.',
      owner_id: COLLEAGUE,
    });
  });

  it('asks a different question than taking an account on', () => {
    render(worked());
    fireEvent.click(screen.getByRole('button', { name: 'Hand it over' }));

    expect(screen.getByLabelText('Why is somebody else taking this on?')).toBeVisible();
    expect(screen.queryByLabelText('Why are you taking this on?')).toBeNull();
  });

  it('does not say *you are working this* to somebody who just gave it away', async () => {
    // **The same defect the confirm button had in LO-01**, one screen later.
    // Recording the decision invalidates the brief, so asking *"do I hold
    // this?"* when the panel renders would answer about the world after the
    // act — the wording is about the act.
    const user = userEvent.setup();
    request.mockResolvedValue({ stage: 'engaged' });
    render(worked({}, COLLEAGUES, { name: 'Initech', go: vi.fn() }));

    await user.click(screen.getByRole('button', { name: 'Hand it over' }));
    fireEvent.change(screen.getByLabelText('Who is taking it on'), {
      target: { value: COLLEAGUE },
    });
    await user.type(screen.getByRole('textbox'), 'On leave until March.');
    await user.click(screen.getByRole('button', { name: 'Hand it to ravi@acme.com' }));

    expect(await screen.findByText('Handed over')).toBeVisible();
    expect(screen.queryByText("You're working this")).toBeNull();
  });
});

describe('an account somebody else holds can be taken over — LO-04', () => {
  // **Two people believing they own an account is a real thing that happens**,
  // and the product settles it in the open rather than preventing it: the
  // taker is the actor, a reason is required, and the previous holder is on
  // the row before it in the trail.

  function held() {
    return withQuery(
      <WorkflowActions
        opportunity={opportunity({
          stage: 'engaged',
          owner_id: COLLEAGUE,
          allowed_next: ['closed_won', 'closed_lost', 'dismissed'],
        })}
        workspaceId="eeeeeeee-5555-4555-8555-555555555555"
        viewerId={VIEWER}
        colleagues={[{ id: COLLEAGUE, name: 'ravi@acme.com' }]}
      />,
    );
  }

  it('offers taking it over, not handing it over', () => {
    render(held());

    expect(screen.getByRole('button', { name: 'Take it over' })).toBeVisible();
    expect(screen.queryByRole('button', { name: 'Hand it over' })).toBeNull();
  });

  it('says what is about to happen before it happens', () => {
    render(held());
    fireEvent.click(screen.getByRole('button', { name: 'Take it over' }));

    expect(screen.getByText(/being worked by somebody else/)).toBeVisible();
  });

  it('assigns the account to the person taking it', async () => {
    render(held());
    fireEvent.click(screen.getByRole('button', { name: 'Take it over' }));
    fireEvent.change(screen.getByRole('textbox'), {
      target: { value: 'Agreed at the pipeline review.' },
    });
    // Scoped to the dialog: the toolbar control that opened it says the same
    // thing, and correctly so.
    fireEvent.click(
      within(screen.getByRole('dialog')).getByRole('button', { name: 'Take it over' }),
    );

    await waitFor(() => expect(request).toHaveBeenCalled());
    expect(sent().body).toEqual({
      stage: 'engaged',
      reason: 'Agreed at the pipeline review.',
      owner_id: VIEWER,
    });
  });

  it('asks no colleague, because the answer is the person asking', () => {
    render(held());
    fireEvent.click(screen.getByRole('button', { name: 'Take it over' }));

    expect(screen.queryByLabelText('Who is taking it on')).toBeNull();
    expect(screen.getByLabelText('Why are you taking this over?')).toBeVisible();
  });
});

describe('the dialog says what happens to the account — the screen audit', () => {
  // **The product built recoverability and never mentioned it at the moment
  // somebody was deciding whether to risk it.** A Sales Manager said it out
  // loud during R4-04: *"I'd tell my reps not to dismiss anything"* — and a rep
  // who will not dismiss produces no qualification-quality signal at all,
  // which is the one thing `dismissed` exists to capture.

  it('tells a first-time dismisser that a dismissal is recoverable', () => {
    render(actions());
    fireEvent.click(screen.getByRole('button', { name: 'Not a real opportunity' }));

    expect(screen.getByText(/find it again/i)).toBeVisible();
    expect(screen.getByText(/track it again if you change your mind/i)).toBeVisible();
  });

  it('says a loss can be picked up, because it can', () => {
    render(actions());
    fireEvent.click(screen.getByRole('button', { name: 'Lost without pursuing' }));

    expect(screen.getByText(/find it again/i)).toBeVisible();
  });

  it('tells the truth about a win, which does not come back', () => {
    // **A statement of consequence, never reassurance.** This one is not
    // recoverable, and pretending otherwise would be the more expensive
    // kindness.
    render(actions({ stage: 'engaged', owner_id: VIEWER, allowed_next: ['closed_won'] }));
    fireEvent.click(screen.getByRole('button', { name: 'Won' }));

    expect(screen.getByText(/Won deals stay won/)).toBeVisible();
    expect(screen.queryByText(/find it again/i)).toBeNull();
  });

  it('still says who an account is being assigned to when that is the news', () => {
    // The consequence of engaging is the assignment, and that sentence was
    // already right — it must not be replaced by a generic one.
    render(actions());
    fireEvent.click(screen.getByRole('button', { name: "I'm working this" }));

    expect(screen.getByText('This account will be assigned to you.')).toBeVisible();
  });
});

describe('the confirmation says what it will actually do', () => {
  it('offers to hand it over, by name, once a colleague is chosen', () => {
    render(
      withQuery(
        <WorkflowActions
          opportunity={opportunity({ stage: 'tracking', allowed_next: ['engaged'] })}
          workspaceId="eeeeeeee-5555-4555-8555-555555555555"
          viewerId={VIEWER}
          colleagues={[{ id: COLLEAGUE, name: 'ravi@acme.com' }]}
        />,
      ),
    );
    fireEvent.click(screen.getAllByRole('button')[0]!);
    fireEvent.change(screen.getByLabelText('Who is working this'), {
      target: { value: COLLEAGUE },
    });

    expect(screen.getByRole('button', { name: 'Hand it to ravi@acme.com' })).toBeVisible();
    expect(screen.queryByRole('button', { name: 'Take it on' })).toBeNull();
  });
});
