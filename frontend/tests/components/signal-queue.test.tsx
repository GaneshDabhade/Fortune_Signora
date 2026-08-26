/**
 * **The Signal Center's queue** — [TASK-439](../../../docs/BACKLOG.md), against
 * `docs/design-snapshot/screens/Fortune Signora Signal Center.dc.html`.
 *
 * > 📁 ***"A triage queue, not a notification list · every signal ends in a
 * > decision."***
 *
 * ⚡ **The two properties worth protecting are both about restraint**: the
 * screen must not invent the words for a signal type, and it must not print a
 * field the platform does not publish.
 */
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { formatDay } from '@/components/intelligence/dates';
import type { QueueEntry, SignalTypeName } from '@/lib/api/types';

const triage = vi.hoisted(() => vi.fn());
const resolveMutate = vi.hoisted(() => vi.fn());
const resolveReset = vi.hoisted(() => vi.fn());
/** ⚡ **Mutable, so a REFUSAL can be rendered** — a write that fails is a state
 *  this screen owes the reader, and a fixed mock can only ever show success. */
const resolveState = vi.hoisted(() => ({ isError: false, error: null as unknown }));
const catalog = vi.hoisted(() => vi.fn());
const identities = vi.hoisted(() => vi.fn());

vi.mock('@/lib/query/hooks/triage', () => ({
  useWorkspaceTriage: triage,
  // ⚡ **The mutation's real shape, not the two fields the screen used to
  // read.** ⛔ **A thin mock hid a genuine dependency**: the dialogs clear a
  // previous refusal with `reset()` on close, and a mock without it threw
  // where the product does not.
  useResolveSignal: () => ({
    mutate: resolveMutate,
    reset: resolveReset,
    isPending: false,
    ...resolveState,
  }),
}));
vi.mock('@/lib/query/hooks', () => ({
  useSignalCatalog: catalog,
  useAccountIdentities: identities,
}));
vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: () => ({ activeWorkspace: { id: 'ws-1' } }),
}));
/**
 * ⚡ **The roster the assign picker offers**, and 📁 `peopleFrom`'s rule that
 * only a membership carrying an address is offerable — so ONE of these two is
 * a choosable colleague and the other is deliberately not.
 */
vi.mock('@/lib/query/hooks/team', () => ({
  useWorkspaceMembers: () => ({
    data: {
      items: [
        { user_id: 'me', role: 'owner', member_email: 'me@acme.com' },
        { user_id: 'ana', role: 'member', member_email: 'ana@acme.com' },
        { user_id: 'ghost', role: 'member', member_email: null },
      ],
    },
  }),
}));
vi.mock('@/lib/auth/client', () => ({ useSession: () => ({ data: { user: { id: 'me' } } }) }));

import { SignalQueue } from '@/app/(app)/signals/signal-queue';

const ACME = 'acc-1';
const GLOBEX = 'acc-2';

function entry(over: Partial<QueueEntry> = {}): QueueEntry {
  return {
    signal_id: 'sig-1',
    signal_type: 'pricing_objection',
    entity_id: ACME,
    rationale: 'Two buyers raised list price on the renewal thread this week.',
    state: 'open',
    resolution: null,
    ...over,
  };
}

/**
 * ⚡ **The catalog's real shape**, including `why_it_matters` — because one of
 * the assertions below is that it never reaches a row.
 */
const TYPES: SignalTypeName[] = [
  {
    key: 'pricing_objection',
    title: 'Pricing objection',
    why_it_matters: 'A pricing objection from an economic buyer often precedes a close-date slip.',
  },
  {
    key: 'champion_left',
    title: 'Champion left',
    why_it_matters: 'A departed champion removes the internal advocate for the renewal.',
  },
];

beforeEach(() => {
  resolveState.isError = false;
  resolveState.error = null;
  resolveMutate.mockClear();
  catalog.mockReturnValue({
    data: new Map(TYPES.map((t) => [t.key, t])),
    isError: false,
    isPending: false,
  });
  identities.mockReturnValue({
    data: new Map([[ACME, { account_id: ACME, name: 'Vantage Logistics A/S' }]]),
  });
  triage.mockReturnValue({ data: { items: [entry()] }, isPending: false, isError: false });
});

