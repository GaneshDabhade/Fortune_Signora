/**
 * **The card registry** — [TASK-1406](../../../docs/BACKLOG.md), against
 * 📁 `docs/design-snapshot/screens/Fortune Signora Authenticated Entry.dc.html`
 * ([D-138](../../../docs/DECISION_REGISTER.md)).
 *
 * > 📁 ***"Modules register capabilities rather than issuing redirects."***
 * > 📁 ***"A new module ships a card contract, and the four compositions decide
 * > whether to include it."***
 *
 * ## ⚡ It is the repository's third registry, and it is built to look like the first two
 *
 * 📁 **The row names them**: `signora_platform/authorization/policies/policy.csv`
 * and `backend/tests/security_invariants/tenancy_policy.py` — ⛔ **read before
 * this file was written, not cited afterwards.** **Both are static, declarative,
 * appended by every lane, and neither registers anything at runtime.**
 *
 * ⚡ **The discipline worth copying is `tenancy_policy.py`'s, and it is one
 * sentence**: 📁 ***"Declaring the split explicitly is the point. Inferring
 * tenant-owned from the presence of a `workspace_id` column meant a new table
 * that simply forgot the column was silently classified as platform
 * infrastructure and exempted from every check."*** ⛔ **The failure mode of a
 * misclassification is a build failure rather than a silent exemption.**
 *
 * ✅ **So the same shape here**: **a card that no composition names, or a
 * composition naming a card the catalogue does not have, fails to compile or
 * fails a test.** ⛔ **Never renders as nothing and never silently disappears.**
 *
 * ## ⛔ There is no `registerCard()`, and that is the design decision
 *
 * ⚠️ **A runtime registry was the obvious reading of *"modules register"* and it
 * is the wrong one.** **Registration at import time makes a composition's
 * contents depend on module load order** — 📁 which is the same class of defect
 * as `REASON_CODES`' ordering in [`lib/entry/reasons.ts`](../entry/reasons.ts):
 * *"the order is load-bearing and is not alphabetical."* ⛔ **A card catalogue
 * that reorders itself because an import moved is not a catalogue.**
 *
 * ✅ **Neither named registry does it either.** `policy.csv` is a file a lane
 * appends a line to; `TENANT_OWNED_TABLES` is a `frozenset` a lane adds a name
 * to. ⚡ **A module contributes by adding an entry below — a diff a reviewer can
 * see** — **not by calling a function at some point during boot.**
 *
 * ## 🔴 Presentational, never authorization
 *
 * ⛔ **[§20c](../../../CLAUDE.md), and the row names this as its own risk.**
 * **`requires` hides a card the caller could not use. It decides nothing.**
 * 📁 **Casbin on the server is the authorization decision (ADR-0010)** and a
 * card whose data the caller may not read is refused there whether or not it
 * was rendered. ⚡ **The registry's filter exists so a member is not offered a
 * card that will come back empty** — 📁 the rule
 * [`navigation.tsx`](../../components/shell/navigation.tsx) already applies:
 * *"a link the caller cannot follow is not rendered."*
 *
 * ## ⚠️ The registry is EMPTY today, and that is the honest state
 *
 * ⛔ **No module contributes a card yet**, so every composition resolves to
 * nothing. ✅ **That is the same condition `ShellBanners` is in — 📁 *"it
 * renders nothing because nothing has state to give it, which is the frame
 * working as designed"*** — **and it is reported rather than filled with
 * placeholders.** ⚡ **The catalogue below is the design's list, so the first
 * contributing module finds its card already named and ordered.**
 */

import type { Composition } from '@/lib/home/composition';
import { can, type Capability, type WorkspaceRole } from '@/lib/state/permissions';

/**
 * 📁 **Every card the design names, across all four compositions.**
 *
 * ⛔ **`as const` is load-bearing**: it makes {@link CardId} a closed union, so
 * **a composition naming a card that does not exist fails to compile** rather
 * than resolving to nothing at runtime.
 */
