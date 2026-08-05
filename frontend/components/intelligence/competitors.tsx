import { Card, CardBody, CardHeader, CardTitle } from '@/components/ui';
import type { DeclaredCompetitors } from '@/lib/api/types';

/**
 * Who this workspace competes against — **read on an account, declared once.**
 *
 * ### The honest framing, and why it is the whole design of this section
 *
 * `GET /competitors` returns a **workspace declaration**: the names a customer
 * typed, identical on every account they open. A section headed *"Competitors"*
 * on one company's page would therefore be read as *"these competitors are at
 * this account"* — which Signora has not said, does not know from this
 * contract, and would be inventing on every account where it is false.
 *
 * **So the section says what it is.** It is the list you told us to watch for,
 * shown where you are about to have a conversation, and the heading and the
 * sentence beneath it both say so.
 *
 * ### What the account-specific version actually is
 *
 * Signora *can* say a competitor is present at an account, and it says it
 * somewhere else: `competitor_entry` is a **signal**, derived by matching a
 * `TECHNOLOGY_ADOPTED` business event against this same declared list
 * ([ADR-0403](../../../docs/architecture/adr/0403-signal-engine-reads-a-declaration.md)).
 * It appears in the hypotheses section above, with its evidence and its
 * limitations, like every other signal.
 *
 * **This section deliberately does not reproduce that.** Marking names here as
 * *detected* would put the same fact on the page twice, in two vocabularies,
 * with only one of them carrying the evidence — and the copy without the
 * evidence is the one a reader would quote (`CLAUDE.md` §2).
 *
 * ### Nothing here is graded
 *
 * No threat level, no rank, no ordering by importance. `commercial_profile`
 * records the names and evaluates none of them; how much a rival moves an
 * account is decided by a reviewed scoring model, not by a list a customer
 * typed.
 */
export function CompetitorContext({
  competitors,
  isError = false,
}: {
  competitors: DeclaredCompetitors | undefined;
  /** **Absence and failure are two different facts** ([C-226](../../../docs/LANE_COORDINATION.md)).
   * Added in TASK-903, which put a second declaration on this page and found
   * this one had the class it was written to avoid: a failed read and a
   * workspace that has declared nothing both rendered as silence, so an outage
   * was indistinguishable from an empty declaration on the one screen where a
   * seller would act on it. */
  isError?: boolean;
}) {
  if (isError) {
    return (
      <Card>
        <CardBody>
          <p className="text-sm leading-6 text-content-muted">
            Signora could not load who your organization competes against. Nothing your
            organization has declared has been lost — reload to try again.
          </p>
        </CardBody>
      </Card>
    );
  }

  /**
   * **Version 0 means nothing has been declared** — which the type documents
   * as different from a customer who declared an empty list. Either way there
   * is nothing to show, and a section explaining its own absence on every
   * account of a workspace that has not filled this in would be noise on the
   * page a seller lives on. The declaration screen is where that prompt
   * belongs.
   */
  if (competitors === undefined || competitors.competitors.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Who you compete against</CardTitle>
      </CardHeader>
      <CardBody>
        <p className="text-xs text-content-subtle">
          {/* The sentence that stops the list being read as an account fact. */}
          Your declared list, the same on every account. Signora says a competitor is
          <em> at </em>
          an account by raising a signal, with its evidence, above.
        </p>
        <ul className="mt-3 flex flex-wrap gap-2">
          {competitors.competitors.map((competitor) => (
            <li
              key={competitor.id}
              className="rounded-md border border-border px-2 py-1 text-sm text-content"
            >
              {competitor.name}
            </li>
          ))}
        </ul>
      </CardBody>
    </Card>
  );
}
