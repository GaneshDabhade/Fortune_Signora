/**
 * 📁 **User Profile → Activity → *"Your data"*** — the design's `dataRights` block.
 *
 * ⚠️ **There is already a test for this file and it reads the SOURCE** —
 * `leave-organization.test.tsx` does `readFileSync` and greps. ⛔ **A source
 * grep cannot see whether the panel renders at all**, what the error branch
 * produces, or what a customer actually reads — 🔴 **and every assertion in it
 * would still pass if this component threw on mount.**
 *
 * ⚡ **So this is the render, and it deliberately asserts only what the grep
 * cannot reach.**
 */
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { ApiError } from '@/lib/api/client';

const push = vi.hoisted(() => vi.fn());
const mutate = vi.hoisted(() => vi.fn());
const leaveState = vi.hoisted(() => ({
  isPending: false,
  error: null as unknown,
}));

vi.mock('next/navigation', () => ({ useRouter: () => ({ push, replace: vi.fn() }) }));
vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: () => ({ activeWorkspace: { id: 'w-1', name: 'Northwind' } }),
}));
vi.mock('@/lib/query/hooks/team', () => ({
  useLeaveOrganization: () => ({
    mutate,
    get isPending() { return leaveState.isPending; },
    get error() { return leaveState.error; },
  }),
}));

import { DataRightsPanel } from '@/app/(app)/profile/data-rights-panel';

/**
 * ⚡ **The real constructor.** ⛔ **A hand-shaped `{ message }` satisfies
 * `instanceof ApiError` never**, so the component would take the else branch
 * and the test would report the generic sentence while claiming to test the
 * server's own.
 */
function apiError(message: string): ApiError {
  return new ApiError(409, { message, code: 'conflict', correlation_id: 'corr-1' });
}

/**
 * 📁 **Matches that a reader can actually SEE.**
 *
 * ⚠️ **Scoping to the `<section>` is not enough** — 🔴 **the `<dialog>` is
 * rendered inside it**, so `within(section)` still reaches the confirmation
 * copy. ⚡ **Ancestry is the real discriminator**: a closed native `<dialog>`
 * is `display:none` and out of the accessibility tree, and **jsdom honours
 * that for `getByRole` but not for `getByText`.**
 *
 * ⛔ **Asserting exactly one match is the point, not a convenience.** A
 * `getByText` that happened to match once would pass while reading whichever
 * copy came first in the DOM — **the panel's sentence and the dialog's are
 * deliberately different**, and a test that cannot tell them apart is not
 * testing either.
 */
function onScreen(matcher: RegExp | string): HTMLElement {
  const visible = screen
    .getAllByText(matcher)
    .filter((el) => el.closest('dialog') === null);
  expect(visible, `expected exactly one visible match for ${matcher}`).toHaveLength(1);
  return visible[0] as HTMLElement;
}

beforeEach(() => {
  vi.clearAllMocks();
  leaveState.isPending = false;
  leaveState.error = null;
});

describe('⛔ two of the design’s three rows describe capabilities that do not exist', () => {
  it('📁 draws neither, rather than drawing them inert', () => {
    const { container } = render(<DataRightsPanel />);
    const text = container.textContent ?? '';

    // ✅ **The pin first** — the block rendered, so the absences below are the
    // panel's answer and not an absent panel.
    expect(screen.getByRole('heading', { name: 'Your data' })).toBeInTheDocument();

    // 📁 *Download your data* — no export endpoint exists in the API.
    expect(text).not.toMatch(/download your data|request export|\bexport\b/i);
    // 📁 *Activity retention* — nothing implements an 18-month purge.
    expect(text).not.toMatch(/retention|18 month/i);
    // ⛔ **And no dead control offering either.**
    expect(screen.getAllByRole('button')).toHaveLength(1);
  });
});

describe('🔴 the sentence a customer reads promises only what leaving actually does', () => {
  it('⛔ never says work is reassigned, and never says an administrator is told', () => {
    /**
     * 📁 **The design's own copy**: *"You lose access immediately. Work you own
     * must be reassigned first, and your administrator is notified."*
     *
     * ⛔ **`leave_workspace.py` does neither.** It locks the membership, counts
     * live owners, refuses to leave a workspace ownerless, **and nothing
     * else.** ⚠️ **Rendering that sentence would tell somebody their work is
     * safe because something reassigned it** — recorded as
     * [C-1552](../../../docs/LANE_COORDINATION.md).
     *
     * ⚡ **Asserted on the RENDER, which is the half the source grep cannot
     * reach**: copy assembled from a variable, a shared constant or a prop
     * never appears in the file this component lives in.
     */
    render(<DataRightsPanel />);
    const text = document.body.textContent ?? '';

    expect(screen.getByText(/You lose access to this organization/)).toBeInTheDocument();
    expect(text).not.toMatch(/reassign/i);
    expect(text).not.toMatch(/administrator/i);
    expect(text).not.toMatch(/notified|notification/i);
  });

  it('⚡ and states what survives, because that part IS true', () => {
    /**
     * ⚠️ **Scoped to the panel, and the reason is worth recording.** `Dialog`
     * is a native `<dialog>` closed with `.close()`, so its content is
     * `display:none` and **out of the accessibility tree** — ✅ correct — but
     * **jsdom's `getByText` does not honour that**, so an unscoped query
     * matches the panel's sentence AND the dialog's.
     *
     * ⛔ **The trap is that the ambiguity is the ONLY thing that surfaced it.**
     * A single-match query would have passed while silently reading whichever
     * copy came first.
     */
    render(<DataRightsPanel />);
    expect(onScreen(/What you have already decided stays on the record/)).toBeInTheDocument();
  });

  it('⛔ and the unopened confirmation is not in the accessibility tree', () => {
    // ⚡ **The half jsdom CAN answer**: `getByRole` honours hidden even where
    // `getByText` does not, so this is the assertion that actually holds the
    // property — a closed dialog whose copy a screen reader could reach would
    // announce the consequence of an action nobody has taken.
    render(<DataRightsPanel />);
    expect(screen.queryByRole('dialog')).toBeNull();
  });
});

