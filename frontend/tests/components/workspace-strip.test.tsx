/**
 * **Home hierarchy 2 — the workspace confirmation strip** —
 * [TASK-1441](../../../docs/BACKLOG.md), against 📁 `Authenticated Entry`
 * rules 11, 12 and 22 and `Home` §09.
 *
 * 🔴 **This component had NO test, and that is how a docstring came to be
 * rendered on Home as visible text.** ⛔ **An unbraced block comment between
 * two JSX children is not a comment — it is a text node**, and React prints
 * it. ⚡ **Nothing in the repository rendered this component**, so nothing
 * could see it.
 */
import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const mutateAsync = vi.hoisted(() => vi.fn());

vi.mock('@/lib/query/hooks/preferences', () => ({
  useRecordEntry: () => ({ mutateAsync }),
}));

import { WorkspaceStrip } from '@/components/home/workspace-strip';

const ENTRY = {
  first_entry_today: true,
  first_entry_ever: false,
  role_change: null,
};

beforeEach(() => {
  vi.clearAllMocks();
  mutateAsync.mockResolvedValue(ENTRY);
});

function strip(overrides: Record<string, unknown> = {}) {
  return render(
    <WorkspaceStrip
      workspaceId="w1"
      workspaceName="Northwind Global"
      memberships={3}
      {...overrides}
    />,
  );
}

describe('🔴 what the strip renders, and what it must never render', () => {
  it('⛔ prints no comment markers, because a docstring outside braces IS content', async () => {
    /**
     * ⚡ **The defect this file was opened for.** ⛔ A block comment placed
     * between `{notice}` and the strip's own `<div>` rendered on Home as
     * literal text — *"/** * ♿ role="status" — 4.1.3…"* — **on the product's
     * most-visited screen.**
     *
     * ⚠️ **The mangled `* *` fragments inside it showed how it happened**: a
     * braced comment reflowed until the braces were lost. ✅ **The permanent
     * guard is `react/jsx-no-comment-textnodes`**, now registered in
     * `eslint.config.mjs` — **a parser rule, because deciding whether a `/**`
     * is inside JSX is a parsing question and every regex answer is either too
     * narrow or too wide.**
     */
    const { container } = strip();
    await screen.findByText(/Northwind Global/);

    const text = container.textContent ?? '';
    expect(text).not.toContain('/**');
    expect(text).not.toContain('*/');
    expect(text).not.toContain('role="status"');
    // ⚡ **The vacuity half**: the strip must actually be on screen, or every
    // assertion above passes against an empty container.
    expect(screen.getByTestId('workspace-confirmation')).toBeInTheDocument();
  });

  it('📁 rule 11 — one membership means no strip at all', async () => {
    // 📁 *"Exactly one membership. Enter it. No confirmation, no picker, no
    // interstitial."* ⛔ Not *a strip that says you have one workspace*.
    strip({ memberships: 1 });
    await waitFor(() => expect(mutateAsync).toHaveBeenCalled());

    expect(screen.queryByTestId('workspace-confirmation')).toBeNull();
  });

  it('📁 rule 22 — a welcome replaces the confirmation, and rule 11 does not suppress it', async () => {
    /**
     * 📁 *"The new workspace becomes active, with a **welcome strip**"*, and
     * the welcome *"replaces the confirmation strip."*
     *
     * ⛔ **Rule 11 is about having nothing to confirm.** ⚡ Somebody who has
     * just joined has something to be told, **whether or not it is their only
     * organization.**
     */
    mutateAsync.mockResolvedValue({ ...ENTRY, first_entry_ever: true });
    strip({ memberships: 1 });

    expect(await screen.findByTestId('workspace-welcome')).toBeInTheDocument();
    expect(screen.queryByTestId('workspace-confirmation')).toBeNull();
  });

  it('⛔ a failed entry record shows no strip, and guesses nothing', async () => {
    // ⚡ It is a courtesy, and *"probably your first visit"* is the one thing
    // it must not say.
    mutateAsync.mockRejectedValue(new Error('down'));
    strip();
    await waitFor(() => expect(mutateAsync).toHaveBeenCalled());

    expect(screen.queryByTestId('workspace-confirmation')).toBeNull();
    expect(screen.queryByTestId('workspace-welcome')).toBeNull();
  });

  it('♿ it announces politely, because confirming where somebody already is is not an interruption', async () => {
    // 📁 `4.1.3` — *"entry announces once"*, and the greeting owns that
    // sentence. ⛔ Not `alert`.
    strip();
    const region = await screen.findByTestId('workspace-confirmation');

    expect(region).toHaveAttribute('role', 'status');
  });
});