export const CARD_IDS = [
  // ── 📁 The registry's own order, §04 ────────────────────────────────────
  'daily-briefing', //          card.briefing          SE · EX
  'needs-you-today', //         card.attention         SE
  'meetings', //                card.meetings          SE
  'agent-queue', //             card.agentqueue        SE · OP
  'recents', //                 card.recents           SE · OP · EX
  'ai-executive-summary', //    card.execsummary       EX
  'forecast-vs-plan', //        card.forecast          EX
  'pipeline-health', //         card.pipeline          EX
  'top-risks', //               card.risks             EX
  'top-opportunities', //       card.opps              EX
  'integration-health', //      card.inthealth         OP · EX
  'agent-runs', //              card.agentruns         OP
  'data-quality', //            card.dataquality       OP
  'pending-requests', //        card.requests          OP
  'connect-a-crm', //           card.activation.*      AC
  'connect-calls', //           card.activation.*      AC
  'invite-the-team', //         card.activation.invite AC
] as const;

export type CardId = (typeof CARD_IDS)[number];

/**
 * **What a module contributes.**
 *
 * ⚡ **Deliberately small.** 📁 The design's boundary table gives Home *"the
 * composition"* and the module *"the card's content"* — ⛔ **so a contract
 * carrying layout, width or position would be the module deciding something
 * Home owns**, and the two layers would drift exactly as §06 warns.
 */
export interface CardContract {
  readonly id: CardId;
  /** 📁 The design's own words for it. ⛔ Never a module's paraphrase. */
  readonly title: string;
  /**
   * ⚡ **Which module answers for this card**, so a broken one has an owner
   * without a `git blame` — the same reason [`modules.toml`](../../../docs/coordination/modules.toml)
   * exists.
   */
  readonly module: string;
  /**
   * 🔴 **Presentational only.** `null` means every member may see it.
   * ⛔ **This is not an authorization decision** — see the header.
   */
  readonly requires: Capability | null;
}

/**
 * 📁 **Which cards each composition shows, in the design's order.**
 *
 * ⛔ **The order IS the design's and is not alphabetised.** ⚡ 📁 The seller
 * composition is *"a day plan, not a dashboard — ordered work"*, so the
 * sequence is content rather than presentation, and sorting this array would
 * silently rewrite what the product recommends a person do first.
 *
 * ✅ **This is the whole of *"the four compositions decide whether to include
 * it"*** — 📁 a fifth composition is a fifth key, and a sixth module is one
 * entry in {@link REGISTRY} plus its id in whichever lists want it.
 */
export const COMPOSITION_CARDS: Readonly<Record<Composition, readonly CardId[]>> =
  Object.freeze({
    /**
     * 📁 ***"How are we doing?"*** — every registry row carrying `EX`.
     */
    executive: [
      'ai-executive-summary',
      'forecast-vs-plan',
      'pipeline-health',
      'top-risks',
      'top-opportunities',
      'integration-health',
      'daily-briefing',
      'recents',
    ],
    /** 📁 ***"What do I do today?"*** — every registry row carrying `SE`. */
    seller: ['daily-briefing', 'needs-you-today', 'meetings', 'agent-queue', 'recents'],
    /** 📁 ***"Is the system healthy?"*** — every registry row carrying `OP`. */
    revenue_operations: [
      'integration-health',
      'agent-runs',
      'data-quality',
      'pending-requests',
      'agent-queue',
      'recents',
    ],
    /**
     * 📁 ***"How do I begin?"*** — `card.activation.*` and
     * `card.activation.invite`, and **nothing else.**
     *
     * ⛔ **`what-signora-will-do` is NOT here and must never be.** 📁 **P-04**:
     * *"'What Signora will do' is a footer line, **not a card**. As a card it
     * competed with the three steps for attention and was routinely skipped."*
     * ✅ It renders as the footer of the incomplete step.
     *
     * ⛔ **`sample-of-one-real-account` is not here either** — 📁 the
     * Authenticated Entry document lists it, **but Home is the composition
     * authority** and its registry does not name it.
     */
    activation: ['connect-a-crm', 'connect-calls', 'invite-the-team'],
  });

