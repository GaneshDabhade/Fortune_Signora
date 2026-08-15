'use client';

/**
 * Roles a customer defines, and what holding one would actually mean.
 *
 * 📁 **[TASK-1479](../../../docs/BACKLOG.md) ⓸**, releasing
 * [ADR-0410](../../../docs/architecture/adr/0410-authorization-capability-layer.md)
 * §6 — ✅ **Settings** *Roles & permissions*, *New role*; ✅ **Team
 * Management** *Change to Analyst*, *Effective permissions*, *A Member will be
 * able to*.
 *
 * ## ⛔ Nothing here decides what a role permits
 *
 * 📁 **ADR-0410 §2: *"Do not create a second independent authorization
 * model."*** ⚡ **Every sentence about what somebody may do is rendered from an
 * answer the server computed against the enforcer that decides their
 * requests** — this file translates it into the customer's vocabulary and does
 * not derive it.
 *
 * ⚠️ **Which is why *New role* says the role grants nothing.** 📁 ADR-0410 §5:
 * *"a capability that is not yet granted denies, which is the safe direction."*
 * ⛔ **A dialog implying a working role would be the one lie this screen is
 * placed to avoid** — somebody would define `Analyst`, assign it, and take
 * their colleague's access away believing they had narrowed it.
 */

import { useState } from 'react';

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
  SkeletonText,
} from '@/components/ui';
import { useToast } from '@/components/ui/toast';
import { describeCapabilities } from '@/components/team/capabilities';
import { ApiError } from '@/lib/api/client';
import type { Permission } from '@/lib/api/types';
import {
  trade,
  useAssignCapabilityRole,
  useCapabilityRoles,
  useCreateCapabilityRole,
  useEffectivePermissions,
  useRoleChangePreview,
} from '@/lib/query/hooks/capability-roles';

/**
 * What a set of permissions means, as lines somebody can read.
 *
 * ⛔ **`undescribed` is rendered rather than swallowed.** 📁 The catalog's own
 * rule: **under-reporting what somebody may do is the worst failure this panel
 * has**, because a reader acts on the absence.
 */
function CapabilityLines({
  permissions,
  empty,
}: {
  permissions: readonly Permission[];
  empty: string;
}) {
  const { lines, undescribed } = describeCapabilities(permissions);

  if (lines.length === 0 && undescribed === 0) {
    return <p className="text-sm text-content-muted">{empty}</p>;
  }

  return (
    <ul className="flex flex-col gap-1.5">
      {lines.map((line) => (
        // ⚠️ **`flex-nowrap` and a `shrink-0` level, found by looking at it.**
        // ⛔ With wrapping, three of nine rows pushed *"Can see and change"*
        // onto its own left-aligned line — **where it reads as a tenth item
        // rather than as the level of the row above it.**
        <li key={line.area} className="flex items-baseline justify-between gap-3">
          <span className="text-sm text-content">{line.area}</span>
          <span className="shrink-0 text-xs text-content-subtle">{line.level}</span>
        </li>
      ))}
      {undescribed > 0 ? (
        <li className="text-xs text-content-subtle">
          {undescribed === 1
            ? 'And one more that this screen cannot describe yet.'
            : `And ${undescribed} more that this screen cannot describe yet.`}
        </li>
      ) : null}
    </ul>
  );
}

/**
 * *Effective permissions* — **what this person is actually able to do here.**
 *
 * 📁 **The design: *"Every line names where it comes from."*** ⚡ **Here every
 * line comes from the same place**, so the panel says which role once rather
 * than repeating it on each row — **and *which role* is the fact that changes.**
 */
