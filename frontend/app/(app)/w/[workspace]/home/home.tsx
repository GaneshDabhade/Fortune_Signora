'use client';

import { Home as HomeIcon } from 'lucide-react';
import { useEffect, useRef } from 'react';

import { StatedAbsence } from '@/components/feedback/stated-absence';
import { cn } from '@/lib/design/cn';
import {
  ConnectCallsCard,
  ConnectCrmCard,
  InviteTheTeamCard,
} from '@/components/home/activation-cards';
import { ActivationProgress } from '@/components/home/activation-progress';
import { AgentQueueCard, AgentRunsCard } from '@/components/home/agent-cards';
import { AttentionCard } from '@/components/home/attention-card';
import { FirstRunOverlay } from '@/components/home/first-run-overlay';
import { CompositionSwitcher } from '@/components/home/composition-switcher';
import { HomeGreeting } from '@/components/home/greeting';
import { IntegrationHealthCard } from '@/components/home/integration-health-card';
import { PipelineHealthCard } from '@/components/home/pipeline-health-card';
import { RecentsCard } from '@/components/home/recents-card';
import { TopOpportunitiesCard, TopRisksCard } from '@/components/home/posture-cards';
import { NoDataStrip } from '@/components/home/no-data-strip';
import { SetupCompleteStrip } from '@/components/home/setup-complete-strip';
import { SourceStrip } from '@/components/home/source-strip';
import { HM_COPY_11 } from '@/lib/home/copy';
import { cardsFor, type CardContract } from '@/lib/home/cards';
import { resolveComposition } from '@/lib/home/composition';
import { useSession } from '@/lib/auth/client';
import { useAccountsCount } from '@/lib/query/hooks/accounts-count';
import { useActivationState, useStatedRole } from '@/lib/query/hooks/home';
import { useIntegrations } from '@/lib/query/hooks/integrations';
import { useWorkspaceTriage } from '@/lib/query/hooks/triage';
import { usePreferences } from '@/lib/query/hooks/preferences';
import { useViewerRole } from '@/lib/query/hooks/team';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';
import type { WorkspaceRole } from '@/lib/state/permissions';

