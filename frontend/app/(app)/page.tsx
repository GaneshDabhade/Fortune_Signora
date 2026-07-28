'use client';

import { Building2, LineChart, Lightbulb } from 'lucide-react';

import { Card, CardBody, CardHeader, CardTitle, EmptyState } from '@/components/ui';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';

/**
 * Overview.
 *
 * **No business data, and no mock of it.** Every section shows its real
 * empty state, which is what a new customer sees on their first day and
 * what an account with no signal sees permanently. These are shipped UX,
 * not placeholders awaiting replacement — the pages that fill them arrive
 * with the modules that produce their data (M2.1 onward).
 */
export default function OverviewPage() {
  const { activeWorkspace } = useWorkspaceContext();

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6">
      <header>
        <h1 className="text-xl font-semibold text-content">
          {activeWorkspace ? activeWorkspace.name : 'Overview'}
        </h1>
        <p className="mt-1 text-sm text-content-muted">
          Connect a data source to start seeing revenue signals here.
        </p>
      </header>

      <div className="grid gap-4 md:grid-cols-3">
        <Section
          title="Companies"
          icon={Building2}
          message="No companies yet"
          description="Companies appear once a CRM or email integration is connected and its first sync completes."
        />
        <Section
          title="Signals"
          icon={Lightbulb}
          message="No signals yet"
          description="Buying signals are detected from company activity. They appear as soon as there is activity to read."
        />
        <Section
          title="Opportunities"
          icon={LineChart}
          message="No opportunities yet"
          description="Opportunities are surfaced when signals combine into a pattern worth acting on."
        />
      </div>
    </div>
  );
}

function Section({
  title,
  icon,
  message,
  description,
}: {
  title: string;
  icon: typeof Building2;
  message: string;
  description: string;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardBody>
        <EmptyState
          icon={icon}
          title={message}
          description={description}
          className="border-0 bg-transparent px-0 py-6"
        />
      </CardBody>
    </Card>
  );
}
