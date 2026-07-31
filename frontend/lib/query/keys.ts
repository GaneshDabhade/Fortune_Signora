/**
 * Query keys, defined in one place.
 *
 * Every key is **prefixed with the workspace id**, which is what makes
 * `invalidateWorkspace()` a single call rather than a list of every cache
 * entry that happens to be tenant-scoped. Getting this wrong is not a
 * performance bug: switching workspaces would leave one tenant's data
 * rendering under another tenant's header until each query happened to
 * refetch.
 *
 * Keys are built by function rather than written inline at call sites, so
 * a typo is a type error instead of a permanent cache miss.
 */
export const queryKeys = {
  /** Not workspace-scoped: the list is what tells you which workspaces
   * exist, so it cannot be keyed by one of them. */
  workspaces: () => ['workspaces'] as const,

  workspace: (workspaceId: string) => ['workspace', workspaceId] as const,

  members: (workspaceId: string) => ['workspace', workspaceId, 'members'] as const,

  accounts: (workspaceId: string) => ['workspace', workspaceId, 'accounts'] as const,

  /** The prefix every workspace-scoped key shares. Passing this to
   * `invalidateQueries` clears exactly one tenant's cached data. */
  workspaceScope: (workspaceId: string) => ['workspace', workspaceId] as const,
} as const;
