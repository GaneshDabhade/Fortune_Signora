'use client';

import { useState } from 'react';

import { Button } from '@/components/ui';
import { signIn } from '@/lib/auth/client';

const OAUTH_LABELS: Record<string, string> = {
  google: 'Continue with Google',
  microsoft: 'Continue with Microsoft',
};

/**
 * The federated methods this deployment actually has.
 *
 * ⛔ **Not a second sign-in journey.** These are the same `socialProviders`
 * the sign-in screen offers, reached from the screen an enterprise buyer
 * opens — `signIn(provider)` is the identical call, producing the identical
 * session ([ADR-0033](../../../../docs/architecture/adr/0033-sign-in-methods.md):
 * the token carries no record of how anybody signed in).
 * **[D-158](../../../../docs/DECISION_REGISTER.md) forbids inventing an
 * alternate customer journey, and this is the existing one offered from a
 * second place.**
 */
export function SsoMethods({ methods }: { methods: string[] }) {
  const [pending, setPending] = useState<string | null>(null);

  if (methods.length === 0) {
    return (
      <p className="rounded-md border border-border bg-surface-sunken px-3 py-2.5 text-sm text-content-muted">
        No federated provider is configured on this deployment, so there is
        nothing to route you to. Your administrator configures these.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-2.5">
      {methods.map((method) => (
        <Button
          key={method}
          type="button"
          variant="secondary"
          className="w-full"
          disabled={pending !== null}
          loading={pending === method}
          onClick={() => {
            setPending(method);
            void signIn(method);
          }}
        >
          {OAUTH_LABELS[method] ?? `Continue with ${method}`}
        </Button>
      ))}
    </div>
  );
}
