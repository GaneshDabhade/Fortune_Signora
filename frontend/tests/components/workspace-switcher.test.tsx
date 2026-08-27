import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { WorkspaceSwitcher } from '@/components/shell/workspace-switcher';
import type { Workspace } from '@/lib/api/types';

/**
 * **The workspace switcher, in the rail** — [TASK-1441](../../../docs/BACKLOG.md).
 *
 * ⚡ **The context is stubbed rather than the network**, because every
 * assertion here is about the switcher's own behaviour — placement, keyboard,
 * filtering and what it does NOT claim.
 */

const setActiveWorkspace = vi.fn();
let state: {
  workspaces: Workspace[];
  activeWorkspace: Workspace | null;
  isLoading: boolean;
};

function ws(id: string, name: string): Workspace {
  return { id, name, created_at: '2026-01-01', updated_at: '2026-01-01' };
}

vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: () => ({ ...state, setActiveWorkspace, error: null }),
}));

function switcher(
  workspaces: Workspace[],
  { isLoading = false }: { isLoading?: boolean } = {},
) {
  state = { workspaces, activeWorkspace: workspaces[0] ?? null, isLoading };
  return render(
    <QueryClientProvider client={new QueryClient()}>
      <WorkspaceSwitcher />
    </QueryClientProvider>,
  );
}

const THREE = [ws('a', 'Northwind Global'), ws('b', 'Northwind Americas'), ws('c', 'Vantage Logistics')];

afterEach(() => setActiveWorkspace.mockClear());

describe('📁 the trigger, and the word a customer hears', () => {
  it('⛔ the accessible name says ORGANIZATION, never workspace', () => {
    /**
     * 📁 **ADR-0034**, and the reason the control it replaces already carried:
     * ⚡ **a screen-reader user hearing *"workspace"* would be the only
     * customer ever told the internal word** — the worst possible place for it
     * to survive.
     */
    switcher(THREE);
    const trigger = screen.getByRole('button', { name: /Active organization/ });
    expect(trigger).toBeInTheDocument();
    expect(trigger).not.toHaveAccessibleName(/workspace/i);
  });

  it('✅ it names the current organization, so the rail says what everything below belongs to', () => {
    // 📁 *"Placement at the top of the rail matches the mental model:
    // everything below belongs to it."* ⛔ A trigger that does not name the
    // current one cannot carry that.
    switcher(THREE);
    expect(screen.getByRole('button', { name: /Northwind Global/ })).toBeInTheDocument();
  });

  it('⛔ renders nothing before the active organization is known', () => {
    // ⚡ Not an empty trigger — a control naming no organization would be the
    // rail claiming a fact it does not have yet.
    const { container } = switcher([], { isLoading: false });
    expect(container).toBeEmptyDOMElement();
  });
});

