import type { Connection, IntegrationSystem } from '@/lib/api/types';

/**
 * **An answer about THIS workspace** — [TASK-1420](../../../../docs/BACKLOG.md),
 * against 📁 `docs/design-snapshot/screens/Fortune Signora Help Center.dc.html`
 * §01 ([D-138](../../../../docs/DECISION_REGISTER.md)).
 *
 * > 📁 ***"Nothing here asks someone to describe their own account back to us —
 * > every route into support arrives carrying the workspace, the plan, the
 * > screen, and the correlation ID."***
 *
 * ## ⚡ The row names its own failure mode, and this file is the answer to it
 *
 * 📁 **[TASK-1420](../../../../docs/BACKLOG.md)'s risk**: ⛔ *"shipping a
 * generic documentation site and calling the workflow done. The workspace-aware
 * answer is the whole differentiator; documentation alone is the commodity
 * half."* ⚡ **So the answer is what this row builds, and the documentation is
 * what it does not.**
 *
 * ## 🔴 It is DERIVED, not generated, and that is a constraint rather than a shortcut
 *
 * 📁 **The design's worked example is LLM prose**: *"A profile change on 3
 * August made `Renewal_Risk__c` read-only for the integration user, so Signora
 * held 41 queued writes rather than dropping them."*
 *
 * ⛔ **This lane may not fabricate an LLM response** — no mock provider, no
 * fake inference. ⚠️ **And it cannot make a real one here**: 📁 `ai_platform`
 * holds the provider, **its `public/` is empty, so no module may consume it**,
 * and this row's budget is 🟢 `frontend/app/(app)/help/**` with **no backend at
 * all.** ⛔ **Raised, not worked around.**
 *
 * ✅ **What IS available is the telemetry the design's own example reads.** 📁
 * `Connection` publishes `health`, `attention`, `reason` and `connected_at`,
 * and 📁 [TASK-407](../../../../docs/BACKLOG.md) made `health` mean *what
 * happened when Signora last actually TRIED to use it* — **distinct from
 * `state`, which is what the records imply.** ⚡ **That distinction is the
 * entire content of the design's example**: *paused, not broken.*
 *
 * ⛔ **So this composes a true sentence from real fields and cites them.** ✅ **A
 * derived answer that is correct beats generated prose that is plausible** —
 * and 📁 [§2](../../../../CLAUDE.md) puts it more sharply: **a customer acting
 * on a fabricated answer is worse off than one told nothing.**
 *
 * ## ⚠️ What it deliberately will NOT answer
 *
 * ⛔ **It answers nothing it cannot source.** **A question with no connected
 * system behind it returns `null`**, and the screen says so rather than
 * producing a paragraph of general advice with a workspace name pasted into it
 * — **which is the *generic documentation site* the row warns about, wearing an
 * answer's clothes.**
 */

/** A citation the customer can open and check. ⛔ Never a footnote to prose. */
export interface AnswerSource {
  label: string;
  /** ⚡ Where the fact came from, as a route this product has. */
  href: string;
}

export interface WorkspaceAnswer {
  /** The finding, in one sentence a person can act on. */
  headline: string;
  /** What follows from it, including what is NOT affected. */
  detail: string;
  /** ⛔ **At least one, always** — an answer with no source is prose. */
  sources: readonly AnswerSource[];
  /** ⚡ The severity the sentence carries, for the surface to render. */
  tone: 'healthy' | 'degraded' | 'unknown';
}

const CONNECTIONS_HREF = '/settings/connections';

/**
 * 📁 **The design's worked question is about a named system** — *"why did my
 * Salesforce write-back stop"*. ⚡ **Matching on the integration's own label
 * rather than a keyword list**, so a system this workspace has connected is
 * findable by the name the customer sees, and one it has not is not matched at
 * all.
 */
function mentioned(question: string, connection: Connection): boolean {
  const asked = question.toLowerCase();
  return (
    asked.includes(connection.label.toLowerCase()) ||
    asked.includes(connection.integration.toLowerCase())
  );
}

/**
 * ⛔ **`null` when nothing can be sourced.** ⚡ **The caller renders a
 * `StatedAbsence`, not an apology** — 📁 the same rule the rest of this product
 * applies to a missing figure.
 */
export function answerFor(
  question: string,
  systems: readonly IntegrationSystem[],
  connections: readonly Connection[],
): WorkspaceAnswer | null {
  if (question.trim() === '') return null;

  const named = connections.filter((c) => mentioned(question, c));
  // ⚡ **A question that names nothing connected is not answered from
  // telemetry.** ⛔ Answering it anyway would mean answering every question the
  // same way, which is the commodity half pretending to be the differentiator.
  if (named.length === 0) return null;

  // 🔴 **The unhealthy one leads.** A person asking a help question during an
  // outage needs the broken system first, not alphabetical order.
  const ranked = [...named].sort((a, b) => rank(b.health) - rank(a.health));
  const subject = ranked[0];
  if (subject === undefined) return null;

  const sources: AnswerSource[] = [
    { label: `${subject.label} connection`, href: CONNECTIONS_HREF },
  ];

  if (subject.health === 'degraded') {
    return {
      tone: 'degraded',
      // 📁 *"paused, not broken"* — ⚡ the distinction `health` exists to carry,
      // said in the customer's words rather than the field's.
      headline: `${subject.label} is connected, and Signora could not use it the last time it tried.`,
      detail:
        subject.reason !== null
          ? `The system reported: ${subject.reason}. Reconnecting from Connections re-checks it straight away.`
          : 'The system did not say why. Reconnecting from Connections re-checks it straight away.',
      sources,
    };
  }

  if (subject.health === 'unknown') {
    return {
      tone: 'unknown',
      headline: `Signora has not tried to use ${subject.label} since it was connected.`,
      // ⛔ **Says what is NOT known.** A confident *"it is working"* here would
      // be the records implying health that nothing measured.
      detail:
        'Checking it from Connections asks the system directly, which is the only thing that answers this.',
      sources,
    };
  }

  return {
    tone: 'healthy',
    headline: `${subject.label} was working the last time Signora used it.`,
    detail:
      subject.connected_at !== null
        ? `It has been connected since ${new Date(subject.connected_at).toLocaleDateString()}. If something still looks wrong, the problem is likelier to be what the other system is sending than the connection itself.`
        : 'If something still looks wrong, the problem is likelier to be what the other system is sending than the connection itself.',
    sources,
  };
}

function rank(health: Connection['health']): number {
  if (health === 'degraded') return 2;
  if (health === 'unknown') return 1;
  return 0;
}

/**
 * ⚡ **Exported so the surface can say what it CAN answer about**, rather than
 * offering a search box that silently answers nothing.
 *
 * ⛔ **Only connected systems.** 📁 The design's suggestions are contextual —
 * *"because you were just on CRM Integrations"* — **and a suggestion about a
 * system this workspace has not connected is the general-advice failure again.**
 */
export function answerableSubjects(connections: readonly Connection[]): readonly string[] {
  return connections.map((c) => c.label);
}
