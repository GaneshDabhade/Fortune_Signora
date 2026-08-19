'use client';

import { AlertTriangle } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { SystemState } from '@/components/ui/system-state';
import { HM_COPY_11 } from '@/lib/home/copy';

/**
 * 📁 **Home's state 12 — `state.noregistry`, *"empty activation registry"***.
 *
 * > *"The activation registry returned zero cards — a configuration or service
 * > fault. **The no-data state with one line reading "Setup steps could not be
 * > loaded" and a retry. Never a progress bar at 0 of 0, and never an empty
 * > activation composition.**"*
 *
 * ## 🔴 Why this state could not exist until the registry moved to the server
 *
 * ⛔ **The registry was a frozen array in the browser bundle**, so *zero cards*
 * was not a state the product could reach — 📁 `AC-H09` says *"return the
 * activation registry as an empty array"*, and there was nothing to return it
 * from. ⚡ **Contract 5 is what makes this reachable**: *"the activation
 * registry is fetched from the server."*
 *
 * ## ⚠️ Two causes, one sentence, and that is the design's decision
 *
 * ⛔ **A read that FAILED and a read that arrived EMPTY both land here.** 📁
 * `P-A` — *"a failed read must never render as an empty result"* — is satisfied
 * because **neither of these renders as an empty result**: both render the
 * fault. ⚡ The design's own wording covers both without distinguishing them,
 * and **`HM-COPY-11` is used verbatim** rather than split into two sentences,
 * because 📁 contract 18 forbids composing one: *"no message is assembled from
 * fragments at runtime."*
 *
 * ## ⛔ `region`, not `page`
 *
 * 📁 The scope ladder's *"a failure claims the smallest surface it can"*. ⚡ The
 * greeting, the date, the strips and the shell are all fine — **only the list of
 * steps is missing**, and taking the page for it would lose the one thing that
 * still worked.
 */
export interface NoRegistryProps {
  readonly onRetry: () => void;
}

export function NoRegistry({ onRetry }: NoRegistryProps) {
  return (
    <div data-testid="home-no-registry" className="col-span-full">
      <SystemState
        scope="region"
        state="region-error"
        glyph={AlertTriangle}
        /* 📁 *"one line"* — ⛔ and `title` is optional at region scope
           precisely so a one-sentence region state is not forced to invent a
           heading to sit above it. */
        description={HM_COPY_11}
        /* 📁 *"and a retry"* — ⚡ the most likely useful thing, which for a
           configuration or service fault is asking again. */
        primaryAction={
          <Button size="sm" onClick={onRetry}>
            Try again
          </Button>
        }
      />
    </div>
  );
}
