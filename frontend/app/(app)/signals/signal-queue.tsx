'use client';

import { useEffect, useMemo, useState } from 'react';

import {
  Badge,
  Button,
  Card,
  Dialog,
  EmptyState,
  ErrorState,
  Input,
  PageHeader,
  Select,
  LoadingRegion,
  Skeleton,
  TabPanel,
  Tabs,
} from '@/components/ui';
import { ApiError } from '@/lib/api/client';
import type { QueueEntry, QueueState, ResolveOutcome } from '@/lib/api/types';
import { useSignalCatalog } from '@/lib/query/hooks';
import { AccountName } from '@/components/intelligence/account-name';
import { formatDay } from '@/components/intelligence/dates';
import { colleaguesFrom, nameOf, peopleFrom } from '@/components/team/people';
import { useAccountIdentities } from '@/lib/query/hooks';
import { useWorkspaceMembers } from '@/lib/query/hooks/team';
import { useResolveSignal, useWorkspaceTriage } from '@/lib/query/hooks/triage';
import { cn } from '@/lib/design/cn';
import { useSession } from '@/lib/auth/client';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';

/**
 * **The Signal Center** — [TASK-439](../../../../docs/BACKLOG.md), against
 * `docs/design-snapshot/screens/Fortune Signora Signal Center.dc.html`
 * ([D-138](../../../../docs/DECISION_REGISTER.md)).
 *
 * > 📁 ***"A triage queue, not a notification list · every signal ends in a
 * > decision."***
 *
 * ## ⛔ What this slice is, and what it deliberately is not
 *
 * **The row's `Delivers` is the boundary, not the design's page count**:
 * *"the queue, grouped and counted · the four ways a signal ends · a dismissal
 * reason · snoozed signals returning at their stated time."*
 *
 * ⚠️ **The design also draws signal analytics, a rules engine with automatic
 * retuning, per-signal evidence, reasoning and a timeline.** ⛔ **None of that
 * is built here.** **No row covers them and none of their reads exist** —
 * building them would be inventing scope ([§21](../../../../CLAUDE.md)), and
 * the row already bounded itself for exactly this reason.
 *
 * ## ⚠️ Two `mechanics` this screen does NOT satisfy, and neither is a defect
 *
 * 📁 ***"Dismissal is training data — every dismissal takes a reason from a
 * closed list."*** ⛔ **The reason here is free text, and that is correct.**
 * 📁 `domain/resolution.py` refuses the closed set in terms: *"Deliberately
 * free text and not a closed set. A vocabulary of dismissal reasons is a
 * product decision about what the platform believes can be wrong with its own
 * judgement, and inventing one inside an implementation slice would be exactly
 * the 'architecture arriving in a feature' §20e forbids."*
 *
 * ✅ **And the mechanic's stated PURPOSE is served anyway** — *"those reasons
 * drive rule precision"*. 📁 `domain/precision.py` counts **outcomes**, not
 * reason texts: `Actioned` as right, `Dismissed` as wrong, and neither
 * `Assigned` nor `Snoozed` at all. **A closed list would change the
 * vocabulary, not the measurement.**
 *
 * 📁 ***"Snooze is a commitment — a snooze needs a date and a reason."*** ⛔
 * **`Snoozed` carries `until` and nothing else**, so a reason is
 * **unrepresentable** rather than merely unasked. ⚡ **That is a domain change
 * with a stored column behind it, and this row's `Delivers` bounds itself to
 * *"snoozed signals returning at their stated time"*** — **the date, not the
 * commitment.**
 *
 * ## 🔴 Two fields the design draws are absent, and that is reported
 *
 * **The design's rows carry `title · type · summary · account · pips`.**
 * ✅ **Three resolve against what is published**: the catalog supplies the
 * title (*"the key travels and `useSignalCatalog` supplies the words"*),
 * `signal_type` is on the entry, and `AccountIdentity` supplies the name.
 *
 * ⛔ **`summary` and `confidence` have no source at all** —
 * [C-251](../../../../docs/LANE_COORDINATION.md). **They are ABSENT rather
 * than drawn empty or drawn locked**, which is
 * [C-248](../../../../docs/LANE_COORDINATION.md)'s precedent.
 *
 * ⚠️ **The tempting wrong move, named so nobody makes it later**: the catalog
 * carries `why_it_matters`, and rendering it as the row summary would look
 * right and be wrong on every row — **it is a fact about the *type*, identical
 * under every signal of that type**, printed where the design puts a
 * per-instance finding.
 */

/**
 * ⚡ **The three states `QueueState` publishes** — `open` · `snoozed` ·
 * `closed`.
 *
 * 🔴 **CORRECTED.** This said *"the design's three tabs"* and the design has no
 * three-tab strip: 📁 `Design Documents/Fortune Signora Signal Center.html`
 * draws a **saved-view** strip — *Needs review · Assigned to me · Critical only
 * · Buying signals · Snoozed* — and puts `Closed` under a separate **history**
 * section with its own tabs. ⛔ **A comment citing a design that does not say
 * that is the false-claim class** ([§2](../../../../CLAUDE.md)).
 *
 * ⚠️ **The implementation is not wrong; the citation was.** Three of the
 * design's five views need fields `QueueEntry` does not carry — **no assignee,
 * no severity, no type taxonomy** — so a five-view strip would be two real
 * views and three that cannot be built. ✅ **The state a signal is in is
 * publishable, and every signal remains reachable**, which is what the strip is
 * for. **The gap is [C-292](../../../../docs/LANE_COORDINATION.md).**
 */