/**
 * **Home — one route, four compositions** — 📁
 * `docs/design-snapshot/screens/Fortune Signora Home.dc.html`, the **composition
 * authority** ([D-138](../../../../../../docs/DECISION_REGISTER.md)).
 *
 * > 📁 ***"Home tells a person what to do next, using the workspace's own data,
 * > with a reason attached to every item. It is not a report, not a dashboard for
 * > its own sake, and not a menu."***
 *
 * ## 📁 The information hierarchy, in the design's fixed order
 *
 * | # | What | Here |
 * |---|---|---|
 * | 1 | Continuity offer | ⛔ **Session Continuity's, and it has no producer** — recorded below |
 * | 2 | Workspace confirmation strip | ✅ `SourceStrip` |
 * | 3 | Greeting and scope line | ✅ `HomeGreeting` |
 * | 4 | **The answer** | ✅ activation step one · ⛔ the briefing has no producer |
 * | 5 | **The work** | ✅ `AttentionCard`, five maximum |
 * | 6 | Context | ✅ `AgentQueueCard`, `RecentsCard` · ⛔ meetings has no producer |
 *
 * ## 🔴 Home always renders Home
 *
 * 📁 §03, and it is absolute: ***"An empty Home that redirects to the Attention
 * list, the account table, or any other surface produces an alternate Home that
 * no document describes, no test covers, and no person can predict."***
 *
 * ⛔ **There is no `router.push` in this file and there must never be one.**
 * ⚡ Contract item 3 asks a reviewer to grep for exactly that, and
 * `home-route.test.tsx` does it in a test so the grep is not a habit.
 *
 * ## ⚠️ Five of the design's sixteen cards have no producer, and none is faked
 *
 * **Measured against every API path the backend publishes, not inferred:**
 *
 * | Card | Dependency | Producer |
 * |---|---|---|
 * | `card.attention` · `card.pipeline` · `card.inthealth` · `card.activation.*` | signals · pipeline-health · integrations · members | ✅ **shipped** |
 * | `card.risks` · `card.opps` | `signals.risk` · `signals.opportunity` | ✅ **shipped** — partitioned by the posture `buying_score_engine` publishes |
 * | `card.recents` | `activity.mine` | ✅ **shipped** — Session Continuity tier 4 |
 * | `card.agentqueue` · `card.agentruns` | `agents.runs` | ✅ **shipped** — the research request IS the run |
 * | `card.briefing` · `card.execsummary` | `ai.briefing.v1` · `ai.execsummary` | ⛔ **no workspace-level AI endpoint** |
 * | `card.meetings` | `calendar.events` | ⛔ **a DEPENDENCY, not a gap** — every catalog entry is `connectable=False` and no meeting is modelled anywhere in the domain |
 * | `card.dataquality` · `card.requests` | `quality.summary` · `access.requests` | ⛔ **no endpoint** |
 * | `card.forecast` | `forecast.committed` | 🔴 **refused by domain law** — [C-1528](../../../../../../docs/LANE_COORDINATION.md) |
 *
 * ⚡ **The absent cards are absent, not stubbed.** 📁 [§20c](../../../../../../CLAUDE.md)
 * and the design's own non-goal: *"Sample or synthetic data to make an empty Home
 * look populated."* ⛔ **`card.forecast` is the one that can never arrive** —
 * `buying_score_engine` states *"it does not forecast a purchase"* in two files.
 *
 * ## ✅ The composition resolves fully now, and [C-268](../../../../../../docs/LANE_COORDINATION.md) is why it did not
 *
 * ⚠️ **This file said *"every reader resolves to `activation`"*** because no
 * primary role existed. ⚡ **Onboarding screen `05` collects it** — *"Role sets
 * the home page"* — so rules 3, 4 and 5 all reach their compositions.
 */
