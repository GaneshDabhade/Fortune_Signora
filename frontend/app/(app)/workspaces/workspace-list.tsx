'use client';

import { useEffect, useState } from 'react';

import { ApiError } from '@/lib/api/client';
import type { Workspace } from '@/lib/api/types';
import { createWorkspace, listWorkspaces } from '@/lib/api/workspaces';

/**
 * Workspace list and creation.
 *
 * The list is scoped by Row-Level Security to the caller's own memberships —
 * there is no client-side filtering here, and none is possible, because the
 * database never returns another user's workspaces.
 */
export function WorkspaceList() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [name, setName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function refresh(): Promise<void> {
    try {
      const page = await listWorkspaces();
      setWorkspaces(page.items);
      setError(null);
    } catch (caught) {
      setError(
        caught instanceof ApiError ? caught.message : 'Could not load workspaces.',
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function onCreate(event: React.FormEvent): Promise<void> {
    event.preventDefault();
    if (!name.trim()) return;
    try {
      await createWorkspace(name.trim());
      setName('');
      await refresh();
    } catch (caught) {
      setError(
        caught instanceof ApiError ? caught.message : 'Could not create workspace.',
      );
    }
  }

  return (
    <div className="space-y-4">
      <form onSubmit={onCreate} className="flex gap-2">
        <input
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="New workspace name"
          maxLength={200}
          className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm"
        />
        <button
          type="submit"
          className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
        >
          Create
        </button>
      </form>

      {error && (
        <p
          role="alert"
          className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-800"
        >
          {error}
        </p>
      )}

      {loading ? (
        <p className="text-sm text-slate-500">Loading…</p>
      ) : workspaces.length === 0 ? (
        <p className="text-sm text-slate-500">
          No workspaces yet. Create one to get started.
        </p>
      ) : (
        <ul className="divide-y divide-slate-200 rounded-md border border-slate-200 bg-white">
          {workspaces.map((workspace) => (
            <li key={workspace.id} className="p-4" data-testid="workspace-item">
              <p className="font-medium">{workspace.name}</p>
              <p className="text-xs text-slate-500">{workspace.id}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
