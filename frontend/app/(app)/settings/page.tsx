'use client';

import { suggestSlug } from '@/lib/workspace/slug';
import Link from 'next/link';
import { useState } from 'react';

import { useToast } from '@/components/ui/toast';
import {
  Button,
  Card,
  CardBody,
  CardHeader,
  CardTitle,
  Dialog,
  EmptyState,
  Input,
  LockedField,
  SkeletonText,
  TBody,
  TD,
  TH,
  THead,
  TR,
  Table,
} from '@/components/ui';
import { ApiError } from '@/lib/api/client';
import { useCreateWorkspace } from '@/lib/query/hooks';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';
import { formatDay } from '@/components/intelligence/dates';
import { NoWorkspace } from '@/components/workspace/no-workspace';
import { OrganizationHistory } from '@/components/team/history';
import {
  AbsentSettings,
  ElsewhereSettings,
  SettingsNav,
  SettingsSectionShell,
} from '@/components/settings/sections';
import { useOrganizationHistory } from '@/lib/query/hooks/team';
import { SETTINGS_SECTIONS } from '@/lib/settings/sections';
import { ReadingColumn } from '../reading-column';

/**
 * Organization settings — **and the index of everything an administrator can
 * configure.**
 *
 * The only screen in M1.5 backed by real data, because Workspace &
 * Tenancy is the only shipped module. It doubles as the proof that the
 * shell, query layer, toasts, and dialog compose against a real API rather
 * than a fixture.
 *
 * ### Why every settings page is listed here (CX-01)
 *
 * **`/settings` is the only entrance to `/settings/*`.** Navigation is two
 * entries by design (D38) and neither is a settings child, so a page not
 * listed on this screen is a page nobody can reach.
 *
 * The Connection Center was exactly that: shipped complete — backend, screen,
 * OAuth flow, disconnect — and **linked from nowhere in the product.** The only
 * references to `/settings/connections` in the codebase were the two OAuth
 * redirect helpers *inside the connection flow itself*, so a customer could
 * reach it only by already being in it. **A closed loop with no door.**
 *
 * **The rule this establishes: a settings page ships with its card here, in the
 * same slice.** Not as a follow-up — a page with no entrance is not shipped,
 * whatever its own tests say (`43-customer-experience.md`).
 *
 * **The screen says *organization*; the code says `workspace`, and that is
 * deliberate** (ADR-0034). One concept, two vocabularies: a customer's
 * company on Signora, and the tenancy boundary that isolates it. The
 * translation happens here, at the edge, and never travels inward — the
 * hook, the query key, the API path and the RLS scope all stay `workspace`,
 * because *workspace* is precise about isolation in a way *organization*
 * is not.
 */

/**
 * 📁 **`#workspace` — *"Identity, region and fiscal calendar"*.**
 *
 * ⛔ **One of those three has a producer.** `Workspace` publishes `id`, `name`,
 * `created_at` and `updated_at` — 🔴 **no region, no fiscal calendar, no plan
 * and no seat count.** ⚡ **So the identity is stated and the rest is named as
 * missing**, rather than a select box that changes nothing.
 *
 * ✅ **`LockedField` is the library's own component for exactly this** — a
 * value the product holds and a customer cannot change — and 📁
 * `/settings/organization` already uses it for the same facts.
 */
function WorkspaceIdentity() {
  const { activeWorkspace, isLoading } = useWorkspaceContext();

  if (isLoading) return <SkeletonText lines={3} label="your organization" />;
  if (!activeWorkspace) return <NoWorkspace />;

  return (
    <div className="flex flex-col gap-4">
      <dl className="grid gap-4 phone:grid-cols-2">
        {/* ✅ **`LockedField` for the NAME, because a name is a setting that
            exists and cannot be changed here** — 📁 the component's own
            definition — **and its `reason` is required by the type**, which is
            the discipline: *"a lock with no reason is worse than an absent
            field, because the customer now knows something is missing and not
            why."* */}
        <LockedField
          label="Name"
          value={activeWorkspace.name}
          reason="Renaming an organization is not something Signora can do yet."
        />
        {/* ⛔ **NOT a `LockedField`.** ⚡ **When the organization was created is
            a FACT, not a setting** — nothing would change it even if the
            product could, so a padlock beside it would promise a control that
            was never withheld. */}
        <div>
          <dt className="text-2xs text-content-subtle">Created</dt>
          <dd className="mt-0.5 text-sm text-content">
            {formatDay(activeWorkspace.created_at)}
          </dd>
        </div>
      </dl>
      {/* ⛔ **Named rather than drawn.** 📁 The design's *region* and *fiscal
          calendar* have no field on `Workspace` and no route that would set
          one — **a disabled select would imply the setting exists and is
          merely unavailable to this reader**, which is a different and false
          statement. */}
      <p className="text-sm leading-6 text-content-muted">
        Renaming your organization, and setting its region or fiscal calendar, are not
        things Signora can do yet.
      </p>
      {/* ⚠️ **`/settings/products` appears in NO final design document's
          Settings navigation**, and this link is here because removing the
          index cards took its only entrance — 📁 `infra/reachability.py`
          refuses a built route no screen leads to.

          ⛔ **It is not stale UI to delete**: the catalog it edits is what
          Account 360's *"What you sell"* reads, so removing the route would
          strand a producer-backed capability the design DOES draw, one screen
          over. ⚡ **What the design does not say is where the editor lives.**
          ✅ **Recorded as [C-1546](../../../../docs/LANE_COORDINATION.md)**
          rather than settled by putting it somewhere that looked reasonable. */}
      <div className="flex flex-wrap gap-x-6 gap-y-2">
        {/* ⚡ **The organization's own screen**, which carries the slug, the
            defaults and the settings this product states it cannot change.
            ⛔ **The section above shows the identity; it does not replace that
            screen**, and removing the index cards took its only entrance. */}
        <Link
          href="/settings/organization"
          className="inline-block rounded text-sm font-medium text-accent underline decoration-border underline-offset-4 transition-colors hover:decoration-accent"
        >
          Organization setup
        </Link>
        <Link
          href="/settings/products"
          className="inline-block rounded text-sm font-medium text-accent underline decoration-border underline-offset-4 transition-colors hover:decoration-accent"
        >
          Change what you sell
        </Link>
      </div>
    </div>
  );
}

