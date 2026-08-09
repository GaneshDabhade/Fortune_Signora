'use client';

import { useMutationState, type Mutation } from '@tanstack/react-query';

/**
 * **What is waiting to be sent, in the order it will go** —
 * [TASK-1435](../../../docs/BACKLOG.md), carved out of
 * [TASK-1409](../../../docs/BACKLOG.md) by
 * [D-215](../../../docs/DECISION_REGISTER.md).
 *
 * > 📁 ***"two edits are queued. They are sent in order when the connection
 * > returns — the queue is visible, not implied."***
 *
 * ## ⛔ There is no queue in this file, and that is the row's own instruction
 *
 * 📁 **The row says it in terms**: *"TanStack Query already ships
 * `onlineManager`, `networkMode` and `resumePausedMutations`. **Do not write a
 * queue** — this is configuration and a surface, not an implementation."*
 * ⚡ **So this READS the library's queue and never keeps one.** **A second
 * queue beside the library's would be two representations of one fact**
 * ([§2](../../../CLAUDE.md)), and the copy would drift the first time a
 * mutation was retried.
 *
 * ## ⚡ Why `isPaused` rather than `isPending`
 *
 * ⛔ **A pending mutation is in flight; a PAUSED one has not left.** 📁 The
 * design's sentence is about the second — *"queued… sent when the connection
 * returns"* — and counting the first would tell somebody two edits are waiting
 * while one of them is already on the wire.
 *
 * ## 📁 Order is the library's, and it is asserted rather than assumed
 *
 * **TanStack replays paused mutations in the order they were paused**, and
 * `useMutationState` returns them in that order. ⛔ **Nothing here sorts**: a
 * sort would be this file deciding a sequence the library owns, and the two
 * would disagree the moment either changed.
 *
 * ## ⚠️ In-session only, deliberately
 *
 * 📁 **The row names the risk and draws the line**: *"persisting a mutation
 * queue across sessions without deciding what a stale queue means… in-session
 * is the scope; a stale replay is a separate decision and not this row's to
 * take."* ⛔ **So no `persistQueryClient`, no storage, nothing survives a
 * reload** — **a queued edit replayed an hour later against changed data is a
 * decision somebody has to make, not a default to inherit.**
 */

/** One thing waiting to be sent, in the customer's terms rather than the library's. */
export interface QueuedEdit {
  /** Stable across renders, so a list does not reorder under a reconnect. */
  id: number;
  /**
   * 📁 The design's `{{ q.t }}` — **what the edit was**, supplied by whoever
   * made it. ⛔ **Never derived from the mutation key**: a key is an
   * engineering identifier and this line is read by a customer
   * ([ADR-0034](../../../docs/architecture/adr/0034-ubiquitous-language.md)).
   */
  title: string;
  /** 📁 `{{ q.meta }}` — which record it touches, when it was made. */
  meta?: string;
}

/**
 * ⚡ **What a mutation must declare to appear in the queue.**
 *
 * ⛔ **A mutation with no `queueTitle` is INVISIBLE in the queue, and that is
 * deliberate rather than a gap.** 📁 The design lists edits a person made and
 * would recognise; **a background refresh that happened to pause is not one**,
 * and inventing a label for it would put engineering vocabulary on a customer
 * surface.
 */
export interface QueueableMeta {
  queueTitle?: string;
  queueMeta?: string;
}

/** ⛔ Narrow rather than cast — `meta` is `Record<string, unknown>` upstream. */
function readMeta(mutation: Mutation<unknown, Error, unknown, unknown>): QueuedEdit | null {
  const meta = mutation.meta as QueueableMeta | undefined;
  if (meta?.queueTitle === undefined) return null;
  return {
    id: mutation.mutationId,
    title: meta.queueTitle,
    ...(meta.queueMeta === undefined ? {} : { meta: meta.queueMeta }),
  };
}

/**
 * **The edits waiting to be sent, in send order.**
 *
 * ⚡ **Empty when online**, because nothing pauses when the connection is
 * there — so a caller renders the queue only when there is one, without
 * asking separately whether the browser is offline.
 */
export function useQueuedEdits(): readonly QueuedEdit[] {
  return useMutationState({
    filters: { predicate: (mutation) => mutation.state.isPaused },
    select: readMeta,
  }).filter((edit): edit is QueuedEdit => edit !== null);
}
