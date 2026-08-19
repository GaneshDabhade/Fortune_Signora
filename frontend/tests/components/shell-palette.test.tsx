import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { afterEach, describe, expect, it, vi } from 'vitest';

import {
  GROUPS_WITH_NO_SOURCE_TODAY,
  PALETTE_GROUPS,
  PER_GROUP,
  ShellPalette,
} from '@/components/shell/shell-palette';
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
let recents: { entity_id: string; kind: string; viewed_at: string }[] = [];
let recentNames = new Map<string, { account_id: string; name: string | null }>();
vi.mock('@/lib/query/hooks/recently-viewed', () => ({
  useRecentlyViewed: () => ({ data: recents }),
}));
vi.mock('@/lib/query/hooks', () => ({
  useAccountIdentities: () => ({ data: recentNames }),
}));
const openCopilot = vi.fn();
vi.mock('@/components/shell/copilot', () => ({ useCopilot: () => ({ open: openCopilot }) }));

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
  openCopilot.mockClear();
  searchData = undefined;
  recents = [];
  recentNames = new Map();
});

/** ⚡ `n` recently-viewed accounts, all named, in the order the server returns. */
function seenRecently(count: number) {
  recents = Array.from({ length: count }, (_, index) => ({
    entity_id: `r${index}`,
    kind: 'account',
    viewed_at: new Date(2026, 7, 19, 9, count - index).toISOString(),
  }));
  recentNames = new Map(
    recents.map((record, index) => [
      record.entity_id,
      { account_id: record.entity_id, name: `Record ${index}` },
    ]),
  );
}

/**
 * The group HEADINGS the palette rendered, top to bottom.
 *
 * ⚠️ **`p`, not any element with the text.** ⛔ The first draft matched
 * `textContent`, so the *Navigate* row labelled *Reports* counted as a
 * `Reports` heading and the *Ask Signora* row as its own — **the test would
 * have reported a group that does not exist.** 📁 The palette renders a heading
 * as a `<p>` and a row as `role="option"`.
 */
function renderedGroups(): string[] {
  return Array.from(document.querySelectorAll('[role="listbox"] > div > p')).map(
    (el) => el.textContent!.trim(),
  );
}

/** The rows the palette rendered, in order, as `label`. */
function renderedRows(): string[] {
  return Array.from(document.querySelectorAll('[role="option"]')).map(
    (el) => el.querySelector('span.flex-1')!.textContent!.trim(),
  );
}

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
    // ⚡ **The kind rides the same line since [TASK-1484](../../../docs/BACKLOG.md)**
    // folded Companies and Technologies under the design's `Records` heading —
    // ⛔ so the assertion is that the row SAYS renamed, not that the line is
    // only that word.
    expect(screen.getByText(/renamed/)).toBeInTheDocument();
    expect(screen.getByText(/^Company/)).toBeInTheDocument();
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

describe('🔴 TASK-1484 ⓐ — the design names seven groups and fixes their order', () => {
  /**
   * 🔴 **The palette was complete against a MISQUOTE.** ⛔ `shell-palette.tsx`
   * stated the requirement as *"the design's groups are `Ask Signora` ·
   * `Recents` · `Actions` · `Navigate`"* — **four, presented as a quotation** —
   * and nothing had ever failed because the code matched the comment.
   *
   * ✅ **So this reads the DESIGN, not the code.** ⚡ The sentence is in the
   * snapshot, which 📁 [D-138](../../../docs/DECISION_REGISTER.md) makes the
   * implementation authority — **a test that asserted the constant against
   * itself would pass on the next misquote too.**
   */
  it('✅ the seven, by name and position, read out of the design document', () => {
    const design = readFileSync(
      join(
        process.cwd(),
        '..',
        'docs/design-snapshot/screens/Fortune Signora App Shell.dc.html',
      ),
      'utf8',
    );

    const sentence = /Group order is fixed\s*&mdash;|Group order is fixed\s*—\s*([^.]+?)\s*&mdash;|Group order is fixed\s*—\s*([^—]+?)\s*—/;
    const match = design.match(/Group order is fixed\s*—\s*([^—]+?)\s*—/);
    expect(match, 'the design no longer states a fixed group order').toBeTruthy();
    void sentence;

    const named = match![1]!.split(',').map((word) => word.trim());
    expect(named).toEqual([...PALETTE_GROUPS]);
  });

  /**
   * ⛔ **Order is a statement about where a group SITS, never a promise that
   * seven headings appear.** ⚡ A heading with nothing under it is the
   * false-affordance class this shell has refused three times.
   */
  it('✅ renders the groups it has, in that order, and no empty headings', async () => {
    seenRecently(2);
    searchData = [group()];
    palette();
    await userEvent.keyboard('{Meta>}k{/Meta}');

    const shown = renderedGroups();
    expect(shown).toEqual(['Ask Signora', 'Recents', 'Records', 'Navigate', 'Settings']);
    // ⛔ **The order is the design's, with the absent groups closed up** —
    // never re-sorted by how many results each happened to return.
    expect(shown).toEqual(PALETTE_GROUPS.filter((g) => shown.includes(g)));
  });

  /**
   * ⚡ **Two of the seven have no source in this product today, and it is a
   * MEASUREMENT.** 📁 `app/(app)/reports/` issues no query and the screen reads
   * *"No reports yet"*; the design's `Actions` examples are selection-scoped and
   * the palette is global. ⛔ 📁 TASK-1484: *"do not add a search backend to
   * satisfy a heading."*
   */
  it('⛔ and the two with no source are absent rather than empty', async () => {
    seenRecently(1);
    palette();
    await userEvent.keyboard('{Meta>}k{/Meta}');

    for (const group of GROUPS_WITH_NO_SOURCE_TODAY) {
      expect(renderedGroups()).not.toContain(group);
    }
  });
});

