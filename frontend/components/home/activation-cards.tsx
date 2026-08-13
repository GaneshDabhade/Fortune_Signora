/**
 * **Activation's two blocking steps** — [TASK-1424](../../../docs/BACKLOG.md),
 * against 📁 `Fortune Signora Home.dc.html` §*Activation*.
 *
 * ## ⛔ Two of the three, and the third is named rather than half-built
 *
 * 🔴 **`invite-the-team` is NOT here.** 📁 It is the only non-blocking card, so
 * it is the only one the design lets a person skip — and *"skip state is per
 * person, on the server, for 30 days. **Nothing about activation lives in
 * localStorage.**"* ⛔ **No endpoint holds that**, and a skip written to a
 * browser is a skip a person loses when they change machine. ✅ **The two
 * blocking cards cannot be dismissed at all**, so they need no such store and
 * ship complete.
 *
 * ## 📁 What Home is forbidden to do here
 *
 * ⛔ ***"Exactly one primary per card, opening the owning module's flow. Home
 * never embeds a connection wizard or an OAuth step."*** ⚡ **So both primaries
 * are links into `/connections`** — the Connection Center owns the flow, and
 * this surface only says which step is next.
 *
 * ⚠️ **The route is `/settings/connections`, and the first version said
 * `/connections`** — ⛔ **a path that does not exist.** ✅ **`route-map.test.ts`
 * caught it before it shipped**, which is the guard doing precisely what it was
 * written for: 📁 *"no route in the product links to a path that no longer
 * exists."* ⚡ **A Home card whose primary action 404s would be the
 * false-affordance class on the first screen a new customer sees.**
 */

'use client';

import Link from 'next/link';
import { Check } from 'lucide-react';

import { Card, CardBody, SkeletonText } from '@/components/ui';
import { StatedAbsence } from '@/components/feedback/stated-absence';
import { cn } from '@/lib/design/cn';
import {
  DEPENDENCY_REASON,
  hasWorkingCapability,
  primaryEnabled,
  type ActivationCardId,
} from '@/lib/home/activation';
import { correlationOf } from '@/lib/accounts/section-state';
import { useIntegrations } from '@/lib/query/hooks/integrations';
import { usePreferences, useSkipInvite } from '@/lib/query/hooks/preferences';
import { useWorkspaceMembers } from '@/lib/query/hooks/team';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';

/** 📁 The design's own words for each step, so the card says what the design
 * says rather than a paraphrase. */
const COPY: Record<
  'connect-a-crm' | 'connect-calls',
  { title: string; body: string; meta: string; action: string }
> = {
  'connect-a-crm': {
    title: 'Connect a CRM',
    body: 'Signora reads your accounts and open opportunities. Nothing is written back.',
    meta: 'About 4 minutes · needs admin consent',
    action: 'Connect',
  },
  'connect-calls': {
    title: 'Connect calls and calendar',
    // 📁 Verbatim from the design — it is the sentence that explains why this
    // step is not optional, and paraphrasing it would lose the argument.
    body: 'This is where the intelligence comes from. Without call data, Signora scores deals on CRM fields alone and cannot tell you why one is slipping.',
    meta: 'Zoom, Teams or Google Meet · about 4 minutes · needs admin consent',
    action: 'Connect',
  },
};

function useActivation() {
  const { activeWorkspace } = useWorkspaceContext();
  const systems = useIntegrations(activeWorkspace?.id ?? null);

  return {
    query: systems,
    complete: {
      'connect-a-crm': hasWorkingCapability(systems.data, 'crm_activity'),
      'connect-calls': hasWorkingCapability(systems.data, 'meetings'),
      // ⛔ **Not this component's card**, and it is present only so the
      // dependency and progress helpers see the whole set.
      'invite-the-team': false,
    } satisfies Record<ActivationCardId, boolean>,
  };
}

export function ConnectCrmCard() {
  return <Step id="connect-a-crm" />;
}

export function ConnectCallsCard() {
  return <Step id="connect-calls" />;
}

/**
 * 🔴 **The one activation card a person may put away** —
 * [TASK-1424](../../../docs/BACKLOG.md).
 *
 * 📁 ***"Signora scores relationships, so a workspace with one person in it
 * measures very little."*** ⚡ **Optional, and the design says so twice**: *"not
 * blocking · you can do this at any time from Team Management"*.
 *
 * ⛔ **Skipping hides it for thirty days and is reversible**, and **the server
 * holds both** — 📁 *"skip state is per person, on the server, for 30 days.
 * Nothing about activation lives in `localStorage`."*
 */