export function EffectivePermissionsPanel({
  workspaceId,
  userId,
  membershipRole,
}: {
  workspaceId: string | null;
  userId: string;
  /** ⚡ **What they authorize as when they hold no capability role** — the
   * fallback the server describes with `role_name: null`, and the screen must
   * name it rather than leave a blank. */
  membershipRole: string;
}) {
  const { data, isLoading, isError } = useEffectivePermissions(workspaceId, userId);

  if (isLoading) return <SkeletonText lines={3} />;
  // 📁 **P-A** — a failed read must never render as an empty result. ⛔ Here it
  // would read as *"this person may do nothing"*, which is a sentence about
  // somebody with no access at all.
  if (isError || data === undefined) {
    return (
      <p className="text-sm text-content-muted">
        What this person can do could not be loaded. Nothing has changed — reload to
        try again.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      <p className="text-sm text-content-muted">
        {data.role_name === null
          ? `Comes from being ${membershipRole}.`
          : `Comes from the ${data.role_name} role.`}
      </p>
      <CapabilityLines
        permissions={data.permissions}
        empty="Nothing yet. This role has not been granted anything."
      />
    </div>
  );
}

/**
 * *Change role* — **and it is a trade, which is what the dialog has to show.**
 *
 * 📁 **The design's own words: *"Both directions are shown, because a role
 * change is a trade rather than a promotion."*** ⛔ **A dialog listing only
 * what somebody gains would describe a promotion**, and this layer exists
 * precisely so a role can narrow.
 */
export function RoleChangeDialog({
  workspaceId,
  open,
  onClose,
  person,
  userId,
  roleId,
  roleName,
}: {
  workspaceId: string | null;
  open: boolean;
  onClose: () => void;
  /** What to call them, already resolved — this dialog never sees an id. */
  person: string;
  userId: string;
  /** ⛔ **`null` is *change back***, the same convention as the request. */
  roleId: string | null;
  roleName: string;
}) {
  const preview = useRoleChangePreview(workspaceId, userId, roleId, { enabled: open });
  const assign = useAssignCapabilityRole(workspaceId);
  const { toast } = useToast();

  const change = () => {
    assign.mutate(
      { userId, roleId },
      {
        onSuccess: () => {
          onClose();
          toast({
            tone: 'success',
            message:
              roleId === null
                ? `${person} is no longer limited`
                : `${person} is now ${roleName}`,
          });
        },
        onError: (error) => {
          onClose();
          toast({
            tone: 'error',
            message:
              error instanceof ApiError ? error.message : 'Could not change their role.',
          });
        },
      },
    );
  };

  const traded = preview.data ? trade(preview.data) : null;

  return (
    <Dialog
      open={open}
      onClose={onClose}
      // ⛔ **Change-back needs its own words.** The select's value for *no
      // capability role* is *"Nothing"*, and *"Change role — you to Nothing"*
      // reads as removing somebody's access rather than restoring it.
      title={
        roleId === null ? `Remove the limit on ${person}` : `Change role — ${person} to ${roleName}`
      }
      // **When it takes effect, said plainly**, because the design says so and
      // because the alternative — somebody signing out and back in to make a
      // change apply — is a support call.
      description="Changes take effect on their next request, not their next sign-in."
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button
            onClick={change}
            loading={assign.isPending}
            // ⛔ **Not offered until both sides are known.** A customer must
            // never confirm a trade the dialog could not describe.
            disabled={traded === null}
          >
            {roleId === null ? 'Remove the limit' : `Change to ${roleName}`}
          </Button>
        </>
      }
    >
      {preview.isLoading ? (
        <SkeletonText lines={4} />
      ) : preview.isError || traded === null ? (
        // 📁 **P-A's loading cousin** — an unresolved read must not render as an
        // empty one. ⛔ Two empty lists here would read as *"nothing changes"*,
        // which is the most dangerous sentence this dialog could produce.
        <p className="text-sm text-content-muted">
          What this change would do could not be worked out. Nothing has changed — close
          this and try again.
        </p>
      ) : (
        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <h3 className="text-sm font-medium text-content">Gains</h3>
            <CapabilityLines
              permissions={traded.gains}
              empty={`Nothing. ${roleName} has not been granted anything yet.`}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <h3 className="text-sm font-medium text-content">Loses</h3>
            <CapabilityLines permissions={traded.loses} empty="Nothing." />
          </div>
          {/* ⚠️ **Ownership is a different fact from permission, and the design
              separates them** — *"Ownership is unaffected by this change; only
              what she may do with them changes."*
              ⛔ **Deliberately written without a pronoun.** `person` is *"You"*
              for the signed-in reader, and *"The companies You owns stay
              theirs"* is what the headed review actually showed. */}
          <p className="text-sm text-content-muted">
            Ownership is not affected. Only what may be done with those companies
            changes.
          </p>
        </div>
      )}
    </Dialog>
  );
}

