'use client';

import { cn } from '@/lib/design/cn';
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
import { usePublishBreadcrumb } from '@/components/shell/breadcrumb-trail';

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
    { label: 'Organization', kind: 'current' },
  ]);

  const { workspaces, activeWorkspace, setActiveWorkspace, isLoading, error } =
    useWorkspaceContext();
  const createWorkspace = useCreateWorkspace();
  const { toast } = useToast();
  const [name, setName] = useState('');

  const submit = () => {
    const trimmed = name.trim();
    if (!trimmed) return;
    createWorkspace.mutate(
      { name: trimmed, slug: suggestSlug(trimmed) },
      {
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
              failure instanceof ApiError
                ? `Reference: ${failure.correlationId}`
                : undefined,
          });
        },
      },
    );
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
        <h1 className="text-title text-content">Organization setup</h1>
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
                {/**
                 * 🔴 **The one field 📁 the design marks EDITABLE was the one
                 * shown bare.**
                 *
                 * 📁 `Settings.dc.html` → `workspaceFields`:
                 * `{ label: 'Workspace name', action: 'Edit', locked: false }`.
                 * ⛔ **There is no `PATCH /workspaces/{id}`** — the API offers
                 * `POST` and `GET` and nothing else, measured against
                 * `openapi.json` — **so the name cannot be changed.**
                 *
                 * ⚠️ **Five fields below this card already say why they are
                 * locked**, each through `LockedField`. **This one said
                 * nothing**, so a reader looking for the rename the design
                 * promises could not tell a missing control from a missing
                 * feature.
                 *
                 * ⚡ **A second `<dd>`, not a `LockedField`.** ⛔ A `<div>`
                 * inside a `<dl>` between `<dt>` and `<dd>` is invalid, and
                 * 📁 `LockedField`'s own comment says the glyph is decorative
                 * and *"the reason below carries the meaning"* — **so the
                 * sentence is the load-bearing half and it is what arrives.**
                 */}
                <dd className="text-sm text-content-subtle">
                  Not yet changeable. Signora can create an organization and read
                  it back, but nothing can rename one — so the name you chose is
                  the name it keeps.
                </dd>
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
            /* ⛔ ***"the change procedure the design specifies"*** — the same
               internal-artefact leak as the brand colour below. ✅ **What a
               customer needs to know is that their links would break and
               nothing yet handles that.** */
            reason="Not yet configurable. Every organization is reached through the application today, and changing that address would break every link anybody has already saved — so it stays fixed until Signora can move them safely."
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
            /**
             * 🔴 ***"The design requires…"* is internal vocabulary in
             * customer copy.**
             *
             * ⛔ **A customer has no design document.** ⚡ Told that *the
             * design* requires something, a reader learns that Signora has an
             * internal artefact and not what the product will do for them —
             * 📁 the same class as [ADR-0034](../../../../../docs/architecture/adr/0034-ubiquitous-language.md)'s
             * *workspace* reaching a screen.
             *
             * ✅ **The constraint is real and worth stating** — a brand colour
             * that fails contrast makes text unreadable — **so it is stated as
             * the promise it is, in the customer's terms.**
             */
            reason="Not yet selectable. A brand colour has to stay readable everywhere Signora draws it, and the check that would prove that does not exist yet — so the palette is fixed for now."
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
              {workspaces.map((candidate) => {
                const current = candidate.id === activeWorkspace?.id;
                return (
                  <li key={candidate.id}>
                    {/**
                      * 🔴 **The current row was announced and INVISIBLE.**
                      * ⛔ `aria-current` was the only thing distinguishing it —
                      * every row carried identical classes — **so a sighted
                      * reader could not tell which organization they were in
                      * from the list that exists to tell them.**
                      *
                      * 📁 **The design draws three markers and this now carries
                      * all three**: `bg: var(--brand-tint)` · `weight: 600` ·
                      * `mark: 'Current'`. ⚡ **Which is the same trio
                      * [`workspace-switcher.tsx`](../../../../components/shell/workspace-switcher.tsx)
                      * already renders** — 📁 `Workspace Chooser` `1.4.1`:
                      * *"the selected row uses the brand tint, a 600-weight
                      * name and the word 'Current'. **Colour alone never marks
                      * selection.**"*
                      *
                      * ⛔ **Not a fourth vocabulary for one fact** — the two
                      * surfaces name the same thing the same way, which is what
                      * stops a customer learning it twice.
                      *
                      * ⚠️ **The design's region, member count and *Suspended*
                      * mark are NOT here**: `Workspace` publishes no region, no
                      * member count and no state. **Three markers that exist
                      * beat six where half are invented.**
                      */}
                    <button
                      type="button"
                      onClick={() => setActiveWorkspace(candidate.id)}
                      aria-current={current ? 'true' : undefined}
                      className={cn(
                        'flex w-full items-center gap-2 rounded border px-3 py-2 text-left text-sm transition-colors',
                        current
                          ? 'border-accent bg-accent-subtle font-semibold text-accent'
                          : 'border-border text-content hover:border-border-strong',
                      )}
                    >
                      <span className="min-w-0 flex-1 truncate">{candidate.name}</span>
                      {current ? (
                        <span className="flex-none text-2xs font-semibold uppercase tracking-wide text-accent">
                          Current
                        </span>
                      ) : null}

                    </button>
                  </li>
                );
              })}
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
