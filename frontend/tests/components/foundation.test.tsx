/**
 * Tests for the frontend platform's own machinery: theme resolution, query
 * policy, permission gating, and toast behaviour.
 *
 * These are the pieces every business page inherits without thinking about
 * them, which is exactly why they need tests — a regression here surfaces
 * as a vague complaint about one page months later.
 */
import { act, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { ToastProvider, useToast } from '@/components/feedback/toast';
import { ErrorBoundary } from '@/components/feedback/error-boundary';
import { ApiError } from '@/lib/api/client';
import { isTheme, resolveTheme } from '@/lib/design/theme';
import { queryClientConfig } from '@/lib/query/client';
import { queryKeys } from '@/lib/query/keys';
import { can, guardFor } from '@/lib/state/permissions';

describe('theme resolution', () => {
  it('resolves an explicit theme to itself', () => {
    expect(resolveTheme('dark')).toBe('dark');
    expect(resolveTheme('light')).toBe('light');
  });

  it('resolves system against the OS preference', () => {
    expect(resolveTheme('system')).toBe('light'); // matchMedia stubbed to false
  });

  it('rejects an unknown stored value', () => {
    // localStorage is user-writable; a bad value must not become a
    // data-theme attribute nothing styles.
    expect(isTheme('midnight')).toBe(false);
    expect(isTheme(null)).toBe(false);
    expect(isTheme('dark')).toBe(true);
  });
});

describe('query keys', () => {
  it('scopes every workspace key under one prefix', () => {
    const workspaceId = 'ws-1';

    // The property that makes invalidating one tenant a single call. If a
    // key escapes this prefix, switching workspaces leaves its data on
    // screen under the new workspace's header.
    expect(queryKeys.workspace(workspaceId)).toEqual(
      queryKeys.workspaceScope(workspaceId),
    );
    expect(queryKeys.members(workspaceId).slice(0, 2)).toEqual(
      queryKeys.workspaceScope(workspaceId),
    );
  });

  it('does not scope the workspace list to a workspace', () => {
    // The list is what tells you which workspaces exist, so it cannot be
    // keyed by one of them.
    expect(queryKeys.workspaces()).toEqual(['workspaces']);
  });
});

describe('query retry policy', () => {
  const retry = queryClientConfig.defaultOptions?.queries?.retry as (
    failureCount: number,
    error: unknown,
  ) => boolean;

  const apiError = (status: number) =>
    new ApiError(status, { code: 'x', message: 'x', correlation_id: 'c' });

  it('never retries a client error', () => {
    // A 400 will be a 400 again; retrying delays the message the user
    // needs. A 401 is already handled by the client's token refresh.
    expect(retry(0, apiError(400))).toBe(false);
    expect(retry(0, apiError(401))).toBe(false);
    expect(retry(0, apiError(404))).toBe(false);
  });

  it('retries a server error twice, then stops', () => {
    expect(retry(0, apiError(503))).toBe(true);
    expect(retry(1, apiError(503))).toBe(true);
    expect(retry(2, apiError(503))).toBe(false);
  });

  it('never retries a mutation', () => {
    // Mutations are not idempotent. Retrying one that may have succeeded
    // is how duplicate workspaces get created.
    expect(queryClientConfig.defaultOptions?.mutations?.retry).toBe(false);
  });
});

describe('permission gating', () => {
  it('fails closed when no role is resolved', () => {
    // Showing a control and then removing it reads as a bug; showing one
    // the caller cannot use reads as a broken feature.
    expect(can(null, 'workspace:read')).toBe(false);
    expect(can(null, 'workspace:update')).toBe(false);
  });

  it('grants a member read but not mutation', () => {
    expect(can('member', 'workspace:read')).toBe(true);
    expect(can('member', 'workspace:update')).toBe(false);
    expect(can('member', 'member:add')).toBe(false);
  });

  it('grants an owner mutation', () => {
    expect(can('owner', 'workspace:update')).toBe(true);
  });

  it('matches a guarded route and its children', () => {
    expect(guardFor('/settings')?.requires).toBe('workspace:update');
    expect(guardFor('/settings/members')?.requires).toBe('workspace:update');
    expect(guardFor('/')).toBeUndefined();
  });
});

describe('toasts', () => {
  function Harness() {
    const { toast } = useToast();
    return (
      <>
        <button onClick={() => toast({ tone: 'success', message: 'Saved' })}>
          succeed
        </button>
        <button
          onClick={() =>
            toast({ tone: 'error', message: 'Failed', detail: 'Reference: abc' })
          }
        >
          fail
        </button>
      </>
    );
  }

  it('announces politely rather than interrupting', async () => {
    render(
      <ToastProvider>
        <Harness />
      </ToastProvider>,
    );

    await userEvent.click(screen.getByText('succeed'));

    expect(screen.getByText('Saved')).toBeInTheDocument();
    // "assertive" would talk over whatever the user is doing.
    expect(document.querySelector('[aria-live]')).toHaveAttribute('aria-live', 'polite');
  });

  it('keeps an error until dismissed', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    render(
      <ToastProvider>
        <Harness />
      </ToastProvider>,
    );

    await userEvent.click(screen.getByText('fail'));
    // Wrapped in act: the dismissal timer's state update happens outside
    // React's event loop, and without act the re-render never flushes —
    // which would make this assertion pass for the wrong reason.
    await act(() => vi.advanceTimersByTimeAsync(30_000));

    // Auto-dismissing an unread error turns a failed action into an
    // unexplained one — and this one carries the support reference.
    expect(screen.getByText('Failed')).toBeInTheDocument();
    expect(screen.getByText('Reference: abc')).toBeInTheDocument();
    vi.useRealTimers();
  });

  it('dismisses a success automatically', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    render(
      <ToastProvider>
        <Harness />
      </ToastProvider>,
    );

    await userEvent.click(screen.getByText('succeed'));
    await act(() => vi.advanceTimersByTimeAsync(7_000));

    expect(screen.queryByText('Saved')).not.toBeInTheDocument();
    vi.useRealTimers();
  });
});

describe('error boundary', () => {
  function Boom(): never {
    throw new ApiError(500, {
      code: 'internal',
      message: 'boom',
      correlation_id: 'corr-123',
    });
  }

  it('contains a render failure and offers a retry', () => {
    vi.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <ErrorBoundary region="Companies">
        <Boom />
      </ErrorBoundary>,
    );

    expect(screen.getByRole('alert')).toHaveTextContent('Companies failed to load');
    expect(screen.getByRole('button', { name: 'Try again' })).toBeInTheDocument();
    vi.restoreAllMocks();
  });

  it('surfaces the correlation id so support can find the request', () => {
    vi.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <ErrorBoundary>
        <Boom />
      </ErrorBoundary>,
    );

    // The single piece of information that turns "it broke" into a
    // specific request an engineer can locate.
    expect(screen.getByText(/corr-123/)).toBeInTheDocument();
    vi.restoreAllMocks();
  });
});
