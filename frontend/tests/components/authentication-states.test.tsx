/**
 * **Workflow 1, milestone 3** — the states between *signed in* and *signed
 * out*, which is where enterprise authentication actually fails.
 *
 * **TASK-467**, against
 * `docs/design-snapshot/screens/Fortune Signora Authentication.dc.html` — the
 * design's own framing: *"the branch points are where enterprise
 * authentication actually fails — domain policy, expired invitations, and
 * session expiry mid-work."*
 *
 * ⚡ **The load-bearing tests here are the ones about what is *not* rendered.**
 * A countdown with no header behind it, a doubling window Better Auth does not
 * implement, an identity provider nobody configured, a green status dot shown
 * before the first response — each is a claim the screen would be making on
 * the platform's behalf, on the surface an enterprise security team reads most
 * carefully.
 */

import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { Authenticating } from '@/app/(auth)/sign-in/authenticating';
import { ErrorDetail } from '@/app/(auth)/error/error-detail';
import { Throttled } from '@/app/(auth)/sign-in/throttled';
import { SignInForm } from '@/app/(auth)/sign-in/sign-in-form';
import { SsoMethods } from '@/app/(auth)/sso/sso-methods';
import { ServiceStatus } from '@/components/auth/service-status';
import { SessionLock } from '@/components/auth/session-lock';

const refresh = vi.fn();
const push = vi.fn();
let search = new URLSearchParams();

vi.mock('next/navigation', () => ({
  useRouter: () => ({ refresh, push }),
  usePathname: () => '/',
  useSearchParams: () => search,
}));

const signInWithPassword = vi.fn();
const signOut = vi.fn();
const signIn = vi.fn();
const session = vi.fn();

vi.mock('@/lib/auth/client', () => ({
  signInWithPassword: (...args: unknown[]) => signInWithPassword(...args),
  signOut: () => signOut(),
  signIn: (provider: string) => signIn(provider),
  useSession: () => session(),
}));

beforeEach(() => {
  vi.clearAllMocks();
  session.mockReturnValue({ data: null });
  search = new URLSearchParams();
});

// ═══════════════════════════════════════════════════════════════════════════
// Design 15 · Authenticating
// ═══════════════════════════════════════════════════════════════════════════

describe('signing you in — design 15', () => {
  afterEach(() => vi.useRealTimers());

  it('⛔ shows nothing at all below 800ms', () => {
    // *"Named steps replace a bare spinner past 800ms."* Below it the button
    // is already saying **Signing in…**, and swapping the whole card out for
    // one frame is a flash rather than feedback.
    vi.useFakeTimers();
    const { container } = render(
      <Authenticating stage="credentials" onCancel={vi.fn()} />,
    );

    expect(container).toBeEmptyDOMElement();
  });

  it('names the step that is actually running, once it is worth explaining', async () => {
    vi.useFakeTimers();
    render(<Authenticating stage="credentials" onCancel={vi.fn()} />);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(800);
    });

    expect(screen.getByRole('heading', { name: 'Signing you in…' })).toBeVisible();
    expect(screen.getByText('Checking your credentials')).toBeVisible();
    expect(screen.getByText('Preparing your organization')).toBeVisible();
  });

  it('⛔ narrates only the two stages it can observe, never the third', async () => {
    // The design names **verified credentials · checking membership · loading
    // permissions**. Permissions resolve in the authenticated shell *after*
    // the navigation, against a session that does not exist while this card
    // is on screen — so a third step would be this screen narrating work it
    // cannot see, which is the fabricated-progress trap in its most
    // convincing form.
    vi.useFakeTimers();
    render(<Authenticating stage="credentials" onCancel={vi.fn()} />);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(800);
    });

    expect(screen.queryByText(/permission/i)).not.toBeInTheDocument();
    expect(screen.getAllByRole('listitem')).toHaveLength(2);
  });

  it('offers an escape past 8 seconds, and it cancels rather than hides', async () => {
    // *"Past 8 seconds the card offers to cancel and try another method — it
    // never hangs silently."*
    vi.useFakeTimers();
    const onCancel = vi.fn();
    render(<Authenticating stage="credentials" onCancel={onCancel} />);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(800);
    });
    expect(screen.queryByRole('button', { name: /cancel/i })).not.toBeInTheDocument();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(7200);
    });
    expect(screen.getByText(/taking longer than usual/i)).toBeVisible();

    vi.useRealTimers();
    await userEvent.click(screen.getByRole('button', { name: /cancel/i }));
    expect(onCancel).toHaveBeenCalled();
  });

  it('a completed step reads as completed without relying on the tick', async () => {
    // 1.4.1 — the mark is decorative, so the state lives in the text.
    vi.useFakeTimers();
    render(<Authenticating stage="organization" onCancel={vi.fn()} />);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(800);
    });

    expect(screen.getByText('— done')).toBeInTheDocument();
    expect(screen.getByText('— in progress')).toBeInTheDocument();
  });
});

