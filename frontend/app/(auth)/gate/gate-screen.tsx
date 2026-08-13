/**
 * **One presentation for every refused gate** —
 * [TASK-1423](../../../../docs/BACKLOG.md).
 *
 * ⚡ **One component, not eleven.** 📁 [`SystemState`](../../../components/ui/system-state.tsx)
 * records the same choice a ladder down — *"the one presentation of a system
 * state"* — and **eleven screens differing in two sentences would drift in
 * layout, heading level and focus order.**
 *
 * ⛔ **It renders in the AUTH shell, not the app shell**, and that is not a
 * layout preference: 📁 every gate here fails **before** a workspace is
 * resolved, so **a rail listing destinations inside an organization the person
 * cannot enter would be offering what the screen is refusing.**
 */

import Link from 'next/link';

import { GATE_COPY, type GateReason } from '@/lib/entry/gates';

export function GateScreen({ reason }: { reason: GateReason }) {
  const copy = GATE_COPY[reason];

  return (
    <div className="flex flex-col gap-3">
      {/* ⚡ **An `h1`, because this IS the page.** ⛔ A refusal rendered as a
          subordinate heading reads as a note about a page rather than the
          answer to why there isn't one. */}
      <h1 className="text-lg font-semibold text-content">{copy.title}</h1>

      <p className="text-sm leading-6 text-content-muted">{copy.body}</p>

      {copy.action === null ? null : (
        <Link
          href={copy.action.href}
          className="w-fit rounded bg-accent px-3 py-1.5 text-sm font-medium text-accent-contrast hover:bg-accent-hover focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
        >
          {copy.action.label}
        </Link>
      )}
    </div>
  );
}
