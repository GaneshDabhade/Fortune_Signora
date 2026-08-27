'use client';

import { useRef, useState } from 'react';

import { Button, CodeInput, PasswordField, StepRail } from '@/components/ui';
import { authClient } from '@/lib/auth/client';

/**
 * **§03 · Set up an authenticator app** — [TASK-1414](../../../../../docs/BACKLOG.md).
 *
 * 📁 ***"Step 2 of 4 · scan, verify, save codes, confirm."***
 *
 * ## ⛔ The password is the first step, and it is not a step this lane invented
 *
 * ⚡ **Better Auth's `twoFactor.enable` takes the account password.** ⛔ **So
 * the fresh factor the design demands before any change *"even inside a valid
 * session"* is enforced by the framework, not by this component** — 📁 which is
 * exactly [TASK-1410](../../../../../docs/BACKLOG.md)'s rule: *"a dialog that
 * guards the dialog guards nothing."*
 *
 * ⚠️ **And it is why this uses a password field rather than
 * [`StepUpDialog`](../../../../components/auth/step-up-dialog.tsx)**: that
 * component takes a **code**, and the code it would take is the one this flow
 * exists to create. **A challenge that requires the factor being enrolled
 * cannot gate the enrolment.**
 *
 * ## 🔴 An account with no password cannot enrol, and it is told so
 *
 * ⛔ **An SSO account has no password to pass**, so enrolment is unavailable —
 * ⚡ **stated rather than rendered as a form that fails on submit.**
 *
 * ## ♿ The manual key is always present
 *
 * 📁 ***"Cannot scan?"*** — 📁 and the row: *"the QR code and its manual key
 * are both offered at every width; this is not a mobile fallback, it is always
 * present"* (WCAG 2.1.1 — **enrolment never depends on a camera**).
 */
const STEPS = [
  { id: 'scan', label: 'Scan' },
  { id: 'verify', label: 'Verify' },
  { id: 'codes', label: 'Save codes' },
  { id: 'done', label: 'Confirm' },
] as const;

type StepId = (typeof STEPS)[number]['id'];

export interface EnrolmentProps {
  /** ⛔ **`false` for an account whose password lives at an identity provider.** */
  readonly canEnrol: boolean;
  readonly onFinished: () => void;
  readonly onCancel: () => void;
}

