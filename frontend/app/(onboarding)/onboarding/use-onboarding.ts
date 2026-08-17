'use client';

import { useCallback, useEffect, useState } from 'react';

import type { OnboardingRun, OnboardingStep } from '@/lib/api/onboarding';
import { advanceOnboarding, startOnboarding } from '@/lib/api/onboarding';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';

/**
 * The run, loaded once per step and re-read from every save.
 *
 * ⚡ **The server's copy is the only copy.** Every mutation returns the whole
 * run and this replaces its state with it, so a screen can never drift from
 * what was persisted — which is the property that makes *"everything saved as
 * you go"* checkable rather than asserted ([§2](../../../../CLAUDE.md), truth
 * has exactly one authoritative representation).
 *
 * ⛔ **`start` rather than `get` on mount, and it is deliberate.** Starting is
 * idempotent and returns the run in progress, so one call covers both the
 * first arrival and the return from the resume banner. **A `get` would 404 the
 * first time and need a second call to recover**, which is a race on the
 * screen a person sees least often and trusts most.
 */
export interface OnboardingState {
  readonly run: OnboardingRun | null;
  readonly workspaceId: string | null;
  readonly error: string | null;
  /** True while the first load is in flight. **Not shared with saving** — a
   * screen that dimmed itself on every autosave would flicker on blur. */
  readonly isLoading: boolean;
  readonly isSaving: boolean;
  /** Runs a mutation and adopts whatever run comes back. */
  readonly save: (mutate: (workspaceId: string) => Promise<OnboardingRun>) => Promise<void>;
  /** Advance, which is what actually completes the step being left. */
  readonly advance: (step: OnboardingStep) => Promise<void>;
}

export function useOnboarding(): OnboardingState {
  const { activeWorkspace } = useWorkspaceContext();
  const workspaceId = activeWorkspace?.id ?? null;
  const [run, setRun] = useState<OnboardingRun | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (workspaceId === null) {
      // 🔴 **Otherwise this screen loads forever.** ⛔ `isLoading` starts
      // `true` and only ever cleared in the `finally` below, which is gated on
      // having a workspace — so **somebody arriving without an active
      // organization saw *"Loading your setup…"* with nothing behind it and no
      // way out.**
      //
      // ⚡ **Found in a headed run, not by a gate** ([B-277](../../../../docs/BUGS.md)):
      // every test supplies a workspace, so the one path where the product
      // hangs is the one path nothing exercised.
      //
      // ✅ **Stops loading and says so.** 📁 [P-A](../../../../docs/DOMAIN_DISCOVERY_REGISTER.md)
      // — a read that cannot happen must not render as a read still happening,
      // any more than as an empty result.
      setIsLoading(false);
      setError('We could not tell which organization you are setting up. Refresh to try again.');
      return;
    }
    setIsLoading(true);
    setError(null);
    let live = true;

    startOnboarding(workspaceId)
      .then((loaded) => {
        if (live) setRun(loaded);
      })
      .catch(() => {
        // ⛔ **A failed read renders as an error, never as an empty form**
        // — P-A, and the shape C-226 found six times on one screen. An empty
        // form here would silently discard answers the person had given.
        if (live) setError('We could not load your setup. Refresh to try again.');
      })
      .finally(() => {
        if (live) setIsLoading(false);
      });

    return () => {
      live = false;
    };
  }, [workspaceId]);

  const save = useCallback(
    async (mutate: (id: string) => Promise<OnboardingRun>) => {
      if (workspaceId === null) return;
      setIsSaving(true);
      setError(null);
      try {
        setRun(await mutate(workspaceId));
      } catch {
        // *"Network drop mid-step: answers are held locally and re-submitted
        // on reconnect."* ⚠️ **The holding is milestone 2's**; this states the
        // failure rather than pretending the save happened, which is the half
        // that must never be wrong.
        setError('That did not save. Check your connection and try again.');
      } finally {
        setIsSaving(false);
      }
    },
    [workspaceId],
  );

  const advance = useCallback(
    async (step: OnboardingStep) => {
      await save((id) => advanceOnboarding(id, step));
    },
    [save],
  );

  return { run, workspaceId, error, isLoading, isSaving, save, advance };
}