describe('📁 the confirmation names the consequence, never “are you sure”', () => {
  it('⛔ opens with the consequence as its title and its body', async () => {
    const user = userEvent.setup();
    render(<DataRightsPanel />);

    await user.click(screen.getByRole('button', { name: 'Leave organization' }));

    const dialog = await screen.findByRole('dialog');
    expect(dialog).toHaveTextContent('Leave this organization');
    expect(dialog).toHaveTextContent(/lose access to this organization immediately/);
    // ⚡ **A question the customer has no way to answer is not a safeguard.**
    expect(dialog.textContent ?? '').not.toMatch(/are you sure|cannot be undone\?/i);
    // ✅ **And a way out that is not the destructive one.**
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument();
  });

  it('⛔ and nothing is sent by opening it', async () => {
    const user = userEvent.setup();
    render(<DataRightsPanel />);

    await user.click(screen.getByRole('button', { name: 'Leave organization' }));
    await screen.findByRole('dialog');

    expect(mutate).not.toHaveBeenCalled();
  });
});

describe('🔴 the server’s refusal is the server’s words, not ours', () => {
  it('📁 renders what the API said when it refused', () => {
    /**
     * 📁 **ADR-0404 put the ownerless check in the application layer** because
     * *"a check in an interface can be raced by a second tab"*. ⚡ **So the
     * panel pre-checks nothing and reports what came back** — and the reason
     * matters to whoever reads it: *the last owner cannot leave* is actionable,
     * *something went wrong* is not.
     */
    leaveState.error = apiError('An organization cannot be left without an owner.');
    render(<DataRightsPanel />);

    const alert = screen.getByRole('alert');
    expect(alert).toHaveTextContent('An organization cannot be left without an owner.');
    // ⛔ **Not replaced by our generic sentence** — the vacuity half.
    expect(alert.textContent ?? '').not.toMatch(/could not be removed/i);
  });

  it('⚠️ and falls back to a sentence that claims nothing when the failure is not the API’s', () => {
    // ⚡ **A network fault is not a refusal**, and it carries no message a
    // customer could act on. ⛔ **The fallback must not imply the server ruled.**
    leaveState.error = new Error('socket hang up');
    render(<DataRightsPanel />);

    const alert = screen.getByRole('alert');
    expect(alert).toHaveTextContent(/could not be removed from this organization/i);
    // 📁 [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md) — **a failed write
    // must say what it did NOT do**, or the reader assumes the worst.
    expect(alert).toHaveTextContent(/Nothing has changed/);
    expect(alert.textContent ?? '').not.toMatch(/socket hang up/);
  });

  it('✅ and says nothing at all when nothing has failed', () => {
    render(<DataRightsPanel />);
    // ⚠️ **The vacuity half of both assertions above** — without this, they
    // would pass on a panel that always renders an alert.
    expect(screen.queryByRole('alert')).toBeNull();
  });
});

describe('⚡ where a leaver lands is the entry resolver’s decision, not this panel’s', () => {
  it('📁 routes to the root and names no destination of its own', async () => {
    /**
     * ⛔ **A hardcoded destination here would be a second answer to a question
     * the entry engine owns** — 📁 D-193. ⚡ **The caller may still belong to
     * other organizations**, and this component cannot know.
     */
    const user = userEvent.setup();
    render(<DataRightsPanel />);

    await user.click(screen.getByRole('button', { name: 'Leave organization' }));
    const dialog = await screen.findByRole('dialog');
    const confirm = within(dialog).getByRole('button', { name: 'Leave organization' });
    await user.click(confirm);

    expect(mutate).toHaveBeenCalledTimes(1);
    // ⚡ **Fire the success path the component was handed.**
    const options = mutate.mock.calls[0]?.[1] as { onSuccess?: () => void } | undefined;
    options?.onSuccess?.();

    await waitFor(() => expect(push).toHaveBeenCalledWith('/'));
    expect(push).toHaveBeenCalledTimes(1);
  });
});

describe('⚡ ADR-0034 — the platform’s word never reaches this block', () => {
  it('⛔ says organization, never workspace', () => {
    const { container } = render(<DataRightsPanel />);
    // ⚡ **Unscoped deliberately here** — the platform word must not appear
    // anywhere this component renders, including the copy the dialog is
    // holding for later.
    expect(container.textContent ?? '').not.toMatch(/workspace/i);
    // ✅ **Pin** — it said *something*, and that something used the customer word.
    expect(onScreen('Leave this organization')).toBeInTheDocument();
  });
});
