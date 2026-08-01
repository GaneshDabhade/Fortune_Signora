'use client';

import { Pencil, Plus, Trash2 } from 'lucide-react';
import { useState } from 'react';

import { formatDay } from '@/components/intelligence/dates';
import { Button, Dialog, EmptyState, Input } from '@/components/ui';
import { ApiError } from '@/lib/api/client';
import type { Product, ProductCatalog } from '@/lib/api/types';
import { usePublishProductCatalog } from '@/lib/query/hooks/commercial';

/**
 * What this workspace sells.
 *
 * **The first screen in Signora where a customer tells the product
 * something.** Every other surface reports what the pipeline computed or
 * records a decision about it; this one stores a sentence somebody typed, and
 * it is the input the ten-stage pipeline has never had.
 *
 * ### Why every change saves immediately
 *
 * The catalog is versioned as a whole, so a *Save* button would collect
 * several edits into one version and lose the sequence. Saving on each change
 * makes the version history a record of what actually happened — and removes
 * the unsaved-work state, which is the one thing a settings screen must never
 * have when somebody navigates away.
 *
 * ### Why a refusal is shown rather than resolved
 *
 * If a colleague saved first, the server refuses on version. **The screen
 * says so and stops**, because the alternative is silently overwriting work
 * this reader has not seen. It is the same discipline as the workflow
 * dialog's refusal, applied to configuration.
 */
export function ProductCatalogEditor({
  catalog,
  workspaceId,
}: {
  catalog: ProductCatalog;
  workspaceId: string | null;
}) {
  const [editing, setEditing] = useState<Product | 'new' | null>(null);
  const publish = usePublishProductCatalog(workspaceId);

  const save = (products: Product[]) =>
    publish.mutate(
      { expected_version: catalog.version, products },
      { onSuccess: () => setEditing(null) },
    );

  const upsert = (product: Product) =>
    save(
      catalog.products.some((existing) => existing.id === product.id)
        ? catalog.products.map((existing) =>
            existing.id === product.id ? product : existing,
          )
        : [...catalog.products, product],
    );

  return (
    <section className="flex flex-col gap-4">
      <header className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-sm font-semibold text-content">Products</h2>
          <p className="mt-1 text-sm text-content-muted">
            What your company sells. Everything you tell Signora later — who buys it, who
            decides, which accounts to watch — hangs off this list.
          </p>
        </div>
        <Button size="sm" onClick={() => setEditing('new')}>
          <Plus aria-hidden className="h-4 w-4" /> Add product
        </Button>
      </header>

      {publish.isError ? <Refusal error={publish.error} /> : null}

      {catalog.products.length === 0 ? (
        <EmptyState
          title="No products yet"
          description="Add the first thing your company sells. A name is enough to start."
          action={<Button onClick={() => setEditing('new')}>Add product</Button>}
        />
      ) : (
        <ul className="flex flex-col divide-y divide-border rounded-md border border-border">
          {catalog.products.map((product) => (
            <li
              key={product.id}
              className="flex items-start justify-between gap-4 px-4 py-3"
            >
              <div className="min-w-0">
                <p className="text-sm font-medium text-content">{product.name}</p>
                {product.description ? (
                  <p className="mt-0.5 text-sm leading-6 text-content-muted">
                    {product.description}
                  </p>
                ) : null}
              </div>
              <div className="flex shrink-0 gap-1">
                <Button
                  size="sm"
                  variant="ghost"
                  aria-label={`Edit ${product.name}`}
                  onClick={() => setEditing(product)}
                >
                  <Pencil aria-hidden className="h-4 w-4" />
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  aria-label={`Remove ${product.name}`}
                  disabled={publish.isPending}
                  onClick={() =>
                    save(catalog.products.filter((other) => other.id !== product.id))
                  }
                >
                  <Trash2 aria-hidden className="h-4 w-4" />
                </Button>
              </div>
            </li>
          ))}
        </ul>
      )}

      <Provenance catalog={catalog} />

      <ProductDialog
        product={editing}
        pending={publish.isPending}
        onClose={() => setEditing(null)}
        onSave={upsert}
      />
    </section>
  );
}

/**
 * One product, added or corrected.
 *
 * **The id is minted here, in the browser.** That is what makes saving
 * idempotent — a retried request cannot duplicate a product — and it is the
 * identity everything declared later will cite, so it has to outlive every
 * revision of the list containing it.
 */
function ProductDialog({
  product,
  pending,
  onClose,
  onSave,
}: {
  product: Product | 'new' | null;
  pending: boolean;
  onClose: () => void;
  onSave: (product: Product) => void;
}) {
  const existing = product === 'new' || product === null ? null : product;
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [key, setKey] = useState<string | null>(null);

  // Reset the fields when the dialog opens on a different product, without an
  // effect: deriving from the identity being edited is one source of truth
  // rather than two that have to be kept in step.
  const identity = existing?.id ?? (product === 'new' ? 'new' : null);
  if (identity !== key) {
    setKey(identity);
    setName(existing?.name ?? '');
    setDescription(existing?.description ?? '');
  }

  const submit = () => {
    if (name.trim() === '') return;
    onSave({
      id: existing?.id ?? crypto.randomUUID(),
      name: name.trim(),
      description: description.trim(),
    });
  };

  return (
    <Dialog
      open={product !== null}
      onClose={onClose}
      title={existing ? 'Edit product' : 'Add product'}
      description="Saved as a new version of your catalog, with your name and the date."
      footer={
        <>
          <Button variant="ghost" onClick={onClose} disabled={pending}>
            Cancel
          </Button>
          <Button onClick={submit} disabled={name.trim() === '' || pending}>
            Save
          </Button>
        </>
      }
    >
      <form
        className="flex flex-col gap-3"
        onSubmit={(event) => {
          event.preventDefault();
          submit();
        }}
      >
        <Input
          label="Name"
          value={name}
          onChange={(event) => setName(event.target.value)}
          maxLength={128}
          placeholder="Revenue Cloud"
          autoFocus
        />
        <Input
          label="What it does"
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          maxLength={1024}
          placeholder="Pipeline generation for mid-market revenue teams"
          hint="Optional. Worth writing — it is the context behind everything you declare next."
        />
      </form>
    </Dialog>
  );
}

/**
 * Which version this is, and who declared it.
 *
 * **Version 0 renders nothing.** A workspace that has declared nothing has no
 * author and no moment, and inventing a line for that state would be the
 * screen filling a gap rather than reporting one.
 */
function Provenance({ catalog }: { catalog: ProductCatalog }) {
  if (catalog.version === 0 || catalog.updated_at === null) return null;

  return (
    <p className="text-xs text-content-subtle">
      Version {catalog.version} · last changed {formatDay(catalog.updated_at)}. Every
      version is kept — a change is a new one, never an edit.
    </p>
  );
}

/**
 * What the server said.
 *
 * A version conflict is the case worth showing accurately: a colleague saved
 * first, and the honest answer is to say so rather than to overwrite work
 * this reader has not seen.
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
