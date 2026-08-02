import { render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import {
  ATTENTION_REASON,
  CAPABILITY_VALUE,
  ConnectionCenter,
  systemName,
} from '@/components/integrations/connection-center';
import type { Connection, IntegrationCapability, IntegrationSystem } from '@/lib/api/types';

function connection(overrides: Partial<Connection> = {}): Connection {
  return {
    id: crypto.randomUUID(),
    integration: 'salesforce',
    label: 'Acme production',
    state: 'validated',
    connected_at: '2026-07-01T09:00:00+00:00',
    attention: 'none',
    reason: null,
    ...overrides,
  };
}

function system(overrides: Partial<IntegrationSystem> = {}): IntegrationSystem {
  return {
    integration: 'salesforce',
    capabilities: ['crm_activity'],
    connectable: false,
    working: false,
    needs_attention: false,
    connections: [],
    ...overrides,
  };
}

function renderCenter(systems: IntegrationSystem[], overrides = {}) {
  return render(
    <ConnectionCenter systems={systems} isLoading={false} isError={false} {...overrides} />,
  );
}

describe('it answers "what would this give me"', () => {
  it('describes the value rather than the system', () => {
    // "Salesforce · Connected" tells an administrator nothing they can act on.
    renderCenter([system()]);
    expect(screen.getByText(CAPABILITY_VALUE.crm_activity)).toBeInTheDocument();
  });

  it.each(Object.keys(CAPABILITY_VALUE) as IntegrationCapability[])(
    '%s has customer-facing wording',
    (capability) => {
      expect(CAPABILITY_VALUE[capability]).toBeTruthy();
    },
  );

  it('says so plainly when Signora cannot use anything from a system yet', () => {
    // The alternative — listing a capability that waits on unbuilt work — is
    // the product promising something it cannot do.
    renderCenter([system({ capabilities: [] })]);
    expect(screen.getByText(/cannot use anything from this yet/i)).toBeInTheDocument();
  });
});

describe('it shows systems nobody has connected', () => {
  it('lists a system with no connections at all', () => {
    // The row that most often matters is the one nobody connected. A screen
    // built from connections alone structurally cannot show it.
    renderCenter([system({ integration: 'hubspot', connections: [] })]);
    expect(screen.getByText(systemName('hubspot'))).toBeInTheDocument();
    expect(screen.getByText('Not connected')).toBeInTheDocument();
  });

  it('says when connecting is not available yet rather than offering a dead button', () => {
    renderCenter([system({ connectable: false })]);
    expect(screen.getByText(/not available yet/i)).toBeInTheDocument();
  });
});

describe('broken connections are impossible to miss', () => {
  it('counts what needs attention at the top', () => {
    renderCenter([
      system({ needs_attention: true }),
      system({ integration: 'hubspot', needs_attention: true }),
    ]);
    expect(screen.getByText('2 connections need your attention.')).toBeInTheDocument();
  });

  it('says nothing at the top when nothing is wrong', () => {
    renderCenter([system({ working: true })]);
    expect(screen.queryByText(/need your attention/i)).not.toBeInTheDocument();
  });

  it.each(Object.entries(ATTENTION_REASON))(
    '%s tells the customer what to do',
    (reason, sentence) => {
      renderCenter([
        system({
          needs_attention: true,
          connections: [connection({ attention: 'now', reason })],
        }),
      ]);
      expect(screen.getByText(sentence)).toBeInTheDocument();
    },
  );
});

describe('working is not the same as connected', () => {
  it('a system whose only connection was revoked does not read as ready', () => {
    // **The worst thing this screen could say.** Answering "is my CRM
    // connected?" with yes, while nothing is flowing, is the failure the whole
    // page exists to prevent.
    renderCenter([
      system({
        working: false,
        needs_attention: true,
        connections: [connection({ state: 'revoked', attention: 'now', reason: 'permission_withdrawn' })],
      }),
    ]);
    expect(screen.queryByText('Ready to use')).not.toBeInTheDocument();
    expect(screen.getByText('Action required')).toBeInTheDocument();
  });

  it('a working system reads as ready to use', () => {
    renderCenter([system({ working: true, connections: [connection()] })]);
    expect(screen.getByText('Ready to use')).toBeInTheDocument();
  });

  it('a deliberately disconnected system reads as turned off, not broken', () => {
    renderCenter([
      system({ working: false, connections: [connection({ state: 'disconnected' })] }),
    ]);
    // Twice, deliberately: the system reads turned off and so does the
    // connection inside it. The point of the assertion is that neither reads
    // as broken.
    expect(screen.getAllByText('Turned off')).toHaveLength(2);
    expect(screen.queryByText('Action required')).not.toBeInTheDocument();
  });
});

describe('it speaks the customer’s language', () => {
  it('never shows an internal state name', () => {
    const internal = /not_connected|authorizing|validated|revoked|disconnected|expired/;
    renderCenter([
      system({
        connections: [
          connection({ state: 'revoked', attention: 'now', reason: 'permission_withdrawn' }),
        ],
      }),
    ]);
    const [list] = screen.getAllByRole('listitem');
    if (!list) throw new Error('expected a system to render');
    expect(list.textContent ?? '').not.toMatch(internal);
  });

  it('never mentions tokens, scopes, grants or OAuth', () => {
    renderCenter([
      system({
        needs_attention: true,
        connections: [connection({ attention: 'now', reason: 'credential_expired' })],
      }),
    ]);
    const body = document.body.textContent ?? '';
    expect(body).not.toMatch(/oauth|token|scope|grant|refresh|credential/i);
  });

  it('shows a product name rather than a slug', () => {
    renderCenter([system({ integration: 'microsoft_365' })]);
    expect(screen.getByText('Microsoft 365')).toBeInTheDocument();
  });

  it('renders an unknown system without breaking', () => {
    // A connection can outlive a catalog entry that was withdrawn, and it is
    // still the customer's.
    renderCenter([system({ integration: 'legacy_thing', capabilities: [] })]);
    expect(screen.getByText('legacy thing')).toBeInTheDocument();
  });
});

describe('states a customer can reach', () => {
  it('renders an error rather than vanishing', () => {
    renderCenter([], { isError: true });
    expect(screen.getByText(/could not load/i)).toBeInTheDocument();
  });

  it('shows each connection separately when a system has several', () => {
    // Every rep connects their own calendar: many connections of one kind is
    // the normal shape.
    renderCenter([
      system({
        integration: 'google_calendar',
        working: true,
        connections: [
          connection({ label: 'Jane' }),
          connection({ label: 'Sam' }),
          connection({ label: 'Ravi' }),
        ],
      }),
    ]);
    const [card] = screen.getAllByRole('listitem');
    if (!card) throw new Error('expected the system card to render');
    for (const name of ['Jane', 'Sam', 'Ravi']) {
      expect(within(card).getByText(name)).toBeInTheDocument();
    }
  });
});
