'use client';

import { PosturePanel } from './posture-panel';
import { SessionsPanel, useSessions } from './sessions-panel';

/**
 * **The two surfaces that answer the same question, reading it once** —
 * [TASK-1414](../../../../../docs/BACKLOG.md).
 *
 * 🔴 **§01's *Active sessions* cell and §05's table are one fact.** ⛔ **Two
 * `listSessions()` calls would be two answers** ([§2](../../../../../CLAUDE.md)),
 * **and they would disagree at exactly the moment the number matters** — a
 * revocation succeeds, the table re-reads, and a posture strip that fetched
 * separately still says four.
 *
 * ⚡ **So the read is lifted here and both panels render from it**, which is the
 * same shape [`copilot.tsx`](../../../../components/shell/copilot.tsx) used for
 * *is the assistant open*, and for the same reason.
 */
export interface AccountSecurityProps {
  readonly currentToken: string;
  /** How many second factors are enrolled — read from the session on the server. */
  readonly factors: number;
}

export function AccountSecurity({ currentToken, factors }: AccountSecurityProps) {
  const read = useSessions();

  return (
    <>
      <PosturePanel
        factors={factors}
        /**
         * ⛔ **`null` while it is still loading AND when it failed**, because
         * 📁 [P-A](../../../../../docs/DOMAIN_DISCOVERY_REGISTER.md) treats both
         * the same on this cell: **neither is a number, and neither may render
         * as one.**
         */
        sessions={read.failed || read.sessions === null ? null : read.sessions.length}
      />
      <SessionsPanel currentToken={currentToken} {...read} />
    </>
  );
}
