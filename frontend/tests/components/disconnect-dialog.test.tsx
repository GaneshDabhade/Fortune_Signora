import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { ConnectionCenter } from '@/components/integrations/connection-center';
import { DisconnectDialog } from '@/components/integrations/disconnect-dialog';
import type { Connection, IntegrationSystem } from '@/lib/api/types';
import type { DisconnectResult } from '@/lib/query/hooks/integrations';

function renderDialog(props: Partial<Parameters<typeof DisconnectDialog>[0]> = {}) {
  return render(
    <DisconnectDialog
      open
      systemSlug="hubspot"
      label="Acme production"
      isPending={false}
      result={null}
      isError={false}
      onConfirm={vi.fn()}
      onClose={vi.fn()}
      {...props}
    />,
  );
}

function result(overrides: Partial<DisconnectResult> = {}): DisconnectResult {
  return {
    state: 'disconnected',
    revoked_at_provider: true,
    already_disconnected: false,
    ...overrides,
  };
}

describe('the confirmation earns its interruption', () => {
  it('says what stops', () => {
    // "Are you sure?" tells somebody nothing they did not already know, and
    // people learn to click through speed bumps.
    renderDialog();
    expect(screen.getByText(/stop reading from acme production immediately/i)).toBeInTheDocument();
  });

  it('says what happens to what Signora already learned', () => {
    renderDialog();
    expect(screen.getByText(/accounts keep their history/i)).toBeInTheDocument();
  });

  it('promises nothing in the other system is changed', () => {
    renderDialog();
    expect(screen.getByText(/nothing in hubspot is changed or deleted/i)).toBeInTheDocument();
  });

  it('says it can be undone before offering the destructive button', () => {
    renderDialog();
    expect(screen.getByText(/connect it again later/i)).toBeInTheDocument();
  });

  it('names the system on the destructive button rather than saying Confirm', () => {
    renderDialog();
    expect(screen.getByRole('button', { name: 'Disconnect HubSpot' })).toBeInTheDocument();
  });

  it('offers a way out that is not a dismissal', () => {
    renderDialog();
    expect(screen.getByRole('button', { name: /keep it connected/i })).toBeInTheDocument();
  });
});

describe('while it is happening', () => {
  it('says so and prevents a second press', () => {
    renderDialog({ isPending: true });
    const button = screen.getByRole('button', { name: /disconnecting/i });
    expect(button).toBeDisabled();
  });

  it('does not let the customer close it mid-flight', () => {
    renderDialog({ isPending: true });
    expect(screen.getByRole('button', { name: /keep it connected/i })).toBeDisabled();
  });
});

describe('the honest partial success', () => {
  it('says plainly when the other system could not be told', () => {
    // **The case that matters most.** A customer who believes they are
    // finished while Signora's access still exists at the vendor is worse off
    // than one given a second step.
    renderDialog({ result: result({ revoked_at_provider: false }) });
    expect(screen.getByText(/could not tell hubspot/i)).toBeInTheDocument();
    expect(screen.getByText(/remove signora from your hubspot settings/i)).toBeInTheDocument();
  });

  it('says the access was removed there when it was', () => {
    renderDialog({ result: result({ revoked_at_provider: true }) });
    expect(screen.getByText(/access there has been removed/i)).toBeInTheDocument();
  });

  it('confirms Signora has stopped reading either way', () => {
    for (const revoked of [true, false]) {
      const { unmount } = renderDialog({ result: result({ revoked_at_provider: revoked }) });
      expect(screen.getByText(/stopped reading from acme production/i)).toBeInTheDocument();
      unmount();
    }
  });

  it('says it can be reconnected', () => {
    renderDialog({ result: result() });
    expect(screen.getByText(/connect hubspot again whenever you want/i)).toBeInTheDocument();
  });
});

describe('when disconnecting fails', () => {
  it('says nothing was changed rather than leaving it ambiguous', () => {
    renderDialog({ isError: true });
    expect(screen.getByText(/nothing was changed/i)).toBeInTheDocument();
  });

  it('leaves the confirmation available to retry', () => {
    renderDialog({ isError: true });
    expect(screen.getByRole('button', { name: 'Disconnect HubSpot' })).toBeEnabled();
  });
});

describe('no implementation language reaches the customer', () => {
  it.each([
    { label: 'confirmation', props: {} },
    { label: 'success', props: { result: result() } },
    { label: 'partial success', props: { result: result({ revoked_at_provider: false }) } },
    { label: 'failure', props: { isError: true } },
  ])('$label mentions no mechanism', ({ props }) => {
    const { unmount } = renderDialog(props);
    expect(document.body.textContent ?? '').not.toMatch(
      /oauth|token|scope|grant|secret|credential|revoke|purge/i,
    );
    unmount();
  });
});

describe('the disconnect control on the Connection Center', () => {
  function system(connections: Connection[]): IntegrationSystem {
    return {
      integration: 'hubspot',
      capabilities: ['crm_activity'],
      connectable: false,
      working: true,
      needs_attention: false,
      connections,
    };
  }

  function connection(overrides: Partial<Connection> = {}): Connection {
    return {
      id: crypto.randomUUID(),
      integration: 'hubspot',
      label: 'Acme production',
      state: 'validated',
      connected_at: null,
      attention: 'none',
      reason: null,
      ...overrides,
    };
  }

  it('offers a labelled control per connection', () => {
    // Labelled with the connection, because an organization with five
    // calendars has five identical buttons otherwise — and a screen reader
    // user would hear "Disconnect" five times with no way to tell them apart.
    render(
      <ConnectionCenter
        systems={[system([connection({ label: 'Jane' }), connection({ label: 'Sam' })])]}
        isLoading={false}
        isError={false}
        onDisconnect={vi.fn()}
      />,
    );
    expect(screen.getByRole('button', { name: 'Disconnect Jane' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Disconnect Sam' })).toBeInTheDocument();
  });

  it('offers nothing for a connection already disconnected', () => {
    render(
      <ConnectionCenter
        systems={[system([connection({ state: 'disconnected' })])]}
        isLoading={false}
        isError={false}
        onDisconnect={vi.fn()}
      />,
    );
    expect(screen.queryByRole('button', { name: /disconnect/i })).not.toBeInTheDocument();
  });

  it('renders no control at all for a reader who cannot disconnect', () => {
    // Not rendered rather than disabled. A disabled button invites somebody to
    // discover they lack permission by pressing it.
    render(
      <ConnectionCenter
        systems={[system([connection()])]}
        isLoading={false}
        isError={false}
      />,
    );
    expect(screen.queryByRole('button', { name: /disconnect/i })).not.toBeInTheDocument();
  });
});
