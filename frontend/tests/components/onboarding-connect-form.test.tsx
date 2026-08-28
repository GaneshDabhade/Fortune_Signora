/**
 * **Onboarding step 6 — Connect** — 📁 `Fortune Signora Onboarding.dc.html`
 * screen `07`.
 *
 * 🔴 **The highest-stakes screen in the flow and nothing rendered it.** 📁 The
 * design's own note: *"Enterprise security reviews read this screen closely."*
 *
 * ⛔ **Its load-bearing claim is a promise about a customer's CRM** — *"read-only
 * to start, nothing is written without your approval"* — **and the design says
 * consent is never inferred.**
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const useIntegrations = vi.hoisted(() => vi.fn());
const usePreferences = vi.hoisted(() => vi.fn());
const useChangePreferences = vi.hoisted(() => vi.fn());
const useOnboarding = vi.hoisted(() => vi.fn());

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => '/onboarding/connect',
  useSearchParams: () => new URLSearchParams(),
}));
vi.mock('@/lib/query/hooks/integrations', () => ({ useIntegrations }));
vi.mock('@/lib/query/hooks/preferences', () => ({
  usePreferences,
  useChangePreferences,
}));
vi.mock('@/app/(onboarding)/onboarding/use-onboarding', () => ({ useOnboarding }));

import { ConnectForm } from '@/app/(onboarding)/onboarding/connect-form';

const NEVER = ['undefined', 'null', 'NaN', '[object Object]', '/**', '*/'];

/**
 * ⚠️ **`crm_activity`, from `IntegrationCapability`'s own union** — 🔴 **the
 * first draft of this fixture said `'crm'` and every assertion in the file
 * failed with *"Cannot read properties of undefined"*.**
 *
 * ⛔ **That is not a product defect and it looked exactly like one.** The union
 * is closed — `crm_activity · meetings · email_engagement · message_delivery` —
 * **so an out-of-union value is unconstructable in TypeScript**, and the screen
 * already guards the empty case. ⚡ **A loosely typed mock reached a state the
 * product cannot.**
 *
 * 📁 **Second time this session**, after `NO_FILTERS`: **a fixture that
 * reconstructs a contract by hand is a second representation of it.**
 */
const SYSTEM = {
  integration: 'salesforce',
  connectable: true,
  working: false,
  needs_attention: false,
  connections: [],
  capabilities: ['crm_activity'] as const,
};

beforeEach(() => {
  vi.clearAllMocks();
  useIntegrations.mockReturnValue({ data: [SYSTEM], isLoading: false, isError: false });
  usePreferences.mockReturnValue({ data: { ai_drafts: false, ai_insights: false } });
  useChangePreferences.mockReturnValue({ mutate: vi.fn(), isPending: false });
  useOnboarding.mockReturnValue({
    run: { answers: {}, step: 'connect' },
    error: null,
    isLoading: false,
    isSaving: false,
    save: vi.fn(),
    advance: vi.fn(),
  });
});

describe('🔴 the promise about a customer’s CRM, verbatim', () => {
  it('⛔ "read-only until you say otherwise" is on the screen', () => {
    /**
     * 📁 **The design's own sentence**, and it is the one line an enterprise
     * security review reads. ⛔ **Asserted verbatim rather than by keyword** —
     * a paraphrase would pass a looser test and weaken a commitment.
     */
    const { container } = render(<ConnectForm />);

    expect(
      screen.getByText(/Signora is read-only until you say otherwise\./),
    ).toBeInTheDocument();
    for (const f of NEVER) expect(container.textContent ?? '').not.toContain(f);
  });

  it('⛔ and the customer word is used, never the platform one', () => {
    /**
     * 📁 **The design writes *"land in a **workspace** with sample data"*** and
     * 📁 [ADR-0034](../../../docs/architecture/adr/0034-ubiquitous-language.md)
     * keeps that word off a customer's screen. ⚡ **The noun was dropped rather
     * than translated** — *Organization* would be accurate and clumsy, and the
     * sentence does not need one.
     */
    const { container } = render(<ConnectForm />);
    expect(container.textContent ?? '').not.toMatch(/workspace/i);
  });

  it('✅ every offered system is labelled read-only, never with a write scope', () => {
    // 📁 *"Read-only · 3 objects."* ⛔ **A write scope here would make the
    // promise above false at the moment it is shown.**
    render(<ConnectForm />);
    expect(screen.getAllByText(/Read-only/).length).toBeGreaterThan(0);
  });
});

describe('⛔ consent is never inferred', () => {
  it('🔴 every AI setting starts at the conservative end', () => {
    /**
     * 📁 **The design states it twice**: *"Inferred: **nothing**. Consent is
     * never inferred."* and *"every AI and data setting starts at the
     * conservative end: read-only, drafts need approval, no CRM writes."*
     *
     * ⚡ **So the checkboxes must be OFF on arrival**, whatever the reader
     * eventually chooses. ⛔ **A pre-ticked consent is consent collected under
     * a false premise.**
     */
    render(<ConnectForm />);

    for (const box of screen.queryAllByRole('checkbox')) {
      expect(box).not.toBeChecked();
    }
  });
});

describe('📁 skipping is offered, and it does not pretend to connect', () => {
  it('✅ the skip names what it gives you instead', () => {
    // ⛔ **A *Skip* that promised sample data and delivered an empty product
    // would be P-A's shape one screen earlier.**
    render(<ConnectForm />);
    expect(
      screen.getByRole('button', { name: 'Skip — use sample data' }),
    ).toBeInTheDocument();
  });

  it('⛔ with nothing connectable it says so, rather than drawing an empty list', () => {
    // 📁 **P-A** — an absence is stated, never rendered as a blank.
    useIntegrations.mockReturnValue({ data: [], isLoading: false, isError: false });
    const { container } = render(<ConnectForm />);

    expect(screen.getByText(/There is nothing to connect yet/)).toBeInTheDocument();
    for (const f of NEVER) expect(container.textContent ?? '').not.toContain(f);
  });
});
