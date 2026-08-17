'use client';

import { suggestSlug } from '@/lib/workspace/slug';
import { Building2, Globe, Palette, ShieldCheck } from 'lucide-react';
import { useState } from 'react';

import {
  Button,
  Card,
  CardBody,
  CardHeader,
  CardTitle,
  EmptyState,
  Input,
  LockedField,
} from '@/components/ui';
import { StatedAbsence } from '@/components/feedback/stated-absence';
import { useToast } from '@/components/ui/toast';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';
import { useCreateWorkspace } from '@/lib/query/hooks';
import { ApiError } from '@/lib/api/client';
import { ReadingColumn } from '../../reading-column';

/**
 * Organization setup — the admin landing page.
 *
 * **TASK-468**, against
 * `docs/design-snapshot/screens/Workspace Setup.dc.html`, which enumerates
 * its own ten sections: Overview · Creation · Settings · Branding · URL ·
 * Domains · Switching · Preferences · States · Specs.
 *
 * ### This replaces a text field; it does not refine one
 *
 * Creating an organization was a name input inside a dialog on
 * `settings/page.tsx`. **The approved design is a different screen with five
 * concerns that do not exist anywhere in the platform** — a data region, a
 * URL with a change procedure, DNS domain verification, branding, and
 * deletion. That is not a rename.
 *
 * ### ⚡ Why the absent capabilities are rendered rather than omitted
 *
 * **The design states the rule and its reasoning**: *"Locked is shown, not
 * hidden — region and policy settings render as disabled fields with a
 * padlock and a reason. Removing them from the page makes administrators
 * think the product lost a feature."*
 *
 * ⛔ **And nothing is invented to fill them.** `GET /workspaces/{id}` returns
 * `id`, `name`, `created_at`, `updated_at` and nothing else, so this screen
 * shows exactly those and names the rest as unavailable with the reason.
 * **A region selector populated with plausible regions would be the mock
 * business data [§20c](../../../../CLAUDE.md) forbids**, and worse than
 * absent: a customer would choose one.
 *
 * ### ⛔ The word on the screen is *organization*
 *
 * The design says *workspace* throughout. **[ADR-0034](../../../../docs/architecture/adr/0034-ubiquitous-language.md)
 * forbids that word in anything a customer reads**, and
 * `vocabulary.test.tsx` enforces it. **The design governs what this screen
 * *is*; the ADR governs what it *says*** — recorded as
 * [C-239](../../../../docs/LANE_COORDINATION.md) because four more design
 * screens meet the same word.
 */
