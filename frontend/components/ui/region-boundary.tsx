'use client';

import { Component, type ErrorInfo, type ReactNode } from 'react';

import { StatedAbsence } from '@/components/feedback/stated-absence';
import { ApiError } from '@/lib/api/client';

/**
 * **The boundary every later workflow consumes** —
 * [TASK-1409](../../../docs/BACKLOG.md), restored by
 * [TASK-1428](../../../docs/BACKLOG.md).
 *
 * > 📁 ***"A region failure keeps its own footprint so the layout never
 * > jumps, states its cause in one sentence, retries three times with
 * > backoff, then stops and hands the decision to the person."***
 *
 * ## ⚡ Why this was deleted once and is back unchanged in substance
 *
 * ⚠️ **The first version wrote its own sentence** — *"X could not load"* —
 * **and [TASK-445](../../../docs/BACKLOG.md)'s guard failed it**, correctly:
 * `StatedAbsence` already owned that sentence across nine call sites.
 * ⛔ **Rewording to dodge the regex would have shipped the fork the guard
 * exists to prevent**, so the boundary was removed rather than disguised, and
 * [C-252](../../../docs/LANE_COORDINATION.md) asked whose the sentence was.
 *
 * ✅ **The ruling composed them instead of choosing.** **`StatedAbsence` owns
 * the sentence; the ladder owns the scope** — so this catches the throw and
 * says nothing of its own.
 *
 * ## 🔴 The property that matters
 *
 * ⚡ **A region failure now renders identically whether a read returned an
 * error or a component threw.** ⛔ **That divergence was the defect**: two
 * failures of the same thing, in the same place, looking like different
 * events.
 *
 * ## ⛔ It never escalates on its own
 *
 * 📁 **§01: *"escalating is a decision with a reason."*** **A boundary that
 * promoted itself to page scope after three failures would take the person's
 * filters and scroll position away for a widget** — the exact defect the
 * ladder was written to end. **After the third attempt it stops and says so.**
 */

/** 📁 *"retries three times with backoff, then stops"* — the design's number. */
export const MAX_ATTEMPTS = 3;

interface Props {
  children: ReactNode;
  /**
   * 📁 *"states its cause in one sentence"* — **in the customer's words and
   * lower case**, because it completes `StatedAbsence`'s sentence: *Signora
   * could not load __*. **"the pipeline trend"**, not **"Pipeline trend"**.
   */
  subject: string;
  /**
   * ⚠️ **What is still true, when the default would be FALSE** —
   * [TASK-1429](../../../docs/BACKLOG.md).
   *
   * ⛔ **Added because the default made the shell's content region lie.** The
   * boundary around `children` in
   * [`app-shell.tsx`](../shell/app-shell.tsx) would have read *"Signora could
   * not load this page. **Everything else on this page is unaffected**"* —
   * ⚡ **a sentence that contradicts itself inside one line**, and the thing
   * that actually survived is the frame around it.
   *
   * ✅ **Optional, and the default is unchanged**, so the nine callers that
   * sit inside a page keep the sentence they already had. **A prop rather
   * than a second boundary**: the shape, the retry budget and the escalation
   * refusal are identical, and only the true statement differs.
   */
  reassurance?: string;
}

interface State {
  error: Error | null;
  attempt: number;
}

export class RegionBoundary extends Component<Props, State> {
  override state: State = { error: null, attempt: 0 };

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { error };
  }

  override componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error('signora.region_failed', {
      subject: this.props.subject,
      message: error.message,
      componentStack: info.componentStack,
    });
  }

  private readonly retry = () => {
    this.setState((s) => ({ error: null, attempt: s.attempt + 1 }));
  };

  override render(): ReactNode {
    const { error, attempt } = this.state;
    if (error === null) return this.props.children;

    const exhausted = attempt >= MAX_ATTEMPTS;

    return (
      <div>
        {/* ⛔ **The sentence is `StatedAbsence`'s, not this file's.** */}
        {/* ⛔ **The identifier is carried, not dropped** —
            [TASK-1429](../../../docs/BACKLOG.md). The retired
            `components/feedback/error-boundary.tsx` printed
            `Reference: {correlationId}` and a test asserted it. ⚡ **It arrives
            COPYABLE here, which that one was not**, and only an `ApiError`
            has one: a component that threw a `TypeError` never reached the
            API, and inventing an identifier for it would send somebody
            looking for a request that was never made. */}
        <StatedAbsence
          subject={this.props.subject}
          reassurance={
            this.props.reassurance ?? 'Everything else on this page is unaffected'
          }
          {...(error instanceof ApiError ? { correlationId: error.correlationId } : {})}
        />
        {/* 📁 *"then stops and hands the decision to the person"* — ⛔ **the
            control disappears when it is spent.** **A button that cannot help
            is worse than none**, and 📁 *"silent infinite retry is how a
            broken widget becomes an unnoticed wrong number."* */}
        {exhausted ? (
          <p className="mt-2 text-2xs text-content-subtle">
            Signora tried {MAX_ATTEMPTS} times and stopped.
          </p>
        ) : (
          <button
            type="button"
            onClick={this.retry}
            className="mt-2 rounded border border-border-strong bg-surface px-3 py-1 text-sm font-medium text-content transition-colors hover:bg-surface-sunken focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          >
            Retry — attempt {attempt + 1} of {MAX_ATTEMPTS}
          </button>
        )}
      </div>
    );
  }
}
