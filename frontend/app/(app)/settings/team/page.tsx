'use client';

import { useState } from 'react';

import { useToast } from '@/components/feedback/toast';
import {
  Badge,
  Button,
  Card,
  CardBody,
  CardHeader,
  CardTitle,
  Dialog,
  EmptyState,
  Input,
  Select,
  SkeletonText,
  TBody,
  TD,
  TH,
  THead,
  TR,
  Table,
} from '@/components/ui';
import { NoWorkspace } from '@/components/workspace/no-workspace';
import { ApiError } from '@/lib/api/client';
import type { Invitation } from '@/lib/api/types';
import {
  useInviteMember,
  useInvitations,
  useRevokeInvitation,
} from '@/lib/query/hooks/team';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';

/**
 * Your team — **an administrator's workspace, not a table of users.**
 *
 * The difference is that a workspace answers questions and a table answers
 * lookups. An administrator arrives with one of two questions today: *is this
 * right?* and *did anybody not come?* The page is ordered by those.
 *
 * ### What is deliberately not here yet
 *
 * **The people.** `GET /members` returns `user_id` and `role`, and no address,
 * because none was ever supplied — `create_workspace` mints the founder's
 * membership from a session and `POST /members` takes an identifier. **The
 * column arrives with invitations**, since a membership created by accepting
 * one carries the address the organization typed
 * ([C-203](../../../../docs/LANE_COORDINATION.md)).
 *
 * Rendering UUIDs in the meantime would be a table of identifiers pretending to
 * be a team, so the section is absent rather than wrong — and the header still
 * answers *how many people, and how many can administer Signora*, which is what
 * makes the last-owner rule comprehensible before anybody meets it.
 *
 * **Accepting.** [C-208](../../../../docs/LANE_COORDINATION.md): the person an
 * invitation names is, by definition, not yet in the workspace, and every RLS
 * policy scopes reads to a workspace membership grants. Inviting, listing and
 * revoking are all administrator operations and need none of that.
 */