/**
 * 📁 **`#audit` — the log the page's own subtitle promises.**
 *
 * ✅ **`OrganizationHistory` is reused unchanged**, which is the point: 📁
 * `/settings/audit`'s own docstring says *"a second renderer of the same
 * entries is how two surfaces start disagreeing about what a role change
 * looked like."* ⚡ **One component, two placements** — the same rule the
 * account history follows between the page and the utility panel.
 */
function AuditLog() {
  const { activeWorkspace, isLoading } = useWorkspaceContext();
  const history = useOrganizationHistory(activeWorkspace?.id ?? null);

  return (
    <div className="flex flex-col gap-3">
      <OrganizationHistory
        entries={history.data?.items ?? []}
        isLoading={history.isLoading || isLoading}
        isError={history.isError}
      />
      {/* ⚡ **The section shows the log; the route pages it.** ⛔ **And the link
          is load-bearing rather than decorative**: 📁 `infra/reachability.py`
          refuses a route no screen leads to — *"the Connection Center had two
          inbound links and was still unreachable"* — **and removing the index
          cards took this route's only entrance with them.** */}
      <Link
        href="/settings/audit"
        className="inline-block self-start rounded text-sm font-medium text-accent underline decoration-border underline-offset-4 transition-colors hover:decoration-accent"
      >
        Open the full log
      </Link>
    </div>
  );
}


/**
 * ✅ **The four sections a shipped module can fill**, each composed from what
 * already exists rather than rebuilt here.
 *
 * ⚠️ **Two render inline and two point at their own route, and the split is a
 * document conflict rather than a preference.** 📁 **The Settings design draws
 * every section's detail inline**; 📁 **the Experience Map names
 * `…/settings/team` and `…/settings/integrations` as canonical ROUTES.** ⛔
 * **Both are final documents.** ✅ **Recorded as
 * [C-1545](../../../../docs/LANE_COORDINATION.md)** — and until it is ruled,
 * the route keeps the flow that works: `/settings/team` carries invitations and
 * role changes, `/settings/connections` carries an OAuth round trip, and
 * **moving either inline is a refactor of a working, producer-backed flow that
 * this slice would not be able to verify.**
 */
function SuppliedSettings({ id }: { id: string }) {
  if (id === 'workspace') return <WorkspaceIdentity />;
  if (id === 'audit') return <AuditLog />;
  if (id === 'users') {
    return (
      <ElsewhereSettings href="/settings/team" label="Open your team">
        Everyone who can see this organization&apos;s accounts, and everyone on their way
        in. Invite a colleague, change what somebody may do, or withdraw an invitation.
      </ElsewhereSettings>
    );
  }
  return (
    <ElsewhereSettings href="/settings/connections" label="Open your connections">
      The systems Signora reads from, what each one last brought in, and what to do when
      one stops answering.
    </ElsewhereSettings>
  );
}


