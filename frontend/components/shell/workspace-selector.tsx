'use client';

import { Select, Skeleton } from '@/components/ui';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';

/**
 * Switches the active organization.
 *
 * Renders nothing when the caller belongs to exactly one: a select with a
 * single option is a control that cannot do anything, and it invites the user
 * to look for options that do not exist.
 *
 * **The label says *organization* and the component says `workspace`**
 * (ADR-0034). The accessible name is the one thing here a person actually
 * reads — a screen-reader user hearing *"active workspace"* would be the only
 * customer ever told the internal word, which is the worst possible place for
 * it to survive.
 */
export function WorkspaceSelector() {
  const { workspaces, activeWorkspace, setActiveWorkspace, isLoading } =
    useWorkspaceContext();

  if (isLoading) return <Skeleton className="h-10 w-48" />;
  if (workspaces.length <= 1) {
    return activeWorkspace ? (
      <span className="text-sm font-medium text-content">{activeWorkspace.name}</span>
    ) : null;
  }

  return (
    <Select
      label="Active organization"
      labelHidden
      value={activeWorkspace?.id ?? ''}
      onChange={(event) => setActiveWorkspace(event.target.value)}
      options={workspaces.map((workspace) => ({
        value: workspace.id,
        label: workspace.name,
      }))}
      className="w-56"
    />
  );
}