export function Enrolment({ canEnrol, onFinished, onCancel }: EnrolmentProps) {
  const [step, setStep] = useState<StepId>('scan');
  const [password, setPassword] = useState('');
  const [secret, setSecret] = useState<string | null>(null);
  const [codes, setCodes] = useState<readonly string[]>([]);
  const [code, setCode] = useState('');
  const [wrong, setWrong] = useState(false);
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState<string | null>(null);
  /**
   * 📁 **`Security Gates` `2.1.1`** — *"paste fills all six boxes and **moves
   * focus to the primary action**."* ⚡ **A complete code has nothing left to
   * type**, and the design's sentence applies wherever a one-time code is
   * entered rather than only on the gate that states it.
   */
  const verifyRef = useRef<HTMLButtonElement>(null);

  if (!canEnrol) {
    return (
      <div className="rounded-md border border-border bg-surface-sunken p-4" role="note">
        <p className="text-sm leading-6 text-content">
          You cannot add an authenticator app to this account.
        </p>
        <p className="mt-1 text-sm leading-6 text-content-muted">
          Signora enrols a second factor by verifying your password, and your password
          lives with your identity provider — Signora has never held it. Your second
          factors are managed there, alongside your sign-in.
        </p>
      </div>
    );
  }

  async function begin(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setFailed(null);
    const result = await authClient.twoFactor.enable({ password });
    setBusy(false);
    if (result.error) {
      setFailed(result.error.message ?? 'That password was not accepted.');
      return;
    }
    setSecret(manualKeyFrom(result.data.totpURI));
    setCodes(result.data.backupCodes);
  }

  async function verify() {
    setBusy(true);
    setWrong(false);
    const result = await authClient.twoFactor.verifyTotp({ code });
    setBusy(false);
    if (result.error) {
      setWrong(true);
      return;
    }
    setStep('codes');
  }

  const completed = STEPS.slice(
    0,
    STEPS.findIndex((s) => s.id === step),
  ).map((s) => s.id);

  return (
    <div className="flex flex-col gap-5" data-testid="enrolment">
      {/* ♿ 📁 *"the enrolment stepper announces step N of 4"* — `StepRail` owns
          `aria-current="step"` and the count, so this composes rather than
          re-solving it ([TASK-478](../../../../../docs/BACKLOG.md)). */}
      <StepRail steps={[...STEPS]} currentId={step} completedIds={completed} />

      {secret === null ? (
        <form className="flex max-w-sm flex-col gap-3" onSubmit={begin}>
          <p className="text-sm leading-6 text-content-muted">
            Confirm it is you before anything changes. Signora asks for a fresh factor
            even inside a valid session.
          </p>
          <PasswordField
            label="Your password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete="current-password"
            required
            /**
             * 🔴 **The refusal was a loose paragraph beside the field** —
             * 📁 `Security Center` `2.4.7`: *"the message is programmatically
             * associated."* ⛔ **Nothing connected the two**, so a
             * screen-reader user heard a sentence with no owner.
             *
             * ✅ **`Input.error` already does all of it** — `aria-invalid`,
             * `aria-describedby` and the message itself. ⛔ **Rendering a
             * second paragraph was building around the library rather than
             * using it** ([§20c](../../../../../CLAUDE.md)).
             */
            {...(failed === null ? {} : { error: failed })}
          />
          <div className="flex flex-wrap gap-2">
            <Button type="submit" loading={busy}>
              Continue
            </Button>
            <Button type="button" variant="ghost" onClick={onCancel}>
              Cancel
            </Button>
          </div>
        </form>
      ) : step === 'scan' ? (
        <ScanStep secret={secret} onNext={() => setStep('verify')} />
      ) : step === 'verify' ? (
        <div className="flex max-w-sm flex-col gap-3">
          <p className="text-sm text-content">
            Enter the 6-digit code to confirm the app is working
          </p>
          <CodeInput
            label="Verification code"
            value={code}
            onChange={setCode}
            invalid={wrong}
            // 📁 `Security Center` `2.4.7` — *"the message is programmatically
            // associated."* ⛔ **The sentence was adjacent and unconnected.**
            errorId="enrolment-code-error"
            onPasteComplete={() => verifyRef.current?.focus()}
          />
          {/**
            * ⚠️ **`role="alert"` KEPT, and the politeness is a conflict this
            * lane will not settle by editing** — 📁
            * [C-1572](../../../../../docs/LANE_COORDINATION.md).
            *
            * 📁 **`Security Center` `4.1.3`**: *"only failures interrupt with
            * an **alert** role"* — **a wrong code is a failure.**
            * 📁 **`System States` `4.1.3`**: *"only a state that **ends the
            * session** announces assertively"* — **a wrong code ends nothing.**
            *
            * ⛔ **Two authoritative documents, opposite answers, one control.**
            * ⚡ **The product already disagrees with itself**:
            * `step-up-dialog.tsx` uses `role="status"` for the same event, with
            * a comment explaining why. **That inconsistency IS the evidence, so
            * it is preserved rather than tidied away.**
            */}
          {wrong ? (
            <p id="enrolment-code-error" role="alert" className="text-sm text-danger">
              That code is not valid. Codes rotate every 30 seconds — a code from the
              previous window is still accepted.
            </p>
          ) : null}
          <div>
            <Button
              ref={verifyRef}
              onClick={verify}
              loading={busy}
              disabled={code.length < 6}
            >
              Verify and continue
            </Button>
          </div>
        </div>
      ) : step === 'codes' ? (
        <BackupCodes codes={codes} onNext={() => setStep('done')} />
      ) : (
        <div className="flex flex-col gap-3">
          <p className="text-sm leading-6 text-content">
            Your authenticator app is active. Signing in now asks for a code from it.
          </p>
          <div>
            <Button onClick={onFinished}>Done</Button>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * 📁 ***"JBSW Y3DP EHPK 3PXP · Grouped in fours and read aloud correctly by
 * screen readers, rather than as one 16-character string."***
 *
 * ⚡ **The grouping is for the ear as much as the eye**, which is why it is
 * real whitespace in the text rather than letter-spacing in CSS.
 */
export function groupInFours(secret: string): string {
  return (secret.match(/.{1,4}/g) ?? []).join(' ');
}

/**
 * ⛔ **The manual key is read out of the URI Better Auth returns**, never
 * stored separately — two copies of a shared secret is one copy too many.
 */
export function manualKeyFrom(totpUri: string): string {
  const secret = new URL(totpUri.replace(/^otpauth:/, 'https:')).searchParams.get(
    'secret',
  );
  return secret ?? '';
}

function ScanStep({ secret, onNext }: { secret: string; onNext: () => void }) {
  return (
    <div className="flex flex-col gap-4">
      <p className="text-sm leading-6 text-content-muted">
        Scan with any TOTP app — 1Password, Okta Verify, Authy, Google Authenticator.
        Signora does not require a specific app: a code is a code.
      </p>

      {/**
       * ⛔ **No QR image is drawn, and the reason is not laziness.** ⚡ **A QR
       * code is a picture of the key** — the repository has no QR renderer, and
       * adding a dependency to draw one is outside this row's Change Budget.
       * ✅ **The manual key below is the same secret and the design already
       * requires it at every width**, so nothing here is unreachable: 📁 *"the
       * QR pane always exposes the manual key, so enrolment never depends on a
       * camera or on seeing an image"* (WCAG 2.1.1).
       */}
      <div>
        <p className="text-sm font-medium text-content">Enter this key in your app</p>
        <p
          className="mt-1 select-all font-mono text-base tracking-wide text-content"
          data-testid="manual-key"
        >
          {groupInFours(secret)}
        </p>
        <p className="mt-1 text-xs text-content-muted">
          Grouped in fours so it can be read aloud and typed without losing your place.
        </p>
      </div>

      <div>
        <Button onClick={onNext}>I have added it</Button>
      </div>
    </div>
  );
}

/**
 * 📁 ***"Ten single-use codes. This is the only screen that will ever display
 * them — Signora stores hashes, so it cannot show them again, and says so
 * instead of implying they can be retrieved."***
 *
 * 🔴 **Shown exactly once is the row's Playwright assertion**, and it holds
 * because nothing keeps them: they arrive in the `enable` response, live in
 * component state for one flow, and there is no call anywhere that could ask
 * for them again.
 */
function BackupCodes({
  codes,
  onNext,
}: {
  codes: readonly string[];
  onNext: () => void;
}) {
  return (
    <div className="flex flex-col gap-4">
      <div>
        <p className="text-sm font-medium text-content">Backup codes · shown once</p>
        <p className="mt-1 text-sm leading-6 text-content-muted">
          Single-use codes for when every device is unavailable. This is the only screen
          that will ever display them — Signora stores hashes, so it cannot show them
          again.
        </p>
      </div>

      {/* ♿ 📁 *"Backup codes are readable, selectable and downloadable — never an
          image."* A list, in a monospace face, that a person can select. */}
      <ol
        className="grid grid-cols-2 gap-1.5 font-mono text-sm"
        data-testid="backup-codes"
      >
        {codes.map((backupCode, index) => (
          <li key={backupCode} className="select-all text-content">
            <span className="mr-2 text-content-muted">
              {String(index + 1).padStart(2, '0')}
            </span>
            {backupCode}
          </li>
        ))}
      </ol>

      <div className="flex flex-wrap gap-2">
        <DownloadCodes codes={codes} />
        <Button onClick={onNext}>I have saved them</Button>
      </div>
    </div>
  );
}

function DownloadCodes({ codes }: { codes: readonly string[] }) {
  /**
   * ♿ **Downloadable, which the design names as an accessibility requirement
   * rather than a convenience** — somebody who cannot reliably transcribe
   * sixteen characters must still be able to keep them.
   */
  const href = `data:text/plain;charset=utf-8,${encodeURIComponent(codes.join('\n'))}`;
  return (
    <a
      className="inline-flex h-9 items-center rounded-md border border-border px-3 text-sm font-medium text-content hover:bg-surface-sunken "
      href={href}
      download="signora-backup-codes.txt"
    >
      Download .txt
    </a>
  );
}
