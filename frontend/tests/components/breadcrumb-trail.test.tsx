/**
 * **The breadcrumb reaches the slot the design names** — against 📁
 * `Fortune Signora App Shell.dc.html` **§04** and **§05**.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import {
  BreadcrumbTrailProvider,
  useBreadcrumbTrail,
  usePublishBreadcrumb,
} from '@/components/shell/breadcrumb-trail';
import type { Crumb } from '@/lib/shell/breadcrumb';

function Slot() {
  const trail = useBreadcrumbTrail();
  return <div data-testid="slot">{trail.map((c) => c.label).join(' / ')}</div>;
}

function Screen({ trail }: { trail: readonly Crumb[] }) {
  usePublishBreadcrumb(trail);
  return null;
}

const COMPANIES: readonly Crumb[] = [
  { label: 'Accounts', kind: 'link', href: '/accounts' },
  { label: 'Companies', kind: 'current' },
];
const ACCOUNT: readonly Crumb[] = [
  { label: 'Accounts', kind: 'link', href: '/accounts' },
  { label: 'Arvely Payments', kind: 'current' },
];

describe('📁 §04 — the screen states where it sits and the shell draws it', () => {
  it('✅ a published trail reaches the slot', () => {
    render(
      <BreadcrumbTrailProvider>
        <Slot />
        <Screen trail={COMPANIES} />
      </BreadcrumbTrailProvider>,
    );

    expect(screen.getByTestId('slot')).toHaveTextContent('Accounts / Companies');
  });

  /**
   * ⛔ **A trail must never outlive the screen that owns it** — ⚠️ a stale
   * crumb tells somebody they are somewhere they have left.
   */
  it('⛔ and is withdrawn when that screen goes', () => {
    const { rerender } = render(
      <BreadcrumbTrailProvider>
        <Slot />
        <Screen trail={COMPANIES} />
      </BreadcrumbTrailProvider>,
    );
    expect(screen.getByTestId('slot')).toHaveTextContent('Accounts / Companies');

    rerender(
      <BreadcrumbTrailProvider>
        <Slot />
      </BreadcrumbTrailProvider>,
    );

    expect(screen.getByTestId('slot')).toBeEmptyDOMElement();
  });

  /**
   * 🔴 **The defect this guard exists for, and it was MEASURED rather than
   * anticipated.**
   *
   * ⚠️ **Clicking a row on `/accounts` left the slot empty**, while loading the
   * same URL directly filled it. **React mounts the incoming tree before
   * unmounting the outgoing one during a client-side transition**, so the order
   * was `publish(new)` → `withdraw()` → nothing.
   *
   * ⛔ **An unguarded cleanup is therefore a stale writer**, and this is the
   * ordinary last-writer-wins fix.
   */
  it('🔴 an outgoing screen cannot clear the incoming screen’s trail', () => {
    // ⚡ **The outgoing screen is mounted, then the incoming one joins it** —
    // which is the order a client-side transition actually commits in.
    const { rerender } = render(
      <BreadcrumbTrailProvider>
        <Slot />
        {/* ⚡ **Keyed, and that is what makes this test bite.** ⛔ Unkeyed
            siblings reconcile by POSITION, so removing the first one *updates*
            the second in place and re-runs its effect — which republishes the
            trail and hides the defect. **Keys give the real mount/unmount
            ordering a route change has.** */}
        <Screen key="companies" trail={COMPANIES} />
        <Screen key="account" trail={ACCOUNT} />
      </BreadcrumbTrailProvider>,
    );
    expect(screen.getByTestId('slot')).toHaveTextContent('Accounts / Arvely Payments');

    // ⛔ **Now the outgoing screen leaves and runs its cleanup.**
    rerender(
      <BreadcrumbTrailProvider>
        <Slot />
        <Screen key="account" trail={ACCOUNT} />
      </BreadcrumbTrailProvider>,
    );

    // ✅ **The incoming screen's trail survives it.** Without the key guard
    // this reads empty, which is exactly what the browser showed.
    expect(screen.getByTestId('slot')).toHaveTextContent('Accounts / Arvely Payments');
  });
});
