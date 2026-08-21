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
 * *"No accounts need your attention"* and *"you do not belong to an
 * organization"* are different sentences with different next actions, and only
 * the second one tells a reader why the screen is empty. Reusing the first
 * would be a confident, wrong answer — the failure mode this product exists to
 * avoid.
 *
 * ### The copy said "workspace" until ADR-0034
 *
 * *"A workspace is where your accounts, evidence and decisions live — and it
 * is the boundary Signora keeps every customer's data inside."* Every word of
 * that was true, and it explained **Signora's tenancy model to a salesperson**
 * at the first moment they ever saw the product. The component keeps its
 * internal name; the sentence a customer reads does not.
 *
 * ### Why it lives outside `components/ui`
 *
 * It carries product copy rather than a reusable primitive, on the same terms
 * as `components/intelligence/`: **composed from the design system, never
 * added to it.**
 */
export function NoWorkspace() {
  return (
    <EmptyState
      icon={Building2}
      title="You are not part of an organization yet"
      description="Your organization is your company on Signora — where its accounts, evidence and decisions live. Create one, or ask a colleague to add you to theirs."
      action={
        <Link
          href="/settings"
          className="rounded text-sm font-medium text-accent underline decoration-border underline-offset-4 transition-colors hover:decoration-accent "
        >
          Create an organization
        </Link>
      }
    />
  );
}
