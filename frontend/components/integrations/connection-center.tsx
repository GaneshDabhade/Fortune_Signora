'use client';

import { Badge, Card, CardBody, CardHeader, CardTitle } from '@/components/ui';
import type {
  Connection,
  ConnectionAttention,
  IntegrationCapability,
  IntegrationSystem,
} from '@/lib/api/types';

/**
 * The Connection Center.
 *
 * **One question, answered at a glance:** *can I trust that Signora is
 * connected to the systems that run my business, and if not, what do I need to
 * do?*
 *
 * ### It is a list of systems, not a list of connections
 *
 * A screen built from connections can only show what somebody already did. The
 * row that most often matters is the one nobody has connected — so every system
 * Signora understands appears, connected or not.
 *
 * ### It talks about what you get, not what you plugged in
 *
 * *Salesforce · Connected* tells an administrator nothing they can act on.
 * *Salesforce — what your team logged against an account* tells them why it is
 * worth fixing when it breaks. The capability is the stable idea; the vendor
 * merely supplies it.
 *
 * ### Nothing here mentions OAuth, tokens, scopes or refreshes
 *
 * A customer reconnects; they do not re-authorize a grant. The domain model
 * carries all of that and none of it reaches this file — which is the point of
 * having put it there.
 */

/** What each capability gives, in the words a customer would use. */
const CAPABILITY_VALUE: Record<IntegrationCapability, string> = {
  crm_activity: 'What your team logged against an account',
  meetings: 'Meetings booked with an account',
  email_engagement: 'Whether an account is replying to your team',
  message_delivery: 'Signora’s conclusions, in your team’s channels',
};

/** Product names. Engineering's slugs never reach a screen. */
const SYSTEM_NAME: Record<string, string> = {
  salesforce: 'Salesforce',
  hubspot: 'HubSpot',
  google_calendar: 'Google Calendar',
  outlook_calendar: 'Outlook Calendar',
  google_workspace: 'Google Workspace',
  microsoft_365: 'Microsoft 365',
  // Slack calls its own tenant a "workspace", which is the exact word ADR-0034
  // keeps off a customer's screen. Saying "team" avoids asking a reader to hold
  // two meanings of one word at once.
  slack: 'Slack',
};

/**
 * What a customer must do, and why. **Never the internal state** — a person
 * reading *"revoked"* learns a database value; reading *"someone removed
 * Signora's access in Salesforce"* learns what happened and who can undo it.
 */
const ATTENTION_REASON: Record<string, string> = {
  permission_withdrawn: 'Access was removed in the other system. Reconnect to restore it.',
  credential_expired: 'The connection has lapsed. Reconnect to restore it.',
  authorization_unfinished: 'Connecting was never finished. Start again to complete it.',
  credential_expiring: 'This will stop working soon. Reconnect to keep it running.',
};

const CONNECTION_STATE: Record<string, string> = {
  connected: 'Connected',
  validated: 'Working',
  authorizing: 'Not finished',
  expired: 'Lapsed',
  revoked: 'Access removed',
  disconnected: 'Turned off',
  not_connected: 'Not connected',
};

function systemName(slug: string): string {
  return SYSTEM_NAME[slug] ?? slug.replace(/[_-]+/g, ' ');
}

function attentionTone(attention: ConnectionAttention): 'warning' | 'danger' | 'neutral' {
  if (attention === 'now') return 'danger';
  if (attention === 'soon') return 'warning';
  return 'neutral';
}

export function ConnectionCenter({
  systems,
  isLoading,
  isError,
}: {
  systems: readonly IntegrationSystem[];
  isLoading: boolean;
  isError: boolean;
}) {
  if (isError) {
    return (
      <p className="text-sm text-muted-foreground">
        We could not load what you have connected. Try again in a moment.
      </p>
    );
  }
  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Loading&hellip;</p>;
  }

  const needsAttention = systems.filter((s) => s.needs_attention);

  return (
    <div className="flex flex-col gap-6">
      {needsAttention.length > 0 ? (
        // Said once at the top, because the whole purpose of the screen is that
        // a broken connection is impossible to miss.
        <p className="text-sm font-medium text-foreground">
          {needsAttention.length === 1
            ? '1 connection needs your attention.'
            : `${needsAttention.length} connections need your attention.`}
        </p>
      ) : null}

      <ul className="flex flex-col gap-4">
        {systems.map((system) => (
          <li key={system.integration}>
            <SystemCard system={system} />
          </li>
        ))}
      </ul>
    </div>
  );
}

function SystemCard({ system }: { system: IntegrationSystem }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{systemName(system.integration)}</CardTitle>
        <StatusBadge system={system} />
      </CardHeader>
      <CardBody>
        <div className="flex flex-col gap-3">
          {system.capabilities.length > 0 ? (
            <ul className="flex flex-col gap-1">
              {system.capabilities.map((capability) => (
                <li key={capability} className="text-sm text-muted-foreground">
                  {CAPABILITY_VALUE[capability]}
                </li>
              ))}
            </ul>
          ) : (
            // Honest rather than empty. A system whose only use is waiting on
            // work Signora has not built must not imply it does something.
            <p className="text-sm text-muted-foreground">
              Signora cannot use anything from this yet.
            </p>
          )}

          {system.connections.map((connection) => (
            <ConnectionRow key={connection.id} connection={connection} />
          ))}

          {system.connections.length === 0 && !system.connectable ? (
            <p className="text-xs text-muted-foreground">
              Connecting this is not available yet.
            </p>
          ) : null}
        </div>
      </CardBody>
    </Card>
  );
}

function StatusBadge({ system }: { system: IntegrationSystem }) {
  if (system.needs_attention) return <Badge tone="danger">Action required</Badge>;
  if (system.working) return <Badge tone="success">Ready to use</Badge>;
  if (system.connections.length > 0) return <Badge tone="neutral">Turned off</Badge>;
  return <Badge tone="neutral">Not connected</Badge>;
}

function ConnectionRow({ connection }: { connection: Connection }) {
  const reason = connection.reason ? ATTENTION_REASON[connection.reason] : null;
  return (
    <div className="flex flex-col gap-0.5 border-l-2 border-border pl-3">
      <div className="flex items-baseline justify-between gap-3">
        <span className="text-sm text-foreground">{connection.label}</span>
        <Badge tone={attentionTone(connection.attention)}>
          {CONNECTION_STATE[connection.state] ?? connection.state}
        </Badge>
      </div>
      {reason ? <span className="text-xs text-muted-foreground">{reason}</span> : null}
    </div>
  );
}

export { ATTENTION_REASON, CAPABILITY_VALUE, CONNECTION_STATE, SYSTEM_NAME, systemName };
