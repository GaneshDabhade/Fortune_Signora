import { render, screen } from '@testing-library/react';
import { useState } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import userEvent from '@testing-library/user-event';

import { LoadingRegion, Skeleton, SkeletonText } from '@/components/ui';

/**
 * 🔴 **[B-1057](../../../docs/BUGS.md) — a loading state conveyed visually only.**
 *
 * ⛔ **QE held a read open for 12 seconds and sampled mid-flight**: three
 * skeletons, correctly `aria-hidden`, **`aria-busy` nowhere in the document,
 * both `aria-live` regions empty, and the word *loading* absent.** 📁 **WCAG 2.2
 * SC 4.1.3 *Status Messages*** — a status that does not take focus must be
 * programmatically determinable.
 *
 * ⚠️ **The row's own note on method, and it is the reason this file exists:**
 * ***"a test against a settled page cannot see this state at all, which is why
 * it survived to now."*** ✅ **So every assertion here is taken while the read
 * is still in flight**, by holding `busy` true rather than by waiting for it.
 */
describe('♿ a read in flight says so', () => {
  it('⛔ the skeletons stay hidden and something else does the talking', async () => {
    render(
      <LoadingRegion label="the signal queue" busy>
        <div aria-hidden data-testid="placeholders">
          <Skeleton className="h-16" />
        </div>
      </LoadingRegion>,
    );

    // ✅ **`aria-hidden` is RIGHT and is not the defect** — 📁 the row is
    // explicit that three pulsing rectangles are not a status message.
    expect(screen.getByTestId('placeholders')).toHaveAttribute('aria-hidden', 'true');

    expect(await screen.findByText('Loading the signal queue…')).toBeInTheDocument();
    expect(screen.getByRole('status')).toHaveTextContent('Loading the signal queue…');
  });

  it('⛔ the region being replaced carries aria-busy, and loses it on settle', async () => {
    function Harness() {
      const [busy, setBusy] = useState(true);
      return (
        <>
          <button type="button" onClick={() => setBusy(false)}>
            settle
          </button>
          <LoadingRegion label="the queue" busy={busy}>
            <p data-testid="body">{busy ? 'placeholder' : 'the real thing'}</p>
          </LoadingRegion>
        </>
      );
    }
    render(<Harness />);

    const region = screen.getByTestId('body').parentElement;
    expect(region).toHaveAttribute('aria-busy', 'true');

    await userEvent.click(screen.getByRole('button', { name: 'settle' }));

    // ⚡ **Absent, not `"false"`** — a settled page should carry no attribute
    // rather than one asserting nothing.
    expect(region).not.toHaveAttribute('aria-busy');
    expect(await screen.findByText('the queue loaded.')).toBeInTheDocument();
  });

  /**
   * ⚠️ 📁 The row: ***"once on entry and once on settle, not on every
   * re-render."***
   */
  it('⛔ says nothing at all when a read never waited', () => {
    render(
      <LoadingRegion label="the queue" busy={false}>
        <p>the real thing</p>
      </LoadingRegion>,
    );
    expect(screen.getByRole('status')).toHaveTextContent('');
  });

  /**
   * 📁 **Sixteen of seventeen route-level `loading.tsx` files are exactly
   * this**, so the announcement lives here rather than at thirty-seven call
   * sites.
   */
  it('♿ a route fallback announces its own wait', async () => {
    render(<SkeletonText lines={5} label="your companies" />);
    expect(await screen.findByText('Loading your companies…')).toBeInTheDocument();
    expect(screen.getByRole('status').parentElement).toHaveAttribute('aria-busy', 'true');
  });

  it('⚡ and an unlabelled one still says something rather than nothing', async () => {
    render(<SkeletonText lines={3} />);
    // 📁 SC 4.1.3's own textbook example.
    expect(await screen.findByText('Loading…')).toBeInTheDocument();
  });

  /**
   * ♿ **The pitfall this would otherwise walk into**: a live region whose text
   * is present on the same paint as the region is a status change that never
   * happened, and screen readers differ on whether they announce it.
   */
  it('⛔ the region mounts empty and the sentence arrives after', () => {
    // ⚡ **Rendered WITHOUT effects**, which is the only way to observe the
    // first paint. ⛔ **If the sentence were present here**, the region and its
    // text would arrive together and the status change would never occur.
    const first = renderToStaticMarkup(<SkeletonText lines={2} label="the queue" />);
    expect(first).toContain('<output');
    expect(first).not.toContain('Loading the queue');
  });
});
