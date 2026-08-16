import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { ShellPalette } from '@/components/shell/shell-palette';
import type { SearchGroup } from '@/lib/api/types';

/**
 * **The palette, mounted** — [TASK-1442](../../../docs/BACKLOG.md), resolving
 * 📁 [C-259](../../../docs/LANE_COORDINATION.md).
 */

const push = vi.fn();
let searchData: SearchGroup[] | undefined;

vi.mock('next/navigation', () => ({ useRouter: () => ({ push }) }));
vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: () => ({
    activeWorkspace: { id: 'w1', name: 'Northwind', created_at: '', updated_at: '' },
    workspaces: [],
    setActiveWorkspace: vi.fn(),
    isLoading: false,
    error: null,
  }),
}));
vi.mock('@/lib/query/hooks/search', () => ({ useAccountSearch: () => ({ data: searchData }) }));

function group(over: Partial<SearchGroup> = {}): SearchGroup {
  return {
    result_type: 'company',
    coverage: 'searched',
    results: [
      {
        account: {
          account_id: 'a1',
          name: 'Vantage Logistics',
          agreement: 'agreed',
          source_count: 1,
          source: null,
          observed_at: null,
        },
        result_type: 'company',
        matched_name: 'Vantage Logistics',
        matched_source: 'crm',
        is_renamed: false,
      },
    ],
    ...over,
  } as SearchGroup;
}

function palette(role: 'owner' | 'member' | null = 'owner') {
  return render(
    <QueryClientProvider client={new QueryClient()}>
      <ShellPalette role={role} />
    </QueryClientProvider>,
  );
}

afterEach(() => {
  push.mockClear();
  searchData = undefined;
});

describe('🔴 ⌘K opens the palette, which is what the design binds it to', () => {
  it('✅ it opens from anywhere, and it was closed before', async () => {
    /**
     * ⛔ **The shortcut belonged to `account-search.tsx`**, which bound it on
     * the document and focused its own input — ⚡ **so it worked and opened the
     * wrong thing.** 📁 *"Search — opens the palette on click or ⌘K."*
     */
    palette();
    expect(screen.queryByRole('dialog')).toBeNull();
    await userEvent.keyboard('{Meta>}k{/Meta}');
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });

  it('⛔ and account search no longer binds it — two handlers would both fire', () => {
    // ⚡ Asserted on the source, because a second document-level handler is
    // invisible to a rendering test that only mounts one of the two.
    const source = readFileSync(
      join(process.cwd(), 'components/intelligence/account-search.tsx'),
      'utf8',
    );
    expect(source).not.toMatch(/metaKey \|\| event\.ctrlKey/);
  });
});

describe('📁 account search is ONE GROUP inside it, not the owner of the shortcut', () => {
  it('✅ results appear alongside the destinations the shell owns', async () => {
    searchData = [group()];
    palette();
    await userEvent.keyboard('{Meta>}k{/Meta}');

    expect(screen.getByText('Vantage Logistics')).toBeInTheDocument();
    // 📁 The design's `Navigate` group — the shell's own destinations.
    expect(screen.getByText('Your business')).toBeInTheDocument();
  });

  it('🔴 a group Signora did NOT search is skipped, not rendered empty', async () => {
    /**
     * 📁 **`coverage` is read before `results`, always** — the product owner
     * ruled on 2026-08-05 that *"the absence of results and the absence of the
     * group represent different business meanings."* ⛔ **Flattening every
     * group would collapse *nothing matched* into *we did not look*.**
     */
    /**
     * ⚠️ **The first version of this test was DECORATIVE and a fire-test
     * caught it.** It used a `not_requested` group with `results: []`, so
     * removing the filter changed nothing and the test passed either way.
     * ⛔ **A group with no results proves nothing about a filter that drops
     * groups.**
     *
     * ✅ **The case the filter actually guards is a non-searched group that
     * CARRIES results** — rendering those would assert Signora looked when it
     * did not, which is precisely the collapse the coverage field exists to
     * prevent.
     */
    searchData = [
      group({
        coverage: 'not_requested',
        results: [{ ...group().results[0]!, matched_name: 'Never Searched Ltd' }],
      }),
      group(),
    ];
    palette();
    await userEvent.keyboard('{Meta>}k{/Meta}');

    expect(screen.queryByText('Never Searched Ltd')).toBeNull();
    expect(screen.getByText('Vantage Logistics')).toBeInTheDocument();
  });

  it('⚡ a renamed account says so, because that is what makes a right match look wrong', async () => {
    searchData = [
      group({
        results: [{ ...group().results[0]!, matched_name: 'Vantage Freight', is_renamed: true }],
      }),
    ];
    palette();
    await userEvent.keyboard('{Meta>}k{/Meta}');
    expect(screen.getByText('Vantage Freight')).toBeInTheDocument();
    expect(screen.getByText('renamed')).toBeInTheDocument();
  });
});

describe('🔴 the palette is not a second answer to what this person can reach', () => {
  it('⛔ a member is not offered a destination the rail withholds', async () => {
    /**
     * 📁 `navigation.tsx`'s own comment: **one list, two renderings** — *"a
     * second array would be a second answer to what can this person reach, and
     * the two would diverge the first time an entry was added to one."*
     * ⚡ **A palette offering `/settings` to a member would be exactly that
     * divergence**, so the same `guardFor`/`can` pair filters both.
     */
    palette('member');
    await userEvent.keyboard('{Meta>}k{/Meta}');
    expect(screen.queryByText('Settings')).toBeNull();
    // ⚡ **Vacuity guard is the NEXT test** — an owner IS offered it, so this
    // absence is the guard working rather than the group being empty.
    expect(screen.getByText('Your business')).toBeInTheDocument();
  });

  it('✅ and an owner is', async () => {
    palette('owner');
    await userEvent.keyboard('{Meta>}k{/Meta}');
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });
});

describe('✅ selecting navigates', () => {
  it('a destination goes to its route', async () => {
    palette();
    await userEvent.keyboard('{Meta>}k{/Meta}');
    // ⚠️ **Was `Attention` → `/`** — [TASK-1482](../../../docs/BACKLOG.md)
    // removed that rail entry on [D-240](../../../docs/DECISION_REGISTER.md),
    // and **the palette offers what the rail offers**, so the destination it
    // navigates to had to move with it. ⛔ **The property under test is
    // unchanged: selecting a destination goes to that destination's route.**
    await userEvent.click(screen.getByText('Your business'));
    expect(push).toHaveBeenCalledWith('/business');
  });

  it('an account goes to its record', async () => {
    searchData = [group()];
    palette();
    await userEvent.keyboard('{Meta>}k{/Meta}');
    await userEvent.click(screen.getByText('Vantage Logistics'));
    expect(push).toHaveBeenCalledWith('/accounts/a1');
  });
});
