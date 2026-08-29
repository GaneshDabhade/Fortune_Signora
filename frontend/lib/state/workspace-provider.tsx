'use client';

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

import { useSelectedLayoutSegments } from 'next/navigation';

import type { Workspace } from '@/lib/api/types';
import { useInvalidateWorkspaceScope, useWorkspaces } from '@/lib/query/hooks';

const ACTIVE_WORKSPACE_KEY = 'signora.activeWorkspaceId';

/**
 * 🔴 **The last workspace this browser was in, or `null`** — 📁 the
 * Authenticated Entry document's rules **12, 13 and 14**: *"several
 * memberships, last-used recorded and healthy → enter the last used"*, *"no
 * last-used → the chooser"*, *"last-used unavailable → fall through and say
 * why"*.
 *
 * ⚡ **Published because the entry engine needs the fact and must not
 * re-declare the key.** 📁 [C-1522](../../../docs/LANE_COORDINATION.md) recorded
 * the engine passing `null` for exactly this reason — *"re-declaring the string
 * here would be two authoritative representations of one fact"* — ⛔ **which
 * made rule 13 unreachable and rule 12 indistinguishable from rule 11.** ✅ **One
 * owner, one key, one reader.**
 *
 * ⛔ **A HINT and never a grant.** The provider validates it against the
 * membership list the API returned, `resolveWorkspace` validates it again, and
 * the server re-verifies membership on every request regardless. **A tampered
 * value selects nothing.**
 *
 * ⚠️ **`null` on the server.** There is no `window` during a render on the
 * server, and *"nothing stored"* is the honest answer there — rule 13's case,
 * which shows the chooser rather than guessing.
 */
export function lastUsedWorkspaceId(): string | null {
  if (typeof window === 'undefined') return null;
  return window.localStorage.getItem(ACTIVE_WORKSPACE_KEY);
}

/**
 * 🔴 **The only writer of the last-used key** — 📁 the Workspace Chooser's
 * persistence table, *"written on every successful entry and on every
 * switch."*
 *
 * ⛔ **One implementation, two occasions**, which is the distinction
 * [§2](../../../CLAUDE.md) draws: entry records what a person reached, a
 * switch records what they chose, and **both are the same fact about the same
 * device.** ⚡ **Two `setItem` calls in two files would be two representations
 * of one rule**, and the one nobody maintained would be the one that drifted.
 */
function rememberLastUsed(workspaceId: string): void {
  window.localStorage.setItem(ACTIVE_WORKSPACE_KEY, workspaceId);
}

/**
 * 🔴 **Which organization this person is in — the Workspace Chooser's §02,
 * ordered exactly as the document orders it.**
 *
 * 📁 **The design asks for this shape by name**: *"`selectWorkspace(url,
 * memberships, prefs)` is **pure**, ordered exactly as section 2, and makes no
 * network call. Eight branches, eight fixtures."*
 *
 * ⛔ **Pure, and that is load-bearing rather than tidy.** ⚡ **The walk used to
 * run in an effect**, so between the membership list arriving and the effect
 * running there was one render carrying *"settled, and nothing selected"* —
 * **which is indistinguishable from rule 7**, and the shell acted on it.
 * 📁 [B-245](../../../docs/BUGS.md).
 *
 * ## 📁 The rules this ships, and the three it does not
 *
 * | | |
 * |---|---|
 * | **1** `WS_FROM_URL` | ✅ *"An explicit request always beats any stored preference — this is the rule that makes links work."* |
 * | **4** `WS_LAST_USED` | ✅ *"The most common path for anyone with several memberships."* |
 * | **6** `WS_SOLE` | ✅ *"Nothing to choose."* |
 * | **7** `WS_AMBIGUOUS` | ✅ ⛔ **`null`, and it is the ANSWER rather than the absence of one** |
 * | **3** `WS_PINNED` | ⛔ **No producer, and the design says so** — U-02: *"ship rules 1, 2, 4–8 only… selection degrades cleanly to last-used"* |
 * | **2** · **5** | ⛔ **No producer** — `GET /workspaces` carries no standing. 📁 [C-1582](../../../docs/LANE_COORDINATION.md) |
 *
 * ⚠️ **Every candidate passes the same membership check.** ⛔ **The URL segment
 * and the stored id are both INPUT, never a grant** — a tampered value selects
 * nothing, and the server re-verifies membership on every request regardless
 * ([§13](../../../CLAUDE.md)).
 */
