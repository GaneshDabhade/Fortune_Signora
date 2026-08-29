/**
 * 🔴 **[B-245](../../../docs/BUGS.md) — which organization a person lands in
 * when they have several and have chosen none.**
 *
 * ## ⛔ The default was *the newest*, and nothing could undo it
 *
 * 📁 **`repositories.py:81`** — *"apply **newest-first** keyset ordering"* —
 * and the provider ended `return isStillAMember ? stored : first.id`. ⚡ **So
 * every organization anybody created became the default for every browser of
 * theirs holding no stored choice**, and ⛔ **nothing in the product deletes an
 * organization**, so the effect was permanent.
 *
 * ⚠️ **Measured cost, in one session**: six organizations accumulated and the
 * suite's account-backed journeys began failing on `main a[href^="/accounts/"]`
 * not found — **the attention list of an empty organization.**
 *
 * ## ✅ The rules are the design's, and [C-299](../../../docs/LANE_COORDINATION.md)
 * is why they are not this lane's to invent
 *
 * 📁 C-299 — *"which organization a person lands in"* — was **`CLOSED` by Lane
 * C on 2026-08-12** and **folded into
 * `Fortune Signora Workspace Chooser.dc.html`**, whose §02 is an ordered list
 * of eight. ⛔ **Four of them decide this walk**, and this file asserts each in
 * the order the document gives, **including the two it cannot ship** and why.
 */
