/**
 * **The scope ladder, rendered** — [TASK-1409](../../../docs/BACKLOG.md).
 *
 * ⚡ **The property worth protecting is the refusal.** Anybody can render a
 * `404`; the thing that makes this a ladder rather than four screens is that
 * a `500` cannot be drawn inside a region, and a `region-error` cannot take
 * the page.
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { SystemState } from '@/components/ui';
import { LEGAL_STATES, SCOPES, type Scope } from '@/lib/system-states/ladder';

describe('each scope renders its own legal states', () => {
  it('⚡ every legal (scope, state) pair renders', () => {
    for (const scope of SCOPES) {
      for (const state of LEGAL_STATES[scope]) {
        const { unmount } = render(
          <SystemState scope={scope} state={state} title="It happened" description="And this is why." />,
        );
        expect(screen.getByText('It happened')).toBeInTheDocument();
        unmount();
      }
    }
  });

  it('🔴 refuses every illegal pair — the ladder, enforced', () => {
    /**
     * ⛔ **A throw rather than a fallback.** A silent downgrade renders
     * something plausible and ships the mistake, and the mistake is the one
     * the ladder exists to prevent.
     */
    const illegal: [Scope, string][] = [
      ['region', '500'],
      ['region', '404'],
      ['app', 'empty-result'],
      ['page', 'maintenance'],
      ['platform', 'retry'],
    ];
    for (const [scope, state] of illegal) {
      expect(() =>
        render(
          // @ts-expect-error — the pair is illegal, which is the point: the
          // type refuses it at compile time and the component at run time.
          <SystemState scope={scope} state={state} title="t" description="d" />,
        ),
      ).toThrow(/cannot render at/);
    }
  });
});

describe('📁 the grammar', () => {
  it('⛔ never renders the status code as a numeral', () => {
    // 📁 *"a 404 with a giant `404` tells you what a machine knows, not what
    // you need."* The state name is data, never copy.
    const { container } = render(
      <SystemState
        scope="page"
        state="404"
        title="This account no longer exists"
        description="It was merged on 22 July."
      />,
    );
    expect(container.textContent).not.toMatch(/\b404\b/);
    expect(screen.getByRole('heading', { name: /This account no longer exists/ })).toBeInTheDocument();
  });

  it('⚡ severity comes from the state, so absence and failure differ at one scope', () => {
    const { container: absent } = render(
      <SystemState scope="page" state="404" title="Gone" description="d" />,
    );
    const { container: broke } = render(
      <SystemState scope="app" state="500" title="Failed" description="d" />,
    );
    expect(absent.firstElementChild).toHaveAttribute('data-severity', 'neutral');
    expect(broke.firstElementChild).toHaveAttribute('data-severity', 'risk');
  });

  it('🔴 the identifier is copyable, not merely printed', async () => {
    // 📁 *"the single thing that makes a support conversation short."* ⛔ An
    // id that must be retyped reaches support with a transposed character.
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });

    render(
      <SystemState
        scope="app"
        state="500"
        title="Something failed on our side"
        description="Not your data and not your configuration."
        correlationId="req_2e88"
      />,
    );
    await userEvent.click(screen.getByRole('button', { name: /req_2e88/ }));
    expect(writeText).toHaveBeenCalledWith('req_2e88');
    expect(screen.getByText('Copied')).toBeInTheDocument();
  });
});

describe('♿ focus and announcement are decided by scope, never by the caller', () => {
  it('📁 2.4.3 — a page-level state is an h1 and takes focus; a region one does not', () => {
    const { unmount } = render(
      <SystemState scope="page" state="404" title="Gone" description="d" />,
    );
    expect(screen.getByRole('heading', { level: 1, name: 'Gone' })).toHaveAttribute('tabindex', '-1');
    unmount();

    render(<SystemState scope="region" state="region-error" title="Score unavailable" description="d" />);
    // ⛔ **Not a heading at all** — a region failure must not steal the
    // document outline any more than it steals focus.
    expect(screen.queryByRole('heading', { name: 'Score unavailable' })).not.toBeInTheDocument();
  });

  it('📁 4.1.3 — only a state that ends the session announces assertively', () => {
    const { container: region } = render(
      <SystemState scope="region" state="region-error" title="t" description="d" />,
    );
    expect(region.firstElementChild).toHaveAttribute('role', 'status');
    expect(region.firstElementChild).toHaveAttribute('aria-live', 'polite');

    const { container: app } = render(<SystemState scope="app" state="500" title="t" description="d" />);
    expect(app.firstElementChild).toHaveAttribute('role', 'alert');
    expect(app.firstElementChild).toHaveAttribute('aria-live', 'assertive');
  });
});
