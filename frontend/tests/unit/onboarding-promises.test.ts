/**
 * **Onboarding names only destinations that exist** —
 * [B-256](../../../docs/BUGS.md).
 *
 * 🔴 **The goals step told a customer where the product would take them, and
 * for three of the six goals it was not true.** 📁 Picking *"Forecast
 * accurately"* — **the first option on the screen** — produced *"Signora will
 * open on Forecast, the Executive Dashboard."* ⛔ **Neither has a route on any
 * branch**, and `forecast` is refused as domain law: `buying_score_engine`
 * states *"no probability, no likelihood, no prediction… it does not forecast a
 * purchase."*
 *
 * ⚡ **This is the false-affordance class this repository refuses by name**
 * ([§20c](../../../CLAUDE.md), [C-017](../../../docs/LANE_COORDINATION.md)) —
 * **and it is the worst variety of it**, because the promise is made in the
 * first two minutes of using the product and is the reason somebody chose the
 * goal.
 */
import { describe, expect, it } from 'vitest';

import { reachable } from '@/app/(onboarding)/onboarding/goals-form';

describe('🔴 a goal names only what a customer can reach', () => {
  /**
   * 🔴 **The assertion the defect failed**, and it is the product's own first
   * goal.
   */
  it('🔴 “forecast accurately” promises nothing, because it has nothing', () => {
    expect(reachable(['forecast', 'executive_dashboard'])).toEqual([]);
  });

  it('✅ a goal whose features ship names them', () => {
    expect(reachable(['signals', 'opportunity_intelligence'])).toEqual(['Signals']);
    expect(reachable(['companies', 'ai_research'])).toEqual(['Companies']);
    expect(reachable(['team_management', 'ai_copilot'])).toEqual(['your team']);
  });

  /**
   * ⛔ **The Copilot is deliberately NOT named**, and that is the interesting
   * case. 📁 [TASK-482](../../../docs/BACKLOG.md) shipped it as a panel that
   * **states it cannot answer yet** — ✅ **honest, and a real surface** — ⚡ **but
   * *"Signora will open on the Copilot"* is a claim about a DESTINATION, and it
   * has no route.** **A room reached through a drawer is not somewhere the
   * product opens on.**
   */
  it('⛔ names nothing that has no route, however honest the surface is', () => {
    expect(reachable(['ai_copilot'])).toEqual([]);
    expect(reachable(['account_360'])).toEqual([]);
  });

  /**
   * ⚠️ **An identifier this file has never heard of is not evidence that a
   * screen exists.** ⛔ **The old map titled an unknown id and promised it**;
   * the risk it was guarding against — a feature vanishing because the map was
   * not updated — **is the smaller of the two.**
   */
  it('⛔ an unknown identifier is not a destination', () => {
    expect(reachable(['something_nobody_has_built'])).toEqual([]);
  });

  it('✅ and the order the server sent is kept', () => {
    expect(reachable(['reports', 'signals', 'companies'])).toEqual([
      'Reports',
      'Signals',
      'Companies',
    ]);
  });
});
