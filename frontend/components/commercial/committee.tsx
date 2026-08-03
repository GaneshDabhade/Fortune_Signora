'use client';

import { Pencil, Plus, X } from 'lucide-react';
import { useState } from 'react';

import {
  DroppedWithTheirProduct,
  keptForCatalog,
} from '@/components/commercial/catalog-scope';
import { PART_HINTS, PART_LABELS } from '@/components/commercial/vocabulary';
import { formatDay } from '@/components/intelligence/dates';
import { Badge, Button, Dialog, EmptyState, Input, Select } from '@/components/ui';
import { ApiError } from '@/lib/api/client';
import type {
  BuyingCommittee,
  CommitteePart,
  CommitteeRole,
  Product,
  ProductCatalog,
  ProductCommittee,
} from '@/lib/api/types';
import { useDeclareBuyingCommittee } from '@/lib/query/hooks/commercial';

/**
 * Who has to agree before a company buys.
 *
 * **The third thing a customer tells Signora**, and the one that turns *"this
 * account is worth attention"* into *"and these are the people it has to get
 * through"*.
 *
 * ### It records seats; it evaluates nobody
 *
 * Nothing here scores a role, ranks the committee, or says whether one is
 * missing somebody. Those are conclusions about a real deal, and this screen
 * has no verdict to show and no field that could carry one. The order of the
 * list is the customer's to arrange and means nothing.
 *
 * ### Roles, never people
 *
 * A committee is a template of job titles. Signora holds no individuals here,
 * and the dialog offers nowhere to type one.
 */
