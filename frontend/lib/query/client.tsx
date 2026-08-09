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
      /**
       * 🔴 **Declared rather than defaulted** —
       * [TASK-1435](../../../docs/BACKLOG.md).
       *
       * 📁 **The design: *"two edits are queued. They are sent in order when
       * the connection returns."*** ⚡ **`'online'` is what makes a mutation
       * fired with no connection PAUSE instead of failing**, and the library
       * replays paused mutations in order when `onlineManager` reports the
       * connection back.
       *
       * ⛔ **It is written out even though it is the library's default**,
       * because it stopped being a default the moment a customer-visible
       * promise rested on it: **a future upgrade that changed it would turn
       * *"your edits are queued"* into a lie**, and nothing here would fail.
       * ✅ **`tests/unit/offline-queue.test.ts` asserts the value for that
       * reason.**
       */
      networkMode: 'online',
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
