'use client';

import { useSearchParams } from 'next/navigation';
import { useState } from 'react';

import { ConnectionCenter } from '@/components/integrations/connection-center';
import { DisconnectDialog } from '@/components/integrations/disconnect-dialog';
import { NoWorkspace } from '@/components/workspace/no-workspace';
import { SkeletonText } from '@/components/ui';
import type { Connection } from '@/lib/api/types';
import { outcomeFor } from '@/lib/integrations/outcomes';
import {
  useCheckConnection,
  useDisconnect,
  useIntegrations,
} from '@/lib/query/hooks/integrations';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';

/**
 * The Connection Center.
 *
 * **Where the systems that run a customer's business meet Signora.** One
 * question, answered at a glance: *can I trust that Signora is connected to
 * what it needs, and if not, what do I do?*
 *
 * ### Why it lives under settings
 *
 * `/settings/*` is guarded to owners, which is right: connecting a business
 * system spends a credential and is administrative, not something an individual
 * seller does. The server enforces it independently — `integration:update` is
 * owner-only — and the route guard is the courtesy, never the enforcement.
 *
 * ### It also handles the return trip
 *
 * A customer coming back from a provider arrives here with an outcome in the
 * query string. Reading it on this page rather than on a dedicated one means
 * they land where they can see the result *and* the state it produced.
 */
export default function ConnectionsPage() {
  const { activeWorkspace, isLoading: workspacesLoading } = useWorkspaceContext();
  const workspaceId = activeWorkspace?.id ?? null;
  const { data, isLoading, isError } = useIntegrations(workspaceId);
  const disconnect = useDisconnect(workspaceId);
  const check = useCheckConnection(workspaceId);
  const [target, setTarget] = useState<Connection | null>(null);
  // Which row is being checked, so only that one says so. A single boolean
  // would make every row on the page claim to be checking.
  const [checking, setChecking] = useState<string | null>(null);

  const params = useSearchParams();
  const returned = params.get('outcome');

  if (workspacesLoading) return <SkeletonText lines={4} />;
  if (!activeWorkspace) return <NoWorkspace />;

  const close = () => {
    setTarget(null);
    disconnect.reset();
  };

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      <header className="flex flex-col gap-1">
        <h1 className="text-lg font-medium text-content">Connections</h1>
        <p className="text-sm text-content-muted">
          The systems Signora reads from to work out which accounts deserve your attention.
        </p>
      </header>

      {returned ? (
        // The return from a provider. Shown above the list so somebody sees the
        // result and the state it produced without scrolling for either.
        <div className="flex flex-col gap-1 border-l-2 border-border pl-3">
          <p className="text-sm text-content">{outcomeFor(returned).what}</p>
          {outcomeFor(returned).next ? (
            <p className="text-sm text-content-muted">{outcomeFor(returned).next}</p>
          ) : null}
        </div>
      ) : null}

      <ConnectionCenter
        systems={data ?? []}
        isLoading={isLoading}
        isError={isError}
        onDisconnect={setTarget}
        onCheck={(connection) => {
          setChecking(connection.id);
          // `onSettled`, not `onSuccess`: a check that fails to reach the
          // server must still release the row, or it says *Checking…* forever.
          check.mutate(connection.id, { onSettled: () => setChecking(null) });
        }}
        checkingId={checking}
      />

      {target ? (
        <DisconnectDialog
          open
          systemSlug={target.integration}
          label={target.label}
          isPending={disconnect.isPending}
          result={disconnect.data ?? null}
          isError={disconnect.isError}
          onConfirm={() => disconnect.mutate(target.id)}
          onClose={close}
        />
      ) : null}
    </div>
  );
}