/**
 * **What modules have actually contributed.**
 *
 * ⛔ **EMPTY, and it is empty on purpose.** ⚠️ **Measured 2026-08-10: no module
 * publishes a Home card.** ✅ **A lane adds one line here when it ships one** —
 * that is the *"registration mechanism"*, and it is a reviewable diff for the
 * reason the header gives.
 *
 * ⚡ **Nothing renders a placeholder in the meantime.** 📁
 * [TASK-1433](../../../docs/BACKLOG.md)'s rule generalises: *"an empty panel
 * does not reserve space for a future feature, it takes space from the one the
 * customer is using today."*
 */
export const REGISTRY: readonly CardContract[] = [
  /**
   * 🔴 **The first card any module has contributed** —
   * [TASK-1425](../../../docs/BACKLOG.md). ⚡ **Until this entry, `REGISTRY`
   * was `[]`**, so `cardsFor` returned nothing and every visit to Home fell
   * through to *"Signora has nothing to put on your home yet"* — **the
   * measurement this row was sequenced on.**
   *
   * 📁 **The design's own registry entry**: *"Pipeline health · `card.pipeline`
   * · EX · **Coverage, stage distribution, movement**"*.
   *
   * ⚠️ **`requires` is `null` and that is not laxity.** 📁 The contract's own
   * rule: *"presentational only… Casbin on the server is the authorization
   * decision."* ⛔ **The read is workspace-scoped and authorized server-side**,
   * and a client-side capability gate here would be the false-claim class
   * [B-253](../../../docs/BUGS.md) is open about.
   */
  /**
   * 🔴 **Activation's two BLOCKING steps** — [TASK-1424](../../../docs/BACKLOG.md).
   * ⛔ **`invite-the-team` is deliberately absent**: it is the only
   * non-blocking card, so it is the only one the design lets a person skip —
   * and *"skip state is per person, on the server, for 30 days. Nothing about
   * activation lives in `localStorage`."* **No endpoint holds that.**
   */
  { id: 'connect-a-crm', title: 'Connect a CRM', module: 'integrations', requires: null },
  {
    id: 'connect-calls',
    title: 'Connect calls and calendar',
    module: 'integrations',
    requires: null,
  },
  /**
   * ✅ **The third activation step, contributed once its store existed** —
   * [TASK-1424](../../../docs/BACKLOG.md). ⛔ It was deliberately absent while
   * the 30-day skip had nowhere to live, **because a *Skip for now* that
   * forgot at the next sign-in is a control that lies.**
   */
  { id: 'invite-the-team', title: 'Invite the team', module: 'workspace_tenancy', requires: null },
  {
    id: 'pipeline-health',
    // 📁 The design's own words, not a paraphrase — the contract requires it.
    title: 'Pipeline health',
    module: 'opportunity_engine',
    requires: null,
  },
  /**
   * 🔴 **The seller composition's answer card, and it had a renderer and no
   * contract.**
   *
   * ⚠️ **Found in a browser, not by a gate.** `AttentionCard` has been in
   * `RENDERERS` since Home was written and `needs-you-today` was never in this
   * registry — so `cardsFor` filtered it out and **the seller composition
   * rendered zero cards on every visit.** ⛔ **`tsc` cannot see it**: the
   * renderer map is `Partial`, the registry is a list, and neither knows about
   * the other. **The composition switched to `seller` and the grid was empty.**
   *
   * ✅ **Registered now because its producers exist** — 📁 the design's
   * dependency is *"signals + deals"*, and the open signal queue, the catalog,
   * the scoring model, the identity batch and the commercial batch all ship.
   *
   * 📁 **`module` is `signal_engine`** and that is the row's source of truth:
   * an attention item **is** an open signal with its rationale. ⛔ **Not
   * `opportunity_engine`** — the product owner ruled `AccountAttention` out of
   * Home on 2026-08-17, and naming that module here would re-assert the
   * dependency the ruling removed.
   */
  {
    id: 'needs-you-today',
    // 📁 The design's own words for `card.attention`.
    title: 'Needs you today',
    module: 'signal_engine',
    requires: null,
  },
  /**
   * ✅ **`card.risks` and `card.opps` — registered because their producers
   * exist, which a previous audit measured wrongly.**
   *
   * ⛔ **It searched `signal_engine` for a risk/opportunity classification,
   * found none, and concluded the cards were unbuildable.** ✅ **The judgement
   * is `buying_score_engine`'s**, ratified in `scoring_model@1.json` as a
   * `posture` per type and published on `GET /workspaces/{id}/scoring-model` —
   * **the module named below is the one that owns it.**
   */
  /**
   * ✅ **`card.inthealth`** — 📁 *"per-connection state"*, whose dependency
   * `integrations.health` is served today by `GET /workspaces/{id}/integrations`.
   *
   * ⛔ **The registry's *"including held write queues"* waits on E2.** 📁 CRM
   * Integrations defines a held write precisely; 📁 `source.py:177` says
   * *"write-back is E2's territory"*, and 📁 `406-epic-e2-crm-write-back.md`
   * is *"prepared… no code was written and none should be."* **Signora cannot
   * hold a write because it cannot write. A dependency, not a gap.**
   */
  { id: 'integration-health', title: 'Integration health', module: 'integrations', requires: null },
  /**
   * ✅ **`card.recents`** — 📁 Session Continuity **tier 4** is the producer,
   * and it defines *"touched"* as **viewed**. `workspace_tenancy` owns the
   * fact because 📁 Home *"defines no storage of its own"*.
   */
  { id: 'recents', title: 'Pick up where you left off', module: 'workspace_tenancy', requires: null },
  { id: 'top-risks', title: 'Top risks', module: 'signal_engine', requires: null },
  { id: 'top-opportunities', title: 'Top opportunities', module: 'signal_engine', requires: null },
];

