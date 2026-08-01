'use client';

import { Pencil, Plus, X } from 'lucide-react';
import { useState } from 'react';

import { formatDay } from '@/components/intelligence/dates';
import { Button, Dialog, EmptyState, Input } from '@/components/ui';
import { ApiError } from '@/lib/api/client';
import type { IcpDeclaration, Product, ProductCatalog, ProductIcp } from '@/lib/api/types';
import { useDeclareIcp } from '@/lib/query/hooks/commercial';

/**
 * Who buys what this company sells.
 *
 * **The second thing a customer tells Signora, and the one that makes the
 * first useful.** A product on its own says what is for sale; this says who it
 * is for, which is what everything Signora goes looking for is eventually
 * checked against.
 *
 * ### It describes; it never matches
 *
 * Nothing on this screen says whether a real company fits. Comparing an
 * account to a description needs resolved facts about that account, which is
 * built elsewhere and deliberately separate — so this screen has no verdict to
 * show and no field that could carry one.
 *
 * ### In the customer's own words
 *
 * Industries and countries are free text rather than a fixed list. A seller
 * says *"mid-market fintech in the US and UK"*, and offering them a taxonomy
 * to pick from would make them translate their own business into ours before
 * they had told us anything.
 *
 * ### Why every change saves immediately
 *
 * The description is versioned as a whole, so a *Save* button collecting
 * several edits into one version would lose the sequence — and leave unsaved
 * work on a settings screen somebody is about to navigate away from.
 */
