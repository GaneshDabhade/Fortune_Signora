'use client';

import { X } from 'lucide-react';
import { useEffect } from 'react';

import { useCardOutcomes } from '@/components/home/card-outcomes';
import { Button } from '@/components/ui/button';
import { SystemState } from '@/components/ui/system-state';
import { ApiError } from '@/lib/api/client';

/**
 * 📁 **Home's state 08, drawn** — `Fortune Signora Home.dc.html` §08,
 * *"state 08 · card error"*.
 *
 * > 📁 ***"Inside the card's own footprint, DASHED border so it is
 * > distinguishable from content. The layout does not move and no sibling is
 * > affected."***
 * > 📁 Contract 13: *"a card query failing after retries renders that card's
 * > error inside its own footprint **with the correlation ID**; siblings are
 * > unaffected."*
 *
 * ## ✅ The grammar is the System States document's, not Home's
 *
 * ⛔ **Home does not get its own failure treatment.** 📁 `SystemState` is the
 * ratified presentation — *"one illustration language… severity picks the
 * colour… identifiers are copyable… one primary action, and it does the most
 * likely useful thing rather than `reload`"* — and it is called here at
 * **`region` scope**, which is what makes the announcement polite and stops the
 * failure claiming the page.
 *
 * ⚠️ **What Home adds is the frame and nothing else**: the dashed border its
 * own document specifies, inside the card's declared footprint.
 *
 * ## 🔴 Every Home card said this differently, and that was the defect
 *
 * ⛔ **Each card hand-rolled a paragraph with the correlation id appended.**
 * ⚡ **The copy was right and the treatment was not**: no tile, no glyph, no
 * retry, a solid border indistinguishable from content, and an id nobody could
 * copy. 📁 *"The single thing that makes a support conversation short"* was
 * rendered as body text.
 *
 * ## ⚡ `Retry` is a real retry, not a reload
 *
 * 📁 *"One primary action, and it does the most likely useful thing rather than
 * `reload`."* ⛔ **A page reload would discard every sibling card that
 * succeeded** — which is the opposite of *"no sibling is affected"*.
 */
export interface CardFailureProps {
  /**
   * 📁 **What failed, in the customer's terms** — the design's own example is
   * *"Your briefing could not be generated"*. ⛔ Never *"Error"* and never a
   * status code.
   */
  readonly title: string;
  /**
   * 📁 **`3.3.1`** — *"failures name the cause, the scope, **what survived**,
   * and the identifier, in that order."* ⚡ The survivor clause is the design's
   * *"Everything else on this page is current as of 4 minutes ago"*, and it is
   * the sentence that stops a person distrusting the whole screen.
   */
  readonly description: string;
  /** The query's error, so the correlation ID comes from the response. */
  readonly error: unknown;
  /** ⚡ The failed query's own `refetch`. */
  readonly onRetry: () => void;
  readonly retrying?: boolean;
  /**
   * ⚡ **The failing card's own test id, carried onto the panel.**
   *
   * 🔴 **A failed card must still be identifiable as THAT card.** ⛔ Replacing
   * the card's frame with an anonymous panel makes *"which card failed?"*
   * unanswerable in the DOM — 📁 and contract 13 is about a failure staying
   * *inside its own footprint*, which cannot be asserted about a panel that
   * belongs to nobody.
   */
  readonly testId?: string;
}

export function CardFailure({
  title,
  description,
  error,
  onRetry,
  retrying = false,
  testId,
}: CardFailureProps) {
  /**
   * 🔴 **State 08's page half is counted here** — 📁 *"if EVERY card fails, the
   * page states that and offers one retry for all."*
   *
   * ⚡ **A card is failed exactly when it renders this**, so this is the one place
   * that knows without Home duplicating ten queries (§2). ⛔ **The registry is
   * optional** — outside Home there is no provider and the count stays zero.
   *
   * ⚠️ **Keyed on `testId`, which is the failing card's own id.** A failure with
   * no id is still reported, under a stable fallback, because *"every card
   * failed"* must not become *"every card with a test hook failed"*.
   */
  const outcomes = useCardOutcomes();
  const id = testId ?? title;
  const { report, forget } = outcomes;
  useEffect(() => {
    report(id, onRetry);
    return () => forget(id);
  }, [id, onRetry, report, forget]);

  /**
   * ⛔ **A wrapper rather than a prop on `SystemState`.** ⚡ That component
   * takes a fixed set of props deliberately — it is the ratified presentation
   * of a system state and every surface renders it identically — **so a test
   * hook belongs to the caller, not to the grammar.**
   */
  return (
    <div data-testid={testId} className="h-full">
    <SystemState
      scope="region"
      state="region-error"
      glyph={X}
      title={title}
      description={description}
      correlationId={error instanceof ApiError ? error.correlationId : undefined}
      primaryAction={
        <Button variant="secondary" size="sm" onClick={onRetry} loading={retrying}>
          Retry
        </Button>
      }
      /* 📁 *"dashed border so it is distinguishable from content"*. ⚡ The
         border colour stays the component's — severity is the tile's job, and
         a red frame would make one failed card shout over four working ones. */
      className="h-full border-dashed"
    />
    </div>
  );
}
