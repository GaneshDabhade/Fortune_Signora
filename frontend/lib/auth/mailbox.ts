import type { AuthEmail } from '@/lib/auth/email';

/**
 * Every email this process has sent, newest first — **the development
 * mailbox's store** ([TASK-474](../../../docs/BACKLOG.md), [ADR-0406](../../../docs/architecture/adr/0406-authentication-execution-modes.md) §3).
 *
 * ### ⛔ It is not a mock, and the distinction is the whole row
 *
 * **Better Auth still mints the token, still builds the URL, still sets the
 * expiry.** `lib/auth/email.ts` has said *"nothing here is mocked"* since it
 * was written and that stays true. ⚡ **Only the last hop is local** — this
 * keeps what was sent so a developer can open it, rather than substituting
 * anything the customer journey depends on.
 *
 * ### 🔴 Why it is in memory, and why that is a security property
 *
 * **A delivery history is a record of credentials being issued.** ⛔ **So it
 * must not outlive the process, must not reach a disk, and must not exist in
 * a deployed environment at all** — `loadAuthConfig` refuses to start one,
 * the same startup refusal the console transport already carries.
 *
 * ⚡ **In-memory makes the bound structural rather than remembered**: there is
 * no file to forget to delete and no row to forget to purge. **A restart is
 * the retention policy.**
 */
export interface MailboxEntry extends AuthEmail {
  /** When this process sent it. Ordering only — never an expiry claim. */
  readonly sentAt: Date;
}

/**
 * **Bounded, because an unbounded one is a slow leak in a long dev session.**
 * Fifty is far more than the handful of flows anybody triggers in a row, and
 * the oldest are the least useful.
 */
export const MAILBOX_CAPACITY = 50;

const delivered: MailboxEntry[] = [];

/** Record a delivery. Called by the transport, never by a flow. */
export function remember(email: AuthEmail): void {
  delivered.unshift({ ...email, sentAt: new Date() });
  if (delivered.length > MAILBOX_CAPACITY) delivered.length = MAILBOX_CAPACITY;
}

/**
 * Everything this process has sent, newest first.
 *
 * ⛔ **A copy, not the array.** A caller that could `push` into the store
 * would be able to put an email in the mailbox that was never sent — which is
 * the one thing a delivery record must never show.
 */
export function delivery(): readonly MailboxEntry[] {
  return [...delivered];
}

/** Empty it. **For tests**, so one case cannot see another's mail. */
export function forget(): void {
  delivered.length = 0;
}
