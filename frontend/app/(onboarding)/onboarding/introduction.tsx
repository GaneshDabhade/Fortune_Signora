'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { cn } from '@/lib/design/cn';
import { Button } from '@/components/ui';

/**
 * **Screen `02 · Product introduction`** — 📁 the design's own heading:
 * *"three panels, skippable, never blocking."*
 *
 * ## ⛔ No rail, and that is the design
 *
 * ⚠️ **Every other screen sits in the 240px-rail frame; this one does not.** 📁
 * The design draws it as a bare 920px plane at `32px 36px`, because the
 * introduction is not a step — **it precedes the counted four and skipping it
 * changes nothing about the run.**
 *
 * ## 📁 Where the three panels' words come from
 *
 * ⚡ **The design specifies the panel TREATMENT and supplies the copy for one
 * of the three** — *"Every number traces back to something someone said"*, with
 * the cited AI-insight illustration beside it. ⛔ **The other two panels are
 * NOT invented here.** ✅ **Their sentences are this same design document's
 * own**, taken verbatim from the Welcome screen's capability cards, which is
 * where it states what the product does.
 *
 * ⚠️ **Recorded rather than quietly authored**: writing two panels of new
 * marketing prose would be product content nobody approved, and 📁
 * [§20e](../../../../CLAUDE.md) makes that a finding rather than a licence.
 *
 * ## ⚡ Never blocking
 *
 * 📁 *"skippable, never blocking"* — **Skip introduction is present on every
 * panel**, and it goes exactly where Next on the last panel goes.
 */
export function ProductIntroduction() {
  const router = useRouter();
  const [panel, setPanel] = useState(0);
  const current = PANELS[panel]!;
  const last = panel === PANELS.length - 1;

  const forward = () => {
    if (last) router.push(NEXT);
    else setPanel((was) => was + 1);
  };

  return (
    <div className="min-h-screen bg-canvas px-5 py-10 phone:py-16">
      <div className="mx-auto w-full max-w-[57.5rem] rounded-xl border border-border-soft bg-surface px-9 py-8 shadow">
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold tabular-nums text-content-subtle">
            {panel + 1} of {PANELS.length}
          </span>
          {/* ♿ **`aria-hidden`, because the count beside it already says the
              position in words.** Two announcements of one fact is the noise
              4.1.3 asks to avoid. */}
          <div aria-hidden className="flex gap-1.5">
            {PANELS.map((entry, index) => (
              <span
                key={entry.title}
                className={cn(
                  'h-1 w-7 rounded-full transition-colors duration-DEFAULT ease-premium',
                  index <= panel ? 'bg-accent' : 'bg-border-soft',
                )}
              />
            ))}
          </div>
          {/* ⚠️ **The path is a literal here and a constant three lines below,
              and that is not an oversight.** 📁 `infra/reachability.py` reads
              static route strings: `href={NEXT}` is a link a customer can use
              and a link the check cannot see, and it reported
              `/onboarding/organization` as having **no entrance at all** the moment
              this screen became its only door. ⛔ **Making the checker's job
              possible is cheaper than declaring an exception.** */}
          <Link
            href="/onboarding/organization"
            className="ml-auto text-label font-semibold text-content-subtle hover:text-content "
          >
            Skip introduction
          </Link>
        </div>

        <div className="mt-6 grid items-center gap-8 smalllaptop:grid-cols-2">
          <div>
            <h1 tabIndex={-1} className="text-title text-content outline-none">
              {current.title}
            </h1>
            <p className="mt-3 text-sm leading-relaxed text-content-muted">
              {current.body}
            </p>
            <div className="mt-[22px] flex gap-2">
              <Button onClick={forward}>{last ? 'Continue' : 'Next'}</Button>
              {/* ⛔ **Back is absent on the first panel rather than disabled** —
                  📁 a control that cannot act is the one this repository keeps
                  refusing to draw. */}
              {panel === 0 ? null : (
                <Button variant="secondary" onClick={() => setPanel((was) => was - 1)}>
                  Back
                </Button>
              )}
            </div>
          </div>

          {/* 📁 The design's right column: a `--sunken` well holding a
              `--surface` card bordered in `--ai-line`. ⛔ **The AI hue is
              reserved** — §14 — and this is content a model authored, which is
              the one thing that may wear it. */}
          <div className="rounded-lg bg-surface-sunken p-[18px]">
            <div className="rounded-md border border-ai-line bg-surface p-3.5">
              <div className="flex items-center gap-1.5">
                <span className="grid h-4 w-4 place-items-center rounded-sm bg-ai text-accent-contrast">
                  <svg
                    width="9"
                    height="9"
                    viewBox="0 0 16 16"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                    aria-hidden
                  >
                    <path d="M8 2v2.5M8 11.5V14M2 8h2.5M11.5 8H14" />
                  </svg>
                </span>
                <span className="text-2xs font-semibold text-ai">AI insight</span>
                <span className="ml-auto text-2xs text-content-subtle">4 of 5</span>
              </div>
              <p className="mt-2 text-label leading-relaxed text-content">
                Pricing pushback appears in three deals within a week of each slip
                <sup className="text-2xs font-semibold text-ai">1</sup>.
              </p>
              <p className="mt-2 border-t border-border-soft pt-2 text-2xs text-content-subtle">
                1 · Vantage QBR, 14 Jul, 38:12
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/** 📁 Where the introduction lets go — the first counted step. */
const NEXT = '/onboarding/organization';

const PANELS = [
  {
    title: 'See what moved',
    body: 'Every change since you last looked, ranked by what it costs you.',
  },
  {
    title: 'Every number traces back to something someone said',
    body: "Scores, risks and forecasts all carry their evidence: the call, the timestamp, the quote. If Signora can't cite it, Signora doesn't claim it.",
  },
  {
    title: 'Forecast you can defend',
    body: "The model's number, the rep's number, and the gap explained.",
  },
] as const;
