/**
 * **Onboarding step 3 — the only step that creates something.** 📁 `Fortune
 * Signora Onboarding.dc.html` screens `03` and `08`.
 *
 * 🔴 **511 lines, the largest file in the repository nothing rendered.** ⚡ **And
 * it is the step every later screen depends on** — the organization does not
 * exist until this form succeeds, which is why the design marks it *Required*
 * and gives it no *Skip for now*.
 *
 * ⛔ **It also carries a permanent decision.** 📁 *"Permanent once created."*
 * The address cannot be changed afterwards — there is no `PATCH /workspaces` —
 * **so every verdict this screen paints is a verdict about something
 * irreversible**, and a wrong one is not a wrong pixel.
 */
import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ApiError } from '@/lib/api/client';
import { MIN_SLUG } from '@/lib/workspace/slug';

const push = vi.hoisted(() => vi.fn());
const checkSlug = vi.hoisted(() => vi.fn());
const mutateAsync = vi.hoisted(() => vi.fn());
const setActiveWorkspace = vi.hoisted(() => vi.fn());
const useSession = vi.hoisted(() => vi.fn());
const isPending = vi.hoisted(() => ({ value: false }));

vi.mock('next/navigation', () => ({ useRouter: () => ({ push, replace: vi.fn() }) }));
vi.mock('@/lib/auth/client', () => ({ useSession }));
vi.mock('@/lib/api/workspaces', () => ({ checkSlug }));
vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: () => ({ setActiveWorkspace }),
}));
vi.mock('@/lib/query/hooks', () => ({
  useCreateWorkspace: () => ({ mutateAsync, get isPending() { return isPending.value; } }),
}));

import { CreatingWorkspace, WorkspaceForm } from '@/app/(onboarding)/onboarding/workspace-form';

/**
 * ⚡ **The real constructor, `ApiError(status, body)`.** ⛔ **A hand-shaped
 * `{ status: 409 }` is the fixture mistake this lane has now made twice** —
 * it satisfies `instanceof` never, so a branch keyed on the class takes the
 * else and the test reports a path the product does not run.
 */
function apiError(status: number, code: string): ApiError {
  return new ApiError(status, { message: 'refused', code, correlation_id: 'corr-1' });
}

function signedInAs(email: string) {
  useSession.mockReturnValue({ data: { user: { email } } });
}

/** 📁 The server answers with the NORMALIZED slug, which is the whole of B-277's shape. */
function available(slug: string) {
  return { slug, available: true, reason: null };
}

beforeEach(() => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  vi.clearAllMocks();
  isPending.value = false;
  signedInAs('marta@northwind.com');
  checkSlug.mockImplementation((s: string) => Promise.resolve(available(s)));
  mutateAsync.mockResolvedValue({ id: 'w-1', name: 'Northwind' });
});
afterEach(() => {
  vi.useRealTimers();
});

/**
 * ⚠️ **`.catch().finally()` is more than one microtask tick**, and a single
 * `act(async () => {})` does not reach the `finally`. 🔴 **A test that under-
 * flushes asserts the state BEFORE the interesting thing happened** — which is
 * how this file's first draft passed with the defect reintroduced.
 */
async function settle() {
  await act(async () => {
    for (let i = 0; i < 5; i += 1) await Promise.resolve();
  });
}

function typist() {
  return userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
}

const name = () => screen.getByLabelText('Organization name') as HTMLInputElement;
const url = () => screen.getByLabelText('Organization URL') as HTMLInputElement;

