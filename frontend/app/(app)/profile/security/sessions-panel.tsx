'use client';

import { useCallback, useEffect, useState } from 'react';

import { StatedAbsence } from '@/components/feedback/stated-absence';
import {
  Badge,
  Button,
  Card,
  Dialog,
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
  /**
   * 🔴 **Bulk revocation** — [TASK-470](../../../../../docs/BACKLOG.md)
   * milestone 3. 📁 **Both approved designs draw it and neither half of the
   * repository had it**: the Security Center's §05 *"Revoke 2 selected"* and
   * *"Sign out everywhere"*, and the User Profile's `05` sessions panel.
   *
   * ⚡ **Selection is held as TOKENS rather than as rows**, the shape
   * [`signal-queue.tsx`](../../signals/signal-queue.tsx) already uses for the
   * same reason: **a re-read replaces every object, and a selection of stale
   * objects acts on sessions that have already gone.**
   */
  readonly selected: ReadonlySet<string>;
  readonly toggleSelected: (token: string) => void;
  readonly clearSelection: () => void;
  readonly revokeSelected: () => Promise<void>;
  /**
   * 📁 ***"Signing out everywhere ends every session except this one, within
   * 60 seconds."*** ⛔ **`includeThisOne` is the design's own second half** —
   * *"Choosing to include it is possible, and warns that you will land on the
   * sign-in screen."*
   */
  readonly signOutEverywhere: (includeThisOne: boolean) => Promise<void>;
  readonly bulkBusy: boolean;
}

