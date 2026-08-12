'use client';

import { useCallback, useEffect, useState } from 'react';

import { StatedAbsence } from '@/components/feedback/stated-absence';
import {
  Badge,
  Button,
  Card,
  CardBody,
  CardHeader,
  CardTitle,
  SkeletonText,
  TBody,
  TD,
  TH,
  THead,
  TR,
  Table,
} from '@/components/ui';
import { authClient } from '@/lib/auth/client';

/**
 * **§05 · Active sessions & revocation** — [TASK-1414](../../../../../docs/BACKLOG.md).
 *
 * 📁 ***"A session is an issued token, not a device. Two browsers on one laptop
 * are two sessions, and are shown that way — collapsing them into one row would
 * hide exactly the session an attacker is using."***
 *
 * ⚡ **So there is no grouping, no de-duplication and no *device* column.**
 * ⛔ **Every row is one token**, which is what the sentence above asks for and
 * what makes the count trustworthy.
 *
 * ## 🔴 Location is absent, and it is the column a frightened person wants most
 *
 * 📁 The design draws **Location** and a *"Usual location"* / *"Never seen
 * before"* tag. ⛔ **Nothing in this repository resolves an address to a
 * place** — there is no geo-IP service, no *seen before* record, and inventing
 * either would be [§20c](../../../../../CLAUDE.md)'s mock business data on the
 * one screen where a wrong answer is dangerous.
 *
 * ✅ **The IP address ships instead, unmasked**, and the column says why. 📁 The
 * design's own responsive rule makes the same argument about hiding it:
 * *"an IP address you cannot see is an IP address you cannot check."*
 *
 * ## ⛔ There is no step-up in front of revocation, deliberately
 *
 * ⚠️ **The row's Security Invariant asks for one and the vendor does not
 * enforce it**: `/revoke-session` uses Better Auth's `sensitiveSessionMiddleware`,
 * which requires a **valid** session and **not a fresh** one — 📁 unlike
 * `changePassword` and `twoFactor.disable`, which take the password and are
 * genuinely challenged.
 *
 * 🔴 **Rendering [`StepUpDialog`](../../../../components/auth/step-up-dialog.tsx)
 * here anyway would be enforcement in the UI only** — precisely what
 * [TASK-1410](../../../../../docs/BACKLOG.md) names as the failure: *"a dialog
 * that guards the dialog guards nothing."*
 *
 * ⛔ **And the fix is not to add one.** 📁 The design guarantees the opposite in
 * §08: *"Session revocation still works — it is enforced by Signora — and that
 * distinction is stated so you know what you can still do while under attack."*
 * ⚡ **A challenge this product cannot perform** — there is no re-verification
 * endpoint, and an SSO account has no password to re-enter — **would take the
 * one control that must survive an attack and make it the first to fail.**
 * **Raised rather than resolved here.**
 */
export interface SessionRow {
  readonly token: string;
  readonly userAgent: string | null;
  readonly ipAddress: string | null;
  readonly createdAt: string;
  readonly updatedAt: string;
}

/**
 * 🔴 **One read, and both surfaces render from it.**
 *
 * ⛔ **The posture strip's *Active sessions* cell and this table are the same
 * question**, and two reads would be two answers ([§2](../../../../../CLAUDE.md))
 * — **they would disagree the moment a revocation succeeded**, which is the one
 * moment the number matters.
 */
export interface SessionsRead {
  readonly sessions: readonly SessionRow[] | null;
  readonly failed: boolean;
  readonly revoking: string | null;
  readonly revoke: (token: string) => Promise<void>;
}