export function InviteTheTeamCard() {
  const { activeWorkspace } = useWorkspaceContext();
  const workspaceId = activeWorkspace?.id ?? null;
  const preferences = usePreferences(workspaceId);
  const skip = useSkipInvite(workspaceId);
  const members = useWorkspaceMembers(workspaceId);

  // ⛔ **Absent until the answer is known.** ⚡ Rendering while the preference is
  // unread would show a card somebody put away, on every slow connection —
  // 📁 [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md) one level up.
  if (preferences.data === undefined || preferences.data.invite_hidden) return null;

  // ⚡ **Completion is derived from the source of truth**, and the source is the
  // roster: 📁 *"a workspace of one measures little"*, so **this step is done
  // when somebody else is in it.**
  const done = (members.data?.items?.length ?? 1) > 1;

  return (
    <Card>
      <CardBody className="flex flex-col gap-2">
        <div className="flex items-center gap-2">
          <span
            aria-hidden
            className={cn(
              'flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-2xs font-semibold',
              done ? 'bg-success text-white' : 'border border-border text-content-subtle',
            )}
          >
            {done ? <Check className="h-3 w-3" /> : '3'}
          </span>
          <h3 className="text-sm font-semibold text-content">Invite the team</h3>
          <span className="text-2xs text-content-subtle">{done ? 'Complete' : 'Optional'}</span>
        </div>

        {/* ⚠️ **The design writes *"a workspace of one"* and this says
            *organization*, deliberately.** 📁 [ADR-0034]: *"a customer says
            organization, the platform says workspace"*, and the translation
            lives at the frontend edge — ⛔ **a design mock is not exempt from
            it**, and `vocabulary.test.tsx` caught this sentence before it
            shipped. */}
        <p className="text-sm leading-6 text-content-muted">
          Signora scores relationships, so an organization with one person in it measures very
          little.
        </p>
        <p className="text-2xs text-content-subtle">
          Not blocking — you can do this at any time from Team Management.
        </p>

        <div className="flex items-center gap-3">
          <Link
            href="/settings/team"
            className="w-fit rounded border border-border px-3 py-1.5 text-sm text-content hover:bg-surface-sunken focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
          >
            {done ? 'Manage the team' : 'Invite people'}
          </Link>

          {done ? null : (
            /* 📁 ***"'Skip for now' applies only to non-blocking cards."*** ⛔ It
               is absent from the two blocking steps by construction — they do
               not render this component. */
            <button
              type="button"
              onClick={() => skip.mutate(true)}
              disabled={skip.isPending}
              className="rounded text-sm text-content-subtle underline decoration-border underline-offset-4 hover:text-content focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent disabled:cursor-not-allowed"
            >
              Skip for now
            </button>
          )}
        </div>
      </CardBody>
    </Card>
  );
}

function Step({ id }: { id: 'connect-a-crm' | 'connect-calls' }) {
  const { query, complete } = useActivation();
  const copy = COPY[id];

  if (query.isError) {
    return (
      <Card>
        <CardBody>
          <StatedAbsence
            subject="which systems you have connected"
            reassurance="Nothing you have connected has been lost"
            {...(correlationOf(query.error) === undefined
              ? {}
              : { correlationId: correlationOf(query.error)! })}
          />
        </CardBody>
      </Card>
    );
  }

  if (query.isLoading) {
    return (
      <Card>
        <CardBody>
          <SkeletonText lines={3} />
        </CardBody>
      </Card>
    );
  }

  const done = complete[id];
  const enabled = primaryEnabled(id, complete);
  const blockedBy = enabled || done ? undefined : DEPENDENCY_REASON[id];

  return (
    <Card>
      <CardBody className="flex flex-col gap-2">
        <div className="flex items-center gap-2">
          {/* 📁 ***"A completed step keeps its line with a ✓… it never
              disappears — vanishing steps make people doubt they did them."***
              ⛔ So completion changes the mark, not the presence. */}
          <span
            aria-hidden
            className={cn(
              'flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-2xs font-semibold',
              done ? 'bg-success text-white' : 'border border-border text-content-subtle',
            )}
          >
            {done ? <Check className="h-3 w-3" /> : id === 'connect-a-crm' ? '1' : '2'}
          </span>
          <h3 className="text-sm font-semibold text-content">{copy.title}</h3>
          {done ? <span className="text-2xs text-success">Complete</span> : null}
        </div>

        <p className="text-sm leading-6 text-content-muted">{copy.body}</p>
        <p className="text-2xs text-content-subtle">{copy.meta}</p>

        {done ? (
          /* 📁 ***"…keeps a secondary action into the owning module, and loses
             its primary."*** */
          <Link
            href="/settings/connections"
            className="w-fit rounded text-sm text-accent underline decoration-border underline-offset-4 hover:decoration-accent focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
          >
            Review mapping
          </Link>
        ) : enabled ? (
          /* ⛔ **A link, not a wizard.** 📁 *"Home never embeds a connection
             wizard or an OAuth step."* */
          <Link
            href="/settings/connections"
            className="w-fit rounded bg-accent px-3 py-1.5 text-sm font-medium text-accent-contrast hover:bg-accent-hover focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
          >
            {copy.action}
          </Link>
        ) : (
          /* 🔴 **Disabled with the reason, and the card still renders.** 📁 The
             soft dependency *"renders before CRM completes but its primary
             action is disabled with the reason"* — ⛔ hiding it would make a
             two-step list look like a one-step list. */
          <div className="flex flex-col gap-1">
            <button
              type="button"
              disabled
              className="w-fit cursor-not-allowed rounded border border-border px-3 py-1.5 text-sm text-content-subtle"
            >
              {copy.action}
            </button>
            <p className="text-2xs text-content-subtle">{blockedBy}</p>
          </div>
        )}
      </CardBody>
    </Card>
  );
}