export function BuyingCommitteeEditor({
  catalog,
  declaration,
  workspaceId,
}: {
  catalog: ProductCatalog;
  declaration: BuyingCommittee;
  workspaceId: string | null;
}) {
  const [editing, setEditing] = useState<Product | null>(null);
  const declare = useDeclareBuyingCommittee(workspaceId);

  // **The catalog decides what survives** (B-005), as in every editor here.
  const { kept, dropped } = keptForCatalog(
    declaration.committees,
    catalog,
    (committee) => committee.product_id,
  );

  const save = (committees: ProductCommittee[]) =>
    declare.mutate(
      { expected_version: declaration.version, committees },
      { onSuccess: () => setEditing(null) },
    );

  const upsert = (committee: ProductCommittee) =>
    save(
      kept.some((existing) => existing.product_id === committee.product_id)
        ? kept.map((existing) =>
            existing.product_id === committee.product_id ? committee : existing,
          )
        : [...kept, committee],
    );

  const clear = (productId: string) =>
    save(kept.filter((committee) => committee.product_id !== productId));

  return (
    <section className="flex flex-col gap-4">
      <header>
        <h2 className="text-sm font-semibold text-content">Buying committee</h2>
        <p className="mt-1 text-sm text-content-muted">
          The roles that have to agree before a company buys each thing you sell. Job
          titles, not names — and no judgement about how much any of them matters.
        </p>
      </header>

      {declare.isError ? <Refusal error={declare.error} /> : null}

      {catalog.products.length === 0 ? (
        <EmptyState
          title="Add a product first"
          description="A committee decides about something specific, so there is nothing to describe until you have said what you sell."
        />
      ) : (
        <ul className="flex flex-col divide-y divide-border rounded-md border border-border">
          {catalog.products.map((product) => {
            const committee =
              kept.find((candidate) => candidate.product_id === product.id) ?? null;

            return (
              <li key={product.id} className="flex flex-col gap-2 px-4 py-3">
                <div className="flex items-start justify-between gap-4">
                  <p className="min-w-0 text-sm font-medium text-content">
                    {product.name}
                  </p>
                  <div className="flex shrink-0 gap-1">
                    <Button
                      size="sm"
                      variant="ghost"
                      aria-label={`Describe who decides about ${product.name}`}
                      onClick={() => setEditing(product)}
                    >
                      {committee === null ? (
                        <Plus aria-hidden className="h-4 w-4" />
                      ) : (
                        <Pencil aria-hidden className="h-4 w-4" />
                      )}
                    </Button>
                    {committee === null ? null : (
                      <Button
                        size="sm"
                        variant="ghost"
                        aria-label={`Remove the committee for ${product.name}`}
                        disabled={declare.isPending}
                        onClick={() => clear(product.id)}
                      >
                        <X aria-hidden className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
                {committee === null ? (
                  <p className="text-sm text-content-muted">Nobody described yet.</p>
                ) : (
                  <ul className="flex flex-wrap gap-2">
                    {committee.roles.map((role) => (
                      <li key={role.title} className="flex items-center gap-2">
                        <span className="text-sm text-content">{role.title}</span>
                        <Badge tone="neutral">{PART_LABELS[role.part]}</Badge>
                      </li>
                    ))}
                  </ul>
                )}
              </li>
            );
          })}
        </ul>
      )}

      <DroppedWithTheirProduct count={dropped} />

      <Provenance declaration={declaration} />

      <CommitteeDialog
        product={editing}
        committee={kept.find((candidate) => candidate.product_id === editing?.id) ?? null}
        pending={declare.isPending}
        onClose={() => setEditing(null)}
        onSave={upsert}
      />
    </section>
  );
}

/**
 * One product's committee, described or corrected.
 *
 * Roles are added one at a time and the whole committee is saved at once,
 * because the declaration is what gets versioned.
 */
function CommitteeDialog({
  product,
  committee,
  pending,
  onClose,
  onSave,
}: {
  product: Product | null;
  committee: ProductCommittee | null;
  pending: boolean;
  onClose: () => void;
  onSave: (committee: ProductCommittee) => void;
}) {
  const [roles, setRoles] = useState<CommitteeRole[]>([]);
  const [title, setTitle] = useState('');
  const [part, setPart] = useState<CommitteePart>('economic_buyer');
  const [key, setKey] = useState<string | null>(null);

  // Reset when the dialog opens on a different product, without an effect:
  // deriving from the identity being edited is one source of truth rather
  // than two that have to be kept in step.
  if ((product?.id ?? null) !== key) {
    setKey(product?.id ?? null);
    setRoles(committee?.roles ?? []);
    setTitle('');
    setPart('economic_buyer');
  }

  const add = () => {
    const stated = title.trim();
    // The server refuses two roles sharing a title, and silently keeping one
    // copy is what the customer meant either way.
    if (
      stated === '' ||
      roles.some((role) => role.title.toLowerCase() === stated.toLowerCase())
    )
      return setTitle('');
    setRoles([...roles, { title: stated, part }]);
    setTitle('');
  };

  const submit = () => {
    if (product === null || roles.length === 0) return;
    onSave({ product_id: product.id, roles });
  };

  return (
    <Dialog
      open={product !== null}
      onClose={onClose}
      title={product === null ? 'Buying committee' : `Who decides about ${product.name}?`}
      description="Saved as a new version of your committee, with your name and the date."
      footer={
        <>
          <Button variant="ghost" onClick={onClose} disabled={pending}>
            Cancel
          </Button>
          <Button onClick={submit} disabled={roles.length === 0 || pending}>
            Save
          </Button>
        </>
      }
    >
      <div className="flex flex-col gap-4">
        <form
          className="flex flex-col gap-3"
          onSubmit={(event) => {
            event.preventDefault();
            add();
          }}
        >
          <Input
            label="Role"
            value={title}
            maxLength={96}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="VP of Revenue Operations"
            hint="What the job is called. Never a person's name."
          />
          <div className="flex flex-col gap-1.5">
            <Select
              label="Part they play"
              value={part}
              onChange={(event) => setPart(event.target.value as CommitteePart)}
              options={Object.entries(PART_LABELS).map(([value, label]) => ({
                value,
                label,
              }))}
            />
            {/* Rendered beside the control rather than through it: `Select`
                has no hint prop, and bending a shared component to suit one
                caller is the thing §20c exists to prevent. */}
            <p className="text-sm text-content-muted">{PART_HINTS[part]}</p>
          </div>
          <div>
            <Button
              type="submit"
              variant="secondary"
              disabled={title.trim() === ''}
              aria-label="Add role"
            >
              Add role
            </Button>
          </div>
        </form>

        {roles.length === 0 ? (
          <p className="text-sm text-content-muted">
            Add at least one role. A committee with nobody in it says nothing.
          </p>
        ) : (
          <ul className="flex flex-col gap-2">
            {roles.map((role) => (
              <li
                key={role.title}
                className="flex items-center justify-between gap-2 rounded border border-border px-3 py-2"
              >
                <span className="flex items-center gap-2 text-sm text-content">
                  {role.title}
                  <Badge tone="neutral">{PART_LABELS[role.part]}</Badge>
                </span>
                <button
                  type="button"
                  aria-label={`Remove ${role.title}`}
                  className="rounded text-content-subtle transition-colors hover:text-content focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
                  onClick={() =>
                    setRoles(roles.filter((other) => other.title !== role.title))
                  }
                >
                  <X aria-hidden className="h-4 w-4" />
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </Dialog>
  );
}

/**
 * Which version this is, and who declared it.
 *
 * **Version 0 renders nothing** — a company that has declared no committee has
 * no author and no moment, and inventing a line for that state would be the
 * screen filling a gap rather than reporting one.
 */
function Provenance({ declaration }: { declaration: BuyingCommittee }) {
  if (declaration.version === 0 || declaration.updated_at === null) return null;

  return (
    <p className="text-xs text-content-subtle">
      Version {declaration.version} · last changed {formatDay(declaration.updated_at)}.
      Every version is kept — a change is a new one, never an edit.
    </p>
  );
}

/**
 * What the server said.
 *
 * A version conflict is the case worth showing accurately: a colleague saved
 * first, and the honest answer is to say so rather than to overwrite work this
 * reader has not seen.
 */
function Refusal({ error }: { error: unknown }) {
  const message =
    error instanceof ApiError
      ? error.message
      : 'That could not be saved. Nothing has changed — try again.';

  return (
    <p
      role="alert"
      className="rounded border border-warning bg-surface-raised p-3 text-sm text-content"
    >
      {message}
    </p>
  );
}
