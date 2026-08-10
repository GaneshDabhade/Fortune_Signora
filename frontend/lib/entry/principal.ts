/**
 * **Who is entering** — [TASK-1407](../../../docs/BACKLOG.md), on
 * [495](../../../docs/architecture/495-principal-and-identity-boundary.md).
 *
 * ## ⛔ This does not build the principal model
 *
 * 📁 **[495](../../../docs/architecture/495-principal-and-identity-boundary.md)
 * ratified it**: *"One principal type. A `kind`. A `subject_id`. A workspace.
 * And — the field that does the real work — `acting_for`."* ✅ **This makes the
 * engine's signature admit one**, which is a type change rather than an
 * abstraction invented for a caller that does not exist.
 *
 * ⚡ **Why now is the whole argument.** `resolveEntry` has **zero callers
 * today** and [TASK-1401](../../../docs/BACKLOG.md) is the one caller-to-be.
 * ⛔ **After the shell, the compositions and the cards consume it, the same
 * change is a refactor across six.**
 *
 * ⚠️ **Not speculative generality** ([§6](../../../CLAUDE.md)). **The test that
 * rule asks is whether the requirement exists**, and
 * [D-196](../../../docs/DECISION_REGISTER.md) §8 states it: *support AI agents,
 * service accounts, delegated access and SSO **without architectural
 * redesign***. **The abstraction is ratified and dated; only the signature is
 * new.**
 */

/**
 * 📁 **495's nine, verbatim.**
 *
 * ⛔ **A closed union, so a tenth cannot arrive by accident** and every
 * exhaustive `switch` over it is checked by the compiler.
 */
export const PRINCIPAL_KINDS = [
  'HUMAN',
  'SERVICE_ACCOUNT',
  'AGENT',
  'API_KEY',
  'PAT',
  'OAUTH_CLIENT',
  'EXTENSION',
  'AUTOMATION',
  'JOB',
] as const;

export type PrincipalKind = (typeof PRINCIPAL_KINDS)[number];

/**
 * 📁 **495's shape, and the two rules that come with it.**
 *
 * ⛔ **`workspaceId` is non-nullable for every non-human kind** — *"a machine
 * identity that is not workspace-scoped is a cross-tenant credential, and §11
 * has no category for one."* ⚡ **Expressed as a discriminated union rather
 * than as a comment**, so the unscoped machine credential is unconstructable
 * ([§2](../../../CLAUDE.md), *types should make incorrect architecture
 * impossible*).
 */
export type Principal =
  | {
      readonly kind: 'HUMAN';
      readonly subjectId: string;
      /** ⚡ **Nullable for a human**: somebody who belongs to nothing yet is
       * still a person signing in, and rule 10 `NO_WORKSPACE` is their
       * designed destination. */
      readonly workspaceId: string | null;
      /**
       * 📁 *"An impersonated session must set `acting_for` and be marked in the
       * audit — an unmarked impersonation is indistinguishable from the person
       * acting."* ⚡ **So it is optional for a human and meaningful when set.**
       */
      readonly actingFor?: string;
    }
  | {
      readonly kind: Exclude<PrincipalKind, 'HUMAN'>;
      readonly subjectId: string;
      /** 🔴 **Non-nullable.** See above — the type is the enforcement. */
      readonly workspaceId: string;
      /** 📁 *"Every machine principal is owned by a human."* ⚡ **What makes
       * revocation on offboarding tractable and audit attributable.** */
      readonly ownerUserId: string;
      /** 📁 **The field the whole model exists for** — the human on whose
       * behalf a machine is acting, when there is one. */
      readonly actingFor?: string;
    };

/** ⚡ The common case, so the engine's own tests read as they always did. */
export function human(subjectId: string, workspaceId: string | null = null): Principal {
  return { kind: 'HUMAN', subjectId, workspaceId };
}

export function isHuman(principal: Principal): boolean {
  return principal.kind === 'HUMAN';
}

/**
 * 🔴 **Why a machine gets no screen, in one sentence per kind's family.**
 *
 * ⛔ **Not a redirect to Home**, which the row names as the defect: **putting
 * an agent on a human's Home is putting it in a human's session.** ⚡ **And a
 * refusal that says nothing is a refusal somebody debugs by guessing** — this
 * is the same reasoning as [TASK-1403](../../../docs/BACKLOG.md)'s reason
 * codes, applied to the one case that has no reason code because the design's
 * twenty-four are all about people.
 */
export function whyNoScreen(kind: Exclude<PrincipalKind, 'HUMAN'>): string {
  return (
    `A ${kind} principal has no screen to land on. Signora resolves an entry ` +
    'destination for people; a machine identity acts through the API on the ' +
    'authority it was granted, and routing one to a person’s home would ' +
    'put it inside a human session.'
  );
}
