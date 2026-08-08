import { notFound } from 'next/navigation';

import { loadAuthConfig } from '@/lib/auth/config';
import { delivery } from '@/lib/auth/mailbox';

/**
 * **The development mailbox** — [TASK-474](../../../../docs/BACKLOG.md)
 * milestone 2, [ADR-0406](../../../../docs/architecture/adr/0406-authentication-execution-modes.md) §3.
 *
 * ⚡ **Read at boot, never baked in.** It reports what this process has sent,
 * which is not a thing that can be decided at build time.
 */
export const dynamic = 'force-dynamic';

/**
 * ### 🔴 One guard, and it is the transport itself
 *
 * **This renders only when `emailTransport` is `mailbox`** — and
 * `loadAuthConfig` already **refuses to start** with that transport in a
 * deployed environment, because *a delivery history is a record of
 * credentials being issued*. ⛔ **So the surface cannot exist where the store
 * cannot exist**, and there is no second condition to keep in step with the
 * first.
 *
 * ⚠️ **Any other transport gives a 404 rather than an empty page.** With
 * `console` or `resend` selected there is nothing to show, and a page that
 * said *"no emails yet"* would be indistinguishable from a mailbox that had
 * simply lost them.
 *
 * ### ⛔ Deliberately not product surface
 *
 * **No approved design draws this screen**, so it does not pretend to be one:
 * no `AuthShell`, no card, no product mark. **It says what it is in its first
 * line.** ⚡ **The product owner chose this placement over `infra/`** — that
 * module is Lane C's, and building there would have been a change in a module
 * this lane is not assigned ([§20e](../../../../CLAUDE.md)).
 */
export default function MailboxPage() {
  if (loadAuthConfig().emailTransport !== 'mailbox') notFound();

  const sent = delivery();

  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col gap-6 px-5 py-10">
      <header className="flex flex-col gap-1">
        <p className="text-xs font-semibold uppercase tracking-wider text-content-subtle">
          Development tool · not part of the product
        </p>
        <h1 className="text-xl font-bold tracking-tight text-content">Mailbox</h1>
        <p className="text-sm leading-6 text-content-muted">
          Every email this process has sent, newest first. The links are real — Better Auth
          minted the token, built the URL and set the expiry. Only the last hop is local, and
          nothing here survives a restart.
        </p>
      </header>

      {sent.length === 0 ? (
        <p className="rounded-md border border-border bg-surface p-6 text-sm text-content-muted">
          Nothing sent yet. Register, ask for a verification email again, or request a password
          reset, and it will appear here.
        </p>
      ) : (
        <ol className="flex flex-col gap-3">
          {sent.map((email) => (
            <li
              key={`${email.sentAt.toISOString()}-${email.to}`}
              className="flex flex-col gap-2 rounded-md border border-border bg-surface p-4"
            >
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <span className="text-sm font-semibold text-content">{email.purpose}</span>
                <span className="text-xs text-content-subtle">
                  {email.sentAt.toISOString()}
                </span>
              </div>
              <span className="text-sm text-content-muted">{email.to}</span>

              {/* ⚡ **A real anchor, because opening it is the point.** The row
                  asks that a developer can *open* the verification and reset a
                  password — not read a string and paste it. */}
              {email.url ? (
                <a
                  href={email.url}
                  className="break-all text-sm font-medium text-accent underline underline-offset-2"
                >
                  {email.url}
                </a>
              ) : null}

              {/* A six-digit code is not a link and is not rendered as one. */}
              {email.code ? (
                <span className="font-mono text-lg tracking-widest text-content">
                  {email.code}
                </span>
              ) : null}
            </li>
          ))}
        </ol>
      )}
    </main>
  );
}
