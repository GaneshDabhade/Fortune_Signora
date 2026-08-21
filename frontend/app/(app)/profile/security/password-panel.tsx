'use client';

import { useState } from 'react';

import {
  Button,
  Card,
  CardBody,
  CardHeader,
  CardTitle,
  PasswordField,
  PasswordStrength,
  evaluatePassword,
} from '@/components/ui';
import { authClient } from '@/lib/auth/client';

/**
 * **§02 · Password** — [TASK-1414](../../../../../docs/BACKLOG.md).
 *
 * ## 🔴 Two states, and the SSO one is the one the row warns about
 *
 * ⚠️ **The row names the risk in terms**: *"Rendering the SSO-managed password
 * state as a disabled field. The design sends the person to their provider
 * with a working link; a disabled field is the false affordance class again."*
 *
 * 📁 **The design asks for both halves**: *"the form is shown disabled rather
 * than hidden — you should be able to see that it exists and where it lives"*,
 * **and** a `Change password at …` control that goes somewhere.
 *
 * ⛔ **So the link is not optional, and it is not invented either.** ✅ **Google
 * and Microsoft are the two providers [`server.ts`](../../../../lib/auth/server.ts)
 * configures**, and their account-security pages are stable public addresses.
 * ⛔ **Any other provider gets the sentence and NO link** — 📁 a dead link on a
 * security page is worse than an absent one, which is the same argument
 * [`copilot.tsx`](../../../../components/shell/copilot.tsx) makes about an
 * input box nothing will answer.
 */
const PROVIDER_SECURITY_PAGE: Readonly<Record<string, { name: string; href: string }>> = {
  google: { name: 'Google', href: 'https://myaccount.google.com/security' },
  microsoft: { name: 'Microsoft', href: 'https://account.microsoft.com/security' },
};

/**
 * 📁 **The design's NIST paragraph, and every word of it is a rule this form
 * keeps**: *"length over composition, a breach check against known-compromised
 * credentials, and no forced rotation schedule — expiry rules push people
 * toward predictable variants of one password."*
 *
 * ✅ **All three are already enforced by the Authentication Authority** —
 * `minPasswordLength` and `haveIBeenPwned()` in
 * [`server.ts`](../../../../lib/auth/server.ts), and nothing anywhere expires a
 * password. ⛔ **This panel restates none of them as its own logic.**
 */
export interface PasswordPanelProps {
  /**
   * The provider this account signs in through, or `null` when it holds its own
   * password. ⛔ **Read from the account list on the server** — never guessed
   * from the presence of a password field.
   */
  readonly ssoProvider: string | null;
}

export function PasswordPanel({ ssoProvider }: PasswordPanelProps) {
  if (ssoProvider !== null) return <ManagedElsewhere provider={ssoProvider} />;
  return <ChangePasswordForm />;
}

function ManagedElsewhere({ provider }: { provider: string }) {
  const known = PROVIDER_SECURITY_PAGE[provider];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Password</CardTitle>
        <p className="mt-1 text-sm text-content-muted">
          Managed by your identity provider
        </p>
      </CardHeader>
      <CardBody className="flex flex-col gap-4">
        <p className="text-sm leading-6 text-content-muted">
          You sign in through {known?.name ?? provider}, so Signora never receives, stores
          or verifies your password. The form is shown disabled rather than hidden — you
          should be able to see that it exists and where it lives.
        </p>

        <div className="flex flex-col gap-3 opacity-60" aria-hidden="true">
          {['Current password', 'New password', 'Confirm new password'].map((label) => (
            <div key={label}>
              <span className="text-xs font-medium text-content-muted">{label}</span>
              <div className="mt-1 h-9 rounded-md border border-border bg-surface-sunken" />
            </div>
          ))}
        </div>

        {known === undefined ? (
          /**
           * ⛔ **No link, and the reason is stated.** ⚡ **A button labelled
           * *Change password at your provider* that goes nowhere is the
           * affordance this panel's own header refuses.**
           */
          <p
            className="text-sm leading-6 text-content-muted"
            data-testid="password-no-link"
          >
            Change it where your account lives. Signora does not know that address for{' '}
            {provider}, and would rather say so than send you to a page that may not
            exist.
          </p>
        ) : (
          <div>
            {/* ⛔ **An anchor, not a `Button` with a handler** — it navigates, and a
                keyboard user must be able to open it in a new tab the ordinary way. */}
            <a
              className="inline-flex h-9 items-center rounded-md border border-border px-3 text-sm font-medium text-content hover:bg-surface-sunken "
              href={known.href}
              target="_blank"
              rel="noreferrer noopener"
            >
              Change password at {known.name}
            </a>
            <p className="mt-1.5 text-xs text-content-muted">Opens in a new tab</p>
          </div>
        )}
      </CardBody>
    </Card>
  );
}

