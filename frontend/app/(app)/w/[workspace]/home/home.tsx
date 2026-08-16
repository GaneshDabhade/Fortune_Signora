'use client';

import { Home as HomeIcon } from 'lucide-react';

import type { ReactElement } from 'react';

import { EmptyState, PageHeader } from '@/components/ui';
import { PipelineHealthCard } from '@/components/home/pipeline-health-card';
import {
  ConnectCallsCard,
  ConnectCrmCard,
  InviteTheTeamCard,
} from '@/components/home/activation-cards';
import { FirstRunOverlay } from '@/components/home/first-run-overlay';
import { ActivationProgress } from '@/components/home/activation-progress';
import { StatedAbsence } from '@/components/feedback/stated-absence';
import { cardsFor, type CardContract } from '@/lib/home/cards';
import {
  COMPOSITION_NAME,
  COMPOSITION_QUESTION,
  resolveComposition,
} from '@/lib/home/composition';
import { useSession } from '@/lib/auth/client';
import { useTargetAccounts } from '@/lib/query/hooks/commercial';
import { useViewerRole } from '@/lib/query/hooks/team';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';
import type { WorkspaceRole } from '@/lib/state/permissions';

/**
 * **Home — one route, four compositions** —
 * [TASK-1405](../../../../../../docs/BACKLOG.md), against
 * `docs/design-snapshot/screens/Fortune Signora Authenticated Entry.dc.html`
 * ([D-138](../../../../../../docs/DECISION_REGISTER.md)).
 *
 * > 📁 ***"Every authenticated person lands on `/w/:workspace/home`. What
 * > renders there is resolved from their role, and the resolution is a
 * > composition of cards from a shared catalogue — not a separate screen with
 * > its own layout, navigation or breadcrumb."***
 *
 * ## 🔴 The two halves were built months apart and had never met
 *
 * ✅ **[`resolveComposition`](../../../../../lib/home/composition.ts) shipped
 * with this row's first half and [`cardsFor`](../../../../../lib/home/cards.ts)
 * with [TASK-1406](../../../../../../docs/BACKLOG.md)** — ⛔ **and
 * `git grep resolveComposition` returned **zero** callers before this file.**
 * ⚡ **Both were on `main`, correct, tested and unreachable**, which is the same
 * shape [TASK-1460](../../../../../../docs/BACKLOG.md)'s column primitives and
 * [C-291](../../../../../../docs/LANE_COORDINATION.md)'s Saved View store have.
 * ⚠️ **Named rather than spelled**: `library-reachability` counts an identifier
 * in a COMMENT as a caller, so writing it here would have quietly marked an
 * orphan reachable — the same trap [TASK-1461](../../../../../../docs/BACKLOG.md)
 * hit with `MobileNavigation`.
 * **This is the caller.**
 *
 * ## ⛔ The route rendered the attention list, and that was correct until now
 *
 * 📁 **[TASK-1438](../../../../../../docs/BACKLOG.md) made this path
 * `export { default } from '../../../page'`** so the entry engine's **eight
 * rules — including 24, the default** — stopped answering 404. ⚠️ **Its own
 * comment named the successor**: *"Home's COMPOSITION is TASK-1405's resolver…
 * inventing a composition here would be a third answer to what Home shows."*
 * ✅ **So this replaces a placeholder that said it was one.**
 *
 * ## 🔴 What renders today, honestly
 *
 * ⚡ **`primaryRole` is `null` on every session the platform can produce** — the
 * design resolves a composition from *"the person's primary role"* and
 * `Membership.role` is `owner | member` — **so every reader resolves to
 * `activation`**, which is the one composition that is honest about knowing
 * nothing. ⛔ **That is the resolver's decision, not this file's**, and it is
 * why nothing here branches on a role.
 *
 * ⚠️ **`REGISTRY` held NOTHING when this file was written and holds TWO now** —
 * `connect-calls` and `pipeline-health`, contributed by
 * [TASK-1425](../../../../../../docs/BACKLOG.md). 🔴 **This line said *"`REGISTRY`
 * is empty"* until 2026-08-16 and it was read as current**: it nearly cost Lane
 * C a verification, because **this is the file somebody opens to decide whether
 * Home can replace `/`.** ⛔ **A doc-comment that was true when written and
 * asserts a state the code has left is the [B-252](../../../../../../docs/BUGS.md)
 * class**, and an enumeration is the shape most likely to go stale.
 *
 * ✅ **The reasoning below is unchanged and still governs**: **where the
 * resolver's composition contributes no renderable card, Home renders its
 * question and says what is missing** — 📁 the row's own words,
 * *"an empty Home is a designed state, not a failure"* — and
 * [§20c](../../../../../../CLAUDE.md): **a screen with no shipped module behind
 * it ships a designed empty state, never invented cards.**
 *
 * > 🔴 **This is a REGRESSION for the default landing destination and it is
 * > reported rather than absorbed** — [C-295](../../../../../../docs/LANE_COORDINATION.md).
 * > **The attention list was a better screen than an empty Home**, and the cause
 * > is an empty registry rather than anything in this row. ⚡ **Three of
 * > `activation`'s five cards — `connect-a-crm`, `invite-the-team`,
 * > `connect-calls` — are ALREADY BUILT** as §18's checklist from
 * > [TASK-1463](../../../../../../docs/BACKLOG.md), **and registering them is a
 * > follow-up row rather than this one's to take.**
 */

