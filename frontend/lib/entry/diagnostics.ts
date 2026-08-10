/**
 * **Why did I land here — answerable without reproducing the login.**
 * [TASK-1403](../../../docs/BACKLOG.md), [workflow 29](../../../docs/coordination/workflows.toml).
 *
 * ## 📁 The design's sentence, which it states twice
 *
 * > ***"Every rule carries a reason code. The code is written to the session,
 * > logged with the redirect, and shown to support in the diagnostics bundle —
 * > so 'why did I land here' is answerable WITHOUT REPRODUCING THE LOGIN."***
 *
 * ⚡ **That last clause is the requirement and everything else is
 * implementation.** ⛔ **All three or none**: a code on the session tells the
 * person's own browser and nobody else · a line in a log has no session to
 * join it to · a bundle with nothing in it is a screen. **Any two of them
 * still require reproducing the login**, which is the one thing the sentence
 * forbids.
 *
 * ## ⛔ The rules stay pure, so none of this happens inside one
 *
 * 📁 ***"Rules are pure: same inputs, same destination, no network call inside
 * the decision."*** ⚡ **Every function here takes a decision that has already
 * been made** and returns a value; ⛔ **nothing in this file reaches a clock, a
 * store or a network either** — the moment arrives as an argument for the same
 * reason the standings do ([`session.ts`](./session.ts)).
 *
 * ## 🔴 This is not a second log
 *
 * ⚠️ **The row is explicit**: a reason code is a security-relevant record —
 * `ACCOUNT_LOCKED`, `STEPUP_REQUIRED` say why somebody was refused — so **it
 * belongs in the security event stream [TASK-492](../../../docs/BACKLOG.md)
 * writes, not in a second one.** ✅ **So {@link entryRecord} produces a record
 * shaped to be handed to that stream verbatim** — `kind` is `noun.verb_past`,
 * the two identities travel together, and `detail` is refused if it carries a
 * credential, **which are that port's three rules mirrored here so a producer
 * cannot build something it would reject.**
 *
 * ⛔ **The producer that hands it over is NOT this row** — the stream is
 * Python, this is `frontend/lib/entry/**`, and the row's Change Budget is
 * 🟢 this directory · 🟠 a session field · 🔴 **nothing**. **Stated rather than
 * exceeded.**
 */

import { GATES, type Gate, type ReasonCode } from './reasons';
import type { EntryDecision } from './session';

/**
 * ⚡ **The stream's kind grammar, and the only kind this engine produces.**
 *
 * 📁 `SecurityEventWriter` raises `MalformedEventKind` for anything that is not
 * `noun.verb_past`. ⛔ **One kind, not twenty-four**: the reason code is the
 * detail, and a kind per code would make every new rule a schema change to a
 * table this module does not own.
 */
export const ENTRY_EVENT_KIND = 'entry.resolved' as const;

/**
 * **What is written to the session** — the first of the design's three.
 *
 * ⛔ **The code, the gate and the moment, and nothing else.** ⚠️ **Not the
 * route**: a session that carried the destination would be a second copy of a
 * fact the URL already states, and the two would disagree the moment somebody
 * navigated ([§2](../../../CLAUDE.md), *truth has exactly one authoritative
 * representation*).
 *
 * ⛔ **And never the workspace id.** 🔴 **The session is readable by the
 * browser**, so anything on it is disclosed to whoever holds the machine —
 * which is precisely the reader the bundle's tenancy rule below exists to
 * bound. **The id is on the record, which support reads; it is not on the
 * session, which anyone reads.**
 */
export interface EntryMark {
  readonly reason: ReasonCode;
  readonly gate: Gate;
  /** ISO-8601. **Passed in**, never read from a clock in this module. */
  readonly at: string;
}

export function entryMark(decision: EntryDecision, at: string): EntryMark {
  return { reason: decision.reason, gate: decision.gate, at };
}

/**
 * **The redirect, logged with its reason** — the second of the three, and the
 * record the security event stream can take unchanged.
 *
 * ⚡ **`correlationId` is what makes it joinable.** 📁 [§16](../../../CLAUDE.md)
 * already requires it on every line the platform emits, so the reason **joins
 * the record the platform already keeps** rather than starting a parallel one —
 * which is the row's own measured reuse.
 */
export interface EntryRecord {
  readonly kind: typeof ENTRY_EVENT_KIND;
  /** Whose entry this was. */
  readonly subjectId: string;
  /**
   * 🔴 **Who was acting.** 📁 The stream carries `subject_id` and `acting_for`
   * **both required**, because *"a signature a caller can satisfy with one
   * identity is a signature that will eventually be satisfied with one."*
   * ⚡ **Equal to `subjectId` for an ordinary sign-in**, and different when
   * support is impersonating — ⛔ **which is the exact case a diagnostics
   * bundle must not lose.**
   */
  readonly actingFor: string;
  /** ⛔ **`null` when the decision resolved no workspace** — gates 1 and 2 fire
   * before any workspace is loaded, and inventing one there would attribute an
   * account-level refusal to a tenant. */
  readonly workspaceId: string | null;
  readonly reason: ReasonCode;
  readonly gate: Gate;
  readonly route: string;
  readonly correlationId: string;
  readonly at: string;
}

