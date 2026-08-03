'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import type {
  AccountAttention,
  AccountIdentity,
  AccountNarration,
  AccountOpportunity,
  AccountResearch,
  AccountScore,
  AccountValidation,
  BusinessEventEvidence,
  DecidedAccount,
  CursorPage,
  OpenedOpportunity,
  RecordDecision,
  SignalCatalog,
  Workspace,
  WorkflowState,
} from '@/lib/api/types';
import { ApiError, apiRequest } from '@/lib/api/client';
import { queryKeys } from '@/lib/query/keys';

/**
 * Query hooks for the endpoints that exist today.
 *
 * Deliberately thin and deliberately few: Workspace & Tenancy is the only
 * shipped module, so these are the only real endpoints. Hooks for business
 * resources arrive with those resources, built against real domain
 * contracts rather than guessed shapes.
 */

export function useWorkspaces() {
  return useQuery({
    queryKey: queryKeys.workspaces(),
    queryFn: () => apiRequest<CursorPage<Workspace>>('/workspaces'),
  });
}

export function useWorkspace(workspaceId: string | null) {
  return useQuery({
    queryKey: queryKeys.workspace(workspaceId ?? ''),
    queryFn: () =>
      apiRequest<Workspace>(`/workspaces/${workspaceId}`, {
        workspaceId: workspaceId ?? undefined,
      }),
    enabled: workspaceId !== null,
  });
}

/**
 * Accounts worth attention, most pressing first.
 *
 * One page, no infinite scroll: the list is a **triage surface**, and a
 * seller who needs to scroll past fifty accounts has a prioritisation
 * problem the product should be solving rather than a paging one.
 */
export type OwnerScope = 'all' | 'mine' | 'unassigned';

/**
 * The accounts worth attention, optionally narrowed to whose they are.
 *
 * **The scope is part of the key**, so *mine* and *everything* are two cached
 * lists rather than one list the browser re-filters. That matters because the
 * server applies the predicate in the page query — a page of *mine* is a page
 * of yours, not the yours that happened to fall on a page of everything.
 *
 * **The brief shares this key** (D41), so a seller walking their own accounts
 * is offered their own next one. That only holds while the account link
 * carries the scope, which is why it travels in the URL rather than in state.
 */
export function useAccounts(workspaceId: string | null, scope: OwnerScope = 'all') {
  return useQuery({
    queryKey: queryKeys.accounts(workspaceId ?? '', scope),
    queryFn: () =>
      apiRequest<CursorPage<AccountAttention>>(
        `/workspaces/${workspaceId}/accounts${scope === 'all' ? '' : `?owner=${scope}`}`,
        { workspaceId: workspaceId ?? undefined },
      ),
    enabled: workspaceId !== null,
  });
}

/**
 * Names for a set of accounts, in one request.
 *
 * **A second request rather than a field on the list, and that is
 * architectural.** No module may reach both workflow and entity names, so the
 * two are composed here. Batched by design: naming fifty rows one at a time is
 * fifty round trips.
 *
 * Returns a lookup rather than an array, because every caller joins it to rows
 * it already has.
 */
export function useAccountIdentities(workspaceId: string | null, accountIds: string[]) {
  const ids = [...new Set(accountIds)].sort();

  return useQuery({
    queryKey: queryKeys.identities(workspaceId ?? '', ids),
    queryFn: async () => {
      const query = ids.map((id) => `ids=${encodeURIComponent(id)}`).join('&');
      const identities = await apiRequest<AccountIdentity[]>(
        `/workspaces/${workspaceId}/account-identities?${query}`,
        { workspaceId: workspaceId ?? undefined },
      );
      return new Map(identities.map((identity) => [identity.account_id, identity]));
    },
    // Nothing to ask about, so nothing is asked — an empty request would be a
    // round trip whose answer is known.
    enabled: workspaceId !== null && ids.length > 0,
    // Names change far more slowly than scores. Holding them longer keeps a
    // list from re-requesting identities that cannot have moved.
    staleTime: 5 * 60_000,
  });
}

/**
 * One account's score, with the ledger that produced it.
 *
 * **Never retried on a 404.** An account that has never been scored is a
 * settled answer, not a transient failure, and retrying it three times before
 * showing the empty state makes a fast truthful response look like a slow
 * broken one.
 */
