'use client';

import Link from 'next/link';

import { NothingSaid, StageBadge } from '@/components/accounts/account-commercial';
import { formatDay } from '@/components/intelligence/dates';
import {
  OpportunityMomentum,
  WorkflowStage,
} from '@/components/intelligence/opportunity';
import { StatedAbsence } from '@/components/feedback/stated-absence';
import { SkeletonText, TD, TR } from '@/components/ui';
import { formatMoney } from '@/lib/accounts/table';
import { ApiError } from '@/lib/api/client';
import type { ListedAccount } from '@/lib/api/types';
import { useAccountDecisionPackage, useAccountOpportunity } from '@/lib/query/hooks';
import type { AccountOwnerProps } from '@/components/accounts/account-owner';
import { peopleFrom } from '@/components/team/people';

/**
 * **The design's expanded row** — 📁 `Fortune Signora Companies.dc.html`,
 * *"Expanded · Vantage Logistics"*.
 *
 * ## 📁 The design's three panels, and what each one is here
 *
 * | Design | Here |
 * |---|---|
 * | **Open opportunities · 3** — name, amount, stage | ✅ **The account's opportunity**, its stage, who holds it, and how far the score has moved since it opened |
 * | **Inline edit · commits on ⏎** — an ACV input | ⛔ **Read-only, and it says why.** ⚠️ ACV is a *claim*, and Signora is not a provider |
 * | **Row-level AI** — one sentence + *Draft the intro →* | ✅ **The Decision Package's `summary`**, with the provenance that authored it. ⛔ No *Draft the intro* — nothing drafts |
 *
 * ## ⚠️ Why the opportunity panel is singular
 *
 * 🔴 **Signora's opportunity is NOT a CRM opportunity, and the difference is
 * not cosmetic.** 📁 [`opportunity.py`](../../../../backend/modules/opportunity_engine/domain/opportunity.py):
 * *"An opportunity records that **a human committed to something**"* — it has a
 * stage, an owner, the score that justified opening it and an append-only
 * history. ⛔ **It has no name and no amount**, because it is a commitment
 * rather than a deal line, and the endpoint is
 * `GET /accounts/{id}/opportunity` — **singular, 404 when nothing is open.**
 *
 * ⛔ **Drawing three rows of *name · amount · stage* would have required
 * inventing all three.** ✅ **What renders instead is the fact the design's
 * panel exists to carry** — *is anything being worked here, by whom, and has it
 * got better or worse since?* — 📁 and it is rendered by the components the
 * account brief already uses (`WorkflowStage`, `OpportunityMomentum`), not by a
 * second implementation of them ([§2](../../../../CLAUDE.md)).
 *
 * ## 🔴 Why there is no inline ACV edit
 *
 * 📁 [ADR-0409](../../../../docs/architecture/adr/0409-commercial-account-facts.md)
 * §5: ***"A claim is only produced where the provider supplies the fact."***
 * ⚠️ **A seller typing a number is not a provider supplying a fact**, and
 * `OPEN_ACV` has exactly one producer in the repository —
 * `provider_normalization/infrastructure/mappers/crm.py`. **There is no write
 * path, and there is deliberately none.**
 *
 * ⛔ **So the panel is NOT drawn as a bordered input that ignores ⏎.** 📁
 * [B-255](../../../../docs/BUGS.md): *a control that silently does nothing is
 * worse than one that is absent.* ✅ **It keeps the panel's occupancy — the
 * commercial figures — and states, once, where they come from.** ⚡ Which is
 * the more useful sentence anyway: *the number is wrong* and *the number is
 * wrong in Salesforce* have different fixes.
 *
 * ## ✅ The AI panel is the endpoint's first consumer anywhere
 *
 * `GET /workspaces/{id}/accounts/{id}/decision-package` has existed since the
 * AI Reasoning Engine shipped **and no screen read it** — 📁 the class
 * `infra/reachability.py` was built for. ⚡ **`summary` is documented as *"the
 * conclusion in one sentence, cited like any other"***, which is exactly the
 * shape the design's row-level AI block draws.
 *
 * ⛔ **No *Draft the intro →*.** ⚠️ `sales_engagement` answers *who* to approach
 * and why them; **nothing in the repository drafts a message**, and a link that
 * went nowhere is B-255 again.
 */
