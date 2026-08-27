'use client';

import { useState } from 'react';

import { Badge, Button, Card, CardBody, CardHeader, CardTitle, PasswordField } from '@/components/ui';
import { authClient } from '@/lib/auth/client';

import { Enrolment } from './enrolment';
import { RESISTANCE_LABEL, byResistance, removalConsequence, type SecondFactor } from './rules';

/**
 * **§03 · Second factors** — [TASK-1414](../../../../../docs/BACKLOG.md).
 *
 * 📁 ***"Methods are ordered by how well they resist phishing, and the order is
 * stated rather than implied."***
 *
 * ## 🔴 The design lists five methods and this product has two
 *
 * ⛔ **Passkey, Okta Verify push and SMS are not built** — 📁 `better-auth@^1.1.0`
 * ships no passkey plugin, and nothing sends a push or an SMS.
 * ⚡ **They are not rendered as greyed-out rows either**: a method a person
 * cannot enrol, drawn as though they could, is the false-affordance class this
 * lane has refused three times.
 *
 * ✅ **What is real is real**: an authenticator app, and the backup codes that
 * come with it.
 *
 * ## ⛔ Removal states its blast radius and never refuses
 *
 * 📁 The design refuses removing the last phishing-resistant factor. ⚠️ **That
 * rule has no subject here** — [`rules.ts`](rules.ts) carries the measurement
 * and the reason, and the alternative would have been a branch that cannot be
 * reached ([§2](../../../../../CLAUDE.md)).
 */
export interface FactorsPanelProps {
  /** ⛔ **Read from the session on the server**, never inferred from a UI state. */
  readonly twoFactorEnabled: boolean;
  /** `false` when the account's password lives with an identity provider. */
  readonly hasPassword: boolean;
}

export function FactorsPanel({ twoFactorEnabled, hasPassword }: FactorsPanelProps) {
  const [enabled, setEnabled] = useState(twoFactorEnabled);
  const [enrolling, setEnrolling] = useState(false);
  const [removing, setRemoving] = useState<string | null>(null);

  const factors = enabled ? byResistance(ENROLLED) : [];

  return (
    <Card>
      <CardHeader className="flex items-start justify-between gap-4">
        <div>
          <CardTitle>Second factors</CardTitle>
          <p className="mt-1 text-sm text-content-muted">
            Ordered by how well they resist phishing, and the order is stated rather than
            implied.
          </p>
        </div>
        {enabled || enrolling ? null : (
          <Button onClick={() => setEnrolling(true)}>Add a method</Button>
        )}
      </CardHeader>
      <CardBody className="flex flex-col gap-5">
        {enrolling ? (
          <Enrolment
            canEnrol={hasPassword}
            onFinished={() => {
              setEnrolling(false);
              setEnabled(true);
            }}
            onCancel={() => setEnrolling(false)}
          />
        ) : factors.length === 0 ? (
          /**
           * ⛔ **Not an empty state that says *no methods*, full stop.** ⚡ **On
           * this page the absence IS the finding**, and the design's own
           * posture cell calls a password-only account a risk.
           */
          <p className="text-sm leading-6 text-content" data-testid="no-factors">
            Your password is the only thing standing between someone with your address and
            your account. Adding an authenticator app takes about a minute and changes that.
          </p>
        ) : (
          <ul className="flex flex-col divide-y divide-border" data-testid="factor-list">
            {factors.map((factor) => (
              <li key={factor.id} className="flex flex-col gap-2 py-3 first:pt-0 last:pb-0">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-sm font-medium text-content">{factor.name}</span>
                  <Badge tone="neutral">{factor.state}</Badge>
                  {/* 📁 *"the order is STATED rather than implied"* — the class
                      travels with the row, not with its position in the list. */}
                  <Badge tone={factor.resistance === 'vulnerable' ? 'danger' : 'info'}>
                    {RESISTANCE_LABEL[factor.resistance]}
                  </Badge>
                </div>
                <p className="text-sm leading-6 text-content-muted">{factor.explanation}</p>
                {factor.id === 'totp' ? (
                  <div>
                    <Button variant="ghost" onClick={() => setRemoving(factor.id)}>
                      Remove
                    </Button>
                  </div>
                ) : null}
              </li>
            ))}
          </ul>
        )}

        {removing === null ? null : (
          <RemoveFactor
            consequence={removalConsequence(factors, removing)}
            onCancel={() => setRemoving(null)}
            onRemoved={() => {
              setRemoving(null);
              setEnabled(false);
            }}
          />
        )}
      </CardBody>
    </Card>
  );
}

/**
 * ⚡ **The two methods this product can actually offer**, in the design's own
 * words for each — ⛔ **the three it cannot are absent rather than disabled.**
 */
const ENROLLED: readonly SecondFactor[] = [
  {
    id: 'totp',
    name: 'Authenticator app',
    state: 'Active',
    resistance: 'codes',
    explanation:
      'Six-digit TOTP. Works offline and when your phone has no signal, which is why it stays even though it is weaker than a passkey.',
  },
  {
    id: 'backup',
    name: 'Backup codes',
    state: 'Shown once',
    resistance: 'last-resort',
    explanation:
      'Single-use codes for when every device is unavailable. The only method that survives losing your phone and your laptop on the same day.',
  },
];

/**
 * 📁 ***"Every destructive control states its blast radius before it fires."***
 *
 * ⚡ **And the fresh factor is the vendor's, not this dialog's**: Better Auth's
 * `twoFactor.disable` takes the password and refuses without it, so a caller
 * that skips this form is refused by the server rather than by the screen it
 * did not open ([TASK-1410](../../../../../docs/BACKLOG.md)).
 */
function RemoveFactor({
  consequence,
  onCancel,
  onRemoved,
}: {
  consequence: string;
  onCancel: () => void;
  onRemoved: () => void;
}) {
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState<string | null>(null);

  async function remove(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setFailed(null);
    const result = await authClient.twoFactor.disable({ password });
    setBusy(false);
    if (result.error) {
      setFailed(result.error.message ?? 'That password was not accepted.');
      return;
    }
    onRemoved();
  }

  return (
    <form
      className="flex max-w-md flex-col gap-3 rounded-md border border-border p-4"
      onSubmit={remove}
      data-testid="remove-factor"
    >
      <p className="text-sm font-medium text-content">Remove your authenticator app?</p>
      <p className="text-sm leading-6 text-content-muted">{consequence}</p>
      <PasswordField
        label="Your password"
        value={password}
        onChange={(event) => setPassword(event.target.value)}
        autoComplete="current-password"
        required
        /**
         * 🔴 **The refusal was a loose paragraph beside the field** — the same
         * defect [`enrolment.tsx`](enrolment.tsx) carried, and this form has
         * **one** field, so there is nothing to guess about what failed.
         *
         * ✅ **`Input.error` already does all of it** — `aria-invalid`,
         * `aria-describedby`, and the message with `role="alert"` on it, so
         * the announcement is unchanged and the association is added.
         * ⛔ **Rendering a second paragraph was building around the library
         * rather than using it** ([§20c](../../../../../CLAUDE.md)).
         */
        {...(failed === null ? {} : { error: failed })}
      />
      <div className="flex flex-wrap gap-2">
        <Button type="submit" variant="danger" loading={busy}>
          Remove it
        </Button>
        <Button type="button" variant="ghost" onClick={onCancel}>
          Keep it
        </Button>
      </div>
    </form>
  );
}
