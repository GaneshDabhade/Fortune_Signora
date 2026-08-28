/**
 * **The onboarding forms** — 📁 `Fortune Signora Onboarding.dc.html`, and
 * `Workspace Setup` `2.4.6` for the labelling rule they share.
 *
 * 🔴 **The largest cluster of surfaces nothing rendered** — and it is the first
 * flow every customer walks. ⛔ **`tsc` and `eslint` pass on a form whose every
 * field is unlabelled**, which is the gap this closes.
 *
 * ⚠️ **Shallow on purpose**: the witness, plus the one contract that is
 * checkable from a render — **every control has an accessible name.**
 */
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const useOnboarding = vi.hoisted(() => vi.fn());

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => '/onboarding/you',
  // ⚡ **`SkipSetup` resolves the entry decision**, which reads the query
  // string — ⛔ **stubbed rather than the hook itself**, so the exit path stays
  // real code rather than a second mock nobody maintains.
  useSearchParams: () => new URLSearchParams(),
}));
vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: () => ({ activeWorkspace: { id: 'w1', name: 'Northwind' } }),
}));
vi.mock('@/app/(onboarding)/onboarding/use-onboarding', () => ({ useOnboarding }));

import { YouForm } from '@/app/(onboarding)/onboarding/you-form';
import { CompanyForm } from '@/app/(onboarding)/onboarding/company-form';

const NEVER = ['undefined', 'null', 'NaN', '[object Object]', '/**', '*/'];

/**
 * ⚡ **The real query client, with retries off** — ⛔ **`SkipSetup` resolves the
 * entry decision and that reads `/workspaces`**, so the exit path stays real
 * code rather than a third mock nobody maintains. **The request never
 * resolves here, which is the *unresolved* branch and a state the form must
 * render through.**
 */
function draw(element: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{element}</QueryClientProvider>);
}

beforeEach(() => {
  vi.clearAllMocks();
  useOnboarding.mockReturnValue({
    run: { answers: {}, step: 'you' },
    error: null,
    isLoading: false,
    isSaving: false,
    save: vi.fn(),
    advance: vi.fn(),
  });
});

const FORMS: readonly (readonly [string, () => React.ReactElement])[] = [
  ['You', () => <YouForm />],
  ['Company', () => <CompanyForm />],
];

describe('⛔ no onboarding form prints an absence, a comment, or an object', () => {
  for (const [name, form] of FORMS) {
    it(`✅ ${name}`, () => {
      const { container } = draw(form());
      const text = container.textContent ?? '';
      // ⚡ **The vacuity half** — a form that returned `null` under these mocks
      // would satisfy every assertion below.
      expect(text.trim().length).toBeGreaterThan(40);
      for (const forbidden of NEVER) expect(text).not.toContain(forbidden);
    });
  }
});

describe('♿ 2.4.6 — every control has a name, and a render is what proves it', () => {
  for (const [name, form] of FORMS) {
    it(`🔴 ${name} — nothing is announced as a bare control`, () => {
      /**
       * 📁 **`Workspace Setup` `2.4.6`**: *"Every field has a visible label and
       * help text. **Placeholders are never used as labels.**"*
       *
       * ⚠️ **A SOURCE SWEEP WAS TRIED FIRST AND ABANDONED, and the reason
       * belongs here.** ⛔ **A raw `<input>` can be named four ways** —
       * `aria-label`, `aria-labelledby`, `id` paired with a `htmlFor`, or a
       * wrapping `<label>` — **and a grep cannot see the fourth.** ⚡ **It
       * reported eighteen candidates and the ones worth checking were all
       * wrapped labels**: correct code, flagged.
       *
       * ✅ **The accessibility tree is the right instrument for a question
       * about the accessibility tree**, and `getByRole` computes the name the
       * same way a screen reader does. 📁 **The lesson one register over**:
       * *deciding whether a `/**` sits inside JSX is a parsing question* —
       * **and so is deciding what names a control.**
       */
      draw(form());

      const controls = [
        ...screen.queryAllByRole('textbox'),
        ...screen.queryAllByRole('combobox'),
        ...screen.queryAllByRole('checkbox'),
        ...screen.queryAllByRole('radio'),
        ...screen.queryAllByRole('radiogroup'),
        ...screen.queryAllByRole('button'),
      ];

      // ⚡ **The vacuity half again, and it is the load-bearing one**: an
      // empty list passes the loop below without running it once.
      expect(controls.length).toBeGreaterThan(2);

      for (const control of controls) {
        const named =
          (control.getAttribute('aria-label') ?? '').trim() !== '' ||
          control.hasAttribute('aria-labelledby') ||
          (control.textContent ?? '').trim() !== '' ||
          (control.id !== '' &&
            document.querySelector(`label[for="${control.id}"]`) !== null) ||
          control.closest('label') !== null;

        expect(named, `${control.tagName} with no accessible name`).toBe(true);
      }
    });
  }
});