describe('the queue says what is waiting', () => {
  it('⚡ takes its words from the catalog, never from a table in the screen', () => {
    /**
     * 📁 **The architecture's rule**: *"`signal_type` is a catalog key and
     * never a title… the key travels and `useSignalCatalog` supplies the
     * words. A translation table here would be a second vocabulary, and two
     * representations of one truth become contradictory truth."*
     */
    render(<SignalQueue />);
    expect(screen.getAllByText('Pricing objection').length).toBeGreaterThan(0);
    // ⛔ The raw key never reaches the screen when the catalog knows it.
    expect(screen.queryByText('pricing_objection')).not.toBeInTheDocument();
  });

  it('names the account, and says so plainly when nobody has named it', () => {
    render(<SignalQueue />);
    expect(screen.getByText('Vantage Logistics A/S')).toBeInTheDocument();

    // ⚠️ *"`name` is null when nobody has named the account."* ⛔ The id is not
    // printed as a fallback — an id is not a name and nobody can act on one.
    identities.mockReturnValue({ data: new Map() });
    triage.mockReturnValue({
      data: { items: [entry({ entity_id: GLOBEX })] },
      isPending: false,
      isError: false,
    });
    render(<SignalQueue />);
    expect(screen.getAllByText('Unnamed account').length).toBeGreaterThan(0);
    expect(screen.queryByText(GLOBEX)).not.toBeInTheDocument();
  });

  it('📁 groups and counts — the design says "grouped and counted"', () => {
    triage.mockReturnValue({
      data: {
        items: [
          entry({ signal_id: 'a' }),
          entry({ signal_id: 'b' }),
          entry({ signal_id: 'c', signal_type: 'champion_left' }),
        ],
      },
      isPending: false,
      isError: false,
    });
    render(<SignalQueue />);
    // Two groups, the larger first, each with its count beside its heading.
    const headings = screen.getAllByRole('heading', { level: 2 });
    expect(headings[0]).toHaveTextContent(/Pricing objection\s*2/);
    expect(headings[1]).toHaveTextContent(/Champion left\s*1/);
  });
});

describe('🔴 the two fields with no source are absent, not invented — C-251', () => {
  it('⛔ never renders why_it_matters as a per-signal summary', () => {
    /**
     * **The tempting wrong move.** The catalog carries `why_it_matters` and it
     * would sit perfectly where the design puts `{{ s.summary }}` — ⛔ **but
     * its own contract says it is *"a fact about the TYPE, true before any
     * account exhibits it"*.** **Rendering it per row prints one sentence
     * under every signal of that type**, where the design puts a per-instance
     * finding, and it would read as though Signora had examined this account.
     */
    render(<SignalQueue />);
    expect(
      screen.queryByText(/often precedes a close-date slip/i),
    ).not.toBeInTheDocument();
  });

  it('⛔ prints no confidence, because nothing computes one', () => {
    // 📁 The design prints *"6 sources · confidence 4 of 5"* — both halves are
    // MEASUREMENTS, and `confidence` appears nowhere in the API contract.
    render(<SignalQueue />);
    expect(screen.queryByText(/confidence/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/\bof 5\b/)).not.toBeInTheDocument();
  });
});

/**
 * ⚡ **What was recorded, ignoring how it was recorded.**
 *
 * ⛔ **`toHaveBeenCalledWith` would assert the mutation's second argument too**
 * — the `onSuccess` callback that closes a dialog — **and that is plumbing, not
 * a decision.** ⚠️ **A test that breaks when a dialog changes when it closes is
 * testing the dialog**, and the property here is *what the API was told*.
 */
function recorded(call = 0): unknown {
  return (resolveMutate.mock.calls[call] as unknown[])[0];
}