export function useSessions(): SessionsRead {
  const [sessions, setSessions] = useState<readonly SessionRow[] | null>(null);
  const [failed, setFailed] = useState(false);
  const [revoking, setRevoking] = useState<string | null>(null);
  const [selected, setSelected] = useState<ReadonlySet<string>>(() => new Set());
  const [bulkBusy, setBulkBusy] = useState(false);

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

  /**
   * ⛔ **A selection is cleared whenever the list is re-read**, because every
   * token in it may already be gone. ⚡ **The same rule the signal queue keeps**
   * — *"a selection that survives is a selection whose action bar lies about
   * what it will act on."*
   */
  const reload = useCallback(async () => {
    setSelected(new Set());
    await load();
  }, [load]);

  const toggleSelected = useCallback((token: string) => {
    setSelected((was) => {
      const next = new Set(was);
      if (!next.delete(token)) next.add(token);
      return next;
    });
  }, []);

  const clearSelection = useCallback(() => setSelected(new Set()), []);

  /**
   * ⚠️ **Sequential, not concurrent, and not one call.**
   *
   * ⛔ **Better Auth publishes no *revoke these N* route** — `/revoke-session`
   * takes one token, `/revoke-sessions` takes none and ends them all.
   * ⚡ **So a selection is n calls**, and they run **in order** rather than in
   * parallel: 📁 the panel's own rule is that the list is re-read rather than
   * spliced, and n concurrent revocations racing one re-read is how a screen
   * ends up showing a session that is already dead.
   *
   * 🔴 **A failure stops the loop and the list is re-read anyway.** ⛔ **The
   * ones that succeeded really are revoked**, and carrying on would report a
   * partial result as a whole one.
   */
  const revokeSelected = useCallback(async () => {
    setBulkBusy(true);
    for (const token of selected) {
      const result = await authClient.revokeSession({ token });
      if (result.error) {
        setFailed(true);
        break;
      }
    }
    setBulkBusy(false);
    await reload();
  }, [selected, reload]);

  const signOutEverywhere = useCallback(
    async (includeThisOne: boolean) => {
      setBulkBusy(true);
      const result = includeThisOne
        ? await authClient.revokeSessions()
        : await authClient.revokeOtherSessions();
      setBulkBusy(false);
      if (result.error) {
        setFailed(true);
        return;
      }
      /**
       * ⛔ **Including this one ends the session reading the page**, so the
       * only honest next screen is the sign-in one. ⚡ **A full navigation
       * rather than a router push** — the client-side cache belongs to a
       * session that no longer exists.
       */
      if (includeThisOne) {
        window.location.href = '/signin';
        return;
      }
      await reload();
    },
    [reload],
  );

  return {
    sessions,
    failed,
    revoking,
    revoke,
    selected,
    toggleSelected,
    clearSelection,
    revokeSelected,
    signOutEverywhere,
    bulkBusy,
  };
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
  selected,
  toggleSelected,
  clearSelection,
  revokeSelected,
  signOutEverywhere,
  bulkBusy,
}: SessionsPanelProps) {
  /**
   * 🔴 **The design's second half, and it is a confirm rather than a button.**
   *
   * 📁 ***"Choosing to include it is possible, and warns that you will land on
   * the sign-in screen."*** ⛔ **A control that signs somebody out of the
   * screen they are looking at may not be one click**, and the warning is the
   * whole reason the design mentions it.
   */
  const [confirming, setConfirming] = useState(false);

  /**
   * ⚡ **Only sessions that are not this one can be selected**, so the count in
   * the bar is the count that will be revoked. ⛔ **A *select all* that
   * silently excluded a row would make the number a guess.**
   */
  const revocable = (sessions ?? []).filter((s) => s.token !== currentToken);
  const allSelected = revocable.length > 0 && revocable.every((s) => selected.has(s.token));

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
          <>
            {/**
              * 🔴 **The bulk bar** — 📁 the Security Center's §05 draws
              * ***"Revoke 2 selected"*** and ***"Sign out everywhere"*** side by
              * side, and neither existed.
              *
              * ⚡ **It is always present rather than appearing on selection**,
              * because *"Sign out everywhere"* needs no selection — ⛔ **and a
              * bar that materialises would move the table under the pointer at
              * the moment somebody is aiming at a revoke control.**
              */}
            <div
              data-testid="sessions-bulk-bar"
              className="mb-3 flex flex-wrap items-center gap-2 border-b border-border pb-3"
            >
              <span className="text-sm text-content-muted">
                {selected.size === 0
                  ? `${revocable.length} other ${revocable.length === 1 ? 'session' : 'sessions'}`
                  : `${selected.size} selected`}
              </span>
              {selected.size > 0 ? (
                <>
                  <Button
                    variant="ghost"
                    loading={bulkBusy}
                    onClick={() => void revokeSelected()}
                  >
                    Revoke {selected.size} selected
                  </Button>
                  <Button variant="ghost" onClick={clearSelection}>
                    Clear selection
                  </Button>
                </>
              ) : null}
              {/**
                * ⛔ **Disabled when there is nothing to sign out of**, rather
                * than hidden: 📁 the control is part of the design's anatomy
                * and its absence would read as a missing capability.
                */}
              <Button
                variant="ghost"
                className="ml-auto"
                loading={bulkBusy}
                disabled={revocable.length === 0}
                onClick={() => void signOutEverywhere(false)}
              >
                Sign out everywhere
              </Button>
            </div>

            <Table>
            <THead>
              <TR>
                <TH>
                  {/**
                    * ♿ **A real `<input type="checkbox">`** — the same choice
                    * [`signal-queue.tsx`](../../signals/signal-queue.tsx) made,
                    * and for the same reason: a styled `div` loses the
                    * indeterminate state and the keyboard.
                    */}
                  <input
                    type="checkbox"
                    aria-label="Select every other session"
                    checked={allSelected}
                    disabled={revocable.length === 0}
                    onChange={() => {
                      if (allSelected) {
                        clearSelection();
                        return;
                      }
                      revocable.forEach((session) => {
                        if (!selected.has(session.token)) toggleSelected(session.token);
                      });
                    }}
                  />
                </TH>
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
                      {/* ⛔ **This session is never selectable** — 📁 *"your own
                          session is never revoked silently"*, and a checkbox
                          that cannot be ticked is worse than none. */}
                      {isThisOne ? null : (
                        <input
                          type="checkbox"
                          aria-label={`Select ${clientOf(session.userAgent)} session`}
                          checked={selected.has(session.token)}
                          onChange={() => toggleSelected(session.token)}
                        />
                      )}
                    </TD>
                    {/**
                      * 🔴 **A row header, not a `<td>`** — 📁 `Security Center`
                      * `1.3.1`: *"Sessions and history are real tables with
                      * **row and column headers**."*
                      *
                      * ⛔ **This table had six `th[scope="col"]` and zero
                      * `th[scope="row"]`**, so a screen reader moving across a
                      * row announced *"203.116.•.• · IP address"* and never
                      * **which session** it belonged to — on the one screen
                      * where the answer decides whether you revoke it.
                      *
                      * ⚡ **The client IS the row's identity here**, deliberately:
                      * the panel's own rule is *"a session is an issued token,
                      * not a device"*, and the client string is the most
                      * identifying thing this repository actually holds.
                      */}
                    <TH scope="row">
                      <span className="text-content">{clientOf(session.userAgent)}</span>
                      {isThisOne ? (
                        <Badge tone="accent" className="ml-2">
                          This device
                        </Badge>
                      ) : null}
                    </TH>
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
          </>
        )}

        <p className="mt-4 text-sm leading-6 text-content-muted">
          Revocation is server-side and takes effect within 60 seconds — a client already
          mid-request may finish it. It does not end your session with your identity provider,
          and it does not change your password. Each of those is a separate control, and
          pretending otherwise gives false comfort.
        </p>

        {/**
          * 📁 ***"Signing out everywhere ends every session except this one…
          * Choosing to include it is possible, and warns that you will land on
          * the sign-in screen."***
          *
          * ⛔ **A link rather than a second primary button.** ⚡ **The design
          * makes this the deliberate path, not the obvious one** — it is the
          * only control on the page that ends the session reading it.
          */}
        <button
          type="button"
          /* ♿ 📁 `2.5.8` — *"targets ≥ 24px with 8px separation"*, and this
             measured `163 × 21`. ⛔ **`min-h-6` rather than a height**: the
             design's treatment here is a link, not a button, so the control
             keeps its underline and gains only the floor it was under —
             ⚡ **and the touch floor, because this is the one control on the
             page that ends the session reading it.** */
          className="mt-2 inline-flex min-h-6 items-center self-start rounded text-sm text-content-muted underline underline-offset-2 hover:text-content coarse:min-h-11"
          onClick={() => setConfirming(true)}
        >
          Sign out of this one too
        </button>

        <Dialog
          open={confirming}
          onClose={() => setConfirming(false)}
          title="Sign out everywhere, including here"
          description="Every session ends, including the one you are using. You will land on the sign-in screen and will need to sign in again."
          footer={
            <>
              <Button variant="ghost" onClick={() => setConfirming(false)}>
                Cancel
              </Button>
              {/**
                * ⛔ **Not *"Sign out everywhere"* again.** ⚡ **The bar already
                * has a button by that name and this one does something
                * different** — it ends the session reading the page — **so two
                * controls sharing an accessible name is the ambiguity a
                * screen-reader user cannot resolve.** 📁 Found by the test
                * refusing to choose between them.
                */}
              <Button
                loading={bulkBusy}
                onClick={() => {
                  setConfirming(false);
                  void signOutEverywhere(true);
                }}
              >
                Sign out, including here
              </Button>
            </>
          }
        >
          <p className="text-sm leading-6 text-content-muted">
            Your identity provider may still hold a session of its own. Signora cannot end
            that one, and does not imply otherwise.
          </p>
        </Dialog>
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
