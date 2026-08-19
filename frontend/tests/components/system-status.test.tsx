/**
 * **The status pill** — [TASK-1484](../../../docs/BACKLOG.md) ⓑ, against 📁
 * `Fortune Signora App Shell.dc.html` **§07**.
 *
 * > 📁 ***"System status is a persistent pill in the top bar rather than a
 * > banner — degradation is a fact about the product, not an interruption, and
 * > it expands into detail on click."***
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { Readiness } from '@/lib/query/hooks/readiness';

const readiness = vi.hoisted(() => vi.fn());
vi.mock('@/lib/query/hooks/readiness', async () => {
  const actual = await vi.importActual<Record<string, unknown>>('@/lib/query/hooks/readiness');
  return { ...actual, useReadiness: readiness };
});

const { SystemStatus } = await import('@/components/ui/system-status');

function ready(over: Partial<Readiness> = {}): Readiness {
  return {
    status: 'ready',
    database: 'ok',
    authentication: 'ok',
    authentication_detail: null,
    ...over,
  };
}

function at(width: number) {
  Object.defineProperty(window, 'innerWidth', { value: width, configurable: true });
}

beforeEach(() => {
  at(1440);
  readiness.mockReturnValue({ data: ready() });
});

describe('⛔ it says nothing until it knows something', () => {
  /**
   * 🔴 **A pill that said *degraded* because a read had not returned would
   * report an outage on every cold load.** ⚡ Same rule as 📁
   * [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md) for an empty result, and
   * the same mistake 🔴 [B-290](../../../docs/BUGS.md) cost one surface over.
   */
  it('renders nothing while the read is in flight', () => {
    readiness.mockReturnValue({ data: undefined });

    const { container } = render(<SystemStatus />);

    expect(container).toBeEmptyDOMElement();
  });

  /**
   * ⚠️ **A failed READ is a different fact from a degraded PRODUCT.** 📁
   * `offline-status.tsx` already owns *"you cannot reach anything"*, and two
   * pills saying it would be two answers to one question.
   */
  it('⛔ and renders nothing when the read itself failed', () => {
    readiness.mockReturnValue({ data: undefined, isError: true });

    const { container } = render(<SystemStatus />);

    expect(container).toBeEmptyDOMElement();
  });
});

describe('📁 the three tones, and what each says', () => {
  it('✅ healthy', () => {
    render(<SystemStatus />);

    expect(screen.getByTestId('system-status')).toHaveAttribute('data-status', 'healthy');
    expect(screen.getByRole('button', { name: 'All systems normal' })).toBeVisible();
  });

  it('⚠️ degraded, when the product says it is', () => {
    readiness.mockReturnValue({
      data: ready({ status: 'degraded', authentication: 'degraded' }),
    });

    render(<SystemStatus />);

    expect(screen.getByTestId('system-status')).toHaveAttribute('data-status', 'degraded');
    expect(screen.getByRole('button', { name: 'Partial degradation' })).toBeVisible();
  });

  /**
   * 🔴 **`unavailable` outranks `degraded`.** ⛔ A dependency that is gone and
   * one that is slow are not the same news, and reporting the milder of the two
   * is the failure this criterion exists to prevent.
   */
  it('🔴 down, when a dependency is unavailable', () => {
    readiness.mockReturnValue({
      data: ready({ status: 'degraded', database: 'unavailable' }),
    });

    render(<SystemStatus />);

    expect(screen.getByTestId('system-status')).toHaveAttribute('data-status', 'down');
    expect(screen.getByRole('button', { name: 'Service unavailable' })).toBeVisible();
  });
});

describe('📁 "green shows a dot only below 1280px; amber and red always keep their label"', () => {
  it('⛔ a healthy pill drops its label below 1280', () => {
    at(1279);

    render(<SystemStatus />);

    expect(screen.queryByText('All systems normal')).not.toBeInTheDocument();
    // ♿ **The name never hides.** 📁 The rule is about pixels and never about
    // who is told.
    expect(screen.getByRole('button', { name: 'All systems normal' })).toBeVisible();
  });

  it('✅ and a degraded one keeps it, at any width', () => {
    at(1279);
    readiness.mockReturnValue({ data: ready({ status: 'degraded', authentication: 'degraded' }) });

    render(<SystemStatus />);

    expect(screen.getByText('Partial degradation')).toBeVisible();
  });
});

describe('📁 "it expands into detail on click"', () => {
  it('✅ lists a row per service the payload reports, and no others', async () => {
    readiness.mockReturnValue({
      data: ready({
        status: 'degraded',
        authentication: 'degraded',
        authentication_detail: 'the signing key is more than 90 days old',
      }),
    });

    render(<SystemStatus />);
    await userEvent.click(screen.getByRole('button', { name: 'Partial degradation' }));

    const panel = screen.getByTestId('system-status-detail');
    expect(panel).toBeVisible();
    expect(screen.getByText('Database')).toBeVisible();
    expect(screen.getByText('Normal')).toBeVisible();
    expect(screen.getByText('Authentication')).toBeVisible();
    expect(screen.getByText('Degraded')).toBeVisible();
    // ⚡ **The API's own sentence** — 📁 paraphrasing it here would be a second
    // vocabulary for one fact.
    expect(screen.getByText(/signing key is more than 90 days old/)).toBeVisible();
  });

  /**
   * 📁 **The design draws five subsystems** — Application, CRM sync, Scoring
   * service, Conversation ingest, Exports — ⛔ **and `GET /ready` reports two.**
   * 📁 TASK-1484: *"do not invent a service the `/ready` payload does not
   * report."*
   */
  it('⛔ and invents none of the three the design draws and nothing publishes', async () => {
    render(<SystemStatus />);
    await userEvent.click(screen.getByRole('button', { name: 'All systems normal' }));

    for (const invented of ['CRM sync', 'Scoring service', 'Conversation ingest', 'Exports']) {
      expect(screen.queryByText(new RegExp(invented))).not.toBeInTheDocument();
    }
    expect(screen.getAllByRole('listitem')).toHaveLength(2);
  });

  /**
   * ⛔ **No status page, no incident feed, no history, no subscription.** 📁 The
   * row forbids each by name, and every one is a promise about something the
   * product does not operate.
   */
  it('⛔ offers nothing the product does not operate', async () => {
    render(<SystemStatus />);
    await userEvent.click(screen.getByRole('button', { name: 'All systems normal' }));

    expect(screen.queryByRole('link')).not.toBeInTheDocument();
    expect(screen.queryByText(/status page/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/subscribe/i)).not.toBeInTheDocument();
  });

  /**
   * ⚠️ **NOT the design's *"Updated 2m ago"*.** ⚡ The pill re-reads on a fixed
   * interval, and a relative time nothing recomputes is the one thing on this
   * panel that could lie.
   */
  it('⚡ says the interval rather than a relative time nothing recomputes', async () => {
    render(<SystemStatus />);
    await userEvent.click(screen.getByRole('button', { name: 'All systems normal' }));

    expect(screen.getByText('Checked every 30s')).toBeVisible();
    expect(screen.queryByText(/ago$/)).not.toBeInTheDocument();
  });
});