export function IcpEditor({
  catalog,
  declaration,
  workspaceId,
}: {
  catalog: ProductCatalog;
  declaration: IcpDeclaration;
  workspaceId: string | null;
}) {
  const [editing, setEditing] = useState<Product | null>(null);
  const declare = useDeclareIcp(workspaceId);

  const save = (profiles: ProductIcp[]) =>
    declare.mutate(
      { expected_version: declaration.version, profiles },
      { onSuccess: () => setEditing(null) },
    );

  const upsert = (profile: ProductIcp) =>
    save(
      declaration.profiles.some((existing) => existing.product_id === profile.product_id)
        ? declaration.profiles.map((existing) =>
            existing.product_id === profile.product_id ? profile : existing,
          )
        : [...declaration.profiles, profile],
    );

  const clear = (productId: string) =>
    save(declaration.profiles.filter((profile) => profile.product_id !== productId));

  return (
    <section className="flex flex-col gap-4">
      <header>
        <h2 className="text-sm font-semibold text-content">Ideal customer</h2>
        <p className="mt-1 text-sm text-content-muted">
          The kind of company that buys each thing you sell — in your words, not ours.
          Signora records what you say here; it does not grade anyone against it.
        </p>
      </header>

      {declare.isError ? <Refusal error={declare.error} /> : null}

      {catalog.products.length === 0 ? (
        <EmptyState
          title="Add a product first"
          description="An ideal customer is the kind of company that buys something specific, so there is nothing to describe until you have said what you sell."
        />
      ) : (
        <ul className="flex flex-col divide-y divide-border rounded-md border border-border">
          {catalog.products.map((product) => {
            const profile =
              declaration.profiles.find(
                (candidate) => candidate.product_id === product.id,
              ) ?? null;

            return (
              <li
                key={product.id}
                className="flex items-start justify-between gap-4 px-4 py-3"
              >
                <div className="min-w-0">
                  <p className="text-sm font-medium text-content">{product.name}</p>
                  <p className="mt-0.5 text-sm leading-6 text-content-muted">
                    {profile === null ? 'Nobody described yet.' : summarise(profile)}
                  </p>
                </div>
                <div className="flex shrink-0 gap-1">
                  <Button
                    size="sm"
                    variant="ghost"
                    aria-label={`Describe who buys ${product.name}`}
                    onClick={() => setEditing(product)}
                  >
                    {profile === null ? (
                      <Plus aria-hidden className="h-4 w-4" />
                    ) : (
                      <Pencil aria-hidden className="h-4 w-4" />
                    )}
                  </Button>
                  {profile === null ? null : (
                    <Button
                      size="sm"
                      variant="ghost"
                      aria-label={`Remove the description for ${product.name}`}
                      disabled={declare.isPending}
                      onClick={() => clear(product.id)}
                    >
                      <X aria-hidden className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      )}

      <Provenance declaration={declaration} />

      <IcpDialog
        product={editing}
        profile={
          declaration.profiles.find(
            (candidate) => candidate.product_id === editing?.id,
          ) ?? null
        }
        pending={declare.isPending}
        onClose={() => setEditing(null)}
        onSave={upsert}
      />
    </section>
  );
}

/**
 * What has been said about one product's buyer, in one line.
 *
 * Deliberately the customer's own words rather than a count. *"3 criteria"*
 * would tell a reader nothing they wanted to know, and the point of the row is
 * recognising your own description at a glance.
 */
function summarise(profile: ProductIcp): string {
  const parts = [
    profile.industries.join(', '),
    profile.countries.join(', '),
    size(profile.employees),
  ].filter((part) => part !== '');

  return parts.join(' · ');
}

function size(employees: ProductIcp['employees']): string {
  if (employees === null) return '';
  const { minimum, maximum } = employees;
  if (minimum !== null && maximum !== null)
    return `${minimum.toLocaleString()}–${maximum.toLocaleString()} people`;
  if (minimum !== null) return `${minimum.toLocaleString()}+ people`;
  if (maximum !== null) return `up to ${maximum.toLocaleString()} people`;
  return '';
}

/**
 * One product's buyer, described or corrected.
 *
 * **Nothing is required except saying something.** A customer who knows only
 * the industry should be able to record the industry and come back; demanding
 * a complete profile up front is how a settings screen ends up empty.
 */
function IcpDialog({
  product,
  profile,
  pending,
  onClose,
  onSave,
}: {
  product: Product | null;
  profile: ProductIcp | null;
  pending: boolean;
  onClose: () => void;
  onSave: (profile: ProductIcp) => void;
}) {
  const [industries, setIndustries] = useState<string[]>([]);
  const [countries, setCountries] = useState<string[]>([]);
  const [minimum, setMinimum] = useState('');
  const [maximum, setMaximum] = useState('');
  const [notes, setNotes] = useState('');
  const [key, setKey] = useState<string | null>(null);

  // Reset when the dialog opens on a different product, without an effect:
  // deriving from the identity being edited is one source of truth rather
  // than two that have to be kept in step.
  if ((product?.id ?? null) !== key) {
    setKey(product?.id ?? null);
    setIndustries(profile?.industries ?? []);
    setCountries(profile?.countries ?? []);
    setMinimum(profile?.employees?.minimum?.toString() ?? '');
    setMaximum(profile?.employees?.maximum?.toString() ?? '');
    setNotes(profile?.notes ?? '');
  }

  const bound = (value: string) => (value.trim() === '' ? null : Number(value));
  const employees =
    bound(minimum) === null && bound(maximum) === null
      ? null
      : { minimum: bound(minimum), maximum: bound(maximum) };
  // The server refuses a description with no criteria, and so does this — but
  // here it is a disabled button rather than an error, because refusing before
  // somebody has typed anything is not news to them.
  const stated =
    industries.length > 0 || countries.length > 0 || employees !== null;

  const submit = () => {
    if (product === null || !stated) return;
    onSave({
      product_id: product.id,
      industries,
      countries,
      employees,
      notes: notes.trim(),
    });
  };

  return (
    <Dialog
      open={product !== null}
      onClose={onClose}
      title={product === null ? 'Ideal customer' : `Who buys ${product.name}?`}
      description="Saved as a new version of your description, with your name and the date."
      footer={
        <>
          <Button variant="ghost" onClick={onClose} disabled={pending}>
            Cancel
          </Button>
          <Button onClick={submit} disabled={!stated || pending}>
            Save
          </Button>
        </>
      }
    >
      <form
        className="flex flex-col gap-4"
        onSubmit={(event) => {
          event.preventDefault();
          submit();
        }}
      >
        <TagField
          label="Industries"
          hint="What kind of business they are. Your words — nothing is matched against a list."
          placeholder="Financial services"
          values={industries}
          onChange={setIndustries}
        />
        <TagField
          label="Countries"
          hint="Where they are."
          placeholder="United Kingdom"
          values={countries}
          onChange={setCountries}
        />
        <div className="grid grid-cols-2 gap-3">
          <Input
            label="Smallest, in people"
            type="number"
            min={0}
            value={minimum}
            onChange={(event) => setMinimum(event.target.value)}
            placeholder="200"
          />
          <Input
            label="Largest, in people"
            type="number"
            min={0}
            value={maximum}
            onChange={(event) => setMaximum(event.target.value)}
            placeholder="2000"
            hint="Leave either side blank for no limit."
          />
        </div>
        <Input
          label="Anything else"
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
          maxLength={1024}
          placeholder="Only where they already run a CRM we integrate with"
          hint="Optional. Read by a colleague, never by a rule."
        />
      </form>
    </Dialog>
  );
}

/**
 * A list somebody types one entry at a time.
 *
 * A business component rather than an addition to the shared library: one
 * screen needs it, and a component added to `ui` for a single caller is one
 * every later caller has to bend (§20c). It moves there when a second screen
 * wants it.
 */
function TagField({
  label,
  hint,
  placeholder,
  values,
  onChange,
}: {
  label: string;
  hint: string;
  placeholder: string;
  values: string[];
  onChange: (values: string[]) => void;
}) {
  const [draft, setDraft] = useState('');

  const add = () => {
    const entry = draft.trim();
    // Case-insensitively already there: the server refuses a duplicate, and
    // silently keeping one copy is what the customer meant either way.
    if (entry === '' || values.some((value) => value.toLowerCase() === entry.toLowerCase()))
      return setDraft('');
    onChange([...values, entry]);
    setDraft('');
  };

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-end gap-2">
        <div className="grow">
          <Input
            label={label}
            hint={hint}
            value={draft}
            maxLength={64}
            placeholder={placeholder}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={(event) => {
              if (event.key !== 'Enter') return;
              // Enter adds an entry; it must not submit the surrounding form,
              // which would save a half-typed description.
              event.preventDefault();
              add();
            }}
          />
        </div>
        <Button
          type="button"
          variant="secondary"
          onClick={add}
          disabled={draft.trim() === ''}
          aria-label={`Add ${label.toLowerCase()}`}
        >
          Add
        </Button>
      </div>
      {values.length === 0 ? null : (
        <ul className="flex flex-wrap gap-2">
          {values.map((value) => (
            <li
              key={value}
              className="flex items-center gap-1 rounded-full border border-border bg-surface-raised px-3 py-1 text-sm text-content"
            >
              {value}
              <button
                type="button"
                aria-label={`Remove ${value}`}
                className="rounded text-content-subtle transition-colors hover:text-content focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
                onClick={() => onChange(values.filter((other) => other !== value))}
              >
                <X aria-hidden className="h-3.5 w-3.5" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

/**
 * Which version this is, and who described it.
 *
 * **Version 0 renders nothing.** A company that has described nobody has no
 * author and no moment, and inventing a line for that state would be the
 * screen filling a gap rather than reporting one.
 */
function Provenance({ declaration }: { declaration: IcpDeclaration }) {
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
