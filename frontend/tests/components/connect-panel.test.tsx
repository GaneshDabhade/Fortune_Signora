import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { ConnectPanel } from '@/components/integrations/connect-panel';
import type { IntegrationSystem } from '@/lib/api/types';
import { CONNECT_OUTCOMES, type ConnectOutcomeCode } from '@/lib/integrations/outcomes';

function system(overrides: Partial<IntegrationSystem> = {}): IntegrationSystem {
  return {
    integration: 'hubspot',
    capabilities: ['crm_activity'],
    connectable: true,
    working: false,
    needs_attention: false,
    connections: [],
    ...overrides,
  };
}

function renderPanel(props: Partial<Parameters<typeof ConnectPanel>[0]> = {}) {
  return render(
    <ConnectPanel
      system={system()}
      onConnect={vi.fn()}
      onDismiss={vi.fn()}
      {...props}
    />,
  );
}

const FAILURES = (Object.keys(CONNECT_OUTCOMES) as ConnectOutcomeCode[]).filter(
  (code) => code !== 'connected',
);

describe('every failure answers three questions', () => {
  it.each(FAILURES)('%s says what, why and what next', (code) => {
    // **The rule this file exists to enforce.** A message answering fewer
    // leaves somebody with a screenshot and a support ticket.
    const outcome = CONNECT_OUTCOMES[code];
    expect(outcome.what).toBeTruthy();
    expect(outcome.why).toBeTruthy();
    expect(outcome.next).toBeTruthy();
  });

  it.each(FAILURES)('%s renders all three to the customer', (code) => {
    renderPanel({ outcome: code });
    const outcome = CONNECT_OUTCOMES[code];
    expect(screen.getByText(outcome.what)).toBeInTheDocument();
    expect(screen.getByText(outcome.why as string)).toBeInTheDocument();
    expect(screen.getByText(outcome.next as string)).toBeInTheDocument();
  });

  it('success needs no explanation', () => {
    expect(CONNECT_OUTCOMES.connected.why).toBeUndefined();
    expect(CONNECT_OUTCOMES.connected.next).toBeUndefined();
  });
});

describe('no implementation language reaches the customer', () => {
  const mechanics = /oauth|token|scope|grant|refresh|redirect|callback|client id|bearer|api key/i;

  it.each(Object.keys(CONNECT_OUTCOMES) as ConnectOutcomeCode[])(
    '%s uses no mechanism vocabulary',
    (code) => {
      const outcome = CONNECT_OUTCOMES[code];
      const text = [outcome.what, outcome.why, outcome.next].join(' ');
      expect(text).not.toMatch(mechanics);
    },
  );

  it('the panel itself names no mechanism', () => {
    renderPanel();
    expect(document.body.textContent ?? '').not.toMatch(mechanics);
  });
});

describe('retry is offered only where it could work', () => {
  it.each(FAILURES.filter((c) => CONNECT_OUTCOMES[c].recoverable))(
    '%s offers a way to try again',
    (code) => {
      renderPanel({ outcome: code });
      expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
    },
  );

  it.each(FAILURES.filter((c) => !CONNECT_OUTCOMES[c].recoverable))(
    '%s does not invite a pointless retry',
    (code) => {
      // Inviting somebody to press a button that will fail identically is the
      // product wasting their afternoon.
      renderPanel({ outcome: code });
      expect(screen.queryByRole('button', { name: /try again/i })).not.toBeInTheDocument();
    },
  );
});

describe('cancelling is not an error', () => {
  it('says nothing was changed rather than that something failed', () => {
    // The commonest reason for landing here is that somebody changed their
    // mind. Reading a choice as a failure is the product misunderstanding them.
    renderPanel({ outcome: 'cancelled' });
    expect(screen.getByText(/nothing was changed/i)).toBeInTheDocument();
    expect(document.body.textContent ?? '').not.toMatch(/error|failed/i);
  });
});

describe('before connecting, it answers what people actually ask', () => {
  it('says what this gives you', () => {
    renderPanel();
    expect(screen.getByText('What this gives you')).toBeInTheDocument();
    expect(screen.getByText(/what your team logged against an account/i)).toBeInTheDocument();
  });

  it('leads with read-only rather than burying it', () => {
    // The most reassuring true thing available, and every Day One capability
    // is an observation source.
    renderPanel();
    expect(screen.getByText(/read only/i)).toBeInTheDocument();
    expect(screen.getByText(/never creates, changes or deletes/i)).toBeInTheDocument();
  });

  it('says how to undo it before asking for the decision', () => {
    // A customer who cannot see how to reverse a choice hesitates over making
    // it. One click, any time, is a reason to say yes.
    renderPanel();
    expect(screen.getByText('If you change your mind')).toBeInTheDocument();
    expect(screen.getByText(/disconnect .* at any time/i)).toBeInTheDocument();
  });

  it('promises Signora never sees a password', () => {
    renderPanel();
    expect(screen.getByText(/never sees your password/i)).toBeInTheDocument();
  });
});

describe('a system that cannot be connected offers no dead button', () => {
  it('says so instead of showing a control that does nothing', () => {
    renderPanel({ system: system({ connectable: false }) });
    expect(screen.getByText('Not available yet')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /continue to/i })).not.toBeInTheDocument();
  });

  it('offers the button when it is connectable', () => {
    renderPanel();
    expect(screen.getByRole('button', { name: /continue to hubspot/i })).toBeInTheDocument();
  });
});

describe('after connecting', () => {
  it('says what happens next rather than only that it worked', () => {
    renderPanel({ outcome: 'connected' });
    expect(screen.getByText(/hubspot is connected/i)).toBeInTheDocument();
    expect(screen.getByText(/start to see it reflected/i)).toBeInTheDocument();
  });

  it('does not offer a retry after success', () => {
    renderPanel({ outcome: 'connected' });
    expect(screen.queryByRole('button', { name: /try again/i })).not.toBeInTheDocument();
  });
});
