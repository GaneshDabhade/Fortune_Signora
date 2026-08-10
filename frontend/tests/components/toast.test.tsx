import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { existsSync } from 'node:fs';
import { join } from 'node:path';
import { act } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { ToastProvider, UNDO_DISMISS_MS, kindOf, useToast } from '@/components/ui';
import type { Toast } from '@/components/ui';

/**
 * **Toast's three kinds** — [TASK-1449](../../../docs/BACKLOG.md), against 📁
 * Design System v2 `toasts`.
 *
 * > 📁 **Shell rule 11**: *"Toasts confirm background outcomes only, never
 * > required reading."*
 */

function Raise({ toast: input }: { toast: Omit<Toast, 'id'> }) {
  const { toast } = useToast();
  return (
    <button type="button" onClick={() => toast(input)}>
      raise
    </button>
  );
}

async function raise(input: Omit<Toast, 'id'>) {
  render(
    <ToastProvider>
      <Raise toast={input} />
    </ToastProvider>,
  );
  await userEvent.click(screen.getByRole('button', { name: 'raise' }));
}

afterEach(() => vi.useRealTimers());

describe('📁 it lives in the library now', () => {
  it('⛔ and nothing is left behind at the old path', () => {
    // ⚡ **A move that leaves the original is not a move** — it is a second
    // copy, and the two diverge the first time either is touched.
    expect(existsSync(join(process.cwd(), 'components', 'feedback', 'toast.tsx'))).toBe(false);
    expect(existsSync(join(process.cwd(), 'components', 'ui', 'toast.tsx'))).toBe(true);
  });
});

describe('🔴 the dismissal rule, which is per kind', () => {
  it('⛔ a FAILURE stays until dismissed', async () => {
    /**
     * 📁 The design writes the rule into the copy itself: *"8,400 synced.
     * **This stays until dismissed**."* ⚡ **Auto-dismissing a failure the
     * person has not read is how a failed action becomes an unexplained one**
     * — and it is the failure that carries the correlation id support needs.
     */
    vi.useFakeTimers({ shouldAdvanceTime: true });
    await raise({ kind: 'failure', message: 'Sync failed for 12 accounts' });
    expect(screen.getByText('Sync failed for 12 accounts')).toBeInTheDocument();

    act(() => void vi.advanceTimersByTime(UNDO_DISMISS_MS * 3));
    expect(screen.getByText('Sync failed for 12 accounts')).toBeInTheDocument();
  });

  it('✅ an UNDO gets the design\'s ten seconds, not the ordinary six', async () => {
    /**
     * 🔴 **[TASK-1452](../../../docs/BACKLOG.md) needed exactly this and could
     * not have it**: the table's inline editing must *"surface undo in the
     * toast for 10 seconds"*, and this component had **no action and a 6000ms
     * dismissal**. ⚡ **Ten seconds is the only window in which somebody can
     * change their mind**, which is why it is longer than a confirmation.
     */
    vi.useFakeTimers({ shouldAdvanceTime: true });
    await raise({ kind: 'undo', message: 'Close date updated' });

    act(() => void vi.advanceTimersByTime(7_000));
    expect(screen.getByText('Close date updated'), 'gone before ten seconds').toBeInTheDocument();

    act(() => void vi.advanceTimersByTime(UNDO_DISMISS_MS));
    expect(screen.queryByText('Close date updated')).toBeNull();
  });

  it('✅ a SUCCESS dismisses on its own', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    await raise({ kind: 'success', message: 'Export ready — 8,412 rows' });
    act(() => void vi.advanceTimersByTime(UNDO_DISMISS_MS));
    expect(screen.queryByText('Export ready — 8,412 rows')).toBeNull();
  });
});

describe('📁 the action every kind carries', () => {
  it('✅ it fires, and dismisses so the outcome is not dismissed twice', async () => {
    const onAction = vi.fn();
    await raise({
      kind: 'undo',
      message: 'Close date updated',
      action: { label: 'Undo', onAction },
    });

    await userEvent.click(screen.getByRole('button', { name: 'Undo' }));
    expect(onAction).toHaveBeenCalled();
    expect(screen.queryByText('Close date updated')).toBeNull();
  });

  it('⛔ no action, no control — a button that does nothing is worse than none', async () => {
    await raise({ kind: 'success', message: 'Saved' });
    expect(screen.queryByRole('button', { name: 'Undo' })).toBeNull();
    // The dismiss control is not an action and is always there.
    expect(screen.getByRole('button', { name: 'Dismiss notification' })).toBeInTheDocument();
  });
});

describe('⚡ the old vocabulary still resolves, so no caller was rewritten in this row', () => {
  it('✅ error means failure, and success means success', () => {
    // ⛔ **Measured before aliasing**: every `toast()` call in the product
    // passes `success` or `error`. `info` had a type and no caller.
    expect(kindOf({ tone: 'error' })).toBe('failure');
    expect(kindOf({ tone: 'success' })).toBe('success');
    expect(kindOf({ kind: 'undo', tone: 'success' })).toBe('undo');
  });

  it('⛔ and an error raised the old way still stays until dismissed', async () => {
    // ⚡ **The behaviour callers depend on is unchanged**, which is what makes
    // this a move rather than a rewrite of eight files.
    vi.useFakeTimers({ shouldAdvanceTime: true });
    await raise({ tone: 'error', message: 'Could not save' });
    act(() => void vi.advanceTimersByTime(UNDO_DISMISS_MS * 3));
    expect(screen.getByText('Could not save')).toBeInTheDocument();
  });
});
