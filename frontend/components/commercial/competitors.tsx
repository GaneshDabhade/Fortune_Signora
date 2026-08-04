'use client';

import { X } from 'lucide-react';
import { useState } from 'react';

import { formatDay } from '@/components/intelligence/dates';
import { Button, EmptyState, Input } from '@/components/ui';
import { ApiError } from '@/lib/api/client';
import type { Competitor, DeclaredCompetitors } from '@/lib/api/types';
import { useDeclareCompetitors } from '@/lib/query/hooks/commercial';

/**
 * Who this customer competes against.
 *
 * **The sixth declaration, and the first about a risk.** The other five say
 * what the customer wants — what they sell, who buys it, who decides, what
 * they are pushing, who they are watching. This one says what they are up
 * against.
 *
 * ### What the copy may and may not promise
 *
 * Saving this records the list. **Nothing consumes it yet** — the signal that
 * reads it is unbuilt — so this screen says Signora *has been told*, and does
 * not say it will warn anybody. A screen promising an alert the platform
 * cannot yet raise would be the product asserting something untrue, which is
 * worse than one that under-promises. The same restraint the watch list keeps.
 *
 * ### Names, not lookups
 *
 * There is no search, no autocomplete, no catalogue of vendors. The customer
 * types what they call the product; working out that *Salesforce*,
 * *salesforce.com* and *SFDC* are one thing happens later and elsewhere.
 * Anything here that resolved a name would put resolution in the recording
 * module — and would be a second resolver, free to disagree with the first.
 *
 * ### It grades nobody, and the absence is the design
 *
 * No threat level, no severity, no ranking, no ordering that means anything.
 * A product is a competitor or it is not. **How much a rival moves an account
 * is decided by a reviewed model a customer can read**, not by a number typed
 * on this screen that nothing would review.
 */
export function CompetitorsEditor({
  declared,
  workspaceId,
}: {
  declared: DeclaredCompetitors;
  workspaceId: string | null;
}) {
  const declare = useDeclareCompetitors(workspaceId);
  const [draft, setDraft] = useState('');

  const save = (next: Competitor[]) =>
    declare.mutate({ expected_version: declared.version, competitors: next });

  const add = () => {
    const name = draft.trim();
    // The server refuses two entries sharing a name — nothing here resolves
    // one, so a duplicate is ambiguous to the only person who could tell them
    // apart. Keeping one copy is what the customer meant either way.
    if (
      name === '' ||
      declared.competitors.some(
        (competitor) => competitor.name.toLowerCase() === name.toLowerCase(),
      )
    ) {
      return setDraft('');
    }
    // **The id is minted here, in the browser.** It is what makes saving
    // idempotent, and what lets a later rename be told apart from a
    // remove-and-re-add.
    save([...declared.competitors, { id: crypto.randomUUID(), name }]);
    setDraft('');
  };

  return (
    <section className="flex flex-col gap-4">
      <header>
        <h2 className="text-sm font-semibold text-content">Who you compete against</h2>
        <p className="mt-1 text-sm text-content-muted">
          The products you lose deals to. Type them the way you say them — Signora records
          who they are and ranks none of them.
        </p>
      </header>

      {declare.isError ? <Refusal error={declare.error} /> : null}

      <form
        className="flex items-end gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          add();
        }}
      >
        <div className="grow">
          <Input
            label="Competing product"
            value={draft}
            maxLength={128}
            placeholder="Salesforce"
            onChange={(event) => setDraft(event.target.value)}
          />
        </div>
        <Button type="submit" variant="secondary" disabled={draft.trim() === ''}>
          Add
        </Button>
      </form>

      {declared.competitors.length === 0 ? <Nobody declared={declared} /> : null}
      {declared.competitors.length > 0 ? (
        <ul className="flex flex-col divide-y divide-border rounded-md border border-border">
          {declared.competitors.map((competitor) => (
            <li
              key={competitor.id}
              className="flex items-center justify-between gap-4 px-4 py-2.5"
            >
              <span className="min-w-0 text-sm text-content">{competitor.name}</span>
              <Button
                size="sm"
                variant="ghost"
                aria-label={`Remove ${competitor.name}`}
                disabled={declare.isPending}
                onClick={() =>
                  save(
                    declared.competitors.filter((other) => other.id !== competitor.id),
                  )
                }
              >
                <X aria-hidden className="h-4 w-4" />
              </Button>
            </li>
          ))}
        </ul>
      ) : null}

      <Provenance declared={declared} />
    </section>
  );
}

/**
 * An empty list, and **which kind of empty it is**.
 *
 * A workspace that has never said anything is at version 0. One that saved an
 * empty list is at version 1 — *"we do not track competitors"* is a statement,
 * with an author and a moment, and the product knows the difference. Telling
 * somebody to *add the first one* when they have already decided not to would
 * be the screen forgetting what they said.
 */
function Nobody({ declared }: { declared: DeclaredCompetitors }) {
  if (declared.version === 0) {
    return (
      <EmptyState
        title="No competitors yet"
        description="Add the first product you lose deals to. Signora keeps the list; you can change it whenever your market does."
      />
    );
  }

  return (
    <EmptyState
      title="You have said you do not track competitors"
      description="This list is empty because you saved it that way, not because nothing was asked. Add one whenever that changes."
    />
  );
}

/**
 * Which version this is, and who declared it.
 *
 * **Version 0 renders nothing.** A workspace that has named nobody has no
 * author and no moment, and inventing a line for that state would be the
 * screen filling a gap rather than reporting one.
 */
function Provenance({ declared }: { declared: DeclaredCompetitors }) {
  if (declared.version === 0 || declared.updated_at === null) return null;

  return (
    <p className="text-xs text-content-subtle">
      Version {declared.version} · last changed {formatDay(declared.updated_at)}. Every
      version is kept — a change is a new one, never an edit.
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