export function selectWorkspace(input: {
  readonly workspaces: readonly { readonly id: string }[];
  /** The `/w/:workspace` segment, if this tab is on one. */
  readonly fromUrl: string | null;
  /** An explicit switch made in this tab. ⛔ Not a preference; a fact. */
  readonly chosen: string | null;
  /** `sig.ws.lastUsed`'s value, per device. */
  readonly lastUsed: string | null;
}): string | null {
  const isAMember = (id: string | null): id is string =>
    id !== null && input.workspaces.some((w) => w.id === id);

  // ① 📁 **Rule 1** — and it beats everything below it, including a switch
  //    made in this tab: a link names a destination and the person followed it.
  if (isAMember(input.fromUrl)) return input.fromUrl;
  // ⚡ **A choice already made HERE.** ⛔ Without it, a list refetch would
  //    re-run the walk and could move somebody mid-session.
  if (isAMember(input.chosen)) return input.chosen;
  // ② 📁 **Rule 4** — last used on this device, when it is still a membership.
  if (isAMember(input.lastUsed)) return input.lastUsed;
  // ③ 📁 **Rule 6** — *"exactly one active membership. Nothing to choose."*
  if (input.workspaces.length === 1) return input.workspaces[0]?.id ?? null;
  // ④ 📁 **Rule 7** — ⛔ **inventing one here is the defect B-245 is.**
  return null;
}

interface WorkspaceContextValue {
  workspaces: Workspace[];
  activeWorkspace: Workspace | null;
  setActiveWorkspace: (workspaceId: string) => void;
  isLoading: boolean;
  error: Error | null;
}

const WorkspaceContext = createContext<WorkspaceContextValue | null>(null);

/**
 * The active workspace, and the list to choose from.
 *
 * The stored id is a **hint, never a grant**. It is validated against the
 * list the API returned, so a tampered localStorage value selects nothing
 * rather than scoping the UI to a workspace the caller is not a member of.
 * The server re-verifies membership on every request regardless
 * (18-authentication.md) — this only keeps the client honest about what it
 * displays.
 */