export function useAccountScore(workspaceId: string | null, accountId: string | null) {
  return useQuery({
    queryKey: queryKeys.accountScore(workspaceId ?? '', accountId ?? ''),
    queryFn: () =>
      apiRequest<AccountScore>(`/workspaces/${workspaceId}/accounts/${accountId}/score`, {
        workspaceId: workspaceId ?? undefined,
      }),
    enabled: workspaceId !== null && accountId !== null,
    retry: (attempt, error) =>
      !(error instanceof ApiError && error.status === 404) && attempt < 2,
  });
}

/**
 * What Signora committed to about one account, and what has happened since.
 *
 * **Not folded into `useAccountScore`.** The score belongs to the Buying Score
 * Engine and the commitment to the Opportunity Engine; no module in the
 * ratified graph reaches both, so the brief composes them here — the same
 * reason names arrive separately (37-product-surface.md §7).
 *
 * Not retried on a 404: an account with nothing open is a settled answer, and
 * retrying makes a fast truthful response look like a slow broken one.
 */
export function useAccountOpportunity(
  workspaceId: string | null,
  accountId: string | null,
) {
  return useQuery({
    queryKey: queryKeys.accountOpportunity(workspaceId ?? '', accountId ?? ''),
    queryFn: () =>
      apiRequest<AccountOpportunity>(
        `/workspaces/${workspaceId}/accounts/${accountId}/opportunity`,
        { workspaceId: workspaceId ?? undefined },
      ),
    enabled: workspaceId !== null && accountId !== null,
    retry: (attempt, error) =>
      !(error instanceof ApiError && error.status === 404) && attempt < 2,
  });
}

/**
 * The latest grounded explanation of one account.
 *
 * **A 404 is the ordinary state, not an error.** Narration is produced by a
 * background worker after the deterministic pipeline has something to explain,
 * so a freshly qualified account has none — and the brief renders nothing at
 * all rather than an empty panel. Never retried: absence is a settled answer.
 *
 * Held longer than the score. A narration is immutable — a better explanation
 * is a *new* one — so a cached copy cannot go subtly wrong, only become older
 * than the newest.
 */
export function useAccountNarration(
  workspaceId: string | null,
  accountId: string | null,
) {
  return useQuery({
    queryKey: queryKeys.accountNarration(workspaceId ?? '', accountId ?? ''),
    queryFn: () =>
      apiRequest<AccountNarration>(
        `/workspaces/${workspaceId}/accounts/${accountId}/narration`,
        { workspaceId: workspaceId ?? undefined },
      ),
    enabled: workspaceId !== null && accountId !== null,
    retry: (attempt, error) =>
      !(error instanceof ApiError && error.status === 404) && attempt < 2,
    staleTime: 5 * 60_000,
  });
}

/**
 * What to check on this account, and what its evidence cannot tell you.
 *
 * **No 404 to handle.** An account with nothing currently held returns an empty
 * list, because *"nothing is live here"* is a real answer and a 404 would say
 * the account does not exist — a different and wrong statement.
 *
 * Held as long as the identities are: this is catalog prose keyed by hypothesis
 * type, and it changes when a domain expert edits a versioned artifact, not
 * when a score moves.
 */
export function useAccountValidation(
  workspaceId: string | null,
  accountId: string | null,
) {
  return useQuery({
    queryKey: queryKeys.accountValidation(workspaceId ?? '', accountId ?? ''),
    queryFn: () =>
      apiRequest<AccountValidation>(
        `/workspaces/${workspaceId}/accounts/${accountId}/validation`,
        { workspaceId: workspaceId ?? undefined },
      ),
    enabled: workspaceId !== null && accountId !== null,
    staleTime: 5 * 60_000,
  });
}

/**
 * The readings beneath one business event — where a citation ends.
 *
 * **Fetched only when a citation is opened.** Every ledger line names an event
 * and most are never followed; loading all of them with the brief would be a
 * dozen requests to answer a question nobody asked. `enabled` is the whole
 * mechanism.
 *
 * Immutable once written — a business event is superseded, never edited — so a
 * cached copy cannot go subtly wrong.
 */