describe('🔴 the suggestion is the signed-in address, and nothing else is claimed', () => {
  it('📁 pre-fills both fields and says where the value came from', () => {
    render(<WorkspaceForm />);

    expect(name().value).toBe('Northwind');
    expect(url().value).toBe('northwind');
    // 📁 *"Filled from northwind.com — edit if it's wrong"* — ⚡ **the domain
    // is named, so the customer can tell a guess from a fact.**
    expect(screen.getByText(/Filled from northwind\.com/)).toBeInTheDocument();
  });

  it('⛔ suggests nothing at all from a free mailbox, rather than an organization called Gmail', () => {
    signedInAs('marta@gmail.com');
    render(<WorkspaceForm />);

    // ✅ **The pin** — the form rendered, so the emptiness below is the
    // screen's answer rather than an absent screen.
    expect(screen.getByRole('button', { name: 'Create organization' })).toBeInTheDocument();

    expect(name().value).toBe('');
    expect(url().value).toBe('');
    expect(screen.queryByText(/Filled from/)).toBeNull();
  });

  it('⛔ and states no data region, because nothing in this product records one', () => {
    render(<WorkspaceForm />);
    const text = document.body.textContent ?? '';

    // 📁 The design's footnote is *"You'll be the owner. Data region is EU, set
    // by your account."* ⚡ **Half of it is a fact and half is a claim about
    // where a customer's data physically lives.** ⛔ **Only the fact ships.**
    expect(screen.getByText(/You.{0,3}ll be the owner/)).toBeInTheDocument();
    expect(text).not.toMatch(/data region/i);
    expect(text).not.toMatch(/\bEU\b/);
  });
});

describe('⛔ the availability check is debounced, and a stale answer never paints', () => {
  it('📁 asks once, 300ms after typing stops — not once per keystroke', async () => {
    signedInAs('marta@gmail.com');
    const user = typist();
    render(<WorkspaceForm />);

    await user.type(name(), 'Northwind');
    await waitFor(() => expect(checkSlug).toHaveBeenCalled());

    // ⚡ **Seven keystrokes produce a slug of length ≥ 3**, and a check per
    // keystroke would be seven requests for an answer about six discarded
    // strings.
    expect(checkSlug).toHaveBeenCalledTimes(1);
    expect(checkSlug).toHaveBeenLastCalledWith('northwind');
  });

  it('🔴 resolves a verdict when the server NORMALIZES the slug, rather than checking forever', async () => {
    /**
     * 🔴 **The defect this replaced compared `answer.slug === candidate` and
     * discarded anything that differed.** ⛔ **The server answers with the
     * normalized slug**, so every value needing normalization had its verdict
     * thrown away and the field said *Checking…* permanently.
     *
     * ⚡ **That is [B-277](../../../docs/BUGS.md)'s shape**: a read that
     * finished, rendered as one still running. ⚠️ **`live` already carries
     * staleness**, so the comparison protected nothing and cost the one case
     * it existed for.
     */
    signedInAs('marta@gmail.com');
    checkSlug.mockImplementation(() => Promise.resolve(available('north-wind')));
    const user = typist();
    render(<WorkspaceForm />);

    /**
     * ⚠️ **Typed into the URL field, and that is the whole point.** 🔴 **The
     * first draft typed into the NAME field and the fire-test did not fire** —
     * `suggestSlug` normalizes on the way in, so the candidate was ALREADY
     * `north-wind` and equalled the server's answer. ⛔ **The test reproduced
     * the defect's shape without reproducing its precondition.**
     *
     * ⚡ **`onChange` on the URL field stores the raw value** — it is the one
     * path where what the client asks about and what the server answers with
     * can differ, which is exactly why the discarded answer went unnoticed.
     */
    await user.clear(url());
    await user.type(url(), 'North_Wind');

    await waitFor(() => expect(screen.getByText('Available')).toBeInTheDocument());
    expect(screen.queryByText('Checking…')).toBeNull();
  });
});

