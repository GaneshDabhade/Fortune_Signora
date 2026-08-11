'use client';

import Link from 'next/link';
import { Check, Plug, MessageSquare, Users } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

import { StatedAbsence } from '@/components/feedback/stated-absence';
import { SkeletonText } from '@/components/ui';
import type { IntegrationCapability, IntegrationSystem, Membership } from '@/lib/api/types';
import type { CursorPage } from '@/lib/api/types';
import { cn } from '@/lib/design/cn';
import { useIntegrations } from '@/lib/query/hooks/integrations';
import { useWorkspaceMembers } from '@/lib/query/hooks/team';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';

/**
 * **§18 · the activation checklist a brand-new workspace works through** —
 * [TASK-1463](../../../docs/BACKLOG.md), against
 * `docs/design-snapshot/screens/Fortune Signora App Shell.dc.html`
 * ([D-138](../../../docs/DECISION_REGISTER.md)).
 *
 * > 📁 ***"A brand-new workspace shows the full shell with real navigation, not
 * > a stripped-down wizard… The content region holds a three-step activation
 * > checklist with live counts."***
 *
 * ## 🔴 *Live counts* is the requirement, and it is what makes this not a wizard
 *
 * ⛔ **A wizard remembers which page you are on. This remembers nothing** —
 * **every step's state is read from the workspace itself**, so it is correct for
 * somebody who connected their CRM last week on another machine, correct after
 * a disconnection, and correct for the second person to join. 📁
 * [§2](../../../CLAUDE.md), *truth has exactly one authoritative representation*:
 * **a stored `activation_step` would be a second copy of a fact the connections
 * already carry**, and the two would disagree the first time a connection broke.
 *
 * ## ⛔ Three figures the design prints that this does not
 *
 * 📁 The design's step one reads *"Salesforce connected · **8,412 accounts
 * imported** · **field mapping confirmed**"* and step three *"**Roles, regions
 * and quota.** 1 member so far — you."*
 *
 * | Figure | Why it is absent |
 * |---|---|
 * | **the imported-account count** | ⛔ **The browse read publishes no total** — [C-289](../../../docs/LANE_COORDINATION.md), found by [TASK-440](../../../docs/BACKLOG.md) building Companies. **The same absence, and the same refusal** |
 * | **field mapping** | ⛔ **No mapping exists to confirm.** `Connection` publishes `state`, `health` and `attention` and nothing about fields |
 * | **roles, regions and quota** | ⛔ **Territories and quota are not built.** `Membership.role` is `owner \| member` |
 *
 * ⚡ **Each is named in the copy as absent rather than dropped silently**, and
 * ⛔ **none is approximated** — 📁 [§20c](../../../CLAUDE.md): a fabricated
 * count on the first screen a customer ever reads is the worst place in the
 * product to put one.
 *
 * ## ⛔ The assistant's row is not built, and that is the honest outcome
 *
 * 📁 The design closes §18 with *"Signora can explain the setup as you go…
 * **Ask a question →**"*. ⛔ **[`Copilot`](copilot.tsx) states, today, that it
 * cannot answer questions yet** — so the control would open a panel that
 * refuses. ⚡ **A door that leads to a refusal is worse than no door on the
 * screen where somebody is deciding whether this product works**, and it is the
 * same false-affordance the assistant's own row declined to build.
 */

/** 📁 Which capability makes each connection step true. */
const CRM: IntegrationCapability = 'crm_activity';
const CONVERSATION: readonly IntegrationCapability[] = ['meetings', 'email_engagement'];

interface Step {
  readonly id: string;
  readonly icon: LucideIcon;
  readonly title: string;
  readonly body: string;
  readonly done: boolean;
  readonly href: string;
  readonly cta: string;
}

/**
 * ⚡ **`working`, never `connections.length`.** 📁 The type says why in its own
 * words: *"At least one connection Signora can currently use — **not merely
 * present**."* ⛔ **A step ticked by a broken connection tells somebody they
 * have finished setting up a product that cannot see their data.**
 */
function servedBy(systems: readonly IntegrationSystem[], caps: readonly IntegrationCapability[]) {
  return systems.filter((s) => s.working && s.capabilities.some((c) => caps.includes(c)));
}

/**
 * 🔴 **The exact count when the page is the whole set, and a floor otherwise.**
 *
 * 📁 `CursorPage` publishes `items`, `next_cursor` and `has_more` — ⛔ **and no
 * total.** ⚡ **So *"3 people"* is only true while `has_more` is false**, and
 * saying it anyway would be inventing the count [C-289](../../../docs/LANE_COORDINATION.md)
 * is already open about on another surface.
 */
function peopleSoFar(page: CursorPage<Membership> | undefined): string | null {
  if (page === undefined) return null;
  const n = page.items.length;
  if (page.has_more) return `More than ${n} people are in this organization`;
  return n === 1 ? 'One person is in this organization — you' : `${n} people are in this organization`;
}