describe('📁 "five per group and a keyboard-reachable show all"', () => {
  it('✅ caps a group at five and offers the rest as a row', async () => {
    seenRecently(9);
    palette();
    await userEvent.keyboard('{Meta>}k{/Meta}');

    expect(screen.getAllByText(/^Record \d$/)).toHaveLength(PER_GROUP);
    // ⚡ **A row, not a control** — ↑↓ and ↵ reach it with no second
    // interaction model, which is what *keyboard-reachable* asks for.
    expect(screen.getByText('Show all 9')).toBeInTheDocument();
    expect(screen.getByText('4 more')).toBeInTheDocument();
  });

  it('✅ and choosing it expands that group without closing the palette', async () => {
    seenRecently(9);
    palette();
    await userEvent.keyboard('{Meta>}k{/Meta}');
    await userEvent.click(screen.getByText('Show all 9'));

    expect(screen.getAllByText(/^Record \d$/)).toHaveLength(9);
    // ⛔ **Closing here would make the one row whose purpose is *show me more*
    // the row that shows you less.**
    expect(screen.getByRole('listbox')).toBeInTheDocument();
    expect(push).not.toHaveBeenCalled();
  });

  it('⛔ a group of exactly five offers no show all', async () => {
    seenRecently(PER_GROUP);
    palette();
    await userEvent.keyboard('{Meta>}k{/Meta}');

    // ⚠️ **Scoped to the count that is five.** ⛔ `Navigate` has more than five
    // destinations for an owner, so an unscoped assertion would fail on a row
    // this test is not about.
    expect(screen.queryByText(`Show all ${PER_GROUP}`)).not.toBeInTheDocument();
    expect(renderedRows().filter((label) => /^Record \d$/.test(label))).toHaveLength(PER_GROUP);
  });
});

describe('📁 the groups this row added', () => {
  /**
   * ⛔ **Not the design's *"Answer: why is EMEA enterprise slipping"***. 📁
   * [TASK-482](../../../docs/BACKLOG.md) shipped the assistant with **no input
   * box** on purpose, so an *Answer:* row would promise a reply nothing can
   * produce. ✅ **The door the rail already offers is what the palette offers.**
   */
  it('✅ Ask Signora opens the assistant rather than promising an answer', async () => {
    palette();
    await userEvent.keyboard('{Meta>}k{/Meta}');
    // ⚠️ **The heading and the row share the label**, which is what the design
    // draws — so this clicks the ROW.
    const row = screen
      .getAllByRole('option')
      .find((el) => el.textContent?.includes('Ask Signora'));
    await userEvent.click(row!);

    expect(openCopilot).toHaveBeenCalledTimes(1);
    expect(push).not.toHaveBeenCalled();
  });

  it('✅ Recents names the record, and drops one nothing can name', async () => {
    seenRecently(2);
    recentNames.set('r1', { account_id: 'r1', name: null });
    palette();
    await userEvent.keyboard('{Meta>}k{/Meta}');

    expect(screen.getByText('Record 0')).toBeInTheDocument();
    // 🔴 **[B-290](../../../docs/BUGS.md) one surface over**: a palette row a
    // reader cannot recognise is one they cannot choose.
    expect(screen.queryByText('Record 1')).not.toBeInTheDocument();
  });

  it('🔴 Settings is withheld from a member, like every other guarded door', async () => {
    palette('member');
    await userEvent.keyboard('{Meta>}k{/Meta}');

    expect(renderedGroups()).not.toContain('Settings');
    expect(screen.queryByText('Your team')).not.toBeInTheDocument();
  });

  it('✅ and an owner is offered the settings page\'s own five, in its own words', async () => {
    palette('owner');
    await userEvent.keyboard('{Meta>}k{/Meta}');

    expect(screen.getByText('Change what you sell')).toBeInTheDocument();
    expect(screen.getByText('Audit log')).toBeInTheDocument();
  });
});
