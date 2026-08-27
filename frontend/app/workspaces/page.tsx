'use client';

import { useEffect, useMemo, useRef, useState } from 'react';

import { Button, EmptyState, Input, SkeletonText } from '@/components/ui';
import { initialsFor } from '@/lib/workspace/initials';
import { useSession } from '@/lib/auth/client';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';
import { useRouter } from 'next/navigation';

/**
 * **WS-B — the standalone chooser** — [TASK-1421](../../../docs/BACKLOG.md),
 * against 📁 `docs/design-snapshot/screens/Fortune Signora Workspace Chooser.dc.html`
 * ([D-138](../../../docs/DECISION_REGISTER.md)).
 *
 * ## 🔴 This route was a 404, and four entry rules already sent people to it
 *
 * ⛔ **`app/workspaces/` held only `none/page.tsx`.** ⚡ **Measured before
 * building**: `rules.ts` routes to `/workspaces` from **rule 9** (intent, no
 * membership), **rule 10** (intent references a workspace they left), **rule
 * 13** — *"Several memberships, no last-used"* — and **rule 14**'s fallback,
 * and `gates.ts:111` offers *"Go to your organizations"* pointing here.
 *
 * 📁 **The design says so in its own first section**, which is how a reader
 * knows this is the gap rather than a preference: *"No Workspace Chooser
 * document existed. **Four Entry rules dead-ended here.** Entry rules 9, 10,
 * 13 and 14 all route to `/workspaces` and nothing drew it."*
 *
 * ⚡ **So somebody with two organizations and no last-used landed on a 404**,
 * which is the ordinary case for anybody who has just been invited to a
 * second one.
 *
 * ## ⚠️ The copy says *organization*, and the design says *workspace*
 *
 * 🔴 **Raised as [C-1517](../../../docs/LANE_COORDINATION.md) rather than
 * decided here.** 📁 [ADR-0034](../../../docs/architecture/adr/0034-ubiquitous-language.md)
 * assigns *workspace* to the platform and *Organization* to the customer, and
 * `vocabulary.test.tsx` **fails any screen literal carrying the first**. ⚡
 * **The shipped switcher already says *organization*** — and the design's own
 * §03 says both surfaces render the same row, **so two different nouns would
 * be the two surfaces disagreeing about what the thing is.**
 *
 * ⛔ **The ROUTE is unchanged.** 📁 ADR-0034: *"no… API path… is renamed."*
 *
 * ## ⛔ Outside both shells, deliberately
 *
 * ⚡ **The same reasoning `workspaces/none` records**: the app shell needs an
 * organization to render a rail for, **and this is the screen for somebody who
 * has not chosen one**; the auth shell is a 400px card for signing in, **and
 * this person is already signed in.**
 */