describe('📁 P-A — a check that FAILED is not a URL that is taken', () => {
  it('⛔ leaves Create enabled and claims nothing when the check errors', async () => {
    /**
     * ⚠️ **Rendering a failed read as *Unavailable* would lock somebody out of
     * an address that is theirs**, permanently, on the one screen where the
     * decision cannot be undone. ✅ **The server decides.**
     */
    checkSlug.mockRejectedValue(apiError(503, 'unavailable'));
    render(<WorkspaceForm />);

    /**
     * 🔴 **The first draft asserted `toBeEnabled()` inside `waitFor` and it
     * passed on the INITIAL render** — before the check had been asked, let
     * alone failed. ⛔ **`waitFor` succeeds the moment its body succeeds**, so
     * it was measuring the state before the interesting thing happened.
     *
     * ✅ **Wait for the request, then flush the rejection**, and only then
     * assert.
     */
    await waitFor(() => expect(checkSlug).toHaveBeenCalled());
    await settle();

    expect(screen.queryByText('Unavailable')).toBeNull();
    expect(screen.getByRole('button', { name: 'Create organization' })).toBeEnabled();
  });

  it('🔴 renders NO verdict when the check failed — never "Checking…" forever', async () => {
    /**
     * 🔴 **Found by fire-testing this file, not by reading it.** ⛔ **A failed
     * check left `checking` false and `availability` null**, which is the same
     * pair as a check that has not answered yet — **so the field said
     * *Checking…* permanently.** ⚡ **A read that finished, rendered as one
     * still running**, on the field carrying onboarding's only irreversible
     * decision.
     *
     * 📁 **The design rules it without a new state**: *"Enrichment unavailable:
     * fields stay empty and editable, **the Inferred badge is absent**, and the
     * step is never blocked by it."*
     */
    checkSlug.mockRejectedValue(apiError(503, 'unavailable'));
    render(<WorkspaceForm />);

    await waitFor(() => expect(checkSlug).toHaveBeenCalled());
    await settle();

    expect(screen.queryByText('Checking…')).toBeNull();
    expect(screen.queryByText('Available')).toBeNull();
    expect(screen.queryByText('Unavailable')).toBeNull();
    // ✅ **The pin** — the control is on screen, so the three absences above
    // are this field's answer rather than an absent field.
    expect(url()).toBeInTheDocument();
  });

  it('⛔ and a genuinely taken URL blocks, with the reason beneath the control', async () => {
    // ⚡ **The vacuity half of the assertion above** — without this, *never
    // says Unavailable* would pass on a screen that cannot say it at all.
    checkSlug.mockResolvedValue({
      slug: 'northwind',
      available: false,
      reason: 'That address is already in use.',
    });
    render(<WorkspaceForm />);

    await waitFor(() => expect(screen.getByText('Unavailable')).toBeInTheDocument());
    expect(screen.getByText('That address is already in use.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Create organization' })).toBeDisabled();
    expect(url()).toHaveAttribute('aria-invalid', 'true');
  });

  it(`⚠️ a slug under ${MIN_SLUG} characters says so, and is never called unavailable`, async () => {
    signedInAs('marta@gmail.com');
    const user = typist();
    render(<WorkspaceForm />);

    await user.type(name(), 'No');

    expect(screen.getByText(`${MIN_SLUG} characters or more`)).toBeInTheDocument();
    // ⛔ **A red mark on a name somebody is still typing teaches them to
    // ignore the mark.**
    expect(screen.queryByText('Unavailable')).toBeNull();
    expect(checkSlug).not.toHaveBeenCalled();
  });
});