/**
 * **A composition, resolved: filtered by what this person may use, ordered by
 * the design.**
 *
 * 📁 ***"A composition is a filtered, ordered read of a registry."*** ⚡ **This
 * function is that sentence and nothing more.**
 *
 * ⛔ **Order comes from {@link COMPOSITION_CARDS}, never from
 * {@link REGISTRY}** — a registry is a set of contributions and the sequence a
 * person reads is the design's decision, not the order lanes happened to append
 * in.
 *
 * ⚠️ **A card named by a composition and absent from the registry is SKIPPED,
 * not rendered empty.** ✅ **That is what makes the catalogue safe to write
 * ahead of the cards**: the design's full list can sit above while the product
 * shows only what exists. 📁 **The consistency the build enforces is the other
 * direction** — a registered card that no composition names is a test failure,
 * because it is a module that shipped a card nobody will ever see.
 */
export function cardsFor(
  composition: Composition,
  role: WorkspaceRole | null,
  registry: readonly CardContract[] = REGISTRY,
): readonly CardContract[] {
  const contributed = new Map(registry.map((card) => [card.id, card]));

  return COMPOSITION_CARDS[composition]
    .map((id) => contributed.get(id))
    .filter((card): card is CardContract => card !== undefined)
    .filter((card) => card.requires === null || can(role, card.requires));
}

/**
 * ## ⛔ There is no `unplacedCards()`, and removing it is the honest half of this row
 *
 * ⚠️ **One was written here, exported, and tested**: it returned registered
 * cards that no composition names — 📁 `tenancy_policy.py`'s *"a table
 * appearing in neither list"* check, transposed.
 *
 * 🔴 **It could never return anything.** **A `CardContract.id` is a
 * {@link CardId}, every `CardId` is placed in a composition (asserted in
 * `home-cards.test.ts`), so a well-typed registry entry is placed by
 * construction.** ⛔ **A function whose removal changes no property is
 * [§2](../../../CLAUDE.md)'s Decorative Logic**, and a test over it passes
 * whatever the code does.
 *
 * ✅ **The real guard is one level up and it CAN fail**: *every card in the
 * catalogue is placed in at least one composition.* **Add a `CardId` and forget
 * to place it and the build goes red** — which is the property the deleted
 * function only appeared to provide.
 */