export function useSessions(): SessionsRead {
  const [sessions, setSessions] = useState<readonly SessionRow[] | null>(null);
  const [failed, setFailed] = useState(false);
  const [revoking, setRevoking] = useState<string | null>(null);

  const load = useCallback(async () => {
    const result = await authClient.listSessions();
    if (result.error || !result.data) {
      setFailed(true);
      return;
    }
    setFailed(false);
    setSessions(result.data as unknown as readonly SessionRow[]);
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const revoke = useCallback(
    async (token: string) => {
      setRevoking(token);
      const result = await authClient.revokeSession({ token });
      setRevoking(null);
      if (result.error) {
        setFailed(true);
        return;
      }
      /**
       * 🔴 **Re-read rather than splice the row out.** 📁 *"Session rows never
       * render optimistically. A stale list here is worse than a slow one."*
       * ⚡ **Removing the row locally would claim the revocation succeeded on
       * the strength of a `200` and then show a list nobody re-checked.**
       */
      await load();
    },
    [load],
  );

  return { sessions, failed, revoking, revoke };
}

export interface SessionsPanelProps extends SessionsRead {
  /** The token of the session reading this page, so it is never offered for revocation. */
  readonly currentToken: string;
}

export function SessionsPanel({
  currentToken,
  sessions,
  failed,
  revoking,
  revoke,
}: SessionsPanelProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Where you are signed in</CardTitle>
        <p className="mt-1 text-sm text-content-muted">
          A session is an issued token, not a device. Two browsers on one laptop are two
          sessions, and are shown that way.
        </p>
      </CardHeader>
      <CardBody>
        {failed ? (
          /* 📁 [P-A](../../../../../docs/DOMAIN_DISCOVERY_REGISTER.md) — ⛔ a
             failed read here must never render as *you are signed in nowhere*. */
          <StatedAbsence subject="where you are signed in" as="card" />
        ) : sessions === null ? (
          <SkeletonText lines={3} />
        ) : (
          <Table>
            <THead>
              <TR>
                <TH>Client</TH>
                <TH>IP address</TH>
                <TH>Signed in</TH>
                <TH>Last active</TH>
                <TH>Action</TH>
              </TR>
            </THead>
            <TBody>
              {sessions.map((session) => {
                const isThisOne = session.token === currentToken;
                return (
                  <TR key={session.token}>
                    <TD>
                      <span className="text-content">{clientOf(session.userAgent)}</span>
                      {isThisOne ? (
                        <Badge tone="accent" className="ml-2">
                          This device
                        </Badge>
                      ) : null}
                    </TD>
                    <TD>
                      <span className="font-mono text-xs">{session.ipAddress ?? 'Not recorded'}</span>
                    </TD>
                    <TD>{when(session.createdAt)}</TD>
                    <TD>{when(session.updatedAt)}</TD>
                    <TD>
                      {isThisOne ? (
                        /**
                         * 📁 ***"Your own session is never revoked silently."***
                         * ⛔ **No control at all rather than a disabled one** —
                         * there is nothing to refuse, so there is nothing to
                         * offer.
                         */
                        <span className="text-xs text-content-muted">You are here</span>
                      ) : (
                        <Button
                          variant="ghost"
                          loading={revoking === session.token}
                          onClick={() => void revoke(session.token)}
                        >
                          Revoke
                        </Button>
                      )}
                    </TD>
                  </TR>
                );
              })}
            </TBody>
          </Table>
        )}

        <p className="mt-4 text-sm leading-6 text-content-muted">
          Revocation is server-side and takes effect within 60 seconds — a client already
          mid-request may finish it. It does not end your session with your identity provider,
          and it does not change your password. Each of those is a separate control, and
          pretending otherwise gives false comfort.
        </p>
      </CardBody>
    </Card>
  );
}

/**
 * ⛔ **A client, not a device**, and the panel's own header says why the
 * difference matters. ⚡ **The browser name is the most a user agent honestly
 * yields** — parsing it into *MacBook Pro 16"* is a guess dressed as a fact.
 */
export function clientOf(userAgent: string | null): string {
  if (userAgent === null || userAgent.trim() === '') return 'Unknown client';
  const known = ['Edge', 'Chrome', 'Firefox', 'Safari'].find((name) =>
    name === 'Safari'
      ? userAgent.includes('Safari') && !userAgent.includes('Chrome')
      : userAgent.includes(name),
  );
  return known ?? 'Unknown client';
}

function when(iso: string): string {
  const at = new Date(iso);
  return Number.isNaN(at.getTime()) ? 'Not recorded' : at.toLocaleString();
}