// ═══════════════════════════════════════════════════════════════════════════
// Design 16 · Authentication error
// ═══════════════════════════════════════════════════════════════════════════

describe('the identity provider refused — design 16', () => {
  it("quotes the provider's own words rather than paraphrasing them", () => {
    // Both values are Better Auth's own query parameters — the OAuth fields
    // the provider returned. A paraphrase would be a claim about somebody
    // else's system.
    search = new URLSearchParams({
      error: 'access_denied',
      error_description: 'user not assigned to this application',
    });
    render(<ErrorDetail />);

    expect(screen.getByText('user not assigned to this application')).toBeVisible();
    expect(screen.getByText(/your IT team assigns it/i)).toBeVisible();
  });

  it('⛔ says the provider gave no reason, rather than inventing one', () => {
    search = new URLSearchParams({ error: 'server_error' });
    render(<ErrorDetail />);

    expect(screen.getByText(/sent no reason/i)).toBeVisible();
  });

  it("the copyable reference is the provider's code, not a generated one", async () => {
    // ⚡ **An identifier this screen made up would be meaningless to the only
    // people who can act on it.** What an IT team pastes into a ticket has to
    // be what their own provider logged.
    const writeText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal('navigator', { clipboard: { writeText } });
    search = new URLSearchParams({ error: 'access_denied', error_description: 'nope' });
    render(<ErrorDetail />);

    await userEvent.click(screen.getByRole('button', { name: /copy/i }));
    expect(writeText).toHaveBeenCalledWith('access_denied — nope');
    vi.unstubAllGlobals();
  });

  it('⛔ never names a provider it was not told', () => {
    // The design's heading is *"Okta rejected the sign-in"*. Better Auth's
    // error redirect carries no provider, and naming a guess would put a
    // wrong vendor in front of a customer's IT team.
    search = new URLSearchParams({ error: 'access_denied' });
    render(<ErrorDetail />);

    expect(screen.queryByText(/okta|entra|azure|google/i)).not.toBeInTheDocument();
  });
});

// ═══════════════════════════════════════════════════════════════════════════
// Design 12 · Too many attempts
// ═══════════════════════════════════════════════════════════════════════════

describe('too many attempts — design 12', () => {
  it('states the pause, and that it is per device rather than per account', () => {
    // True of this implementation and not merely copied: Better Auth keys its
    // limiter on `ip + path`, so the sentence is a description.
    render(<Throttled retryAfterSeconds={278} onExpire={vi.fn()} />);

    expect(screen.getByRole('heading', { name: 'Too many attempts' })).toBeVisible();
    expect(
      screen.getByText(/sign-in is paused for this device/i),
    ).toBeVisible();
    expect(screen.getByText(/per device and IP, not per account/i)).toBeVisible();
  });

  it('counts down from the seconds the response carried', () => {
    render(<Throttled retryAfterSeconds={278} onExpire={vi.fn()} />);

    expect(screen.getByText('4:38')).toBeVisible();
  });

  it('⛔ shows no countdown when nothing told it one', () => {
    // A `429` whose `X-Retry-After` a proxy stripped. **The state is still
    // reported; the number is not invented** — a made-up countdown is a
    // promise about when sign-in resumes that nothing supports (P-A).
    render(<Throttled onExpire={vi.fn()} />);

    expect(screen.getByRole('heading', { name: 'Too many attempts' })).toBeVisible();
    expect(screen.getByText(/try again shortly/i)).toBeVisible();
    expect(screen.queryByText(/^\d+:\d\d$/)).not.toBeInTheDocument();
  });

  it("⛔ never claims the window doubles, because Better Auth's does not", () => {
    // The design says *"doubles with each further attempt"*. The vendor's
    // window is a fixed rolling ten seconds. Rendering the sentence would
    // misstate a security control by a factor of two.
    render(<Throttled retryAfterSeconds={278} onExpire={vi.fn()} />);

    expect(screen.queryByText(/doubles/i)).not.toBeInTheDocument();
  });

  it('releases the screen when the window runs out', async () => {
    vi.useFakeTimers();
    const onExpire = vi.fn();
    try {
      render(<Throttled retryAfterSeconds={2} onExpire={onExpire} />);
      expect(screen.getByText('0:02')).toBeVisible();

      // Inside `act`, because the tick lands in a `setInterval` callback:
      // without it the state update is queued and the effect that answers it
      // has not run when the assertion reads the spy.
      await act(async () => {
        await vi.advanceTimersByTimeAsync(2000);
      });

      expect(onExpire).toHaveBeenCalled();
    } finally {
      vi.useRealTimers();
    }
  });
});

