'use client';

import Link from 'next/link';

import { cn } from '@/lib/design/cn';
import type { AccountAttention } from '@/lib/api/types';
import { useAccounts } from '@/lib/query/hooks';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';

import { OnboardingShell } from '../onboarding-shell';
import { useOnboardingExit } from './exit';

/**
 * **Screen `09 Completion` — *"the payoff is the product, not a
 * congratulation"*.**
 *
 * ### 🔴 The design's third finding cannot be produced, and it is not faked
 *
 * 📁 The mock's three are **Accounts read · At risk today · Forecast gap**, and
 * the third asks for *"the gap between the model and the committed number"*.
 * ⛔ **`buying_score_engine` refuses it in two files** — *"it does not forecast
 * a purchase"* and *"no recommendation, no opportunity, and no probability"*.
 * **That is domain law, not a missing endpoint**, and producing it here would
 * create a second meaning for a Signora score.
 *
 * 📁 **Raised as [C-1528](../../../../docs/LANE_COORDINATION.md).** ⚡ **The
 * screen keeps the design's three-across structure** and gives the third card
 * a stated absence rather than a number — ⛔ **the card is not deleted**,
 * because a two-card row is a different design, and **the absence is a fact
 * about this product worth showing on the one screen that explains what
 * Signora does.**
 *
 * ### ✅ The two that are real are genuinely read
 *
 * ⚡ Both come from the attention list, which is a shipped producer: **how many
 * accounts Signora is watching**, and **how many are contested or have a
 * stale reading**. ⛔ **Neither is a money figure** — 📁 [ADR-0409](../../../../docs/architecture/adr/0409-commercial-account-facts.md)
 * §5 forbids summing `OPEN_ACV` across a set where some accounts have none,
 * because the total would silently understate and nobody reading it could
 * tell. **A count of accounts is a fact; a partial sum of money is not.**
 *
 * ### ⚠️ It never claims to have read a CRM
 *
 * 📁 The design writes *"Signora read 8,412 accounts and 96 calls from your
 * CRM."* ⛔ **Nothing here has read a CRM unless one was actually connected**,
 * and screen `07` makes that skippable by design. **The sentence names what
 * was actually read.**
 */