/**
 * ♿ **The id the expander names**, derived from the account rather than held in
 * state — ⛔ **two places computing one id is how `aria-controls` comes to point
 * at nothing** ([§2](../../../../CLAUDE.md), one authoritative representation).
 */
export function expandedRowId(accountId: string): string {
  return `account-expanded-${accountId}`;
}

export function ExpandedRow({
  row,
  span,
  workspaceId,
  viewerId,
  members,
}: {
  row: ListedAccount;
  /** ⚡ **How many columns the row must reach across.** Passed rather than
   * counted here: the page owns which columns are shown. */
  span: number;
  workspaceId: string | null;
  /** So the workflow line can say *you* rather than a name the reader would
   * have to recognise as their own. */
  viewerId: string | null;
  members: AccountOwnerProps['members'];
}) {
  return (
    <TR id={expandedRowId(row.account.account_id)}>
      <TD
        colSpan={span}
        /* 📁 **The design's plane** — `background:var(--sunken)`, and the row's
           own `--line-soft` rule beneath it. ⚡ **The 84px left indent is the
           checkbox column plus the expander plus the table's padding**, so the
           panel starts under the company name rather than under the tick. */
        className="border-b border-border-soft bg-surface-sunken p-0"
      >
        <div className="py-4 pl-[84px] pr-4">
          <div className="flex items-center gap-2.5">
            <p className="text-2xs font-semibold uppercase tracking-wide text-content-subtle">
              Expanded · {row.account.name ?? 'This account'}
            </p>
            {/* 📁 The design's right-aligned *Open full record*. ✅ Real: the
                account brief is a built screen. */}
            <Link
              href={`/accounts/${row.account.account_id}`}
              className="ml-auto text-xs font-semibold text-accent hover:underline "
            >
              Open full record
            </Link>
          </div>

          {/* 📁 **The design's `1.1fr 1fr 1fr`, gap 14px.** ⚠️ Stacked below the
              reference layout: three 15px-padded panels side by side on a
              narrow viewport are three unreadable columns. */}
          <div className="mt-3 grid gap-3.5 laptop:grid-cols-[1.1fr_1fr_1fr]">
            <OpportunityPanel
              accountId={row.account.account_id}
              workspaceId={workspaceId}
              viewerId={viewerId}
              members={members}
            />
            <CommercialPanel row={row} />
            <AiPanel accountId={row.account.account_id} workspaceId={workspaceId} />
          </div>
        </div>
      </TD>
    </TR>
  );
}

/** 📁 One of the design's panels — `--surface`, 12px radius, `--line-soft`. */
function Panel({
  label,
  ai = false,
  children,
}: {
  label: React.ReactNode;
  /** 📁 §14's reserved hue, and the only thing that may wear it: content a
   * model authored. */
  ai?: boolean;
  children: React.ReactNode;
}) {
  return (
    <section
      className={
        'rounded-lg border bg-surface p-4 ' + (ai ? 'border-ai/40' : 'border-border-soft')
      }
    >
      <p
        className={
          'text-xs ' +
          (ai ? 'flex items-center gap-1.5 font-semibold text-ai' : 'text-content-muted')
        }
      >
        {label}
      </p>
      <div className="mt-2">{children}</div>
    </section>
  );
}

/**
 * 📁 The design's *Open opportunities* panel.
 *
 * ⛔ **A 404 is the ordinary state and is NOT an error.** 📁 The endpoint's own
 * words: *"404 when nothing is open here"*, and the hook does not retry one.
 * ⚡ **So it renders a sentence, not a failure** — and the sentence says what
 * is true rather than *No data*.
 */
