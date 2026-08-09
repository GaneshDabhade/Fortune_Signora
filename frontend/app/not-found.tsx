import { SearchX } from 'lucide-react';
import Link from 'next/link';

import { SystemState } from '@/components/ui/system-state';

/**
 * What a customer sees when an address does not lead anywhere.
 *
 * **Until now, Next.js's default.** A bare white page reading *"404 | This
 * page could not be found"* — no product name, no theme, no navigation, and
 * no way back. A customer with a stale bookmark, a mistyped URL, or a link
 * to a page that has since moved was simply stranded, and the last thing they
 * saw was not Signora.
 *
 * **It is reachable more easily than it looks.** `/settings/team` is a URL an
 * optimistic customer will try — the product has no Team page yet
 * ([C-024](../../docs/LANE_COORDINATION.md)) — and below `768px` there is no
 * navigation to recover with at all ([B-019](../../docs/BUGS.md)).
 *
 * ### It says what is true, and nothing more
 *
 * **Not *"this page was deleted"*, and not *"you do not have access"*.** The
 * router knows only that nothing is registered at this address; asserting a
 * cause would be inventing one, and the wrong cause is worse than none — a
 * customer told they lack access will ask an administrator for something they
 * already have.
 *
 * ### It renders through the ladder, and that is [TASK-1429](../docs/BACKLOG.md)
 *
 * ⛔ **This file used to write its own 404** — its own heading, its own
 * layout, no identifier — and so did three other surfaces, each slightly
 * differently. 📁 **[TASK-1409](../docs/BACKLOG.md) built the ladder for
 * exactly this**, and its own failure test was *no surface writes a local
 * 404*. ⚡ **The COPY is unchanged; only its author moved.**
 *
 * ⚠️ **No `correlationId`, deliberately.** **A 404 is not a failure** — the
 * router answered correctly — **and an identifier invites somebody to open a
 * support conversation about a mistyped URL.**
 *
 * ### One way out, and it is the right one for both readers
 *
 * `/` resolves correctly whoever arrives: a signed-in customer lands on their
 * attention list, and a signed-out visitor is taken to sign-in by the shell.
 * **A second link would have to guess which of the two this is**, and this
 * page renders outside the authenticated shell, so it cannot know.
 */
export default function NotFound() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-canvas px-6">
      <div className="w-full max-w-md">
        <SystemState
          scope="page"
          state="404"
          glyph={SearchX}
          // ⛔ **The words are unchanged.** [TASK-1429](../docs/BACKLOG.md)
          // delivers *"no new component, no visual redesign"* — what changes is
          // that the shape comes from the ladder instead of from this file.
          title="That address does not lead anywhere"
          description="Nothing in Signora sits at this link. It may have moved, or it may never have existed — either way, nothing about your accounts has changed."
          primaryAction={
            <Link
              href="/"
              className="rounded text-sm font-medium text-accent underline decoration-border underline-offset-4 transition-colors hover:decoration-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            >
              Back to Signora
            </Link>
          }
        />
      </div>
    </main>
  );
}