import { render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const useWorkspaces = vi.hoisted(() => vi.fn());
const segments = vi.hoisted(() => vi.fn());

vi.mock('@/lib/query/hooks', () => ({
  useWorkspaces,
  useInvalidateWorkspaceScope: () => vi.fn(),
}));
vi.mock('next/navigation', () => ({ useSelectedLayoutSegments: segments }));

const { WorkspaceProvider, useWorkspaceContext, lastUsedWorkspaceId, selectWorkspace } =
  await import('@/lib/state/workspace-provider');

const KEY = 'signora.activeWorkspaceId';

/**
 * ⛔ **Newest first, exactly as the API orders them.** ⚠️ **A fixture in any
 * other order would make `workspaces[0]` look harmless**, and the whole defect
 * is which end of this list the old code reached for.
 */
const NEWEST = { id: 'w-newest', name: 'Scratch org', created_at: '2026-08-20T00:00:00Z' };
const OLDEST = { id: 'w-oldest', name: 'Northwind', created_at: '2024-01-01T00:00:00Z' };

function Probe() {
  const { activeWorkspace } = useWorkspaceContext();
  return <span data-testid="active">{activeWorkspace?.id ?? 'none'}</span>;
}

function mount(items: readonly { id: string; name: string }[]) {
  useWorkspaces.mockReturnValue({ data: { items }, isLoading: false, error: null });
  return render(
    <WorkspaceProvider>
      <Probe />
    </WorkspaceProvider>,
  );
}

const active = () => screen.getByTestId('active').textContent;

beforeEach(() => {
  window.localStorage.clear();
  segments.mockReturnValue([]);
});
afterEach(() => vi.clearAllMocks());

describe('🔴 rule 7 — with several memberships and no last-used, nothing is chosen', () => {
  it('⛔ does NOT fall to the newest organization', async () => {
    /**
     * 🔴 **The defect, stated as the assertion that catches it.** ⛔ **Not
     * `toBe('none')` alone** — that would pass on a provider that had simply
     * failed to resolve anything. ⚡ **Both are asserted**: nothing is
     * selected, *and* the thing that used to be selected specifically is not.
     */
    mount([NEWEST, OLDEST]);

    await waitFor(() => expect(active()).toBe('none'));
    expect(active()).not.toBe(NEWEST.id);
  });

  it('⛔ and does not silently pick the oldest either', async () => {
    // ⚠️ **A guard that only forbade `[0]` would pass on `[length - 1]`**,
    // which is the same invention wearing the other end of the list.
    mount([NEWEST, OLDEST]);

    await waitFor(() => expect(active()).toBe('none'));
    expect(active()).not.toBe(OLDEST.id);
  });
});

describe('✅ rule 6 — exactly one membership is entered without asking', () => {
  it('enters it, because there is nothing to choose', async () => {
    // 📁 *"No picker, no confirmation, no strip."* ⛔ Refusing to select here
    // would send somebody to a chooser holding one row.
    mount([OLDEST]);

    await waitFor(() => expect(active()).toBe(OLDEST.id));
  });
});

describe('✅ rule 4 — the last used on this device, when it is still a membership', () => {
  it('enters the stored organization ahead of any list position', async () => {
    // ⚡ **Stored is the OLDEST and the list leads with the newest**, so a
    // provider reading position would fail this and one reading the key passes.
    window.localStorage.setItem(KEY, OLDEST.id);

    mount([NEWEST, OLDEST]);

    await waitFor(() => expect(active()).toBe(OLDEST.id));
  });

  it('⛔ a stored id that is no longer a membership selects nothing', async () => {
    /**
     * ⚠️ **A hint, never a grant.** 📁 The provider's standing rule: the
     * stored id *"is validated against the list the API returned, so a
     * tampered value selects nothing rather than scoping the UI to a
     * workspace the caller is not a member of."*
     *
     * ⛔ **And it must not fall to the newest either** — falling through to a
     * guess is the defect one step along.
     */
    window.localStorage.setItem(KEY, 'w-left-last-year');

    mount([NEWEST, OLDEST]);

    await waitFor(() => expect(active()).toBe('none'));
  });
});

describe('✅ rule 1 — the URL beats every stored preference', () => {
  it('enters the workspace the link names', async () => {
    // 📁 *"An explicit request always beats any stored preference — this is
    // the rule that makes links work."*
    window.localStorage.setItem(KEY, OLDEST.id);
    segments.mockReturnValue(['w', NEWEST.id, 'home']);

    mount([NEWEST, OLDEST]);

    await waitFor(() => expect(active()).toBe(NEWEST.id));
  });

  it('⛔ but only for a workspace this person is a member of', async () => {
    /**
     * ⚡ **The segment is INPUT, never a grant**, and it passes the same
     * membership check the stored id always did. ⛔ **A member of nothing
     * typing another organization's id lands where a non-member lands** —
     * here, at the chooser, because two memberships remain ambiguous.
     */
    segments.mockReturnValue(['w', 'w-somebody-elses', 'home']);

    mount([NEWEST, OLDEST]);

    await waitFor(() => expect(active()).toBe('none'));
  });
});

describe('🔴 the persistence contract — last-used is written on ENTRY, not only on a switch', () => {
  it('records a workspace reached by deep link', async () => {
    /**
     * 📁 The design's persistence table: *"written on **every successful
     * entry** and on every switch."*
     *
     * ⛔ **It was written only by `setActiveWorkspace`**, so somebody who
     * arrived by a shared link had entered an organization nothing recorded —
     * ⚡ **and returning later with no URL fell to rule 7 and was asked to
     * choose the organization they had been working in that morning.**
     * **Rule 4 cannot fire on a producer nothing writes.**
     */
    segments.mockReturnValue(['w', NEWEST.id, 'home']);

    mount([NEWEST, OLDEST]);

    await waitFor(() => expect(lastUsedWorkspaceId()).toBe(NEWEST.id));
  });

  it('⛔ and writes nothing at all while the choice is still the person’s', async () => {
    // ⚡ **Rule 7 must not record a decision nobody made.** A key written here
    // would make the next visit skip the chooser and enter a guess.
    mount([NEWEST, OLDEST]);

    await waitFor(() => expect(active()).toBe('none'));
    expect(lastUsedWorkspaceId()).toBeNull();
  });
});

/**
 * 🔴 **The half no component test found, and the browser did.**
 *
 * ⛔ **The walk used to run in a `useEffect`.** ⚡ **So between the membership
 * list arriving and the effect running there was ONE render carrying
 * *"settled, and nothing selected"*** — **which is exactly rule 7's shape**,
 * and the shell acts on rule 7 by navigating.
 *
 * ⚠️ **Measured in Chromium against the running product**: choose an
 * organization at `/workspaces`, then open `/accounts` — **and land back on
 * `/workspaces`**, with a perfectly good last-used in `localStorage`. **Every
 * assertion in this file was green.**
 *
 * ✅ **A derivation cannot race itself**, and this asserts the property rather
 * than the implementation: **no render may report *nothing selected* once the
 * list has arrived and a valid choice exists.**
 */
describe('🔴 no render may say "settled, and nothing selected" when there is a choice', () => {
  it('⛔ activeWorkspace is never null on ANY render, not merely the last one', async () => {
    const seen: (string | null)[] = [];
    function Recorder() {
      const { activeWorkspace, isLoading } = useWorkspaceContext();
      if (!isLoading) seen.push(activeWorkspace?.id ?? null);
      return null;
    }

    window.localStorage.setItem(KEY, OLDEST.id);
    useWorkspaces.mockReturnValue({
      data: { items: [NEWEST, OLDEST] },
      isLoading: false,
      error: null,
    });

    render(
      <WorkspaceProvider>
        <Recorder />
      </WorkspaceProvider>,
    );

    await waitFor(() => expect(seen.length).toBeGreaterThan(0));
    // ⛔ **`toContain(null)` is what the effect-based version failed**, and it
    // failed on the FIRST entry — the render before the effect had run.
    expect(seen, 'a render reported no organization while one was stored').not.toContain(null);
  });
});

/**
 * 📁 **The design asks for the function by name and by shape**: *"`selectWorkspace(url,
 * memberships, prefs)` is pure, ordered exactly as section 2, and makes no
 * network call. **Eight branches, eight fixtures.**"*
 *
 * ⚠️ **Five branches, not eight, and the three absent ones are named** — rules
 * 2, 3 and 5 have no producer ([C-1582](../../../docs/LANE_COORDINATION.md)),
 * and the design's own U-02 rules that rules 1, 2, 4–8 ship without rule 3.
 */
describe('📁 selectWorkspace — the ordering, asserted directly', () => {
  const BOTH = [NEWEST, OLDEST];

  it('rule 1 beats a switch made in this tab', () => {
    // ⚡ **A link names a destination and the person followed it**, so it
    // outranks even an explicit choice made earlier in the same tab.
    expect(
      selectWorkspace({
        workspaces: BOTH,
        fromUrl: OLDEST.id,
        chosen: NEWEST.id,
        lastUsed: NEWEST.id,
      }),
    ).toBe(OLDEST.id);
  });

  it('a switch in this tab beats last-used', () => {
    expect(
      selectWorkspace({ workspaces: BOTH, fromUrl: null, chosen: NEWEST.id, lastUsed: OLDEST.id }),
    ).toBe(NEWEST.id);
  });

  it('rule 4 beats rule 7', () => {
    expect(
      selectWorkspace({ workspaces: BOTH, fromUrl: null, chosen: null, lastUsed: OLDEST.id }),
    ).toBe(OLDEST.id);
  });

  it('rule 6 — a sole membership needs no stored anything', () => {
    expect(
      selectWorkspace({ workspaces: [OLDEST], fromUrl: null, chosen: null, lastUsed: null }),
    ).toBe(OLDEST.id);
  });

  it('rule 7 — and it is null, which is an answer', () => {
    expect(
      selectWorkspace({ workspaces: BOTH, fromUrl: null, chosen: null, lastUsed: null }),
    ).toBeNull();
  });

  it('⛔ every candidate passes the SAME membership check', () => {
    /**
     * ⚠️ **All three inputs are non-members here**, so a walk that trusted any
     * one of them would return it. ⛔ **The URL segment looks like routing and
     * is input**; the stored id looks like state and is input; a stale
     * `chosen` survives a membership ending.
     */
    expect(
      selectWorkspace({
        workspaces: BOTH,
        fromUrl: 'w-not-mine',
        chosen: 'w-left',
        lastUsed: 'w-revoked',
      }),
    ).toBeNull();
  });

  it('⛔ and an empty membership list selects nothing rather than throwing', () => {
    // 📁 Rule 8's territory — `/workspaces/none`, and the walk simply has
    // nothing to return.
    expect(
      selectWorkspace({ workspaces: [], fromUrl: 'w-1', chosen: 'w-1', lastUsed: 'w-1' }),
    ).toBeNull();
  });
});
