'use client';

import { Search } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useEffect, useId, useRef, useState } from 'react';

import { MINIMUM_QUERY, useAccountSearch } from '@/lib/query/hooks/search';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';
import { cn } from '@/lib/design/cn';

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

  const { data: results, isFetching } = useAccountSearch(workspaceId, text);
  const rows = results ?? [];
  const asked = text.trim().length >= MINIMUM_QUERY;

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
      if (chosen) go(chosen.account_id);
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
          {rows.map((row, index) => (
            <button
              key={row.account_id}
              type="button"
              role="option"
              aria-selected={index === active}
              onMouseEnter={() => setActive(index)}
              onClick={() => go(row.account_id)}
              className={cn(
                'block w-full truncate px-3 py-2 text-left text-sm text-content',
                index === active && 'bg-surface-raised',
              )}
            >
              {/* **An account nobody has named is still a result.** It is a
                  company the pipeline is watching, and hiding it would make
                  search quietly disagree with the list that shows it. */}
              {row.name ?? <span className="text-content-subtle">Unnamed account</span>}
            </button>
          ))}

          {rows.length === 0 ? (
            <p className="px-3 py-2 text-sm text-content-muted" role="status">
              {isFetching ? 'Looking…' : `No account here is called “${text.trim()}”`}
            </p>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
