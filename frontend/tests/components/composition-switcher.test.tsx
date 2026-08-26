/**
 * 🔴 **A failed composition switch was silent** — the third instance recorded
 * in [C-1562](../../../docs/LANE_COORDINATION.md), filed there because Lane A's
 * `B-` block is exhausted at 100/100.
 *
 * 📁 **Notification Center's `deliveryRules` ⑧**: ***"A failed write reverts
 * the control and says so — a preference that silently did not save is worse
 * than one that refused."***
 *
 * ⚡ **The control DID revert.** It renders `current`, which only moves when the
 * server confirms — **so the first half of the rule held all along.** ⛔ **The
 * second did not**: a reader clicked *Executive*, the button re-enabled, the
 * selection stayed put, and **nothing said why.**
 *
 * ⚠️ **The wording is the product's own**, from the four profile panels that
 * already implement this rule — ⛔ a third phrasing of *it did not save* would
 * be the two-representations defect in copy.
 */
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import type { ReactElement } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const apiRequest = vi.hoisted(() => vi.fn());
vi.mock('@/lib/api/client', () => ({ apiRequest }));

import { CompositionSwitcher } from '@/components/home/composition-switcher';

const WORKSPACE = '11111111-1111-4111-8111-111111111111';

function mount(node: ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(<QueryClientProvider client={client}>{node}</QueryClientProvider>);
}

function switcher() {
  return mount(
    <CompositionSwitcher current="seller" statedRole="executive" workspaceId={WORKSPACE} />,
  );
}

beforeEach(() => {
  apiRequest.mockReset();
});

describe('🔴 a preference that did not save says so', () => {
  it('⛔ renders an alert when the write fails', async () => {
    apiRequest.mockRejectedValue(new Error('nope'));
    switcher();

    fireEvent.click(screen.getByRole('radio', { name: /executive/i }));

    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent(/did not save/i),
    );
  });

  /**
   * ✅ **The control reverts, which is the rule's first half** — and it holds
   * because the selection is `current`, never local state. ⛔ **A switcher that
   * moved optimistically and failed would show a composition the reader is not
   * looking at.**
   */
  it('✅ and the selection stays where the server left it', async () => {
    apiRequest.mockRejectedValue(new Error('nope'));
    switcher();

    fireEvent.click(screen.getByRole('radio', { name: /executive/i }));

    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument());
    expect(screen.getByRole('radio', { name: /seller/i })).toHaveAttribute(
      'aria-checked',
      'true',
    );
  });

  /**
   * ⚠️ **The half that stops this becoming an unconditional banner.** ⛔ A
   * component that always rendered the alert would satisfy the first assertion
   * on any implementation at all.
   */
  it('⚠️ and a healthy switcher shows no alert', () => {
    apiRequest.mockResolvedValue({ home_composition: 'executive' });
    switcher();

    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  /** ⚡ **Vacuity guard** — the radios are really there to be clicked. */
  it('⚡ vacuity guard — both compositions render as radios', () => {
    apiRequest.mockResolvedValue({});
    switcher();

    expect(screen.getAllByRole('radio').length).toBeGreaterThanOrEqual(2);
  });
});
