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

  /** ⚡ **Home's executive card** — [TASK-1425](../../../docs/BACKLOG.md). */
  pipelineHealth: (workspaceId: string) => ['pipeline-health', workspaceId] as const,

  /** ⚡ **Workspace-scoped, because `person_preferences` is keyed by
   * `(workspace_id, user_id)`** — [TASK-1424](../../../docs/BACKLOG.md). */
  preferences: (workspaceId: string) => ['preferences', workspaceId] as const,

  members: (workspaceId: string) => ['workspace', workspaceId, 'members'] as const,
  organizationHistory: (workspaceId: string) =>
    ['workspace', workspaceId, 'history'] as const,
  invitations: (workspaceId: string) =>
    ['workspace', workspaceId, 'invitations'] as const,

  /** **Scoped, so *mine* and *everything* are two lists.** The server applies
   * the predicate in the page query, so they genuinely are. */
  accounts: (workspaceId: string, scope: string = 'all') =>
    ['workspace', workspaceId, 'accounts', scope] as const,

  /**
   * ⛔ **A different key from `accounts` above, and that is deliberate** —
   * [TASK-440](../../../docs/BACKLOG.md). ⚡ **`accounts` is the ATTENTION
   * list**, ranked and narrowed; **this is the whole book, oldest first.**
   * 📁 Two questions, two reads, two caches — **sharing a key would make one
   * screen's refetch overwrite the other's data with a different set.**
   */
  accountsList: (workspaceId: string) =>
    ['workspace', workspaceId, 'accounts-list'] as const,
  /** 📁 [TASK-466](../../../docs/BACKLOG.md) — the workspace's tag vocabulary. */
  accountTags: (workspaceId: string) =>
    ['workspace', workspaceId, 'account-tags'] as const,
  /**
   * ⚡ **Keyed by the accounts asked about**, because the answer is only about
   * them — a page of rows is a different question from the next page, and a
   * shared key would serve one page's answer to the other.
   */
  accountTagAssignments: (workspaceId: string, accountIds: readonly string[]) =>
    ['workspace', workspaceId, 'account-tag-assignments', [...accountIds].sort()] as const,

  /**
   * 📁 [TASK-1479](../../../docs/BACKLOG.md) slice ⓶ — who owns each company.
   * ⚡ **Keyed by the accounts asked about, for the reason above**: a page of
   * rows is a different question from the next page.
   */
  accountAssignments: (workspaceId: string, accountIds: readonly string[]) =>
    ['workspace', workspaceId, 'account-assignments', [...accountIds].sort()] as const,

  /** ⚡ **TASK-1479 ⓶b.** The panel: every saved grouping and its count. */
  accountSegments: (workspaceId: string) =>
    ['workspace', workspaceId, 'account-segments'] as const,

  /** ⛔ **Sorted, like the assignment key above** — the same forty accounts in
   *  a different order are one question, and an unsorted key would cache two
   *  answers to it. */
  accountSegmentMemberships: (workspaceId: string, accountIds: readonly string[]) =>
    ['workspace', workspaceId, 'account-segment-memberships', [...accountIds].sort()] as const,

  accountScore: (workspaceId: string, accountId: string) =>
    ['workspace', workspaceId, 'accounts', accountId, 'score'] as const,

  accountObservations: (workspaceId: string, accountId: string) =>
    ['workspace', workspaceId, 'accounts', accountId, 'observations'] as const,

  accountOpportunity: (workspaceId: string, accountId: string) =>
    ['workspace', workspaceId, 'accounts', accountId, 'opportunity'] as const,

  accountTimeline: (workspaceId: string, accountId: string) =>
    ['workspace', workspaceId, 'accounts', accountId, 'timeline'] as const,

  integrations: (workspaceId: string) =>
    ['workspace', workspaceId, 'integrations'] as const,

  accountNarration: (workspaceId: string, accountId: string) =>
    ['workspace', workspaceId, 'accounts', accountId, 'narration'] as const,

  accountValidation: (workspaceId: string, accountId: string) =>
    ['workspace', workspaceId, 'accounts', accountId, 'validation'] as const,

  /** Lane B (Commercial Profile). The catalog is read whole and saved whole,
   * so one key per workspace is the whole cache surface. */
  products: (workspaceId: string) => ['workspace', workspaceId, 'products'] as const,

  /** Lane B (Commercial Profile). Described whole and saved whole, like the
   * catalog, and versioned separately from it. */
  icp: (workspaceId: string) => ['workspace', workspaceId, 'icp'] as const,

  /** Lane B (Commercial Profile). The segments list — paginated, so the key
   * carries the cursor: two pages are two cache entries, and echoing a cursor
   * back must not overwrite the page it came from. */
  icpSegments: (workspaceId: string, cursor: string | null) =>
    ['workspace', workspaceId, 'icp-segments', cursor ?? 'first'] as const,

  /** Lane B (Commercial Profile). Versioned separately from the catalog and
   * the ideal customer, so it is its own cache entry. */
  buyingCommittee: (workspaceId: string) =>
    ['workspace', workspaceId, 'buying-committee'] as const,

  /** Lane B (Commercial Profile). The fastest-changing of the four, and
   * versioned separately from all of them. */
  commercialFocus: (workspaceId: string) =>
    ['workspace', workspaceId, 'focus'] as const,

  /** Lane B (Commercial Profile). The one declaration anything downstream
   * reads, and the only one that announces its own changes. */
  targetAccounts: (workspaceId: string) =>
    ['workspace', workspaceId, 'target-accounts'] as const,

  /** Lane A (Provider Platform). When Signora last looked at each declared
   * company — a different module's fact from the list itself, so a different
   * key: declaring a new list must not serve stale attempt times, and an
   * attempt landing must not invalidate the declaration. */
  targetAccountCoverage: (workspaceId: string, subjects: readonly string[]) =>
    ['workspace', workspaceId, 'target-account-coverage', ...subjects] as const,

  /** Who this workspace competes against. */
  competitors: (workspaceId: string) =>
    ['workspace', workspaceId, 'competitors'] as const,

  signalCatalog: (workspaceId: string) =>
    ['workspace', workspaceId, 'signal-catalog'] as const,

  /** Lane A (Signal Engine). The Signal Center's queue, across the workspace.
   * The state filter is part of the key: *open* and *everything* are two
   * cached lists rather than one the browser re-filters, because the server
   * derives state from the clock and the browser cannot. */
  workspaceTriage: (workspaceId: string, state: string) =>
    ['workspace', workspaceId, 'triage', state] as const,

  businessEvent: (workspaceId: string, eventId: string) =>
    ['workspace', workspaceId, 'business-events', eventId] as const,

  /** Keyed by the *sorted* ids, so the same set of accounts is one cache entry
   * however the caller happened to order them. */
  identities: (workspaceId: string, accountIds: readonly string[]) =>
    ['workspace', workspaceId, 'identities', [...accountIds].sort().join(',')] as const,

  /** Keyed by the search text, so each distinct query is its own cache entry
   * and returning to one the customer already typed is instant. */
  accountSearch: (workspaceId: string, text: string) =>
    ['workspace', workspaceId, 'account-search', text] as const,

  decidedAccounts: (workspaceId: string) =>
    ['workspace', workspaceId, 'accounts', 'decided'] as const,

  accountResearch: (workspaceId: string, accountId: string) =>
    ['workspace', workspaceId, 'accounts', accountId, 'research'] as const,

  /** The prefix every workspace-scoped key shares. Passing this to
   * `invalidateQueries` clears exactly one tenant's cached data. */
  workspaceScope: (workspaceId: string) => ['workspace', workspaceId] as const,
} as const;
