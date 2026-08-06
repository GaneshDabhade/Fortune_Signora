'use client';

import { Search } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useEffect, useId, useRef, useState } from 'react';

import { MINIMUM_QUERY, useAccountSearch } from '@/lib/query/hooks/search';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';
import { cn } from '@/lib/design/cn';
import type { SearchCoverage, SearchResultType } from '@/lib/api/types';

/**
 * *"Show me Databricks."* — A1, and the second question of every evaluation.
 *
 * **Search is a verb, not a place**, so this lives in the shell header rather
 * than becoming another navigation entry. A ranked list answers *"what should
 * I work on?"*; it structurally cannot answer *"what about this one?"*, and the
 * second is the question an evaluator asks to find out whether Signora knows
 * their world.
 *
 * ### It searches names nobody is displaying, and that is deliberate
 *
 * The server matches every `legal_name` a source has ever claimed, not the one
 * being shown. **A company that renamed is found under its old name and listed
 * under its new one** — which is what somebody who has not heard about the
 * rename is typing. It also means a result may not visibly contain what was
 * searched for, so the list shows the *current* name and never highlights a
 * matched substring: highlighting would promise the match is in the text, and
 * sometimes it is not.
 *
 * **That refusal is now a disclosure.** The server says which name matched, so
 * a row that came back under a name it is not being shown under says so —
 * *matched «Northwind Traders»* under a company now called Northwind Group.
 * **Only those rows are annotated.** A row that matched under its own name
 * needs no explanation, and a list that explains every row is one people stop
 * reading.
 *
 * ### The keyboard is the point, not an accessibility afterthought
 *
 * A seller who has learned this control never touches the mouse for it. **⌘K**
 * from anywhere, arrows to move, Enter to open, Escape to leave. Every one of
 * those is also what makes it operable without sight, which is why it is one
 * implementation rather than two (§20c — an unreachable control is a defect).
 *
 * **A listbox rather than a menu.** The results are a set of things to choose
 * between, not commands to run, and the difference decides which ARIA pattern
 * a screen reader announces.
 */