export function ActivationChecklist() {
  const { activeWorkspace } = useWorkspaceContext();
  const workspaceId = activeWorkspace?.id ?? null;

  const integrations = useIntegrations(workspaceId);
  const members = useWorkspaceMembers(workspaceId);

  /**
   * 🔴 **[P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md): a failed read must
   * never render as an empty result** — and on THIS screen the empty result is
   * *"you have connected nothing"*.
   *
   * ⛔ **That is the most damaging possible version of the mistake**: a
   * customer who connected Salesforce yesterday is told they have not, on the
   * screen whose entire job is to say what is left to do. ⚡ **Checked before
   * anything else renders.**
   */
  if (integrations.isError || members.isError) {
    return <StatedAbsence as="card" icon={Plug} subject="your setup progress" />;
  }

  if (integrations.isPending || members.isPending) {
    return <SkeletonText lines={5} />;
  }

  const systems = integrations.data ?? [];
  const crm = servedBy(systems, [CRM]);
  const conversation = servedBy(systems, CONVERSATION);
  const people = peopleSoFar(members.data);
  const alone = members.data !== undefined && !members.data.has_more && members.data.items.length <= 1;

  const steps: readonly Step[] = [
    {
      id: 'crm',
      icon: Plug,
      title: 'Connect your CRM',
      body:
        crm.length > 0
          ? `${crm.map((s) => s.integration).join(', ')} connected. Signora reads the companies and deals already in it.`
          : 'Signora starts from the accounts you already work. Nothing here is scored until it can read them.',
      done: crm.length > 0,
      href: '/settings/connections',
      cta: crm.length > 0 ? 'Review connection' : 'Connect',
    },
    {
      id: 'conversations',
      icon: MessageSquare,
      title: 'Connect conversation sources',
      // 📁 The design's own sentence, and it is a true statement about the
      // pipeline rather than a persuasion.
      body:
        conversation.length > 0
          ? `${conversation.map((s) => s.integration).join(', ')} connected. Signora can see how engaged an account is.`
          : 'Calendar, email and call recording. Signora cannot score engagement without at least one.',
      done: conversation.length > 0,
      href: '/settings/connections',
      cta: conversation.length > 0 ? 'Review connections' : 'Connect',
    },
    {
      id: 'team',
      icon: Users,
      title: 'Invite your team',
      // ⛔ **Not *"and set territories"***. 📁 The design's step names roles,
      // regions and quota; **none of the three exists**, and naming them here
      // would promise a screen that is not built.
      body:
        people === null
          ? 'Signora is more useful when the people working these accounts can see them.'
          : `${people}. Signora is more useful when the people working these accounts can see them.`,
      done: !alone,
      href: '/settings/team',
      cta: 'Invite',
    },
  ];

  const done = steps.filter((s) => s.done).length;

  return (
    <section
      data-testid="activation-checklist"
      aria-labelledby="activation-heading"
      className="flex flex-col gap-4"
    >
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          {/* 📁 *"Welcome to Northwind Global"* — ⚡ **the organization's own
              name**, in the customer's word for it ([ADR-0034](../../../docs/architecture/adr/0034-ubiquitous-language.md)). */}
          <h2 id="activation-heading" className="text-lg font-semibold text-content">
            {activeWorkspace === null
              ? 'Welcome to Signora'
              : `Welcome to ${activeWorkspace.name}`}
          </h2>
          {/* ⛔ **No *"about twelve minutes"***. 📁 The design prints a duration
              and **nothing measures it** — a promise about how long somebody's
              setup takes is a claim the product cannot keep. */}
          <p className="mt-1 text-sm text-content-muted">
            Signora needs three things before it can score anything.
          </p>
        </div>
        {/* 📁 *"1 of 3"* — ⚡ **counted from the steps themselves**, so it can
            never disagree with the marks below it. */}
        <p
          data-testid="activation-progress"
          className="text-sm font-medium tabular-nums text-content-muted"
        >
          {done} of {steps.length}
        </p>
      </header>

      <ol className="overflow-hidden rounded-lg border border-border">
        {steps.map((step) => (
          <li
            key={step.id}
            data-step={step.id}
            data-done={step.done ? 'true' : 'false'}
            className={cn(
              'flex flex-wrap items-center gap-4 border-b border-border p-4 last:border-b-0',
              !step.done && 'bg-surface-sunken',
            )}
          >
            {/* 🔴 **The mark carries the state, never colour alone** — the rule
                [`StepRail`](../ui/step-rail.tsx) already establishes for the
                onboarding flow, applied to the checklist that is not a wizard. */}
            <span
              aria-hidden
              className={cn(
                'grid h-7 w-7 shrink-0 place-items-center rounded-full border',
                step.done
                  ? 'border-success bg-success text-accent-contrast'
                  : 'border-border text-content-subtle',
              )}
            >
              {step.done ? <Check className="h-4 w-4" /> : <step.icon className="h-4 w-4" />}
            </span>

            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-content">
                {step.title}
                {/* ⚡ **Readable without seeing the mark** — the state is in the
                    text as well as the glyph. */}
                <span className="sr-only">{step.done ? ' — done' : ' — not done yet'}</span>
              </p>
              <p className="mt-1 text-sm text-content-muted">{step.body}</p>
            </div>

            <Link
              href={step.href}
              className={cn(
                'shrink-0 rounded-md border px-3 py-1.5 text-sm font-medium transition-colors',
                step.done
                  ? 'border-border text-content hover:bg-surface-sunken'
                  : 'border-accent bg-accent text-accent-contrast hover:bg-accent-hover',
              )}
            >
              {step.cta}
              <span className="sr-only"> — {step.title}</span>
            </Link>
          </li>
        ))}
      </ol>
    </section>
  );
}