export default function TeamPage() {
  const { activeWorkspace, isLoading: workspacesLoading } = useWorkspaceContext();
  const workspaceId = activeWorkspace?.id ?? null;
  const { data, isLoading, isError } = useInvitations(workspaceId);
  const invite = useInviteMember(workspaceId);
  const revoke = useRevokeInvitation(workspaceId);
  const { toast } = useToast();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [email, setEmail] = useState('');
  const [role, setRole] = useState<'owner' | 'member'>('member');

  if (workspacesLoading) return <SkeletonText lines={4} />;
  if (!activeWorkspace) return <NoWorkspace />;

  const invitations = data ?? [];
  const waiting = invitations.filter((one) => one.state === 'pending');
  const settled = invitations.filter((one) => one.state !== 'pending');
  // **Older than a week and still unanswered.** Nobody goes looking for a
  // forgotten invitation — that is what forgotten means — so the page raises it.
  const forgotten = waiting.filter(
    (one) => Date.now() - Date.parse(one.created_at) > 7 * 24 * 60 * 60 * 1000,
  );

  const send = () => {
    invite.mutate(
      { email: email.trim(), role },
      {
        onSuccess: (created) => {
          setDialogOpen(false);
          setEmail('');
          setRole('member');
          toast({ tone: 'success', message: `Invitation sent to ${created.invited_email}` });
        },
        onError: (error) => {
          toast({
            tone: 'error',
            message:
              error instanceof ApiError
                ? error.message
                : 'Could not send the invitation.',
            detail: error instanceof ApiError ? `Reference: ${error.correlationId}` : undefined,
          });
        },
      },
    );
  };

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      <header className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold text-content">Your team</h1>
          <p className="mt-1 text-sm text-content-muted">
            Everyone who can see this organization&apos;s accounts, and everyone on
            their way in.
          </p>
        </div>
        <Button onClick={() => setDialogOpen(true)}>Invite a colleague</Button>
      </header>

      {forgotten.length > 0 ? (
        <div className="flex flex-col gap-1 rounded border-l-2 border-warning bg-warning-subtle px-3 py-2.5">
          <p className="text-sm text-content">
            {forgotten.length === 1
              ? 'One invitation was sent over a week ago and has not been accepted.'
              : `${forgotten.length} invitations were sent over a week ago and have not been accepted.`}
          </p>
          <p className="text-sm text-content-muted">
            You can send it again, or withdraw it below.
          </p>
        </div>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>Invited</CardTitle>
        </CardHeader>
        <CardBody>
          {isLoading ? (
            <SkeletonText lines={3} />
          ) : isError ? (
            // Rendered rather than absent: a section that vanishes on failure
            // reads as a feature the customer does not have (B-006).
            <p className="text-sm text-content-muted">
              The invitations could not be loaded. Nothing has changed — reload to
              try again.
            </p>
          ) : invitations.length === 0 ? (
            <EmptyState
              title="Nobody has been invited yet"
              description="Signora is more useful when the people working these accounts can see them. Invite a colleague to get started."
              action={<Button onClick={() => setDialogOpen(true)}>Invite a colleague</Button>}
              className="border-0 bg-transparent"
            />
          ) : (
            <Table>
              <THead>
                <TR>
                  <TH>Email</TH>
                  <TH>Role</TH>
                  <TH>Status</TH>
                  <TH>{''}</TH>
                </TR>
              </THead>
              <TBody>
                {[...waiting, ...settled].map((one) => (
                  <TR key={one.id}>
                    <TD>{one.invited_email}</TD>
                    <TD className="text-content-muted">{ROLE_WORDS[one.role]}</TD>
                    <TD>
                      <Badge tone={STATE_TONE[one.state]}>{STATE_WORDS[one.state]}</Badge>
                    </TD>
                    <TD>
                      {one.state === 'pending' ? (
                        <Button
                          variant="secondary"
                          size="sm"
                          loading={revoke.isPending}
                          onClick={() => revoke.mutate(one.id)}
                        >
                          Withdraw
                        </Button>
                      ) : null}
                    </TD>
                  </TR>
                ))}
              </TBody>
            </Table>
          )}
        </CardBody>
      </Card>

      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        title="Invite a colleague"
        // Says what will happen, in the order it happens. Not "are you sure" —
        // a question the customer has no way to answer.
        description="They will get an email inviting them to join this organization. You can withdraw it any time before they accept."
        footer={
          <>
            <Button variant="secondary" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={send} loading={invite.isPending} disabled={email.trim() === ''}>
              Send invitation
            </Button>
          </>
        }
      >
        <div className="flex flex-col gap-3">
          <Input
            label="Their email address"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="colleague@yourcompany.com"
            autoFocus
          />
          <Select
            label="What they can do"
            value={role}
            onChange={(event) => setRole(event.target.value as 'owner' | 'member')}
            options={ROLE_OPTIONS}
          />
        </div>
      </Dialog>
    </div>
  );
}

/**
 * What each role means, said in full.
 *
 * **Not *Owner* and *Member*.** Those are the words the policy uses; an
 * administrator choosing between them is asking *what will this person be able
 * to do*, and the answer belongs in the control rather than in a tooltip.
 * (Explaining the full permission set is still unsolved — §5 of
 * `46-team-management.md`.)
 */
const ROLE_OPTIONS = [
  { value: 'member', label: 'Work accounts — see everything, decide on accounts' },
  { value: 'owner', label: 'Administer Signora — and everything a member can do' },
] as const;

/** The customer's words for a role, not the enum's (ADR-0034). */
const ROLE_WORDS: Record<Invitation['role'], string> = {
  owner: 'Can administer Signora',
  member: 'Works accounts',
};

/**
 * What became of an offer.
 *
 * **Four words for four states**, and *Withdrawn* rather than *Revoked*
 * because a salesperson withdraws an offer and a system revokes a credential.
 */
const STATE_WORDS: Record<Invitation['state'], string> = {
  pending: 'Waiting',
  accepted: 'Joined',
  revoked: 'Withdrawn',
  expired: 'Expired',
};

const STATE_TONE: Record<Invitation['state'], 'neutral' | 'success' | 'warning'> = {
  pending: 'neutral',
  accepted: 'success',
  revoked: 'neutral',
  expired: 'warning',
};
