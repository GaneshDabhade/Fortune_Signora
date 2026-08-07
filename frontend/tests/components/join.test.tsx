/**
 * Joining an organization, as the person holding the link reads it.
 *
 * **The only screen shown to somebody who is not a member of the workspace it
 * is about**, so the tests are about what it does not claim: it cannot name
 * the organization, it does not join anybody by being opened, and it repeats
 * the server's refusal rather than inventing a friendlier one.
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { ApiError } from '@/lib/api/client';

const accept = vi.hoisted(() => vi.fn());
const push = vi.hoisted(() => vi.fn());

vi.mock('next/navigation', () => ({
  useParams: () => ({ workspaceId: 'aaaaaaaa-1111-4111-8111-111111111111' }),
  useRouter: () => ({ push, prefetch: vi.fn() }),
}));

vi.mock('@/lib/query/hooks/team', () => ({ useAcceptInvitation: accept }));

const signOut = vi.hoisted(() => vi.fn());
vi.mock('@/lib/auth/client', () => ({ signOut }));

import JoinPage from '@/app/(app)/join/[workspaceId]/page';

const IDLE = {
  mutate: vi.fn(),
  isPending: false,
  isSuccess: false,
  error: null,
  data: undefined,
};

beforeEach(() => {
  vi.clearAllMocks();
  accept.mockReturnValue({ ...IDLE, mutate: vi.fn() });
});

describe('the page asks rather than acts', () => {
  it('does not join anybody by being opened', () => {
    /**
     * **A side effect behind a link somebody could be sent.** Mail clients
     * preview URLs, browsers restore tabs, and joining a customer's workspace
     * is not something to do because a redirect was followed.
     */
    const mutate = vi.fn();
    accept.mockReturnValue({ ...IDLE, mutate });

    render(<JoinPage />);

    expect(mutate).not.toHaveBeenCalled();
  });

  it('joins when the person says so', async () => {
    const mutate = vi.fn();
    accept.mockReturnValue({ ...IDLE, mutate });

    render(<JoinPage />);
    await userEvent.click(screen.getByRole('button', { name: /accept invitation/i }));

    expect(mutate).toHaveBeenCalledOnce();
  });

  it('does not offer to join twice while it is joining', () => {
    accept.mockReturnValue({ ...IDLE, isPending: true });

    render(<JoinPage />);

    expect(screen.getByRole('button', { name: /joining/i })).toBeDisabled();
  });
});

describe('it does not name what it cannot read', () => {
  it('says "this organization" rather than guessing a name', () => {
    /**
     * A workspace's name is inside the tenant and the reader is not in it yet
     * — C-208's trade-off, taken knowingly. The invitation email carries the
     * name, which is where the customer already saw it.
     */
    render(<JoinPage />);

    expect(screen.getByRole('heading', { name: /join this organization/i })).toBeVisible();
  });

  it('names the role only once the membership exists', () => {
    accept.mockReturnValue({
      ...IDLE,
      isSuccess: true,
      data: { role: 'member', workspace_id: 'aaaaaaaa-1111-4111-8111-111111111111' },
    });

    render(<JoinPage />);

    expect(screen.getByText(/you are a member of this organization/i)).toBeVisible();
  });
});

describe('a refusal is repeated, not rewritten', () => {
  it('shows the sentence the server wrote', () => {
    /**
     * *"There is no invitation to this organization for your address."* The
     * server's messages are written to be read; a second phrasing here would
     * be the copy nobody maintains.
     */
    accept.mockReturnValue({
      ...IDLE,
      error: new ApiError(404, {
        code: 'invitation_not_found',
        message: 'There is no invitation to this organization for your address.',
        correlation_id: '11111111-1111-4111-8111-111111111111',
      }),
    });

    render(<JoinPage />);

    expect(
      screen.getByText(/no invitation to this organization for your address/i),
    ).toBeInTheDocument();
  });

  it('announces the refusal to a screen reader', () => {
    accept.mockReturnValue({
      ...IDLE,
      error: new ApiError(403, {
        code: 'email_not_verified',
        message: 'Verify your email address first.',
        correlation_id: '22222222-2222-4222-8222-222222222222',
      }),
    });

    render(<JoinPage />);

    expect(screen.getByRole('alert')).toHaveTextContent(/verify your email address/i);
  });

  it('says a network failure is worth retrying, which a refusal is not', () => {
    accept.mockReturnValue({ ...IDLE, error: new Error('offline') });

    render(<JoinPage />);

    expect(screen.getByRole('alert')).toHaveTextContent(/could not be reached/i);
  });

  it('🔴 a refusal offers a way out, rather than the button that just refused', async () => {
    // **Design `17 · Unauthorized`** — *"three routes out, in the order most
    // people need them"*, and the module's rule that **none is a dead end.**
    // Until milestone 4 a refusal here left one control on screen: *Accept
    // invitation*, which had just been refused and would be again.
    accept.mockReturnValue({
      ...IDLE,
      error: new ApiError(404, {
        code: 'invitation_not_found',
        message: 'There is no invitation to this organization for your address.',
        correlation_id: '33333333-3333-4333-8333-333333333333',
      }),
    });

    render(<JoinPage />);

    expect(screen.queryByRole('button', { name: 'Accept invitation' })).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Sign in as someone else' }));
    expect(signOut).toHaveBeenCalled();
  });

  it('⛔ never offers to request access, because nothing can grant it', () => {
    // The design's primary route out needs a request-to-join capability —
    // no endpoint, no table, no row. **A button that quietly did nothing is
    // worse than its absence**, which is the rule the shell already applies
    // to controls the server will refuse.
    accept.mockReturnValue({
      ...IDLE,
      error: new ApiError(404, {
        code: 'invitation_not_found',
        message: 'There is no invitation to this organization for your address.',
        correlation_id: '44444444-4444-4444-8444-444444444444',
      }),
    });

    render(<JoinPage />);

    expect(screen.queryByText(/request access/i)).not.toBeInTheDocument();
  });

  it('sends the new member to a route that exists', async () => {
    /**
     * The first draft pushed `/accounts`, which is not a route — the attention
     * list is at `/` and `/accounts/[id]` is the only page under that segment.
     * `vocabulary.test.tsx` caught it before a customer could.
     */
    accept.mockReturnValue({
      ...IDLE,
      isSuccess: true,
      data: { role: 'member', workspace_id: 'aaaaaaaa-1111-4111-8111-111111111111' },
    });

    render(<JoinPage />);
    await userEvent.click(screen.getByRole('button', { name: /go to your accounts/i }));

    expect(push).toHaveBeenCalledWith('/');
  });
});
