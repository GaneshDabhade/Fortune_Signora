'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

import { getOnboarding, type OnboardingRun } from '@/lib/api/onboarding';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';

const DISMISSED_KEY = 'signora.onboardingBannerDismissed';

/**
 * **The resume banner** — [TASK-469](../../../docs/BACKLOG.md), and the
 * design's own mechanism for the person who left part-way through.
 *
 * > *"Skip states the cost, once. The dialog says what gets worse in product
 * > terms and lets them leave. **No second ask, no guilt copy — the resume
 * > banner does the remaining work quietly.**"*
 *
 * ### 🔴 Quietly is a requirement, not a tone
 *
 * ⛔ **Dismissible, and the dismissal sticks.** A banner that returned on the
 * next page load would be the *second ask* the design forbids, one screen
 * later and more often.
 *
 * ⛔ **`role="status"`, never `alert`.** *"Progress changes and autosave
 * confirmations are status messages, not alerts — they do not interrupt"*
 * (4.1.3). An unfinished setup is not an emergency.
 *
 * ### ⚡ It is also onboarding's only entrance, and that is deliberate
 *
 * **Nothing else in the product links to `/onboarding`.** A person with a
 * finished run has no reason to go back, and a person with none has nothing
 * to resume — so an entrance that was always visible would be a permanent
 * offer to continue something that does not exist. **`infra/reachability.py`
 * is what made this explicit**: the routes shipped unreachable and the check
 * refused them, which is exactly the defect it exists to catch.
 */
export function ResumeOnboarding() {
  const { activeWorkspace } = useWorkspaceContext();
  const workspaceId = activeWorkspace?.id ?? null;
  const [run, setRun] = useState<OnboardingRun | null>(null);
  const [dismissed, setDismissed] = useState(true);

  useEffect(() => {
    setDismissed(window.localStorage.getItem(DISMISSED_KEY) === 'true');
  }, []);

  useEffect(() => {
    if (workspaceId === null) return;
    let live = true;

    getOnboarding(workspaceId)
      .then((loaded) => {
        if (live) setRun(loaded);
      })
      // ⛔ **A 404 is the ordinary case, not an error.** Most workspaces have
      // no run, and rendering a failure for the majority state would make
      // this banner the thing that is broken.
      .catch(() => undefined);

    return () => {
      live = false;
    };
  }, [workspaceId]);

  if (dismissed || run === null || run.finished_at !== null) return null;

  const dismiss = () => {
    window.localStorage.setItem(DISMISSED_KEY, 'true');
    setDismissed(true);
  };

  return (
    <div
      role="status"
      className="flex flex-wrap items-center gap-3 border-b border-border-soft bg-surface-sunken px-5 py-2.5 text-sm"
    >
      <span className="text-content-muted">
        Your setup is unfinished. Signora works better once it knows what you are trying to fix.
      </span>
      <Link
        href="/onboarding"
        className="rounded font-medium text-accent underline decoration-border underline-offset-4 transition-colors hover:decoration-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
      >
        Finish setting up
      </Link>
      <button
        type="button"
        onClick={dismiss}
        className="ml-auto rounded text-content-subtle underline underline-offset-4 transition-colors hover:text-content focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
      >
        Not now
      </button>
    </div>
  );
}
