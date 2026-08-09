/**
 * **No internet, cold start, rendered** — [TASK-1436](../../../docs/BACKLOG.md).
 *
 * ⚡ **The formatting and the probe are tested in `tests/unit/last-connected.test.ts`.**
 * ⛔ **These are the things only the assembled screen can get wrong**: whether
 * it claims a connection time it does not have, whether retry navigates, and
 * whether it announces the way platform scope requires.
 */
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { NoConnection, RETRY_SECONDS } from '@/components/feedback/no-connection';

beforeEach(() => {
  window.localStorage.clear();
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 503 }));
});
afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('📁 the design’s own screen', () => {
  it('names what happened, not the status', () => {
    render(<NoConnection />);
    expect(screen.getByRole('heading', { name: 'No connection' })).toBeInTheDocument();
  });

  it('⚡ distinguishes "your network" from "our service"', () => {
    // 📁 The design's reason for two sentences: a person who thinks Signora is
    // down tells their colleagues Signora is down.
    render(<NoConnection />);
    expect(
      screen.getByText(/Your device reports no network.*almost certainly local/),
    ).toBeInTheDocument();
  });

  it('offers Check again and the status page', () => {
    render(<NoConnection />);
    expect(screen.getByRole('button', { name: 'Check again' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Status page' })).toBeInTheDocument();
  });
});

describe('🔴 it never claims a connection it cannot prove', () => {
  it('⛔ a browser that has never connected shows only the countdown', async () => {
    /**
     * 📁 **The design asks this screen to be *"honest about having nothing"***,
     * and this is the case where it has nothing. ⛔ **"Last connected just
     * now" would be a fabrication on the one screen told not to make any.**
     */
    render(<NoConnection />);
    await waitFor(() =>
      expect(screen.getByText(`Retrying in ${RETRY_SECONDS}s`)).toBeInTheDocument(),
    );
    expect(screen.queryByText(/Last connected/)).not.toBeInTheDocument();
  });

  it('📁 and shows both facts on one line once there is one', async () => {
    window.localStorage.setItem('signora.last-connected', String(Date.now() - 180_000));
    render(<NoConnection />);
    // 📁 "Last connected 3 minutes ago · retrying in 8s"
    await waitFor(() =>
      expect(
        screen.getByText(`Last connected 3 minutes ago · retrying in ${RETRY_SECONDS}s`),
      ).toBeInTheDocument(),
    );
  });
});

describe('🔴 retry re-checks rather than reloading', () => {
  it('⛔ Check again probes the service and does not navigate', async () => {
    /**
     * 📁 The row: *"a reload on a cold start with no network returns the
     * browser's own error page — the customer loses the product's designed
     * state and gets the browser's undesigned one, which is the one screen
     * Signora cannot style."*
     */
    const reload = vi.fn();
    Object.defineProperty(window, 'location', {
      value: { ...window.location, reload, assign: vi.fn(), replace: vi.fn() },
      writable: true,
    });

    render(<NoConnection />);
    await userEvent.click(screen.getByRole('button', { name: 'Check again' }));

    expect(globalThis.fetch).toHaveBeenCalledWith('/api/health', expect.anything());
    expect(reload).not.toHaveBeenCalled();
  });

  it('⚡ tells the caller when the connection is back, rather than deciding itself', async () => {
    // ⛔ It does not route. What happens next belongs to whoever mounted it —
    // this screen has no idea where the customer was going.
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true }));
    const onRestored = vi.fn();

    render(<NoConnection onRestored={onRestored} />);
    await userEvent.click(screen.getByRole('button', { name: 'Check again' }));

    await waitFor(() => expect(onRestored).toHaveBeenCalledTimes(1));
  });

  it('⛔ a failed check does not report the connection restored', async () => {
    const onRestored = vi.fn();
    render(<NoConnection onRestored={onRestored} />);
    await userEvent.click(screen.getByRole('button', { name: 'Check again' }));
    await waitFor(() =>
      expect(screen.getByRole('button', { name: 'Check again' })).toBeEnabled(),
    );
    expect(onRestored).not.toHaveBeenCalled();
  });
});

describe('♿ platform scope announces assertively, and the ladder decides that', () => {
  it('⚡ this state ends the session, so it interrupts — once', () => {
    // 📁 `4.1.3`: only a state that ends the session announces assertively.
    // Derived from the scope by SystemState, never chosen here.
    const { container } = render(<NoConnection />);
    const state = container.querySelector('[data-scope="platform"]');
    expect(state).toHaveAttribute('aria-live', 'assertive');
    expect(state).toHaveAttribute('role', 'alert');
    expect(state).toHaveAttribute('data-state', 'no-internet');
  });
});
