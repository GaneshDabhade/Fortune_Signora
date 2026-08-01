/**
 * Whether two sources agreed — `R3-01`.
 *
 * Fifteen of sixteen business events in the Playground rest on one provider,
 * and every one of them used to read *"Reported by coresignal"*. **A reader who
 * sees that four times stops reading the line**, then misses it on the one
 * account where two sources agree — which is the only place the line was doing
 * any work.
 *
 * The line now states absence rather than implying it, and these tests are
 * about the contrast surviving somebody who is skimming.
 */
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactElement } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { BusinessEventEvidence } from '@/lib/api/types';

const businessEvent = vi.hoisted(() => vi.fn());

vi.mock('@/lib/query/hooks', () => ({
  useBusinessEvent: businessEvent,
}));

import { EvidenceDrawer } from '@/components/intelligence/evidence';

const EVENT = 'aaaaaaaa-1111-4111-8111-111111111111';

function evidence(providers: string[]): BusinessEventEvidence {
  return {
    id: EVENT,
    type_key: 'headcount_growth',
    summary: 'Headcount in platform engineering grew over the quarter.',
    occurred_at: '2026-07-04T00:00:00Z',
    corroborating_providers: providers,
    observations: [],
  };
}

function withQuery(node: ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={client}>{node}</QueryClientProvider>;
}

function drawer(providers: string[]) {
  businessEvent.mockReturnValue({
    data: evidence(providers),
    isLoading: false,
    isError: false,
  });
  return render(
    withQuery(
      <EvidenceDrawer workspaceId="ws" eventId={EVENT} onClose={() => undefined} />,
    ),
  );
}

beforeEach(() => {
  businessEvent.mockReset();
});

describe('when only one source reported it', () => {
  it('says so, rather than reporting the source neutrally', () => {
    drawer(['coresignal']);

    // "Reported by coresignal" and "Only coresignal has reported this" are the
    // same fact and different claims. The second is the one a reader can act on.
    expect(screen.getByText(/Only coresignal has reported this/)).toBeVisible();
  });

  it('never reads as though corroboration existed', () => {
    const { container } = drawer(['coresignal']);

    expect(container.textContent).not.toContain('Reported by coresignal ·');
  });
});

describe('when two sources agreed', () => {
  it('names them both', () => {
    drawer(['apollo', 'coresignal']);

    expect(screen.getByText(/Reported by apollo and coresignal/)).toBeVisible();
  });

  it('is left unmarked — the contrast does the work', () => {
    // A badge on the rare case would be a second vocabulary for a distinction
    // the sentence already carries, and it would need a reader to have learned
    // it. The wording needs nobody to have learned anything.
    const { container } = drawer(['apollo', 'coresignal']);

    expect(container.querySelector('[class*="success"]')).toBeNull();
    expect(container.textContent).not.toMatch(/corroborat/i);
  });

  it('names three sources without inventing a summary', () => {
    drawer(['apollo', 'bombora', 'coresignal']);

    expect(screen.getByText(/apollo, bombora and coresignal/)).toBeVisible();
  });
});

describe('when nothing is on record', () => {
  it('says that, and does not guess', () => {
    drawer([]);

    // An event with no provider on record is a storage fault rather than an
    // ordinary state, and a sentence naming zero sources is the honest form
    // of it. Silence here would read as corroboration by omission.
    expect(screen.getByText(/No provider on record/)).toBeVisible();
  });
});
