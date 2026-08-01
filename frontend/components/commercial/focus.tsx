'use client';

import { useState } from 'react';

import { formatDay } from '@/components/intelligence/dates';
import { Button, EmptyState, Input } from '@/components/ui';
import { ApiError } from '@/lib/api/client';
import type { CommercialFocus, ProductCatalog } from '@/lib/api/types';
import { useDeclareFocus } from '@/lib/query/hooks/commercial';

/**
 * What this company is pushing right now.
 *
 * **The fourth thing a customer tells Signora**, and the one that goes stale
 * fastest. It answers *"what are you working on this quarter?"* — which is why
 * the version line matters more here than anywhere else on the page.
 *
 * ### In focus, or not — never ranked
 *
 * There is no first, second, third. The roadmap calls this capability
 * *business priorities*, and an ordinal is one consumer away from a weight in
 * a score; a seller says *"we're pushing Revenue Cloud"*, not *"Revenue Cloud
 * is priority two"*. The toggles below carry no order and neither does the API.
 *
 * ### No period field, on purpose
 *
 * *"When did we last say this?"* is already answered by the version line. A
 * typed *"Q3 2026"* would be a second version of that fact, free to disagree
 * with the first.
 */
export function CommercialFocusEditor({
  catalog,
  focus,
  workspaceId,
}: {
  catalog: ProductCatalog;
  focus: CommercialFocus;
  workspaceId: string | null;
}) {
  const declare = useDeclareFocus(workspaceId);
  const [objective, setObjective] = useState(focus.objective);
  const [editing, setEditing] = useState(false);

  const save = (products: string[], stated: string) =>
    declare.mutate(
      { expected_version: focus.version, products, objective: stated },
      { onSuccess: () => setEditing(false) },
    );

  const toggle = (productId: string) =>
    save(
      focus.products.includes(productId)
        ? focus.products.filter((other) => other !== productId)
        : [...focus.products, productId],
      focus.objective,
    );

  return (
    <section className="flex flex-col gap-4">
      <header>
        <h2 className="text-sm font-semibold text-content">What you are pushing now</h2>
        <p className="mt-1 text-sm text-content-muted">
          The products you are actively selling this quarter, and what you are trying to
          do. Nothing here is ranked — a product is in focus or it is not.
        </p>
      </header>

      {declare.isError ? <Refusal error={declare.error} /> : null}

      {catalog.products.length === 0 ? (
        <EmptyState
          title="Add a product first"
          description="There is nothing to focus on until you have said what you sell."
        />
      ) : (
        <ul className="flex flex-wrap gap-2">
          {catalog.products.map((product) => {
            const inFocus = focus.products.includes(product.id);

            return (
              <li key={product.id}>
                {/* A toggle button rather than a checkbox: `components/ui` has
                    no checkbox, and adding one to the frozen library for a
                    single caller is what §20c exists to prevent. `aria-pressed`
                    is what makes this a toggle to a screen reader. */}
                <Button
                  size="sm"
                  variant={inFocus ? 'secondary' : 'ghost'}
                  aria-pressed={inFocus}
                  disabled={declare.isPending}
                  onClick={() => toggle(product.id)}
                >
                  {product.name}
                </Button>
              </li>
            );
          })}
        </ul>
      )}

      {editing ? (
        <form
          className="flex flex-col gap-3"
          onSubmit={(event) => {
            event.preventDefault();
            save(focus.products, objective.trim());
          }}
        >
          <Input
            label="What you are trying to do"
            value={objective}
            maxLength={1024}
            onChange={(event) => setObjective(event.target.value)}
            placeholder="Land three health systems before December"
            hint="Your words. Read by a colleague, never by a rule."
            autoFocus
          />
          <div className="flex gap-2">
            <Button type="submit" size="sm" disabled={declare.isPending}>
              Save
            </Button>
            <Button
              type="button"
              size="sm"
              variant="ghost"
              disabled={declare.isPending}
              onClick={() => {
                setObjective(focus.objective);
                setEditing(false);
              }}
            >
              Cancel
            </Button>
          </div>
        </form>
      ) : (
        <div className="flex items-start justify-between gap-4">
          <p className="text-sm leading-6 text-content-muted">
            {focus.objective === ''
              ? 'No objective written yet.'
              : focus.objective}
          </p>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => {
              setObjective(focus.objective);
              setEditing(true);
            }}
          >
            {focus.objective === '' ? 'Add an objective' : 'Edit'}
          </Button>
        </div>
      )}

      <Provenance focus={focus} />
    </section>
  );
}

/**
 * When this was last said, and by whom.
 *
 * **This carries more weight here than on the other three sections**, because
 * a focus is the declaration that goes stale: a customer reading *"last changed
 * in March"* in September knows to revisit it, and there is no period field
 * claiming otherwise.
 */
function Provenance({ focus }: { focus: CommercialFocus }) {
  if (focus.version === 0 || focus.updated_at === null) return null;

  return (
    <p className="text-xs text-content-subtle">
      Version {focus.version} · last changed {formatDay(focus.updated_at)}. Every version
      is kept — a change is a new one, never an edit.
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