// ═══════════════════════════════════════════════════════════════════════════
// The defect: a throttle reported as a wrong password
// ═══════════════════════════════════════════════════════════════════════════

describe('the sign-in card answers a throttle as a throttle', () => {
  it('🔴 replaces the form, and never says the credentials did not match', async () => {
    // **This is the regression.** Before milestone 3 the client mapped every
    // non-403 failure to *"that email and password do not match an account"* —
    // so somebody whose password was correct was told it was wrong, and the
    // retry that message invites is the one action that extends the block.
    signInWithPassword.mockResolvedValue({
      ok: false,
      throttled: true,
      retryAfterSeconds: 9,
      error: 'For your protection, sign-in is paused for this device.',
    });

    render(<SignInForm passwordEnabled oauthMethods={[]} />);
    await userEvent.type(screen.getByLabelText('Work email'), 'm.reinhardt@northwind.com');
    await userEvent.type(screen.getByLabelText('Password'), 'correct-horse');
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }));

    expect(await screen.findByRole('heading', { name: 'Too many attempts' })).toBeVisible();
    expect(screen.queryByText(/don't match|do not match/i)).not.toBeInTheDocument();
    // The form is gone rather than disabled: every use of it while paused
    // makes the wait longer.
    expect(screen.queryByLabelText('Work email')).not.toBeInTheDocument();
  });

  it('a wrong password is still answered as one', async () => {
    signInWithPassword.mockResolvedValue({ ok: false, error: "That email and password don't match." });

    render(<SignInForm passwordEnabled oauthMethods={[]} />);
    await userEvent.type(screen.getByLabelText('Work email'), 'm.reinhardt@northwind.com');
    await userEvent.type(screen.getByLabelText('Password'), 'wrong');
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }));

    expect(await screen.findByText("That email and password don't match.")).toBeVisible();
    expect(screen.queryByRole('heading', { name: 'Too many attempts' })).not.toBeInTheDocument();
  });
});

// ═══════════════════════════════════════════════════════════════════════════
// Design 18 · Session expired, over the current view
// ═══════════════════════════════════════════════════════════════════════════

function withSession(expiresAt: Date) {
  session.mockReturnValue({ data: { session: { expiresAt: expiresAt.toISOString() } } });
}