/**
 * 📁 ***"Changing your password signs you out of 3 other sessions. You choose
 * whether that happens — keeping them is legitimate when you are simply
 * rotating a credential, and dangerous when you suspect compromise, so we ask
 * rather than assume."***
 *
 * ⚡ **The choice is a real parameter**: Better Auth's `changePassword` takes
 * `revokeOtherSessions`, so this is a decision the customer makes and the
 * server performs — ⛔ **not a checkbox the screen reads and then ignores.**
 */
function ChangePasswordForm() {
  const [current, setCurrent] = useState('');
  const [next, setNext] = useState('');
  const [signOutOthers, setSignOutOthers] = useState(true);
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setFailed(null);
    const result = await authClient.changePassword({
      currentPassword: current,
      newPassword: next,
      revokeOtherSessions: signOutOthers,
    });
    setBusy(false);
    if (result.error) {
      /**
       * ⛔ **The server's own sentence, never a paraphrase.** 📁 §08:
       * *"errors are adjacent, textual and specific"*, and a rewritten error is
       * a worse explanation in front of somebody who is already worried.
       */
      setFailed(result.error.message ?? 'That did not work.');
      return;
    }
    setDone(true);
    setCurrent('');
    setNext('');
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Password</CardTitle>
        <p className="mt-1 text-sm text-content-muted">
          Length over composition, checked against known-compromised credentials, and
          never expired on a schedule — expiry rules push people toward predictable
          variants of one password.
        </p>
      </CardHeader>
      <CardBody>
        <form className="flex max-w-md flex-col gap-4" onSubmit={submit}>
          <PasswordField
            label="Current password"
            value={current}
            onChange={(event) => setCurrent(event.target.value)}
            autoComplete="current-password"
            required
          />
          <div>
            <PasswordField
              label="New password"
              value={next}
              onChange={(event) => setNext(event.target.value)}
              autoComplete="new-password"
              required
            />
            {/**
             * ⛔ **It REPORTS and never gates** — 📁 [TASK-485](../../../../../docs/BACKLOG.md)
             * established that and the row forbids re-deciding it here.
             */}
            <PasswordStrength rules={evaluatePassword(next)} />
          </div>

          <fieldset className="flex flex-col gap-2">
            <legend className="text-sm font-medium text-content">
              Your other sessions
            </legend>
            <Choice
              checked={signOutOthers}
              onSelect={() => setSignOutOthers(true)}
              label="Sign out everywhere else"
              hint="The safe default when you suspect compromise"
            />
            <Choice
              checked={!signOutOthers}
              onSelect={() => setSignOutOthers(false)}
              label="Keep my other sessions"
              hint="For routine rotation on trusted devices"
            />
          </fieldset>

          {failed === null ? null : (
            <p role="alert" className="text-sm text-danger">
              {failed}
            </p>
          )}
          {done ? (
            <p role="status" className="text-sm text-success">
              Your password has been changed.
              {signOutOthers
                ? ' Your other sessions have ended.'
                : ' Your other sessions are still open.'}
            </p>
          ) : null}

          <div>
            <Button type="submit" disabled={busy}>
              {busy ? 'Changing…' : 'Change password'}
            </Button>
          </div>
        </form>
      </CardBody>
    </Card>
  );
}

function Choice({
  checked,
  onSelect,
  label,
  hint,
}: {
  checked: boolean;
  onSelect: () => void;
  label: string;
  hint: string;
}) {
  return (
    <label className="flex cursor-pointer items-start gap-2.5">
      <input
        type="radio"
        name="other-sessions"
        checked={checked}
        onChange={onSelect}
        className="mt-1"
      />
      <span>
        <span className="block text-sm text-content">{label}</span>
        <span className="block text-xs text-content-muted">{hint}</span>
      </span>
    </label>
  );
}