/**
 * 🔴 **Keys a record may never carry**, mirroring the stream's own refusal.
 *
 * ⛔ **`ForbiddenDetailKey` is raised by the backend type on construction.**
 * ⚡ **Mirrored rather than trusted**: a producer that only discovers the rule
 * when the server rejects it has already put the credential in a browser's
 * memory, and on the wire.
 */
const FORBIDDEN = ['password', 'token', 'secret', 'credential', 'authorization', 'cookie'];

export class ForbiddenDetail extends Error {}

/**
 * ⚡ **The decision, made joinable.**
 *
 * @throws {ForbiddenDetail} when any string in the record looks like a
 * credential. 🔴 **Checked on the values, not only the keys** — this record has
 * a fixed shape, so the way a secret reaches it is somebody passing one as a
 * `correlationId` or a `route`, not by adding a field.
 */
export function entryRecord(
  decision: EntryDecision,
  context: {
    subjectId: string;
    /** Defaults to `subjectId` — an ordinary sign-in acts for itself. */
    actingFor?: string;
    correlationId: string;
    at: string;
  },
): EntryRecord {
  for (const [name, value] of Object.entries(context)) {
    if (typeof value !== 'string') continue;
    const lowered = value.toLowerCase();
    if (FORBIDDEN.some((word) => lowered.includes(word))) {
      throw new ForbiddenDetail(
        `${name} looks like a credential, and an entry record is readable by support. ` +
          'The security event stream refuses this on construction; refusing it here ' +
          'keeps it out of the browser as well.',
      );
    }
  }

  return {
    kind: ENTRY_EVENT_KIND,
    subjectId: context.subjectId,
    actingFor: context.actingFor ?? context.subjectId,
    workspaceId: decision.workspaceId,
    reason: decision.reason,
    gate: decision.gate,
    route: decision.route,
    correlationId: context.correlationId,
    at: context.at,
  };
}

/**
 * **The support bundle** — the third, and the one the Definition of Done is
 * written about: 📁 *"support can answer* why did I land here *from the bundle
 * alone, without a reproduction."*
 *
 * ## 🔴 It is workspace-tenanted, and that is the Security Invariant
 *
 * ⛔ **The row names it before it is met**: *"a diagnostics bundle is a
 * data-egress surface… it is workspace-tenanted like everything else, and that
 * is stated here rather than assumed because a debug artifact is where tenancy
 * is usually forgotten."*
 *
 * ⚡ **So the workspace is a required argument and the filter is not optional.**
 * ⛔ **A signature that let a caller ask for *everything* is a signature
 * somebody will eventually call that way** ([§2](../../../CLAUDE.md), *types
 * should make incorrect architecture impossible*).
 *
 * ⚠️ **Records with no workspace are kept.** 🔴 **Gates 1 and 2 fire before any
 * workspace is loaded** — `ACCOUNT_SUSPENDED`, `SESSION_EXPIRED` — **and those
 * are the refusals support is most often asked about.** ✅ **They belong to the
 * person rather than to a tenant, so they leak nothing about another workspace
 * and dropping them would answer the commonest question with silence.**
 */
export interface DiagnosticsBundle {
  readonly workspaceId: string;
  readonly subjectId: string;
  readonly entries: readonly EntryRecord[];
  /** ⚡ **How many were withheld as another workspace's.** ⛔ **Stated rather
   * than silent**: support seeing eleven of fourteen needs to know the three
   * exist, or they will read the gap as a missing record and chase it. */
  readonly withheld: number;
}

export function diagnosticsBundle(
  records: readonly EntryRecord[],
  scope: { workspaceId: string; subjectId: string },
): DiagnosticsBundle {
  const mine = records.filter(
    (record) =>
      record.subjectId === scope.subjectId &&
      (record.workspaceId === null || record.workspaceId === scope.workspaceId),
  );

  return {
    workspaceId: scope.workspaceId,
    subjectId: scope.subjectId,
    entries: mine,
    withheld: records.length - mine.length,
  };
}

/**
 * **The sentence a support engineer reads**, in the words of the gate that
 * produced it.
 *
 * ⚡ **Why a sentence and not the raw code.** 📁 The design puts the gate on
 * every rule so a decision can name it, and **a support engineer asking *why*
 * is better served by *"gate 4, workspace standing"* than by a code alone** —
 * which is [`reasons.ts`](./reasons.ts)'s own stated reason for carrying it.
 *
 * ⛔ **This is not customer copy.** It is read by support, so it names the gate
 * rather than translating it — 📁 [ADR-0034](../../../docs/architecture/adr/0034-ubiquitous-language.md)'s
 * customer vocabulary governs what reaches a *customer's* screen, and this
 * reaches an engineer's.
 */
const GATE_NAMES: Record<Gate, string> = {
  [GATES.ACCOUNT_STANDING]: 'account standing',
  [GATES.SESSION_VALIDITY]: 'session validity',
  [GATES.WORKSPACE_RESOLUTION]: 'workspace resolution',
  [GATES.WORKSPACE_STANDING]: 'workspace standing',
  [GATES.MEMBERSHIP_AND_ROLE]: 'membership and role',
  [GATES.READINESS]: 'readiness',
};

export function explainEntry(record: EntryRecord): string {
  return (
    `${record.at} · sent to ${record.route} by gate ${record.gate} ` +
    `(${GATE_NAMES[record.gate]}), reason ${record.reason} · ` +
    `correlation ${record.correlationId}`
  );
}