function OpportunityPanel({
  accountId,
  workspaceId,
  viewerId,
  members,
}: {
  accountId: string;
  workspaceId: string | null;
  viewerId: string | null;
  members: AccountOwnerProps['members'];
}) {
  const opportunity = useAccountOpportunity(workspaceId, accountId);
  const missing =
    opportunity.error instanceof ApiError && opportunity.error.status === 404;

  return (
    <Panel label="Open opportunity">
      {opportunity.isPending ? (
        <SkeletonText lines={2} />
      ) : missing ? (
        <p className="text-sm text-content-muted">
          Nothing is open here. Signora is not tracking this account.
        </p>
      ) : opportunity.data === undefined ? (
        <StatedAbsence subject="what is open at this account" />
      ) : (
        <div className="flex flex-col gap-2">
          <WorkflowStage
            opportunity={opportunity.data}
            viewerId={viewerId}
            people={peopleFrom(members)}
          />
          <OpportunityMomentum opportunity={opportunity.data} />
        </div>
      )}
    </Panel>
  );
}

/**
 * 📁 The design's *Inline edit* panel, **as a read**.
 *
 * ⚡ **The figures come from the row that is already on screen** — ⛔ not a
 * second fetch. The list published them, and reading them again here would be
 * a second answer to a question already answered.
 */
function CommercialPanel({ row }: { row: ListedAccount }) {
  return (
    <Panel label="Commercial · read from your sources">
      <dl className="flex flex-col gap-1.5">
        <Line label="Open ACV">
          {row.commercial.open_acv === null ? (
            <NothingSaid />
          ) : (
            formatMoney(row.commercial.open_acv)
          )}
        </Line>
        <Line label="Renewal">
          {row.commercial.renewal_date === null ? (
            <NothingSaid />
          ) : (
            formatDay(row.commercial.renewal_date)
          )}
        </Line>
        <Line label="Stage">
          {row.commercial.stage === null ? (
            <NothingSaid />
          ) : (
            <StageBadge stage={row.commercial.stage} />
          )}
        </Line>
      </dl>
      {/* 🔴 **The sentence that replaces the input.** ⚡ It names where the fix
          is, which a disabled field would not. */}
      <p className="mt-3 text-xs leading-relaxed text-content-subtle">
        Signora reads these from the system that reported them and does not author them.
        Correct them where they are kept.
      </p>
    </Panel>
  );
}

/**
 * 📁 The design's *Row-level AI* panel.
 *
 * ⚡ **The provenance line is not decoration.** 📁 `AccountNarration`'s contract
 * states the rule this follows: *"a customer reading generated language is
 * entitled to know what generated it **while they are reading it**"* — which is
 * why the model is beside the sentence rather than behind a hover.
 */
function AiPanel({
  accountId,
  workspaceId,
}: {
  accountId: string;
  workspaceId: string | null;
}) {
  const conclusion = useAccountDecisionPackage(workspaceId, accountId);
  const missing = conclusion.error instanceof ApiError && conclusion.error.status === 404;

  return (
    <Panel
      ai
      label={
        <>
          <Sparkle />
          Row-level AI
        </>
      }
    >
      {conclusion.isPending ? (
        <SkeletonText lines={2} />
      ) : missing ? (
        <p className="text-sm text-content-muted">
          Signora has not reached a conclusion about this account yet.
        </p>
      ) : conclusion.data === undefined ? (
        <StatedAbsence subject="what Signora concluded here" />
      ) : (
        <div className="flex flex-col gap-2">
          <p className="text-sm leading-relaxed text-content-muted">
            {conclusion.data.summary.text}
          </p>
          <p className="text-2xs text-content-subtle">
            {/* ⛔ **Never empty** — an uncited statement is refused before the
                package is stored, so the count is always a real number. */}
            {conclusion.data.summary.evidence.length === 1
              ? '1 cited fact'
              : `${conclusion.data.summary.evidence.length} cited facts`}
            {' '}· {conclusion.data.model}
          </p>
        </div>
      )}
    </Panel>
  );
}

/** 📁 The design's four-point spark, at the size it draws it. */
function Sparkle() {
  return (
    <svg
      width="11"
      height="11"
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      aria-hidden="true"
    >
      <path d="M8 2v2.5M8 11.5V14M2 8h2.5M11.5 8H14" />
    </svg>
  );
}

/** One `k` / `v` line of the commercial panel. */
function Line({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-baseline gap-3">
      <dt className="text-xs text-content-subtle">{label}</dt>
      <dd className="ml-auto text-sm font-semibold tabular-nums text-content">
        {children}
      </dd>
    </div>
  );
}
