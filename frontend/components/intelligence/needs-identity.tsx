'use client';

import { AttentionScore } from '@/components/intelligence/attention';
import { Card, CardBody } from '@/components/ui';
import type { AccountAttention, AccountIdentity } from '@/lib/api/types';

/**
 * Real evidence about a company nobody can name.
 *
 * **A6, and it is [C-321](../../../docs/LANE_COORDINATION.md) wearing a
 * slice's name.** The ruling answers six questions about a record Signora
 * cannot identify, and four of them are what this section is:
 *
 * | | Ruled |
 * |---|---|
 * | Appear at all? | **Yes** — hiding it discards real intelligence |
 * | On the working list? | **No** — that list answers *"who should I call?"* |
 * | Contribute to a score? | **Yes** — the score measures evidence, and the evidence is real |
 * | Be workable? | **Never.** Today it is |
 *
 * ### Identity and significance are different axes, and the list was
 * multiplying them into one number
 *
 * `70b04700` has four weeks of elevated research on Design Systems, peaked at
 * 87, and has no name ([PX-301](../../../docs/PRODUCT_EXPERIENCE.md)).
 * **That combination is genuinely interesting and genuinely not actionable** —
 * and the working list offered *"I'm working this"* on it, which is a button
 * that cannot work being pressed by somebody who then has nothing to do.
 *
 * ### So it keeps the score and offers no action
 *
 * The score is **not** recomputed, discounted or hidden: it measures evidence,
 * and the evidence is real. What changes is that this is not a call list.
 * **No ownership badge, no hand-over, no *"I'm working this"*** — there is
 * nobody to call, and a control that goes nowhere costs more trust than an
 * absent one.
 *
 * ### It is a read today, and that limit is stated rather than papered over
 *
 * C-321 says *"`Needs identity` — a queue with its own workflow, not a
 * filter"*, and **the workflow was not specified, because there is nothing yet
 * for a customer to do about it**: Signora has no capability by which a person
 * names an account. A6's own reuse audit reached the same place — the read
 * *"is worthless without knowing what the queue does"* — so this builds the
 * four answers that were ruled and **invents no fifth**.
 *
 * **When a naming capability exists, this is where its action belongs.**
 */
export function NeedsIdentity({
  accounts,
  identities,
}: {
  /** Already partitioned by the caller, which is where the identities live. */
  accounts: AccountAttention[];
  /** Only to show how much is known about a company that cannot be named —
   * a source count is evidence of substance, and it is the one thing that
   * distinguishes a record worth chasing from a stray. */
  identities: ReadonlyMap<string, AccountIdentity> | undefined;
}) {
  // Nothing to say, and no section explaining its absence. A workspace whose
  // sources name everything should never learn this queue exists.
  if (accounts.length === 0) return null;

  return (
    <section className="flex flex-col gap-3">
      <div>
        <h2 className="text-sm font-semibold text-content">Needs identity</h2>
        <p className="mt-1 text-sm text-content-muted">
          {/* **The sentence that stops this reading as a defect.** These rows
              are not broken records; they are evidence Signora holds and
              cannot attach to a company anybody can call. */}
          Signora has evidence about {accounts.length === 1 ? 'this company' : 'these companies'}{' '}
          and no source has named{' '}
          {accounts.length === 1 ? 'it' : 'them'}. There is nobody to call yet, so{' '}
          {accounts.length === 1 ? 'it is' : 'they are'} kept here rather than on your list.
        </p>
      </div>

      <ul className="flex flex-col gap-2">
        {accounts.map((account) => (
          <li key={account.id}>
            <Card>
              <CardBody className="flex items-start justify-between gap-4 py-3">
                <div className="min-w-0">
                  {/* **Not `EntityName`, and deliberately not a link.** That
                      component renders a truncated id as an openable heading,
                      which is right on the working list where a seller most
                      wants to open the one nobody has named. Here the row is
                      already the statement *we cannot name this*, and dressing
                      an id as a name would put the id back in the position the
                      name would occupy. */}
                  <p className="font-mono text-sm text-content-subtle">
                    {account.account_id.slice(0, 8)}
                    <span className="sr-only"> — no source has named this account</span>
                  </p>
                  <Evidence identity={identities?.get(account.account_id)} />
                </div>
                {/* **The score is kept, unchanged.** It measures evidence, the
                    evidence is real, and discounting it here would be this
                    screen overruling the scoring model — which is a reviewed
                    artifact and not a render's to second-guess. */}
                <div className="w-9 shrink-0 text-right">
                  <AttentionScore score={account.score} />
                </div>
              </CardBody>
            </Card>
          </li>
        ))}
      </ul>
    </section>
  );
}

/**
 * How much is known about a company that cannot be named.
 *
 * **A count of sources, never a judgement.** Four sources reporting on one
 * unnamed record is a different thing from one, and it is the only signal a
 * reader has about whether this is worth anybody's time — but the product does
 * not say which, because it has no basis to.
 */
function Evidence({ identity }: { identity: AccountIdentity | undefined }) {
  if (identity === undefined || identity.source_count === 0) return null;
  return (
    <p className="mt-0.5 text-xs text-content-subtle">
      {identity.source_count === 1
        ? '1 source has reported on it'
        : `${identity.source_count} sources have reported on it`}
    </p>
  );
}