describe('every signal leaves by a decision', () => {
  /**
   * 🔴 **📁 The design's four exits, and the screen's own description promises
   * all four** — *"Every one leaves the queue by being actioned, assigned,
   * snoozed or dismissed with a reason."*
   *
   * ⛔ **Two of them had no control**, so the sentence was a claim the product
   * would not perform and the *Snoozed* view showed the result of an action
   * nobody could take.
   */
  it('🔴 offers every exit its own description promises', () => {
    render(<SignalQueue />);
    for (const name of ['Act on it', 'Assign', 'Snooze', 'Dismiss']) {
      expect(screen.getByRole('button', { name }), name).toBeInTheDocument();
    }
  });

  it('records an action', async () => {
    render(<SignalQueue />);
    // 📁 ***"Act on it"*** — the design's label for the button. *Actioned* is
    // its name for the resulting STATE, and a button labelled with an outcome
    // reads as a filter.
    await userEvent.click(screen.getByRole('button', { name: 'Act on it' }));
    expect(recorded()).toEqual({ signalId: 'sig-1', outcome: { kind: 'actioned' } });
  });

  /**
   * 🔴 **📁 *"Assign to someone"*** — and 📁 `resolution.py`'s rule that it is
   * **routing, not resolving**: *"a queue that treated it as an ending would
   * lose every signal handed to a colleague."*
   */
  it('🔴 assigns to a named colleague, and offers nobody who cannot be named', async () => {
    render(<SignalQueue />);
    await userEvent.click(screen.getByRole('button', { name: 'Assign' }));

    const confirm = screen.getByRole('button', { name: 'Assign signal' });
    // ⛔ **No default.** 📁 *"the first colleague in a list is not a guess, it
    // is a person"* — so nothing is submittable until somebody is named.
    expect(confirm).toBeDisabled();

    const picker = screen.getByLabelText('Colleague');
    // ⛔ **The viewer is not offered their own signal to hand to themselves**,
    // and ⛔ **`ghost` has no address, so `colleaguesFrom` withholds it** —
    // 📁 *"'Somebody here' in a picker is a row nobody can choose between."*
    expect(within(picker).queryByText('me@acme.com')).not.toBeInTheDocument();
    expect(within(picker).queryByText(/somebody here/i)).not.toBeInTheDocument();

    await userEvent.selectOptions(picker, 'ana');
    await waitFor(() => expect(confirm).toBeEnabled());
    await userEvent.click(confirm);

    expect(recorded()).toEqual({ signalId: 'sig-1', outcome: { kind: 'assigned', to: 'ana' } });
  });

  /**
   * 🔴 **📁 *"Snooze with a date"***, and 📁 `resolution.py` refuses one that has
   * already elapsed — *"the signal would come straight back."*
   */
  it('🔴 refuses a snooze that is not in the future, and sends an instant with a zone', async () => {
    render(<SignalQueue />);
    await userEvent.click(screen.getByRole('button', { name: 'Snooze' }));

    const confirm = screen.getByRole('button', { name: 'Snooze signal' });
    expect(confirm).toBeDisabled();

    const field = screen.getByLabelText('Comes back on');
    // ⛔ **Yesterday is refused at the control**, not left to a `422` after the
    // customer has committed to it.
    await userEvent.type(field, '2020-01-01');
    expect(confirm).toBeDisabled();

    const soon = new Date();
    soon.setDate(soon.getDate() + 7);
    const day = soon.toISOString().slice(0, 10);
    await userEvent.clear(field);
    await userEvent.type(field, day);
    await waitFor(() => expect(confirm).toBeEnabled());
    await userEvent.click(confirm);

    const call = recorded() as { outcome: { kind: string; until: string } };
    expect(call.outcome.kind).toBe('snoozed');
    // ⚡ **A real instant, and in the future** — 📁 the schema requires both:
    // *"Must be in the future and carry a timezone."*
    expect(new Date(call.outcome.until).getTime()).toBeGreaterThan(Date.now());
  });

  /**
   * 🔴 **📁 The design's keyboard grammar** — *"E assigns · S snoozes · D
   * dismisses"*. ⚡ **Focus is the cursor**, because the design's `current` row
   * needs `J`/`K` and a detail pane that are not built.
   */
  it('🔴 opens the right dialog from the row the keyboard is in', async () => {
    render(<SignalQueue />);
    const row = screen.getByRole('listitem');

    await userEvent.click(within(row).getByRole('checkbox'));
    await userEvent.keyboard('e');
    expect(screen.getByRole('button', { name: 'Assign signal' })).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Cancel' }));

    within(row).getByRole('checkbox').focus();
    await userEvent.keyboard('s');
    expect(screen.getByRole('button', { name: 'Snooze signal' })).toBeInTheDocument();
  });

  /**
   * ⚠️ **The guard that stops a single-letter key being hostile** — 📁
   * `shortcuts.ts`: *"a single-letter binding that fired inside a text field
   * would be the shape that makes people distrust every shortcut."*
   */
  it('⛔ never fires a shortcut while somebody is typing a reason', async () => {
    render(<SignalQueue />);
    await userEvent.click(screen.getByRole('button', { name: 'Dismiss' }));

    const field = screen.getByLabelText(/reason/i);
    await userEvent.type(field, 'sales escalated it');

    expect(field).toHaveValue('sales escalated it');
    expect(screen.queryByRole('button', { name: 'Assign signal' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Snooze signal' })).not.toBeInTheDocument();
  });

  it('🔴 refuses a dismissal with no reason, and the type says why', async () => {
    /**
     * ⛔ **`ResolveOutcome` makes a reasonless dismissal unconstructable** —
     * this keeps that true at the edge rather than leaving the server to
     * refuse it. 📁 **And the design gives the product reason**: *"Dismissal
     * reasons feed rule precision."* **An empty one is a lost measurement.**
     */
    render(<SignalQueue />);
    await userEvent.click(screen.getByRole('button', { name: 'Dismiss' }));

    const confirm = screen.getByRole('button', { name: 'Dismiss signal' });
    expect(confirm).toBeDisabled();

    // ⛔ Whitespace is not a reason.
    await userEvent.type(screen.getByLabelText(/reason/i), '   ');
    expect(confirm).toBeDisabled();

    await userEvent.type(screen.getByLabelText(/reason/i), 'Already handled on the call');
    await waitFor(() => expect(confirm).toBeEnabled());
    await userEvent.click(confirm);

    expect(recorded()).toEqual({
      signalId: 'sig-1',
      outcome: { kind: 'dismissed', reason: 'Already handled on the call' },
    });
  });

  /**
   * 🔴 **Assigning does not close a signal** — 📁 `resolution.py`: *"Still open.
   * Assigning is routing, not resolving."*
   *
   * ⛔ **So without a chip, pressing *Assign* changes nothing a reader can
   * see**, and a control whose effect is invisible is indistinguishable from
   * one that was never wired up. 📁 The design draws it: *"Assigned · JO"*.
   */
  it('🔴 says who an open signal was routed to, and keeps its actions', () => {
    triage.mockReturnValue({
      data: {
        items: [
          entry({
            resolution: { outcome: 'assigned', assigned_to: 'ana', snoozed_until: null } as never,
          }),
        ],
      },
      isPending: false,
      isError: false,
    });
    render(<SignalQueue />);
    expect(screen.getByText('Assigned to ana@acme.com')).toBeInTheDocument();
    // ⚡ **Still actionable**, because assigning did not end it.
    expect(screen.getByRole('button', { name: 'Act on it' })).toBeInTheDocument();
  });

  /**
   * 🔴 **📁 The design draws the return on the row** — *"Snoozed · 2d"*.
   * ⛔ **This printed the bare word `snoozed`**, which told a reader the one
   * thing the tab they were standing on had already told them.
   */
  it('🔴 says when a snoozed signal comes back', () => {
    triage.mockReturnValue({
      data: {
        items: [
          entry({
            state: 'snoozed',
            resolution: {
              outcome: 'snoozed',
              assigned_to: null,
              snoozed_until: '2026-09-24T00:00:00Z',
            } as never,
          }),
        ],
      },
      isPending: false,
      isError: false,
    });
    render(<SignalQueue />);
    // ⚡ **Formatted by the product's one date function**, not by a literal —
    // 📁 `dates.ts` renders in the READER's locale, so a hardcoded *"24 Sep"*
    // would assert the machine the suite happens to run on.
    expect(
      screen.getByText(`Returns ${formatDay('2026-09-24T00:00:00Z')}`),
    ).toBeInTheDocument();
  });

  /**
   * 🔴 **A refused write must say so.** ⛔ ***Act on it*** **calls the API with
   * no dialog to report into**, so a failure left the row where it was and the
   * reader's only evidence that anything happened was the row moving — and it
   * did not. ⚡ **[P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md)'s rule
   * pointed at a write instead of a read.**
   */
  it('🔴 says when a decision could not be recorded', () => {
    resolveState.isError = true;
    resolveState.error = new Error('nope');
    render(<SignalQueue />);
    expect(screen.getByRole('alert')).toHaveTextContent(/could not be recorded/i);
  });

  it('offers no decision on a signal that has already left the queue', () => {
    triage.mockReturnValue({
      data: {
        items: [
          entry({ state: 'closed', resolution: { outcome: 'dismissed' } as never }),
        ],
      },
      isPending: false,
      isError: false,
    });
    render(<SignalQueue />);
    expect(screen.queryByRole('button', { name: 'Actioned' })).not.toBeInTheDocument();
    expect(screen.getByText('dismissed')).toBeInTheDocument();
  });
});

describe('the states the queue can be in', () => {
  it('⚡ a quiet queue is a success state, not a broken page', () => {
    triage.mockReturnValue({ data: { items: [] }, isPending: false, isError: false });
    render(<SignalQueue />);
    expect(screen.getByText(/Nothing needs review/i)).toBeInTheDocument();
  });

  it('🔴 says when it could not find out — P-A, and never renders as empty', () => {
    /**
     * ⛔ **An empty queue and an unreachable one are different facts.** A page
     * that renders the success state on a failed read tells a seller there is
     * nothing waiting when Signora simply could not look.
     */
    triage.mockReturnValue({ data: undefined, isPending: false, isError: true });
    render(<SignalQueue />);
    expect(screen.getByText(/could not be loaded/i)).toBeInTheDocument();
    expect(screen.queryByText(/Nothing needs review/i)).not.toBeInTheDocument();
  });
});

describe('🔴 the summary is the signal’s own, never the type’s', () => {
  /**
   * **This is the whole of [TASK-1427](../../../docs/BACKLOG.md), stated as a
   * test.** 📁 The row's own Playwright line: *"two rows of the same
   * `signal_type` render DIFFERENT summaries"* — ⛔ **that assertion is the
   * defect**, because the failure mode it catches is silent: rendering the
   * catalog's `why_it_matters` puts one sentence under fifty rows and **every
   * one of them looks right.**
   */
  it('⛔ two rows of the SAME type render different summaries', () => {
    const first = 'Two buyers raised list price on the renewal thread this week.';
    const second = 'Procurement asked for a discount schedule before signing.';
    triage.mockReturnValue({
      data: {
        items: [
          entry({ signal_id: 'a', rationale: first }),
          entry({ signal_id: 'b', rationale: second }),
        ],
      },
      isPending: false,
      isError: false,
    });
    render(<SignalQueue />);

    // Same type — one group, so a per-type sentence would satisfy the grouping
    // and still be wrong. The two summaries are what distinguishes them.
    expect(screen.getAllByRole('heading', { level: 2 })).toHaveLength(1);
    expect(screen.getByText(first)).toBeInTheDocument();
    expect(screen.getByText(second)).toBeInTheDocument();
  });

  it('⚡ and the guard can fail — identical rationales collapse to one node', () => {
    // 📁 B-162's lesson: a scan proved only by passing is a scan nobody has
    // seen work. If the component rendered a per-TYPE sentence, both rows
    // would carry the same text — this asserts that case is distinguishable.
    const same = 'The same sentence under every row.';
    triage.mockReturnValue({
      data: {
        items: [
          entry({ signal_id: 'a', rationale: same }),
          entry({ signal_id: 'b', rationale: same }),
        ],
      },
      isPending: false,
      isError: false,
    });
    render(<SignalQueue />);
    expect(screen.getAllByText(same)).toHaveLength(2);
  });

  it('📱 clamped to two lines, and complete in the DOM', () => {
    /**
     * ⛔ 📁 *"a truncated rationale must not read as the whole reason"*. The
     * clamp is visual only — **the full sentence stays in the document**, so a
     * screen reader hears all of it and `title` carries it on hover.
     */
    const long =
      'Procurement asked for a discount schedule before signing, and two buyers ' +
      'raised list price on the renewal thread in the same week, which together ' +
      'read as a budget conversation rather than an objection to the product.';
    triage.mockReturnValue({
      data: { items: [entry({ rationale: long })] },
      isPending: false,
      isError: false,
    });
    render(<SignalQueue />);
    const node = screen.getByText(long);
    expect(node).toHaveClass('line-clamp-2');
    expect(node).toHaveAttribute('title', long);
  });
});

describe('📁 Signal Center mechanics — the dismissal reason stays free text', () => {
  /**
   * 📁 ***"Dismissal is training data — every dismissal takes a reason from a
   * closed list."*** ⛔ **And it must NOT, here.**
   *
   * 📁 `domain/resolution.py` refuses the closed set in terms: *"Deliberately
   * free text and not a closed set. A vocabulary of dismissal reasons is a
   * product decision about what the platform believes can be wrong with its
   * own judgement, and inventing one inside an implementation slice would be
   * exactly the 'architecture arriving in a feature' §20e forbids."*
   *
   * ⚡ **A `<Select>` here would be that invention one layer up**, and it is
   * the obvious "fix" for somebody reading the design without reading the
   * domain. **This test is what makes that read the source first.**
   *
   * ✅ **The mechanic's stated purpose is served regardless**: `precision.py`
   * counts OUTCOMES, not reason texts.
   */
  it('🔴 offers a free-text reason, not a list the design has not chosen', async () => {
    render(<SignalQueue />);
    await userEvent.click(screen.getByRole('button', { name: 'Dismiss' }));

    // ⛔ A textbox, and deliberately NOT a combobox.
    const field = screen.getByLabelText(/reason/i);
    expect(field).toHaveProperty('tagName', 'INPUT');
    expect(screen.queryByRole('combobox')).not.toBeInTheDocument();
  });
});
