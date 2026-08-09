/**
 * **The scope ladder** — [TASK-1409](../../../docs/BACKLOG.md), against
 * `docs/design-snapshot/screens/Fortune Signora System States.dc.html`
 * ([D-138](../../../docs/DECISION_REGISTER.md)).
 *
 * > 📁 **§01 — *"A failure claims the smallest surface it can."***
 *
 * ## ⚡ The ladder is the deliverable, not the four screens
 *
 * 📁 **The design's own diagnosis**: *"The single most common error-handling
 * defect in enterprise software is a widget failure that takes the whole
 * page. One chart cannot reach its service, and a person loses their filters,
 * their scroll position and their unsaved edit."*
 *
 * ⛔ **So `scope` is not a styling choice.** It decides what survives, and
 * 📁 *"escalating is a decision with a reason"* — which is why
 * {@link escalate} demands one in the type rather than in a comment.
 *
 * ## 🔴 Why this file is data and not four components
 *
 * ⚠️ **The repository already had four of these, written independently**:
 * `app/not-found.tsx`, `app/error.tsx`, `components/feedback/error-boundary.tsx`
 * and `components/ui/error-state.tsx`. **Each decided severity, wording,
 * identifier presentation and actions for itself** — three of them rendered a
 * correlation id, in three different shapes. ⚡ **None of them was wrong
 * alone; the set was.**
 *
 * ✅ **The row named that outcome as its own failure condition**: *"if a
 * later workflow still writes a local 404, this row was built as four screens
 * rather than as a ladder."*
 */

/**
 * 📁 The design's four scopes, **in escalation order** — the array's order is
 * load-bearing and {@link atLeast} reads it.
 */
export const SCOPES = ['region', 'page', 'app', 'platform'] as const;
export type Scope = (typeof SCOPES)[number];

/**
 * 📁 Every state the design names, keyed to the scope that owns it.
 *
 * ⛔ **A state belongs to exactly one scope.** That is what makes
 * {@link isLegal} able to refuse, and refusing is the whole mechanism — a
 * `500` rendered at region scope claims the page survived when it did not,
 * and an `empty-result` rendered at app scope tells somebody the product is
 * down when one list happens to be empty.
 */
export const LEGAL_STATES = {
  // 📁 *"Everything: filters, scroll, selection, unsaved edits."*
  region: ['retry', 'skeleton', 'region-error', 'empty-result'],
  // 📁 *"Shell, navigation, workspace context, other tabs."*
  page: ['404', '403', 'feature-not-enabled', 'permission-required'],
  // 📁 *"Local drafts and view state, restored on recovery."*
  app: ['500', 'global-error-boundary'],
  // 📁 *"Nothing in-session; the state is served statically."*
  platform: ['maintenance', 'region-outage', 'no-internet'],
} as const satisfies Record<Scope, readonly string[]>;

export type StateOf<S extends Scope> = (typeof LEGAL_STATES)[S][number];
export type SystemStateName = (typeof LEGAL_STATES)[Scope][number];

/** 📁 §01's *"What survives"* column, verbatim in substance. */
export const SURVIVES: Record<Scope, string> = {
  region: 'Everything: filters, scroll, selection, unsaved edits.',
  page: 'Shell, navigation, workspace context, other tabs.',
  app: 'Local drafts and view state, restored on recovery.',
  platform: 'Nothing in-session; the state is served statically.',
};

/**
 * 📁 **§01's *"When it is right"*** — the test a caller applies before
 * choosing a scope, kept beside the scope rather than in a comment on the
 * component, because the caller choosing is the one who needs it.
 */
export const WHEN: Record<Scope, string> = {
  region: 'One widget, panel or list cannot load. The rest of the page is valid and usable.',
  page: 'The primary record or query failed, or the person may not see it at all.',
  app: 'The client crashed or an unrecoverable server error occurred.',
  platform: 'The service is unavailable to everyone, planned or otherwise.',
};

/**
 * 📁 **The grammar's severity rule** — *"Neutral for absence, warn for
 * permission and interruption, risk for genuine failure, brand for planned
 * events, positive for recovery. The colour is never decorative."*
 *
 * ⛔ **Severity is a property of the state, never of the scope.** A
 * `region-error` and a `500` are both `risk`; an `empty-result` and a `404`
 * are both `neutral`. **Deriving it from scope would make a missing record
 * look like a broken one**, which is the fabrication §2 forbids one level up.
 */
export type Severity = 'neutral' | 'warn' | 'risk' | 'brand' | 'positive';

export const SEVERITY: Record<SystemStateName, Severity> = {
  // Absence — nothing failed.
  'empty-result': 'neutral',
  '404': 'neutral',
  skeleton: 'neutral',
  // Permission and interruption.
  '403': 'warn',
  'permission-required': 'warn',
  'feature-not-enabled': 'warn',
  'no-internet': 'warn',
  // Genuine failure.
  'region-error': 'risk',
  '500': 'risk',
  'global-error-boundary': 'risk',
  'region-outage': 'risk',
  // Planned.
  maintenance: 'brand',
  // Recovery.
  retry: 'positive',
};

/** Does this scope legally own this state? */
export function isLegal(scope: Scope, state: string): state is SystemStateName {
  return (LEGAL_STATES[scope] as readonly string[]).includes(state);
}

/** The scope that owns a state, or `null` if nothing does. */
export function scopeOf(state: string): Scope | null {
  return SCOPES.find((s) => isLegal(s, state)) ?? null;
}

/** `true` when `a` is at or above `b` on the ladder. */
export function atLeast(a: Scope, b: Scope): boolean {
  return SCOPES.indexOf(a) >= SCOPES.indexOf(b);
}

/**
 * ⛔ **Thrown when a caller renders a state at a scope that does not own it.**
 *
 * ⚡ **A throw rather than a fallback, deliberately.** A silent downgrade
 * would render *something* and the mistake would ship — and the mistake is
 * precisely the one the ladder exists to prevent, so it must be loud in
 * development and caught by a test rather than smoothed over at runtime.
 */
export class IllegalScopeError extends Error {
  constructor(scope: Scope, state: string) {
    const owner = scopeOf(state);
    super(
      owner === null
        ? `"${state}" is not a system state the design defines.`
        : `"${state}" is a ${owner}-scope state and cannot render at ${scope} scope. ` +
          `${scope} scope owns: ${LEGAL_STATES[scope].join(', ')}.`,
    );
    this.name = 'IllegalScopeError';
  }
}

/**
 * 📁 **§01: *"escalating is a decision with a reason"*** — so escalation takes
 * one, and the type refuses an empty string.
 *
 * ⚡ **This exists to be awkward.** Escalating from region to page costs the
 * person their filters and their scroll position; the friction is the design's
 * intent, expressed where a component author will meet it.
 */
export function escalate(from: Scope, to: Scope, reason: string): Scope {
  if (!atLeast(to, from)) {
    throw new Error(`Escalation must go up the ladder: ${from} → ${to} does not.`);
  }
  if (reason.trim() === '') {
    throw new Error(
      `Escalating ${from} → ${to} requires a stated reason (§01: "a stated reason in the component, not a default").`,
    );
  }
  return to;
}