const STATES: readonly { value: QueueState; label: string }[] = [
  { value: 'open', label: 'Needs review' },
  { value: 'snoozed', label: 'Snoozed' },
  { value: 'closed', label: 'Closed' },
];

/**
 * ⛔ **A dismissal requires a reason and the type already says so** —
 * `ResolveOutcome` is a discriminated union where *"a dismissal without a
 * reason is unconstructable rather than merely rejected"*. **This screen keeps
 * that true at the edge**: the control cannot submit an empty one.
 *
 * 📁 **And the design says why it matters, which is not politeness**:
 * *"Dismissal reasons feed rule precision."* **A reason is an input to
 * retuning, so an empty one is a lost measurement rather than a rude click.**
 */
/**
 * ♿ **One id base, shared by the tab strip and the panel it controls** — 📁
 * [B-1055](../../../../docs/BUGS.md). ⛔ **Not spelled twice**: two spellings
 * of one link is how the link rots without any test noticing.
 */
const QUEUE_TABS = 'signal-queue-state';

const MIN_REASON = 1;

/**
 * ⚡ **What the API said, in the customer's words** — and nothing invented when
 * it said nothing a person can act on.
 *
 * ⛔ **A local function rather than a shared one, deliberately.** 📁
 * [`workflow.tsx`](../../../components/intelligence/workflow.tsx) has the same
 * shape and **carries a translation this screen must not**: it rewrites
 * `transition_refused` into a sentence about an account moving underneath the
 * reader. ⚠️ **Two callers is a coincidence** — 📁
 * [`people.ts`](../../../components/team/people.ts) records the rule that three
 * is the trigger — **and folding an account-specific refusal into a signal
 * screen would be sharing the wrong half.**
 */
function refusal(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  return 'This could not be recorded. Nothing has changed — try again.';
}

/**
 * 🔴 **The earliest day a snooze may name — tomorrow, in the reader's own
 * timezone.**
 *
 * ⛔ **The backend refuses a snooze that has already elapsed** — 📁
 * `resolution.py`: *"A snooze until … has already elapsed, so the signal would
 * come straight back. Choose a time in the future."* ⚡ **The control refuses it
 * first**, so the customer meets the rule at the field rather than as a `422`
 * after they committed to it.
 */
function earliestSnooze(now: Date = new Date()): string {
  const day = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1);
  const month = `${day.getMonth() + 1}`.padStart(2, '0');
  const date = `${day.getDate()}`.padStart(2, '0');
  return `${day.getFullYear()}-${month}-${date}`;
}

/**
 * ⚡ **A day the customer chose, as the instant the API needs.**
 *
 * 📁 **Day precision is the product's rule, not this screen's shortcut** —
 * [`dates.ts`](../../../components/intelligence/dates.ts): *"evidence decays in
 * bands measured in weeks, and a timestamp to the minute implies a resolution
 * the pipeline does not have."* ⛔ **So the control asks for a DATE**, which is
 * also the design's own word: 📁 *"Snooze with a date."*
 *
 * ⚠️ **The instant is the START of that day where the reader is**, and that is
 * a stated choice rather than a hidden one. ⛔ **09:00 would have been a guess
 * about a working day the product knows nothing about**; *"it comes back on
 * the 24th"* is what the customer asked for and what they get.
 */
function returnsAt(day: string): string {
  const [year, month, date] = day.split('-').map(Number);
  return new Date(year as number, (month as number) - 1, date as number).toISOString();
}

