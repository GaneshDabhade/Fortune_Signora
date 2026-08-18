import type { Posture } from '@/lib/api/types';

/**
 * 📁 **Posture is the severity, and this map is the only part of it a screen
 * owns.**
 *
 * ⛔ **The posture itself is NOT decided here.** 📁 It is Signora's, published
 * per hypothesis type by the Buying Score Engine's reviewed artifact
 * (`scoring_model@1.json`), whose own comment settles why it is not a
 * preference:
 *
 * > 📁 ***"Posture is not configurable — whether `CONTRACTION_RISK` reads as
 * > contractionary is a fact about the English language, not a preference, and
 * > a workspace inverting it would make `contested` meaningless across the
 * > platform."***
 *
 * ⚡ **Extracted here because three Home cards need it** — `card.attention`,
 * `card.risks` and `card.opps` — **and a second copy would be free to
 * disagree** ([§2](../../../CLAUDE.md), *truth has exactly one authoritative
 * representation*).
 *
 * 🔴 **This is also the answer to a question a previous audit got wrong.** ⛔ It
 * concluded that nothing in the repository classified a signal type as a risk
 * or an opportunity, **having searched `signal_engine` only** — the catalog
 * there carries no polarity, and the conclusion looked sound. ✅ **The
 * classification was one module over, ratified, and already published on
 * `GET /workspaces/{id}/scoring-model`.**
 */
export const TONE: Readonly<Record<Posture, 'risk' | 'warn' | 'pos'>> = Object.freeze({
  contractionary: 'risk',
  neutral: 'warn',
  expansionary: 'pos',
});

/**
 * 📁 **Which posture each Executive card is about.**
 *
 * ⛔ **`neutral` belongs to NEITHER, and that is deliberate.** 📁 The design
 * asks `card.opps` for *"ranked **positive** signals"*, and
 * `consolidation_underway` and `new_decision_maker` are not positive — they are
 * the two the model declines to call either way. ⚡ **Putting them in one card
 * would assert a reading the domain explicitly refuses to make.**
 */
export const CARD_POSTURE = Object.freeze({
  risks: 'contractionary',
  opportunities: 'expansionary',
} as const satisfies Record<'risks' | 'opportunities', Posture>);