export default function SettingsPage() {
  const { workspaces, activeWorkspace, setActiveWorkspace, isLoading } =
    useWorkspaceContext();
  const createWorkspace = useCreateWorkspace();
  const { toast } = useToast();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [name, setName] = useState('');

  const submit = () => {
    createWorkspace.mutate(
      { name: name.trim(), slug: suggestSlug(name) },
      {
        onSuccess: (workspace) => {
          setActiveWorkspace(workspace.id);
          setDialogOpen(false);
          setName('');
          toast({ tone: 'success', message: `Created ${workspace.name}` });
        },
        onError: (error) => {
          // The correlation id is surfaced to the user, not just logged. It
          // is what turns "it didn't work" into a request an engineer can
          // find in seconds (19-api-conventions.md).
          toast({
            tone: 'error',
            message:
              error instanceof ApiError
                ? error.message
                : 'Could not create the organization.',
            detail:
              error instanceof ApiError ? `Reference: ${error.correlationId}` : undefined,
          });
        },
      },
    );
  };

  return (
    <ReadingColumn>
      <header className="flex flex-col gap-3 phone:flex-row phone:items-start phone:justify-between phone:gap-4">
        <div>
          <h1 className="text-title text-content">Settings</h1>
          {/* 🔴 **📁 The design's subtitle, verbatim** — `Design Documents/
              Fortune Signora Settings.html`: ***"Every change is attributed,
              reversible and visible in the audit log"***.

              ⛔ **This read *"The organizations you belong to."*** — ⚡ **which
              describes the LAST card on the page and not the page.** 📁 The
              design's sentence states the property that makes a settings screen
              safe to use, and it is the same promise `#audit` is built on.

              ⚠️ **It is a claim this product can support**: 📁 `/settings/audit`
              renders the log, and every mutation here goes through the audited
              write path. **A subtitle promising attribution on a product with no
              audit log would be the false claim; this one is backed.** */}
          <p className="mt-1 text-sm text-content-muted">
            Every change is attributed, reversible and visible in the audit log.
          </p>
        </div>
        <Button onClick={() => setDialogOpen(true)}>New organization</Button>
      </header>

      {/* 🔴 **The design's eleven sections replace six index cards.**

          📁 `Design Documents/Fortune Signora Settings.html` draws ONE page —
          a four-group navigation over eleven anchored sections, each with the
          detail inline. ⛔ **This screen was an INDEX**: six cards, each a
          title and a sentence and a link out, and **not one of the six appears
          in the design.**

          ⚠️ **The index was not wrong when it was built** — 📁 its own docstring
          records the rule it exists for: *"a settings page ships with its card
          here… a page with no entrance is not shipped."* ⚡ **That rule is
          satisfied better by the design's navigation**, which reaches every
          section including the ones nothing can fill.

          ⛔ **Removed rather than kept beside the new structure**: an index and
          a navigation over the same eleven destinations is two answers to
          *what can I configure*, and 📁 [§2](../../../../CLAUDE.md) says the
          second copy eventually contradicts the first. */}
      <div className="grid gap-6 smalllaptop:grid-cols-[208px_minmax(0,1fr)] smalllaptop:items-start">
        {/* 📁 **Sticky, like the design's own navigation and Account 360's
            rail.** ⛔ **Below the laptop band it becomes an ordinary block
            above the sections**, which is the same regime change
            `OnThisPage` makes and for the same reason: 238px of navigation
            beside 320px of content is not a layout. */}
        <SettingsNav className="smalllaptop:sticky smalllaptop:top-4" />

        <div className="flex flex-col gap-6">
          {SETTINGS_SECTIONS.map((section) => (
            <SettingsSectionShell key={section.id} section={section}>
              {section.supply === 'absent' ? (
                <AbsentSettings section={section} />
              ) : (
                <SuppliedSettings id={section.id} />
              )}
            </SettingsSectionShell>
          ))}
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Organizations</CardTitle>
        </CardHeader>
        <CardBody>
          {isLoading ? (
            <SkeletonText lines={3} />
          ) : workspaces.length === 0 ? (
            <EmptyState
              title="No organizations yet"
              description="An organization is your company on Signora. Create one to get started."
              action={
                <Button onClick={() => setDialogOpen(true)}>New organization</Button>
              }
              className="border-0 bg-transparent"
            />
          ) : (
            <Table>
              <THead>
                <TR>
                  <TH pin>Name</TH>
                  <TH>Created</TH>
                </TR>
              </THead>
              <TBody>
                {workspaces.map((workspace) => (
                  <TR key={workspace.id}>
                    <TD pin>
                      {workspace.name}
                      {workspace.id === activeWorkspace?.id ? (
                        <span className="ml-2 text-xs text-content-subtle">Active</span>
                      ) : null}
                    </TD>
                    <TD className="text-content-muted">
                      {new Date(workspace.created_at).toLocaleDateString()}
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
        title="New organization"
        // **Not "organizations are isolated from each other".** That was the
        // previous copy, and it is a true statement of the tenancy
        // architecture put in front of a salesperson — it answers a question
        // nobody asked and raises one nobody wanted (ADR-0034).
        description="Your company on Signora. Its accounts, evidence and decisions are its own."
        footer={
          <>
            <Button variant="secondary" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={submit}
              loading={createWorkspace.isPending}
              disabled={name.trim() === ''}
            >
              Create
            </Button>
          </>
        }
      >
        <Input
          label="Name"
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="Acme Revenue"
          autoFocus
        />
      </Dialog>
    </ReadingColumn>
  );
}