/**
 * 🔴 **The seam a card needs and `CardContract` does not carry.**
 *
 * 📁 **The contract is deliberately metadata only** — *"a contract carrying
 * layout, width or position would be the module deciding something Home owns"*
 * — ⛔ **so it publishes no component, and something must map an id to what
 * renders.**
 *
 * ⚡ **That map belongs to HOME rather than to the contract**, which is the same
 * boundary the design draws: 📁 *"Home owns the composition; the module owns
 * the card's content."* **A `component` field on `CardContract` would let a
 * module hand Home a node and decide its own placement.**
 *
 * ⛔ **Empty, and it stays empty until a module ships a card.** ⚠️ **A renderer
 * registered here for a card absent from `REGISTRY` would never be reached**,
 * and one registered for a card that has no component is exactly the
 * placeholder [TASK-1433](../../../../../../docs/BACKLOG.md) refused.
 */
/**
 * ⚠️ **`ReactElement | null`, and the `null` is the design's rather than a
 * convenience** — [TASK-1424](../../../../../../docs/BACKLOG.md).
 *
 * ⛔ **Most cards must NEVER return nothing**: 📁 *"cards degrade individually…
 * the composition never changes shape because one card has nothing"*, so an
 * empty read is an empty STATE and not an absent card.
 *
 * ✅ **Exactly one case is different, and the design names it**: *"non-blocking
 * cards can be skipped, which HIDES them for 30 days."* ⚡ **A skipped card is
 * gone, not empty** — that is what skipping means — **so the type has to allow
 * it, and the comment has to say which case it is for.**
 */
const RENDERERS: Readonly<Partial<Record<CardContract['id'], () => ReactElement | null>>> =
  /**
   * 🔴 **This was `Object.freeze({})`** — [TASK-1425](../../../../../../docs/BACKLOG.md).
   * ⚡ **With both it and `REGISTRY` empty, `cardsFor` returned nothing and
   * every visit fell through to the empty state**, which is the measurement
   * this row was sequenced on.
   *
   * ⛔ **A card appears here only when it can be RENDERED**, which is why the
   * filter below exists: 📁 the catalogue is deliberately written ahead of the
   * cards, and a registered card with no renderer must not draw a hole.
   */
  Object.freeze({
    'pipeline-health': PipelineHealthCard,
    'connect-a-crm': ConnectCrmCard,
    'connect-calls': ConnectCallsCard,
    'invite-the-team': InviteTheTeamCard,
  });

