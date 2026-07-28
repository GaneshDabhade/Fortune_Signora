'use client';

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

import type { Workspace } from '@/lib/api/types';
import { useInvalidateWorkspaceScope, useWorkspaces } from '@/lib/query/hooks';

const ACTIVE_WORKSPACE_KEY = 'signora.activeWorkspaceId';

interface WorkspaceContextValue {
  workspaces: Workspace[];
  activeWorkspace: Workspace | null;
  setActiveWorkspace: (workspaceId: string) => void;
  isLoading: boolean;
  error: Error | null;
}

const WorkspaceContext = createContext<WorkspaceContextValue | null>(null);

/**
 * The active workspace, and the list to choose from.
 *
 * The stored id is a **hint, never a grant**. It is validated against the
 * list the API returned, so a tampered localStorage value selects nothing
 * rather than scoping the UI to a workspace the caller is not a member of.
 * The server re-verifies membership on every request regardless
 * (18-authentication.md) — this only keeps the client honest about what it
 * displays.
 */
export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const { data, isLoading, error } = useWorkspaces();
  const invalidateScope = useInvalidateWorkspaceScope();
  const [activeId, setActiveId] = useState<string | null>(null);

  const workspaces = useMemo(() => data?.items ?? [], [data]);

  useEffect(() => {
    const first = workspaces[0];
    if (first === undefined) return;

    const stored = window.localStorage.getItem(ACTIVE_WORKSPACE_KEY);
    const isStillAMember = stored !== null && workspaces.some((w) => w.id === stored);

    setActiveId((current) => {
      if (current !== null && workspaces.some((w) => w.id === current)) return current;
      return isStillAMember ? stored : first.id;
    });
  }, [workspaces]);

  const setActiveWorkspace = useCallback(
    (workspaceId: string) => {
      setActiveId((previous) => {
        // Drop the outgoing workspace's cached data. Leaving it would show
        // one tenant's rows under another tenant's header until each query
        // happened to go stale.
        if (previous && previous !== workspaceId) void invalidateScope(previous);
        return workspaceId;
      });
      window.localStorage.setItem(ACTIVE_WORKSPACE_KEY, workspaceId);
    },
    [invalidateScope],
  );

  const activeWorkspace = workspaces.find((w) => w.id === activeId) ?? null;

  return (
    <WorkspaceContext.Provider
      value={{
        workspaces,
        activeWorkspace,
        setActiveWorkspace,
        isLoading,
        error: error as Error | null,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspaceContext(): WorkspaceContextValue {
  const context = useContext(WorkspaceContext);
  if (!context)
    throw new Error('useWorkspaceContext must be used within WorkspaceProvider');
  return context;
}