export function CompleteForm() {
  const { exit } = useOnboardingExit();
  const { activeWorkspace } = useWorkspaceContext();
  const accounts = useAccounts(activeWorkspace?.id ?? null);

  const rows: readonly AccountAttention[] = accounts.data?.items ?? [];
  const watching = rows.length;
  // ⚡ **`stale`, not `expired`** — 📁 `EvidenceState` is
  // `current | cooling | stale`, and `tsc` caught the guess. **The vocabulary
  // is the contract's, never the one that sounded right.**
  const unsettled = rows.filter((r) => r.contested || r.evidence === 'stale').length;
  const name = activeWorkspace?.name ?? null;

  return (
    <OnboardingShell
      // ⛔ **No rail** — 📁 the design draws a single `40px 44px` plane, and
      // there are no steps left to count.
      roomy
      largeTitle
      lead={
        /**
         * 📁 *"44px circle, `--pos-tint` on `--pos-line`, a 21px check in
         * `--pos`"* — ⚡ **the one moment in the flow that celebrates
         * anything**, and it is a mark rather than a sentence, because 📁 the
         * design's own title says the payoff is the product and not a
         * congratulation.
         *
         * ♿ `aria-hidden` — the heading says *"… is ready"* right beneath it.
         */
        <span
          aria-hidden
          className="mb-[18px] grid h-11 w-11 place-items-center rounded-full border border-success/30 bg-success-subtle text-success"
        >
          <svg
            width="21"
            height="21"
            viewBox="0 0 16 16"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.9"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="m3.5 8.5 3 3 6-6.5" />
          </svg>
        </span>
      }
      title={name === null ? 'You are ready' : `${name} is ready`}
      description={
        accounts.isLoading
          ? 'Reading what is in your account…'
          : summarise(watching, accounts.isError)
      }
      actions={
        <>
          <button
            type="button"
            onClick={exit}
            className="inline-flex h-control-md items-center rounded-md bg-accent px-[18px] text-[13.5px] font-semibold text-accent-contrast shadow-sm transition-colors hover:bg-accent-hover focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
          >
            Go to my home page
          </button>
          {/* 📁 The design's second action, and it goes somewhere real. */}
          <Link
            href="/settings/team"
            className="inline-flex h-control-md items-center rounded-md border border-border px-[15px] text-[13.5px] font-semibold text-content transition-colors hover:border-accent hover:text-accent focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
          >
            Invite your team
          </Link>
          {/* ⛔ **The design's third action — *"Take the 2-minute tour"* — is
              NOT drawn.** 📁 No tour exists anywhere in this product, and
              [B-255](../../../../docs/BUGS.md): **a control that silently does
              nothing is worse than one that is absent.** ⚠️ Welcome's *"Take
              the tour first"* is the same absence one screen away and is
              recorded there. */}
        </>
      }
    >
      {/* 📁 *"grid-template-columns:repeat(3,1fr); gap:12px"*. */}
      <div className="grid gap-3 smalllaptop:grid-cols-3">
        <Finding
          label="Accounts on your list"
          value={accounts.isLoading ? null : accounts.isError ? null : watching.toLocaleString()}
          detail={
            accounts.isError
              ? 'We could not read this just now. It will be on your home page.'
              : watching === 0
                ? 'Connect a source and the first ones arrive with it.'
                : 'Signora is watching these and will tell you when one moves.'
          }
        />
        <Finding
          label="Needing a look"
          value={accounts.isLoading || accounts.isError ? null : unsettled.toLocaleString()}
          detail={
            accounts.isError
              ? 'We could not read this just now.'
              : unsettled === 0
                ? 'Nothing is contested and no reading has gone stale.'
                : 'Contested, or the evidence behind the reading has gone stale.'
          }
        />
        {/* 🔴 **The design's third card, kept and honest.** 📁 [C-1528](../../../../docs/LANE_COORDINATION.md). */}
        <Finding
          label="Forecast gap"
          value={null}
          detail="Signora does not forecast. It ranks what deserves your attention and shows the evidence — there is no predicted number to compare against."
          absent
        />
      </div>

      {/* 📁 The design's AI line beneath the findings. ⛔ **It says what the
          product actually did with the answers** — the goals ordered the home
          page — **and names no deal count and no money figure**, because
          neither has a producer. */}
      <div className="mt-3.5 flex items-start gap-3 rounded-lg border border-ai/30 bg-ai-subtle px-[17px] py-[15px]">
        <span
          aria-hidden
          className="mt-px grid h-5 w-5 flex-none place-items-center rounded-sm bg-ai"
        >
          <svg
            width="11"
            height="11"
            viewBox="0 0 16 16"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.7"
            strokeLinecap="round"
            className="text-accent-contrast"
          >
            <path d="M8 2v2.5M8 11.5V14M2 8h2.5M11.5 8H14M4 4l1.8 1.8M10.2 10.2 12 12" />
          </svg>
        </span>
        <p className="text-[13.5px] leading-[1.6] text-content">
          Your home page is ordered by what you told us you are trying to fix. Everything Signora
          shows you cites the evidence behind it — change any of it in Settings.
        </p>
      </div>
    </OnboardingShell>
  );
}

/**
 * 📁 *"padding:18px; border-radius:12px; box-shadow:--e1"* — a label, a 24px
 * tabular figure, and a line of context.
 *
 * ⚠️ **`value === null` is three different things and the card must not
 * flatten them**: still reading, could not read, and *there is no such number*.
 * ⛔ **The first two say so in the detail line and the third is marked
 * `absent`** — 📁 [P-A](../../../../docs/DOMAIN_DISCOVERY_REGISTER.md), and a
 * dash where a figure belongs reads as zero to everybody.
 */
function Finding({
  label,
  value,
  detail,
  absent = false,
}: {
  label: string;
  value: string | null;
  detail: string;
  absent?: boolean;
}) {
  return (
    <div
      className={cn(
        'rounded-lg border border-border-soft p-[18px]',
        absent ? 'bg-surface-sunken' : 'bg-surface shadow-sm',
      )}
    >
      <p className="text-[11.5px] text-content-subtle">{label}</p>
      {value === null ? (
        // ⛔ **A word, never a dash or a zero.**
        <p
          className={cn(
            'mt-2 text-sm font-semibold',
            absent ? 'text-content-subtle' : 'text-content-muted',
          )}
        >
          {absent ? 'Not something Signora produces' : 'Not available'}
        </p>
      ) : (
        <p className="mt-2 text-2xl font-bold tabular-nums tracking-[-0.026em] text-content">
          {value}
        </p>
      )}
      <p className="mt-1.5 text-xs leading-[1.5] text-content-muted">{detail}</p>
    </div>
  );
}

/** ⛔ **Never *"Signora read 8,412 accounts from your CRM"* unless it did.** */
function summarise(watching: number, failed: boolean): string {
  if (failed) {
    return 'Your organization is live. We could not read your account list just now — it will be on your home page.';
  }
  if (watching === 0) {
    return 'Your organization is live. Connect a source and Signora starts reading straight away.';
  }
  return `Signora has already read what is in your account. Here is what it found before you opened it.`;
}
