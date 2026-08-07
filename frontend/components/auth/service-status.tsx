'use client';

import { useEffect, useState } from 'react';

import { cn } from '@/lib/design/cn';

/**
 * The line under the authentication card — **the host, and a live status dot.**
 *
 * **TASK-467 · Workflow 1, milestone 3**, against
 * `docs/design-snapshot/screens/Fortune Signora Authentication.dc.html` §01:
 * *"Region and status are printed under the card: `EU · eu.signora.app` and a
 * live status dot. **Buyers check both.**"*
 *
 * ### ⚡ The dot is real, and that is the whole reason it is worth building
 *
 * It reads **`/api/health`**, which has existed since M1 and reports the
 * authentication subsystem: the auth database, the signing key pair, the JWT
 * configuration and whether any sign-in method is configured at all. **A green
 * dot here means somebody can actually sign in** — the one thing the screen
 * behind it is for.
 *
 * ⛔ **A decorative dot would have been worse than no dot.** The design's own
 * rationale is that an enterprise buyer reads this line; a green dot that is
 * green because it is always green is the exact shape of claim
 * [§2](../../../CLAUDE.md) forbids.
 *
 * ### ⚠️ Region is not rendered, because Signora has no region
 *
 * The design prints `EU ·` before the host. **No region concept exists** — not
 * in `AuthConfig`, not in the platform, not in a backlog row. Printing `EU`
 * would be inventing a data-residency claim on the screen an enterprise
 * security team reads most carefully, which is the most expensive possible
 * place to invent one. **The host is real and is printed; the region is absent
 * and is omitted** (P-A).
 *
 * ### Checking is its own state
 *
 * ⚡ **Never optimistic.** Until the first response lands the dot is neutral
 * and the word is *Checking* — because *"absence can never distinguish itself
 * from failure"* ([P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md)), and a dot
 * that starts green is asserting health it has not yet been told.
 */
export function ServiceStatus() {
  const [status, setStatus] = useState<'checking' | 'ok' | 'degraded' | 'unavailable'>(
    'checking',
  );
  const [host, setHost] = useState('');

  useEffect(() => {
    setHost(window.location.host);

    let live = true;
    void fetch('/api/health')
      .then(async (response) => {
        // A 503 still carries the report — `/api/health` returns the body
        // either way, and reading it is how "unavailable" reaches the dot
        // instead of being flattened into the network-failure branch below.
        const report: unknown = await response.json();
        const reported = (report as { status?: unknown }).status;
        if (!live) return;
        setStatus(
          reported === 'ok' || reported === 'degraded' || reported === 'unavailable'
            ? reported
            : 'unavailable',
        );
      })
      .catch(() => {
        // ⚠️ **A failed request is reported as unavailable, not as unknown.**
        // If this page cannot reach its own server, nobody signs in — so the
        // honest reading of the failure is the same as the honest reading of
        // a 503, and leaving the dot neutral would understate it.
        if (live) setStatus('unavailable');
      });

    return () => {
      live = false;
    };
  }, []);

  return (
    <span className="inline-flex items-center gap-1.5">
      <span
        aria-hidden
        className={cn('h-1.5 w-1.5 rounded-full', DOT[status])}
        data-status={status}
      />
      {/* The dot carries no meaning on its own — 1.4.1, colour is never the
          only channel — so the word beside it is the announcement, and the dot
          is furniture. */}
      <span>{WORD[status]}</span>
      {host ? <span aria-hidden>·</span> : null}
      {host ? <span>{host}</span> : null}
    </span>
  );
}

const DOT: Record<string, string> = {
  checking: 'bg-content-subtle',
  ok: 'bg-success',
  degraded: 'bg-warning',
  unavailable: 'bg-danger',
};

const WORD: Record<string, string> = {
  checking: 'Checking sign-in',
  ok: 'Sign-in operational',
  degraded: 'Sign-in degraded',
  unavailable: 'Sign-in unavailable',
};