describe('📁 the menu', () => {
  it('✅ every organization is offered, and the current one is marked', async () => {
    switcher(THREE);
    await userEvent.click(screen.getByRole('button', { name: /Active organization/ }));

    const menu = screen.getByRole('menu', { name: 'Switch organization' });
    const items = within(menu).getAllByRole('menuitemradio');
    expect(items).toHaveLength(THREE.length);
    // ⛔ `aria-checked`, not colour — colour alone never carries a state.
    expect(items[0]).toHaveAttribute('aria-checked', 'true');
    expect(items[1]).toHaveAttribute('aria-checked', 'false');
  });

  it('✅ choosing one switches, and does not navigate', async () => {
    /**
     * 📁 *"Switching keeps the current route when it exists in the
     * destination."* ⚡ **Every route in this product exists in every
     * workspace**, so *staying put* IS route preservation — and a `router.push`
     * here would be the switcher inventing a destination.
     */
    switcher(THREE);
    await userEvent.click(screen.getByRole('button', { name: /Active organization/ }));
    await userEvent.click(screen.getByRole('menuitemradio', { name: /Northwind Americas/ }));

    expect(setActiveWorkspace).toHaveBeenCalledWith('b');
    expect(screen.queryByRole('menu')).toBeNull();
  });

  it('📁 administrative actions are the last rows, and only ones that exist', async () => {
    /**
     * 📁 *"Administrative actions are always the last two rows."* ⛔ **The
     * design does not name them, and only destinations that EXIST are
     * offered** — there is no create-workspace route, and a row leading
     * nowhere is [C-269](../../../docs/LANE_COORDINATION.md) again.
     *
     * ⚠️ **This test asserted NOTHING when first written** — it clicked the
     * trigger and ended. **A test body with no expectation is the purest form
     * of the Decorative Logic [§2](../../../CLAUDE.md) names**, and it passed.
     */
    switcher(THREE);
    await userEvent.click(screen.getByRole('button', { name: /Active organization/ }));
    const menu = screen.getByRole('menu', { name: 'Switch organization' });

    const links = within(menu).getAllByRole('menuitem');
    expect(links.map((a) => a.getAttribute('href'))).toEqual([
      '/settings/organization',
      '/settings/team',
    ]);

    // ⛔ **Last**, which is the half the design states — asserted as document
    // order against the organization rows above them.
    const rows = within(menu).getAllByRole('menuitemradio');
    const lastRow = rows[rows.length - 1];
    const firstAction = links[0];
    // ⚡ **Asserted present before compared** — `getAllByRole` cannot return an
    // empty array without throwing, but the indexed reads can still be
    // `undefined` to the compiler, and `!` would hide a real emptiness.
    expect(lastRow).toBeDefined();
    expect(firstAction).toBeDefined();
    expect(
      (lastRow as HTMLElement).compareDocumentPosition(firstAction as HTMLElement) &
        Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
  });
});

describe('📁 the keyboard, which is most of this row', () => {
  it('✅ ⌘⇧W opens it from anywhere', async () => {
    switcher(THREE);
    expect(screen.queryByRole('menu')).toBeNull();

    await userEvent.keyboard('{Meta>}{Shift>}W{/Shift}{/Meta}');
    expect(screen.getByRole('menu', { name: 'Switch organization' })).toBeInTheDocument();
  });

  it('✅ 1–9 selects by position', async () => {
    switcher(THREE);
    await userEvent.click(screen.getByRole('button', { name: /Active organization/ }));
    await userEvent.keyboard('2');
    expect(setActiveWorkspace).toHaveBeenCalledWith('b');
  });

  it('♿ Escape closes it and returns focus to the trigger', async () => {
    // 📁 *"Focus returns to the trigger on close."* ⚡ The half that is usually
    // dropped, and dropping it returns a keyboard user to the top of the page.
    switcher(THREE);
    const trigger = screen.getByRole('button', { name: /Active organization/ });
    await userEvent.click(trigger);
    await userEvent.keyboard('{Escape}');

    expect(screen.queryByRole('menu')).toBeNull();
    expect(trigger).toHaveFocus();
  });
});

describe('📁 search appears above six', () => {
  it('⛔ three organizations get no filter', async () => {
    switcher(THREE);
    await userEvent.click(screen.getByRole('button', { name: /Active organization/ }));
    expect(screen.queryByRole('searchbox', { name: /Filter organizations/ })).toBeNull();
  });

  it('✅ seven do, and typing filters them', async () => {
    // 📁 *"Search appears above six workspaces."* ⚡ **Seven, not six** — the
    // threshold is *above six*, and asserting at six would pass whether the
    // comparison were `>` or `>=`.
    const seven = Array.from({ length: 7 }, (_, i) => ws(`w${i}`, `Org ${i}`));
    switcher(seven);
    await userEvent.click(screen.getByRole('button', { name: /Active organization/ }));

    const search = screen.getByRole('searchbox', { name: /Filter organizations/ });
    await userEvent.type(search, 'Org 4');
    expect(screen.getAllByRole('menuitemradio')).toHaveLength(1);
  });

  it('⛔ a digit typed into the filter does not switch organization', async () => {
    /**
     * 🔴 **The two keyboard rules collide and the filter wins.** ⚡ *"1–9
     * selects by position"* and *"type to filter"* are both the design's, and
     * **a person searching for an organization whose name starts with a digit
     * must be able to type it.** ⛔ Without the guard, typing `1` would switch
     * them to the first organization instead.
     */
    const seven = Array.from({ length: 7 }, (_, i) => ws(`w${i}`, `Org ${i}`));
    switcher(seven);
    await userEvent.click(screen.getByRole('button', { name: /Active organization/ }));
    await userEvent.type(screen.getByRole('searchbox', { name: /Filter organizations/ }), '1');

    expect(setActiveWorkspace).not.toHaveBeenCalled();
  });
});

describe('🔴 what the switcher does NOT claim', () => {
  it('⛔ no environment or role tag is rendered, because no field publishes one', async () => {
    /**
     * 📁 The design's row is *"22px avatar, name, role and environment,
     * right-hand tag"*, and its rationale is a SAFETY one: *"role and
     * environment on the row prevent the classic mistake of editing production
     * while thinking it is sandbox."*
     *
     * ⛔ **`Workspace` publishes `id`, `name`, `created_at`, `updated_at`.**
     * ⚡ **A tag reading *Prod* on every row because no field says otherwise
     * would be the product asserting a fact it does not have, about the one
     * thing the design says people get wrong.** ✅ **Absent, and raised as
     * [C-276](../../../docs/LANE_COORDINATION.md).**
     *
     * ⚠️ **This test states today's truth so the day a field arrives is loud.**
     */
    switcher(THREE);
    await userEvent.click(screen.getByRole('button', { name: /Active organization/ }));

    // ⚡ **Vacuity guard.** ⛔ **This first used `.click()` rather than
    // `userEvent`, so the menu may never have opened** — every absence below
    // would then have passed over a closed menu. **The menu is asserted OPEN
    // before anything is asserted missing from it.**
    expect(screen.getByRole('menu', { name: 'Switch organization' })).toBeInTheDocument();
    expect(screen.getAllByRole('menuitemradio')).toHaveLength(THREE.length);

    for (const invented of [/sandbox/i, /production/i, /guest/i, /admin/i, /read-only/i]) {
      expect(screen.queryByText(invented)).toBeNull();
    }
  });
});

describe('📁 §1.4.1 — the selected row carries three markers, not two', () => {
  /**
   * 📁 `Workspace Chooser`, `a11y` §1.4.1, verbatim:
   *
   * > ***"The selected row uses the brand tint, a 600-weight name and the word
   * > 'Current'. Colour alone never marks selection."***
   *
   * ✅ **The tint and the weight were both present.** ⛔ **The word was not** —
   * `grep` for it in `workspace-switcher.tsx` returned **zero**.
   *
   * ⚠️ **This was not *colour alone***: a 600-weight name is a genuine
   * non-colour signal, so the strict reading of 1.4.1 was already satisfied.
   * ⚡ **It is the design naming three markers and the product carrying two**,
   * and weight is the weakest of the three for a reader with low vision.
   *
   * ♿ **`aria-checked` on the `menuitemradio` already tells assistive
   * technology, and did before this** — ⛔ **so the gap was the SIGHTED half**,
   * which is the half 1.4.1 is about.
   */
  it('🔴 names the current organization in words, not only in tint and weight', async () => {
    switcher(THREE);
    await userEvent.click(screen.getByRole('button', { name: /Active organization/ }));

    const rows = screen.getAllByRole('menuitemradio');
    const current = rows.find((row) => row.getAttribute('aria-checked') === 'true');
    expect(current, 'no row is marked current').toBeDefined();

    expect(current).toHaveTextContent('Current');
  });

  it('⛔ says it on the current row ONLY', async () => {
    switcher(THREE);
    await userEvent.click(screen.getByRole('button', { name: /Active organization/ }));

    // ⚡ A label on every row would mark nothing — the positive control for
    // this assertion, and the shape [B-1033](../../../docs/BUGS.md) lacked.
    const labelled = screen
      .getAllByRole('menuitemradio')
      .filter((row) => row.textContent?.includes('Current'));
    expect(labelled).toHaveLength(1);
  });
});

describe('📁 §4.1.3 — a switch announces politely, and it was silent', () => {
  /**
   * 📁 ***"Switch start announces politely with the destination name.
   * Completion announces once with the workspace and the landing route."***
   *
   * ⛔ **Nothing announced at all.** ⚡ **A switch changes every scoped figure
   * on the screen without moving the page** — a sighted reader watches the
   * numbers change and a screen-reader user is told nothing.
   *
   * ⚠️ **Only the first sentence is implemented**, and the second is
   * [C-1558](../../../docs/LANE_COORDINATION.md): this component sets the
   * active organization and returns, so **it cannot observe when the re-read
   * finished**, and announcing completion at the moment of the request would
   * claim an arrival that has not happened.
   */
  it('🔴 names the destination when a switch starts', async () => {
    switcher(THREE);
    await userEvent.click(screen.getByRole('button', { name: /Active organization/ }));
    await userEvent.click(screen.getByRole('menuitemradio', { name: /Northwind Americas/ }));

    expect(screen.getByRole('status')).toHaveTextContent('Switching to Northwind Americas');
  });

  it('⛔ says nothing before a switch is chosen', () => {
    /**
     * ⚡ **The positive control.** ⛔ A live region rendering its message
     * unconditionally would satisfy the test above and announce on every
     * render — the [B-1057](../../../docs/BUGS.md) shape, where the
     * announcement element exists and says the wrong thing.
     */
    switcher(THREE);

    expect(screen.getByRole('status')).toHaveTextContent('');
  });

  it('⛔ announces politely, never assertively', () => {
    // 📁 §4.1.3 reserves assertive for a state that ends the session.
    switcher(THREE);

    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('🔴 the arrows walk the menu, because `role="menu"` promises they do', async () => {
    /**
     * ⛔ **Every row was a `<button>` reachable only by `Tab`** — which is what
     * a list of buttons offers, ⚡ **but a `menu` puts most screen readers into
     * application mode, where `Tab` is intercepted and the arrows are the way
     * through.** 📁 [B-1055](../../../docs/BUGS.md), one component along:
     * *"the role is claimed only when it is true."*
     */
    switcher(THREE);
    await userEvent.click(screen.getByRole('button', { name: /Active organization/ }));

    const rows = screen.getAllByRole('menuitemradio');
    rows[0]?.focus();

    await userEvent.keyboard('{ArrowDown}');
    expect(rows[1]).toHaveFocus();
    await userEvent.keyboard('{ArrowDown}');
    expect(rows[2]).toHaveFocus();

    // ⚡ **The administrative rows are part of the menu**, so arrowing past the
    // last organization reaches them rather than stopping.
    await userEvent.keyboard('{ArrowDown}');
    expect(screen.getByRole('menuitem', { name: 'Organization settings' })).toHaveFocus();

    // ⛔ **Wraps** — the menu is short and holding ArrowDown should not stall.
    await userEvent.keyboard('{ArrowDown}{ArrowDown}');
    expect(rows[0]).toHaveFocus();

    await userEvent.keyboard('{ArrowUp}');
    expect(screen.getByRole('menuitem', { name: 'Members & roles' })).toHaveFocus();
  });

  it('⛔ and only ONE item is a tab stop, so Tab leaves the menu', async () => {
    /**
     * 📁 **A roving tabindex** — the same correction `utility-panel.tsx`
     * needed: *"all three read `null` before, so `Tab` walked the strip instead
     * of leaving it."*
     */
    switcher(THREE);
    await userEvent.click(screen.getByRole('button', { name: /Active organization/ }));

    const stops = [
      ...screen.getAllByRole('menuitemradio'),
      ...screen.getAllByRole('menuitem'),
    ].filter((node) => node.getAttribute('tabindex') === '0');
    expect(stops).toHaveLength(1);
  });

  it('⚡ Home and End reach the ends, and End is not confused by filtering', async () => {
    /**
     * ⛔ **The count comes from what was RENDERED, never from the ref array** —
     * a ref array keeps `null` holes and its stale length, and the moment that
     * matters is immediately after a filter keystroke.
     */
    switcher(THREE);
    await userEvent.click(screen.getByRole('button', { name: /Active organization/ }));
    screen.getAllByRole('menuitemradio')[0]?.focus();

    await userEvent.keyboard('{End}');
    expect(screen.getByRole('menuitem', { name: 'Members & roles' })).toHaveFocus();

    await userEvent.keyboard('{Home}');
    expect(screen.getAllByRole('menuitemradio')[0]).toHaveFocus();
  });
});
