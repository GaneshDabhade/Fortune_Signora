'use client';

import { useEffect, useState } from 'react';

import { Button } from '@/components/ui';
import { CodeInput } from '@/components/ui/code-input';
import { Dialog } from '@/components/ui/dialog';

/**
 * **Confirm it is you** — [TASK-1410](../../../docs/BACKLOG.md), against
 * `docs/design-snapshot/screens/Fortune Signora Security Center.dc.html` §02.
 *
 * > 📁 ***"Every control in this module requires a fresh factor before it will
 * > act, even inside a valid session. The prompt states what it is about to
 * > authorise, because 'confirm your identity' with no object is how people
 * > approve things they did not intend."***
 *
 * ## 🔴 It is an authorization boundary that happens to have a dialog
 *
 * ⚠️ **The row names the risk in exactly those terms**: *"building this as a UI
 * dialog"* is the failure. ⛔ **This component authorises nothing.** **The
 * server does** — `freshAge: 600` in
 * [`lib/auth/server.ts`](../../lib/auth/server.ts), enforced by Better Auth,
 * which raises `SESSION_NOT_FRESH`. ⚡ **A caller that never opens this dialog
 * is refused by the server rather than by the screen it did not open**, which
 * is the whole of the row's Security Invariant.
 *
 * ## ⛔ `action` is required, and that is the design's sentence made structural
 *
 * 📁 ***"'confirm your identity' with no object is how people approve things
 * they did not intend."*** ⚡ **So there is no default and no optional
 * phrasing**: a caller that cannot name what it is about to do cannot open
 * this dialog. **The design's own example is *"You are about to Revoke 3
 * sessions and 2 connected apps"*** — a count and a noun, in the customer's
 * words.
 *
 * ## ⚡ The expiry is shown because the design shows it
 *
 * 📁 *"6-digit code from Okta Verify · **expires in 4:52**"*. ⛔ **A code with
 * a silent expiry fails as a wrong code**, and somebody retypes it twice
 * before suspecting time.
 *
 * ## ♿ Focus returns to the control that opened it
 *
 * ⚠️ **[B-312](../../../docs/BUGS.md) is an open defect for exactly this class
 * and the row says it must not be repeated.** ✅ **`Dialog` already traps focus
 * and restores it** — 📁 [TASK-478](../../../docs/BACKLOG.md) built that, so
 * this composes rather than re-solving it.
 */

export interface StepUpDialogProps {
  open: boolean;
  /**
   * 📁 **What is about to be authorised, in the customer's words** — the
   * sentence completes *"You are about to __"*. ⛔ **Required.**
   */
  action: string;
  /** Seconds until the code expires. 📁 The design shows a countdown. */
  expiresInSeconds: number;
  /** Verifies the code. ⛔ **Resolves `false` for a wrong code — it never throws for one.** */
  onConfirm: (code: string) => Promise<boolean>;
  onDismiss: () => void;
  onUseBackupCode?: () => void;
}

/** 📁 `otpLength: 6`, and the design's *"6-digit code"*. */
const CODE_LENGTH = 6;

function clock(seconds: number): string {
  const safe = Math.max(0, seconds);
  return `${Math.floor(safe / 60)}:${String(safe % 60).padStart(2, '0')}`;
}

export function StepUpDialog({
  open,
  action,
  expiresInSeconds,
  onConfirm,
  onDismiss,
  onUseBackupCode,
}: StepUpDialogProps) {
  const [code, setCode] = useState('');
  const [wrong, setWrong] = useState(false);
  const [checking, setChecking] = useState(false);
  const [left, setLeft] = useState(expiresInSeconds);

  useEffect(() => {
    if (!open) return;
    setLeft(expiresInSeconds);
    setCode('');
    setWrong(false);
  }, [open, expiresInSeconds]);

  useEffect(() => {
    if (!open || left <= 0) return;
    const tick = setInterval(() => setLeft((s) => s - 1), 1000);
    return () => clearInterval(tick);
  }, [open, left]);

  const expired = left <= 0;

  const confirm = async () => {
    setChecking(true);
    const ok = await onConfirm(code);
    setChecking(false);
    // ⛔ **A wrong code KEEPS the digits.** 📁 TASK-486's rule: retyping six
    // characters to fix one is the complaint the design names.
    setWrong(!ok);
  };

  return (
    <Dialog open={open} onClose={onDismiss} title="Confirm it is you">
      <div className="flex flex-col gap-4">
        {/* 🔴 The object of the sentence, and the reason the prop is required. */}
        <p className="text-sm leading-6 text-content">
          You are about to <strong className="font-semibold">{action}</strong>
        </p>

        <CodeInput
          value={code}
          onChange={(next) => {
            setCode(next);
            setWrong(false);
          }}
          length={CODE_LENGTH}
          label="6-digit code"
          disabled={checking || expired}
          invalid={wrong}
          // 📁 `2.4.7` — the sentence below is now connected to this group.
          errorId="step-up-code-error"
        />

        {wrong ? (
          // ♿ Announced politely: the person is looking at the field they just
          // used, so an assertive interruption buys nothing.
          <p id="step-up-code-error" role="status" className="text-sm text-danger">
            That code did not match. Check it and try again.
          </p>
        ) : (
          <p role="status" className="text-xs text-content-subtle">
            {expired
              ? 'That code has expired — ask for another.'
              : `Expires in ${clock(left)}`}
          </p>
        )}

        <div className="flex items-center gap-3">
          <Button
            type="button"
            onClick={() => void confirm()}
            loading={checking}
            disabled={code.length < CODE_LENGTH || expired}
          >
            Confirm
          </Button>
          {onUseBackupCode ? (
            <button
              type="button"
              onClick={onUseBackupCode}
              className="rounded text-sm font-medium text-accent underline decoration-border underline-offset-4 transition-colors hover:decoration-accent "
            >
              Use a backup code
            </button>
          ) : null}
        </div>

        {/* 📁 *"Step-up lasts 10 minutes… short enough that an unlocked laptop
            is not a standing authorisation."* Said to the person, because a
            time-boxed grant they do not know about is one they will be
            surprised by. */}
        <p className="text-xs text-content-subtle">
          Confirming lasts 10 minutes, then Signora asks again.
        </p>
      </div>
    </Dialog>
  );
}
