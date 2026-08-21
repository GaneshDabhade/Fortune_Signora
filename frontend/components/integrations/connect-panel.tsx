'use client';

import { Badge, Button } from '@/components/ui';
import { CAPABILITY_VALUE, systemName } from '@/components/integrations/connection-center';
import type { IntegrationCapability, IntegrationSystem } from '@/lib/api/types';
import { outcomeFor } from '@/lib/integrations/outcomes';

/**
 * What a customer reads before they connect a system, and after they return.
 *
 * **The most consequential screen in the module.** Everything else reports
 * state; this one asks somebody to hand Signora access to a system their
 * business runs on. It has to earn that, and it earns it by being specific.
 *
 * ### It answers the four questions people actually have
 *
 * *What am I connecting · what will Signora do with it · what is it allowed to
 * do · how do I undo this.* The last is not a footnote: a customer who cannot
 * see how to reverse a decision hesitates over making it, and the honest answer
 * — one click, any time — is a reason to say yes rather than a caveat.
 *
 * ### Read-only is the headline, not the small print
 *
 * Every Day One capability is an observation source. Saying so first is both
 * true and the single most reassuring sentence available, and burying it under
 * a permissions list would waste it.
 *
 * ### Failures get the same care as success
 *
 * Every outcome answers what happened, why, and what to do next. A customer who
 * cancelled is told nothing was changed rather than that something failed —
 * they made a choice, and reading it as an error is the product misunderstanding
 * them.
 */

interface ConnectPanelProps {
  system: IntegrationSystem;
  /** The outcome of a return trip, if the customer has just come back. */
  outcome?: string;
  onConnect: () => void;
  onDismiss: () => void;
}

export function ConnectPanel({ system, outcome, onConnect, onDismiss }: ConnectPanelProps) {
  if (outcome) {
    return <ConnectResult system={system} code={outcome} onRetry={onConnect} onDismiss={onDismiss} />;
  }

  const name = systemName(system.integration);

  return (
    <section className="flex flex-col gap-4">
      <header className="flex flex-col gap-1">
        <h2 className="text-base font-medium text-content">Connect {name}</h2>
        <p className="text-sm text-content-muted">
          Signora will read information from {name} to work out which accounts deserve your
          attention and why.
        </p>
      </header>

      <div className="flex flex-col gap-2">
        <h3 className="text-xs font-medium uppercase tracking-wide text-content-muted">
          What this gives you
        </h3>
        <ul className="flex flex-col gap-1">
          {system.capabilities.map((capability: IntegrationCapability) => (
            <li key={capability} className="text-sm text-content">
              {CAPABILITY_VALUE[capability]}
            </li>
          ))}
        </ul>
      </div>

      <div className="flex flex-col gap-2">
        <h3 className="text-xs font-medium uppercase tracking-wide text-content-muted">
          What Signora can do
        </h3>
        {/* First and unqualified, because it is the most reassuring true thing
            available and every Day One capability is an observation source. */}
        <p className="text-sm text-content">
          Read only. Signora never creates, changes or deletes anything in {name}.
        </p>
        <p className="text-sm text-content-muted">
          You will be taken to {name} to approve this. Signora never sees your password.
        </p>
      </div>

      <div className="flex flex-col gap-2">
        <h3 className="text-xs font-medium uppercase tracking-wide text-content-muted">
          If you change your mind
        </h3>
        <p className="text-sm text-content-muted">
          You can disconnect {name} at any time from this page. Signora stops reading from it
          immediately.
        </p>
      </div>

      {system.connectable ? (
        <div className="flex flex-wrap items-center gap-2">
          <Button onClick={onConnect}>Continue to {name}</Button>
          <Button variant="ghost" onClick={onDismiss}>
            Not now
          </Button>
        </div>
      ) : (
        // No dead button. The catalog says this cannot be connected yet, and
        // offering a control that does nothing is worse than saying so.
        <div className="flex flex-col gap-2">
          <Badge tone="neutral">Not available yet</Badge>
          <p className="text-sm text-content-muted">
            Connecting {name} is not available yet. It will appear here when it is.
          </p>
          <Button variant="ghost" onClick={onDismiss}>
            Close
          </Button>
        </div>
      )}
    </section>
  );
}

function ConnectResult({
  system,
  code,
  onRetry,
  onDismiss,
}: {
  system: IntegrationSystem;
  code: string;
  onRetry: () => void;
  onDismiss: () => void;
}) {
  const name = systemName(system.integration);
  const outcome = outcomeFor(code);
  const succeeded = code === 'connected';

  return (
    <section className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-2">
        <Badge tone={succeeded ? 'success' : 'warning'}>
          {succeeded ? 'Connected' : 'Not connected'}
        </Badge>
        <h2 className="text-base font-medium text-content">
          {succeeded ? `${name} is connected` : outcome.what}
        </h2>
      </div>

      {succeeded ? (
        <p className="text-sm text-content-muted">
          Signora is now reading from {name}. You will start to see it reflected in your
          accounts shortly.
        </p>
      ) : (
        <>
          {outcome.why ? (
            <p className="text-sm text-content-muted">{outcome.why}</p>
          ) : null}
          {outcome.next ? <p className="text-sm text-content">{outcome.next}</p> : null}
        </>
      )}

      <div className="flex flex-wrap items-center gap-2">
        {/* Retry offered only where trying again could plausibly work. Inviting
            somebody to press a button that will fail identically is the product
            wasting their afternoon. */}
        {!succeeded && outcome.recoverable ? (
          <Button onClick={onRetry}>Try again</Button>
        ) : null}
        <Button variant="ghost" onClick={onDismiss}>
          {succeeded ? 'Done' : 'Close'}
        </Button>
      </div>
    </section>
  );
}
