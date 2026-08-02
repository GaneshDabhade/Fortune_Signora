'use client';

import Link from 'next/link';
import { useState } from 'react';

import { useToast } from '@/components/feedback/toast';
import {
  Button,
  Card,
  CardBody,
  CardHeader,
  CardTitle,
  Dialog,
  EmptyState,
  Input,
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
 * The way out of Settings, and the only way into two of them.
 *
 * **A shared shape rather than a shared component**, because it is one page's
 * repetition and `components/ui` is frozen (§20c) — *"add to the library rather
 * than around it"* applies to a component the library would benefit from, and a
 * settings-page link is not one. If a third page needs it, it earns promotion.
 */
function SettingsLink({ href, children }: { href: string; children: string }) {
  return (
    <Link
      href={href}
      className="mt-3 inline-block rounded text-sm font-medium text-accent underline decoration-border underline-offset-4 transition-colors hover:decoration-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
    >
      {children}
    </Link>
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
    createWorkspace.mutate(name.trim(), {
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
    });
  };

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      <header className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold text-content">Settings</h1>
          <p className="mt-1 text-sm text-content-muted">
            The organizations you belong to.
          </p>
        </div>
        <Button onClick={() => setDialogOpen(true)}>New organization</Button>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Your business</CardTitle>
        </CardHeader>
        <CardBody>
          <p className="text-sm text-content-muted">
            What your company sells, and — as it arrives — who buys it and who decides.
            Signora needs this before it can tell you anything useful about anyone
            else&apos;s company.
          </p>
          <SettingsLink href="/settings/products">Products</SettingsLink>
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Your team</CardTitle>
        </CardHeader>
        <CardBody>
          <p className="text-sm text-content-muted">
            Everyone who can see this organization&apos;s accounts, and everyone on
            their way in. Invite a colleague, or withdraw an invitation.
          </p>
          <SettingsLink href="/settings/team">Your team</SettingsLink>
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Connections</CardTitle>
        </CardHeader>
        <CardBody>
          <p className="text-sm text-content-muted">
            The systems Signora reads from to work out which accounts deserve your
            attention. Connect the ones your team already uses.
          </p>
          <SettingsLink href="/settings/connections">Connections</SettingsLink>
        </CardBody>
      </Card>

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
                  <TH>Name</TH>
                  <TH>Created</TH>
                </TR>
              </THead>
              <TBody>
                {workspaces.map((workspace) => (
                  <TR key={workspace.id}>
                    <TD>
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
    </div>
  );
}