export function useBusinessEvent(workspaceId: string | null, eventId: string | null) {
  return useQuery({
    queryKey: queryKeys.businessEvent(workspaceId ?? '', eventId ?? ''),
    queryFn: () =>
      apiRequest<BusinessEventEvidence>(
        `/workspaces/${workspaceId}/business-events/${eventId}`,
        { workspaceId: workspaceId ?? undefined },
      ),
    enabled: workspaceId !== null && eventId !== null,
    staleTime: 5 * 60_000,
  });
}

/**
 * Records what a person decided about an account.
 *
 * **The only write in the product surface**, and the invalidation is the whole
 * reason it lives here rather than in a component. A decision changes the
 * brief, the attention list *and* whether the account appears on it at all —
 * dismissing something is how a seller makes their morning shorter, and a list
 * that kept showing it would make the decision pointless.
 *
 * Deliberately **not optimistic**. Everywhere else in this product a number on
 * screen is one the server computed; a stage that flipped locally and was then
 * refused — a won deal cannot reopen — would be the one place the UI stated
 * something untrue, however briefly. The round trip is the price of that.
 */
export function useRecordDecision(
  workspaceId: string | null,
  accountId: string | null,
  opportunityId: string | null,
) {
  const client = useQueryClient();

  return useMutation({
    mutationFn: (decision: RecordDecision) =>
      apiRequest<WorkflowState>(
        `/workspaces/${workspaceId}/opportunities/${opportunityId}/states`,
        { method: 'POST', body: decision, workspaceId: workspaceId ?? undefined },
      ),
    onSuccess: () => {
      void client.invalidateQueries({
        queryKey: queryKeys.accountOpportunity(workspaceId ?? '', accountId ?? ''),
      });
      void client.invalidateQueries({
        queryKey: queryKeys.accounts(workspaceId ?? ''),
      });
      // A decision is exactly what moves an account between the two lists.
      // Without this, dismissing one would leave it visible on the list it
      // has left and absent from the one it has joined until a reload —
      // which is the shape of bug that teaches people to distrust a screen.
      void client.invalidateQueries({
        queryKey: queryKeys.decidedAccounts(workspaceId ?? ''),
      });
    },
  });
}

/**
 * Opening an opportunity by hand — LO-07.
 *
 * **The one write that creates rather than progresses.** Every other write in
 * the product surface appends to something a customer is already looking at;
 * this brings an account back into their work after Signora has stopped
 * suggesting it, or after somebody closed the wrong one.
 *
 * Invalidates the same three queries a decision does, for the same reason: an
 * opening moves an account between the two lists, and a screen that shows it
 * on the list it has left is the shape of bug that teaches people to distrust
 * a screen.
 */
export function useOpenOpportunity(workspaceId: string | null, accountId: string | null) {
  const client = useQueryClient();

  return useMutation({
    mutationFn: (opening: { reason: string }) =>
      apiRequest<OpenedOpportunity>(
        `/workspaces/${workspaceId}/accounts/${accountId}/opportunity`,
        { method: 'POST', body: opening, workspaceId: workspaceId ?? undefined },
      ),
    onSuccess: () => {
      void client.invalidateQueries({
        queryKey: queryKeys.accountOpportunity(workspaceId ?? '', accountId ?? ''),
      });
      void client.invalidateQueries({ queryKey: queryKeys.accounts(workspaceId ?? '') });
      void client.invalidateQueries({
        queryKey: queryKeys.decidedAccounts(workspaceId ?? ''),
      });
    },
  });
}

/**
 * What Signora can conclude about an account, and what each is called.
 *
 * **The one place a hypothesis has a name.** Every surface that shows one
 * cites it by key: the attention list does because the module that ranks
 * accounts is forbidden from reaching the Signal Engine at all, and a
 * translation table in this file would be a second vocabulary that drifts from
 * the catalog within a release.
 *
 * Held for the session. A change to the catalog is a **new version of a
 * reviewed artifact**, never an edit, so a held copy cannot go subtly wrong —
 * only become older than the newest, and the version travels with it.
 */