export function SignalQueue() {
  const { activeWorkspace } = useWorkspaceContext();
  const workspaceId = activeWorkspace?.id ?? null;

  const [state, setState] = useState<QueueState>('open');
  const [dismissing, setDismissing] = useState<QueueEntry | null>(null);
  const [reason, setReason] = useState('');
  /**
   * 🔴 **Two of the four exits the screen PROMISES, and neither had a control.**
   *
   * 📁 The description this page renders is the design's own sentence —
   * *"Every one leaves the queue by being actioned, **assigned**, **snoozed** or
   * dismissed with a reason"* — and 📁 `ResolveOutcome` carries all four.
   * ⛔ **The row offered two**, so the screen stated a capability the product
   * would not perform, and the *Snoozed* view showed the result of an action
   * nobody could take.
   *
   * ⚠️ **The inverse of the usual defect**: not invented UI, but *promised* UI.
   */
  const [assigning, setAssigning] = useState<QueueEntry | null>(null);
  const [assignTo, setAssignTo] = useState<string | null>(null);
  const [snoozing, setSnoozing] = useState<QueueEntry | null>(null);
  const [snoozeUntil, setSnoozeUntil] = useState('');

  /**
   * 📁 **Surface ② — the design's filter chips** ([TASK-1468](../../../../docs/BACKLOG.md)).
   *
   * ⛔ **By `signal_type`, and NOT by the design's own example.** 📁 It draws
   * *"Confidence ≥ 3"* — 🔴 **`QueueEntry` publishes six fields and confidence
   * is not one of them**, so a confidence chip would be filtering on a number
   * this screen invented. **The gap is stated to the reader instead**
   * ([§20c](../../../../CLAUDE.md)).
   *
   * 🔴 **And the filter is CLIENT-side while the state tabs are SERVER-side —
   * the two are not the same decision.** 📁 [`triage.ts`](../../../lib/query/hooks/triage.ts)
   * says why: *"queue state is derived on the server from the decision in force
   * and the clock; a browser re-filtering a cached page would be re-deriving it
   * from stale inputs, and a snooze that had elapsed would keep looking
   * snoozed."* ⚡ **`signal_type` carries no clock** — it is a fact about the
   * signal, fixed when it was raised — **so narrowing on it locally cannot go
   * stale.** ⛔ **Nothing here may narrow `state`.**
   */
  const [types, setTypes] = useState<ReadonlySet<string>>(() => new Set());

  /**
   * 📁 **Surface ③ — bulk selection.** ⚡ **Held as `signal_id`s rather than as
   * entries**, so a selection survives a refetch that replaced the objects: 📁
   * `useResolveSignal` invalidates every triage view on each decision, **and a
   * selection of stale objects would act on rows that had already moved.**
   */
  const [selected, setSelected] = useState<ReadonlySet<string>>(() => new Set());

  const queue = useWorkspaceTriage(workspaceId, state);
  /**
   * 📁 **Surface ⑦ — the counts header.** ⚡ **A second read of the OPEN queue**,
   * so *"needs review"* is true on every tab rather than only on the one that
   * happens to be showing. ⛔ **react-query de-duplicates it against the tab's
   * own request when `state` is `open`**, so this is one request, not two.
   */
  const open = useWorkspaceTriage(workspaceId, 'open');
  const catalog = useSignalCatalog(workspaceId);
  const resolve = useResolveSignal(workspaceId);
  /**
   * ⚡ **The roster, so a signal can be handed to a colleague** — 📁 the same
   * query [Company 360](../accounts/[accountId]/page.tsx) and the Team page
   * already hold, same cache key, **so this costs no request.**
   *
   * ⛔ **Named or not offered.** 📁 [`people.ts`](../../../components/team/people.ts):
   * *"A membership added by identifier has no address, and 'Somebody here' in a
   * picker is a row nobody can choose between."* ⚡ **`colleaguesFrom` already
   * enforces that**, which is why this screen resolves nothing itself.
   */
  const { data: roster } = useWorkspaceMembers(workspaceId);
  const viewerId = useSession().data?.user.id ?? null;
  const people = peopleFrom(roster?.items);
  const colleagues = colleaguesFrom(roster?.items, viewerId);

  const all = useMemo(() => queue.data?.items ?? [], [queue.data]);

  /**
   * ⚡ **What the list shows** — `all` narrowed by the chosen types. ⛔ **An
   * empty selection is *not narrowed*, never *nothing*** — the same rule
   * [`working-list.ts`](../../../lib/views/working-list.ts) applies to `all`:
   * **the absence of a narrowing is not a narrowing to zero.**
   */
  const entries = useMemo(
    () => (types.size === 0 ? all : all.filter((entry) => types.has(entry.signal_type))),
    [all, types],
  );

  // ⚡ **One request for every name on the page**, not one per row — the hook
  // de-duplicates and sorts the ids so the key is stable.
  const identities = useAccountIdentities(
    workspaceId,
    entries.map((entry) => entry.entity_id),
  );

  /** The catalog's words for a key. ⛔ **Never a table in this file** — that
   * would be the second vocabulary the architecture forbids. */
  const titleFor = (key: string): string => catalog.data?.get(key)?.title ?? key;

  /**
   * 📁 *"Grouped and counted."* **Grouped by signal type**, which is the only
   * grouping the published contract can support — ⛔ severity, the design's
   * other axis, is not a field the entry carries.
   */
  const groups = useMemo(() => {
    const byType = new Map<string, QueueEntry[]>();
    for (const entry of entries) {
      const bucket = byType.get(entry.signal_type);
      if (bucket === undefined) byType.set(entry.signal_type, [entry]);
      else bucket.push(entry);
    }
    return [...byType.entries()].sort((a, b) => b[1].length - a[1].length);
  }, [entries]);

  /**
   * ⛔ **The chips are built from the UNFILTERED page, never from `entries`.**
   * ⚡ **Otherwise choosing a type removes every other chip** — the control
   * that narrows the list would delete the way back, which is the
   * control-that-traps-you shape rather than a filter.
   */
  const availableTypes = useMemo(() => {
    const counts = new Map<string, number>();
    for (const entry of all)
      counts.set(entry.signal_type, (counts.get(entry.signal_type) ?? 0) + 1);
    return [...counts.entries()].sort((a, b) => b[1] - a[1]);
  }, [all]);

  const toggleType = (type: string) =>
    setTypes((was) => {
      const next = new Set(was);
      if (next.has(type)) next.delete(type);
      else next.add(type);
      return next;
    });

  /**
   * ⛔ **Selection is cleared whenever the visible set changes.** ⚠️ **A
   * selection that survives a filter is a selection whose action bar says
   * *"3 selected"* while two of them are off screen** — and the person presses
   * it believing it means the three they can see.
   */
  const visibleIds = entries.map((entry) => entry.signal_id).join(',');
  useEffect(() => setSelected(new Set()), [visibleIds]);

  const toggleSelected = (signalId: string) =>
    setSelected((was) => {
      const next = new Set(was);
      if (next.has(signalId)) next.delete(signalId);
      else next.add(signalId);
      return next;
    });

  /**
   * ⛔ **`onSettled` is where a dialog closes, never on the click.**
   *
   * 🔴 **The dismissal dialog used to close the moment it was pressed** — so a
   * refused write left the reader looking at a queue that had not changed,
   * believing they had dismissed something. ⚠️ **That is a fake interaction
   * that appears functional**, which is the one thing this product may never
   * render: 📁 [P-A](../../../../docs/DOMAIN_DISCOVERY_REGISTER.md)'s rule
   * pointed at a write instead of a read.
   */
  const decide = (entry: QueueEntry, outcome: ResolveOutcome, onDone?: () => void) => {
    resolve.mutate(
      { signalId: entry.signal_id, outcome },
      { onSuccess: () => onDone?.() },
    );
  };

  const closeAssign = () => {
    setAssigning(null);
    setAssignTo(null);
    resolve.reset();
  };

  const closeSnooze = () => {
    setSnoozing(null);
    setSnoozeUntil('');
    resolve.reset();
  };

  const closeDismiss = () => {
    setDismissing(null);
    setReason('');
    resolve.reset();
  };

  /**
   * 📁 **Surface ③'s action bar.** ⛔ **Only the outcomes that need no further
   * input.** ⚠️ **Dismissal is deliberately NOT here**: 📁 the queue's own rule
   * is that a dismissal carries a reason — *"a dismissal without a reason is
   * unconstructable rather than merely rejected"* — **and one reason typed once
   * for eleven different signals is the reason nobody can cite later.**
   */
  const decideMany = (outcome: ResolveOutcome) => {
    for (const signalId of selected) resolve.mutate({ signalId, outcome });
    setSelected(new Set());
  };

  if (queue.isError || catalog.isError) {
    // ⛔ **[P-A](../../../../docs/DOMAIN_DISCOVERY_REGISTER.md): a page must say
    // when it could not find out.** An empty queue and an unreachable one are
    // different facts and must never render the same.
    return (
      <ErrorState
        title="The queue could not be loaded"
        description="Signora could not reach the signal service. Nothing has been lost — every signal is still waiting."
      />
    );
  }

  return (
    <section className="flex flex-col gap-6" aria-label="Signals">
      {/* 🔴 **§08's page header, and it is the APPROVED one** — 📁 `Design
          Documents/Fortune Signora Signal Center.html` draws the band as
          `h1` + counts on one baseline, then the description beneath:

          ```
          <div style="display:flex;align-items:baseline;gap:10px">
          <h1 style="font-size:25px;font-weight:700;…">Signals</h1>
          <span style="font-size:13px;color:var(--ink-3)">14 need review · …</span>
          </div>
          <div style="font-size:13px;color:var(--ink-2);margin-top:3px">Detected events…</div>
          ```

          ⛔ **This screen hand-rolled that band** — a local `<header>` with the
          title at `text-xl` and the count in a separate paragraph BELOW the
          description. ⚡ **`PageHeader` is that shape exactly**: §04's `Title`
          role, `titleMeta` on the title's baseline, `description` beneath —
          and 📁 [`/reports`](../reports/reports-screen.tsx) next door already
          uses it. **Shell rule 03's one-primary-action slot comes with it.**

          ⚠️ **The title text is unchanged and that was checked, not assumed**:
          the design's `<h1>` is *"Signals"*. **"Signal center" is the DESIGN
          DOCUMENT's own name, not the screen's heading** — and the description
          below already matches the design word for word. */}
      <PageHeader
        className="mb-0"
        title="Signals"
        // 📁 **Surface ⑦ — the counts, on the title's baseline.** The design
        // draws *"14 need review · 6 assigned to you · 41 this week"*.
        //
        // 🔴 **ONE of those three is publishable and the other two are absent
        // rather than approximated.** ⛔ **`QueueEntry` has no assignee** — so
        // *"assigned to you"* would be a number this screen invented — **and no
        // timestamp**, so *"this week"* has no clock to count against.
        // ⚡ **[§20c](../../../../CLAUDE.md): screens without a shipped module
        // behind them state the absence.** **The gap is
        // [C-292](../../../../docs/LANE_COORDINATION.md).**
        //
        // ⚠️ **Withheld entirely while the read is in flight** — a zero that
        // becomes thirteen is a false statement for as long as it shows.
        {...(open.isPending
          ? {}
          : {
              titleMeta: (
                <span data-testid="queue-counts">
                  <span className="font-medium text-content tabular-nums">
                    {open.data?.items.length ?? 0}
                  </span>
                  {' '}
                  need review
                </span>
              ),
            })}
        description="Detected events arrive continuously. Every one leaves the queue by being actioned, assigned, snoozed or dismissed with a reason."
      />

      <Tabs
        label="Queue state"
        idBase={QUEUE_TABS}
        items={STATES.map((tab) => ({
          value: tab.value,
          label: tab.label,
          // ⛔ **The count only when it is known.** A count rendered while the
          // read is pending would be a number the screen cannot support.
          badge: state === tab.value && !queue.isPending ? entries.length : undefined,
        }))}
        value={state}
        onChange={setState}
      />

      {/* ♿ **The panel those tabs control** — 📁 [B-1055](../../../../docs/BUGS.md).
          ⛔ **Six `role="tab"` on this screen and no `role="tabpanel"` anywhere in
          the document**: a screen-reader user was told *"tab, selected"* and given
          nothing to reach. ⚡ **The filters belong inside it**, because they narrow
          the selected state's queue and are meaningless without it — 🔴 **the panel
          is everything the tab changed, not just the list.**
          ⚠️ **The `gap-6` is the parent `<section>`'s**, carried in so that adding
          the wrapper does not close the spacing between its children. */}
      <TabPanel idBase={QUEUE_TABS} value={state} className="flex flex-col gap-6">
        {/* 📁 **Surface ② — the filter chips and *"14 of 22 shown"*.**
            ⛔ **Rendered only when there is more than one type to choose
            between**: a single chip that cannot narrow anything is a control
            that does nothing ([§2](../../../../CLAUDE.md)). */}
        {availableTypes.length > 1 ? (
          <div className="flex flex-wrap items-center gap-2" data-testid="signal-filters">
            <span className="text-2xs uppercase tracking-wide text-content-subtle">
              Filter
            </span>
            {availableTypes.map(([type, count]) => {
              const on = types.has(type);
              return (
                <button
                  key={type}
                  type="button"
                  onClick={() => toggleType(type)}
                  // ♿ **`aria-pressed`, not a styled `div`.** A chip that only
                  // looks selected is unselected to a screen reader.
                  aria-pressed={on}
                  className={cn(
                    'flex h-7 items-center gap-1.5 rounded-full border px-3 text-2xs transition-colors',
                    on
                      ? 'border-accent bg-accent-subtle font-semibold text-accent'
                      : 'border-border text-content-muted hover:bg-surface-sunken hover:text-content',
                  )}
                >
                  {titleFor(type)}
                  <span className="tabular-nums">{count}</span>
                </button>
              );
            })}
            {types.size > 0 ? (
              <>
                {/* 📁 The design's *"14 of 22 shown"*, and ⚡ **both numbers are
                    counted rather than claimed.** */}
                <span className="tabular-nums text-2xs text-content-subtle">
                  {entries.length} of {all.length} shown
                </span>
                {/* ⛔ **The way back is always offered.** ⚠️ A narrowing a reader
                    cannot undo in one action is how an empty list gets reported
                    as missing data. */}
                <button
                  type="button"
                  onClick={() => setTypes(new Set())}
                  className="rounded text-2xs text-accent underline decoration-border underline-offset-4 transition-colors hover:decoration-accent "
                >
                  Clear
                </button>
              </>
            ) : null}
          </div>
        ) : null}

        {/* 📁 **Surface ③'s action bar** — the design's *"✓ 3 selected"*.
            ⛔ **Present only when something is selected**, and ♿ **`role="status"`**
            so a screen-reader user learns the count changed without being
            interrupted mid-row. */}
        {selected.size > 0 ? (
          <div
            role="status"
            data-testid="bulk-bar"
            className="flex flex-wrap items-center gap-3 rounded-lg border border-accent bg-accent-subtle px-4 py-2.5"
          >
            <span className="text-sm font-medium text-accent tabular-nums">
              {selected.size} selected
            </span>
            <Button variant="secondary" onClick={() => decideMany({ kind: 'actioned' })}>
              Mark actioned
            </Button>
            {/* 🔴 **CORRECTED — two of the three reasons given here have
                expired, and one was never the real one.**

                📁 The design's `bulkActions` are ***Assign · Snooze · Dismiss ·
                Bookmark*** — ⚠️ **and notably NOT *Act on it***, which is the one
                this bar ships. **The design's bulk set and ours barely overlap.**

                ⛔ **This comment said bulk snooze was impossible because *"this
                screen has no per-row snooze to borrow a duration from"*. It has
                one now**, and bulk assign is a single person for a selection —
                exactly what the design draws. ⚡ **So the remaining reason is
                SCOPE, not the contract**, and saying otherwise would be the
                false-claim class ([§2](../../../../CLAUDE.md)).

                ✅ **Bulk dismissal's reason still holds and is a product
                argument**: *"one reason typed once for eleven signals is the
                reason nobody can cite later."* ⛔ **`Bookmark` has no producer at
                all.** **The bulk gap is
                [C-292](../../../../docs/LANE_COORDINATION.md).** */}
            <button
              type="button"
              onClick={() => setSelected(new Set())}
              className="ml-auto rounded text-2xs text-accent underline decoration-border underline-offset-4 "
            >
              Clear selection
            </button>
          </div>
        ) : null}

        {/* 🔴 **A refused write must say so, and this screen said nothing.**
            ⛔ ***Act on it*** **and the bulk bar call the API with no dialog to
            report into**, so a failure left the row exactly where it was with no
            explanation — **the reader's only evidence that anything happened at
            all is the row moving, and it did not.**
            ⚡ **Suppressed while a dialog is open**, because a modal makes
            everything behind it unreachable: 📁 `dialog.tsx` — *"`showModal()`
            makes background content inert"* — **and an alert nobody can reach is
            an alert nobody gets.** Each dialog carries its own. */}
        {resolve.isError &&
        assigning === null &&
        snoozing === null &&
        dismissing === null ? (
          <p
            role="alert"
            data-testid="resolve-refusal"
            className="rounded-lg border border-danger bg-danger-subtle px-4 py-2.5 text-sm text-danger"
          >
            {refusal(resolve.error)}
          </p>
        ) : null}

        {/* ♿ **The wait is announced** — 📁 [B-1057](../../../../docs/BUGS.md).
            ⛔ **These skeletons stay `aria-hidden` and the region says the
            sentence**: QE held this exact read open for 12s and found
            `aria-busy` nowhere and both live regions empty. ⚡ **The region
            wraps all three branches**, because one that unmounted with the
            placeholders could never announce the settle. */}
        <LoadingRegion label="the signal queue" busy={queue.isPending}>
        {queue.isPending ? (
          <div className="flex flex-col gap-3" aria-hidden>
            <Skeleton className="h-16" />
            <Skeleton className="h-16" />
            <Skeleton className="h-16" />
          </div>
        ) : entries.length === 0 ? (
          /* ⚡ **A quiet queue is a success state and must read as one** — the
             design's own rule on the neighbouring screen. */
          <EmptyState
            title={state === 'open' ? 'Nothing needs review' : 'Nothing here'}
            description={
              state === 'open'
                ? 'Every signal Signora raised has been actioned, assigned, snoozed or dismissed.'
                : 'No signals are in this state.'
            }
          />
        ) : (
          <div className="flex flex-col gap-6">
            {groups.map(([type, rows]) => (
              <div key={type} className="flex flex-col gap-2">
                <h2 className="flex items-center gap-2 text-sm font-medium text-content">
                  {titleFor(type)}
                  <span className="tabular-nums text-content-subtle">{rows.length}</span>
                </h2>

                <ul className="flex flex-col gap-2">
                  {rows.map((entry) => {
                    const identity = identities.data?.get(entry.entity_id) ?? null;
                    return (
                      /* 🔴 **📁 The design's keyboard grammar — *"E assigns · S
                         snoozes · D dismisses"*.**

                         ⛔ **Scoped to the row the keyboard is ON, not bound to
                         the window.** ⚠️ **The design's grammar assumes a *current
                         row* — its rows carry `current` — and this queue has no
                         such cursor**, because 📁 *"J / K moves"* and *"⏎ opens"*
                         need the detail pane that is not built. **A global
                         single-letter key with no cursor would have no target and
                         would fire while somebody was typing a dismissal
                         reason.**

                         ✅ **Focus IS the cursor here**, and it is the one every
                         keyboard and screen-reader user already has: tab into a
                         row, press `E`. ⚡ **Registered as `partial` with that
                         limit in
                         [`shortcuts.ts`](../../../lib/shell/shortcuts.ts)** —
                         📁 [B-239](../../../../docs/BUGS.md)'s rule is that **a
                         live key omitted from the reference misleads exactly as
                         much as a dead one listed.** */
                      <li
                        key={entry.signal_id}
                        onKeyDown={(event) => {
                          if (entry.state !== 'open') return;
                          if (event.metaKey || event.ctrlKey || event.altKey) return;
                          // ⛔ **Never while somebody is typing.** 📁 The same
                          // guard every single-letter binding in this product
                          // carries — `shortcuts.ts`: *"a single-letter binding
                          // that fired inside a text field would be the shape
                          // that makes people distrust every shortcut."*
                          //
                          // ⚠️ **A CHECKBOX is not typing, and excluding every
                          // `<input>` would have broken the feature rather than
                          // guarded it** — 🔴 **the row's first focusable element
                          // IS the selection checkbox**, so a tag-name test would
                          // have made `E` dead exactly where a keyboard user
                          // arrives. **Found by the test, not by the diff.**
                          const target = event.target as HTMLElement;
                          if (target.isContentEditable) return;
                          if (/^(SELECT|TEXTAREA)$/.test(target.tagName)) return;
                          if (
                            target instanceof HTMLInputElement &&
                            !/^(checkbox|radio|button|submit|reset)$/.test(target.type)
                          ) {
                            return;
                          }
                          const key = event.key.toLowerCase();
                          if (key !== 'e' && key !== 's' && key !== 'd') return;
                          event.preventDefault();
                          if (key === 'e') setAssigning(entry);
                          else if (key === 's') setSnoozing(entry);
                          else setDismissing(entry);
                        }}
                      >
                        <Card className="flex flex-wrap items-start justify-between gap-3 p-4">
                          {/* 📁 **Surface ③'s per-row control.**
                              ♿ **A real `<input type="checkbox">`**, not a styled
                              button: ⛔ **it is what gives a screen reader the
                              checked state, the group semantics and the shift-
                              click behaviour a reader already knows** — and
                              reimplementing those is the workflow-local
                              reimplementation [498](../../../../docs/architecture/498-common-platform-audit.md)
                              found once already on this very screen's tabs.
                              ⚡ **The label names the SIGNAL, never *"select"***,
                              so somebody hearing the row hears what they are
                              about to act on. */}
                          {/* ♿ 📁 **Design System v2 §17 `2.5.8`** — *"Targets ≥
                              24px."* ⚠️ **Measured at `16 × 16`** on every row of
                              the queue. ⛔ **The VISUAL stays at the design's
                              size and the TARGET grows** — a wrapping `<label>`
                              forwards the click and costs no new component,
                              which is the pattern the Companies table and the
                              Columns panel already use. */}
                          <label className="mt-0.5 flex min-h-6 min-w-6 shrink-0 cursor-pointer items-center justify-center coarse:min-h-11 coarse:min-w-11">
                            <input
                              type="checkbox"
                              checked={selected.has(entry.signal_id)}
                              onChange={() => toggleSelected(entry.signal_id)}
                              aria-label={`Select ${titleFor(entry.signal_type)}`}
                              className="h-4 w-4 shrink-0 accent-accent "
                            />
                          </label>
                          <div className="flex min-w-0 flex-col gap-1">
                            <span className="text-sm font-medium text-content">
                              {titleFor(entry.signal_type)}
                            </span>
                            {/* ⚠️ **Nullable by design** — *"`name` is null when
                                nobody has named the account"*. ⛔ The id is not
                                printed as a fallback: an id is not a name, and a
                                seller cannot act on one. */}
                            {/* 🔴 **B-290** — ⛔ the identity read settles after
                                the queue does, so this rendered its fallback as an
                                answer and then replaced it. */}
                            {/* 🔴 **The queue's exit into the record** — 📁 the
                                Experience Map: *"the monitoring loop enters at
                                the queue, **exits into accounts**"*, and Account
                                360 lists **signal** among its five entries.
                                ⛔ **This was plain text**: a triager could
                                disposition a signal and had no way to open the
                                company it was about. */}
                            <AccountName
                              name={identity?.name ?? null}
                              pending={identities.isPending}
                              absent="Unnamed account"
                              href={`/accounts/${entry.entity_id}`}
                              className="w-fit text-sm text-content-muted"
                            />
                            {/* 🔴 **Per signal, never per type.** The catalog's
                                `why_it_matters` describes the TYPE and would read
                                as right under all fifty rows; `rationale` is
                                authored where the reasoning happened.
                                ⛔ **Not recomposed here** — the interpretation a
                                customer reads and the evidence an auditor checks
                                must not diverge, so this renders the sentence and
                                composes nothing.
                                📱 **Clamped to two lines and complete in the DOM**:
                                the full text stays readable to assistive tech and
                                on hover, because a truncated reason that reads as
                                the whole reason is worse than none. */}
                            <p
                              className="line-clamp-2 text-sm leading-6 text-content-muted"
                              title={entry.rationale}
                            >
                              {entry.rationale}
                            </p>
                          </div>

                          {entry.state === 'open' ? (
                            <div className="flex flex-wrap items-center gap-2">
                              {/* 🔴 **Assigning does not close a signal, and the
                                  row has to say so** — 📁 `resolution.py`:
                                *"**Still open.** Assigning is routing, not
                                  resolving, and a queue that treated it as an
                                  ending would lose every signal handed to a
                                  colleague."*
                                  ⛔ **Without this chip, pressing *Assign* would
                                  visibly do nothing** — the row stays exactly
                                  where it was — **and a control whose effect is
                                  invisible is indistinguishable from one that is
                                  not wired up.** 📁 The design draws it as a row
                                  state: *"Assigned · JO"*.
                                  ⚡ **`nameOf` is the product's one resolution of
                                  an identifier**, so the picker, this chip and
                                  the account trail cannot describe three
                                  different people. */}
                              {entry.resolution?.outcome === 'assigned' &&
                              entry.resolution.assigned_to !== null ? (
                                <Badge tone="info">
                                  Assigned to{' '}
                                  {nameOf(entry.resolution.assigned_to, people, viewerId)}
                                </Badge>
                              ) : null}
                              {/* 📁 **The design's `detailActions`, in the
                                  design's order** — *Assign · Snooze · Bookmark ·
                                  Dismiss · **Act on it*** (primary last).
                                  ⛔ **`Bookmark` is absent**: nothing in the
                                  contract stores one, and it is
                                  [C-292](../../../../docs/LANE_COORDINATION.md).
                                  ⚠️ **They are on the ROW because the detail pane
                                  the design puts them in is not built** — the two
                                  that already existed were placed here on the
                                  same reasoning, and splitting one action group
                                  across two conventions would be worse than
                                  either. */}
                              <Button
                                size="sm"
                                variant="secondary"
                                onClick={() => setAssigning(entry)}
                                disabled={resolve.isPending}
                              >
                                Assign
                              </Button>
                              <Button
                                size="sm"
                                variant="secondary"
                                onClick={() => setSnoozing(entry)}
                                disabled={resolve.isPending}
                              >
                                Snooze
                              </Button>
                              <Button
                                size="sm"
                                variant="secondary"
                                onClick={() => setDismissing(entry)}
                                disabled={resolve.isPending}
                              >
                                Dismiss
                              </Button>
                              {/* 📁 ***"Act on it"*** — the design's own label
                                  for the button. ⛔ **This read *"Actioned"***,
                                  which is the design's name for the resulting
                                  STATE — 📁 its history tabs are *All · Actioned ·
                                  Dismissed · Snoozed*. **A button labelled with an
                                  outcome reads as a filter.** */}
                              <Button
                                size="sm"
                                onClick={() => decide(entry, { kind: 'actioned' })}
                                disabled={resolve.isPending}
                              >
                                Act on it
                              </Button>
                            </div>
                          ) : (
                            /* 🔴 **A snoozed row says WHEN it comes back.**
                               📁 `Resolution` publishes `snoozed_until`, and the
                               design draws the return on the row — *"Snoozed ·
                               2d"*. ⛔ **This printed the bare word `snoozed`**,
                               which told a reader the one thing they already knew
                               from the tab they were standing on.
                               ⚡ **`formatDay` rather than a countdown**: the
                               product writes days, and *"2d"* would need a clock
                               this row re-reads. */
                            <Badge>
                              {entry.resolution?.outcome === 'snoozed' &&
                              entry.resolution.snoozed_until !== null
                                ? `Returns ${formatDay(entry.resolution.snoozed_until)}`
                                : (entry.resolution?.outcome ?? entry.state)}
                            </Badge>
                          )}
                        </Card>
                      </li>
                    );
                  })}
                </ul>
              </div>
            ))}
          </div>
        )}
        </LoadingRegion>
      </TabPanel>

      {/* 🔴 **📁 *"Assign to someone"*** — the design's second exit, and the
          first control the product has ever had for it.

          ⚠️ **`Assigned` keeps the signal open**, so this dialog's question is
        *who owns the decision*, not *how does this end*. */}
      <Dialog
        open={assigning !== null}
        onClose={closeAssign}
        title="Who should decide this?"
        description="Assigning routes the signal without closing it — it stays in the queue under their name until somebody acts."
        footer={
          <div className="flex flex-wrap items-center gap-3">
            <Button
              // ⛔ **No default, and the placeholder is not a person.** ⚡ The
              // same rule 📁 [`workflow.tsx`](../../../components/intelligence/workflow.tsx)
              // states for a hand-over: *"the first colleague in a list is not
              // a guess, it is a person"* — so the confirm stays disabled until
              // somebody is named.
              disabled={assignTo === null || resolve.isPending}
              onClick={() => {
                if (assigning === null || assignTo === null) return;
                decide(assigning, { kind: 'assigned', to: assignTo }, closeAssign);
              }}
            >
              {resolve.isPending ? 'Assigning…' : 'Assign signal'}
            </Button>
            <Button variant="secondary" onClick={closeAssign}>
              Cancel
            </Button>
          </div>
        }
      >
        {/* ⛔ **An empty roster is a stated absence, never an empty picker.**
            📁 `colleaguesFrom` returns only members whose membership carries an
            address (TM-01), so a workspace of one — or one whose colleagues
            were all added by identifier — has nobody to offer. ⚡ **Saying so
            beats a `<select>` with one unselectable row in it.** */}
        {colleagues.length === 0 ? (
          <p className="text-sm leading-6 text-content-muted">
            There is nobody else here to assign this to yet. Invite a colleague from
            Settings, and they will appear in this list.
          </p>
        ) : (
          <Select
            label="Colleague"
            value={assignTo ?? ''}
            onChange={(event) => setAssignTo(event.target.value || null)}
            options={[
              { value: '', label: 'Choose a colleague' },
              ...colleagues.map((one) => ({ value: one.id, label: one.name })),
            ]}
          />
        )}
        {resolve.isError ? (
          <p role="alert" className="mt-3 text-sm text-danger">
            {refusal(resolve.error)}
          </p>
        ) : null}
      </Dialog>

      {/* 🔴 **📁 *"Snooze with a date"*** — and 📁 the design's own note on what
          that costs: ***"Snooze is a commitment. A snooze needs a date and a
          reason. The signal returns with its original evidence and a note that
          it was deferred once already."***

          ⛔ **The REASON half is not built, and it is not collected either.**
          ⚠️ **`ResolveOutcome`'s `snoozed` carries `until` and nothing else**,
          and `Resolution.reason` is documented *"present only on a dismissal,
          where it is required"* — **so a reason typed here would be discarded
          on the way to the API**, which is worse than not asking: it takes
          something from a customer and drops it. ✅ **The date is asked for;
          the reason is [C-292](../../../../docs/LANE_COORDINATION.md).**

          ⛔ **The *"deferred once already"* note is absent for the same
          reason** — nothing counts prior snoozes. */}
      <Dialog
        open={snoozing !== null}
        onClose={closeSnooze}
        title="When should this come back?"
        description="Snoozed signals return at the stated time with their original evidence intact — nothing about the signal is touched while it waits."
        footer={
          <div className="flex flex-wrap items-center gap-3">
            <Button
              // ⛔ **Cannot submit a date that has already gone.** The domain
              // refuses it — *"the signal would come straight back"* — and the
              // control refuses it first.
              disabled={snoozeUntil < earliestSnooze() || resolve.isPending}
              onClick={() => {
                if (snoozing === null || snoozeUntil === '') return;
                decide(
                  snoozing,
                  { kind: 'snoozed', until: returnsAt(snoozeUntil) },
                  closeSnooze,
                );
              }}
            >
              {resolve.isPending ? 'Snoozing…' : 'Snooze signal'}
            </Button>
            <Button variant="secondary" onClick={closeSnooze}>
              Cancel
            </Button>
          </div>
        }
      >
        <Input
          label="Comes back on"
          type="date"
          value={snoozeUntil}
          min={earliestSnooze()}
          onChange={(event) => setSnoozeUntil(event.target.value)}
          hint="It returns at the start of that day, wherever you are."
        />
        {resolve.isError ? (
          <p role="alert" className="mt-3 text-sm text-danger">
            {refusal(resolve.error)}
          </p>
        ) : null}
      </Dialog>

      <Dialog
        open={dismissing !== null}
        onClose={closeDismiss}
        title="Why is this not worth acting on?"
        description="Dismissal reasons feed rule precision — a rule dismissed often enough is proposed for retuning."
        footer={
          <div className="flex flex-wrap items-center gap-3">
            <Button
              // ⛔ **Cannot submit an empty reason.** The type makes a
              // reasonless dismissal unconstructable; this keeps that true at
              // the edge rather than relying on the server to refuse it.
              disabled={reason.trim().length < MIN_REASON || resolve.isPending}
              onClick={() => {
                if (dismissing === null) return;
                decide(
                  dismissing,
                  { kind: 'dismissed', reason: reason.trim() },
                  closeDismiss,
                );
              }}
            >
              {resolve.isPending ? 'Dismissing…' : 'Dismiss signal'}
            </Button>
            <Button variant="secondary" onClick={closeDismiss}>
              Cancel
            </Button>
          </div>
        }
      >
        {/* 🔴 **Free text, and the design asks for a closed list — read the
            header before changing this.** 📁 `Signal Center` `mechanics`:
            *"every dismissal takes a reason from a closed list."*

            ⛔ **`domain/resolution.py` refuses to invent that list**, and a
            `<Select>` here would be the same invention one layer up: *"a
            vocabulary of dismissal reasons is a product decision about what the
            platform believes can be wrong with its own judgement."*

            ⚡ **The placeholder is an EXEMPLAR, not an option** — the design's
            own history row shows *"Not a buying signal"* the same way. */}
        <Input
          label="Reason"
          value={reason}
          onChange={(event) => setReason(event.target.value)}
          placeholder="Already handled on the call"
        />
        {resolve.isError ? (
          <p role="alert" className="mt-3 text-sm text-danger">
            {refusal(resolve.error)}
          </p>
        ) : null}
      </Dialog>
    </section>
  );
}
