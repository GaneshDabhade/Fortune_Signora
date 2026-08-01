'use client';

import { Building2 } from 'lucide-react';
import Link from 'next/link';

import { EmptyState } from '@/components/ui';

/**
 * Signed in, and belonging to nowhere.
 *
 * **The state every brand-new account is in**, and until M12.3 the state that
 * rendered a heading and blank space. Every business page tested `isLoading`,
 * `isError` and `data`, and with no workspace the query is disabled — so all
 * three are falsy and none of the branches fired. A page that renders nothing
 * is indistinguishable from a broken one, and this is the first thing somebody
 * sees before they have done anything wrong (**D36**).
 *
 * ### Why this is not one of the existing empty states
 *
 * *"No accounts need your attention"* and *"you are not in a workspace"* are
 * different sentences with different next actions, and only the second one
 * tells a reader why the screen is empty. Reusing the first would be a
 * confident, wrong answer — the failure mode this product exists to avoid.
 *
 * ### Why it lives outside `components/ui`
 *
 * It carries product copy about tenancy rather than a reusable primitive, on
 * the same terms as `components/intelligence/`: **composed from the design
 * system, never added to it.**
 */
export function NoWorkspace() {
  return (
    <EmptyState
      icon={Building2}
      title="You are not in a workspace yet"
      description="A workspace is where your accounts, evidence and decisions live — and it is the boundary Signora keeps every customer's data inside. Create one, or ask a colleague to add you to theirs."
      action={
        <Link
          href="/settings"
          className="rounded text-sm font-medium text-accent underline decoration-border underline-offset-4 transition-colors hover:decoration-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
        >
          Create a workspace
        </Link>
      }
    />
  );
}
