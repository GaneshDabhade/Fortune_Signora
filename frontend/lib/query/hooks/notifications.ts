'use client';

/**
 * **The shell's notification reads** — [TASK-495](../../../../docs/BACKLOG.md)
 * slice ⓑ, against 📁 `Fortune Signora App Shell.dc.html` §10.
 *
 * ⚡ **Its own file**, on the precedent `commercial.ts` and `home.ts` set:
 * adding a file is a use of the frozen foundation rather than a change to it
 * ([§20c](../../../../CLAUDE.md)).
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { apiRequest } from '@/lib/api/client';
import type { NotificationFeed, UnreadBadge } from '@/lib/api/types';
import { queryKeys } from '@/lib/query/keys';

/**
 * 📁 **The badge** — *"count badge caps at 99+"*, and the cap is the server's.
 *
 * ⚡ **Read on every screen, because the bell is in the top bar.** ⛔ So it is
 * deliberately the cheap half: a count, not a list. 📁 The design's *"real-time
 * arrival animates the badge count only"* is the same separation — **the number
 * moves without the panel being fetched.**
 */
export function useUnreadNotifications(workspaceId: string | null) {
  return useQuery({
    queryKey: queryKeys.unreadNotifications(workspaceId ?? ''),
    enabled: workspaceId !== null,
    queryFn: () =>
      apiRequest<UnreadBadge>(`/workspaces/${workspaceId}/notifications/unread`),
  });
}

/**
 * 📁 **The panel's items**, newest first.
 *
 * ⛔ **`enabled` is the panel's open state**, so a bell nobody has clicked costs
 * one count rather than a list. ⚡ 📁 *"A popover keeps the user in place"* — and
 * a list fetched on every screen for a panel opened twice a day is the cost that
 * makes people turn the bell off.
 */
export function useNotifications(workspaceId: string | null, open: boolean) {
  return useQuery({
    queryKey: queryKeys.notifications(workspaceId ?? ''),
    enabled: workspaceId !== null && open,
    queryFn: () => apiRequest<NotificationFeed>(`/workspaces/${workspaceId}/notifications`),
  });
}

/**
 * 🔴 **Marking read, and it is per item.**
 *
 * 📁 ***"Opening the panel does not mark items read; opening an item does."***
 * ⛔ **So this takes ids** — a *mark everything* call on open would be the
 * behaviour the design rules out in the same sentence, and it would destroy the
 * one signal the badge exists to carry.
 *
 * ⚡ **The server answers with the resulting badge**, so the count is never
 * stale between the act and the next read — and the feed is invalidated so the
 * dot disappears from the row that was opened.
 */
export function useMarkNotificationsRead(workspaceId: string | null) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (notificationIds: readonly string[]) =>
      apiRequest<UnreadBadge>(`/workspaces/${workspaceId}/notifications/read`, {
        method: 'POST',
        body: JSON.stringify({ notification_ids: notificationIds }),
      }),
    onSuccess: (badge) => {
      // ⚡ **The answer IS the new badge**, so it is written rather than refetched.
      client.setQueryData(queryKeys.unreadNotifications(workspaceId ?? ''), badge);
      void client.invalidateQueries({
        queryKey: queryKeys.notifications(workspaceId ?? ''),
      });
    },
  });
}