/**
 * *Roles & permissions* — **the roles this organization has defined.**
 *
 * ⚡ **A member sees this and cannot change it**, which is deliberate: Team
 * Management shows a colleague's role to everyone, and **defining roles is
 * administration.**
 */
export function RolesAndPermissions({
  workspaceId,
  canAdminister,
}: {
  workspaceId: string | null;
  /** **Presentational only** — Casbin on the server is the decision (§20c).
   * Hiding a control the server would refuse is a courtesy. */
  canAdminister: boolean;
}) {
  const { data, isLoading, isError } = useCapabilityRoles(workspaceId);
  const create = useCreateCapabilityRole(workspaceId);
  const { toast } = useToast();
  const [naming, setNaming] = useState(false);
  const [name, setName] = useState('');

  const roles = data?.roles ?? [];

  const define = () => {
    create.mutate(
      { name },
      {
        onSuccess: (role) => {
          setNaming(false);
          setName('');
          toast({ tone: 'success', message: `${role.name} is now a role here` });
        },
        onError: (error) => {
          toast({
            tone: 'error',
            message: error instanceof ApiError ? error.message : 'Could not create the role.',
          });
        },
      },
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Roles &amp; permissions</CardTitle>
      </CardHeader>
      <CardBody className="flex flex-col gap-4">
        {isLoading ? (
          <SkeletonText lines={3} />
        ) : isError ? (
          // Rendered rather than absent: a section that vanishes on failure
          // reads as a feature the customer does not have (B-006, P-A).
          <p className="text-sm text-content-muted">
            The roles could not be loaded. Nothing has changed — reload to try again.
          </p>
        ) : roles.length === 0 ? (
          <EmptyState
            title="Every colleague is an owner or a member"
            description="That is enough for most organizations. Define a role when somebody needs to do less than a member — a role can narrow what a colleague may do, never widen it."
            action={
              canAdminister ? (
                <Button onClick={() => setNaming(true)}>New role</Button>
              ) : undefined
            }
            className="border-0 bg-transparent"
          />
        ) : (
          <>
            <ul className="flex flex-col gap-2">
              {roles.map((role) => (
                <li
                  key={role.role_id}
                  className="flex flex-wrap items-center justify-between gap-2"
                >
                  <span className="text-sm text-content">{role.name}</span>
                  {/* ⚡ **`holders` is the honest fact a new role has**, and it
                      is what a *remove* control would have to ask first — the
                      database refuses to delete a role somebody holds. */}
                  <Badge tone={role.holders === 0 ? 'warning' : 'neutral'}>
                    {role.holders === 0
                      ? 'Nobody holds this'
                      : role.holders === 1
                        ? '1 person'
                        : `${role.holders} people`}
                  </Badge>
                </li>
              ))}
            </ul>
            {canAdminister ? (
              <div>
                <Button variant="secondary" size="sm" onClick={() => setNaming(true)}>
                  New role
                </Button>
              </div>
            ) : null}
          </>
        )}
      </CardBody>

      <Dialog
        open={naming}
        onClose={() => setNaming(false)}
        title="New role"
        // 🔴 **The sentence that stops this screen lying.** 📁 ADR-0410 §5 — a
        // role grants nothing until somebody grants it something, and that is a
        // reviewed change rather than something this dialog can do.
        description="A new role starts able to do nothing at all. Somebody has to grant it what it should be able to do before anybody holds it — until then, putting a colleague on it takes their access away."
        footer={
          <>
            <Button variant="secondary" onClick={() => setNaming(false)}>
              Cancel
            </Button>
            <Button onClick={define} loading={create.isPending} disabled={name.trim() === ''}>
              Create role
            </Button>
          </>
        }
      >
        <Input
          label="What to call it"
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="Analyst"
          autoFocus
        />
      </Dialog>
    </Card>
  );
}

