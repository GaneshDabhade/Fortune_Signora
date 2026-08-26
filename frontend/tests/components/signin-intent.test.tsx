/**
 * 🔴 **[C-1559](../../../docs/LANE_COORDINATION.md) — the half a lane can
 * take.**
 *
 * 📁 `Session Continuity`'s `contract`: ***"Deep-link intent is captured before
 * the first redirect, stored in sessionStorage, replayed once, then
 * deleted."***
 *
 * ⚡ **The reading side has always been complete** — 📁 `use-entry.ts:144` reads
 * `?next=`, and `rules.ts` 06–09 route it four ways with open-redirect
 * validation in `captureIntent`. ⛔ **This form dropped the parameter**, so the
 * chain ended one step before the resolver built for it.
 *
 * ⚠️ **These do NOT close C-1559.** 📁 The three authenticated layouts still
 * `redirect('/signin')` carrying nothing, so a deep link is discarded **before**
 * it reaches this form. **That capture needs `middleware.ts`, which is 🔴
 * routing.**
 */
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const push = vi.hoisted(() => vi.fn());
const refresh = vi.hoisted(() => vi.fn());
const search = vi.hoisted(() => ({ value: new URLSearchParams() }));
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push, refresh }),
  useSearchParams: () => search.value,
}));

const signInWithPassword = vi.hoisted(() => vi.fn());
vi.mock('@/lib/auth/client', () => ({
  signIn: vi.fn(),
  signInWithPassword: (...a: unknown[]) => signInWithPassword(...a),
}));

import { SignInForm } from '@/app/(auth)/signin/signin-form';

beforeEach(() => {
  push.mockReset();
  refresh.mockReset();
  signInWithPassword.mockReset().mockResolvedValue({ ok: true });
  search.value = new URLSearchParams();
});

async function signIn() {
  const user = userEvent.setup();
  render(<SignInForm passwordEnabled oauthMethods={[]} />);
  await user.type(screen.getByLabelText(/email/i), 'dana@northwind.test');
  await user.type(screen.getByLabelText(/password/i), 'correct horse battery');
  await user.click(screen.getByRole('button', { name: /sign in/i }));
}

describe('🔴 a deep link that reaches sign-in is honoured, not dropped', () => {
  it('forwards the intended path to the resolver', async () => {
    search.value = new URLSearchParams({ next: '/accounts/abc-123' });

    await signIn();

    await waitFor(() =>
      expect(push).toHaveBeenCalledWith('/?next=%2Faccounts%2Fabc-123'),
    );
  });

  it('goes to the resolver unadorned when there is no intent', async () => {
    // ⚡ The positive control: forwarding unconditionally would send `/?next=`
    // with an empty value on every ordinary sign-in.
    await signIn();

    await waitFor(() => expect(push).toHaveBeenCalledWith('/'));
  });
});

describe('⛔ and a hostile `next` is refused, not forwarded', () => {
  /**
   * 🔴 **The value arrives in a URL a stranger can write.** ⚡ `decodeIntent`
   * rejects `//`, `/\`, any scheme and control characters — **forwarding it
   * unchecked would be the open redirect the resolver's own validator exists
   * to refuse.**
   */
  it.each([
    ['//evil.example.com', 'a protocol-relative host'],
    ['https://evil.example.com', 'an absolute URL'],
    ['javascript:alert(1)', 'a scheme'],
    ['not-a-path', 'a bare word'],
  ])('refuses %s (%s)', async (hostile) => {
    search.value = new URLSearchParams({ next: hostile });

    await signIn();

    await waitFor(() => expect(push).toHaveBeenCalledWith('/'));
  });
});