export function AccountSearch() {
  const router = useRouter();
  const { activeWorkspace } = useWorkspaceContext();
  const workspaceId = activeWorkspace?.id ?? null;

  const [text, setText] = useState('');
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listId = useId();

  const { data: groups, isFetching } = useAccountSearch(workspaceId, text);
  const asked = text.trim().length >= MINIMUM_QUERY;
  /** **Every match, in group order — the keyboard's view of the list.**
   * Arrow keys move through results and never through headings, so the index
   * `active` holds must count matches rather than rendered rows. */
  const rows = (groups ?? []).flatMap((group) => group.results);

  useEffect(() => {
    // **⌘K, and Ctrl+K for everyone not on a Mac.** Bound on the document
    // because the whole value is reaching search from wherever you are; a
    // shortcut that only works once the control has focus is not a shortcut.
    function onKey(event: KeyboardEvent) {
      if (event.key.toLowerCase() !== 'k' || !(event.metaKey || event.ctrlKey)) return;
      event.preventDefault();
      inputRef.current?.focus();
      inputRef.current?.select();
    }
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, []);

  // The highlighted row returns to the top whenever the answer changes.
  // Without this, typing one more letter leaves the highlight on whatever is
  // now in position four — and Enter opens an account nobody chose.
  useEffect(() => setActive(0), [text]);

  if (!workspaceId) return null;

  function go(accountId: string) {
    setOpen(false);
    setText('');
    inputRef.current?.blur();
    router.push(`/accounts/${accountId}`);
  }

  function onKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (event.key === 'Escape') {
      setOpen(false);
      inputRef.current?.blur();
      return;
    }
    if (!open || rows.length === 0) return;

    if (event.key === 'ArrowDown') {
      event.preventDefault();
      setActive((index) => (index + 1) % rows.length);
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      setActive((index) => (index - 1 + rows.length) % rows.length);
    } else if (event.key === 'Enter') {
      event.preventDefault();
      const chosen = rows[active];
      if (chosen) go(chosen.account.account_id);
    }
  }

  return (
    <div className="relative w-full max-w-sm">
      <Search
        aria-hidden="true"
        className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-content-subtle"
      />
      <input
        ref={inputRef}
        type="search"
        value={text}
        onChange={(event) => {
          setText(event.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        // A click on a result would otherwise be lost: blur closes the list
        // before the click lands. The delay is the smallest that survives it.
        onBlur={() => setTimeout(() => setOpen(false), 120)}
        onKeyDown={onKeyDown}
        placeholder="Find an account"
        aria-label="Find an account by name"
        role="combobox"
        aria-expanded={open && asked}
        aria-controls={listId}
        aria-autocomplete="list"
        className="h-8 w-full rounded border border-border bg-canvas pl-8 pr-3 text-sm text-content placeholder:text-content-subtle focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
      />

      {open && asked ? (
        <div
          id={listId}
          role="listbox"
          aria-label="Accounts"
          className="absolute left-0 right-0 top-9 z-20 overflow-hidden rounded border border-border bg-surface shadow-lg"
        >
          {/* **Grouped by kind, and the group is drawn whether or not it
              matched** — *"the absence of results and the absence of the group
              represent different business meanings"* (product owner,
              2026-08-05). **B-208**: this surface read the API's groups as if
              they were results and threw on the first match; the grouping the
              server has sent since TASK-408 is now what is rendered. */}
          {(groups ?? []).map((group) => (
            <div key={group.result_type}>
              <p className="px-3 pt-2 text-xs font-medium uppercase tracking-wide text-content-subtle">
                {KIND_LABEL[group.result_type]}
              </p>
              {group.results.length === 0 ? (
                <p role="status" className="px-3 pb-2 pt-1 text-sm text-content-muted">
                  {/* **`coverage` is read before `results`, always.** An empty
                      list means nothing until this says which emptiness it is —
                      collapsing *"nothing matched"* into *"we did not look"* is
                      exactly what the group exists to prevent. */}
                  {coverageSentence(group.coverage, group.result_type, text.trim())}
                </p>
              ) : null}
              {group.results.map((row) => {
                const index = rows.indexOf(row);
                return (
                  <button
                    key={row.account.account_id}
                    type="button"
                    role="option"
                    aria-selected={index === active}
                    onMouseEnter={() => setActive(index)}
                    onClick={() => go(row.account.account_id)}
                    className={cn(
                      'block w-full px-3 py-2 text-left text-sm text-content',
                      index === active && 'bg-surface-raised',
                    )}
                  >
                    {/* **An account nobody has named is still a result.** It is
                        a company the pipeline is watching, and hiding it would
                        make search quietly disagree with the list that shows
                        it. */}
                    <span className="block truncate">
                      {row.account.name ?? (
                        <span className="text-content-subtle">Unnamed account</span>
                      )}
                    </span>
                    {/* **Only the rows that need explaining.** `is_renamed` is
                        the server's answer to *"did this match under something
                        other than what you are reading?"*, and it is false for
                        almost every row. */}
                    {row.is_renamed ? (
                      <span className="block truncate text-xs text-content-muted">
                        matched “{row.matched_name}”
                      </span>
                    ) : null}
                  </button>
                );
              })}
            </div>
          ))}

          {rows.length === 0 && (groups ?? []).length === 0 ? (
            <p className="px-3 py-2 text-sm text-content-muted" role="status">
              {isFetching ? 'Looking…' : `No account here is called “${text.trim()}”`}
            </p>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

/** What each kind is called on screen. **The customer's word, not
 * `EntityKind`'s** — a heading reading `company` would be the data model
 * showing through (ADR-0034). */
const KIND_LABEL: Record<SearchResultType, string> = {
  company: 'Accounts',
  technology: 'Technologies',
};

/**
 * Which emptiness this is.
 *
 * **Three states and three sentences**, because they ask a customer to do
 * different things: search for something else · stop expecting this kind ·
 * change what you asked for.
 */
function coverageSentence(
  coverage: SearchCoverage,
  kind: SearchResultType,
  query: string,
): string {
  if (coverage === 'not_applicable') {
    return `Signora does not search ${KIND_LABEL[kind].toLowerCase()} by name.`;
  }
  if (coverage === 'not_requested') {
    return `${KIND_LABEL[kind]} were not included in this search.`;
  }
  return `Nothing in ${KIND_LABEL[kind].toLowerCase()} matches “${query}”.`;
}
