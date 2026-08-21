'use client';

import { useState } from 'react';

import { useToast } from '@/components/ui/toast';
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
import {
  ROLE_CAPABILITIES,
  ROLE_OPTIONS,
  onlyOwnersCan,
  type TeamRole,
} from '@/components/team/capabilities';
import {
  EffectivePermissionsPanel,
  RoleChangeDialog,
  RolesAndPermissions,
} from '@/components/team/capability-roles';
import { OrganizationHistory } from '@/components/team/history';
import { NoWorkspace } from '@/components/workspace/no-workspace';
import {
  classifyAddresses,
  explainVerdict,
  sendable,
} from '@/lib/team/invitations';
import { ApiError } from '@/lib/api/client';
import type { Invitation, Membership } from '@/lib/api/types';
import {
  useChangeRole,
  useInviteMember,
  useInvitations,
  useRemoveMember,
  useOrganizationHistory,
  useResendInvitation,
  useTransferOwnership,
  useRevokeInvitation,
  useViewerRole,
  useWorkspaceMembers,
} from '@/lib/query/hooks/team';
import {
  useCapabilityAssignments,
  useCapabilityRoles,
} from '@/lib/query/hooks/capability-roles';
import { useSession } from '@/lib/auth/client';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';
import { ReadingColumn } from '../../reading-column';
import { usePublishBreadcrumb } from '@/components/shell/breadcrumb-trail';

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
  /**
   * 📁 **§05 Breadcrumbs — *"Mandatory below the first level, because most
   * sessions start from a deep link in Slack or email."***
   *
   * ⛔ **Six routes below the first level published nothing**, so the top bar's
   * slot rendered empty on every settings screen and a person arriving from a
   * link had no route back up. ⚡ **The channel already existed and was
   * correct** — [`usePublishBreadcrumb`](../../../../components/shell/breadcrumb-trail.tsx),
   * which `accounts` has used since it shipped — **so this is a consumer
   * adopting the canonical surface, not a new one.**
   *
   * 📁 *"They mirror the data hierarchy, not the click path"*, and the last
   * crumb is the current record and is not a link.
   */
  usePublishBreadcrumb([
    { label: 'Settings', kind: 'link', href: '/settings' },
    { label: 'Team', kind: 'current' },
  ]);

  const { activeWorkspace, isLoading: workspacesLoading } = useWorkspaceContext();
  const workspaceId = activeWorkspace?.id ?? null;
  const { data, isLoading, isError } = useInvitations(workspaceId);
  const invite = useInviteMember(workspaceId);
  const revoke = useRevokeInvitation(workspaceId);
  const resend = useResendInvitation(workspaceId);
  const remove = useRemoveMember(workspaceId);
  const changeRole = useChangeRole(workspaceId);
  const transfer = useTransferOwnership(workspaceId);
  const history = useOrganizationHistory(workspaceId);
  const { data: session } = useSession();
  const viewerId = session?.user.id ?? null;
  const { data: roster, isLoading: rosterLoading, isError: rosterFailed } =
    useWorkspaceMembers(workspaceId);
  const { role: myRole } = useViewerRole(workspaceId, viewerId);
  const { toast } = useToast();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [email, setEmail] = useState('');
  const [role, setRole] = useState<'owner' | 'member'>('member');
  const [leaving, setLeaving] = useState<Membership | null>(null);
  const [handingTo, setHandingTo] = useState<Membership | null>(null);
  const [promoting, setPromoting] = useState<{
    membership: Membership;
    to: 'owner' | 'member';
  } | null>(null);
  /** ⚡ **TASK-1479 ⓸** — the design's *Change role* trade, and its *Effective
   * permissions* panel. Both are about one person, so both hold one. */
  const [narrowing, setNarrowing] = useState<{
    membership: Membership;
    roleId: string | null;
    roleName: string;
  } | null>(null);
  const [inspecting, setInspecting] = useState<Membership | null>(null);
  const { data: capabilityRoles } = useCapabilityRoles(workspaceId);
  const { data: held } = useCapabilityAssignments(workspaceId);

  if (workspacesLoading) return <SkeletonText lines={4} />;
  if (!activeWorkspace) return <NoWorkspace />;

  const people = roster?.items ?? [];
  const owners = people.filter((one) => one.role === 'owner');
  const mine = people.find((one) => one.user_id === viewerId);
  const others = people.filter((one) => one.user_id !== viewerId);
  const invitations = data ?? [];
  const waiting = invitations.filter((one) => one.state === 'pending');
  const settled = invitations.filter((one) => one.state !== 'pending');
  // **Older than a week and still unanswered.** Nobody goes looking for a
  // forgotten invitation — that is what forgotten means — so the page raises it.
  const forgotten = waiting.filter(
    (one) => Date.now() - Date.parse(one.created_at) > 7 * 24 * 60 * 60 * 1000,
  );

  /**
   * ⚡ **[TASK-471](../../../../docs/BACKLOG.md) — every address that can be
   * invited, and only those.**
   *
   * 📁 **The design's §02**: *"j.okafor@northwind.com is already a member. It
   * will be skipped."* ⛔ **Skipped, not rejected** — somebody pasting twenty
   * addresses from a spreadsheet must not have the batch refused because one
   * colleague is already here, **or they will send nineteen invitations one at
   * a time instead.**
   */
  /**
   * ⚠️ **Only the addresses the platform actually knows.** 📁 `member_email` is
   * *"the address this membership was created with, **when one is known**"* —
   * ⛔ **`null` for a founder, and for anybody added by identifier before
   * invitations existed.**
   *
   * ⚡ **So a member with no recorded address cannot be detected here, and the
   * invitation goes out** — ✅ **which is correct: the server is the authority
   * and will refuse it.** ⛔ **Claiming to have checked what was never on the
   * wire would be the worse failure**, because somebody would trust the
   * absence of a warning.
   */
  const classified = classifyAddresses(
    email,
    people.map((one) => one.member_email).filter((one): one is string => one !== null),
    waiting.map((one) => one.invited_email),
  );
  const toInvite = sendable(classified);

  const send = () => {
    // ⛔ **One request per address, because the contract takes one.** ⚡ The
    // batching is the customer's, not the API's, and inventing a bulk endpoint
    // here would be this row designing `workspace_tenancy`'s contract.
    invite.mutate(
      { email: toInvite[0] ?? '', role },
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
    <ReadingColumn>
      <header className="flex flex-col gap-3 phone:flex-row phone:items-start phone:justify-between phone:gap-4">
        <div>
          <h1 className="text-title text-content">Your team</h1>
          {/* **The answer to *is this right?*, before any row.** How many
              people, and how many can administer Signora — the second is what
              makes the last-owner refusal comprehensible before anybody meets
              it. */}
          <p className="mt-1 text-sm text-content-muted">
            {rosterLoading
              ? 'Everyone who can see this organization\u2019s accounts.'
              : `${countWord(people.length, 'person', 'people')} · ${
                  owners.length === 1
                    ? '1 can administer Signora'
                    : `${owners.length} can administer Signora`
                }`}
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
          <CardTitle>People</CardTitle>
        </CardHeader>
        <CardBody className="flex flex-col gap-4">
          {/* **Where a control is absent, say who has it.** A member reading
              this page sees roles and no way to change them; without this they
              cannot tell whether the feature exists, is broken, or is not
              theirs. Naming who *can* is a fact they can act on — 403 is not. */}
          {myRole === 'member' ? (
            <p className="text-sm text-content-muted">
              {onlyOwnersCan('invite colleagues, remove them, or change what they can do')}
            </p>
          ) : null}
          {rosterLoading ? (
            <SkeletonText lines={3} />
          ) : rosterFailed ? (
            <p className="text-sm text-content-muted">
              The people in this organization could not be loaded. Nothing has
              changed — reload to try again.
            </p>
          ) : (
            <Table>
              <THead>
                <TR>
                  <TH pin>Person</TH>
                  <TH>Role</TH>
                  {/* ⚡ **TASK-1479 ⓸** — a second, narrower fact, and it is a
                      separate column because it is a separate question: *Role*
                      says whether they administer this organization, this says
                      whether anything has been narrowed on top of it. */}
                  <TH>Limited to</TH>
                  <TH>{''}</TH>
                </TR>
              </THead>
              <TBody>
                {people.map((one) => (
                  <TR key={one.id}>
                    <TD pin>
                      {nameOf(one, viewerId)}
                      {one.user_id === viewerId ? (
                        <span className="ml-2 text-xs text-content-subtle">You</span>
                      ) : null}
                    </TD>
                    <TD>
                      {/* **The role is the control**, rather than a menu item
                          beside a label. An owner reading the roster to decide
                          whether somebody should be an administrator is
                          already looking at this column. */}
                      {myRole === 'owner' ? (
                        <Select
                          label={`What ${nameOf(one, viewerId)} can do`}
                          labelHidden
                          value={one.role}
                          disabled={changeRole.isPending}
                          onChange={(event) =>
                            setPromoting({
                              membership: one,
                              to: event.target.value as TeamRole,
                            })
                          }
                          options={ROLE_OPTIONS}
                        />
                      ) : (
                        <span className="text-content-muted">{ROLE_CAPABILITIES[one.role].summary}</span>
                      )}
                    </TD>
                    <TD>
                      {/* 🔴 **What they are narrowed to, and it is the fact
                          the Role column CANNOT carry.** ⛔ Rendering `Member`
                          for somebody who effectively authorizes as `Analyst`
                          would be a false claim on the screen — the class this
                          repository keeps finding. */}
                      {myRole === 'owner' && (capabilityRoles?.roles.length ?? 0) > 0 ? (
                        <Select
                          label={`What ${nameOf(one, viewerId)} can be limited to`}
                          labelHidden
                          value={
                            (capabilityRoles?.roles ?? []).find(
                              (role) => role.name === held?.assignments[one.user_id],
                            )?.role_id ?? ''
                          }
                          onChange={(event) => {
                            const roleId = event.target.value === '' ? null : event.target.value;
                            setNarrowing({
                              membership: one,
                              roleId,
                              roleName:
                                (capabilityRoles?.roles ?? []).find(
                                  (role) => role.role_id === roleId,
                                )?.name ?? UNNARROWED,
                            });
                          }}
                          options={[
                            // ⛔ **`''` is *change back*** — the same
                            // affordance the request calls `role_id: null`.
                            { value: '', label: UNNARROWED },
                            ...(capabilityRoles?.roles ?? []).map((role) => ({
                              value: role.role_id,
                              label: role.name,
                            })),
                          ]}
                        />
                      ) : (
                        <span className="text-content-muted">
                          {held?.assignments[one.user_id] ?? UNNARROWED}
                        </span>
                      )}
                      {/* 🔴 **In this cell rather than a column of its own, and
                          the headed review is why.** ⛔ A fifth column pushed
                          *Effective permissions* and *Remove* off the card —
                          **reachable only by scrolling sideways, which is the
                          unreachable class arriving through layout.**
                          ⚡ **It belongs here anyway**: *Limited to* and *what
                          that actually means* are one subject, and a customer
                          asks the second immediately after reading the first.
                          ✅ **Offered to everybody, because a member may read
                          it** — somebody who cannot see why a control is
                          missing has no way to find out who to ask. */}
                      <button
                        type="button"
                        onClick={() => setInspecting(one)}
                        /* ♿ 📁 `2.5.8` — this measured `130 × 18`, fifty times
                           on one screen. ⛔ **`block` on a text link gives it the
                           line box's height and nothing more.** ⚡ `min-h-6` is
                           the floor as a token; the treatment stays a link,
                           which is what the design draws here. */
                        className="mt-1 inline-flex min-h-6 items-center rounded text-xs text-content-subtle underline underline-offset-2 hover:text-content coarse:min-h-11"
                      >
                        See what they can do
                      </button>
                    </TD>
                    <TD>
                      <div className="flex flex-wrap gap-2">
                        {/* **Absent, never disabled**, and absent for two
                            different reasons: a member is not offered a control
                            the server would refuse, and nobody is offered one
                            that removes themselves — leaving is a different
                            operation, and it is blocked on C-207. */}
                        {myRole === 'owner' && one.user_id !== viewerId ? (
                          <Button
                            variant="secondary"
                            size="sm"
                            loading={remove.isPending}
                            onClick={() => setLeaving(one)}
                          >
                            Remove
                          </Button>
                        ) : null}
                      </div>
                    </TD>
                  </TR>
                ))}
              </TBody>
            </Table>
          )}
        </CardBody>
      </Card>

      {/* ⚡ **TASK-1479 ⓸ — the design's *Roles & permissions*, next to the
          people it applies to.** 📁 The design's Settings screen puts it
          directly under *Users*, and putting it on its own route would need a
          card on `/settings` as well (CX-01) for a section nobody would look
          for separately. */}
      <RolesAndPermissions workspaceId={workspaceId} canAdminister={myRole === 'owner'} />

      {/* **Last, because it answers a question asked after the others.** An
          administrator arrives to see who is here or to change something; they
          come to the history when something already looks wrong. */}
      <Card>
        <CardHeader>
          <CardTitle>What has happened</CardTitle>
        </CardHeader>
        <CardBody>
          <OrganizationHistory
            // 🔴 B-420 — this was `history.data ?? []`, and `history.data`
            // was the ENVELOPE. The hook declares `CursorPage<HistoryEntry>`
            // now, so the compiler catches at this line what the wire was
            // doing silently.
            entries={history.data?.items ?? []}
            isLoading={history.isLoading}
            isError={history.isError}
          />
        </CardBody>
      </Card>

      {/* **At the foot, away from the list.** An administrator scanning names
          should not be one mis-click from handing over the organization —
          danger separated by scope rather than hidden behind a confirmation. */}
      {myRole === 'owner' && mine !== undefined && others.length > 0 ? (
        <div className="flex flex-col gap-2 rounded border border-border px-4 py-3">
          <h2 className="text-sm font-medium text-content">Hand over this organization</h2>
          <p className="text-sm text-content-muted">
            Make somebody else the owner and step back to working accounts. It happens
            as one change — there is never a moment when both of you are owners.
          </p>
          <div className="mt-1 flex flex-wrap gap-2">
            {others.map((one) => (
              <Button
                key={one.id}
                variant="secondary"
                size="sm"
                onClick={() => setHandingTo(one)}
              >
                Hand over to {nameOf(one, viewerId)}
              </Button>
            ))}
          </div>
        </div>
      ) : null}

      {/* **The explanation lives where the decision is made**, closed by
          default. An owner choosing between two roles is the one person who
          needs it, and a permanently expanded list of nine sentences would be
          the clutter a matrix was avoided to prevent. */}
      <details className="rounded border border-border px-4 py-3">
        <summary className="cursor-pointer text-sm font-medium text-content">
          What each role can do
        </summary>
        <div className="mt-3 flex flex-col gap-4">
          {(['owner', 'member'] as const).map((role) => (
            <div key={role} className="flex flex-col gap-1.5">
              <h3 className="text-sm font-medium text-content">
                {ROLE_CAPABILITIES[role].summary}
              </h3>
              <ul className="flex list-disc flex-col gap-1 pl-5 text-sm text-content-muted">
                {ROLE_CAPABILITIES[role].can.map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
              {ROLE_CAPABILITIES[role].cannot.length > 0 ? (
                <ul className="flex list-disc flex-col gap-1 pl-5 text-sm text-content-subtle">
                  {ROLE_CAPABILITIES[role].cannot.map((line) => (
                    <li key={line}>Cannot {line.charAt(0).toLowerCase() + line.slice(1)}</li>
                  ))}
                </ul>
              ) : null}
            </div>
          ))}
        </div>
      </details>

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
                  <TH pin>Email</TH>
                  <TH>Role</TH>
                  <TH>Status</TH>
                  <TH>{''}</TH>
                </TR>
              </THead>
              <TBody>
                {[...waiting, ...settled].map((one) => (
                  <TR key={one.id}>
                    <TD pin>{one.invited_email}</TD>
                    <TD className="text-content-muted">{ROLE_CAPABILITIES[one.role].summary}</TD>
                    <TD>
                      <Badge tone={STATE_TONE[one.state]}>{STATE_WORDS[one.state]}</Badge>
                    </TD>
                    <TD>
                      {one.state === 'pending' ? (
                        // **Send again before Withdraw.** The banner above
                        // offers both, and an administrator chasing a
                        // forgotten invitation reaches for the recoverable one
                        // first. Withdrawing is the deliberate second choice.
                        <div className="flex flex-wrap gap-2">
                          <Button
                            variant="secondary"
                            size="sm"
                            loading={resend.isPending}
                            onClick={() =>
                              resend.mutate(one.id, {
                                onSuccess: () =>
                                  toast({
                                    tone: 'success',
                                    message: `Sent again to ${one.invited_email}`,
                                  }),
                              })
                            }
                          >
                            Send again
                          </Button>
                          <Button
                            variant="secondary"
                            size="sm"
                            loading={revoke.isPending}
                            onClick={() => revoke.mutate(one.id)}
                          >
                            Withdraw
                          </Button>
                        </div>
                      ) : null}
                    </TD>
                  </TR>
                ))}
              </TBody>
            </Table>
          )}
        </CardBody>
      </Card>

      <RoleChangeDialog
        workspaceId={workspaceId}
        open={narrowing !== null}
        onClose={() => setNarrowing(null)}
        person={narrowing ? inASentence(narrowing.membership, viewerId) : ''}
        userId={narrowing?.membership.user_id ?? ''}
        roleId={narrowing?.roleId ?? null}
        roleName={narrowing?.roleName ?? UNNARROWED}
      />

      <Dialog
        open={inspecting !== null}
        onClose={() => setInspecting(null)}
        title={
          inspecting
            ? `What ${inASentence(inspecting, viewerId)} can actually do`
            : 'Effective permissions'
        }
        // 📁 **ADR-0410 §3 — computed, never stored.** ⚡ Every line was asked
        // of the same enforcer that decides this person's requests, so what the
        // dialog says and what the server does cannot disagree.
        description="Worked out from what the server would actually allow, just now."
        footer={
          <Button variant="secondary" onClick={() => setInspecting(null)}>
            Close
          </Button>
        }
      >
        {inspecting ? (
          <EffectivePermissionsPanel
            workspaceId={workspaceId}
            userId={inspecting.user_id}
            membershipRole={inspecting.role === 'owner' ? 'an owner' : 'a member'}
          />
        ) : null}
      </Dialog>

      <Dialog
        open={handingTo !== null}
        onClose={() => setHandingTo(null)}
        title="Hand over this organization"
        // **The gain, then the loss, then the thing they cannot undo alone.**
        // Three sentences in the order somebody needs them.
        description={
          handingTo
            ? `${nameOf(handingTo, viewerId)} will be able to invite people, remove them, and change this organization\u2019s settings. You will keep working accounts and will no longer be able to. Only they can hand it back.`
            : ''
        }
        footer={
          <>
            <Button variant="secondary" onClick={() => setHandingTo(null)}>
              Cancel
            </Button>
            <Button
              loading={transfer.isPending}
              onClick={() => {
                if (!handingTo || !mine) return;
                transfer.mutate(
                  { fromMembershipId: mine.id, toMembershipId: handingTo.id },
                  {
                    onSuccess: () => {
                      setHandingTo(null);
                      toast({ tone: 'success', message: 'This organization has a new owner' });
                    },
                    onError: (error) => {
                      setHandingTo(null);
                      toast({
                        tone: 'error',
                        message:
                          error instanceof ApiError
                            ? error.message
                            : 'Could not hand over the organization.',
                      });
                    },
                  },
                );
              }}
            >
              Hand over
            </Button>
          </>
        }
      />

      <Dialog
        open={promoting !== null}
        onClose={() => setPromoting(null)}
        title={
          promoting?.to === 'owner' ? 'Let them administer Signora' : 'Remove administration'
        }
        // **A gain, then a loss, in that order** — and the loss sentence
        // appears only when it is true.
        description={
          promoting
            ? promoting.to === 'owner'
              ? `${nameOf(promoting.membership, viewerId)} will be able to invite people, remove them, and change this organization\u2019s settings.`
              : `${nameOf(promoting.membership, viewerId)} will keep working accounts, and will no longer be able to invite people or change settings.${
                  promoting.membership.user_id === viewerId
                    ? ' That includes you — you will not be able to undo this yourself.'
                    : ''
                }`
            : ''
        }
        footer={
          <>
            <Button variant="secondary" onClick={() => setPromoting(null)}>
              Cancel
            </Button>
            <Button
              loading={changeRole.isPending}
              onClick={() => {
                if (!promoting) return;
                changeRole.mutate(
                  { membershipId: promoting.membership.id, role: promoting.to },
                  {
                    onSuccess: () => {
                      setPromoting(null);
                      toast({ tone: 'success', message: 'Their role has changed' });
                    },
                    onError: (error) => {
                      setPromoting(null);
                      toast({
                        tone: 'error',
                        message:
                          error instanceof ApiError
                            ? error.message
                            : 'Could not change their role.',
                      });
                    },
                  },
                );
              }}
            >
              {promoting?.to === 'owner' ? 'Let them administer' : 'Change role'}
            </Button>
          </>
        }
      />

      <Dialog
        open={leaving !== null}
        onClose={() => setLeaving(null)}
        title="Remove from this organization"
        // Names the person and the consequence. Never "are you sure" — a
        // question the customer has no way to answer.
        description={
          leaving
            ? `${nameOf(leaving, viewerId)} will lose access to this organization\u2019s accounts, evidence and decisions. What they have already decided stays on the record.`
            : ''
        }
        footer={
          <>
            <Button variant="secondary" onClick={() => setLeaving(null)}>
              Cancel
            </Button>
            <Button
              onClick={() => {
                if (!leaving) return;
                remove.mutate(
                  { membershipId: leaving.id },
                  {
                    onSuccess: () => {
                      setLeaving(null);
                      toast({ tone: 'success', message: 'Removed from this organization' });
                    },
                    onError: (error) => {
                      setLeaving(null);
                      toast({
                        tone: 'error',
                        message:
                          error instanceof ApiError
                            ? error.message
                            : 'Could not remove them.',
                      });
                    },
                  },
                );
              }}
              loading={remove.isPending}
            >
              Remove
            </Button>
          </>
        }
      />

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
            <Button onClick={send} loading={invite.isPending} disabled={toInvite.length === 0}>
              {/* 📁 The design counts what will actually be sent — *"Send 3
                  invitations"* — ⛔ **not how many were typed.** */}
              {toInvite.length > 1 ? `Send ${toInvite.length} invitations` : 'Send invitation'}
            </Button>
          </>
        }
      >
        <div className="flex flex-col gap-3">
          <Input
            label="Their email addresses"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="colleague@yourcompany.com, another@yourcompany.com"
            autoFocus
          />
          {/**
            * ⚡ **The verdicts, BEFORE Send** — 📁 the design puts them under the
            * input rather than in a toast afterwards, **so somebody knows what
            * will happen rather than reading about it once it has.**
            *
            * ⛔ **Nothing is said about an ordinary address.** A line under every
            * one of twenty turns the list into a wall nobody reads.
            */}
          {classified.some((entry) => entry.verdict !== 'invite') ? (
            <ul className="flex flex-col gap-1 text-sm text-content-muted">
              {classified.map((entry) => {
                const line = explainVerdict(entry);
                return line === null ? null : <li key={entry.address}>{line}</li>;
              })}
            </ul>
          ) : null}
          <Select
            label="What they can do"
            value={role}
            onChange={(event) => setRole(event.target.value as TeamRole)}
            options={ROLE_OPTIONS}
          />
          {/* **The same sentences, at the moment the choice is made.** An
              administrator inviting somebody as an owner should not have to
              open a disclosure elsewhere to learn what that grants. */}
          <ul className="flex list-disc flex-col gap-1 pl-5 text-sm text-content-muted">
            {ROLE_CAPABILITIES[role].can.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        </div>
      </Dialog>
    </ReadingColumn>
  );
}

