'use client';

import {
  QueryClient,
  QueryClientProvider,
  type QueryClientConfig,
} from '@tanstack/react-query';
import { useState, type ReactNode } from 'react';

import { ApiError } from '@/lib/api/client';

/**
 * Retry policy.
 *
 * A 4xx means the request was wrong and will be wrong again — retrying it
 * wastes a round trip and delays the error the user needs to see. A 401 is
 * additionally already handled inside the API client, which refreshes the
 * token and retries once; retrying here would stack a second refresh on
 * top of that one.
 *
 * 5xx and network failures are transient and worth retrying, twice.
 */
function shouldRetry(failureCount: number, error: unknown): boolean {
  if (error instanceof ApiError && error.status >= 400 && error.status < 500) {
    return false;
  }
  return failureCount < 2;
}

export const queryClientConfig: QueryClientConfig = {
  defaultOptions: {
    queries: {
      retry: shouldRetry,
      // Long enough that navigating back to a page does not refetch
      // immediately, short enough that data does not look stale after a
      // colleague changes something.
      staleTime: 30_000,
      // Refetch when the tab regains focus or the network returns —
      // together these cover the "laptop was asleep" case without polling.
      refetchOnWindowFocus: true,
      refetchOnReconnect: true,
    },
    mutations: {
      // Mutations are not idempotent by default. Retrying one that may
      // have succeeded is how duplicate workspaces get created.
      retry: false,
    },
  },
};

export function QueryProvider({ children }: { children: ReactNode }) {
  // Created in state rather than at module scope: a module-level client is
  // shared across every request on the server, which would leak one user's
  // cached data into another's render.
  const [client] = useState(() => new QueryClient(queryClientConfig));

  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
