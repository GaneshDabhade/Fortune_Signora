/**
 * **The region boundary, after the four surfaces converged** —
 * [TASK-1429](../../../docs/BACKLOG.md).
 *
 * ⚡ **Two of these cases are INHERITED rather than new.** They lived in
 * `tests/components/foundation.test.tsx` against
 * `components/feedback/error-boundary.tsx`, which this row retired — **a
 * contained failure with a retry, and a surfaced correlation id.** ⛔ **A test
 * deleted alongside its subject is a guarantee nobody notices leaving**, so
 * both are re-asserted here against the component that replaced it.
 *
 * 🔴 **And one is a defect the retired component had**: 📁 the row records it —
 * *"`error-boundary.tsx` — its own colours, an identifier that cannot be
 * copied, **no retry limit at all**."* **The boundary that replaced it stops
 * after three.**
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { MAX_ATTEMPTS, RegionBoundary } from '@/components/ui/region-boundary';
import { ApiError } from '@/lib/api/client';

/** Throws an `ApiError`, which is the only kind that carries an identifier. */
function Boom(): never {
  throw new ApiError(500, { code: 'internal', message: 'boom', correlation_id: 'corr-123' });
}

/** Throws something that never reached the API, so it has no identifier. */
function Bare(): never {
  throw new TypeError('undefined is not a function');
}

beforeEach(() => {
  // The boundary logs deliberately (`signora.region_failed`); React also logs
  // the caught error. Neither is the subject of these cases.
  vi.spyOn(console, 'error').mockImplementation(() => {});
});
afterEach(() => vi.restoreAllMocks());

describe('⚡ inherited from the retired boundary — both properties survive', () => {
  it('contains a render failure and offers a retry', () => {
    render(
      <RegionBoundary subject="your accounts">
        <Boom />
      </RegionBoundary>,
    );
    expect(screen.getByText(/Signora could not load your accounts/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Retry/ })).toBeInTheDocument();
  });

  it('🔴 surfaces the correlation id so support can find the request', () => {
    // ⛔ The single case most likely to be lost in a convergence: the retired
    // component printed `Reference: corr-123` and nothing about rendering
    // through the ladder implies the identifier comes with it. It had to be
    // threaded through StatedAbsence deliberately.
    render(
      <RegionBoundary subject="your accounts">
        <Boom />
      </RegionBoundary>,
    );
    expect(screen.getByText(/corr-123/)).toBeInTheDocument();
  });

  it('⚡ and it arrives COPYABLE, which the retired one was not', () => {
    render(
      <RegionBoundary subject="your accounts">
        <Boom />
      </RegionBoundary>,
    );
    expect(screen.getByRole('button', { name: /copy/i })).toBeInTheDocument();
  });
});

describe('⛔ an identifier is never invented', () => {
  it('a component that threw before reaching the API shows none', () => {
    /**
     * ⚠️ **A `TypeError` never produced a request**, so there is nothing for
     * support to look up. ⛔ **Printing the digest or a generated id would send
     * somebody searching logs for a request that was never made** — 📁 §10's
     * *"an incorrect attribution is worse than none, because it misdirects the
     * investigation."*
     */
    render(
      <RegionBoundary subject="your accounts">
        <Bare />
      </RegionBoundary>,
    );
    expect(screen.getByText(/Signora could not load your accounts/)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /copy/i })).not.toBeInTheDocument();
  });
});

describe('🔴 the retry budget the retired boundary did not have', () => {
  it('⛔ stops after three attempts and says so, rather than offering a fourth', async () => {
    // 📁 *"retries three times with backoff, then stops and hands the decision
    // to the person"* — and *"silent infinite retry is how a broken widget
    // becomes an unnoticed wrong number."* The retired component offered
    // `Try again` for ever.
    render(
      <RegionBoundary subject="your accounts">
        <Boom />
      </RegionBoundary>,
    );

    for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt += 1) {
      const retry = screen.getByRole('button', { name: `Retry — attempt ${attempt} of ${MAX_ATTEMPTS}` });
      await userEvent.click(retry);
    }

    expect(screen.queryByRole('button', { name: /Retry/ })).not.toBeInTheDocument();
    expect(screen.getByText(`Signora tried ${MAX_ATTEMPTS} times and stopped.`)).toBeInTheDocument();
  });
});

describe('📁 the reassurance is a prop, because the default can be false', () => {
  it('⚡ the default holds for a region inside a page', () => {
    render(
      <RegionBoundary subject="the pipeline trend">
        <Boom />
      </RegionBoundary>,
    );
    expect(
      screen.getByText(/Everything else on this page is unaffected/),
    ).toBeInTheDocument();
  });

  it('🔴 and the shell’s content region says what actually survived', () => {
    /**
     * ⛔ **"Signora could not load this page. Everything else on this page is
     * unaffected" contradicts itself inside one line.** ⚡ **When the content
     * region IS the page, what survives is the frame** — so the frame is what
     * the sentence names.
     */
    render(
      <RegionBoundary
        subject="this page"
        reassurance="The navigation and your organizations are unaffected"
      >
        <Boom />
      </RegionBoundary>,
    );
    const text = screen.getByText(/Signora could not load this page/).textContent ?? '';
    expect(text).toContain('The navigation and your organizations are unaffected');
    expect(text).not.toContain('Everything else on this page is unaffected');
  });
});

describe('♿ politeness comes from the scope, not from this component', () => {
  it('⛔ a region failure announces POLITELY — it must not interrupt', () => {
    // The retired boundary hardcoded `role="alert"`, so a failed sidebar
    // interrupted a screen reader mid-sentence. 📁 `4.1.3`: only a state that
    // ends the session announces assertively.
    const { container } = render(
      <RegionBoundary subject="your accounts">
        <Boom />
      </RegionBoundary>,
    );
    const state = container.querySelector('[data-scope="region"]');
    expect(state).toHaveAttribute('aria-live', 'polite');
    expect(state).toHaveAttribute('role', 'status');
  });
});
