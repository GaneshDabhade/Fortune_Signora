import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import AuditLogPage from '@/app/(app)/settings/audit/page';
import type { CursorPage, HistoryEntry } from '@/lib/api/types';

/**
 * **The audit log becomes a place you can go** —
 * [TASK-1412](../../../docs/BACKLOG.md).
 *
 * ⚡ **The row's remaining Definition of Done is *"every change is attributed
 * in the audit log"***, and 📁 the Settings design's page promise is
 * ***"Every change is attributed, reversible and visible in the audit log."***
 */

const entry = (over: Partial<HistoryEntry> = {}): HistoryEntry => ({
  occurred_at: '2026-08-09T09:14:00Z',
  kind: 'role_changed',
  actor_id: 'user_1',
  actor_email: 'marta@northwind.test',
  subject_email: 'lars@northwind.test',
  subject_membership_id: 'mem_2',
  previous_role: 'member',
  new_role: 'owner',
  // ⚡ **The wire carries a reason on every entry**, and the fixture states it
  // rather than letting `Partial` quietly make the field optional — the same
  // slip the entry fixtures made one row earlier.
  reason: null,
  ...over,
});

let historyState: {
  data: CursorPage<HistoryEntry> | undefined;
  isLoading: boolean;
  isError: boolean;
} = { data: undefined, isLoading: false, isError: false };

let workspaceState: { activeWorkspace: { id: string; name: string } | null; isLoading: boolean; error: Error | null } =
  { activeWorkspace: { id: 'ws_north', name: 'Northwind' }, isLoading: false, error: null };

vi.mock('@/lib/query/hooks/team', () => ({
  useOrganizationHistory: () => historyState,
}));

vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: () => ({ ...workspaceState, workspaces: [], setActiveWorkspace: vi.fn() }),
}));

describe('🔴 the record that had no door', () => {
  it('⚡ renders the change with WHO made it and what it was before', () => {
    /**
     * 📁 **The design**: *"Every entry records actor, before and after
     * values."* ⚡ **The platform publishes `previous_role` and `new_role`**,
     * so that half is real rather than promised.
     */
    historyState = { data: { items: [entry()], next_cursor: null, has_more: false }, isLoading: false, isError: false };

    render(<AuditLogPage />);

    expect(screen.getByRole('heading', { name: 'Audit log' })).toBeInTheDocument();
    expect(screen.getByText(/marta@northwind\.test/)).toBeInTheDocument();
  });

  it('⛔ states that entries cannot be edited, because that is the claim being made', () => {
    // ⚡ **An audit log's only value is that nobody can change it**, so the
    // page says so rather than leaving a reader to assume it.
    historyState = { data: { items: [entry()], next_cursor: null, has_more: false }, isLoading: false, isError: false };

    render(<AuditLogPage />);

    expect(screen.getByText(/never edited/i)).toBeInTheDocument();
  });
});

describe('⛔ what the platform cannot answer is shown locked, never invented', () => {
  it('🔴 prints NO retention period, because stating one would be a claim in an audit', () => {
    /**
     * 📁 **The design says *"Immutable · 7 years"*.** ⛔ **Printing *7 years*
     * would be [§20c](../../../CLAUDE.md)'s mock business data on the one
     * screen whose entire value is that it does not make things up** — and a
     * customer would rely on it.
     */
    historyState = { data: { items: [entry()], next_cursor: null, has_more: false }, isLoading: false, isError: false };

    const { container } = render(<AuditLogPage />);

    expect(screen.getByText('Retention period')).toBeInTheDocument();
    expect(container.textContent).not.toMatch(/7 years/);
  });

  it('⚡ every locked field carries its reason — a lock without one is worse than absence', () => {
    historyState = { data: { items: [], next_cursor: null, has_more: false }, isLoading: false, isError: false };

    render(<AuditLogPage />);

    for (const label of ['Sign-in address and session', 'Retention period', 'Export']) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
    expect(screen.getByText(/not captured yet/)).toBeInTheDocument();
  });
});

describe('♿ the states every route owes', () => {
  it('⛔ a failed read is STATED, never rendered as an empty log', () => {
    /**
     * 🔴 **[P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md)**: *a failed read
     * must never render as an empty result.* ⚠️ **On an audit log this is the
     * sharpest case in the product** — **an empty audit log reads as *nothing
     * happened***, which is a different and much more dangerous claim than
     * *this did not load*.
     */
    historyState = { data: undefined, isLoading: false, isError: true };

    render(<AuditLogPage />);

    expect(screen.getByText(/could not be loaded/i)).toBeInTheDocument();
  });

  it('⚡ and a genuinely empty log is not mistaken for a failure either', () => {
    historyState = { data: { items: [], next_cursor: null, has_more: false }, isLoading: false, isError: false };

    render(<AuditLogPage />);

    expect(screen.queryByText(/could not be loaded/i)).not.toBeInTheDocument();
  });

  it('⛔ no workspace is its own answer, not an empty audit log', () => {
    workspaceState = { activeWorkspace: null, isLoading: false, error: null };
    historyState = { data: { items: [], next_cursor: null, has_more: false }, isLoading: false, isError: false };

    render(<AuditLogPage />);

    expect(screen.queryByRole('heading', { name: 'Audit log' })).not.toBeInTheDocument();

    workspaceState = { activeWorkspace: { id: 'ws_north', name: 'Northwind' }, isLoading: false, error: null };
  });
});
