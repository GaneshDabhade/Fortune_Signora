/**
 * 📁 **Home's state 04** — `AC-H03`: *"the next render is the role composition,
 * with the setup-complete strip shown **exactly once**."*
 *
 * ⚡ ***Exactly once* is a promise that is easy to write and hard to keep**, and
 * it is kept here by a decision that looks like an omission: **there is no
 * dismiss control.** ⛔ **A dismiss would change the promise from *shown once*
 * to *shown until dismissed*** — somebody who read it and navigated away would
 * meet it again tomorrow.
 */
import { StrictMode } from 'react';

import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { HM_COPY_04 } from '@/lib/home/copy';

const usePreferences = vi.hoisted(() => vi.fn());
const acknowledge = vi.hoisted(() => vi.fn());

vi.mock('@/lib/query/hooks/preferences', () => ({
  usePreferences,
  useAcknowledgeSetupComplete: () => ({ mutate: acknowledge }),
}));

import { SetupCompleteStrip } from '@/components/home/setup-complete-strip';

/** ⚡ `undefined` is the third state and the one that matters — the read has not landed. */
function preference(seen: boolean | undefined) {
  usePreferences.mockReturnValue({ data: seen === undefined ? undefined : { setup_complete_seen: seen } });
}

function strip(over: { complete?: boolean; activation?: boolean } = {}) {
  return render(
    <SetupCompleteStrip
      workspaceId="w-1"
      complete={over.complete ?? true}
      activation={over.activation ?? false}
    />,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  preference(false);
});

describe('🔴 shown exactly once, and recorded on RENDER rather than on dismiss', () => {
  it('📁 renders HM-COPY-04 and records that it did, in the same paint', () => {
    strip();

    expect(screen.getByText(HM_COPY_04)).toBeInTheDocument();
    expect(acknowledge).toHaveBeenCalledTimes(1);
  });

  it('⛔ offers NO way to dismiss it, because that would be a different promise', () => {
    /**
     * ⚡ **The absence is the mechanism.** 📁 *One-time* means the next visit
     * does not show it — ⛔ **not that it goes away when you click.**
     */
    strip();
    expect(screen.queryByRole('button')).toBeNull();
    expect(screen.queryByLabelText(/dismiss|close/i)).toBeNull();
  });

  it('⚠️ and records once under StrictMode, which is the condition the ref exists for', () => {
    /**
     * 🔴 **The first version of this test re-rendered and asserted one call —
     * and it PASSED with the ref deleted.** ⛔ **A plain re-render does not
     * re-run the effect at all**: `show` is unchanged and `mutate` is stable,
     * so the assertion was about a code path the test never reached.
     *
     * ⚡ **`StrictMode` is what the ref actually guards** — 📁 React invokes
     * effects twice in development to surface exactly this. **The server is
     * idempotent (*"the first moment wins"*), so a duplicate costs a request
     * rather than a wrong answer** — ✅ **the ref removes the request.**
     *
     * ⚠️ **Found by fire-testing: deleting the ref changed nothing, which is
     * the finding rather than a pass.**
     */
    render(
      <StrictMode>
        <SetupCompleteStrip workspaceId="w-1" complete activation={false} />
      </StrictMode>,
    );

    expect(acknowledge).toHaveBeenCalledTimes(1);
  });
});

describe('🔴 P-A — silent until the preference is actually known', () => {
  it('⛔ renders nothing while the read is in flight, and records nothing', () => {
    /**
     * ⚠️ **Rendering while unread would show the strip to somebody who was told
     * last week**, on every slow connection — ⛔ **and would BURN the one
     * showing they had left**, because the acknowledgement fires on paint.
     *
     * ⚡ **So the loading case is not merely cosmetic here: it would spend the
     * promise.**
     */
    preference(undefined);
    const { container } = strip();

    expect(container).toBeEmptyDOMElement();
    expect(acknowledge).not.toHaveBeenCalled();
  });

  it('⛔ and renders nothing once the answer is that they have already seen it', () => {
    preference(true);
    const { container } = strip();

    expect(container).toBeEmptyDOMElement();
    expect(acknowledge).not.toHaveBeenCalled();
  });
});

describe('📁 state 04 belongs to the ROLE composition, not to activation', () => {
  it('⛔ never announces completion beside the steps it just completed', () => {
    /**
     * 📁 State 04 is not an activation state: *"composition switches to SELLER,
     * OPERATIONS or EXECUTIVE."* ⚡ **A strip drawn on the activation
     * composition would congratulate somebody in front of the checklist they
     * are still looking at.**
     */
    const { container } = strip({ activation: true });

    expect(container).toBeEmptyDOMElement();
    expect(acknowledge).not.toHaveBeenCalled();
  });

  it('⛔ and says nothing while setup is not complete', () => {
    const { container } = strip({ complete: false });
    expect(container).toBeEmptyDOMElement();
    expect(acknowledge).not.toHaveBeenCalled();
  });

  it('✅ every branch above is refused for a DIFFERENT reason, and the positive proves it', () => {
    // ⚡ **The vacuity half for all four absences.** Without it, a component
    // that rendered nothing under every condition would pass them all.
    strip({ complete: true, activation: false });
    expect(screen.getByTestId('setup-complete')).toBeInTheDocument();
  });
});

describe('♿ it is a fact, not an interruption', () => {
  it('📁 4.1.3 — polite status, because the greeting owns the assertive queue', () => {
    strip();

    const status = screen.getByRole('status');
    expect(status).toHaveTextContent(HM_COPY_04);
    // ⛔ **Never `alert`** — nothing has gone wrong, and an assertive
    // announcement would interrupt whatever a screen reader was saying.
    expect(screen.queryByRole('alert')).toBeNull();
    // ♿ **The mark is decorative**; the sentence carries the meaning.
    expect(status.querySelector('[aria-hidden]')).not.toBeNull();
  });

  it('⚡ states what CHANGED, which is the design’s own requirement for this strip', () => {
    strip();
    expect(screen.getByText(/Home now shows your accounts, deals and signals/)).toBeInTheDocument();
  });
});