describe('session expired — design 18', () => {
  afterEach(() => vi.useRealTimers());

  it('renders nothing over a live session', () => {
    withSession(new Date(Date.now() + 60_000));
    const { container } = render(<SessionLock email="m.reinhardt@northwind.com" />);

    // Closed, so the platform keeps it out of the accessibility tree — the
    // lock is mounted at the shell for every signed-in page and must cost
    // nothing until the session it watches actually expires.
    expect(container.querySelector('dialog')?.open).toBe(false);
    expect(
      screen.queryByRole('heading', { name: 'Your session expired' }),
    ).not.toBeInTheDocument();
  });

  it('locks the view once the session has expired', async () => {
    withSession(new Date(Date.now() - 1));
    render(<SessionLock email="m.reinhardt@northwind.com" />);

    expect(await screen.findByRole('heading', { name: 'Your session expired' })).toBeVisible();
    // ⚡ **The address is named on the field**, which is the design's own
    // wording — `Password for m.reinhardt@northwind.com` — so somebody who
    // shares a machine can see whose session they are resuming.
    expect(screen.getByLabelText('Password for m.reinhardt@northwind.com')).toBeVisible();
  });

  it('⛔ claims nothing about drafts, because nothing tracks them', () => {
    // The design names the record whose unsaved edits survive. Nothing in
    // this product tracks draft state, so what is claimed is only what the
    // implementation guarantees: no navigation happened.
    withSession(new Date(Date.now() - 1));
    render(<SessionLock email="m.reinhardt@northwind.com" />);

    expect(screen.getByText(/nothing has navigated away/i)).toBeVisible();
    expect(screen.queryByText(/unsaved edits/i)).not.toBeInTheDocument();
  });

  it('re-authenticates in place and never navigates', async () => {
    signInWithPassword.mockResolvedValue({ ok: true });
    withSession(new Date(Date.now() - 1));
    render(<SessionLock email="m.reinhardt@northwind.com" />);

    await userEvent.type(
      await screen.findByLabelText('Password for m.reinhardt@northwind.com'),
      'correct-horse',
    );
    await userEvent.click(screen.getByRole('button', { name: 'Unlock' }));

    await waitFor(() => expect(refresh).toHaveBeenCalled());
    // **The whole point of the screen.** A push would have thrown away the
    // route, the scroll position and every unsubmitted control — which is the
    // data-loss the design is arguing against.
    expect(push).not.toHaveBeenCalled();
  });

  it('answers a wrong password without confirming the address exists', async () => {
    signInWithPassword.mockResolvedValue({ ok: false, error: "That password doesn't match." });
    withSession(new Date(Date.now() - 1));
    render(<SessionLock email="m.reinhardt@northwind.com" />);

    await userEvent.type(
      await screen.findByLabelText('Password for m.reinhardt@northwind.com'),
      'wrong',
    );
    await userEvent.click(screen.getByRole('button', { name: 'Unlock' }));

    expect(await screen.findByText("That password doesn't match.")).toBeVisible();
    expect(screen.queryByText(/no such account|not found/i)).not.toBeInTheDocument();
  });

  it('a revoked session signs out rather than offering to unlock', async () => {
    // The design draws this line itself: *"a full redirect is used only when
    // the session is revoked rather than expired."* An administrator ended it,
    // or a password reset signed the other devices out — offering to unlock in
    // place would be offering to undo a security action.
    withSession(new Date(Date.now() + 60_000));
    const view = render(<SessionLock email="m.reinhardt@northwind.com" />);

    session.mockReturnValue({ data: null });
    view.rerender(<SessionLock email="m.reinhardt@northwind.com" />);

    await waitFor(() => expect(signOut).toHaveBeenCalled());
  });
});

// ═══════════════════════════════════════════════════════════════════════════
// Design 04 · SSO discovery
// ═══════════════════════════════════════════════════════════════════════════

describe('single sign-on — design 04', () => {
  it('offers the providers this deployment actually has', async () => {
    render(<SsoMethods methods={['microsoft']} />);

    await userEvent.click(screen.getByRole('button', { name: 'Continue with Microsoft' }));
    expect(signIn).toHaveBeenCalledWith('microsoft');
  });

  it('⛔ says so plainly when none is configured, rather than offering nothing', () => {
    render(<SsoMethods methods={[]} />);

    expect(screen.getByText(/no federated provider is configured/i)).toBeVisible();
  });
});

// ═══════════════════════════════════════════════════════════════════════════
// Design 01 · the status line an enterprise buyer reads
// ═══════════════════════════════════════════════════════════════════════════

describe('the status dot is answered, never assumed', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('⛔ is not green before anything has answered', () => {
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {})));
    render(<ServiceStatus />);

    // P-A. A dot that starts green asserts health it has not been told.
    expect(screen.getByText('Checking sign-in')).toBeVisible();
  });

  it('reports the health endpoint it actually reached', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.resolve({ json: () => Promise.resolve({ status: 'degraded' }) })),
    );
    render(<ServiceStatus />);

    expect(await screen.findByText('Sign-in degraded')).toBeVisible();
  });

  it('a request that never arrives is unavailable, not unknown', async () => {
    // If the page cannot reach its own server, nobody signs in — so the
    // honest reading of the failure is the same as the honest reading of a
    // 503, and a neutral dot would understate it.
    vi.stubGlobal('fetch', vi.fn(() => Promise.reject(new Error('offline'))));
    render(<ServiceStatus />);

    expect(await screen.findByText('Sign-in unavailable')).toBeVisible();
  });
});
