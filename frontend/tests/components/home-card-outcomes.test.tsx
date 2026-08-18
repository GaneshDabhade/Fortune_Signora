/**
 * **State 08's page half, counted** — 📁 `Fortune Signora Home.dc.html`:
 *
 * > *"Failed cards render their own error inside their own footprint with a
 * > correlation ID. The composition never collapses. **If every card fails, the
 * > page states that and offers one retry for all.**"*
 *
 * ⚡ **Home's RULE lives in `home-route.test.tsx`; the COUNT lives here.** ⛔ Home
 * cannot see the cards' queries — 📁 §09's independence rule, *"no card waits for
 * a sibling"* — so a failure reports itself from the one component every failure
 * already goes through.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { CardFailure } from '@/components/home/card-failure';
import { CardOutcomesProvider, useCardOutcomes } from '@/components/home/card-outcomes';

/** Reads the registry back out, so a test can assert what Home would see. */
function Count() {
  const { failed } = useCardOutcomes();
  return <output data-testid="failed">{failed}</output>;
}

function Retry() {
  const { retryAll } = useCardOutcomes();
  return (
    <button type="button" onClick={retryAll}>
      Retry all
    </button>
  );
}

function failure(id: string, onRetry = () => {}) {
  return (
    <CardFailure
      key={id}
      title={`${id} could not be loaded`}
      description="Everything else on this page is current."
      error={new Error('down')}
      onRetry={onRetry}
      testId={id}
    />
  );
}

describe('🔴 a card that renders its failure is counted', () => {
  it('counts one failure', () => {
    render(
      <CardOutcomesProvider>
        <Count />
        {failure('needs-you-today')}
      </CardOutcomesProvider>,
    );

    expect(screen.getByTestId('failed')).toHaveTextContent('1');
  });

  it('counts each failing card once', () => {
    render(
      <CardOutcomesProvider>
        <Count />
        {failure('needs-you-today')}
        {failure('recents')}
        {failure('agent-queue')}
      </CardOutcomesProvider>,
    );

    expect(screen.getByTestId('failed')).toHaveTextContent('3');
  });

  /**
   * ⛔ **A card that stops failing must stop being counted**, or the page-level
   * line would survive the retry that fixed it — 📁 which is the opposite of
   * *"one retry for all"* meaning anything.
   */
  it('🔴 forgets a card once it recovers', () => {
    const { rerender } = render(
      <CardOutcomesProvider>
        <Count />
        {failure('recents')}
      </CardOutcomesProvider>,
    );
    expect(screen.getByTestId('failed')).toHaveTextContent('1');

    rerender(
      <CardOutcomesProvider>
        <Count />
      </CardOutcomesProvider>,
    );

    expect(screen.getByTestId('failed')).toHaveTextContent('0');
  });

  /**
   * ⚡ **Re-registering the same id replaces its retry rather than counting
   * twice.** ⛔ A card whose `refetch` identity changed between renders must not
   * inflate the count — which would make one failed card read as two and trip
   * the page-level line on a page that mostly works.
   */
  it('⛔ and does not double-count a card that re-renders', () => {
    const { rerender } = render(
      <CardOutcomesProvider>
        <Count />
        {failure('recents', () => {})}
      </CardOutcomesProvider>,
    );

    rerender(
      <CardOutcomesProvider>
        <Count />
        {failure('recents', () => {})}
      </CardOutcomesProvider>,
    );

    expect(screen.getByTestId('failed')).toHaveTextContent('1');
  });
});

describe('📁 "one retry for all" retries, it does not reload', () => {
  it("🔴 fires every failed card's own retry", async () => {
    const first = vi.fn();
    const second = vi.fn();

    render(
      <CardOutcomesProvider>
        <Retry />
        {failure('needs-you-today', first)}
        {failure('recents', second)}
      </CardOutcomesProvider>,
    );
    screen.getByRole('button', { name: 'Retry all' }).click();

    expect(first).toHaveBeenCalledTimes(1);
    expect(second).toHaveBeenCalledTimes(1);
  });
});

describe('⛔ the registry is optional', () => {
  /**
   * ⚡ **A card rendered outside Home must not throw for want of a provider it
   * has no reason to know about.** ⛔ And the default must not lie: with no
   * provider the count is zero, which is what a page that is not Home would do
   * with it anyway.
   */
  it('renders a failure with no provider at all', () => {
    render(failure('recents'));

    expect(screen.getByTestId('recents')).toBeVisible();
  });
});
