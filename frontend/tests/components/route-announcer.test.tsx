/**
 * 🔴 **[B-1077](../../../docs/BUGS.md) — the route announcer read a raw URL,
 * UUID and all, to a screen reader.**
 *
 * ⚠️ **A screen-reader user is the ONLY user who hears this**, so the one
 * audience the component exists for was the one served worst.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const path = vi.hoisted(() => ({ value: '/w/4e158d14-ab29-4b23-b99d-a8b10986f8e5/home' }));
vi.mock('next/navigation', () => ({ usePathname: () => path.value }));

import { RouteAnnouncer } from '@/components/shell/route-announcer';

/** ⚡ The announcer reads the page's own heading, so a page must be on screen. */
function page(title: string) {
  return (
    <>
      <main>
        <h1>{title}</h1>
      </main>
      <RouteAnnouncer />
    </>
  );
}

const spoken = () => screen.getByRole('status').textContent ?? '';

beforeEach(() => {
  path.value = '/w/4e158d14-ab29-4b23-b99d-a8b10986f8e5/home';
});

describe('⛔ arrival is not a change, so the first paint is silent', () => {
  it('📁 says nothing on mount, because the page has only just been read out', () => {
    render(page('Home'));
    expect(spoken()).toBe('');
  });

  it('⛔ and says nothing when the path has not actually changed', () => {
    const { rerender } = render(page('Home'));
    rerender(page('Home'));
    expect(spoken()).toBe('');
  });
});

describe('🔴 what it announces is the PAGE TITLE, never the route', () => {
  it('📁 App Shell: “receives focus on route change and announces the new page title”', () => {
    const { rerender } = render(page('Home'));

    path.value = '/accounts';
    rerender(page('Accounts'));

    expect(spoken()).toBe('Accounts');
  });

  it('⛔ never speaks a UUID, a slug or a route template', () => {
    /**
     * 📁 **Measured on Home before the fix:**
     * *"Navigated to /w/4e158d14-ab29-4b23-b99d-a8b10986f8e5/home"* — ⛔ **a
     * thirty-six character identifier, spoken aloud.**
     *
     * 📁 [ADR-0034](../../../docs/architecture/adr/0034-ubiquitous-language.md)
     * — **`/w/<uuid>/home` is platform vocabulary**, and the translation is
     * supposed to live at the frontend edge.
     */
    /**
     * ⚠️ **The first draft started at the UUID path** — the value `beforeEach`
     * sets — **so the "change" was a no-op and the branch never ran.** ⛔ **The
     * assertion passed on an empty announcement**, which is the same defect
     * class this file is testing for: **a precondition the test never
     * established.**
     */
    path.value = '/accounts';
    const { rerender } = render(page('Accounts'));

    path.value = '/w/4e158d14-ab29-4b23-b99d-a8b10986f8e5/home';
    rerender(page('Home'));

    const said = spoken();
    expect(said).not.toMatch(/[0-9a-f]{8}-[0-9a-f]{4}/i);
    expect(said).not.toContain('/');
    expect(said).not.toMatch(/\[workspace\]|\bNavigated\b/);
    // ✅ **The pin** — it said the page's name, so the absences above are the
    // announcement rather than an absent announcement.
    expect(said).toBe('Home');
  });

  it('⚡ and it inherits ADR-0034 rather than restating it', () => {
    // ⛔ **The heading is already guarded by `vocabulary.test.tsx`**, so an
    // announcement built from it cannot carry the platform's word unless the
    // heading does — **one representation, not two.**
    const { rerender } = render(page('Accounts'));

    path.value = '/settings';
    rerender(page('Organization settings'));

    expect(spoken()).toBe('Organization settings');
    expect(spoken()).not.toMatch(/workspace/i);
  });
});

describe('⚠️ silence rather than a guess when there is no heading to read', () => {
  it('⛔ announces nothing rather than falling back to the route', () => {
    /**
     * ⛔ **A page with no `h1` is itself a defect** — 📁
     * `page-heading-role.test.tsx` enumerates every route-level heading with a
     * verdict. ⚡ **Announcing nothing is honest; announcing a route is not.**
     */
    const { rerender } = render(page('Home'));

    path.value = '/nowhere';
    rerender(
      <>
        <main />
        <RouteAnnouncer />
      </>,
    );

    expect(spoken()).toBe('');
  });
});

describe('♿ once, and politely — both halves are the rule', () => {
  it('📁 4.1.3 — a polite live region, never assertive', () => {
    // ⛔ **`assertive` would interrupt whatever the person is reading**, which
    // is the opposite of helpful during navigation they initiated.
    render(page('Home'));

    const region = screen.getByRole('status');
    expect(region).toHaveAttribute('aria-live', 'polite');
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('⚡ and it is heard, not seen', () => {
    render(page('Home'));
    expect(screen.getByRole('status').classList.contains('sr-only')).toBe(true);
  });
});