describe('🔴 a refusal from the server keeps everything the person typed', () => {
  it('📁 renders the design’s own sentence for a URL taken while typing', async () => {
    mutateAsync.mockRejectedValue(apiError(409, 'conflict'));
    const user = typist();
    render(<WorkspaceForm />);

    await user.click(screen.getByRole('button', { name: 'Create organization' }));

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent(/taken while you were typing/);
    expect(alert).toHaveTextContent(/Your other answers are saved/);

    // ⚡ **The claim the sentence makes, asserted rather than trusted** — 📁 a
    // screen that says nothing is lost while clearing the form is worse than
    // one that says nothing.
    expect(name().value).toBe('Northwind');
    expect(url().value).toBe('northwind');
  });

  it('⛔ and never sends the reader to the next screen on a failure', async () => {
    mutateAsync.mockRejectedValue(apiError(500, 'internal_error'));
    const user = typist();
    render(<WorkspaceForm />);

    await user.click(screen.getByRole('button', { name: 'Create organization' }));

    expect(await screen.findByRole('alert')).toHaveTextContent(/could not create/i);
    expect(push).not.toHaveBeenCalled();
    expect(setActiveWorkspace).not.toHaveBeenCalled();
  });

  it('✅ and on success it makes the organization active BEFORE navigating', async () => {
    /**
     * ⚡ **Order is the assertion.** 📁 Every screen after this one is
     * organization-scoped, and [B-277](../../../docs/BUGS.md) is precisely
     * what an onboarding screen does with no active organization.
     */
    const user = typist();
    render(<WorkspaceForm />);

    await user.click(screen.getByRole('button', { name: 'Create organization' }));

    await waitFor(() => expect(push).toHaveBeenCalledWith('/onboarding/company'));
    expect(mutateAsync).toHaveBeenCalledWith({ name: 'Northwind', slug: 'northwind' });
    expect(setActiveWorkspace).toHaveBeenCalledWith('w-1');
    // ⚠️ **The fallbacks make a MISSING call fail rather than crash** — an
    // absent order is `undefined`, and `Infinity < 0` is false.
    expect(setActiveWorkspace.mock.invocationCallOrder[0] ?? Infinity).toBeLessThan(
      push.mock.invocationCallOrder[0] ?? 0,
    );
  });
});

describe('⚡ ADR-0034 — the customer never reads the platform’s word', () => {
  it('⛔ says organization throughout, and workspace nowhere', () => {
    const { container } = render(<WorkspaceForm />);
    expect(screen.getByText('Name your organization')).toBeInTheDocument();
    expect(container.textContent ?? '').not.toMatch(/workspace/i);
  });
});

describe('📁 screen 08 — the wait is named steps, and it claims no progress it cannot see', () => {
  it('⛔ names no data region among the steps', () => {
    render(<CreatingWorkspace name="Northwind" />);

    expect(screen.getByText('Creating Northwind')).toBeInTheDocument();
    expect(screen.getByText('Applying your preferences')).toBeInTheDocument();
    // 📁 The design's mock lists *Data region set to EU* as a completed step.
    // ⛔ **A tick beside that sentence is a claim about where somebody's data
    // physically lives**, and nothing here sets or records one.
    expect(document.body.textContent ?? '').not.toMatch(/data region/i);
  });

  it('⚠️ says nothing about a long wait before there has been one', () => {
    render(<CreatingWorkspace name="Northwind" />);
    expect(screen.queryByText(/taking longer/i)).toBeNull();
  });

  it('📁 and past 6s it says so — without offering to continue in the background', () => {
    /**
     * 📁 The design says *"offers to continue in the background"*. ⛔ **That
     * control is deliberately not built**: there is nothing to continue *to*
     * until the organization exists, and every screen after this one needs it.
     * ⚡ **An offer that cannot do what it says is worse than no offer.**
     */
    render(<CreatingWorkspace name="Northwind" />);

    // ⚠️ **Inside `act`** — the copy is driven by a 1s interval writing
    // state, and advancing the clock outside `act` moves the timer without
    // ever flushing the render it causes.
    act(() => { vi.advanceTimersByTime(6000); });

    expect(screen.getByText(/taking longer than usual/i)).toBeInTheDocument();
    expect(screen.getByText(/Nothing is lost/)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /background/i })).toBeNull();
    expect(document.body.textContent ?? '').not.toMatch(/in the background/i);
  });

  it('⛔ and a nameless organization is not rendered as an empty one', () => {
    // ⚡ **`Creating ` with nothing after it** is the absence-collapsed-into-a-
    // value shape this lane keeps finding.
    render(<CreatingWorkspace name="" />);
    expect(screen.getByText('Creating your organization')).toBeInTheDocument();
  });
});
