'use client';

import { Select, Skeleton } from '@/components/ui';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';

/**
 * Switches the active workspace.
 *
 * Renders nothing when the caller belongs to exactly one workspace: a
 * select with a single option is a control that cannot do anything, and
 * it invites the user to look for options that do not exist.
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
      label="Active workspace"
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