export function Home() {
  const { activeWorkspace, isLoading, error } = useWorkspaceContext();
  const workspaceId = activeWorkspace?.id ?? null;

  const { data: session } = useSession();
  /**
   * 🔴 **Presentational only.** 📁 The card contract: *"`requires` is
   * presentational… **This is not an authorization decision**"* — Casbin on the
   * server decides what may be read ([§20c](../../../../../../CLAUDE.md)).
   */
  const viewer = useViewerRole(workspaceId, session?.user.id ?? null);
  const role: WorkspaceRole | null = viewer.role;

  /**
   * 📁 **Rule 1's signal** — *"No integration has ever completed a sync."*
   *
   * ⚠️ **This used to read the target-account version and that was the wrong
   * question.** ⛔ A workspace can declare no target accounts and be fully
   * connected; the design's test is about *connection*. 📁 Content emptiness is
   * state `05`, which renders a role composition — **so conflating them sent a
   * set-up customer back to setup.**
   */
  const integrations = useIntegrations(workspaceId);
  const preferences = usePreferences(workspaceId);
  const statedRole = useStatedRole(workspaceId);
  /**
   * ⚡ **Read here as well as inside the attention card, and deliberately.** 📁
   * The greeting's scope line is *"a count of what needs attention"* — hierarchy
   * 3 — **so Home needs the number before any card resolves.** ⛔ One query key,
   * one request: React Query serves both readers from the same cache entry.
   *
   * ⚠️ **This was `useAccounts` — the Opportunity Engine's `AccountAttention`
   * list — until the product owner ruled it out of Home on 2026-08-17.** 📁 The
   * registry's dependency for `card.attention` is *"signals + deals"*, and the
   * open signal queue is the signals half. ⛔ **The count and the card must read
   * the SAME list**, or the scope line would promise a number the card below it
   * does not show.
   */
  const attention = useWorkspaceTriage(workspaceId, 'open');

  /**
   * ♿ **Focus lands on the h1, not the search field** — 📁 §10's keyboard table
   * and contract item 19. ⛔ **Once per mount**, so a card resolving later does
   * not steal focus from somebody already reading.
   */
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    heading.current?.focus();
  }, []);

  /**
   * 🔴 **[P-A](../../../../../../docs/DOMAIN_DISCOVERY_REGISTER.md): a failed read
   * must never render as an empty result.**
   *
   * ⛔ **Here an empty result would resolve a DIFFERENT COMPOSITION** — the
   * integrations read decides rule 1 — **so a failure does not merely show less,
   * it would show a customer the wrong Home.** ⚡ **Only the composition-deciding
   * reads gate the page**; every other card degrades inside its own footprint,
   * which is §08's whole point.
   */
  if (error !== null || integrations.isError) {
    return <StatedAbsence as="page" icon={HomeIcon} subject="your home" />;
  }

  /**
   * 📁 **State 07 — *"the greeting and scope line render immediately from session
   * data; only cards skeleton."***
   *
   * ⛔ **So this does NOT return early with a page-level placeholder.** ⚠️ The
   * previous version rendered *"Resolving your home…"* over the whole page, which
   * is the full-screen spinner the design refuses. ✅ **The frame paints and the
   * cards carry their own skeletons at their declared footprints.**
   */
  const resolving = isLoading || integrations.isPending;

  /**
   * 🔴 **States 01, 03, 04, 05 and 14 all read from here** — 📁 activation's
   * completion, derived from the source of truth and never stored on Home.
   *
   * ⚡ **Read on every composition, not only activation.** ⛔ States 04 and 14
   * are *data* compositions that need to know what activation did: 04 announces
   * that setup just finished, and 14 says the optional step is still outstanding.
   */
  const activationState = useActivationState(workspaceId);

  /**
   * 📁 **State 05's second half** — *"record count is zero"*. ⚡ **The
   * workspace's own count, not the loaded page's**: `accounts-list` is
   * keyset-paginated, so counting rows measures how much has been fetched.
   */
  const accounts = useAccountsCount(workspaceId);

  /**
   * ⚡ **`working` is *"at least one connection Signora can currently use"*.**
   * 📁 Rule 1 asks whether one has ever *completed a sync*, and a working
   * connection is the closest fact the contract publishes — ⚠️ **recorded because
   * they are not identical**: a connection that worked yesterday and is now
   * revoked is state `10`, not state `01`, and `SourceStrip` is what tells them
   * apart.
   */
  const systems = integrations.data ?? [];
  const everConnected = systems.some((s) => s.working || s.connections.length > 0);
  const neverSynced = !resolving && !everConnected;

  const composition = resolveComposition({
    neverSynced,
    preference: preferences.data?.home_composition ?? null,
    statedRole: statedRole.data ?? null,
  });

  const cards = cardsFor(composition, role);
  /** 📁 Whether any rendered card claims the design's wide column. */
  const hasWide = cards.some((card) => WIDE.has(card.id));
  const rendered = cards.filter((card) => RENDERERS[card.id] !== undefined);

  /**
   * 📁 **State 12 — *"the activation registry returned zero cards."*** ⛔ **The
   * design is explicit about what must NOT happen**: *"Never a progress bar at 0
   * of 0, and never an empty activation composition."*
   */
  const registryEmpty = composition === 'activation' && rendered.length === 0 && !resolving;

  /**
   * ⚠️ **A data composition that could compose nothing at all.**
   *
   * 📁 **§03 is absolute — *"Home always renders Home"*** — so this is a designed
   * state rather than a blank region. ⛔ **It cannot happen in production today**
   * (every data composition contains a card with a renderer), **and it is drawn
   * anyway**: 📁 the design bans *"any empty state that does not name what was
   * checked"*, and a composition that silently produced no DOM would be the
   * alternate Home §03 exists to forbid.
   */
  const nothingComposed = composition !== 'activation' && rendered.length === 0 && !resolving;

  return (
    /**
     * 📁 **Content capped at 1360px at every viewport above it, and no third
     * column at any breakpoint** — §09's responsive laws and contract item 21.
     * ⚡ *"Surplus width becomes margin, not a third column."*
     */
    /**
     * 🔴 **A `<div>`, not a second `<main>`.**
     *
     * ⚠️ **This rendered `<main>` and the App Shell already renders one** —
     * `<main id="shell-content">`, 📁 the App Shell document's *"the content
     * region. Receives focus on route change."* ⛔ **Two `main` landmarks in one
     * document is invalid**, and a screen reader offering *"main, 1 of 2"* is
     * the opposite of the single landmark 1.3.1 asks for.
     *
     * ✅ **📁 Home's *"Home is one `<main>` with an h1 naming the workspace"* is
     * SATISFIED, by the shell's.** ⚡ The two documents are not in conflict —
     * the shell owns the content region and Home fills it, which is 📁 Home's
     * own reconciliation: *"no second shell. Home occupies the content region
     * only."*
     *
     * 🔴 **Found by a browser, in `cold-boot-frame.spec.ts`**, which resolved
     * `main` to two elements the moment `/` started landing here.
     */
    <div className="mx-auto flex w-full max-w-[85rem] flex-col gap-4" data-testid="home" data-composition={composition}>
      {/* 📁 Hierarchy 1 and 2. ⚠️ The continuity offer is Session Continuity's
          and has no producer; the source strip is states 10 and 11. */}
      <SourceStrip systems={systems} loading={resolving} />

      {/* 📁 **State 04** — *"a one-time strip states that setup is finished and
          what changed"*. ⛔ **On the ROLE composition, never on activation**:
          the design's own render for 04 is *"composition switches to SELLER,
          OPERATIONS or EXECUTIVE"*. */}
      <SetupCompleteStrip
        workspaceId={workspaceId}
        complete={
          activationState.resolved &&
          activationState.progress.done === activationState.progress.total
        }
        activation={composition === 'activation'}
      />

      {/* 📁 **State 05** — *"one strip naming which source returned nothing"*.
          ⛔ **Not on activation**, which the design excludes by name, and ⛔ never
          the same component as state 06b (contract 4). */}
      <NoDataStrip
        systems={systems}
        accounts={accounts.data?.total ?? null}
        activation={composition === 'activation'}
        loading={resolving}
      />

      {/* 🔴 **Over whichever composition resolved, never instead of one** — 📁
          Entry rule 20 and Home's own words. ⛔ It is not a fifth composition. */}
      <FirstRunOverlay composition={composition} />

      {/* 📁 Hierarchy 3 — *"name, date, and a count of what needs attention"*,
          and the greeting is never skeletonised. */}
      <div className="flex flex-wrap items-end gap-3.5">
        <HomeGreeting
          ref={heading}
          name={session?.user.name ?? null}
          workspace={activeWorkspace?.name ?? null}
          composition={composition}
          compositionKnown={!resolving}
          attention={attention.data?.items.length ?? null}
          attentionFailed={attention.isError}
          meetings={null}
          /* 📁 **States 01 and 03**, and only on the activation composition —
             ⛔ every other composition greets by the clock. ⚡ **`null` until
             activation has resolved**, so the sentence never opens with *"let us
             get you connected"* to somebody who already has. */
          activation={
            composition === 'activation' && activationState.resolved
              ? { done: activationState.progress.done, total: activationState.progress.total }
              : null
          }
        />
        <CompositionSwitcher
          className="ml-auto"
          current={composition}
          statedRole={statedRole.data ?? null}
          workspaceId={workspaceId}
        />
      </div>

      {/* 📁 ***"Progress counts blocking cards only"***, activation only. */}
      {composition === 'activation' && !registryEmpty ? <ActivationProgress /> : null}

      {nothingComposed ? (
        <section
          aria-label="Your home"
          className="rounded-lg border border-border-soft bg-surface p-5 shadow-sm"
        >
          <p className="text-sm font-semibold text-content">
            Signora has nothing to put on your home yet
          </p>
          {/* ⛔ **Names what was checked**, which is the design's own credibility
              test for an empty state — and never *"coming soon"*. */}
          <p className="mt-1.5 text-xs leading-[1.5] text-content-muted">
            Home is composed from what each part of Signora publishes, and nothing it checked has a
            card for you today. Your accounts, signals and settings all work.
          </p>
        </section>
      ) : registryEmpty ? (
        /* 📁 State 12's copy, verbatim, with a retry and no progress bar. */
        <section
          aria-label="Setup steps"
          className="rounded-lg border border-border-soft bg-surface p-5 shadow-sm"
        >
          <p className="text-sm font-semibold text-content">{HM_COPY_11}</p>
          <button
            type="button"
            onClick={() => void integrations.refetch()}
            className="mt-3 inline-flex h-control-sm items-center rounded-md border border-border px-3 text-xs font-semibold text-content transition-colors hover:border-accent hover:text-accent focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
          >
            Try again
          </button>
        </section>
      ) : (
        /**
         * 📁 **Two columns, `1.45fr / 1fr`, 14px gap at the reference viewport**
         * — §09. ⛔ **One column below `laptop`**, which is where the design drops
         * the split rather than compressing it.
         *
         * 🔴 **The wide column is reserved only when a card actually claims
         * it** — 📁 the registry's footprints, and **found in a screenshot.**
         *
         * ⛔ **`[1.45fr_1fr]` was hard-coded**, and the only card in `WIDE` is
         * `card.attention`, which is **SELLER's**. ⚠️ **So the Executive
         * composition rendered every card crushed into the 1fr column against
         * 770px of empty space** — its own wide card, `card.forecast` at
         * *"1.4fr × 320px"*, is the one the domain refuses to produce
         * ([C-1528](../../../../../../docs/LANE_COORDINATION.md)), **so the
         * column it would have filled can never be filled.**
         *
         * ✅ **With no wide card present the columns are equal**, which is what
         * the registry asks for when everything remaining is `1fr` —
         * `card.pipeline`, `card.risks` and `card.opps` all are. 📁 **Contract
         * 21 still holds**: *"surplus width becomes margin, not a third
         * column"* — ⛔ **and an empty reserved column is neither.**
         */
        <div
          className={cn(
            'grid grid-cols-1 gap-3.5 laptop:items-start',
            hasWide ? 'laptop:grid-cols-[1.45fr_1fr]' : 'laptop:grid-cols-2',
          )}
        >
          {/**
           * 🔴 **Nothing is drawn until the composition is RESOLVED, and that is
           * a conformance rule rather than a preference.**
           *
           * ⛔ **The prohibition table forbids composition substitution**, and
           * 📁 §09's loading rule is *"each skeleton uses the card's declared
           * height… **so nothing reflows when data lands**"*. ⚠️ Rule 1's input
           * is a read, so until it lands the resolver falls through to rule 5 —
           * **and a brand-new workspace's first paint was the SELLER
           * composition's five cards, replaced a moment later by the three
           * activation steps.** ⚡ **Measured in a browser**, not reasoned about:
           * the composition attribute read `seller` before the integrations
           * response arrived.
           *
           * ✅ **One placeholder at the answer card's footprint** — 📁 hierarchy
           * 4, *"one card that states what to do first"*, which every composition
           * has. ⛔ **Not the default composition's card list**, because that is
           * the substitution itself.
           */}
          {resolving ? (
            <div
              aria-hidden
              data-testid="home-resolving"
              className="h-[164px] animate-pulse rounded-lg border border-border-soft bg-surface-sunken"
            />
          ) : null}
          {resolving ? null : rendered.map((card) => {
            const Card = RENDERERS[card.id];
            if (Card === undefined) return null;
            return (
              /**
               * ♿ **Each card is a `<section>` with its own heading** — 📁 1.3.1
               * and contract item 19. ⚡ **DOM order is visual order**, which is
               * why the grid places rather than reorders.
               */
              <section
                key={card.id}
                data-card={card.id}
                aria-label={card.title}
                /**
                 * 🔴 **`col-start-2` is a PIN, and it was unconditional.**
                 *
                 * ⛔ **Every card that is not in `WIDE` was pinned to column
                 * two** — which is right while `card.attention` holds column
                 * one, and **wrong for every composition that has no wide card
                 * at all.** ⚠️ **The Executive composition has none**, so all
                 * three of its cards stacked in the right-hand column against
                 * an empty left one. **Widening the template did not fix it;
                 * the pin did.**
                 *
                 * ✅ **With no wide card the cards simply FLOW**, filling both
                 * equal columns in DOM order — 📁 which is the order the design
                 * ranks them in, and *"DOM order is visual order"* above.
                 */
                className={
                  FULL.has(card.id)
                    ? 'laptop:col-span-2'
                    : WIDE.has(card.id)
                      ? 'laptop:col-start-1'
                      : hasWide
                        ? 'laptop:col-start-2'
                        : undefined
                }
              >
                <Card />
              </section>
            );
          })}
        </div>
      )}
    </div>
  );
}

