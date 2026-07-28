'use client';

import { Component, type ErrorInfo, type ReactNode } from 'react';

import { Button } from '@/components/ui';
import { ApiError } from '@/lib/api/client';

interface Props {
  children: ReactNode;
  /** Names the region for the fallback copy, so a failed sidebar does not
   * claim the whole application is broken. */
  region?: string;
}

interface State {
  error: Error | null;
}

/**
 * Catches render errors so a thrown exception degrades one region instead
 * of blanking the page.
 *
 * A class component because React provides no hook equivalent — this is
 * the one place a class is still the only option.
 *
 * The fallback shows a `correlation_id` when the error carries one: it is
 * the single piece of information that turns "it broke" into a specific
 * request an engineer can find (16-logging, 19-api-conventions).
 */
export class ErrorBoundary extends Component<Props, State> {
  override state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  override componentDidCatch(error: Error, info: ErrorInfo): void {
    // Logged rather than swallowed. Sentry's React integration also picks
    // this up; the console line is what a developer sees locally.
    console.error('render error', {
      region: this.props.region ?? 'application',
      message: error.message,
      componentStack: info.componentStack,
    });
  }

  private readonly reset = () => this.setState({ error: null });

  override render(): ReactNode {
    const { error } = this.state;
    if (!error) return this.props.children;

    const correlationId = error instanceof ApiError ? error.correlationId : null;

    return (
      <div
        role="alert"
        className="flex flex-col items-center gap-3 rounded-lg border border-danger bg-danger-subtle px-6 py-8 text-center"
      >
        <div>
          <p className="text-sm font-semibold text-danger">
            {this.props.region
              ? `${this.props.region} failed to load`
              : 'Something went wrong'}
          </p>
          <p className="mt-1 text-sm text-content-muted">
            The error has been recorded. Retrying often resolves it.
          </p>
          {correlationId ? (
            <p className="mt-2 font-mono text-xs text-content-subtle">
              Reference: {correlationId}
            </p>
          ) : null}
        </div>
        <Button variant="secondary" size="sm" onClick={this.reset}>
          Try again
        </Button>
      </div>
    );
  }
}
