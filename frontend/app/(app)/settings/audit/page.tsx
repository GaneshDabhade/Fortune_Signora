'use client';

import { ScrollText } from 'lucide-react';

import { OrganizationHistory } from '@/components/team/history';
import { StatedAbsence } from '@/components/feedback/stated-absence';
import { NoWorkspace } from '@/components/workspace/no-workspace';
import { Card, CardBody, CardHeader, CardTitle, LockedField, PageHeader } from '@/components/ui';
import { useOrganizationHistory } from '@/lib/query/hooks/team';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';

/**
 * **The audit log** — [TASK-1412](../../../../../docs/BACKLOG.md),
 * 📁 `Fortune Signora Settings.dc.html`.
 *
 * ## 🔴 The data existed and nothing could reach it
 *
 * 📁 **The Settings design carries *"View audit log"* as a page action and
 * *Audit log* as a Governance destination**, and its page subtitle is the
 * promise the whole screen is built on: ***"Every change is attributed,
 * reversible and visible in the audit log."***
 *
 * ⚡ **The platform already publishes it** — `GET /workspaces/{id}/history`,
 * with `previous_role` and `new_role` on every entry, which is the design's
 * *"before and after values"*. ⛔ **But the only surface rendering it was a
 * section inside `/settings/team`**, so an administrator looking for an audit
 * log had to already know it lived under *Your team*.
 *
 * 🔴 **That is this codebase's own CX-01 rule, and `settings/page.tsx` states
 * it**: *"a page not listed on this screen is a page nobody can reach… A
 * closed loop with no door."* **The Connection Center was exactly that once.**
 *
 * ## ⛔ It renders the SAME component, not a second one
 *
 * ✅ **`OrganizationHistory` is reused unchanged.** ⚠️ **A second renderer of
 * the same entries is how two surfaces start disagreeing about what a role
 * change looked like** — and an audit log that disagrees with itself is worth
 * less than none, because it is the record people cite.
 *
 * ⛔ **`/settings/team` keeps its section.** ⚡ **The history in context is
 * useful where the members are**; this is the same record reached as a
 * destination rather than found by accident. **Same component, same data, one
 * truth** ([§2](../../../../../CLAUDE.md)).
 *
 * ## ⚠️ What the design promises that the platform cannot yet keep
 *
 * 📁 *"Immutable · 7 years"* · *"Every entry records actor, before and after
 * values, IP and session. Exportable to SIEM."*
 *
 * ✅ **Actor and before/after are on the wire and render.** ⛔ **IP, session,
 * the retention period and SIEM export are not published by anything**, so
 * they are shown **designed-locked rather than absent** — 📁 the design's own
 * rule, ruled at [D-225](../../../../../docs/DECISION_REGISTER.md) §4:
 * *"Locked is shown, not hidden… removing them from the page makes
 * administrators think the product lost a feature."*
 *
 * ⛔ **And no retention figure is printed.** ⚡ **Stating *7 years* would be
 * [§20c](../../../../../CLAUDE.md)'s mock business data on the one screen whose
 * entire value is that it does not make things up** — worse than absent,
 * because a customer would rely on it in an audit.
 */
export default function AuditLogPage() {
  const { activeWorkspace, isLoading: workspaceLoading, error } = useWorkspaceContext();
  const history = useOrganizationHistory(activeWorkspace?.id ?? null);

  if (error) {
    return <StatedAbsence as="page" icon={ScrollText} subject="your workspaces" />;
  }

  if (!workspaceLoading && activeWorkspace === null) return <NoWorkspace />;

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Audit log"
        // ⚡ **The design's own sentence**, and it is a claim about the record
        // rather than a description of the page.
        description="Every change is attributed and visible here. Entries are never edited — not by an administrator, and not by Signora."
      />

      <Card>
        <CardHeader>
          <CardTitle>What has changed</CardTitle>
        </CardHeader>
        <CardBody>
          <OrganizationHistory
            entries={history.data?.items ?? []}
            isLoading={history.isLoading || workspaceLoading}
            isError={history.isError}
          />
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Not recorded yet</CardTitle>
        </CardHeader>
        <CardBody>
          {/**
           * ⛔ **Shown rather than hidden, and each says WHY.** ⚡ **An
           * administrator who cannot see these cannot ask for them** — and an
           * auditor who assumes they exist would be assuming wrongly, which is
           * the more expensive of the two mistakes.
           */}
          <div className="flex flex-col gap-4">
            <LockedField
              label="Sign-in address and session"
              value="Not recorded"
              reason="Signora records who made a change and what it was. Where they were signed in from is not captured yet, so it cannot be shown."
            />
            <LockedField
              label="Retention period"
              value="Not stated"
              reason="How long entries are kept has not been set for this workspace. No period is shown here rather than one that has not been agreed."
            />
            <LockedField
              label="Export"
              value="Unavailable"
              reason="Entries cannot be exported to a security tool yet. They remain readable here."
            />
          </div>
        </CardBody>
      </Card>
    </div>
  );
}
