/**
 * The two pages a customer sees when something has gone wrong.
 *
 * **Both were Next.js's defaults until now.** A bad address produced a bare
 * *"404 | This page could not be found"* — no product, no theme, no way back —
 * and a render error outside the authenticated shell blanked the application,
 * because `ErrorBoundary` wraps three regions *inside* the shell and the
 * `(auth)` group has none.
 *
 * **These assert what the pages promise a customer**, not how they are built:
 * that neither invents a cause it does not know, that both offer a way out,
 * and that a failure carrying a correlation id shows it — the one piece of
 * information that turns *"it broke"* into a request an engineer can find.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import AppError from '@/app/error';
import NotFound from '@/app/not-found';
import { ApiError } from '@/lib/api/client';

describe('an address that does not lead anywhere', () => {
  it('says so in words a customer would use', () => {
    render(<NotFound />);

    expect(
      screen.getByRole('heading', { name: 'That address does not lead anywhere' }),
    ).toBeVisible();
  });

  it('offers the way back', () => {
    render(<NotFound />);

    expect(screen.getByRole('link', { name: 'Back to Signora' })).toHaveAttribute(
      'href',
      '/',
    );
  });

  it('never claims a cause the router does not know', () => {
    // The router knows only that nothing is registered here. "Deleted" and
    // "no access" are both inventions, and the second is the expensive one:
    // it sends a customer to an administrator for something they already have.
    const { container } = render(<NotFound />);
    const text = (container.textContent ?? '').toLowerCase();

    expect(text).not.toContain('deleted');
    expect(text).not.toContain('permission');
    expect(text).not.toContain('access');
    expect(text).not.toContain('forbidden');
  });

  it('reassures that nothing about the customer’s data changed', () => {
    render(<NotFound />);

    expect(screen.getByText(/nothing about your accounts has\s+changed/i)).toBeVisible();
  });
});

describe('a render that failed outside the shell', () => {
  const reset = () => {};

  it('says what broke, and what did not', () => {
    render(<AppError error={new Error('boom')} reset={reset} />);

    expect(screen.getByRole('heading', { name: 'Something went wrong' })).toBeVisible();
    expect(screen.getByText(/the failure is in displaying/i)).toBeVisible();
  });

  it('offers a retry that does not cost the customer their place', () => {
    const retry = vi.fn();
    render(<AppError error={new Error('boom')} reset={retry} />);

    fireEvent.click(screen.getByRole('button', { name: 'Try again' }));
    expect(retry).toHaveBeenCalledOnce();
  });

  it('shows the correlation id when the failure carries one', () => {
    const error = new ApiError(500, {
      code: 'internal_error',
      message: 'no',
      correlation_id: 'corr-12345',
    });

    render(<AppError error={error} reset={reset} />);

    expect(screen.getByText(/corr-12345/)).toBeVisible();
  });

  it('falls back to the digest when there is no correlation id', () => {
    // A server-side render failure has no API response, so no correlation id
    // — Next supplies a digest instead, and it is the only handle support has.
    const error = Object.assign(new Error('boom'), { digest: 'dig-987' });

    render(<AppError error={error} reset={reset} />);

    expect(screen.getByText(/dig-987/)).toBeVisible();
  });

  it('offers no reference rather than an empty one', () => {
    const { container } = render(<AppError error={new Error('boom')} reset={reset} />);

    expect(container.textContent).not.toContain('Reference:');
  });
});
