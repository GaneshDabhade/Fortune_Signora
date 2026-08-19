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
 * 📁 **The panel's items**, newest first — **and the badge is counted from
 * them.**
 *
 * ## 🔴 This used to be two reads, and the first of them was broken
 *
 * ⚠️ **`useUnreadNotifications` issued a `GET` to
 * `/workspaces/{id}/notifications/unread`.** ⛔ **That route is a `POST`** —
 * 📁 *"the caller supplies a list of notification ids and a list does not fit in
 * a query string"* — **so every authenticated screen took a `405` and the bell
 * never showed a count.** ⚡ **Found by writing this row's journey**, which is
 * the [§19](../../../../CLAUDE.md) step that was outstanding.
 *
 * ## ⛔ And calling it correctly would have been the wrong repair
 *
 * 📁 **That endpoint answers *which of THESE has this person not read*** — it
 * takes the ids because it was built (TASK-480) **against a feed that did not
 * carry read state.** ✅ **Slice ⓐ changed that**: `GET /notifications` returns
 * `read_at` per item. ⛔ **So asking the server to count what the answer already
 * contains is a second round trip to learn what arrived in the first.**
 *
 * ⚡ **The count is `read_at === null`, and the 99+ cap is `badgeLabel`'s** —
 * 📁 the design puts the cap in the shell (*"count badge caps at 99+"*) and the
 * shell already had it.
 *
 * ## ⚠️ What this costs, stated rather than hidden
 *
 * ⛔ **The feed is now read on every screen** rather than on first open — 📁 the
 * bell is Slot 4 of the top bar. ⚡ **It is one bounded read** (the panel's
 * limit, server-side) **replacing one that was failing**, and 📁 *"real-time
 * arrival animates the badge count only"* still holds: the number moves when
 * this query refetches, whether or not the panel is open.
 */
export function useNotifications(workspaceId: string | null) {
  return useQuery({
    queryKey: queryKeys.notifications(workspaceId ?? ''),
    enabled: workspaceId !== null,
    queryFn: () =>
      apiRequest<NotificationFeed>(`/workspaces/${workspaceId}/notifications`, {
        workspaceId: workspaceId ?? undefined,
      }),
    /**
     * 🔴 **The row's own acceptance is *"an event occurs and the customer sees
     * it **without reloading**"*** — 📁 [TASK-495](../../../../docs/BACKLOG.md).
     * ⛔ **Nothing pushed this before**: the query settled once and the bell
     * then described the moment the screen was opened, so a notification
     * arriving while somebody worked was invisible until they navigated.
     *
     * ⚠️ **30 seconds, and it is the client's existing `staleTime`** — 📁
     * `lib/query/client.tsx`. ⛔ **Not `useAccountResearch`'s 4s**: that polls a
     * run somebody is watching finish, and this is on **every screen for every
     * customer**. ⚡ **Two requests a minute for a bounded list** is the cost,
     * and it is stated rather than tuned.
     *
     * ⛔ **This is not *"real-time"* and the design's word is not borrowed.**
     * 📁 *"Real-time arrival animates the badge count only"* describes what the
     * customer sees; **the repository has no push transport**, and a poll is the
     * honest mechanism rather than a claim about latency.
     */
    refetchInterval: 30_000,
  });
}

/**
 * 📁 *"Count badge caps at 99+."* — ⛔ **the number, not the label**: the cap is
 * `badgeLabel`'s and lives in the shell.
 */
export function unreadCount(feed: NotificationFeed | undefined): number {
  return (feed?.notifications ?? []).filter((item) => item.read_at === null).length;
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
    /**
     * ⚠️ **The body is an OBJECT, not a string.** ⛔ `apiRequest` calls
     * `JSON.stringify` itself — **this passed an already-encoded string and the
     * API received a quoted blob instead of a document.** ⚡ Every other caller
     * in the repository passes the object; this one had a second encoding and
     * nothing exercised it.
     */
    mutationFn: (notificationIds: readonly string[]) =>
      apiRequest<UnreadBadge>(`/workspaces/${workspaceId}/notifications/read`, {
        method: 'POST',
        workspaceId: workspaceId ?? undefined,
        body: { notification_ids: notificationIds },
      }),
    onSuccess: () => {
      /**
       * ⚡ **The feed is the badge now**, so one invalidation moves both — ⛔ the
       * dot on the row that was opened AND the number on the bell.
       *
       * ⚠️ **The server still answers with its own count and it is discarded.**
       * 📁 It is computed over *the ids this call sent*, which is the panel's
       * page rather than the feed — **writing it into the badge would show the
       * unread total of one click's worth of rows.**
       */
      void client.invalidateQueries({
        queryKey: queryKeys.notifications(workspaceId ?? ''),
      });
    },
  });
}