/**
 * Who somebody is, in the only terms the product can honestly use.
 *
 * The address a membership was created with, when one is known. **Otherwise
 * *"Somebody here"*** — the wording D23 established for exactly this, and the
 * reason a UUID never reaches the screen.
 */
function nameOf(membership: Membership, viewerId: string | null): string {
  if (membership.member_email) return membership.member_email;
  return membership.user_id === viewerId ? 'You' : 'Somebody here';
}

function countWord(n: number, one: string, many: string): string {
  return `${n} ${n === 1 ? one : many}`;
}

/**
 * ⚡ **What holding no capability role means, under the *Limited to* heading**
 * — [TASK-1479](../../../../docs/BACKLOG.md) ⓸.
 *
 * ⛔ **Not *"—"* and not a blank.** 📁 The state is the ordinary one — nobody
 * holds a capability role until somebody assigns one — and **rendering the
 * common case as a blank would make every colleague look misconfigured.**
 * ⚡ ***"Limited to: Nothing"* is a real answer to the column's question**,
 * which an empty cell is not.
 *
 * ⚠️ **It read *"Everything their role allows"* until the headed review.** 🔴
 * **Five of those, one per row, pushed the actions column off the card** —
 * *Effective permissions* and *Remove* were reachable only by horizontal
 * scrolling, **which is the unreachable class arriving through layout rather
 * than through wiring.**
 */
const UNNARROWED = 'Nothing';

/**
 * What to call somebody **inside a sentence**.
 *
 * ⛔ **`nameOf` returns *"You"*, capitalised, because it starts a table cell**
 * — and the headed review showed the cost: *"What **You** can actually do"* and
 * *"The companies **You** owns stay theirs."* ⚡ **Two different jobs, and one
 * of them needs a lower-case subject pronoun.**
 */
function inASentence(membership: Membership, viewerId: string | null): string {
  return membership.user_id === viewerId ? 'you' : nameOf(membership, viewerId);
}


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