export default function WorkspaceChooserPage() {
  const { workspaces, isLoading, error, setActiveWorkspace } = useWorkspaceContext();
  const router = useRouter();
  const [filter, setFilter] = useState('');
  const headingRef = useRef<HTMLHeadingElement>(null);

  /**
   * ⚡ **Once, on arrival.** ⛔ **Not on every render** — re-focusing the
   * heading while somebody is typing in the filter would take the cursor away
   * from them, which is the opposite of what `2.4.3` is protecting.
   */
  useEffect(() => {
    headingRef.current?.focus();
  }, []);
  const { data: session } = useSession();
  const signedInAs = session?.user.email ?? null;

  const shown = useMemo(() => {
    const needle = filter.trim().toLowerCase();
    if (needle === '') return workspaces;
    return workspaces.filter((one) => one.name.toLowerCase().includes(needle));
  }, [workspaces, filter]);

  const choose = (workspaceId: string) => {
    setActiveWorkspace(workspaceId);
    router.push('/');
  };

  return (
    // 📁 *"520px column."* ⚡ A reading width rather than the page's, because
    // the whole screen is one decision.
    <main className="mx-auto flex min-h-screen w-full max-w-[520px] flex-col justify-center gap-6 px-6 py-12">
      {/* 🔴 **Who is signed in, and it is not decoration.** 📁 The design's
          WS-B header carries the product mark, the person's address and their
          avatar — ⚡ **and this is a screen somebody reaches on a shared
          laptop, or after an SSO redirect that may have signed them in as
          somebody else.** ⛔ **Without it a person cannot tell whose
          organizations they are looking at**, which is the one question this
          screen must not leave open. ⚠️ **Added after looking at it rendered**;
          the assertions were green without it. */}
      <div className="flex items-center justify-between gap-3 border-b border-border pb-4">
        <span className="text-sm font-semibold text-content">Signora</span>
        {signedInAs === null ? null : (
          <span className="truncate text-xs text-content-muted">{signedInAs}</span>
        )}
      </div>

      <header className="flex flex-col gap-2">
        {/**
          * 🔴 **📁 `2.4.3`: *"WS-B places focus on the h1 on load, **not the
          * search field**, so the list is announced before the control."***
          *
          * ⛔ **The search field used to focus itself on load**, so a
          * screen-reader user arrived inside a filter for a list they had not
          * been told existed —
          * ⚡ **and the sentence above it, *"you are a member of four"*, is the
          * one fact that makes the filter make sense.**
          *
          * ⚠️ **`tabIndex={-1}` is what makes a heading focusable at all** — the
          * heading is a focus TARGET, never a tab stop. ⛔ **And no
          * `outline-none` beside it**: the global indicator is `:focus-visible`,
          * which does not match programmatic focus, **so there is nothing to
          * suppress and suppressing it would only lean on an exemption the
          * repository's focus guard grants for a different case.**
          */}
        <h1
          ref={headingRef}
          tabIndex={-1}
          className="text-xl font-semibold text-content"
        >
          Choose an organization
        </h1>
        <p className="text-sm text-content-muted">
          {/* 📁 *"You are a member of four. Signora will remember this choice on
              this device, so you will not be asked again."*
              ⛔ **The count is rendered only once it is known** — `isLoading`
              returns above this, so it is never *"a member of 0"*. */}
          {isLoading
            ? 'Signora will remember this choice on this device, so you will not be asked again.'
            : `You are a member of ${countWord(workspaces.length)}. Signora will remember this choice on this device, so you will not be asked again.`}
        </p>
      </header>

      {isLoading ? (
        <SkeletonText lines={4} />
      ) : error !== null ? (
        /* 📁 **P-A** — a failed read must never render as an empty result.
           ⛔ Here an empty list would say *"you belong to nothing"*, which is
           a sentence about somebody's access rather than about a request. */
        <p className="text-sm text-content-muted">
          Your organizations could not be loaded. Nothing has changed — reload to try
          again.
        </p>
      ) : workspaces.length === 0 ? (
        /* ⚠️ **Reachable, and the entry engine does not send anybody here in
           this state** — rule 10 routes a person with no membership to
           `/workspaces/none`. ⛔ **It is rendered anyway**: a person who
           bookmarks this route and later leaves their last organization
           arrives with an empty list, and a blank column is not an answer. */
        <EmptyState
          title="You are not in an organization yet"
          description="Your organization is your company on Signora — where its accounts, evidence and decisions live. Create one, or ask a colleague to add you to theirs."
          action={
            <Button onClick={() => router.push('/settings')}>
              Create an organization
            </Button>
          }
        />
      ) : (
        <>
          {/* ⛔ **`>`, not `>=`** — 📁 *"search appears **above** 6 memberships"*,
              which is seven and not six. ⚠️ **The switcher already used `>`**,
              so the two surfaces disagreed about one word. */}
          {workspaces.length > SEARCH_APPEARS_ABOVE ? (
            <Input
              // ⚡ **The label IS the placeholder's sentence**, and `Input`
              // requires one — 📁 *"an unlabelled input is unusable with a
              // screen reader."*
              label={`Search ${countWord(workspaces.length)}`}
              type="search"
              value={filter}
              onChange={(event) => setFilter(event.target.value)}
              placeholder={`Search ${countWord(workspaces.length)}`}
              // 📁 *"Esc clears the filter."*
              onKeyDown={(event) => {
                if (event.key === 'Escape') setFilter('');
              }}
            />
          ) : null}

          {shown.length === 0 ? (
            /* ⛔ **Names the query rather than saying *no results*** — the
               switcher's own rule, and the design bans *"No workspaces
               found"* outright. */
            <p className="text-sm text-content-muted">
              No organization matches “{filter}”.
            </p>
          ) : (
            <ul className="flex flex-col gap-1.5" aria-label="Your organizations">
              {shown.map((workspace) => (
                <li key={workspace.id}>
                  <button
                    type="button"
                    onClick={() => choose(workspace.id)}
                    className="flex w-full items-center gap-3 rounded-lg border border-border px-3 py-3 text-left transition-colors hover:bg-surface-sunken "
                  >
                    <span
                      aria-hidden
                      className="grid h-8 w-8 flex-none place-items-center rounded-md bg-surface-sunken text-xs font-semibold text-content-muted"
                    >
                      {initialsFor(workspace.name)}
                    </span>
                    <span className="min-w-0 flex-1 truncate text-sm font-medium text-content">
                      {workspace.name}
                    </span>
                    {/* 📁 *"↵ enter workspace."* ⚡ The row IS the control, so
                        the affordance is the row rather than a second button
                        inside it. */}
                    <span aria-hidden className="flex-none text-xs text-content-subtle">
                      →
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}

          {/* 📁 *"Expecting a workspace that is not here? Ask an administrator
              to invite you."* ⚠️ **Never names one they cannot see** — the
              design bans exactly that, and there is nothing to name. */}
          <p className="text-xs text-content-subtle">
            Expecting an organization that is not here? Ask an administrator to invite
            you.
          </p>
        </>
      )}
    </main>
  );
}

/**
 * 📁 **`Workspace Chooser`, three times**: *"At 8 rows in the switcher and
 * **6 in the chooser**"* · *"Search appears **above 6 memberships**"* ·
 * *"above 8 rows in WS-A and above 6 in WS-B."*
 *
 * ⚠️ **This constant's previous note said *"the same threshold the shell
 * switcher uses"*, and the design says the opposite** — the two surfaces have
 * deliberately different numbers, with a stated reason: *"below that a filter
 * field is a control asking to be used for no reason; above it, scrolling is
 * the wrong interaction."*
 *
 * ⛔ **The switcher's own number is contested and is NOT changed here** —
 * 📁 [C-1575](../../../docs/LANE_COORDINATION.md). **WS-B's is not contested:
 * only this document describes WS-B at all.**
 */
const SEARCH_APPEARS_ABOVE = 6;

/**
 * *"a member of four"*, in the design's own form.
 *
 * ⛔ **Not *"4 organizations"*.** 📁 The design writes the number as a word in
 * a sentence, and a digit mid-sentence reads as a metric rather than as
 * something somebody is telling you.
 */
function countWord(n: number): string {
  const words = [
    'no',
    'one',
    'two',
    'three',
    'four',
    'five',
    'six',
    'seven',
    'eight',
    'nine',
  ];
  const said = words[n] ?? String(n);
  return n === 1 ? `${said} organization` : `${said} organizations`;
}