export function useSignalCatalog(workspaceId: string | null) {
  return useQuery({
    queryKey: queryKeys.signalCatalog(workspaceId ?? ''),
    queryFn: async () => {
      const catalog = await apiRequest<SignalCatalog>(
        `/workspaces/${workspaceId}/signal-catalog`,
        { workspaceId: workspaceId ?? undefined },
      );
      return new Map(catalog.types.map((type) => [type.key, type.title]));
    },
    enabled: workspaceId !== null,
    staleTime: Infinity,
  });
}

export function useCreateWorkspace() {
  const client = useQueryClient();

  return useMutation({
    mutationFn: (name: string) =>
      apiRequest<Workspace>('/workspaces', { method: 'POST', body: { name } }),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: queryKeys.workspaces() });
    },
  });
}

/**
 * Drops every cached entry belonging to a workspace.
 *
 * Called when the active workspace changes. Without it, a switch leaves
 * the previous tenant's data on screen under the new tenant's header until
 * each query independently goes stale — which looks exactly like a data
 * leak to anyone who sees it, and is indistinguishable from one in a
 * screenshot.
 */
export function useInvalidateWorkspaceScope() {
  const client = useQueryClient();

  return (workspaceId: string) =>
    client.invalidateQueries({ queryKey: queryKeys.workspaceScope(workspaceId) });
}

/**
 * Where research on this account stands, and the brief once there is one.
 *
 * **One hook for both questions.** *"Is it still running?"* and *"what did it
 * find?"* are the same question asked at different moments, and splitting them
 * would make the page stitch a story the server already knows.
 *
 * **It polls only while something is happening.** A research run takes about a
 * minute; a page that checked every few seconds forever would spend a request
 * a second on twelve accounts that finished yesterday. `refetchInterval`
 * returns `false` the moment the request settles, so the polling stops itself
 * rather than relying on the reader to leave.
 *
 * A `404` is *"nobody has asked"* and is not retried — retrying an answer would
 * make an ordinary state look like a flaky one.
 */
export function useAccountResearch(workspaceId: string | null, accountId: string | null) {
  return useQuery({
    queryKey: queryKeys.accountResearch(workspaceId ?? '', accountId ?? ''),
    queryFn: () =>
      apiRequest<AccountResearch>(
        `/workspaces/${workspaceId}/accounts/${accountId}/research`,
        { workspaceId: workspaceId ?? undefined },
      ),
    enabled: workspaceId !== null && accountId !== null,
    retry: (attempt, error) =>
      !(error instanceof ApiError && error.status === 404) && attempt < 2,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === 'requested' || status === 'running' ? 4_000 : false;
    },
  });
}

/**
 * Ask Signora to research this account.
 *
 * **Returns immediately; nothing has run.** The server records the ask and a
 * worker does the work, so the mutation settling means *accepted*, never
 * *finished* — which is why success invalidates the read rather than writing a
 * result into the cache.
 *
 * Asking again while a run is in flight is answered rather than refused, so
 * there is no already-running error for a caller to handle.
 */
export function useRequestResearch(workspaceId: string | null, accountId: string | null) {
  const client = useQueryClient();

  return useMutation({
    mutationFn: () =>
      apiRequest<AccountResearch>(
        `/workspaces/${workspaceId}/accounts/${accountId}/research`,
        { method: 'POST', workspaceId: workspaceId ?? undefined },
      ),
    onSuccess: (research) => {
      client.setQueryData(
        queryKeys.accountResearch(workspaceId ?? '', accountId ?? ''),
        research,
      );
    },
  });
}

/**
 * Accounts this workspace has decided about (**R4-04**).
 *
 * **Fetched alongside the attention list, not behind a control.** The section
 * renders only when the page is non-empty, so a workspace where nobody has
 * dismissed anything shows nothing at all — and a reader who never dismisses
 * never sees a control advertising a feature they do not use (**D6**).
 *
 * Invalidated by `useRecordDecision`, because deciding something is exactly
 * what moves an account between the two lists.
 */
export function useDecidedAccounts(workspaceId: string | null) {
  return useQuery({
    queryKey: queryKeys.decidedAccounts(workspaceId ?? ''),
    queryFn: () =>
      apiRequest<CursorPage<DecidedAccount>>(
        `/workspaces/${workspaceId}/accounts/decided`,
        { workspaceId: workspaceId ?? undefined },
      ),
    enabled: workspaceId !== null,
  });
}