export default function OrganizationSetupPage() {
  const { workspaces, activeWorkspace, setActiveWorkspace, isLoading, error } =
    useWorkspaceContext();
  const createWorkspace = useCreateWorkspace();
  const { toast } = useToast();
  const [name, setName] = useState('');

  const submit = () => {
    const trimmed = name.trim();
    if (!trimmed) return;
    createWorkspace.mutate({ name: trimmed, slug: suggestSlug(trimmed) }, {
      onSuccess: (created) => {
        setActiveWorkspace(created.id);
        setName('');
        toast({ tone: 'success', message: `Created ${created.name}` });
      },
      onError: (failure) => {
        toast({
          tone: 'error',
          message:
            failure instanceof ApiError
              ? failure.message
              : 'Could not create the organization.',
          detail:
            failure instanceof ApiError ? `Reference: ${failure.correlationId}` : undefined,
        });
      },
    });
  };

  // §13 and P-A: a failed read must never render as an empty result. This is
  // checked before `isLoading` and before the empty case, because the three
  // are different answers and only one of them means "there is nothing here".
  if (error) {
    // **`StatedAbsence`, not a tenth local copy.** TASK-445 folded nine
    // hand-written failed-read paragraphs into one implementation and
    // `stated-absence.test.tsx` refuses a new one — which is what caught this
    // exact file writing its own.
    return (
      <StatedAbsence
        as="page"
        icon={Building2}
        subject="this organization's settings"
        reassurance="Nothing has been changed, and anything open elsewhere is unaffected"
      />
    );
  }

  return (
    <ReadingColumn>
      <header>
        <h1 className="text-xl font-semibold text-content">Organization setup</h1>
        <p className="mt-1 text-sm text-content-muted">
          Identity and defaults for everyone in this organization.
        </p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Overview</CardTitle>
        </CardHeader>
        <CardBody>
          {isLoading ? (
            <p className="text-sm text-content-muted">Loading…</p>
          ) : activeWorkspace ? (
            <dl className="flex flex-col gap-3">
              <div>
                <dt className="text-sm font-medium text-content">Name</dt>
                <dd className="text-sm text-content-muted">{activeWorkspace.name}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-content">Created</dt>
                <dd className="text-sm text-content-muted">
                  {new Date(activeWorkspace.created_at).toLocaleDateString()}
                </dd>
              </div>
            </dl>
          ) : (
            <EmptyState
              icon={Building2}
              title="No organization selected"
              description="Create one below, or pick one from the switcher to see its settings."
            />
          )}
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Create an organization</CardTitle>
        </CardHeader>
        <CardBody className="flex flex-col gap-4">
          <p className="text-sm text-content-muted">
            Organizations are fully separate: their own members, data, integrations and
            billing line. Nothing is shared between them except your login.
          </p>
          <Input
            id="organization-name"
            label="Organization name"
            hint="2–48 characters. Shown to every member."
            value={name}
            onChange={(event) => setName(event.target.value)}
          />

          {/* The design's other two creation fields. Shown locked rather than
              omitted, and carrying no value, because neither has a platform
              behind it and a populated control would be a promise. */}
          <LockedField
            label="Organization URL"
            reason="Not yet configurable. Every organization is reached through the application today; a custom URL needs the change procedure the design specifies, which is not built."
          />
          <LockedField
            label="Data region"
            reason="Not yet selectable, and permanent once it is. Moving data between regions later means exporting and recreating the organization, so this is deliberately not offered before it can be honoured."
          />
          {/**
            * ⚡ **[TASK-1412](../../../../../docs/BACKLOG.md) — two more of the
            * Settings design's identity fields, shown locked rather than
            * absent.**
            *
            * 📁 **`Fortune Signora Settings.dc.html` lists six `workspaceFields`**
            * and this block carried three of them. ⛔ **The two below have no
            * platform behind them either**, so they arrive the same way the
            * region does: **named, with the reason, and carrying no value.**
            *
            * ⚠️ **Fiscal year is deliberately NOT among them.** It is
            * [C-1415](../../../../../docs/LANE_COORDINATION.md)'s and was
            * removed from this row's scope; adding it here would be re-taking
            * scope Lane C removed.
            */}
          <LockedField
            label="Default currency"
            reason="Not yet selectable. Amounts are shown in the currency each source reports, and no conversion is applied — so nothing here is silently restated in another currency."
          />
          <LockedField
            label="Test organization"
            reason="Not yet available. There is no separate copy of your data to try changes against, so every change here is to the real thing."
          />

          <div>
            <Button onClick={submit} disabled={!name.trim() || createWorkspace.isPending}>
              {createWorkspace.isPending ? 'Creating…' : 'Create organization'}
            </Button>
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Branding</CardTitle>
        </CardHeader>
        <CardBody className="flex flex-col gap-3">
          <p className="text-sm text-content-muted">
            Branding applies to what leaves the product — exported reports, shared links,
            notification emails and the sign-in page. The interface itself is not
            themeable, so a board pack looks like yours without the application drifting
            from the design system.
          </p>
          <LockedField
            label="Logo"
            reason="Not yet uploadable. Exports and emails currently carry no organization logo."
          />
          <LockedField
            label="Brand colour"
            reason="Not yet selectable. The design requires every choice to clear a 4.5:1 contrast check against three surfaces, and that check is not built."
          />
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Domains</CardTitle>
        </CardHeader>
        <CardBody>
          <EmptyState
            icon={Globe}
            title="No domains added"
            description="Everyone joins by invitation only. Verifying a domain would let colleagues join with their work email — that verification is not built yet, so invitations remain the only route."
          />
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Switching</CardTitle>
        </CardHeader>
        <CardBody>
          {workspaces.length > 1 ? (
            <ul className="flex flex-col gap-2">
              {workspaces.map((candidate) => (
                <li key={candidate.id}>
                  <button
                    type="button"
                    onClick={() => setActiveWorkspace(candidate.id)}
                    aria-current={candidate.id === activeWorkspace?.id ? 'true' : undefined}
                    className="w-full rounded border border-border px-3 py-2 text-left text-sm text-content transition-colors hover:border-border-strong focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
                  >
                    {candidate.name}
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState
              icon={Building2}
              title="This is your only organization"
              description="Create another above if you need one that is fully separate — different members, data and integrations."
            />
          )}
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Danger zone</CardTitle>
        </CardHeader>
        <CardBody>
          <LockedField
            label="Delete this organization"
            reason="Not yet available. Deletion has to remove data across every connected system before it can be offered, and offering a button that half-deletes would be worse than not offering one."
          />
        </CardBody>
      </Card>

      <p className="text-sm text-content-subtle">
        <ShieldCheck aria-hidden className="mr-1.5 inline h-3.5 w-3.5" />
        Locked settings are shown rather than hidden, so it is clear what this product
        will do and what it cannot do yet.
        <Palette aria-hidden className="ml-1.5 inline h-3.5 w-3.5" />
      </p>
    </ReadingColumn>
  );
}
