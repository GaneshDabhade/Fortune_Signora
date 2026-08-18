/**
 * 📁 **Home's state 08** — *"inside the card's own footprint, DASHED border so
 * it is distinguishable from content. The layout does not move and no sibling
 * is affected."*
 *
 * 🔴 **Eight cards said this eight ways before this panel existed.** The copy
 * was right each time; the treatment was not.
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { CardFailure } from '@/components/home/card-failure';
import { ApiError } from '@/lib/api/client';

function failure(overrides: Partial<React.ComponentProps<typeof CardFailure>> = {}) {
  return (
    <CardFailure
      title="Your briefing could not be generated"
      description="Everything else on this page is unaffected."
      error={null}
      onRetry={() => {}}
      {...overrides}
    />
  );
}

describe('📁 the failure is distinguishable from content', () => {
  it('⛔ draws a DASHED border, which is the design\'s own distinction', () => {
    const { container } = render(failure());

    expect(container.querySelector('[data-state="region-error"]')).toHaveClass('border-dashed');
  });

  it('✅ claims the region, never the page', () => {
    /**
     * 📁 The ladder refuses an illegal pairing rather than downgrading it:
     * *"`500` rendered at region scope claims the page survived when it did
     * not."* ⚡ Here the same rule runs the other way — one card failing must
     * not claim the page.
     */
    const { container } = render(failure());

    expect(container.querySelector('[data-scope="region"]')).toBeInTheDocument();
  });

  it('⛔ announces POLITELY — a card is not an outage', () => {
    // 📁 `4.1.3`: only a state that ends the session announces assertively.
    render(failure());

    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });
});

describe('🔴 the identifier is the thing that makes a support conversation short', () => {
  it('✅ renders the correlation ID the response carried', () => {
    render(failure({ error: new ApiError(500, {
      code: 'internal_error',
      message: 'boom',
      correlation_id: 'req_7c14-9de2',
    }) }));

    expect(screen.getByText('req_7c14-9de2')).toBeInTheDocument();
  });

  it('⛔ renders NO identifier when the failure carried none', () => {
    /**
     * ⚠️ **An empty reference is worse than none** — support would search for
     * it. A network failure that never reached the server has no id to show.
     */
    render(failure({ error: new Error('the network went away') }));

    expect(screen.queryByText(/req_/)).not.toBeInTheDocument();
  });
});

describe('⚡ Retry is a retry, not a reload', () => {
  it('✅ calls the failed query back', async () => {
    const onRetry = vi.fn();
    render(failure({ onRetry }));

    await userEvent.click(screen.getByRole('button', { name: 'Retry' }));

    expect(onRetry).toHaveBeenCalledOnce();
  });

  it('⛔ cannot be pressed twice while it is running', () => {
    // 📁 `Button`'s own rule: a caller cannot express "busy but clickable",
    // which is the state that produces duplicate submissions.
    render(failure({ retrying: true }));

    expect(screen.getByRole('button', { name: 'Retry' })).toBeDisabled();
  });
});
