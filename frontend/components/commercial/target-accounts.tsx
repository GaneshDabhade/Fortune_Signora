'use client';

import { X } from 'lucide-react';
import { useMemo, useState } from 'react';

import { formatDay } from '@/components/intelligence/dates';
import { LastChecked } from '@/components/intelligence/freshness';
import { Button, EmptyState, Input } from '@/components/ui';
import { ApiError } from '@/lib/api/client';
import type { SubjectCoverage, TargetAccount, TargetAccountList } from '@/lib/api/types';
import { useDeclareTargetAccounts } from '@/lib/query/hooks/commercial';
import { useTargetAccountCoverage } from '@/lib/query/hooks/coverage';

/**
 * The companies this customer wants watched.
 *
 * **The last of the five declarations, and the one the rest of the platform
 * actually reads.** Everything else here describes the customer's business;
 * this names the companies Signora is being pointed at.
 *
 * ### What the copy may and may not promise
 *
 * Saving this records the list and announces that it changed. **Nothing
 * downstream consumes that announcement yet** — the consuming side is another
 * lane's, unbuilt — so this screen says Signora *has been told*, and does not
 * say it has started looking. A screen that promised monitoring the platform
 * is not yet doing would be the product asserting something untrue, which is
 * worse than a screen that under-promises.
 *
 * ### Names, not lookups
 *
 * There is no search, no autocomplete against a company database, and no
 * validation that a company exists. The customer types what they call the
 * company; working out which company that is happens later and elsewhere.
 * Anything here that resolved a name would put resolution in the recording
 * module.
 *
 * ### It now shows whether Signora has looked, and that took a second request
 *
 * **A7, and [C-219](../../../docs/LANE_COORDINATION.md) option ③ as Lane C
 * ratified it.** This screen used to say that whether Signora had looked at an
 * account was Provider Platform's fact and that the API carried none of them.
 * The first half is still true — which is exactly why the answer arrives on its
 * own request rather than as a field on the declaration. **The module that owns
 * this list may not read the module that owns the attempts**, and reversing
 * that edge would make the dependency graph cyclic, so **the screen composes
 * the two** — the same arrangement the attention list uses to put names on
 * accounts.
 *
 * **The key is the company name**, because it is the same string on both sides
 * by construction: what the customer typed here is what `RunProviderSync` is
 * given. There is no join to build, and nothing resolves a name to find one.
 *
 * **What it still does not show** is what Signora found or when it will look
 * again. Neither exists as a fact yet, and a screen promising either would be
 * back to asserting something untrue.
 */
export function TargetAccountsEditor({
  accounts,
  workspaceId,
}: {
  accounts: TargetAccountList;
  workspaceId: string | null;
}) {
  const declare = useDeclareTargetAccounts(workspaceId);
  const [draft, setDraft] = useState('');

  // Memoised because the array is the query key. Rebuilding it each render
  // would make every render a new key, and every new key a new request.
  const subjects = useMemo(
    () => accounts.accounts.map((account) => account.name),
    [accounts.accounts],
  );
  const { data: coverage } = useTargetAccountCoverage(workspaceId, subjects);

  // **Keyed by name, which is the only key both sides share.** The declaration
  // entry's id is Commercial Profile's and never reaches a sync; the subject a
  // sync records is this name, verbatim.
  const checked = useMemo(() => {
    const found = new Map<string, SubjectCoverage>();
    for (const entry of coverage ?? []) found.set(entry.subject, entry);
    return found;
  }, [coverage]);

  const save = (next: TargetAccount[]) =>
    declare.mutate({ expected_version: accounts.version, accounts: next });

  const add = () => {
    const name = draft.trim();
    // The server refuses two entries sharing a name — nothing here resolves
    // one, so a duplicate is ambiguous to the only person who could tell them
    // apart. Keeping one copy is what the customer meant either way.
    if (
      name === '' ||
      accounts.accounts.some(
        (account) => account.name.toLowerCase() === name.toLowerCase(),
      )
    ) {
      return setDraft('');
    }
    // **The id is minted here, in the browser.** It is what makes saving
    // idempotent, and what lets a later rename be told apart from a
    // remove-and-re-add — different instructions about spending money.
    save([...accounts.accounts, { id: crypto.randomUUID(), name }]);
    setDraft('');
  };

  return (
    <section className="flex flex-col gap-4">
      <header>
        <h2 className="text-sm font-semibold text-content">Accounts you are watching</h2>
        <p className="mt-1 text-sm text-content-muted">
          The companies you want Signora watching. Type them the way you say them — you
          do not need a website or a legal name.
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
            label="Company"
            value={draft}
            maxLength={128}
            placeholder="Northwind Health"
            onChange={(event) => setDraft(event.target.value)}
          />
        </div>
        <Button type="submit" variant="secondary" disabled={draft.trim() === ''}>
          Add
        </Button>
      </form>

      {accounts.accounts.length === 0 ? (
        <EmptyState
          title="No accounts yet"
          description="Add the first company you want watched. Signora keeps the list; you can change it whenever your territory does."
        />
      ) : (
        <ul className="flex flex-col divide-y divide-border rounded-md border border-border">
          {accounts.accounts.map((account) => (
            <li
              key={account.id}
              className="flex items-center justify-between gap-4 px-4 py-2.5"
            >
              <div className="min-w-0">
                <span className="text-sm text-content">{account.name}</span>
                {/* **Rendered only once the answer has arrived.** *Loading* and
                    *nobody has looked* are different facts, and a line that
                    said the second while the first was true would be the
                    screen inventing an answer to fill a gap. */}
                {checked.has(account.name) ? (
                  <LastChecked
                    lastAttempt={checked.get(account.name)!.last_attempt}
                    storedAnything={checked.get(account.name)!.stored_anything}
                  />
                ) : null}
              </div>
              <Button
                size="sm"
                variant="ghost"
                aria-label={`Stop watching ${account.name}`}
                disabled={declare.isPending}
                onClick={() =>
                  save(accounts.accounts.filter((other) => other.id !== account.id))
                }
              >
                <X aria-hidden className="h-4 w-4" />
              </Button>
            </li>
          ))}
        </ul>
      )}

      <Provenance accounts={accounts} />
    </section>
  );
}

/**
 * Which version this is, and who declared it.
 *
 * **Version 0 renders nothing.** A workspace that has named nobody has no
 * author and no moment, and inventing a line for that state would be the
 * screen filling a gap rather than reporting one.
 */
function Provenance({ accounts }: { accounts: TargetAccountList }) {
  if (accounts.version === 0 || accounts.updated_at === null) return null;

  return (
    <p className="text-xs text-content-subtle">
      Version {accounts.version} · last changed {formatDay(accounts.updated_at)}. Every
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