export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const { data, isLoading, error } = useWorkspaces();
  const invalidateScope = useInvalidateWorkspaceScope();
  const [chosen, setChosen] = useState<string | null>(null);

  /**
   * 🔴 **The URL segment, and it is EXACTLY as untrusted as the stored id** —
   * [TASK-1438](../../../docs/BACKLOG.md).
   *
   * 📁 **The design's route is `/w/:workspace/home`**, and the row's named risk
   * is *"treating the URL as a grant because it looks like routing rather than
   * input."* ⛔ **It is input.** ⚡ **The provider's existing rule carries over
   * unchanged and is what makes this safe**: *"the stored id is a hint, never
   * a grant… validated against the list the API returned."*
   *
   * ✅ **So a member of nothing typing another workspace's id lands where a
   * non-member lands**, because the segment is filtered by the same
   * membership check the stored id always was. 📁 **Server-side
   * re-verification is unchanged and is still the control**
   * ([§13](../../../CLAUDE.md)).
   */
  // ⚠️ **`?? []` is not defensive noise.** Outside a layout context — which is
  // every component test that renders the provider directly — Next returns
  // `null` here, and reading `[0]` off it throws. ⛔ **A provider that only
  // works inside a route tree is a provider no test can mount.**
  const segment = useSelectedLayoutSegments() ?? [];
  const fromUrl = segment[0] === 'w' ? (segment[1] ?? null) : null;

  const workspaces = useMemo(() => data?.items ?? [], [data]);

  /**
   * 🔴 **[B-245](../../../docs/BUGS.md) — the default was *the newest
   * organization*, and nothing in the product could ever undo it.**
   *
   * ⛔ **This ended `return isStillAMember ? stored : first.id`.** 📁 The list
   * is newest-first (`repositories.py:81`, *"apply newest-first keyset
   * ordering"*), **so every organization a person created became the default
   * for every browser of theirs that had no stored choice** — ⚡ **and nothing
   * in the product deletes an organization**, so the effect was permanent.
   *
   * ⚠️ **A salesperson who creates a second organization to try something out
   * was put into it on every new device, ahead of the one holding their book
   * of business.**
   *
   * ## ✅ The rules, and they are the Workspace Chooser's own §02
   *
   * 📁 [C-299](../../../docs/LANE_COORDINATION.md) was `CLOSED` on 2026-08-12
   * and **folded into `Fortune Signora Workspace Chooser.dc.html`**, so the
   * default is specified rather than open. **Four of its eight rules decide
   * this branch:**
   *
   * | | |
   * |---|---|
   * | **1** `WS_FROM_URL` | *"An explicit request always beats any stored preference — this is the rule that makes links work."* |
   * | **4** `WS_LAST_USED` | *"The most common path for anyone with several memberships."* |
   * | **6** `WS_SOLE` | *"Nothing to choose."* |
   * | **7** `WS_AMBIGUOUS` | *"The system genuinely cannot decide… the chooser is mandatory here and only here."* |
   *
   * ⛔ **Rule 7 is what `first.id` was standing in for, and it is not a
   * fallback — it is a REFUSAL to guess.** 📁 *"Automatic routing is the
   * default… the chooser is mandatory in exactly one case."*
   *
   * ⚠️ **Rule 3 (`prefs.defaultWorkspace`) is deliberately absent**, and the
   * design says so itself — 📁 **U-02**: *"Rule 3 reads `prefs.defaultWorkspace`,
   * which does not exist. This document does not invent it as shipped
   * capability… ship rules 1, 2, 4–8 only. Rule 3 is a no-op until the field
   * exists, and selection degrades cleanly to last-used."*
   *
   * ⚠️ **Rule 5's health fall-through is absent for the same reason** — `GET
   * /workspaces` returns `id · name · created_at · updated_at` and **no
   * standing**, which is why `lib/entry/observed.ts` declares membership
   * standing UNOBSERVED. 📁 [C-1582](../../../docs/LANE_COORDINATION.md)
   * records the producer gap. ⛔ **Not simulated**: a workspace guessed
   * healthy is exactly the fabricated continuity the design forbids.
   */
  /**
   * ⛔ **Read ONCE, at mount, and never during a render that could disagree
   * with the last one.** ⚠️ **`null` on the server** — there is no `window`,
   * and *"nothing stored"* is the honest answer there.
   */
  const [storedAtMount] = useState<string | null>(() =>
    typeof window === 'undefined' ? null : window.localStorage.getItem(ACTIVE_WORKSPACE_KEY),
  );

  /**
   * 🔴 **Derived during the render, NOT in an effect** — and that is
   * [B-245](../../../docs/BUGS.md)'s second half, which the browser found and
   * no component test could.
   *
   * ⛔ **The walk used to live in a `useEffect`, so between the list arriving
   * and the effect running there was a render carrying *"settled, and nothing
   * selected"*** — ⚡ **which is indistinguishable from rule 7.** ⚠️ **The
   * shell read that render and sent a person who had a perfectly good stored
   * choice back to the chooser**, on every navigation. **Measured in the
   * browser: choose an organization, go to `/accounts`, land on
   * `/workspaces` again.**
   *
   * ✅ **A derivation cannot race itself.** 📁 And the design already asked
   * for exactly this shape: *"`selectWorkspace(url, memberships, prefs)` is
   * **pure**, ordered exactly as section 2, and makes no network call."*
   *
   * ⚡ **`chosen` remains state** because an explicit switch is a fact about
   * this tab that no input carries — ⛔ **but it is an INPUT to the walk
   * rather than the walk's only output**, so it can never be stale with
   * respect to a list that has since changed.
   */
  const activeId = selectWorkspace({
    workspaces,
    fromUrl,
    chosen,
    lastUsed: storedAtMount,
  });

  /**
   * 🔴 **📁 The persistence table: last-used is *"written on every successful
   * entry and on every switch."*** ⛔ **It was written only on a switch.**
   *
   * ⚠️ **So a person who arrived by deep link had entered a workspace that was
   * never recorded** — and returning later with no URL fell to rule 7 and was
   * asked to choose an organization they had been working in that morning.
   * ⚡ **Rule 4 cannot fire on a producer nothing writes.**
   */
  useEffect(() => {
    if (activeId !== null) rememberLastUsed(activeId);
  }, [activeId]);

  const setActiveWorkspace = useCallback(
    (workspaceId: string) => {
      setChosen((previous) => {
        // Drop the outgoing workspace's cached data. Leaving it would show
        // one tenant's rows under another tenant's header until each query
        // happened to go stale.
        if (previous && previous !== workspaceId) void invalidateScope(previous);
        return workspaceId;
      });
      // ⛔ **Synchronously, and NOT left to the effect above.** 📁 The
      // contract is *"last-used is written on activation of a switch, BEFORE
      // the route change, so a failed switch still records intent"* — ⚡ and
      // an effect runs after the render, by which time the caller has already
      // pushed. **One writer, two occasions.**
      rememberLastUsed(workspaceId);
    },
    [invalidateScope],
  );

  const activeWorkspace = workspaces.find((w) => w.id === activeId) ?? null;

  return (
    <WorkspaceContext.Provider
      value={{
        workspaces,
        activeWorkspace,
        setActiveWorkspace,
        isLoading,
        error: error as Error | null,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspaceContext(): WorkspaceContextValue {
  const context = useContext(WorkspaceContext);
  if (!context)
    throw new Error('useWorkspaceContext must be used within WorkspaceProvider');
  return context;
}
