/**
 * **The breadcrumb, rendered** — [TASK-1408](../../../docs/BACKLOG.md), rule 6.
 *
 * ⚡ **The law is tested in `tests/unit/breadcrumb.test.ts`.** These are the
 * things only rendering can get wrong: what is a link, what is not, and what
 * happens to the segments the collapse hides.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { Breadcrumb } from '@/components/ui/breadcrumb';
import type { Crumb } from '@/lib/shell/breadcrumb';

const link = (label: string, href: string): Crumb => ({ label, kind: 'link', href });
const current = (label: string, tone?: Crumb['tone']): Crumb => ({
  label,
  kind: 'current',
  ...(tone === undefined ? {} : { tone }),
});

describe('📁 rule 6 — mandatory below the first level, absent at it', () => {
  it('renders nothing for a single segment', () => {
    const { container } = render(<Breadcrumb trail={[current('Accounts')]} />);
    expect(container).toBeEmptyDOMElement();
  });

  it('renders a labelled navigation landmark below it', () => {
    render(<Breadcrumb trail={[link('Accounts', '/accounts'), current('Vantage')]} />);
    expect(screen.getByRole('navigation', { name: 'Breadcrumb' })).toBeInTheDocument();
  });
});

describe('⛔ the page you are on is never a link', () => {
  it('marks it aria-current and gives it no href', () => {
    // ⚡ **A link to here is a control that does nothing** — §2's class.
    render(<Breadcrumb trail={[link('Accounts', '/accounts'), current('Vantage')]} />);
    const here = screen.getByText('Vantage').closest('[aria-current]');
    expect(here).toHaveAttribute('aria-current', 'page');
    expect(screen.queryByRole('link', { name: 'Vantage' })).not.toBeInTheDocument();
    // The parent still is one.
    expect(screen.getByRole('link', { name: 'Accounts' })).toHaveAttribute('href', '/accounts');
  });

  it('🔴 refuses a malformed trail loudly in development', () => {
    /**
     * ⛔ **Rendering it would draw a link to the current page.** **Loud here,
     * silent in production** — a caller's defect should stop the person who
     * can fix it, not the customer.
     */
    expect(() =>
      render(<Breadcrumb trail={[link('a', '/a'), link('b', '/b')]} />),
    ).toThrow(/exactly one `current`/);
  });
});

describe('🔴 the collapsed segment stays reachable', () => {
  it('⚡ renders the gap as a control, not as an ellipsis', () => {
    /**
     * ⛔ **A trail that silently drops levels cannot be navigated back up**,
     * which is the one thing a breadcrumb is for.
     */
    render(
      <Breadcrumb
        trail={[
          link('Reports', '/reports'),
          link('Funnel', '/reports/funnel'),
          link('Stage velocity', '/reports/velocity'),
          link('Cohorts', '/reports/cohorts'),
          current('Negotiation cohort'),
        ]}
      />,
    );
    expect(
      screen.getByRole('button', { name: 'Show hidden breadcrumb levels' }),
    ).toBeInTheDocument();
    // First and last two survive; the middle is what went.
    expect(screen.getByRole('link', { name: 'Reports' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Cohorts' })).toBeInTheDocument();
    expect(screen.queryByText('Funnel')).not.toBeInTheDocument();
  });
});

describe('⚠️ a crumb with no href is text, never a dead link', () => {
  it('📁 the cross-workspace root often has none', () => {
    render(
      <Breadcrumb
        trail={[
          { label: 'Vantage Logistics', kind: 'workspace' },
          link('Accounts', '/accounts'),
          current('Meridian Freight'),
        ]}
      />,
    );
    expect(screen.getByText('Vantage Logistics')).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'Vantage Logistics' })).not.toBeInTheDocument();
  });
});

describe('📁 the current record carries its status dot', () => {
  it('renders a tone dot only when the caller supplies one', () => {
    const { container: plain } = render(
      <Breadcrumb trail={[link('Deals', '/deals'), current('Vantage renewal')]} />,
    );
    expect(plain.querySelector('.bg-danger')).toBeNull();

    const { container: risky } = render(
      <Breadcrumb trail={[link('Deals', '/deals'), current('Vantage renewal', 'risk')]} />,
    );
    expect(risky.querySelector('.bg-danger')).not.toBeNull();
  });
});
