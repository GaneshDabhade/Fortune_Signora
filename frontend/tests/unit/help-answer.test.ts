import { describe, expect, it } from 'vitest';

import { answerFor, answerableSubjects } from '@/app/(app)/help/answer';
import type { Connection, IntegrationSystem } from '@/lib/api/types';

/**
 * **The Help Center's answer** — [TASK-1420](../../../docs/BACKLOG.md).
 *
 * 📁 **The row names its own failure**: ⛔ *"shipping a generic documentation
 * site and calling the workflow done."* ⚡ **So the assertions here are mostly
 * about what the answer REFUSES to say**, which is the part that separates an
 * answer about this workspace from advice about any workspace.
 */

function connection(over: Partial<Connection> = {}): Connection {
  return {
    id: 'c1',
    integration: 'salesforce',
    label: 'Salesforce',
    state: 'connected',
    connected_at: '2026-08-01T00:00:00Z',
    attention: 'none',
    reason: null,
    health: 'healthy',
    ...over,
  };
}

function system(connections: Connection[]): IntegrationSystem {
  return {
    integration: 'salesforce',
    capabilities: [],
    connectable: true,
    working: connections.some((c) => c.health === 'healthy'),
    needs_attention: connections.some((c) => c.attention !== 'none'),
    connections,
  };
}

describe('⛔ what it refuses to answer', () => {
  it('⛔ an empty question gets nothing', () => {
    expect(answerFor('', [], [])).toBeNull();
    expect(answerFor('   ', [], [])).toBeNull();
  });

  it('🔴 a question naming no connected system gets NOTHING, not general advice', () => {
    /**
     * ⚡ **This is the row's named risk, as an assertion.** ⛔ **Answering here
     * would mean answering every question the same way** — the commodity half
     * wearing the differentiator's clothes.
     */
    const c = connection();
    expect(answerFor('why is my HubSpot sync slow', [system([c])], [c])).toBeNull();
  });

  it('⛔ a workspace with nothing connected gets nothing, however the question is phrased', () => {
    expect(answerFor('why did my Salesforce write-back stop', [], [])).toBeNull();
  });
});

describe('✅ what it answers, from real telemetry', () => {
  it('🔴 degraded says CONNECTED-but-unusable, which is the distinction health exists for', () => {
    /**
     * 📁 [TASK-407](../../../docs/BACKLOG.md) made `health` mean *what happened
     * when Signora last actually TRIED to use it*, distinct from `state`, which
     * is what the records imply. ⚡ **The design's worked example is exactly
     * that distinction** — *"paused, not broken"*.
     */
    const c = connection({ health: 'degraded', reason: 'Field-level security denied' });
    const answer = answerFor('why did my Salesforce write-back stop', [system([c])], [c]);

    expect(answer).not.toBeNull();
    expect(answer?.tone).toBe('degraded');
    expect(answer?.headline).toContain('could not use it');
    // ⛔ **The system's own reason, quoted rather than paraphrased.**
    expect(answer?.detail).toContain('Field-level security denied');
  });

  it('⛔ degraded with no reason says the system did not say why', () => {
    // ⚡ **It does not invent one.** A plausible cause here is the fabrication
    // that costs most: a customer would go and change the wrong setting.
    const c = connection({ health: 'degraded', reason: null });
    const answer = answerFor('salesforce', [system([c])], [c]);
    expect(answer?.detail).toContain('did not say why');
  });

  it('⛔ unknown says NOT CHECKED rather than implying health', () => {
    // 🔴 A confident *"it is working"* here would be the records implying a
    // health nothing measured — the exact failure `health` was added to end.
    const c = connection({ health: 'unknown' });
    const answer = answerFor('salesforce', [system([c])], [c]);
    expect(answer?.tone).toBe('unknown');
    expect(answer?.headline).toContain('has not tried');
  });

  it('✅ every answer carries at least one source the customer can open', () => {
    // 📁 The design shows *"3 sources"* beside the answer. ⛔ **An answer with
    // no source is prose**, so the floor is asserted rather than the count.
    for (const health of ['healthy', 'degraded', 'unknown'] as const) {
      const c = connection({ health });
      const answer = answerFor('salesforce', [system([c])], [c]);
      expect(answer?.sources.length, health).toBeGreaterThan(0);
      expect(answer?.sources[0]?.href).toBe('/settings/connections');
    }
  });

  it('🔴 the unhealthy connection leads when several are named', () => {
    /**
     * ⚡ **A person asking a help question during an outage needs the broken
     * system first**, not the alphabetically first. ⛔ **Vacuity guard**: both
     * connections match the question, so the ordering is what is under test
     * rather than the matching.
     */
    const healthy = connection({ id: 'a', label: 'Salesforce', health: 'healthy' });
    const broken = connection({ id: 'b', label: 'Salesforce', health: 'degraded' });
    const answer = answerFor('salesforce', [system([healthy, broken])], [healthy, broken]);
    expect(answer?.tone).toBe('degraded');
  });
});

describe('📁 it says what it CAN answer about', () => {
  it('✅ names the connected systems, so the box is not a silent dead end', () => {
    const a = connection({ id: 'a', label: 'Salesforce' });
    const b = connection({ id: 'b', label: 'HubSpot', integration: 'hubspot' });
    expect(answerableSubjects([a, b])).toEqual(['Salesforce', 'HubSpot']);
  });

  it('⛔ and names nothing when nothing is connected', () => {
    expect(answerableSubjects([])).toEqual([]);
  });
});