/**
 * 📁 **The design's footprints, reduced to which column a card takes.**
 *
 * ⚡ `card.attention` is *"1.45fr × auto"* and `card.pipeline` *"1fr × 320px"* —
 * ⛔ **so the wide column is not a preference, it is the registry's own
 * `footprint` field.** ⚠️ **A card absent from this set takes the narrow
 * column**, which is the design's default for everything in the right-hand
 * stack.
 */
const WIDE: ReadonlySet<CardContract['id']> = new Set([
  'needs-you-today',
]);

/**
 * 📁 **The registry's `full × auto` footprint.**
 *
 * 🔴 **Found in a screenshot, not by a gate.** ⛔ The activation cards were
 * placed in the `1.45fr` column and rendered against a column of empty space —
 * 📁 **the registry gives every activation card and both AI summaries `full ×
 * auto`**, and *"full"* is the content region rather than the wide column.
 */
const FULL: ReadonlySet<CardContract['id']> = new Set([
  'connect-a-crm',
  'connect-calls',
  'invite-the-team',
  'daily-briefing',
  'ai-executive-summary',
]);

/**
 * 🔴 **The seam a card needs and `CardContract` does not carry.**
 *
 * 📁 The contract is metadata only — *"a contract carrying layout, width or
 * position would be the module deciding something Home owns"* — ⛔ so it
 * publishes no component, and this map belongs to **Home**.
 *
 * ⚠️ **A card appears here only when it can be RENDERED.** The catalogue is
 * written ahead of the cards, and a registered card with no renderer would draw
 * a hole — which is why `Home` filters on this map rather than on `REGISTRY`.
 */
const RENDERERS: Readonly<Partial<Record<CardContract['id'], () => React.ReactElement | null>>> =
  Object.freeze({
    'needs-you-today': AttentionCard,
    'pipeline-health': PipelineHealthCard,
    'integration-health': IntegrationHealthCard,
    recents: RecentsCard,
    // 📁 The Executive composition's two ranked lists, partitioned from one
    // queue by the posture the Buying Score Engine publishes.
    'top-risks': TopRisksCard,
    'top-opportunities': TopOpportunitiesCard,
    // 📁 Both read `agents.runs` — the queue takes the runs with something to
    // read, the runs card ranks every run failures first.
    'agent-queue': AgentQueueCard,
    'agent-runs': AgentRunsCard,
    'connect-a-crm': ConnectCrmCard,
    'connect-calls': ConnectCallsCard,
    'invite-the-team': InviteTheTeamCard,
  });
