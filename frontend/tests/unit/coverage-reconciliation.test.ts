/**
 * **The reconciliation that would have caught [B-1027](../../../docs/BUGS.md)** —
 * 393 tests enumerated, 385 accounted for, and nothing said so.
 */
import type { FullResult, Suite, TestCase } from '@playwright/test/reporter';
import { afterEach, describe, expect, test, vi } from 'vitest';

import { CoverageReconciliation } from '../e2e/reporters/coverage-reconciliation';

function testCase(id: string, title = id): TestCase {
  return { id, titlePath: () => ['', 'owner', `${title}.spec.ts`, title] } as unknown as TestCase;
}

function suiteOf(...tests: TestCase[]): Suite {
  return { allTests: () => tests } as unknown as Suite;
}

function ended(status: FullResult['status']): FullResult {
  return { status } as FullResult;
}

async function run(
  reporter: CoverageReconciliation,
  enumerated: TestCase[],
  reported: TestCase[],
  status: FullResult['status'] = 'failed',
): ReturnType<CoverageReconciliation['onEnd']> {
  reporter.onBegin(undefined, suiteOf(...enumerated));
  for (const test of reported) reporter.onTestEnd(test);
  return reporter.onEnd(ended(status));
}

const written: string[] = [];
vi.spyOn(process.stdout, 'write').mockImplementation((chunk) => {
  written.push(String(chunk));
  return true;
});

afterEach(() => {
  written.length = 0;
});

describe('a run that does not account for every test it enumerated', () => {
  test('🔴 fails, and names the tests that never ran', async () => {
    const ran = testCase('a');
    const abandoned = testCase('b', 'the tail of a serial block');

    const outcome = await run(new CoverageReconciliation(), [ran, abandoned], [ran]);

    expect(outcome).toEqual({ status: 'failed' });
    expect(written.join('')).toContain('1 of 2 enumerated tests never ran');
    // ⚡ **Named, not counted** — 📁 the whole defect was that a count looked complete.
    expect(written.join('')).toContain('the tail of a serial block');
  });

  test('✅ and says nothing at all when everything is accounted for', async () => {
    const tests = [testCase('a'), testCase('b')];

    const outcome = await run(new CoverageReconciliation(), tests, tests, 'passed');

    expect(outcome).toBeUndefined();
    expect(written).toEqual([]);
  });

  /**
   * 🔴 **The case the printed count cannot cover.** ⚡ **Playwright's own
   * summary prints `N did not run`** — measured, `359 did not run` — **but a
   * printed line does not change an exit code.** ⛔ **A run whose every
   * reported outcome passed must not exit `0` while tests it enumerated never
   * ran**, because that is indistinguishable from a green run.
   */
  test('🔴 a run whose reported outcomes all passed still fails if something never ran', async () => {
    const ran = testCase('a');

    const outcome = await run(new CoverageReconciliation(), [ran, testCase('b')], [ran], 'passed');

    expect(outcome).toEqual({ status: 'failed' });
  });

  /**
   * ⚠️ **A retry reports the same `TestCase` twice.** ⛔ **Counting reports
   * rather than distinct tests would hide a missing test behind a retried one**
   * — which is this defect's own shape, one level along.
   */
  test('✅ a retried test is one test, not two', async () => {
    const flaky = testCase('a');
    const missing = testCase('b');

    const outcome = await run(new CoverageReconciliation(), [flaky, missing], [flaky, flaky]);

    expect(outcome).toEqual({ status: 'failed' });
    expect(written.join('')).toContain('1 of 2 enumerated tests never ran');
  });

  /**
   * ⛔ **An interrupted run already says it did not finish** — `--max-failures`,
   * or a Ctrl-C. ✅ **Reported, never re-failed**: the tests that did not run
   * there are the ones the operator asked not to run.
   */
  test('⚠️ an interrupted run is reported but not re-failed', async () => {
    const ran = testCase('a');

    const outcome = await run(new CoverageReconciliation(), [ran, testCase('b')], [ran], 'interrupted');

    expect(outcome).toBeUndefined();
    expect(written.join('')).toContain('1 of 2 enumerated tests never ran');
  });
});