export function Home() {
  const { activeWorkspace, isLoading, error } = useWorkspaceContext();
  const workspaceId = activeWorkspace?.id ?? null;

  /**
   * 🔴 **Presentational only, and the card contract says so** — 📁 *"`requires`
   * is presentational. `null` means every member may see it. **This is not an
   * authorization decision**."* ⛔ **Casbin on the server decides what a person
   * may read; this only decides what it is useful to draw** ([§20c](../../../../../../CLAUDE.md)).
   *
   * ⚡ **The same hook the shell already holds**, so this costs no request.
   */
  const { data: session } = useSession();
  const viewer = useViewerRole(workspaceId, session?.user.id ?? null);
  const role: WorkspaceRole | null = viewer.role;

  /**
   * ⚡ **The one signal that genuinely decides a composition today** — 📁 the
   * design's qualifier for Activation is *"Any role, empty workspace"*, and
   * `CompositionInput.workspaceIsEmpty` is the field that carries it.
   *
   * ⛔ **A workspace that has never declared a target account is the same
   * signal `/` already uses to tell an empty INPUT from an empty RESULT** — one
   * question, one read, one answer ([§2](../../../../../../CLAUDE.md)).
   */
  const targets = useTargetAccounts(workspaceId);

  /**
   * 🔴 **[P-A](../../../../../../docs/DOMAIN_DISCOVERY_REGISTER.md): a failed
   * read must never render as an empty result.**
   *
   * ⛔ **Here the empty result is *"your workspace holds nothing"***, which
   * resolves the ACTIVATION composition — **so a failed read would not merely
   * show less, it would show a customer the wrong Home.**
   */
  if (error !== null || targets.isError) {
    return <StatedAbsence as="page" icon={HomeIcon} subject="your home" />;
  }

  /**
   * ⚠️ **`workspaceIsEmpty` is only knowable once the read lands.** ⛔ **Guessing
   * `true` while it is in flight would flash Activation at an established
   * customer**, and guessing `false` would flash an executive shell at a new
   * one. ✅ **So the composition is not resolved until it can be resolved.**
   */
  if (isLoading || targets.isPending) {
    return <PageHeader title="Home" description="Resolving your home…" />;
  }

  const workspaceIsEmpty = (targets.data?.version ?? 0) === 0;

  // ⛔ **`primaryRole` is `null` and the type says so** — nothing here invents
  // one, which is what [D-167](../../../../../../docs/DECISION_REGISTER.md) §4
  // forbids and what the resolver's own fallback exists for.
  const composition = resolveComposition({ workspaceIsEmpty, primaryRole: null });
  const cards = cardsFor(composition, role);
  const rendered = cards.filter((card) => RENDERERS[card.id] !== undefined);

  return (
    <div className="flex flex-col gap-6" data-testid="home" data-composition={composition}>
      {/* 🔴 **Over whichever composition resolved, never instead of one** —
          [TASK-1424](../../../../../../docs/BACKLOG.md). 📁 Rule 20: *"Home,
          with the first-run overlay"*, and Home's own words: *"adds the
          first-run overlay **over whichever composition resolved**."* ⛔ **It is
          not a fifth composition**, and the cards below it are unchanged — a
          new person's Home must be the same screen they come back to. */}
      <FirstRunOverlay />

      {/* 📁 ***"Progress counts blocking cards only"***, and 📁 ***"skipping is
          reversible from the PROGRESS LINE"*** — [TASK-1424](../../../../../../docs/BACKLOG.md).
          ⛔ **Only in the activation composition**: the other three are not a
          setup sequence, and a *step 1 of 2* over an executive dashboard would
          be counting something nobody is doing. */}
      {composition === 'activation' ? <ActivationProgress /> : null}
      {/* 📁 *"not a separate screen with its own layout, navigation or
          breadcrumb"* — ⛔ **so this states the composition and nothing more.**
          ⚡ The question is the design's own for each of the four. */}
      <PageHeader
        title="Home"
        description={`${COMPOSITION_NAME[composition]} · ${COMPOSITION_QUESTION[composition]}`}
      />

      {rendered.length === 0 ? (
        <EmptyState
          icon={HomeIcon}
          title="Signora has nothing to put on your home yet"
          /* ⛔ **Never *"coming soon"***, and never a count of cards that do not
             exist. ⚡ **It says what would fill this and where the work is
             today**, so somebody who wants a home reads an instruction rather
             than an apology. */
          description="Home is composed from what each part of Signora publishes, and none of them publishes a card yet. Your accounts, signals and settings all work — this surface is the one that gathers them."
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 laptop:grid-cols-2">
          {rendered.map((card) => {
            const Card = RENDERERS[card.id];
            return Card === undefined ? null : (
              <section key={card.id} data-card={card.id} aria-label={card.title}>
                <Card />
              </section>
            );
          })}
        </div>
      )}
    </div>
  );
}
