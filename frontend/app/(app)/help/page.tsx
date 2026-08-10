'use client';

import { useMemo, useState } from 'react';

import { StatedAbsence } from '@/components/feedback/stated-absence';
import { NoWorkspace } from '@/components/workspace/no-workspace';
import { Card, CardBody, Input, PageHeader, SkeletonText } from '@/components/ui';
import { useIntegrations } from '@/lib/query/hooks/integrations';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';
import type { Connection } from '@/lib/api/types';

import { answerFor, answerableSubjects } from './answer';

/**
 * **Help & support** — [TASK-1420](../../../../docs/BACKLOG.md), against 📁
 * `docs/design-snapshot/screens/Fortune Signora Help Center.dc.html`
 * ([D-138](../../../../docs/DECISION_REGISTER.md)).
 *
 * ## ✅ This route is what two of this lane's own findings were missing
 *
 * 📁 **[C-275](../../../../docs/LANE_COORDINATION.md)** recorded the top bar's
 * help slot as ABSENT — ⛔ *"there is no help, docs or support route, and
 * `Fortune Signora Help Center.dc.html` is a design with nothing built behind
 * it."* 📁 **[C-269](../../../../docs/LANE_COORDINATION.md)** recorded the
 * rail's `Docs & support` the same way. ⚡ **Both close when this lands.**
 *
 * ## 🔴 The differentiator is built and the commodity is not
 *
 * 📁 **The row names its own failure**: ⛔ *"shipping a generic documentation
 * site and calling the workflow done. **The workspace-aware answer is the whole
 * differentiator**; documentation alone is the commodity half."*
 *
 * ✅ **So this screen answers about THIS workspace, from
 * [`answer.ts`](./answer.ts), sourced to the connection it read** — ⛔ **and
 * ships no documentation library at all.**
 *
 * ## ⛔ Four of the design's sections have no source, and are ABSENT
 *
 * ⚠️ **Measured before building, which is the habit
 * [C-277](../../../../docs/LANE_COORDINATION.md) cost this lane a slice for
 * skipping:**
 *
 * | Design section | Source |
 * |---|---|
 * | §01 the answer | ✅ **connection telemetry — [TASK-407](../../../../docs/BACKLOG.md)'s `health`, `attention`, `reason`** |
 * | §01 *Your support entitlement* — CSM, plan, response times | ⛔ **nothing publishes an entitlement, a CSM or an SLA** |
 * | §01 *Your open tickets* | ⛔ **no ticketing contract exists** |
 * | §02 status scoped to REGION | ⛔ **a workspace has no region** ([C-1415](../../../../docs/LANE_COORDINATION.md)) |
 * | §03 documentation with applicability | ⛔ **no documentation corpus** |
 *
 * ⚡ **§02 scoped to INTEGRATIONS is the half that has a source, and it is
 * built.** 📁 The design asks for status *"not as a global average"* — ✅ **and
 * a customer's own connections are exactly not a global average.**
 *
 * ⛔ **Nothing is invented to fill the other four.** 📁 A CSM's name, a
 * response-time commitment or a ticket list rendered from no contract would be
 * the mock business data [§20c](../../../../CLAUDE.md) forbids — **and a
 * contractual response time is the worst possible thing to invent.**
 */
export default function HelpPage() {
  const { activeWorkspace, isLoading: workspaceLoading } = useWorkspaceContext();
  const { data: systems, isLoading } = useIntegrations(activeWorkspace?.id ?? null);
  const [question, setQuestion] = useState('');

  const connections: Connection[] = useMemo(
    () => (systems ?? []).flatMap((system) => system.connections),
    [systems],
  );

  const answer = useMemo(
    () => answerFor(question, systems ?? [], connections),
    [question, systems, connections],
  );

  const subjects = answerableSubjects(connections);

  if (workspaceLoading) return <SkeletonText lines={3} />;
  if (activeWorkspace === null) return <NoWorkspace />;

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      <PageHeader
        title="Help & support"
        description="Ask about this organization and Signora answers from what it can actually see."
      />

      <Card>
        <CardBody>
          <Input
            label="What has gone wrong?"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="why did my Salesforce write-back stop"
          />

          {isLoading ? (
            <div className="mt-4">
              <SkeletonText lines={2} />
            </div>
          ) : answer !== null ? (
            <div className="mt-4">
              {/* 📁 *"Answer for your workspace"* — ⚡ **the heading is a claim,
                  so it only appears when the answer is genuinely about this
                  workspace.** */}
              <p className="text-label uppercase tracking-wide text-content-subtle">
                Answer for your organization
              </p>
              <p className="mt-1.5 font-medium text-content">{answer.headline}</p>
              <p className="mt-1.5 text-sm leading-6 text-content-muted">{answer.detail}</p>

              {/* 🔴 **Sources, always.** 📁 The design shows *"3 sources"* beside
                  the answer, and an answer without one is prose. ⚡ Each is a
                  route the customer can open and check for themselves. */}
              <ul className="mt-3 flex flex-wrap gap-2">
                {answer.sources.map((source) => (
                  <li key={source.href}>
                    <a
                      href={source.href}
                      className="rounded text-sm text-accent underline decoration-border underline-offset-4 transition-colors hover:decoration-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
                    >
                      {source.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ) : question.trim() === '' ? (
            // ⚡ **What it can answer about, named** — ⛔ rather than a search
            // box that silently answers nothing.
            <p className="mt-4 text-sm leading-6 text-content-muted">
              {subjects.length === 0
                ? 'Signora can answer about the systems this organization has connected. None are connected yet.'
                : `Signora can answer about ${subjects.join(', ')}.`}
            </p>
          ) : (
            // ⛔ **Says what it cannot answer and why**, rather than producing
            // general advice with an organization name pasted into it.
            <div className="mt-4">
              <StatedAbsence
                subject="an answer for this organization"
                reassurance={
                  subjects.length === 0
                    ? 'Nothing is connected yet, so there is no state to read'
                    : `Signora can answer about ${subjects.join(', ')}`
                }
              />
            </div>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
